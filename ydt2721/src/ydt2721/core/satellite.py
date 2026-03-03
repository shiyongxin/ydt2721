"""
M02: 卫星参数计算模块
"""

import math
from .constants import LIGHT_SPEED


def calculate_sfd(sfd_ref: float, gt_s: float, gt_s_ref: float) -> float:
    """
    计算卫星饱和通量密度(SFD)

    SFD_s = SFD_ref - (G/T_s - G/T_s,ref)

    Args:
        sfd_ref: 参考点SFD, 单位dB(W/m²)
        gt_s: 卫星G/T值, 单位dB/K
        gt_s_ref: 参考点G/T值, 单位dB/K

    Returns:
        卫星SFD, 单位dB(W/m²)

    Example:
        >>> calculate_sfd(-84, 5.96, 0)
        -89.96
    """
    return sfd_ref - (gt_s - gt_s_ref)


def calculate_antenna_gain_per_area(frequency: float) -> float:
    """
    计算卫星天线孔径单位面积增益

    G_m² = 10 × lg(4 × π / λ²)
    λ = c / f

    Args:
        frequency: 工作频率, 单位Hz

    Returns:
        天线单位面积增益, 单位dB/m²

    Example:
        >>> calculate_antenna_gain_per_area(14.25e9)
        44.53
    """
    wavelength = LIGHT_SPEED / frequency
    gain_linear = 4 * math.pi / (wavelength ** 2)
    gain_db = 10 * math.log10(gain_linear)
    return gain_db
