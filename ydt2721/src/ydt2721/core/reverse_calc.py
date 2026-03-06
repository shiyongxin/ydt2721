"""
反向计算模块 - 根据预留A_UPC计算可用度
"""

import math
from typing import Dict, Optional, Tuple
from .space_loss import calculate_rain_attenuation
from .itu_rain_wrapper import calculate_rain_attenuation_iturpy, ITURPY_AVAILABLE


def invert_availability_from_rain_attenuation(
    target_rain_att: float,
    lat: float,
    lon: float,
    satellite_lon: float,
    frequency: float,
    polarization: str,
    antenna_diameter: float,
    elevation: float,
    station_height: float = 0.0,
    rain_model: str = 'simplified'
) -> Tuple[float, Dict]:
    """
    根据目标降雨衰减反推可用度（使用二分查找）

    Args:
        target_rain_att: 目标降雨衰减 (dB)
        lat: 纬度 (度)
        lon: 经度 (度)
        satellite_lon: 卫星经度 (度)
        frequency: 频率 (GHz)
        polarization: 极化方式
        antenna_diameter: 天线直径 (m)
        elevation: 仰角 (度)
        station_height: 站高度 (km)
        rain_model: 降雨模型 ('simplified' 或 'iturpy')

    Returns:
        (可用度%, 详细信息)
    """
    # 可用度搜索范围: 90% ~ 99.999%
    # 对应的不可用度: 10% ~ 0.001%
    low_avail = 90.0
    high_avail = 99.999
    tolerance = 0.001  # 可用度精度
    max_iterations = 50

    for _ in range(max_iterations):
        mid_avail = (low_avail + high_avail) / 2

        # 计算当前可用度对应的降雨衰减
        if rain_model == 'iturpy' and ITURPY_AVAILABLE:
            try:
                result = calculate_rain_attenuation_iturpy(
                    lat=lat,
                    lon=lon,
                    satellite_lon=satellite_lon,
                    frequency=frequency,
                    polarization=polarization,
                    antenna_diameter=antenna_diameter,
                    availability=mid_avail,
                    station_height=station_height,
                    elevation=elevation
                )
                current_rain_att = result['rain_attenuation_dB']
            except Exception:
                # 回退到简化模型
                current_rain_att = calculate_rain_attenuation(
                    mid_avail, frequency, elevation, lat, polarization
                )
        else:
            current_rain_att = calculate_rain_attenuation(
                mid_avail, frequency, elevation, lat, polarization
            )

        # 二分查找逻辑
        # 可用度越高 → 降雨衰减越大
        if current_rain_att < target_rain_att:
            low_avail = mid_avail
        else:
            high_avail = mid_avail

        # 检查收敛
        if high_avail - low_avail < tolerance:
            break

    final_avail = (low_avail + high_avail) / 2

    # 计算最终的降雨衰减详情
    details = {
        'availability': final_avail,
        'unavailability': 100 - final_avail,
        'rain_attenuation_dB': current_rain_att,
        'target_rain_attenuation_dB': target_rain_att,
        'error_dB': abs(current_rain_att - target_rain_att)
    }

    return final_avail, details


def calculate_uplink_power_from_upc(
    upc_reserved: float,
    sfd: float,
    bo_il: float,
    gm2: float,
    loss_u: float,
    loss_at: float
) -> Dict[str, float]:
    """
    根据预留的 UPC 计算雨天功放功率

    Args:
        upc_reserved: 预留的 UPC 补偿量 (dB)
        sfd: 卫星 SFD (dB(W/m²))
        bo_il: 输入回退 (dB)
        gm2: 天线单位面积增益 (dB/m²)
        loss_u: 上行自由空间损耗 (dB)
        loss_at: 发射站损耗 (dB)

    Returns:
        功率计算结果
    """
    # 雨天地球站 EIRP
    eirp_el_rain = sfd - bo_il - gm2 + loss_u + loss_at + upc_reserved

    # 相对于晴天的 EIRP 增加
    eirp_el_clear = sfd - bo_il - gm2 + loss_u + loss_at
    eirp_increase = eirp_el_rain - eirp_el_clear

    return {
        'upc_reserved_dB': upc_reserved,
        'eirp_el_clear_dBW': eirp_el_clear,
        'eirp_el_rain_dBW': eirp_el_rain,
        'eirp_increase_dB': eirp_increase
    }


