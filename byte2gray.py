import numpy as np

# 将8bit ADC输出的数据转换为像素12bit的灰度值
def convert_data(img_data):
    img_data = img_data.reshape((160, 6)).astype(np.uint16)
    ch1 = np.zeros((160,1), dtype=np.uint16)
    ch2 = np.zeros((160,1), dtype=np.uint16)
    ch3 = np.zeros((160,1), dtype=np.uint16)
    ch4 = np.zeros((160,1), dtype=np.uint16)
    ch1[:, 0] = (img_data[:, 0] & 0x03) << 10 | (img_data[:, 1] & 0x03) << 8 | (
                 img_data[:, 2] & 0x03) << 6 | (img_data[:, 3] & 0x03) << 4 | (img_data[:, 4] & 0x03) << 2 | (
                          img_data[:, 5] & 0x03)
    ch2[:, 0] = (img_data[:, 0] & 0x0C) << 8 | (img_data[:, 1] & 0x0C) << 6 | (img_data[:, 2] & 0x0C) << 4 | (
             img_data[:, 3] & 0x0C) << 2 | (img_data[:, 4] & 0x0C) | (img_data[:, 5] & 0x0C) >> 2
    ch3[:, 0] = (img_data[:, 0] & 0x30) << 6 | (img_data[:, 1] & 0x30) << 4 | (img_data[:, 2] & 0x30) << 2 | (
             img_data[:, 3] & 0x30) | (img_data[:, 4] & 0x30) >> 2 | (img_data[:, 5] & 0x30) >> 4
    ch4[:, 0] = (img_data[:, 0] & 0xC0) << 4 | (img_data[:, 1] & 0xC0) << 2| (img_data[:, 2] & 0xC0) | (
                img_data[:, 3] & 0xC0) >> 2 | (img_data[:, 4] & 0xC0) >> 4 | (img_data[:, 5] & 0xC0) >> 6

    return ch1.astype(np.uint16), ch2.astype(np.uint16), ch3.astype(np.uint16), ch4.astype(np.uint16)


## 将3byte的rgb888转换为2byte的rgb565数据
def convert_rgb888_to_rgb565(rgb888):
    # 分离RGB888的R、G、B分量
    red = rgb888[0]
    green = rgb888[1]
    blue = rgb888[2]

    # 将R、G、B分量转换成RGB565格式
    # R分量占5bit，将8bit的R分量右移3位后取低5位
    r = (red >> 3) & 0x1f
    # G分量占6bit，将8bit的G分量右移2位后取低6位
    g = (green >> 2) & 0x3f
    # B分量占5bit，将8bit的B分量右移3位后取低5位
    b = (blue >> 3) & 0x1f

    # 将RGB565的R、G、B分量合并成一个16位数
    # R分量左移11位，G分量左移5位，B分量不移位
    rgb565 = (r << 11) | (g << 5) | b

    # 将16位的RGB565格式的数据转换成2个8位的数表示
    # 用高8位表示高字节，用低8位表示低字节
    high_byte = (rgb565 >> 8) & 0xff
    low_byte = rgb565 & 0xff

    # 返回2个8位数的元组
    return (high_byte, low_byte)


## 这里udp_data为udp包中有效的图像数据，要求是1440byte的长度
def pixel_gray_dec(udp_data):
    udp_rgb565 = np.zeros((480, 2), dtype=np.uint16)
    udp_data = udp_data.reshape((480, 3)).astype(np.uint16)
    # 160来源：1440/1.5（RGB888转RGB565）/6（每6byte代表4个像素）
    ch1 = np.zeros((160,1), dtype=np.uint16)
    ch2 = np.zeros((160,1), dtype=np.uint16)
    ch3 = np.zeros((160,1), dtype=np.uint16)
    ch4 = np.zeros((160,1), dtype=np.uint16)
    # rgb888转换成rgb565
    for i in range(0, 480):
        udp_rgb565[i, :] = convert_rgb888_to_rgb565(udp_data[i, :])

    # udp_rgb565中的数据为一个udp包中的图像有效数据（1440 * 2/3 = 960 byte）
    udp_rgb565 = udp_rgb565.reshape((960, 1)).astype(np.uint8)
    [ch1, ch2, ch3, ch4] = convert_data(udp_rgb565)
    return ch1, ch2, ch3, ch4

########################### FUNCTION TEST #############################
# 160来源：1440/1.5（RGB888转RGB565）/6（每6byte代表4个像素）
ch1 = np.zeros((160, 1), dtype=np.uint16)
ch2 = np.zeros((160, 1), dtype=np.uint16)
ch3 = np.zeros((160, 1), dtype=np.uint16)
ch4 = np.zeros((160, 1), dtype=np.uint16)
# udp_rgb565 = np.zeros((480, 2), dtype=np.uint16)

# 创建一个长度为1440的随机numpy数组
udp_data = 8*np.ones(1440, dtype=np.uint8)
# 调用convert_data函数将数据转换为4个数组
udp_rgb565 = np.zeros((480, 2), dtype=np.uint16)
# ch1, ch2, ch3, ch4 = convert_data(img_data)
# [ch1, ch2, ch3, ch4] = convert_data(udp_data)
# rgb转换测试
udp_data = udp_data.reshape((480, 3)).astype(np.uint16)

for i in range(0, 480):
    udp_rgb565[i, :] = convert_rgb888_to_rgb565(udp_data[i, :])


# udp_rgb565中的数据为一个udp包中的图像有效数据（1440 * 2/3 = 960 byte）
udp_rgb565 = udp_rgb565.reshape((960, 1)).astype(np.uint8)
[ch1, ch2, ch3, ch4] = convert_data(udp_rgb565)
ch1 = ch1 >> 4
ch2 = ch2 >> 4
ch3 = ch3 >> 4
ch4 = ch4 >> 4


ch1 = ch1.astype(np.uint8)
ch2 = ch2.astype(np.uint8)
ch3 = ch3.astype(np.uint8)
ch4 = ch4.astype(np.uint8)


# 输出结果
print("ch1:", ch1)
print("ch2:", ch2)
print("ch3:", ch3)
print("ch4:", ch4)

print ('shape', ch4.shape)

# print("udp_rgb565:", udp_rgb565)