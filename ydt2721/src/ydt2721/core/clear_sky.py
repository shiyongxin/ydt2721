"""
M06: 晴天链路计算模块
"""

import math
from .constants import BOLTZMANN_CONSTANT_DB


def calculate_satellite_power_allocation(
        eirp_ss: float, bo_o: float, sfd: float,
        bandwidth_ratio: float, bo_i: float) -> tuple:
    """
    计算卫星功率分配

    Args:
        eirp_ss: 卫星饱和EIRP, 单位dBW
        bo_o: 转发器输出回退, 单位dB
        sfd: 卫星SFD, 单位dB(W/m²)
        bandwidth_ratio: 带宽占用比, 小数形式
        bo_i: 转发器输入回退, 单位dB

    Returns:
        (载波EIRP, PFD, 输入回退, 输出回退)

    Example:
        >>> calculate_satellite_power_allocation(48.48, 3, -89.96, 0.0346, 6)
        (27.19, -120.25, 30.29, 21.29)
    """
    # 计算载波EIRP
    eirp_sl = eirp_ss - bo_o + 10 * math.log10(bandwidth_ratio)

    # 计算PFD (新增bo_i参数)
    pfd = sfd - bo_i - (eirp_ss - bo_o - eirp_sl)

    # 计算回退
    bo_il = sfd - pfd
    bo_ol = eirp_ss - eirp_sl

    return eirp_sl, pfd, bo_il, bo_ol


def calculate_uplink_cn(pfd: float, gm2: float, gt_s: float,
                         noise_bandwidth: float) -> float:
    """
    计算上行链路C/N

    C/N_u = PFD_s - G_m² + G/T_s - 10 × lg(BW_n) - k

    Args:
        pfd: 功率通量密度, 单位dB(W/m²)
        gm2: 天线孔径单位面积增益, 单位dB/m²
        gt_s: 卫星G/T, 单位dB/K
        noise_bandwidth: 噪声带宽, 单位Hz

    Returns:
        上行C/N, 单位dB

    Example:
        >>> calculate_uplink_cn(-114.25, 44.53, 5.96, 1600000)
        13.7
    """
    cn_u = (pfd - gm2 + gt_s -
            10 * math.log10(noise_bandwidth) -
            BOLTZMANN_CONSTANT_DB)
    return cn_u


def calculate_downlink_cn(eirp_sl: float, loss_d: float, loss_ar: float,
                           gt_e: float, noise_bandwidth: float) -> float:
    """
    计算下行链路C/N

    C/N_d = EIRP_sl - L_d - L_ar + G/T_e - 10 × lg(BW_n) - k

    Args:
        eirp_sl: 卫星载波EIRP, 单位dBW
        loss_d: 下行自由空间损耗, 单位dB
        loss_ar: 接收站损耗, 单位dB
        gt_e: 地球站G/T, 单位dB/K
        noise_bandwidth: 噪声带宽, 单位Hz

    Returns:
        下行C/N, 单位dB

    Example:
        >>> calculate_downlink_cn(27.19, 206.03, 0.5, 24.53, 1600000)
        11.7
    """
    cn_d = (eirp_sl - loss_d - loss_ar + gt_e -
            10 * math.log10(noise_bandwidth) -
            BOLTZMANN_CONSTANT_DB)
    return cn_d


def calculate_interference_ci(ci0_param: float, bo: float, noise_bandwidth: float,
                               antenna_gain: float = 0, off_axis_gain: float = 0,
                               interference_type: str = 'default') -> float:
    """
    计算干扰C/I

    Args:
        ci0_param: 干扰参数, 单位dB·Hz
        bo: 回退值, 单位dB
        noise_bandwidth: 噪声带宽, 单位Hz
        antenna_gain: 天线增益(下行邻星干扰需要), 单位dBi
        off_axis_gain: 偏轴增益(下行邻星干扰需要), 单位dBi
        interference_type: 干扰类型

    Returns:
        C/I, 单位dB

    Example:
        >>> calculate_interference_ci(98.3, 21.29, 1600000)
        15.0
    """
    if interference_type == 'downlink_adjacent':
        # 下行邻星干扰需要考虑天线增益差
        ci = (ci0_param - bo + antenna_gain - off_axis_gain -
              10 * math.log10(noise_bandwidth))
    else:
        # 其他干扰类型
        ci = ci0_param - bo - 10 * math.log10(noise_bandwidth)

    return ci


