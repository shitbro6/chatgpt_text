from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2

from PIL import Image, ImageDraw, ImageFont
import serial
import serial.tools.list_ports

import time
import threading

import stop_threading as st

from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
import imutils
import dlib
from infer import *


class SerialPort:

    def __init__(self, port, buand):
        super(SerialPort, self).__init__()
        self.port = serial.Serial(port, buand)
        self.port.close()
        if not self.port.isOpen():
            self.port.open()

    def send_data(self, data):
        n = self.port.write((data).encode())
        return n


class FatigueWindow():
    def __init__(self) -> None:

        self.camera = cv2.VideoCapture(0)
        # 初始化帧计数器和眨眼总数
        self.COUNTER = 0
        self.TOTAL = 0
        # 初始化帧计数器和打哈欠总数
        self.mCOUNTER = 0
        self.mTOTAL = 0
        # 初始化帧计数器和点头总数
        self.hCOUNTER = 0
        self.hTOTAL = 0

        self.font = ("仿宋", 18)
        self.root = Tk()
        self.root.geometry("952x623")
        self.root.resizable(0, 0)
        self.root.title("欢迎使用工作状态监测软件-郭逸群-自动化-1902-17517206")

        self.panel = Label(self.root)  # initialize image panel
        self.panel.place(x=250, y=100)
        self.root.config(cursor="arrow")
        self.showframe()

        Label(self.root, text='串口选择：', font=("宋体", 12),
              anchor='w', justify='left').place(x=0, y=25, width=80, height=30)

        self.combox = ttk.Combobox(self.root)
        self.combox.place(x=80, y=25, width=130, height=30)
        self.combox["values"] = ["COM1"]
        self.combox.current(0)  # 选择第一个

        self.combox.bind("<<ComboboxSelected>>", self.selectevent)

        # 串口连接按钮
        self.link_btn = Button(self.root, text="串口连接", font=self.font, borderwidth=0,
                               bg="#bbded6", fg="#525252", relief="solid", cursor="hand2", command=self.uart_connect)
        self.link_btn.place(x=300, y=20, width=150, height=40)

        self.open_vid_btn = Button(self.root, text='打开摄像头', font=self.font, borderwidth=0,
                                   bg="#bbded6", fg="#525252", relief="solid", cursor="hand2")
        self.open_vid_btn.place(x=500, y=20, width=150, height=40)

        self.clear_btn = Button(self.root, text="状态清除", font=self.font, borderwidth=0,
                                bg="#8ac6d1", fg="#525252", relief="solid", cursor="hand2", command=self.take_snapshot)
        self.clear_btn.place(x=700, y=20, width=150, height=40)

        self.label_group = LabelFrame(self.root, text="状态信息实时监测", font=self.font,
                                      borderwidth=4, relief="solid").place(x=10, y=100, width=230, height=460)

        # 状态标签
        self.str_hCOUNTER = StringVar()
        self.str_mCOUNTER = StringVar()
        self.str_TOTAL = StringVar()
        self.str_mTOTAL = StringVar()
        self.str_hTOTAL = StringVar()
        self.str_MAR = StringVar()
        self.str_EAR = StringVar()

        self.str_hCOUNTER.set('打盹时间 ： ')
        self.str_mCOUNTER.set('打哈欠时间 ： ')
        self.str_TOTAL.set('眨眼次数 ： ')
        self.str_mTOTAL.set('哈欠次数 ： ')
        self.str_hTOTAL.set('点头次数 ： ')
        self.str_MAR.set('嘴部面积 ： ')
        self.str_EAR.set('眼部面积 ： ')

        self.label_1 = Label(self.label_group, textvariable=self.str_hCOUNTER, font=("宋体", 15),
                                 bg="#f5f4e8", fg="#000", anchor='w', justify='left').place(x=20, y=140, width=200, height=40)

        self.label_2 = Label(self.label_group, textvariable=self.str_mCOUNTER, font=("宋体", 15),
                                 bg="#f5f4e8", fg="#000", anchor='w', justify='left').place(x=20, y=190, width=200, height=40)

        self.label_3 = Label(self.label_group, textvariable=self.str_TOTAL, font=("宋体", 15),
                                 bg="#FFFBCB", fg="#000", anchor='w', justify='left').place(x=20, y=260, width=200, height=40)

        self.label_4 = Label(self.label_group, textvariable=self.str_mTOTAL, font=("宋体", 15),
                                 bg="#FFFBCB", fg="#000", anchor='w', justify='left').place(x=20, y=310, width=200, height=40)

        self.label_5 = Label(self.label_group, textvariable=self.str_hTOTAL, font=("宋体", 15),
                                 bg="#FFFBCB", fg="#000", anchor='w', justify='left').place(x=20, y=360, width=200, height=40)

        self.label_6 = Label(self.label_group, textvariable=self.str_MAR, font=("宋体", 15),
                                 bg="#c0ced5", fg="#000", anchor='w', justify='left').place(x=20, y=430, width=200, height=40)

        self.label_7 = Label(self.label_group, textvariable=self.str_EAR, font=("宋体", 15),
                                 bg="#c0ced5", fg="#000", anchor='w', justify='left').place(x=20, y=480, width=200, height=40)
        # 状态标签

        # self.setupUi()
        self.serialPort = ""

        self.mSerial = None

    def setupUi(self):
        self.get_com_list()
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.root.mainloop()

    def showframe(self):
        img = cv2.imread("images/1.jpg")
        current_image = Image.fromarray(img)  # 将图像转换成Image对象
        imgtk = ImageTk.PhotoImage(image=current_image)
        self.panel.imgtk = imgtk
        self.panel.config(image=imgtk)

    def get_com_list(self):  # 定义方法
        # print(self.combox.get()) #打印选中的值
        # print(int(time.time()))
        port_list = list(serial.tools.list_ports.comports())
        port_list_name = []
        # get all com
        if len(port_list) <= 0:
            print("未检测到串口,请插入设备！")
            return False
        else:
            for itms in port_list:
                port_list_name.append(itms.device)
        
            self.combox["values"] = port_list_name
            self.timer = threading.Timer(1, self.get_com_list)  # 每秒运行
            self.timer.start()  # 执行方法

    def selectevent(self, event):
        self.serialPort = str(self.combox.get())
        print(self.serialPort)

    def uart_connect(self):
        if self.serialPort != "":
            self.mSerial = SerialPort(self.serialPort, 9600)
        else:
            messagebox.showinfo(title='warning', message='请先选择串口!')

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        # st.stop_thread(self.timer)
        self.root.destroy()

    def take_snapshot(self):
        # video_loop()
        # global TOTAL, mTOTAL, hTOTAL
        self.TOTAL = 0
        self.mTOTAL = 0
        self.hTOTAL = 0


