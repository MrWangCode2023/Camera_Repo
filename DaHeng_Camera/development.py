import gxipy as gx
import sys
import time
from PIL import Image

device_manager = gx.DeviceManager()


####################### 枚举设备 #####################
dev_num, dev_info_list = device_manager.update_device_list()
# dev_num, dev_info_list = device_manager.update_all_device_list()
# dev_num, dev_info_list = device_manager.update_device_list_ex()
if dev_num == 0:
    print("没有检测到设备")
print("dev_num:", dev_num)
print("dev_info_list", dev_info_list)

###################### 打开设备 ######################
# 方法一:DeviceManager.open_device_by_sn(self, sn, access_mode=GxAccessMode.CONTROL)
# 获取设备基本信息列表
str_sn = dev_info_list[0].get("sn")
# 通过序列号打开设备
cam = device_manager.open_device_by_sn(str_sn)

# 方法二:DeviceManager.open_device_by_user_id(self,user_id,access_mode=GxAccessMode.CONTROL)
# 通过用户 ID 打开设备
# str_user_id = dev_info_list[0].get("user_id")
# cam = device_manager.open_device_by_user_id(str_user_id)


# 方法三:DeviceManager.open_device_by_index(self,index,access_mode=GxAccessMode.CONTROL)
# 通过索引打开设备
# str_index = dev_info_list[0].get("index")
# cam = device_manager.open_device_by_index(str_index)

# 方法四:DeviceManager.open_device_by_ip(ip, access_mode=GxAccessMode.CONTROL)
# 通过 ip 地址打开设备
# str_ip= dev_info_list[0].get("ip")
# cam = device_manager.open_device_by_ip(str_ip)

# 方法五:DeviceManager.open_device_by_mac(mac, access_mode=GxAccessMode.CONTROL)
# 通过 mac 地址打开设备
# str_mac = dev_info_list[0].get("mac")
# cam = device_manager.open_device_by_mac(str_mac)

###################### 关闭设备 ######################
# cam.close_device()

###################### 采集控制 ######################
# get_image 方式
# 开始采集
cam.stream_on()
# 获取流通道个数
# 如果 int_channel_num == 1，设备只有一个流通道，列表 data_stream 元素个数为 1
# 如果 int_channel_num > 1，设备有多个流通道，列表 data_stream 元素个数大于 1
# 目前千兆网相机、USB3.0、USB2.0 相机均不支持多流通道
# int_channel_num = cam.get_stream_channel_num()
# 获取数据
# num 为采集图片次数
num = 1
for i in range(num):
    # 打开第 0 通道数据流
    raw_image = cam.data_stream[0].get_image()
if raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
    print("incomplete frame")

# 停止采集
cam.stream_off()

###################### 回调方式 ######################
# 定义采集回调函数
def capture_callback(raw_image):
    if raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
        print("incomplete frame")
    # 注册回调
    cam.data_stream[0].register_capture_callback(capture_callback)
    # 开始采集
    cam.stream_on()
    # 等待一段时间，这段时间会自动调用采集回调函数
    time.sleep(1)
    # 停止采集
    cam.stream_off()
    # 注销回调
    cam.data_stream[0].unregister_capture_callback()

###################### 图像处理 ######################
# 1 图像格式转换
# 创建设备管理器
# 创建设备管理器
device_manager = gx.DeviceManager()
# 枚举设备
dev_num, dev_info_list = device_manager.update_device_list()
if dev_num == 0:
    sys.exit(1)

# 打开第一台设备
cam = device_manager.open_device_by_index(1)
# 开始采集
cam.stream_on()

# 获取 raw 图像，假设其像素格式为 BayerRG12
raw_image = cam.data_stream[0].get_image()
# 停止采集
cam.stream_off()