def calculate_system_cn(cn_u: float, cn_d: float, ci_im: float,
                        ci_u_as: float, ci_d_as: float,
                        ci_u_xp: float, ci_d_xp: float) -> float:
    """
    计算链路系统C/N（功率叠加）

    1/(c/n_T) = Σ 1/(c/n_i)
    C/N_T = 10 × lg(c/n_T)

    Args:
        cn_u: 上行C/N, 单位dB
        cn_d: 下行C/N, 单位dB
        ci_im: 互调干扰C/I, 单位dB
        ci_u_as: 上行邻星干扰C/I, 单位dB
        ci_d_as: 下行邻星干扰C/I, 单位dB
        ci_u_xp: 上行交叉极化干扰C/I, 单位dB
        ci_d_xp: 下行交叉极化干扰C/I, 单位dB

    Returns:
        系统C/N, 单位dB

    Example:
        >>> calculate_system_cn(13.7, 11.7, 15.0, 25.91, 21.51, 19.11, 19.35)
        7.58
    """
    # 转换为真数
    cn_u_linear = 10 ** (cn_u / 10)
    cn_d_linear = 10 ** (cn_d / 10)
    ci_im_linear = 10 ** (ci_im / 10)
    ci_u_as_linear = 10 ** (ci_u_as / 10)
    ci_d_as_linear = 10 ** (ci_d_as / 10)
    ci_u_xp_linear = 10 ** (ci_u_xp / 10)
    ci_d_xp_linear = 10 ** (ci_d_xp / 10)

    # 计算总载噪比真数
    inv_cn_total = (1 / cn_u_linear + 1 / cn_d_linear +
                    1 / ci_im_linear + 1 / ci_u_as_linear +
                    1 / ci_d_as_linear + 1 / ci_u_xp_linear +
                    1 / ci_d_xp_linear)

    cn_total_linear = 1 / inv_cn_total if inv_cn_total > 0 else 0

    # 转换回dB
    cn_total_db = 10 * math.log10(cn_total_linear) if cn_total_linear > 0 else -99

    return cn_total_db


def calculate_threshold_cn(ebno_th: float, info_rate: float,
                           noise_bandwidth: float) -> float:
    """
    计算载波门限C/N

    C/N_th = E_b/N_o,th + 10 × lg(R_b) - 10 × lg(BW_n)

    Args:
        ebno_th: Eb/No门限, 单位dB
        info_rate: 信息速率, 单位bit/s
        noise_bandwidth: 噪声带宽, 单位Hz

    Returns:
        门限C/N, 单位dB

    Example:
        >>> calculate_threshold_cn(4.5, 2000000, 1600000)
        5.47
    """
    cn_th = ebno_th + 10 * math.log10(info_rate) - 10 * math.log10(noise_bandwidth)
    return cn_th


def calculate_margin(cn_system: float, cn_th: float) -> float:
    """
    计算系统余量

    M = C/N_T - C/N_th

    Args:
        cn_system: 系统C/N, 单位dB
        cn_th: 门限C/N, 单位dB

    Returns:
        系统余量, 单位dB

    Example:
        >>> calculate_margin(7.58, 5.47)
        2.11
    """
    return cn_system - cn_th


def calculate_earth_station_eirp(sfd: float, bo_il: float, gm2: float,
                                   loss_u: float, loss_at: float) -> float:
    """
    计算载波所需地球站EIRP

    EIRP_el = SFD_s - BO_il - G_m² + L_u + L_at

    Args:
        sfd: 卫星SFD, 单位dB(W/m²)
        bo_il: 输入回退, 单位dB
        gm2: 天线单位面积增益, 单位dB/m²
        loss_u: 上行自由空间损耗, 单位dB
        loss_at: 发射站损耗, 单位dB

    Returns:
        地球站EIRP, 单位dBW

    Example:
        >>> calculate_earth_station_eirp(-89.96, 24.29, 44.53, 207.01, 0.5)
        48.74
    """
    eirp_el = sfd - bo_il - gm2 + loss_u + loss_at
    return eirp_el


def calculate_hpa_power(eirp_el: float, antenna_gain: float,
                         feed_loss: float, noise_bandwidth: float,
                         off_axis_gain: float = 0) -> tuple:
    """
    计算地球站功放发射功率和偏轴EIRP谱密度

    Args:
        eirp_el: 地球站EIRP, 单位dBW
        antenna_gain: 天线发射增益, 单位dBi
        feed_loss: 馈线损耗, 单位dB
        noise_bandwidth: 噪声带宽, 单位Hz
        off_axis_gain: 偏轴增益, 单位dBi

    Returns:
        (功放功率dBW, 功放功率W, 功率谱密度, 偏轴EIRP谱密度)

    Example:
        >>> calculate_hpa_power(48.74, 54.67, 1.5, 1600000, 18.02)
        (-4.43, 0.36, -66.47, -49.96)
    """
    # 计算功放发射功率
    power_dBW = eirp_el - antenna_gain + feed_loss
    power_W = 10 ** (power_dBW / 10)

    # 计算功率谱密度
    power_density = power_dBW - 10 * math.log10(noise_bandwidth)

    # 计算偏轴EIRP谱密度
    off_axis_eirp_density = power_density - feed_loss + off_axis_gain

    return power_dBW, power_W, power_density, off_axis_eirp_density


def calculate_power_ratio(eirp_sl: float, eirp_ss: float, bo_o: float) -> float:
    """
    计算载波卫星功率占用比

    η_P = 10^([EIRP_sl - (EIRP_ss - BO_o)]/10) × 100%

    Args:
        eirp_sl: 卫星载波EIRP, 单位dBW
        eirp_ss: 卫星饱和EIRP, 单位dBW
        bo_o: 转发器输出回退, 单位dB

    Returns:
        功率占用比, 单位%

    Example:
        >>> calculate_power_ratio(27.19, 48.48, 3)
        1.48
    """
    available_power = eirp_ss - bo_o
    power_ratio = 10 ** ((eirp_sl - available_power) / 10) * 100
    return power_ratio
