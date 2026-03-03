"""
M07: 降雨影响计算模块
"""

import math
from .constants import BOLTZMANN_CONSTANT_DB


def calculate_uplink_rain_impact(eirp_ss: float, bo_ol: float,
                                  rain_attenuation: float, upc_max: float,
                                  sfd: float, bo_il: float, gm2: float,
                                  loss_u: float, loss_at: float) -> tuple:
    """
    计算上行降雨影响

    A_UPC = min(A_pu, A_UPC,max)
    EIRP_sl = EIRP_ss - BO_ol - A_pu + A_UPC
    EIRP_el = SFD_s - BO_il - G_m² + L_u + L_at + A_UPC

    Args:
        eirp_ss: 卫星饱和EIRP, 单位dBW
        bo_ol: 输出回退, 单位dB
        rain_attenuation: 上行降雨衰减, 单位dB
        upc_max: UPC最大补偿能力, 单位dB
        sfd: 卫星SFD, 单位dB(W/m²)
        bo_il: 输入回退, 单位dB
        gm2: 天线单位面积增益, 单位dB/m²
        loss_u: 上行自由空间损耗, 单位dB
        loss_at: 发射站损耗, 单位dB

    Returns:
        (UPC补偿量, 卫星载波EIRP, 地球站EIRP)

    Example:
        >>> calculate_uplink_rain_impact(48.48, 21.29, 4.84, 5, -89.96, 24.29, 44.53, 207.01, 0.5)
        (4.84, 27.19, 53.58)
    """
    # UPC实际补偿量
    upc_compensation = min(rain_attenuation, upc_max)

    # 调整后的卫星载波EIRP
    eirp_sl = eirp_ss - bo_ol - rain_attenuation + upc_compensation

    # 调整后的地球站EIRP
    eirp_el = sfd - bo_il - gm2 + loss_u + loss_at + upc_compensation

    return upc_compensation, eirp_sl, eirp_el


def calculate_downlink_rain_cn(eirp_sl: float, loss_d: float, loss_ar: float,
                                rain_attenuation: float, gt_e: float,
                                gt_degradation: float, noise_bandwidth: float) -> float:
    """
    计算下行降雨时的下行链路C/N

    C/N_d = EIRP_sl - L_d - L_ar - A_pd + G/T_e - Δ(G/T_e) - 10 × lg(BW_n) - k

    Args:
        eirp_sl: 卫星载波EIRP, 单位dBW
        loss_d: 下行自由空间损耗, 单位dB
        loss_ar: 接收站损耗, 单位dB
        rain_attenuation: 降雨衰减, 单位dB
        gt_e: 地球站G/T, 单位dB/K
        gt_degradation: G/T下降量, 单位dB
        noise_bandwidth: 噪声带宽, 单位Hz

    Returns:
        下行C/N, 单位dB

    Example:
        >>> calculate_downlink_rain_cn(27.19, 206.03, 0.5, 0.09, 24.53, 0.20, 1600000)
        11.5
    """
    cn_d = (eirp_sl - loss_d - loss_ar - rain_attenuation + gt_e - gt_degradation
            - 10 * math.log10(noise_bandwidth) - BOLTZMANN_CONSTANT_DB)
    return cn_d
