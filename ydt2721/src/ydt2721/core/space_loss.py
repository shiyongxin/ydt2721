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
