from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *

import numpy as np
import struct

from widget_select import WidgetSelect
from widget_cg import WidgetCG
from widget_qd import WidgetQD
from widget_js import WidgetJS

class Game(QWidget):
    signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.data = b''

        self.signal.connect(self.slot)

        vbox = QVBoxLayout()
        self.ws = WidgetSelect(self.signal)
        self.wcg = WidgetCG(self.signal)
        self.wqd = WidgetQD(self.signal)
        self.wjs = WidgetJS(self.signal)
        vbox.addWidget(self.ws)
        vbox.addWidget(self.wcg)
        vbox.addWidget(self.wqd)
        vbox.addWidget(self.wjs)

        self.wcg.setVisible(False)
        self.wqd.setVisible(False)
        self.wjs.setVisible(False)

        self.setLayout(vbox)

        self.game_widget = None

    def set_serial(self, ser):
        self.ser = ser

    def receive_data(self, data):
        self.data += data
        if data == b'\n':
            s = self.data.decode('utf-8').strip()
            self.data = b''

            if s[0] == '(' and s[-1] == ')':
                s = s[1:-1]
                id, msg = s.split()
                id = int(id)
                print('game widget got:', id, msg)

                if self.game_widget is not None:
                    self.game_widget.add_udp_msg(id, msg)

    def slot(self, arg):
        if arg == 'cg':
            self.ws.setVisible(False)
            self.wcg.setVisible(True)
            self.game_widget = self.wcg
        elif arg == 'qd':
            self.ws.setVisible(False)
            self.wqd.setVisible(True)
            self.game_widget = self.wqd
        elif arg == 'js':
            self.ws.setVisible(False)
            self.wjs.setVisible(True)
            self.game_widget = self.wjs

    def btn_clicked(self, arg):
        pass