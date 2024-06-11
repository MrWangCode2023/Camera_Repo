import gxipy as gx
import cv2
import numpy as np
from datetime import datetime


def main():
    # 创建设备管理对象
    device_manager = gx.DeviceManager()

    # 枚举设备
    dev_num, dev_info_list = device_manager.update_device_list()

    if dev_num == 0:
        print("没有检测到设备")
        return

    # 打开设备
    cam = device_manager.open_device_by_sn(dev_info_list[0].get("sn"))

    # 设置连续采集模式
    cam.TriggerMode.set(gx.GxSwitchEntry.OFF)

    # 开始采集
    cam.stream_on()

    # 获取图像的宽度和高度
    width = cam.Width.get()
    height = cam.Height.get()

    # 定义视频编码格式并创建 VideoWriter 对象
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.avi")
    out = cv2.VideoWriter(output_filename, fourcc, 20.0, (width, height))

    print("正在录制视频。按 'q' 键停止录制。")

    while True:
        # 获取一幅图像
        raw_image = cam.data_stream[0].get_image()

        if raw_image is None:
            print("获取图像失败")
            continue

        if raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
            print("图像不完整")
            continue

        # 将图像数据转换为NumPy数组
        numpy_image = raw_image.get_numpy_array()

        if numpy_image is None:
            print("图像数据转换失败")
            continue

        # 检查图像的像素格式并进行相应的转换
        pixel_format = raw_image.get_pixel_format()

        if pixel_format == gx.GxPixelFormatEntry.RGB8:
            frame = numpy_image
        elif pixel_format == gx.GxPixelFormatEntry.BAYER_RG8:
            frame = cv2.cvtColor(numpy_image, cv2.COLOR_BAYER_RG2RGB)
        else:
            print(f"不支持的图像格式: {pixel_format}")
            continue

        # 写入视频文件
        out.write(frame)

        # 显示图像
        cv2.imshow('Frame', frame)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cam.stream_off()
    cam.close_device()
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