class FatigueInfer(FatigueWindow):
    def __init__(self) -> None:
        super().__init__()
        self.video_loop()

        self.setupUi()
        # # 定义常数
        # # 眼睛长宽比
        # # 闪烁阈值
        # self.COUNTEREYE_AR_THRESH = 0.2
        # self.COUNTEREYE_AR_CONSEC_FRAMES = 3
        # # 打哈欠长宽比
        # # 闪烁阈值
        # self.COUNTERMAR_THRESH = 0.5
        # self.COUNTERMOUTH_AR_CONSEC_FRAMES = 3
        # # 瞌睡点头
        # self.COUNTERHAR_THRESH = 0.3
        # self.COUNTERNOD_AR_CONSEC_FRAMES = 3


    def dete_tired(self, frame):
        # 第五步：进行循环，读取图片，并对图片做维度扩大，并进灰度化
        frame = imutils.resize(frame, width=660)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 第六步：使用detector(gray, 0) 进行脸部位置检测
        rects = detector(gray, 0)

        mar = ''
        ear = ''
        # global self.COUNTER, self.TOTAL, self.mCOUNTER, self.mTOTAL, self.hCOUNTER, self.hTOTAL

        # 第七步：循环脸部位置信息，使用predictor(gray, rect)获得脸部特征位置的信息
        for rect in rects:
            shape = predictor(gray, rect)

            # 第八步：将脸部特征信息转换为数组array的格式
            shape = face_utils.shape_to_np(shape)

            # 第九步：提取左眼和右眼坐标
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            # 嘴巴坐标
            mouth = shape[mStart:mEnd]

            # 第十步：构造函数计算左右眼的EAR值，使用平均值作为最终的EAR
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            # 打哈欠
            mar = mouth_aspect_ratio(mouth)

            # 第十一步：使用cv2.convexHull获得凸包位置，使用drawContours画出轮廓位置进行画图操作
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
            mouthHull = cv2.convexHull(mouth)
            cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)

            # 第十二步：进行画图操作，用矩形框标注人脸
            left = rect.left()
            top = rect.top()
            right = rect.right()
            bottom = rect.bottom()
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 1)

            '''
                分别计算左眼和右眼的评分求平均作为最终的评分，如果小于阈值，则加1，如果连续3次都小于阈值，则表示进行了一次眨眼活动
            '''
            # 第十三步：循环，满足条件的，眨眼次数+1
            if ear < EYE_AR_THRESH:  # 眼睛长宽比：0.2
                self.COUNTER += 1

            else:
                # 如果连续3次都小于阈值，则表示进行了一次眨眼活动
                if self.COUNTER >= EYE_AR_CONSEC_FRAMES:  # 阈值：3
                    self.TOTAL += 1
                # 重置眼帧计数器
                self.COUNTER = 0

            global EAR, MAR
            EAR = "{:.2f}".format(ear)
            MAR = "{:.2f}".format(mar)

            # 第十四步：进行画图操作，同时使用cv2.putText将眨眼次数进行显示
            cv2.putText(frame, "Faces: {}".format(len(rects)),
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "COUNTER: {}".format(self.COUNTER),
                        (150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "EAR: {:.2f}".format(
                ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            '''
                计算张嘴评分，如果小于阈值，则加1，如果连续3次都小于阈值，则表示打了一次哈欠，同一次哈欠大约在3帧
            '''
            # 同理，判断是否打哈欠
            if mar > MAR_THRESH:  # 张嘴阈值0.5
                self.mCOUNTER += 1
                cv2.putText(frame, "Yawning!", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)




            else:
                # 如果连续3次都小于阈值，则表示打了一次哈欠
                if self.mCOUNTER >= MOUTH_AR_CONSEC_FRAMES:  # 阈值：3
                    self.mTOTAL += 1
                # 重置嘴帧计数器
                self.mCOUNTER = 0
            cv2.putText(frame, "COUNTER: {}".format(self.mCOUNTER),
                        (150, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "MAR: {:.2f}".format(
                mar), (300, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            """
            瞌睡点头
            """
            # 第十五步：获取头部姿态
            reprojectdst, euler_angle = get_head_pose(shape)

            har = euler_angle[0, 0]  # 取pitch旋转角度
            if har > HAR_THRESH:  # 点头阈值0.3
                self.hCOUNTER += 1
            else:
                # 如果连续3次都小于阈值，则表示瞌睡点头一次
                if self.hCOUNTER >= NOD_AR_CONSEC_FRAMES:  # 阈值：3
                    self.hTOTAL += 1
                # 重置点头帧计数器
                self.hCOUNTER = 0

            # 绘制正方体12轴
            # for start, end in line_pairs:
            #     cv2.line(frame, reprojectdst[start], reprojectdst[end], (0, 0, 255))
            # 显示角度结果
            cv2.putText(frame, "X: " + "{:7.2f}".format(euler_angle[0, 0]), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                        (0, 255, 0), thickness=2)  # GREEN
            cv2.putText(frame, "Y: " + "{:7.2f}".format(euler_angle[1, 0]), (150, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                        (255, 0, 0), thickness=2)  # BLUE
            cv2.putText(frame, "Z: " + "{:7.2f}".format(euler_angle[2, 0]), (300, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                        (0, 0, 255), thickness=2)  # RED

            # 第十六步：进行画图操作，68个特征点标识
            for (x, y) in shape:
                cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

        # print('嘴巴实时长宽比:{:.2f} '.format(mar) + "\t是否张嘴：" + str([False, True][mar > MAR_THRESH]))
        # print('眼睛实时长宽比:{:.2f} '.format(ear) + "\t是否眨眼：" + str([False, True][self.COUNTER >= 1]))

        # 确定疲劳提示:眨眼50次，打哈欠15次，瞌睡点头15次
        # global mSerial
        if self.TOTAL >= 50 or self.mTOTAL >= 15 or self.hTOTAL >= 15:
            cv2.putText(frame, "SLEEP!!!", (100, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
            if self.mSerial != None:
                self.mSerial.send_data(data='1')

        return frame

    def video_loop(self):
        success, img = self.camera.read()  # 从摄像头读取照片
        if success:
            # print(img.shape)
            img = cv2.flip(img, 1)
            detect_result = self.dete_tired(img)
            cv2image = cv2.cvtColor(
                detect_result, cv2.COLOR_BGR2RGBA)  # 转换颜色从BGR到RGBA
            current_image = Image.fromarray(cv2image)  # 将图像转换成Image对象
            imgtk = ImageTk.PhotoImage(image=current_image)
            self.panel.imgtk = imgtk
            self.panel.config(image=imgtk)

            #################################### updata########################
            # global hCOUNTER, mCOUNTER, TOTAL, mTOTAL, hTOTAL
            global global_pitch, global_yaw, global_roll
            global EAR, MAR

            self.root.update()  # 不断更新
            self.root.after(10)

            self.str_hCOUNTER.set('打盹时间 : '+str(self.hCOUNTER))
            self.str_mCOUNTER.set('打哈欠时间 : ' + str(self.mCOUNTER))
            self.str_TOTAL.set('眨眼次数 : ' + str(self.TOTAL))
            self.str_mTOTAL.set('哈欠次数 : ' + str(self.mTOTAL))
            self.str_hTOTAL.set('点头次数 : ' + str(self.hTOTAL))
            self.str_MAR.set('嘴部面积 : ' + str(MAR))
            self.str_EAR.set('眼部面积 : ' + str(EAR))
            # Label(self.root, text='打盹时间:'+str(hCOUNTER), font=("黑体", 14), fg="red", width=12, height=2).place(x=10, y=570,
            #                                                                                                   anchor='nw')
            # Label(self.root, text='打哈欠时间:' + str(mCOUNTER), font=("黑体", 14), fg="red", width=12, height=2).place(x=140, y=570,
            #                                                                                                      anchor='nw')

            # Label(self.root, text='眨眼次数:' + str(TOTAL), font=("黑体", 14), fg="red", width=12, height=2).place(x=270, y=570,
            #                                                                                                  anchor='nw')
            # Label(self.root, text='哈欠次数:' + str(mTOTAL), font=("黑体", 14), fg="red", width=12, height=2).place(x=400, y=570,
            #                                                                                                   anchor='nw')
            # Label(self.root, text='点头次数:' + str(hTOTAL), font=("黑体", 14), fg="red", width=12, height=2).place(x=530, y=570,
            #                                                                                                   anchor='nw')

            # Label(self.root, text='嘴部面积 : ' + str(MAR), font=("黑体", 14),
            #       fg="red", width=20, height=2).place(x=130, y=610, anchor='nw')
            # Label(self.root, text='眼部面积 : ' + str(EAR), font=("黑体", 14),
            #       fg="red", width=20, height=2).place(x=320, y=610, anchor='nw')
            # Label(root, text='头部yaw:' + str(global_yaw), font=("黑体", 14), fg="red", width=12, height=2).place(x=140, y=600, anchor='nw')
            # Label(root, text='头部横滚角:' + str(global_roll), font=("黑体", 14), fg="red", width=12, height=2).place(x=270, y=600, anchor='nw')

            self.root.after(1, self.video_loop)







if __name__ == "__main__":
    # FA = FatigueWindow()
    fa = FatigueInfer()
