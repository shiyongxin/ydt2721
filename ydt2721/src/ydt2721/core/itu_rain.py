"""
ITU-R 标准降雨衰减计算模型
根据 ITU-R P.837, P.838, P.618 标准实现
"""

import math
from typing import Tuple, Dict


# ITU-R P.837-7 降雨率统计模型（简化版）
# 完整实现需要访问 ITU-R 数字地图

def get_rain_rate_p837(latitude: float, longitude: float,
                       p: float = 0.01, month: int = None) -> float:
    """
    根据 ITU-R P.837-7 计算降雨率

    完整实现需要访问 ITU-R P.837 数字地图，这里使用气候区近似。

    Args:
        latitude: 纬度 (度)
        longitude: 经度 (度)
        p: 超时概率 (0.001-1.0)，默认 0.01 (即 0.01% 不可用时间)
        month: 月份 (1-12)，不指定则使用年平均值

    Returns:
        降雨率 (mm/h)
    """
    # 气候区划分（简化）
    if abs(latitude) < 30:
        climate = 'A'  # 热带/亚热带
    elif abs(latitude) < 60:
        climate = 'C'  # 温带
    else:
        climate = 'E'  # 寒带

    # 气候区基准降雨率 (P.837 的近似值)
    climate_base_rates = {
        'A': {'base': 30, 'factor': 50},    # 热带
        'B': {'base': 35, 'factor': 60},    # 干燥亚热带
        'C': {'base': 35, 'factor': 60},    # 温带海洋性
        'D': {'base': 40, 'factor': 70},    # 温带大陆性
        'E': {'base': 40, 'factor': 70},    # 寒带
        'F': {'base': 45, 'factor': 80},    # 极地
        'H': {'base': 25, 'factor': 40},    # 高地
    }

    # 获取当前气候区参数
    params = climate_base_rates.get(climate, climate_base_rates['C'])

    # 计算降雨率 (P.837 简化公式)
    # R_p = R_0.01 × (p / 0.01)^α
    # 这里使用线性近似（实际是幂函数关系）

    # 将 p 从百分比转换为小数
    p_decimal = p / 100.0

    # 简化公式（实际 P.837 更复杂）
    rain_rate = params['base'] + params['factor'] * p_decimal * 100

    return rain_rate


# ITU-R P.838-3 比衰减模型

def get_specific_attenuation_p838(frequency: float,
                                      rain_rate: float,
                                      polarization: str = 'H',
                                      temperature: float = 20.0) -> Tuple[float, float]:
    """
    根据 ITU-R P.838-3 计算比衰减系数 k 和 α

    Args:
        frequency: 频率 (GHz)
        rain_rate: 降雨率 (mm/h)
        polarization: 极化方式 ('H', 'V', 或 Circular)
        temperature: 温度 (°C)，默认 20°C

    Returns:
        (k, alpha): 比衰减系数和指数
    """
    # P.838-3 提供的 k 和 α 的多项式系数
    # 这里使用分段多项式拟合（简化版）

    # 频率段划分
    if frequency < 2.8:
        # < 2.8 GHz
        kv = 0.0637 * (frequency ** 0.785)
        kh = kv * 1.0
        alpha = 0.8955 * (frequency ** 0.0261)
    elif frequency < 8.5:
        # 2.8 - 8.5 GHz
        kv = 0.0691 * (frequency ** 0.758)
        kh = kv * 1.0
        alpha = 0.9075 * (frequency ** -0.0022)
    elif frequency < 25:
        # 8.5 - 25 GHz
        kv = 0.0501 * (frequency ** 0.899)
        kh = kv * 1.0
        alpha = 1.0750 * (frequency ** -0.0045)
    elif frequency < 40:
        # 25 - 40 GHz
        kv = 0.0101 * (frequency ** 1.239)
        kh = kv * 1.0
        alpha = 1.0550 * (frequency ** -0.0125)
    elif frequency < 100:
        # 40 - 100 GHz
        kv = 0.0099 * (frequency ** 1.239)
        kh = kv * 1.0
        alpha = 1.0550 * (frequency ** -0.0125)
    else:
        # > 100 GHz
        kv = 0.0199 * (frequency ** 1.119)
        kh = kv * 1.0
        alpha = 1.1000

    # 极化修正
    if polarization.upper() == 'H':
        k = kh
    elif polarization.upper() == 'V':
        k = kv
    else:  # 圆极化
        k = (kh + kv) / 2.0

    return k, alpha


