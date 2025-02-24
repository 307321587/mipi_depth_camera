from .Ui_new import Ui_MainWindow

import rclpy
from rclpy.node import Node
from qt_image.msg import QtImage
from std_msgs.msg import String

import cv2
import numpy as np
from PyQt5.QtGui import QPixmap,QImage
from PyQt5.QtCore import pyqtSignal, QObject,QTimer
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication,QWidget,QTextEdit,QVBoxLayout,QPushButton
from rclpy.executors import MultiThreadedExecutor
import threading
import sys
import time

def letterbox_image(image, target_shape):
    """
    缩放图片, 填充短边
    :param image:            np.ndarray [H, W, C]
    :param target_shape:     tuple (H, W)
    :return:
    """
    image_h, image_w = image.shape[:2]
    target_h, target_w = target_shape
    # 获取缩放尺度, resize
    scale = min(float(target_h) / image_h, float(target_w) / image_w)
    new_h = int(image_h * scale)
    new_w = int(image_w * scale)
    image = cv2.resize(image, (new_w, new_h))
    canvas = np.zeros(shape=[target_h, target_w, 3], dtype=np.float32)
    canvas[:, :, :] = (128, 128, 128)
    start_h, start_w = (target_h - new_h) // 2, (target_w - new_w) // 2
    canvas[start_h:start_h + new_h, start_w:start_w + new_w, :] = image[:, :, :]
    canvas = canvas.astype(np.uint8)
    return canvas


def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (ct - int(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    return time_stamp

class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        # self.receiver = Subscriber()
        # self.receiver.image_show.connect(self.show_img)
        #在界面主线程中开启守护线程启动节点
        # self.thread_ros()
        self.node = None
        t_ = threading.Thread(target=self.thread_ros, args=())
        t_.setDaemon(True)            # 主线程崩掉，守护线程可以自己shutdown
        t_.start()

    def timer_callback(self):
        # rclpy.spin_once(node=self.receiver,timeout_sec=0.001)
        if(self.node.image_mat_left is None):
            return
        image_mat_resize=letterbox_image(self.node.image_mat_left,[self.lb_img_left.height(),self.lb_img_left.width()])
        image=QImage(image_mat_resize.data,image_mat_resize.shape[1],image_mat_resize.shape[0],image_mat_resize.shape[1]*3,QImage.Format_RGB888)
        pix=QPixmap.fromImage(image)
        self.lb_img_left.setPixmap(pix)

        image_mat_resize=letterbox_image(self.node.image_mat_right,[self.lb_img_right.height(),self.lb_img_right.width()])
        image=QImage(image_mat_resize.data,image_mat_resize.shape[1],image_mat_resize.shape[0],image_mat_resize.shape[1]*3,QImage.Format_RGB888)
        pix=QPixmap.fromImage(image)
        self.lb_img_right.setPixmap(pix)



    def thread_ros(self):
        
        self.node = Subscriber()
        self.node.img_show.connect(self.timer_callback)
        rclpy.spin(self.node.node)
        self.node.destroy_node()
        # rclpy.shutdown()
    
    def show_img(self,pix_map):
        self.lb_img.setPixmap(pix_map)

class Subscriber(QObject):
    img_show=pyqtSignal()
    def __init__(self):
        QObject.__init__(self)
        # super().__init__('subscriber')
        # print(threading.current_thread())
        self.node = Node('subscriber')
        self.img_subscription = self.node.create_subscription(QtImage,"qt_image",self.image_callback,200)        #image
        self.img_subscription 
        self.image_mat_left=None
        self.image_mat_right=None

    def image_callback(self, msg):
        global image_mat

        print(get_time_stamp())
        print('image process start...')
        array_left=np.array(bytearray(msg.serialize_image_1), dtype='uint8')
        array_right=np.array(bytearray(msg.serialize_image_2), dtype='uint8')
        self.image_mat_left = cv2.imdecode(array_left, cv2.IMREAD_COLOR)
        self.image_mat_right=cv2.imdecode(array_right, cv2.IMREAD_COLOR)
        self.image_mat_left=cv2.cvtColor(self.image_mat_left,cv2.COLOR_BGR2RGB)
        self.image_mat_right=cv2.cvtColor(self.image_mat_right,cv2.COLOR_BGR2RGB)
        self.img_show.emit()

def main(args=None):
    # print(threading.current_thread())
    rclpy.init(args=None)
    # rclpy.init(args=None)                     # 初始化python接口函数
    # node = Subscriber()
    # rclpy.spin(node)
    # node.destroy_node()
    # rclpy.shutdown()

    app=QApplication(sys.argv)
    hmi_ws=MainWindow()
    hmi_ws.show()
    # image_subscriber=Subscriber()
    # rcl_thread = threading.Thread(target=rclpy.spin, args=(image_subscriber,))  
    # rcl_thread.start()  
      
    # main_window = image_subscriber.main_window  
    # main_window.show() 
    # rclpy.shutdown() 
    sys.exit(app.exec_())