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


class WidgetJS(QWidget):
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

        self.btn = QPushButton('竞赛开始')
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
            if self.btn.text() != '竞赛开始':
                return
            self.total = int(self.le_total.text())
            self.t = int(self.le_t.text())
            if self.t <= 1:
                print('显示时长最低2秒')
                return

            self.thread = ThreadShow(self.total, self.t, self.signal_done, self.signal_q)
            self.thread.start()
            self.signal.emit('js_start')

            self.ans = -1
            self.all_ans = {}
            self.q_num = -1

            self.label.setFont(self.font)

            self.label.setVisible(True)
            self.tableview.setVisible(False)
            self.btn.setText('进行中')
        
    def slot(self, arg):
        if arg == 'done':
            self.btn.setText('竞赛开始')
            self.label.setText('')

            self.label.setVisible(False)
            self.tableview.setVisible(True)

            self.model = QStandardItemModel(self.total+1, 7)
            self.model.setHorizontalHeaderLabels(['题目', 'ID0结果', 'ID1结果', 'ID2结果', 'ID0耗时', 'ID1耗时', 'ID2耗时'])
            self.tableview.setModel(self.model)

            aa = []
            for id in range(3):
                if id not in self.all_ans.keys():
                    aa.append({})
                else:
                    aa.append(self.all_ans[id])

            all_cost = [0, 0, 0]

            for i in range(self.total):
                self.model.setItem(i, 0, QStandardItem(f'题目{i+1}'))
                for id in range(3):
                    if i not in aa[id].keys():
                        self.model.setItem(i, 1 + id, QStandardItem('未作答'))
                        all_cost[id] += self.t - 1
                    else:
                        ans_real, ans, cost = aa[id][i]
                        if ans == ans_real:
                            self.model.setItem(i, 1 + id, QStandardItem('正确'))
                        else:
                            self.model.setItem(i, 1 + id, QStandardItem('错误'))
                        self.model.setItem(i, 4 + id, QStandardItem('%.1fs' % cost))
                        all_cost[id] += cost

            for id in range(3):
                print(all_cost[id] / self.total)
                self.model.setItem(self.total, 4 + id, QStandardItem('%.1f' % (all_cost[id] / self.total)))
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
            print(f'竞赛 注册 {id}')
        else:
            if self.state == '2':
                ans = int(msg)
                if id not in self.all_ans.keys():
                    self.all_ans[id] = {}
                cur_all_ans = self.all_ans[id]
                if self.q_num in cur_all_ans.keys():
                    print(f'already redceived ans for ID {id}')
                    return
                cost = time.time() - self.t_start
                cur_all_ans[self.q_num] = (self.ans, ans, cost)
                if self.ans == ans:
                    print(f'{id} {ans} correct')
                else:
                    print(f'{id} {ans} {self.ans} wrong')
            else:
                print(f'drop ans, state = {self.state}')