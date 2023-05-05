from deep_sort.utils.parser import get_config
from deep_sort.deep_sort import DeepSort
import torch
import cv2
import numpy as np
import os
from splitUtils.splitImages_multi_processor import splitbase
from splitUtils.resultMerge import py_cpu_nms
# 记录真实目标的真实宽度，方便通过像素宽度计算比例尺

CLASS_WIDTH_DICT = {
    "car": 1.8,
    "person": 0.5
}


cfg = get_config() #
cfg.merge_from_file("deep_sort/configs/deep_sort.yaml")
deepsort = DeepSort(cfg.DEEPSORT.REID_CKPT,
                    max_dist=cfg.DEEPSORT.MAX_DIST, min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                    nms_max_overlap=cfg.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                    max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                    use_cuda=True)

# 用于记录上一帧图片中的目标坐标以及类别和ID
last_obj_id_list = [] # 记录上一帧的目标ID
last_obj_xywh = [] # 记录上一帧的目标中心点坐标以及像素长宽
last_obj_cls = [] # 记录上一帧目标的类别
# pro_speed_thresh_image = np.array([]) # 用于画超出阈值的加速度点

last_obj_dict = {} # 记录上一帧目标的中心点坐标、宽高以及类别，目标ID作为key
last_obj_speed_dict = {} # 记录上一帧目标的速度
last_obj_pro_speed_dict = {}
cur_frame_id = 0 # 记录当前的帧号，用于保存加速度超过阈值的图片

def xyxy2xywh(x1,y1,x2,y2):


    w,h = x2-x1, y2-y1
    x,y = x1+w/2, y1+h/2
    return x,y,w,h



def save_last_obj_dict(cur_obj_list):
    global last_obj_dict
    for obj in cur_obj_list:
        last_obj_dict[obj[-1]] = [xyxy2xywh(obj[0],obj[1],obj[2],obj[3]), obj[4]]

def get_speed_for_obj(cur_obj_list, fps):

    speed_list = [0.0 for i in range(len(cur_obj_list))]
    speed_pro_list = [0.0 for i in range(len(cur_obj_list))]
    speed_pro_change_list = [-1 for i in range(len(cur_obj_list))]
    if len(last_obj_dict) == 0:
        save_last_obj_dict(cur_obj_list=cur_obj_list)
        return speed_list, speed_pro_list, speed_pro_change_list
    for idx, obj in enumerate(cur_obj_list):
        curid = obj[-1]
        if curid in last_obj_dict.keys():
            xywh = last_obj_dict[curid][0]
            cls = last_obj_dict[curid][1]

            if cls not in CLASS_WIDTH_DICT.keys():
                continue
            cur_xywh = xyxy2xywh(obj[0],obj[1],obj[2],obj[3])
            ratio = CLASS_WIDTH_DICT[cls]/(cur_xywh[2] + xywh[2]) * 2
            t = 2.0 / float(fps) / 3600
            speed = np.round(np.sqrt((xywh[0] - cur_xywh[0])**2 + (xywh[1] - cur_xywh[1])**2) * ratio / t / 1000, 1)
            last_speed = 0.0 if curid not in last_obj_speed_dict.keys() else last_obj_speed_dict[curid]
            last_obj_speed_dict[curid] = speed
            speed_list[idx] = speed
            speed_pro_list[idx] = np.round((speed - last_speed) / 3.6 / (t*3600),1)
            last_pro_speed = 0 if curid not in last_obj_pro_speed_dict.keys() else last_obj_pro_speed_dict[curid]
            last_obj_pro_speed_dict[curid] = speed_pro_list[idx]
            if last_pro_speed*speed_pro_list[idx] < 0:
                speed_pro_change_list[idx] = 1
        else:
            speed_list[idx] = 0.0
            speed_pro_list[idx] = 0.0
            last_obj_speed_dict[curid] = 0.0
            speed_pro_change_list[idx] = -1
    save_last_obj_dict(cur_obj_list=cur_obj_list)
    return speed_list, speed_pro_list, speed_pro_change_list

def plot_text(text_list, img, c1, c3, fillcolor, fontheight, fontScale, tf):
    colors = [
        [255, 255, 255],
        [255, 255, 255],
        [255, 255, 255],
    ]


    blk = np.zeros(img.shape, np.uint8)
    cv2.rectangle(blk, c1, c3, fillcolor, -1)	# 注意在 blk的基础上进行绘制；
    img = cv2.addWeighted(img, 1.0, blk, 0.7, 1)
    for idx, text in enumerate(text_list):
        cv2.putText(img, text, (c1[0], c1[1]-idx*fontheight-(idx+1)), 0, fontScale, colors[idx], thickness=tf, lineType=cv2.LINE_AA)
    return img