def calculate_specific_attenuation(k: float, alpha: float,
                                       rain_rate: float) -> float:
    """
    计算比衰减

    γ_R = k × R^α

    Args:
        k: 比衰减系数
        alpha: 幂指数
        rain_rate: 降雨率 (mm/h)

    Returns:
        比衰减 (dB/km)
    """
    return k * (rain_rate ** alpha)


# ITU-R P.618-13 降雨衰减模型

def get_rain_height(latitude: float) -> float:
    """
    计算等效雨高

    根据 ITU-R P.618-13
    h_R = h₀ + 0.36,  对于 0° ≤ φ < 36°
    h_R = 4.0,  对于 φ ≥ 36°

    Args:
        latitude: 纬度 (度)

    Returns:
        等效雨高 (km)
    """
    h0 = 1.6  # 参考高度 (km)

    if latitude >= 36:
        return 4.0
    elif latitude >= 0:
        return h0 + 0.36
    elif latitude >= -36:
        return h0 + 0.36
    else:
        return h0 + 0.36


def calculate_slant_path_length(latitude: float,
                              longitude: float,
                              satellite_longitude: float,
                              rain_height: float,
                              earth_station_height: float = 0.0) -> float:
    """
    计算斜路径长度

    L_s = (h_R - h_S) / sin(θ)

    Args:
        latitude: 地球站纬度 (度)
        longitude: 地球站经度 (度)
        satellite_longitude: 卫星经度 (度)
        rain_height: 雨高 (km)
        earth_station_height: 地球站海拔 (km)

    Returns:
        斜路径长度 (km)
    """
    # 计算仰角（需要导入 earth_station 模块）
    # 这里使用简化的仰角计算
    lat_rad = math.radians(latitude)
    lon_diff_rad = math.radians(abs(longitude - satellite_longitude))

    cos_psi = math.cos(lat_rad) * math.cos(lon_diff_rad)

    # 计算仰角
    numerator = cos_psi - 0.151
    denominator = math.sqrt(max(0, 1 - cos_psi ** 2))

    if abs(denominator) < 1e-10:
        elevation = 0
    else:
        elevation_rad = math.atan(numerator / denominator)
        elevation = math.degrees(elevation_rad)

    # 确保最小仰角 5°
    elevation = max(elevation, 5.0)

    # 斜路径长度
    ls = (rain_height - earth_station_height) / math.sin(math.radians(elevation))

    return ls


def calculate_horizontal_projection(ls: float, elevation: float) -> float:
    """
    计算水平投影

    L_G = L_s × cos(θ)

    Args:
        ls: 斜路径长度 (km)
        elevation: 仰角 (度)

    Returns:
        水平投影 (km)
    """
    return ls * math.cos(math.radians(elevation))


def get_path_length_reduction_factor(lg: float,
                                       p: float = 0.01,
                                       frequency: float = 12.5) -> float:
    """
    计算路径长度缩减因子

    r = 1 / (1 + L_G / (L_R × r_0.01))

    根据 ITU-R P.618-13，r_0.01 与频率有关

    Args:
        lg: 水平投影 (km)
        p: 超时概率 (0.001-1.0)
        frequency: 频率 (GHz)，用于确定 r_0.01

    Returns:
        缩减因子 r
    """
    # r_0.01 参考值（根据频率简化）
    # 完整实现需要查表
    if frequency < 10:
        r_001 = 20.0
    elif frequency < 25:
        r_001 = 22.0
    else:
        r_001 = 25.0

    # 计算缩减因子
    r = 1 / (1 + lg / r_001)

    return r


