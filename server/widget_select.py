from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *

class WidgetSelect(QWidget):
    def __init__(self, signal):
        super().__init__()

        self.signal = signal

        font = QFont()
        font.setPointSize(50)

        btn_cg = QPushButton('闯关模式')
        btn_cg.setMinimumHeight(100)
        btn_cg.setFont(font)
        btn_cg.clicked.connect(lambda: self.btn_clicked("cg"))

        btn_qd = QPushButton('抢答模式')
        btn_qd.setMinimumHeight(100)
        btn_qd.setFont(font)
        btn_qd.clicked.connect(lambda: self.btn_clicked("qd"))

        btn_js = QPushButton('竞赛模式')
        btn_js.setMinimumHeight(100)
        btn_js.setFont(font)
        btn_js.clicked.connect(lambda: self.btn_clicked("js"))

        vbox = QVBoxLayout()
        vbox.addWidget(btn_cg)
        vbox.addWidget(btn_qd)
        vbox.addWidget(btn_js)

        self.setLayout(vbox)

    def btn_clicked(self, arg):
        self.signal.emit(arg)