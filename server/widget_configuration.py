from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import serial.tools.list_ports

class ZcsComboBox(QComboBox):
    signal_show_popup = pyqtSignal()

    def __init__(self):
        super(ZcsComboBox, self).__init__()

    def showPopup(self):
        self.signal_show_popup.emit()
        super(ZcsComboBox, self).showPopup()

class Configuration(QWidget):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.ser = serial.Serial()
        self.init_ui()
        self.devices = {}
        self.update_uart_devices()
        # self.show()

    def init_ui(self):
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("串口号", maximumWidth = 40))
        self.combo_box_uart_id = ZcsComboBox()
        self.combo_box_uart_id.signal_show_popup.connect(self.slot)
        hbox1.addWidget(self.combo_box_uart_id)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("波特率", maximumWidth = 40))
        self.combo_box_baudrate = QComboBox()
        self.combo_box_baudrate.setEditable(True)
        # self.combo_box_baudrate.setValidator(QIntValidator(0, 9))
        self.combo_box_baudrate.addItems(('115200', '9600', '19200'))
        hbox2.addWidget(self.combo_box_baudrate)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel("数据位", maximumWidth = 40))
        self.combo_box_data_bits = QComboBox()
        self.combo_box_data_bits.addItem("8")
        hbox3.addWidget(self.combo_box_data_bits)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(QLabel("校验位", maximumWidth = 40))
        self.combo_box_check_bit = QComboBox()
        self.combo_box_check_bit.addItem("NONE")
        hbox4.addWidget(self.combo_box_check_bit)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(QLabel("停止位", maximumWidth = 40))
        self.combo_box_stop_bits = QComboBox()
        self.combo_box_stop_bits.addItem("1")
        hbox5.addWidget(self.combo_box_stop_bits)

        self.btn_turn_on_off = QPushButton("打开")
        self.btn_turn_on_off.clicked.connect(lambda: self.btn_clicked("turn_on_off"))

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox5)
        vbox.addWidget(self.btn_turn_on_off)

        self.setLayout(vbox)

    def update_uart_devices(self):
        self.devices = {}
        coms = list(serial.tools.list_ports.comports())
        for i in range(self.combo_box_uart_id.count()):
            self.combo_box_uart_id.removeItem(0)
        # print(coms)
        for com in coms:
            # print(com.device, com.description)
            self.combo_box_uart_id.addItem(com.description)
            self.devices[com.description] = com.device

    def btn_clicked(self, arg):
        if self.btn_turn_on_off.text() == "关闭":
            self.ser.close()
            self.btn_turn_on_off.setText("打开")
            self.combo_box_uart_id.setEnabled(True)
            self.combo_box_baudrate.setEnabled(True)
            self.combo_box_data_bits.setEnabled(True)
            self.combo_box_check_bit.setEnabled(True)
            self.combo_box_stop_bits.setEnabled(True)
            self.signal.emit(self.ser, 'CLOSE')
            return

        description = self.combo_box_uart_id.currentText()
        if description not in self.devices.keys():
            QMessageBox.warning(self, "错误", "%s not found" % description)
            return

        try:
            baudrate = int(self.combo_box_baudrate.currentText())
        except Exception as e:
            print(e)
            QMessageBox.warning(self, "错误", e.__str__())
            return

        try:
            self.ser.port = self.devices[description]
            self.ser.baudrate = baudrate
            self.ser.timeout = 0.2
            self.ser.open()
        except Exception as e:
            print(e)
            QMessageBox.warning(self, "错误", e.__str__())
            return

        self.btn_turn_on_off.setText("关闭")
        self.combo_box_uart_id.setEnabled(False)
        self.combo_box_baudrate.setEnabled(False)
        self.combo_box_data_bits.setEnabled(False)
        self.combo_box_check_bit.setEnabled(False)
        self.combo_box_stop_bits.setEnabled(False)
        self.signal.emit(self.ser, 'OPEN')

    def slot(self):
        self.update_uart_devices()