def calculate_effective_path_length(ls: float, r: float) -> float:
    """
    计算有效路径长度

    L_e = L_s × r

    Args:
        ls: 斜路径长度 (km)
        r: 缩减因子

    Returns:
        有效路径长度 (km)
    """
    return ls * r


def calculate_rain_attenuation_itu(latitude: float, longitude: float,
                                   satellite_longitude: float,
                                   frequency: float,
                                   polarization: str = 'H',
                                   availability: float = 99.9,
                                   earth_station_height: float = 0.0,
                                   temperature: float = 20.0) -> Dict[str, float]:
    """
    完整的 ITU-R 降雨衰减计算

    整合 ITU-R P.837, P.838, P.618 标准

    Args:
        latitude: 地球站纬度 (度)
        longitude: 地球站经度 (度)
        satellite_longitude: 卫星经度 (度)
        frequency: 工作频率 (GHz)
        polarization: 极化方式
        availability: 系统可用度 (%)
        earth_station_height: 地球站海拔 (km)
        temperature: 温度 (°C)

    Returns:
        包含所有计算结果的字典
    """
    # 1. 计算降雨率 (ITU-R P.837)
    p = (100 - availability) / 100.0
    rain_rate = get_rain_rate_p837(latitude, longitude, p)

    # 2. 计算比衰减系数 (ITU-R P.838)
    k, alpha = get_specific_attenuation_p838(
        frequency, rain_rate, polarization, temperature
    )
    specific_attenuation = calculate_specific_attenuation(k, alpha, rain_rate)

    # 3. 计算有效路径长度 (ITU-R P.618)
    rain_height = get_rain_height(latitude)
    ls = calculate_slant_path_length(
        latitude, longitude, satellite_longitude,
        rain_height, earth_station_height
    )

    # 需要仰角计算（这里使用简化版本）
    # 实际应用中应该使用精确的仰角计算
    lat_rad = math.radians(latitude)
    lon_diff_rad = math.radians(abs(longitude - satellite_longitude))
    cos_psi = math.cos(lat_rad) * math.cos(lon_diff_rad)
    elevation = max(5.0, math.degrees(math.atan2(
        math.sqrt(max(0, 1 - cos_psi ** 2)),
        cos_psi - 0.151
    )))

    lg = calculate_horizontal_projection(ls, elevation)
    r = get_path_length_reduction_factor(lg, p, frequency)
    le = calculate_effective_path_length(ls, r)

    # 4. 计算总降雨衰减
    rain_attenuation = specific_attenuation * le

    # 5. 计算降雨噪声温度
    medium_temp = 260.0  # 有效介质温度 (K)
    rain_noise_temp = medium_temp * (1 - 1 / (10 ** (rain_attenuation / 10)))

    # 6. 计算 G/T 下降（需要系统参数）
    feed_loss = 0.2  # 馈线损耗 (dB)
    ant_noise_temp = 35.0  # 天线噪声温度 (K)
    receiver_noise_temp = 75.0  # 接收机噪声温度 (K)

    feed_loss_linear = 10 ** (feed_loss / 10)
    system_noise_temp = (ant_noise_temp / feed_loss_linear +
                         (1 - 1 / feed_loss_linear) * 290 +
                         receiver_noise_temp)

    degraded_gt = (rain_noise_temp / feed_loss_linear + system_noise_temp)
    gt_degradation = 10 * math.log10(degraded_gt / system_noise_temp)

    return {
        'rain_rate_mm_h': rain_rate,
        'k_coefficient': k,
        'alpha_exponent': alpha,
        'specific_attenuation_dB_km': specific_attenuation,
        'rain_height_km': rain_height,
        'slant_path_length_km': ls,
        'horizontal_projection_km': lg,
        'reduction_factor': r,
        'effective_path_length_km': le,
        'rain_attenuation_dB': rain_attenuation,
        'rain_noise_temp_K': rain_noise_temp,
        'gt_degradation_dB': gt_degradation,
        'unavailability_p': p,
    }