def plot_bboxes(args, image, speed_list, speed_pro_list, speed_pro_change_list, bboxes, line_thickness=1):
    global cur_frame_id
    pro_speed_thresh_image = None
    speed_thresh_image = None

    # 如果需要检测加速度，则需要复制一个原图方便标记
    if args.pro_speed_thresh != -1 and pro_speed_thresh_image is None:
        pro_speed_thresh_image = image.copy()
    pro_speed_flag = False # 标识当前帧是否有超过加速度阈值的目标

    # 如果需要检测速度，则需要复制一个原图方便标记
    if args.speed_thresh != -1 and speed_thresh_image is None:
        speed_thresh_image = image.copy()
    speed_flag = False # 标识当前帧是否有超过速度阈值的目标

    # 设置绘制边框的线条粗细程度
    tl = line_thickness or round(0.002 * (image.shape[0] + image.shape[1]) / 2) + 1  # line/font thickness

    cur_cls_num = {} # 记录当前所有目标的总数

    for idx, (x1, y1, x2, y2, cls_id, pos_id) in enumerate(bboxes):
        fontScale = np.abs(x2-x1)*0.01

        # 如果目标是行人，则用蓝色来标记
        if cls_id in ['person']:
            color = (0, 0, 255)
        else: # 如果是车辆
            color = (255, 0, 0)

        # 记录目标的左上角坐标和右下角坐标
        c1, c2 = (x1, y1), (x2, y2)

        # 绘制正常检测的目标边框
        cv2.rectangle(image, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
        tf = max(tl - 1, 2)  # font thickness
        t_size = cv2.getTextSize(cls_id, 0, fontScale=fontScale, thickness=tf)[0]

        # 绘制边框左上角部分的一个颜色填充区，用来写入ID和类别标签
        text_list = [
            '{}-{}'.format(cls_id, pos_id),
            "{}km/h".format(str(speed_list[idx])),
            # "{}m/s^2".format(str(speed_pro_list[idx]))
        ]
        if len(text_list)*t_size[1] > np.abs(y2-y1)*0.5:
            fontScale = fontScale/2
            t_size = cv2.getTextSize(cls_id, 0, fontScale=fontScale, thickness=tf)[0]
        if len(text_list)*t_size[1] < np.abs(y2-y1)*0.2:
            fontScale = fontScale*2
            t_size = cv2.getTextSize(cls_id, 0, fontScale=fontScale, thickness=tf)[0]

        c3 = c2[0], c1[1] - len(text_list)*t_size[1]-3
        fontheight = t_size[1]
        # 这里标记目标类别和图像的id，可以在此处添加计算速度的代码
        image = plot_text(text_list=text_list,img=image,c1=c1,c3=c3,
                          fillcolor=color,fontheight=fontheight,fontScale=fontScale,tf=tf)

        # 如果当前遍历的目标存在超过加速度阈值的，就要标记
        if args.pro_speed_thresh != -1 and speed_pro_list[idx] > args.pro_speed_thresh:
            cv2.rectangle(pro_speed_thresh_image, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
            pro_speed_thresh_image = plot_text(text_list=text_list,img=pro_speed_thresh_image,c1=c1,c3=c3,fillcolor=color,fontheight=fontheight,fontScale=fontScale,tf=tf)
            pro_speed_flag = True # 只要有一个目标超越了阈值，就标记为True

        # 如果当前遍历的目标存在超过速度阈值的，就要标记
        if args.speed_thresh != -1 and speed_list[idx] > args.speed_thresh:
            cv2.rectangle(speed_thresh_image, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
            speed_thresh_image = plot_text(text_list=text_list,img=speed_thresh_image,c1=c1,c3=c3,fillcolor=color,fontheight=fontheight,fontScale=fontScale,tf=tf)
            speed_flag = True # 只要有一个目标超越了阈值，就标记为True

        if cls_id not in cur_cls_num.keys():
            cur_cls_num[cls_id] = 1
        else:
            cur_cls_num[cls_id] += 1


    # 在图片的左上角显示各类别目标的统计数量
    showtitle = "Target stats: "
    title_fontScale = image.shape[0]/512*10
    title_fontheight = int(title_fontScale)
    for k in cur_cls_num.keys():
        showtitle = showtitle + k + ":" + str(cur_cls_num[k])+" "
    tf = 2  # font thickness
    cv2.putText(image,showtitle, (0, title_fontheight*10), cv2.FONT_HERSHEY_SIMPLEX, tl, [255, 0, 0], tf)
    if speed_flag:
        cv2.putText(speed_thresh_image,showtitle, (0, title_fontheight*2), cv2.FONT_HERSHEY_SIMPLEX, tl, [255, 0, 0], tf)
    if pro_speed_flag:
        cv2.putText(pro_speed_thresh_image,showtitle, (0, title_fontheight*2), cv2.FONT_HERSHEY_SIMPLEX, tl, [255, 0, 0], tf)
    # 保存加速度警告目标
    pro_speed_rootpath = os.path.join(args.output_dir,"pro_speed_thresh_images")
    save_img(pro_speed_rootpath,pro_speed_thresh_image,pro_speed_flag,args.pro_speed_thresh)

    # 保存速度警告目标
    speed_rootpath = os.path.join(args.output_dir,"speed_thresh_images")
    save_img(speed_rootpath,speed_thresh_image,speed_flag,args.speed_thresh)

    cur_frame_id += 1
    return image

def save_img(rootpath, img, flag, thresh):
    if not os.path.exists(rootpath):
        os.makedirs(rootpath)
    if flag:
        filepath = os.path.join(rootpath, "frame "+str(cur_frame_id)+" speedup over "+str(thresh)+".jpg")
        cv2.imwrite(filepath,img)

def update_tracker(args, target_detector, image, fps):
    new_faces = []
    allbboxes = []
    cls_idlist = []
    if args.is_split:
        # 首先将当前帧存入指定的临时文件夹中
        args.splitDir = os.path.join(args.output_dir,"splitDir")
        if not os.path.exists(args.splitDir):
            os.makedirs(args.splitDir)
        tmpdir = os.path.join(args.splitDir,"tmp")
        tmpdir2 = os.path.join(args.splitDir,"tmp_split")
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)
        if not os.path.exists(tmpdir2):
            os.makedirs(tmpdir2)
        cv2.imwrite(os.path.join(tmpdir,"tmp.png"),image)
        split = splitbase(tmpdir,
                          tmpdir2,
                          gap=args.gap,
                          subsize=args.subsize,
                          num_process=args.num_process)
        split.splitdata(1) # 1表示不放缩原图进行裁剪
        for filename in os.listdir(tmpdir2):
            filepath = os.path.join(tmpdir2,filename) # tmp__1__0___0
            yshfit = int(filename.split("___")[1].split(".")[0])
            xshfit = int(filename.split("__")[2])
            img = cv2.imread(filepath)
            _, bboxes = target_detector.detect(img) # 检测器推理图片
            for x1, y1, x2, y2, cls_id, conf in bboxes:
                cls_idlist.append(cls_id)
                x1 += xshfit
                y1 += yshfit
                x2 += xshfit
                y2 += yshfit
                allbboxes.append([x1,y1,x2,y2,conf.cpu()])
    else:
        _, bboxes = target_detector.detect(image) # 检测器推理图片
        for x1, y1, x2, y2, cls_id, conf in bboxes:
            cls_idlist.append(cls_id)
            allbboxes.append([x1,y1,x2,y2,conf.cpu()])
    allbboxes = np.array(allbboxes)
    keep = list(range(allbboxes.shape[0])) if not args.is_split else py_cpu_nms(allbboxes,thresh=args.iou_thresh)
    bboxes = allbboxes[keep]
    clss = []
    for idx in keep:
        clss.append(cls_idlist[idx])
    bbox_xywh = []
    confs = []
    for x1, y1, x2, y2, conf in bboxes:
        obj = [
            int((x1+x2)/2), int((y1+y2)/2),
            x2-x1, y2-y1
        ]
        bbox_xywh.append(obj)
        confs.append(conf)
        # clss.append(cls_id)

    xywhs = torch.Tensor(bbox_xywh)
    confss = torch.Tensor(confs)

    outputs = deepsort.update(xywhs, confss, clss, image)

    bboxes2draw = []
    face_bboxes = []
    current_ids = []
    for value in list(outputs):
        x1, y1, x2, y2, cls_, track_id = value
        bboxes2draw.append(
            (x1, y1, x2, y2, cls_, track_id)
        )
        current_ids.append(track_id)
        if cls_ == 'face':
            if not track_id in target_detector.faceTracker:
                target_detector.faceTracker[track_id] = 0
                face = image[y1:y2, x1:x2]
                new_faces.append((face, track_id))
            face_bboxes.append(
                (x1, y1, x2, y2)
            )

    # 计算每个目标的速度和加速度大小
    speed_list,speed_pro_list,speed_pro_change_list = get_speed_for_obj(bboxes2draw, fps)

    ids2delete = []
    for history_id in target_detector.faceTracker:
        if not history_id in current_ids:
            target_detector.faceTracker[history_id] -= 1
        if target_detector.faceTracker[history_id] < -5:
            ids2delete.append(history_id)

    for ids in ids2delete:
        target_detector.faceTracker.pop(ids)
        print('-[INFO] Delete track id:', ids)

    image = plot_bboxes(args, image, speed_list, speed_pro_list, speed_pro_change_list, bboxes2draw)

    return image, new_faces, face_bboxes
