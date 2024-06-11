import os
import sys
import time
import gxipy as gx
from PIL import Image

import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)
from PySide6 import QtWidgets

rgb_image = None
numpy_image = None
gray_frame = None

# 定义回调函数
def capture_callback_color(raw_image):
    global rgb_image, numpy_image, gray_frame
    print("Frame ID: %d   Height: %d   Width: %d"
          % (raw_image.get_frame_id(), raw_image.get_height(), raw_image.get_width()))

    # get RGB image from raw image
    # 设置图片参数
    rgb_image = raw_image.convert("RGB")
    rgb_image.brightness(75)
    rgb_image.contrast(-25)
    if rgb_image is None:
        print('Failed to convert RawImage to RGBImage')
        return

    # create numpy array with data from rgb image
    numpy_image = rgb_image.get_numpy_array()
    if numpy_image is None:
        print('Failed to get numpy array from RGBImage')
        return

    gray_frame = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2GRAY)

# 定义线程类：该类继承子Thread()
class Thread(QThread):
    updateFrame = Signal(QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.img = None
        self.scaled_img = None
        self.dev_info_list = None
        self.dev_num = None
        self.device_manager = None
        self.cam = None
        self.trained_file = None
        self.status = True
        self.cap = True

    def set_file(self, fname):
        self.trained_file = os.path.join(cv2.data.haarcascades, fname)

    def run(self):
        self.device_manager = gx.DeviceManager()
        self.dev_num, self.dev_info_list = self.device_manager.update_device_list()
        if self.dev_num == 0:
            print("Number of enumerated devices is 0")
            return
        self.cam = self.device_manager.open_device_by_index(1)
        self.cam.GainAuto = 1
        self.cam.BalanceWhiteAuto = 1
        self.cam.DeviceLinkThroughputLimitMode = 0
        self.cam.ExposureAuto = 1
        self.cam.AutoExposureTimeMax = 10000
        self.cam.UserSetSelector = 1
        self.data_stream = self.cam.data_stream[0]
        self.data_stream.register_capture_callback(capture_callback_color)
        self.cam.stream_on()
        time.sleep(0.1)
        while self.status:
            cascade = cv2.CascadeClassifier(self.trained_file)

            detections = cascade.detectMultiScale(gray_frame, scaleFactor=1.1,
                                                  minNeighbors=5, minSize=(30, 30))

            # Drawing green rectangle around the pattern
            for (x, y, w, h) in detections:
                pos_ori = (x, y)
                pos_end = (x + w, y + h)
                color = (0, 255, 0)
                cv2.rectangle(numpy_image, pos_ori, pos_end, color, 2)

            # Reading the image in RGB to display it
            color_frame = numpy_image
            # Creating and scaling QImage
            h, w, ch = color_frame.shape
            self.img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
            self.scaled_img = self.img.scaled(640, 480, Qt.KeepAspectRatio)

            # Emit signal
            self.updateFrame.emit(self.scaled_img)
            time.sleep(0.05)
        sys.exit(-1)

# 定义UI窗口界面
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Patterns detection")
        self.setGeometry(0, 0, 800, 500)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)
        self.menu_file.addAction(exit)

        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
                        triggered=qApp.aboutQt)
        self.menu_about.addAction(about)

        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setFixedSize(640, 480)

        # Model group
        self.group_model = QGroupBox("Trained model")
        self.group_model.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        model_layout = QHBoxLayout()

        self.combobox = QComboBox()
        for xml_file in os.listdir(cv2.data.haarcascades):
            if xml_file.endswith(".xml"):
                self.combobox.addItem(xml_file)

        model_layout.addWidget(QLabel("File:"), 10)
        model_layout.addWidget(self.combobox, 90)
        self.group_model.setLayout(model_layout)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.button1 = QPushButton("Start")
        self.button2 = QPushButton("Stop/Close")
        self.button1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.button2)
        buttons_layout.addWidget(self.button1)

        right_layout = QHBoxLayout()
        right_layout.addWidget(self.group_model, 1)
        right_layout.addLayout(buttons_layout, 1)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(right_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Initialize thread attribute
        self.th = None

        # Connections
        self.button1.clicked.connect(self.start)
        self.button2.clicked.connect(self.kill_thread)
        self.button2.setEnabled(False)
        self.combobox.currentTextChanged.connect(self.set_model)

    @Slot()
    def set_model(self, text):
        if self.th:
            self.th.set_file(text)
        else:
            print("Thread not started yet. Please start the thread first.")

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        self.button2.setEnabled(False)
        self.button1.setEnabled(True)
        self.th.status = False
        self.th.scaled_img.save("img.jpg")
        self.th.cam.stream_off()
        self.th.cam.data_stream[0].unregister_capture_callback()
        self.th.cam.close_device()
        self.th.quit()
        self.button2.setEnabled(True)
        print("over")

    @Slot()
    def start(self):
        print("Starting...")
        self.button2.setEnabled(True)
        self.button1.setEnabled(False)
        self.th = Thread(self)
        self.th.finished.connect(self.close)
        self.th.updateFrame.connect(self.setImage)
        self.th.set_file(self.combobox.currentText())
        self.th.start()

    @Slot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

# 主函数
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Window()
    w.show()
    print("正在运行")
    sys.exit(app.exec())
