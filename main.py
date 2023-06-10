import sys

sys.path.append("c:\\users\\u1s1\\appdata\\local\\programs\\python\\python39\\lib\\site-packages")
import numpy as np
import socket
import threading
import struct
# import cv2
import time
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QPixmap, QImage
from ui.main_window import Ui_MainWindow
import byte2gray

mutex = threading.Lock()
atomic_bool = False

img_mutex = threading.Lock()
img_data = None

sum_has_run = False



def set_img_data(data):
    global img_data;
    img_mutex.acquire()
    img_data = data
    img_mutex.release()


def get_img_data():
    global img_data;
    img_mutex.acquire()
    ret_data = img_data
    img_mutex.release()
    return ret_data


def get_atomic_bool():
    ret = None
    mutex.acquire()
    global atomic_bool
    ret = atomic_bool
    mutex.release()
    return ret


def set_atomic_bool(val):
    global atomic_bool
    mutex.acquire()
    atomic_bool = val
    mutex.release()

def udp_init():
    if sum_has_run:
        # sum_has_run = True
        return
    else:
        # UDP IP与端口定义
        UDP_IP = '192.168.1.42'  # 监听所有可用网络接口
        UDP_PORT = 8080  # 监听的端口号
        # FPGA的UDP端口定义
        FPGA_UDP_IP = '192.168.1.11'
        FPGA_UDP_PORT = 8080
        # 创建UDP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 发送询问数据 0x 00020001
        send_ask = b'\x6c\x00\x02\x00\x01'
        # 发送数据 FPGA MAC: 0x00, 0x0a, 0x35, 0x00, 0x01, 0x02
        send_data = b'\x6c\x00\x02\x00\x02\x00\x0a\x35\x00\x01\x02\x01\x01'
        # send_data = input("请输入要发送的数据:")

        # 发送数据到指定的电脑上的指定程序中
        sock.bind((UDP_IP, UDP_PORT))
        sock.sendto(send_ask, (FPGA_UDP_IP, FPGA_UDP_PORT))
        time.sleep(0.1)
        data, addr = sock.recvfrom(65536)  # 使用二帧图片大小（1280 * 1448）的缓冲区大小接收数据
        # 解码图像数据
        ack = np.frombuffer((data), np.uint8)
        # print(ack[0])
        # print(ack[1])
        # print(ack[2])
        # print(ack[3])
        # print(ack[4])
        # ack_head_judge = ack[0] == b'\x6d' and ack[1] == b'\x00' and ack[2] == b'\x02' and ack[3] == b'\x00' and ack[4] == b'\x01'
        ack_head_judge = ack[0] == 109 and ack[1] == 0 and ack[2] == 2 and ack[3] == 0 and ack[4] == 1
        print(ack)
        while ~(ack_head_judge):
            print("Bad Ack! Send Ask Package again\r\n")
            time.sleep(0.1)
            sock.sendto(send_ask, (FPGA_UDP_IP, FPGA_UDP_PORT))
        else:
            print("Successfully Ack! Send Data_Req Package\r\n")
            sock.sendto(send_data, (FPGA_UDP_IP, FPGA_UDP_PORT))


## img_data: 1440 byte length (udp recv img data)
# 输入一个numpy数组img_data，长度为1440，包含1440byte的数据，img_data每6个数据作为一组，
# 将每6个数据的第7、6bit拼成一个byte，存在ch4数组中；将每6个数据的第5、4bit拼成一个byte，
# 存在ch3数组中；将每6个数据的第3、2bit拼成一个byte，存在ch2数组中；将每6个数据的第1、0bit拼成一个byte，存在ch1数组中



