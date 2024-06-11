import cv2
import gxipy as gx
from gxipy.gxidef import *
from gxipy.gxidev import *


def main():
    # 初始化相机
    cam = gx.Camera()
    cam.open()
    cam.start_data_acquisition()

    # 创建 Opencv 窗口
    cv2.namedWindow("Preview", cv2.WINDOW_NORMAL)

    while True:
        # 从相机中获取一帧图像
        raw_image = cam.data_stream[0].get_image()
        if raw_image is None:
            print("获取图像失败")
            continue

        # 将 raw_image 转换为 OpenCV 格式
        numpy_image = raw_image.get_numpy_array()
        if numpy_image is None:
            continue

        # 显示图像
        cv2.imshow("Preview", numpy_image)

        # 检测按键输入，按下 ESC 键退出循环
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

    # 停止数据采集，关闭相机
    cam.stop_data_acquisition()
    cam.close()


if __name__ == "__main__":
    main()
