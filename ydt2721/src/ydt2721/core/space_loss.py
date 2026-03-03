"""
M05: 空间损耗计算模块
"""

import math
from .constants import MEDIUM_TEMP, BOLTZMANN_CONSTANT_DB


def calculate_free_space_loss(frequency: float, distance: float) -> float:
    """
    计算自由空间传播损耗

    L = 20 × lg(f) + 20 × lg(d) + 32.45
    f单位: MHz
    d单位: km

    Args:
        frequency: 工作频率, 单位MHz
        distance: 传播距离, 单位km

    Returns:
        自由空间损耗, 单位dB

    Example:
        >>> calculate_free_space_loss(14250, 37533)
        207.01
    """
    return 20 * math.log10(frequency) + 20 * math.log10(distance) + 32.45


def calculate_rain_rate(unavailability: float, latitude: float) -> float:
    """
    计算降雨率 (简化版，完整实现需参考ITU-R P.837标准)

    Args:
        unavailability: 不可用时间百分比 (0-1)
        latitude: 纬度, 单位度

    Returns:
        降雨率, 单位mm/h
    """
    if latitude < 30:
        return 20 + 40 * unavailability * 100
    else:
        return 30 + 50 * unavailability * 100


def calculate_specific_attenuation(frequency: float, rain_rate: float,
                                    pol: str) -> float:
    """
    计算比衰减 (简化版，完整实现需参考ITU-R P.838标准)

    Args:
        frequency: 工作频率, 单位GHz
        rain_rate: 降雨率, 单位mm/h
        pol: 极化方式 (V/H)

    Returns:
        比衰减, 单位dB/km
    """
    k = 0.05 if frequency < 10 else 0.08
    alpha = 1.1
    if pol.upper() == 'H':
        k *= 1.1
    return k * (rain_rate ** alpha)


def calculate_effective_path_length(elevation: float, rain_rate: float) -> float:
    """
    计算有效路径长度 (简化版，完整实现需参考ITU-R P.618标准)

    Args:
        elevation: 仰角, 单位度
        rain_rate: 降雨率, 单位mm/h

    Returns:
        有效路径长度, 单位km
    """
    base_length = 5 / math.sin(math.radians(max(elevation, 5)))
    reduction_factor = 1 / (1 + base_length / 20)
    return base_length * reduction_factor


def calculate_rain_attenuation(availability: float, frequency: float,
                                elevation: float, latitude: float,
                                pol: str = 'V') -> float:
    """
    计算降雨衰减 (简化版，完整实现需参考YD/T 984标准)

    Args:
        availability: 系统可用度, 单位%
        frequency: 工作频率, 单位GHz
        elevation: 仰角, 单位度
        latitude: 纬度, 单位度
        pol: 极化方式 (V/H)

    Returns:
        降雨衰减, 单位dB

    Note:
        完整实现需要参考YD/T 984标准
    """
    # 计算不可用时间百分比
    unavailability = (100 - availability) / 100

    # 计算降雨率
    rain_rate = calculate_rain_rate(unavailability, latitude)

    # 计算比衰减 (dB/km)
    specific_attenuation = calculate_specific_attenuation(
        frequency, rain_rate, pol
    )

    # 计算有效路径长度
    effective_length = calculate_effective_path_length(elevation, rain_rate)

    # 总降雨衰减
    rain_attenuation = specific_attenuation * effective_length

    return rain_attenuation


def calculate_rain_noise_temp(rain_attenuation: float,
                               medium_temp: float = MEDIUM_TEMP) -> float:
    """
    计算降雨噪声温度

    T_s = T_m × (1 - 1/10^(A_pd/10))

    Args:
        rain_attenuation: 降雨衰减, 单位dB
        medium_temp: 有效介质温度, 单位K, 默认260K

    Returns:
        降雨噪声温度, 单位K

    Example:
        >>> calculate_rain_noise_temp(5)
        116.7
    """
    return medium_temp * (1 - 1 / (10 ** (rain_attenuation / 10)))


def calculate_gt_degradation(rain_noise_temp: float, feed_loss: float,
                              system_noise_temp: float) -> float:
    """
    计算降雨衰减等效G/T下降

    Δ(G/T_e) = 10 × lg((T_s/L_fr + T_es) / T_es)

    Args:
        rain_noise_temp: 降雨噪声温度, 单位K
        feed_loss: 馈线损耗, 单位dB
        system_noise_temp: 地球站等效噪声温度, 单位K

    Returns:
        G/T下降量, 单位dB

    Example:
        >>> calculate_gt_degradation(5.74, 0.2, 121.48)
        0.20
    """
    feed_loss_linear = 10 ** (feed_loss / 10)
    degraded_gt = (rain_noise_temp / feed_loss_linear + system_noise_temp)
    degradation_db = 10 * math.log10(degraded_gt / system_noise_temp)
    return degradation_db
