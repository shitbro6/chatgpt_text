from os import X_OK
import sys
import numpy as np
import serial
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import widget_configuration as wc
import widget_game as wg

class ThreadInteraction(QThread):
    def __init__(self, tab_widget):
        super(ThreadInteraction, self).__init__()
        # self.signal = signal
        self.tab_widget = tab_widget
        self.running = False
    
    def set_serial(self, ser):
        print('set_serial:', ser)
        self.ser = ser

    def run(self):
        self.running = True
        while True:
            try:
                recv = self.ser.read(1)
                # hex_txt = str(recv, encoding='utf-8')
                # print(recv, len(recv), type(recv), hex_txt)
            except Exception as e:
                print(e, '. interaction done')
                break

            if len(recv) <= 0:
                continue
            # for b in recv:
            #     print(chr(b), end='')
            # print()
            cur_w = self.tab_widget.currentWidget()
            if not isinstance(cur_w, wc.Configuration):
                cur_w.receive_data(recv)
        self.running = False
        # self.ser.close()

class Matrix(QMainWindow):
    signal = pyqtSignal(serial.Serial, str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.signal.connect(self.slot)
        self.thread = ThreadInteraction(self.tab_widget)
        self.show()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        tab_uart_configuration = wc.Configuration(self.signal)
        self.tab_widget.addTab(tab_uart_configuration, '设置')
        self.tab_monitor = wg.Game()
        self.tab_widget.addTab(self.tab_monitor, '游戏')

        self.setCentralWidget(self.tab_widget)

        self.resize(820, 900)  # resize()方法调整了widget组件的大小。它现在是600px宽，400px高。
        self.move(400, 50)  # move()方法移动widget组件到一个位置，这个位置是屏幕上x=500,y=200的坐标。
        self.setWindowTitle('math game')  # 设置了窗口的标题。这个标题显示在标题栏中。

    def slot(self, ser, action):
        if self.thread.running:
            QMessageBox.warning(self, '警告', '上一次交互线程尚未退出')
            return
        self.tab_monitor.set_serial(ser)
        self.thread.set_serial(ser)
        self.thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tm = Matrix()
    sys.exit(app.exec_())
    # modify_img('./2021-11-27_14-16-25.png')
