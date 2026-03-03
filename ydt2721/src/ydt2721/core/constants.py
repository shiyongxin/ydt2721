"""
物理常数和默认参数
"""

import math

# ========== 物理常数 ==========
LIGHT_SPEED = 3e8  # 光速, m/s
BOLTZMANN_CONSTANT_DB = -228.6  # 玻尔兹曼常数, dB(W/(K·Hz))
EARTH_RADIUS = 6378  # 地球半径, km
SATELLITE_ALTITUDE = 35786.6  # 卫星高度, km
BETA_RATIO = 6.62  # 同步轨道直径与地球直径比
AMBIENT_TEMP = 290  # 地面环境温度, K
MEDIUM_TEMP = 260  # 有效介质温度, K

# ========== 调制方式对照表 ==========
MODULATION_INDEX = {
    'BPSK': 1,
    'QPSK': 2,
    '8PSK': 3,
    '16QAM': 4,
}

# ========== 默认参数 ==========
DEFAULT_PARAMS = {
    'bo_i': 6.0,  # 卫星输入回退, dB
    'bo_o': 3.0,  # 卫星输出回退, dB
    'alpha1': 1.2,  # 载波噪声带宽因子
    'alpha2': 1.4,  # 载波分配带宽因子
    'efficiency': 0.65,  # 天线效率
    'antenna_noise_temp': 35,  # 天线噪声温度, K
    'receiver_noise_temp': 75,  # 接收机噪声温度, K
    'loss_at': 0.5,  # 发射站损耗, dB
    'loss_ar': 0.5,  # 接收站损耗, dB
    'feed_loss_tx': 1.5,  # 发射馈线损耗, dB
    'feed_loss_rx': 0.2,  # 接收馈线损耗, dB
    'hpa_bo': 3.0,  # 地球站功放回退, dB
    'system_margin': 2.0,  # 系统余量, dB
}

# ========== 频段定义 ==========
BANDS = {
    'C': {'uplink': (5.8, 6.4), 'downlink': (3.4, 4.2)},
    'Ku': {'uplink': (14.0, 14.5), 'downlink': (11.7, 12.75)},
}

# ========== 极化方式代码 ==========
POLARIZATION = {
    'V': '垂直极化',
    'H': '水平极化',
    'LH': '左旋圆极化',
    'RH': '右旋圆极化',
}
