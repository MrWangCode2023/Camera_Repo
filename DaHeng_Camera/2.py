import gxipy as gx
import cv2
import numpy as np

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

    print("按 'q' 键退出查看。")

    # 创建一个窗口，并设置为全屏模式
    cv2.namedWindow('Frame', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

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

        # 获取屏幕分辨率
        screen_width = cv2.getWindowImageRect('Frame')[2]
        screen_height = cv2.getWindowImageRect('Frame')[3]

        # 计算缩放比例
        h_ratio = screen_height / frame.shape[0]
        w_ratio = screen_width / frame.shape[1]
        scale = min(h_ratio, w_ratio)

        # 保持比例调整图像大小
        new_size = (int(frame.shape[1] * scale), int(frame.shape[0] * scale))
        resized_frame = cv2.resize(frame, new_size)

        # 创建一个黑色画布用于显示
        canvas = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
        canvas[:resized_frame.shape[0], :resized_frame.shape[1]] = resized_frame

        # 显示图像
        cv2.imshow('Frame', canvas)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cam.stream_off()
    cam.close_device()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
