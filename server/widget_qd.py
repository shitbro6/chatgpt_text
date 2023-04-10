from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *
import time

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


class WidgetQD(QWidget):
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

        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel('显示时长：'))
        self.le_t = QLineEdit('2')
        hbox3.addWidget(self.le_t)
        hbox3.addWidget(QLabel('秒'))

        self.btn = QPushButton('抢答开始')
        self.btn.clicked.connect(lambda: self.btn_clicked('start'))

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.btn)
        vbox.addStretch()

        ##############################
        self.font = QFont()
        self.font.setPointSize(200)

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

        self.tableview = QTableView()
        vbox.addWidget(self.tableview)
        vbox.addStretch()

        self.tableview.setVisible(False)

        self.setLayout(vbox)

    def btn_clicked(self, arg):
        if arg == 'start':
            if self.btn.text() != '抢答开始':
                return
            self.total = int(self.le_total.text())
            self.t = int(self.le_t.text())
            if self.t <= 1:
                print('显示时长最低2秒')
                return

            self.thread = ThreadShow(self.total, self.t, self.signal_done, self.signal_q)
            self.thread.start()
            self.signal.emit('qd_start')

            self.ans = -1
            self.all_ans = {}
            self.q_num = -1

            self.label.setFont(self.font)

            self.label.setVisible(True)
            self.tableview.setVisible(False)
            self.btn.setText('进行中')
        
    def slot(self, arg):
        if arg == 'done':
            self.btn.setText('抢答开始')
            self.label.setText('')

            self.label.setVisible(False)
            self.tableview.setVisible(True)

            self.model = QStandardItemModel(self.total, 4)
            self.model.setHorizontalHeaderLabels(['题目', '作答ID', '结果', '耗时'])
            self.tableview.setModel(self.model)

            for i in range(self.total):
                self.model.setItem(i, 0, QStandardItem(f'题目{i+1}'))
                if i not in self.all_ans.keys():
                    self.model.setItem(i, 1, QStandardItem('-'))
                else:
                    id, ans_real, ans, cost = self.all_ans[i]
                    self.model.setItem(i, 1, QStandardItem(f'{id}'))
                    if ans == ans_real:
                        self.model.setItem(i, 2, QStandardItem('正确'))
                    else:
                        self.model.setItem(i, 2, QStandardItem('错误'))
                    self.model.setItem(i, 3, QStandardItem('%.1fs' % cost))
            print(self.all_ans)

    def slot_q(self, q, ans, s, q_num):
        if s == '1':
            self.label.setPalette(self.pe1)
            self.label.setText(q)
            self.ans = ans
            self.q_num = q_num
        elif s == '2':
            self.t_start = time.time()
            self.label.setPalette(self.pe2)
        elif s == '3':
            pass

        self.state = s

    def add_udp_msg(self, id, msg):
        if msg == 'R':
            print(f'抢答 注册 {id}')
        else:
            if self.state == '2':
                ans = int(msg)
                if self.q_num in self.all_ans.keys():
                    print('already redceived ans')
                    return
                cost = time.time() - self.t_start
                self.all_ans[self.q_num] = (id, self.ans, ans, cost)
                if self.ans == ans:
                    print(f'{id} {ans} correct')
                else:
                    print(f'{id} {ans} {self.ans} wrong')
            else:
                print(f'drop ans, state = {self.state}')