def calculate_required_hpa_for_availability(
    target_availability: float,
    sfd: float,
    bo_il: float,
    gm2: float,
    loss_u: float,
    loss_at: float,
    lat: float,
    lon: float,
    satellite_lon: float,
    frequency: float,
    polarization: str,
    antenna_diameter: float,
    elevation: float,
    station_height: float = 0.0,
    upc_max: float = 5.0,
    rain_model: str = 'simplified'
) -> Dict[str, float]:
    """
    计算满足目标可用度所需的功放参数

    Args:
        target_availability: 目标可用度 (%)
        ... (其他参数同上)
        upc_max: UPC 最大补偿能力 (dB)
        rain_model: 降雨模型

    Returns:
        功放参数需求
    """
    # 计算目标可用度对应的降雨衰减
    if rain_model == 'iturpy' and ITURPY_AVAILABLE:
        try:
            result = calculate_rain_attenuation_iturpy(
                lat=lat,
                lon=lon,
                satellite_lon=satellite_lon,
                frequency=frequency,
                polarization=polarization,
                antenna_diameter=antenna_diameter,
                availability=target_availability,
                station_height=station_height,
                elevation=elevation
            )
            rain_att = result['rain_attenuation_dB']
        except Exception:
            rain_att = calculate_rain_attenuation(
                target_availability, frequency, elevation, lat, polarization
            )
    else:
        rain_att = calculate_rain_attenuation(
            target_availability, frequency, elevation, lat, polarization
        )

    # UPC 补偿量
    upc_used = min(rain_att, upc_max)

    # 晴天 EIRP
    eirp_el_clear = sfd - bo_il - gm2 + loss_u + loss_at

    # 雨天 EIRP (含 UPC 补偿)
    eirp_el_rain = eirp_el_clear + upc_used

    # 剩余未补偿衰减
    residual_att = rain_att - upc_used

    return {
        'target_availability': target_availability,
        'rain_attenuation_dB': rain_att,
        'upc_used_dB': upc_used,
        'upc_max_dB': upc_max,
        'residual_attenuation_dB': residual_att,
        'eirp_el_clear_dBW': eirp_el_clear,
        'eirp_el_rain_dBW': eirp_el_rain,
        'eirp_increase_dB': upc_used,
        'upc_sufficient': rain_att <= upc_max
    }


def analyze_power_margin(
    hpa_power_w: float,
    antenna_gain: float,
    feed_loss: float,
    sfd: float,
    bo_il: float,
    gm2: float,
    loss_u: float,
    loss_at: float,
    upc_max: float,
    lat: float,
    lon: float,
    satellite_lon: float,
    frequency: float,
    polarization: str,
    antenna_diameter: float,
    elevation: float,
    station_height: float = 0.0,
    rain_model: str = 'simplified'
) -> Dict[str, float]:
    """
    分析给定功放功率可支持的可用度范围

    Args:
        hpa_power_w: 功放功率 (W)
        ... (其他参数同上)

    Returns:
        分析结果
    """
    # 计算晴天 EIRP
    hpa_power_dbw = 10 * math.log10(hpa_power_w)
    eirp_el_clear = hpa_power_dbw + antenna_gain - feed_loss

    # 晴天 EIRP 对应的理论值
    eirp_el_theoretical = sfd - bo_il - gm2 + loss_u + loss_at

    # 可用的 UPC 余量
    upc_margin = eirp_el_clear - eirp_el_theoretical

    # 实际可用的 UPC (受限于最大 UPC)
    upc_available = min(upc_margin, upc_max)

    # 可补偿的降雨衰减
    compensable_rain_att = upc_available

    # 反推可用度
    availability, details = invert_availability_from_rain_attenuation(
        target_rain_att=compensable_rain_att,
        lat=lat,
        lon=lon,
        satellite_lon=satellite_lon,
        frequency=frequency,
        polarization=polarization,
        antenna_diameter=antenna_diameter,
        elevation=elevation,
        station_height=station_height,
        rain_model=rain_model
    )

    return {
        'hpa_power_W': hpa_power_w,
        'hpa_power_dBW': hpa_power_dbw,
        'eirp_el_clear_dBW': eirp_el_clear,
        'upc_margin_dB': upc_margin,
        'upc_available_dB': upc_available,
        'compensable_rain_attenuation_dB': compensable_rain_att,
        'supported_availability': availability,
        'upc_limited_by': 'max_capacity' if upc_margin >= upc_max else 'hpa_power',
        **details
    }