class ReceiveThread(threading.Thread, QObject):

    def __init__(self, port, signal):
        super().__init__()
        # # 创建一个 udp socket
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # # 绑定到指定的端口上
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.signals = signal
        self.ch1_frame_v = np.zeros((640 * 128, 1), np.uint8)
        self.ch2_frame_v = np.zeros((640 * 128, 1), np.uint8)
        self.ch3_frame_v = np.zeros((640 * 128, 1), np.uint8)
        self.ch4_frame_v = np.zeros((640 * 128, 1), np.uint8)

        self.index_past = 0

    def generateImgData(self):
        img_frame = np.zeros((720, 1280), dtype=np.uint16)
        img_gray8 = np.zeros((640, 512), np.uint8)


        # UDP IP与端口定义
        UDP_IP = '192.168.1.42'  # 监听所有可用网络接口
        UDP_PORT = 8080  # 监听的端口号
        # FPGA的UDP端口定义
        FPGA_UDP_IP = '192.168.1.11'
        FPGA_UDP_PORT = 8080
        # 创建UDP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # # 发送询问数据 0x 00020001
        # send_ask = b'\x6c\x00\x02\x00\x01'
        # 发送数据 FPGA MAC: 0x00, 0x0a, 0x35, 0x00, 0x01, 0x02
        send_data = b'\x6c\x00\x02\x00\x02\x00\x0a\x35\x00\x01\x02\x01\x01'
        # # send_data = input("请输入要发送的数据:")

        # 发送数据到指定的电脑上的指定程序中
        sock.bind((UDP_IP, UDP_PORT))
        # # 解码图像数据
        sock.sendto(send_data, (FPGA_UDP_IP, FPGA_UDP_PORT))
        # 确定当前包序号

        index = 0
        while index != 1:
            data, addr = sock.recvfrom(640 * 512 * 3)  # 使用二帧图片大小（1280 * 1448）的缓冲区大小接收数据
            if not data:
                break
            # 解码图像数据
            nparr = np.frombuffer((data), np.uint8)
            index = nparr[6] * 16 + nparr[7]

        # 接收数据
        for i in range(0, 512):
            data, addr = sock.recvfrom(2000)  # 使用二帧图片大小（1280 * 1448）的缓冲区大小接收数据
            if not data:
                break
            # 解码图像数据
            nparr = np.frombuffer((data), np.uint8)
            index = nparr[6] * 16 + nparr[7]
            print("第%d包的数据为：" % index)
            print(nparr)
            if len(nparr) != 1440+8:
                print ("异常的package中对应img_data的值")
                continue
            # elif nparr[6]*16 + nparr[7] != self.nparr_past[6]*16 + self.nparr_past[7] + 1:   # 如果存在丢包
            #     print("存在丢包")
            #     continue
            else:
                # index = nparr[6]*16 + nparr[7]
                # udp接收到的一包有效图像数据（1440byte）
                img_data = nparr[8:]
                ch1 = np.zeros(160, dtype=np.uint16)
                ch2 = np.zeros(160, dtype=np.uint16)
                ch3 = np.zeros(160, dtype=np.uint16)
                ch4 = np.zeros(160, dtype=np.uint16)
                # 转换为12bit的灰度值
                ch1, ch2, ch3, ch4 = byte2gray.pixel_gray_dec(img_data)
                ch1 = ch1 >> 4
                ch2 = ch2 >> 4
                ch3 = ch3 >> 4
                ch4 = ch4 >> 4

                ch1 = ch1.astype(np.uint8)
                ch2 = ch2.astype(np.uint8)
                ch3 = ch3.astype(np.uint8)
                ch4 = ch4.astype(np.uint8)

                self.ch1_frame_v[160*i:160*(i+1)] = ch1
                self.ch2_frame_v[160*i:160*(i+1)] = ch2
                self.ch3_frame_v[160*i:160*(i+1)] = ch3
                self.ch4_frame_v[160*i:160*(i+1)] = ch4

            # if nparr[6] * 16 + nparr[7] == 512:
            #     print("到帧头了 %d", nparr[6] * 16 + nparr[7])
            #     # 存储上次的udp接收数据
            #     self.index_past = 0
            #     break
            # # 存储上次的udp接收数据
            self.index_past = nparr[6] * 16 + nparr[7]

        ch1_frame_rsp = self.ch1_frame_v.reshape((640, 128)).astype(np.uint8)
        ch2_frame_rsp = self.ch2_frame_v.reshape((640, 128)).astype(np.uint8)
        ch3_frame_rsp = self.ch3_frame_v.reshape((640, 128)).astype(np.uint8)
        ch4_frame_rsp = self.ch4_frame_v.reshape((640, 128)).astype(np.uint8)
        gray_frame = np.hstack((ch1_frame_rsp, ch2_frame_rsp, ch3_frame_rsp, ch4_frame_rsp))
        h, w = 640, 512
        np_img = np.random.randint(0, 255, [h, w, 3], np.uint8)
        np_img[:, :, 0] = gray_frame
        np_img[:, :, 1] = gray_frame
        np_img[:, :, 2] = gray_frame
        set_img_data(np_img)
        return

    def run(self):
        while get_atomic_bool():
            time.sleep(0.1)
            self.generateImgData()

            img_bytes = bytearray(1)
            self.signals.run(img_bytes)


class QTypeSignal(QObject):
    # 定义一个信号
    sendmsg = pyqtSignal(bytearray)

    def __init__(self):

        super(QTypeSignal, self).__init__()
    def run(self, data):
        # 发射信号
        self.sendmsg.emit(data)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, signal, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.signal = signal
        self.signal.sendmsg.connect(self.setPixmap)
        self.udp_state = False

        self.udp_thread = ReceiveThread(5000, signal)
        self.pushButton_2.clicked.connect(self.udp_thread_manager)

    @pyqtSlot(bytearray)
    def setPixmap(self, data):
        img_data = get_img_data()
        img = QImage(img_data, img_data.shape[1], img_data.shape[0], img_data.shape[1] * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.label_2.setPixmap(pixmap)

    def udp_thread_manager(self):
        if not self.udp_state:
            self.udp_state = True
            set_atomic_bool(True)
            self.pushButton_2.setText("暂停")
            self.udp_thread.start()
        else:
            udp_state = False
            set_atomic_bool(False)
            self.pushButton_2.setText("开始")
            self.udp_thread.join()

    def closeEvent(self, event):
        self.udp_thread_manager()


if __name__ == "__main__":
    udp_init()

    app = QApplication(sys.argv)
    imageDataSignal = QTypeSignal()
    window = MainWindow(imageDataSignal)
    window.show()

    sys.exit(app.exec())