# 创建格式转换器
image_convert = device_manager.create_image_format_convert()
# 设置要转换的目标像素格式
image_convert.set_dest_format(gx.GxPixelFormatEntry.RGB8)
# 设置要转换的有效位
image_convert.set_valid_bits(gx.DxValidBit.BIT4_11)
# 创建转换后的图像缓存
buffer_out_size = image_convert.get_buffer_size_for_conversion(raw_image)
output_image_array = (c_ubyte * buffer_out_size)()
output_image = addressof(output_image_array)
# 转换像素格式成 RGB8
image_convert.convert(raw_image, output_image, buffer_out_size, False)
if output_image is None:
    pass  # replace 'continue' with 'pass' as 'continue' is not valid here

# 创建 numpy 数组
numpy_image = np.frombuffer(output_image_array, dtype=np.ubyte).reshape(raw_image.get_height(), raw_image.get_width(), 3)
if numpy_image is None:
    pass  # replace 'continue' with 'pass' as 'continue' is not valid here


# 2 图像质量提升
import gxipy as gx
from ctypes import c_ubyte, addressof

# 假设 remote_device_feature 和 image_config 已经初始化
# 假设 raw_image 已经获取

# 假设对像素格式为 RGB8 的图像做图像质量提升
# 创建设备管理器
device_manager = gx.DeviceManager()
# 打开第一台设备
cam = device_manager.open_device_by_index(1)
# 创建图像质量提升处理对象
image_process = device_manager.create_image_process()
# 创建图像质量提升参数配置对象
image_config = cam.create_image_process_config()
# 创建属性控制器
remote_device_feature = cam.get_remote_device_feature_control()
#获取对比度、Gamma 参数

# 检查和获取 GammaParam 参数
if remote_device_feature.is_readable("GammaParam"):
    gamma_param = remote_device_feature.get_float_feature("GammaParam").get()
else:
    gamma_param = 0.1

# 检查和获取 ContrastParam 参数
if remote_device_feature.is_readable("ContrastParam"):
    contrast_param = remote_device_feature.get_int_feature("ContrastParam").get()
else:
    contrast_param = 0

# 设置对比度和 Gamma 参数
image_config.set_contrast_param(gamma_param)
image_config.set_gamma_param(contrast_param)

# 创建图像质量提升后存放的 Buffer 缓存
output_image_array = (c_ubyte * raw_image.frame_data.image_size)()
output_image = addressof(output_image_array)

# 采集获取图像 raw_image，调用图像处理接口实现质量提升
image_process.image_improvement(raw_image, output_image, image_config)

# 3 图像显示和保存
# 显示并保存获得的黑白图片
image = Image.fromarray(numpy_image, 'L')
image.show()
image.save("acquisition_mono_image.jpg")

# 彩色相机
# 显示并保存获得的彩色图片
image = Image.fromarray(numpy_image, 'RGB')
image.show()
image.save("acquisition_RGB_image.jpg")

###################### 相机控制 ######################
# 1 属性参数访问类型

# 获取远程设备特性控制器
remote_device_feature = cam.get_remote_device_feature_control()

# 查询 "PixelFormat" 特性是否已实现
is_implemented = remote_device_feature.is_implemented("PixelFormat")
if is_implemented:
    # 查询 "PixelFormat" 特性是否可写
    is_writable = remote_device_feature.is_writable("PixelFormat")
    if is_writable:
        # 设置像素格式为 "Mono8"
        remote_device_feature.get_enum_feature("PixelFormat").set("Mono8")

        # 查询 "PixelFormat" 特性是否可读
        is_readable = remote_device_feature.is_readable("PixelFormat")
        if is_readable:
            # 获取并打印像素格式
            value, str_value = remote_device_feature.get_enum_feature("PixelFormat").get()
            print(str_value)

# 2 属性控制种类
# 属性控制分如下几种。
DeviceManagerstr = gx.DeviceManager()

# 枚举设备
dev_num, dev_info_list = device_manager.update_device_list()
if dev_num == 0:
    print("No devices found")
    sys.exit(1)

# 打开第一台设备
Device = device_manager.open_device_by_index(1)

Device.get_local_device_feature_control() # 获取本地备属性控制器
Device.get_remote_device_feature_control() # 获取远端设备属性控制器
DeviceManagetr.get_interface().get_feature_control() # 获取 interface 属性控制器
Device.get_stream().get_feature_control() # 获取流属性控制器