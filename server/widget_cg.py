from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *

from utils import gen_q

class ThreadShow(QThread):
    def __init__(self, total, t, signal_done, signal_q):
        super().__init__()

        self.total = total
        self.t = t
        self.signal_done = signal_done
        self.signal_q = signal_q

    def run(self):
        for i in range(self.total):
            q, ans = gen_q()
            self.signal_q.emit(q, ans, '1', i)
            self.sleep(1)
            self.signal_q.emit(q, ans, '2', i)
            self.sleep(self.t-1)
            self.signal_q.emit(q, ans, '3', i)
        self.signal_done.emit('done')


class WidgetCG(QWidget):
    signal_done = pyqtSignal(str)
    signal_q = pyqtSignal(str, int, str, int)

    def __init__(self, signal):
        super().__init__()

        self.signal = signal
        self.signal_done.connect(self.slot)
        self.signal_q.connect(self.slot_q)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('题目数量：'))
        self.le_total = QLineEdit('10')
        hbox.addWidget(self.le_total)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('过关数量：'))
        self.le_thres = QLineEdit('10')
        hbox2.addWidget(self.le_thres)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel('显示时长：'))
        self.le_t = QLineEdit('2')
        hbox3.addWidget(self.le_t)
        hbox3.addWidget(QLabel('秒'))

        self.btn = QPushButton('闯关开始')
        self.btn.clicked.connect(lambda: self.btn_clicked('start'))

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.btn)
        vbox.addStretch()

        ##############################
        self.font = QFont()
        self.font.setPointSize(200)
        self.font2 = QFont()
        self.font2.setPointSize(60)

        self.pe1 = QPalette()
        self.pe1.setColor(QPalette.ColorRole.WindowText, QColor(0xff0000))

        self.pe2 = QPalette()
        self.pe2.setColor(QPalette.ColorRole.WindowText, QColor(0x000000))

        self.label = QLabel('')
        self.label.setFont(self.font)
        self.label.setPalette(self.pe1)

        self.state = '1'
        self.ans = -1
        self.all_ans = {}
        self.q_num = -1
        ######################################

        vbox.addWidget(self.label)
        vbox.addStretch()

        self.setLayout(vbox)

    def btn_clicked(self, arg):
        if arg == 'start':
            if self.btn.text() != '闯关开始':
                return
            self.total = int(self.le_total.text())
            self.thres = int(self.le_thres.text())
            self.t = int(self.le_t.text())
            if self.thres > self.total:
                print('错误配置')
                return
            if self.t <= 1:
                print('显示时长最低2秒')
                return

            self.thread = ThreadShow(self.total, self.t, self.signal_done, self.signal_q)
            self.thread.start()
            self.signal.emit('cg_start')

            self.ans = -1
            self.all_ans = {}
            self.q_num = -1

            self.label.setFont(self.font)
            self.btn.setText('进行中')
        
    def slot(self, arg):
        if arg == 'done':
            self.btn.setText('闯关开始')
            # self.label.setText('')

            self.label.setFont(self.font2)
            c, w, n = 0, 0, 0
            for i in range(self.total):
                if i not in self.all_ans.keys():
                    n += 1
                else:
                    if self.all_ans[i][0] == self.all_ans[i][1]:
                        c += 1
                    else:
                        w += 1
            ret = '成功' if c >= self.thres else '失败'
            self.label.setText(f'闯关{ret}!!\r\n正确{c}题，错误{w}题，未作答{n}题')
            print(self.all_ans)

    def slot_q(self, q, ans, s, q_num):
        if s == '1':
            self.label.setPalette(self.pe1)
            self.label.setText(q)
            self.ans = ans
            self.q_num = q_num
        elif s == '2':
            self.label.setPalette(self.pe2)
        elif s == '3':
            pass

        self.state = s

    def add_udp_msg(self, id, msg):
        if id != 0:
            print('drop, id != 0')
            return
        if msg == 'R':
            print(f'闯关 注册 {id}')
        else:
            if self.state == '2':
                ans = int(msg)
                if self.q_num in self.all_ans.keys():
                    print('already redceived ans')
                    return
                self.all_ans[self.q_num] = (self.ans, ans)
                if self.ans == ans:
                    print(f'{id} {ans} correct')
                else:
                    print(f'{id} {ans} {self.ans} wrong')
            else:
                print(f'drop ans, state = {self.state}')