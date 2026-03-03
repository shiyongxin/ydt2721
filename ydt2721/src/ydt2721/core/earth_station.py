"""
M04: 地球站参数计算模块
"""

import math
from .constants import LIGHT_SPEED, AMBIENT_TEMP


def calculate_antenna_gain(diameter: float, wavelength: float,
                           efficiency: float) -> float:
    """
    计算天线增益

    G_e = 20 × lg(π × D / λ) + 10 × lg(η)

    Args:
        diameter: 天线口径, 单位m
        wavelength: 波长, 单位m
        efficiency: 天线效率 (0-1之间)

    Returns:
        天线增益, 单位dBi

    Example:
        >>> calculate_antenna_gain(4.5, 0.021, 0.65)
        54.67
    """
    term1 = 20 * math.log10(math.pi * diameter / wavelength)
    term2 = 10 * math.log10(efficiency)
    return term1 + term2


def calculate_antenna_pointing(es_lat: float, es_lon: float,
                                sat_lon: float) -> tuple:
    """
    计算天线指向角度

    Args:
        es_lat: 地球站纬度, 单位度 (北纬为正)
        es_lon: 地球站经度, 单位度 (东经为正)
        sat_lon: 卫星经度, 单位度 (东经为正)

    Returns:
        (仰角, 方位角), 单位度

    Example:
        >>> calculate_antenna_pointing(39.92, 116.45, 110.5)
        (43.42, 189.22)
    """
    # 转换为弧度
    lat_rad = math.radians(es_lat)
    lon_diff_rad = math.radians(es_lon - sat_lon)

    # 计算仰角
    cos_psi = math.cos(lat_rad) * math.cos(lon_diff_rad)
    numerator = cos_psi - 0.151
    denominator = math.sqrt(max(0, 1 - cos_psi ** 2))

    if abs(denominator) < 1e-10:
        elevation = 0
    else:
        elevation_rad = math.atan(numerator / denominator)
        elevation = math.degrees(elevation_rad)

    # 计算方位角
    if abs(math.sin(lat_rad)) < 1e-10:
        # 赤道上的地球站
        azimuth = 90 if es_lon > sat_lon else 270
    else:
        az_rad = math.atan(math.tan(lon_diff_rad) / math.sin(lat_rad))
        azimuth = math.degrees(az_rad)

        # 根据纬度和经度差调整方位角
        if es_lat > 0:
            azimuth = 180 + azimuth
        elif es_lon - sat_lon > 0:
            azimuth = 360 + azimuth

        # 归一化到0-360度
        azimuth = azimuth % 360

    return elevation, azimuth


def calculate_satellite_distance(es_lat: float, es_lon: float,
                                  sat_lon: float) -> float:
    """
    计算地球站与卫星之间的距离

    d = 42644 × √(1 - 0.2954 × cos(ψ))
    cos(ψ) = cos(θ₁) × cos(φ)

    Args:
        es_lat: 地球站纬度, 单位度
        es_lon: 地球站经度, 单位度
        sat_lon: 卫星经度, 单位度

    Returns:
        距离, 单位km

    Example:
        >>> calculate_satellite_distance(39.92, 116.45, 110.5)
        37533.2
    """
    lat_rad = math.radians(es_lat)
    lon_diff_rad = math.radians(abs(es_lon - sat_lon))

    cos_psi = math.cos(lat_rad) * math.cos(lon_diff_rad)
    distance = 42644 * math.sqrt(max(0, 1 - 0.2954 * cos_psi))

    return distance


def calculate_earth_station_gt(antenna_gain: float, feed_loss: float,
                                ant_noise_temp: float, receiver_noise_temp: float,
                                ambient_temp: float = AMBIENT_TEMP) -> float:
    """
    计算地球站G/T值

    T_es = T_a/L_fr + (1 - 1/L_fr) × T₀ + T_er
    G/T_e = G_er - L_fr - 10 × lg(T_es)

    Args:
        antenna_gain: 天线增益, 单位dBi
        feed_loss: 馈线损耗, 单位dB
        ant_noise_temp: 天线噪声温度, 单位K
        receiver_noise_temp: 接收机噪声温度, 单位K
        ambient_temp: 环境温度, 单位K, 默认290K

    Returns:
        G/T值, 单位dB/K

    Example:
        >>> calculate_earth_station_gt(45.57, 0.2, 35, 75)
        24.53
    """
    # 馈线损耗转换为真数
    feed_loss_linear = 10 ** (feed_loss / 10)

    # 计算等效噪声温度
    system_noise_temp = (ant_noise_temp / feed_loss_linear +
                         (1 - 1 / feed_loss_linear) * ambient_temp +
                         receiver_noise_temp)

    # 计算G/T
    gt = antenna_gain - feed_loss - 10 * math.log10(system_noise_temp)

    return gt
