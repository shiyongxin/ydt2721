"""
系统余量调整模块 - 通过调整EIRP实现目标余量
"""

import math
from typing import Dict, Tuple, Callable


def find_eirp_for_target_margin(
    target_margin: float,
    calculate_margin_func: Callable[[float], float],
    eirp_min: float = -10.0,
    eirp_max: float = 60.0,
    tolerance: float = 0.01,
    max_iterations: int = 50
) -> Tuple[float, Dict]:
    """
    通过二分查找找到实现目标余量所需的EIRP

    原理:
    - EIRP ↑ → C/N_d ↑ → C/N_T ↑ → margin ↑
    - EIRP ↓ → C/N_d ↓ → C/N_T ↓ → margin ↓

    Args:
        target_margin: 目标系统余量 (dB)
        calculate_margin_func: 计算EIRP对应余量的函数 (EIRP_dBW → margin_dB)
        eirp_min: EIRP搜索下限 (dBW)
        eirp_max: EIRP搜索上限 (dBW)
        tolerance: 收敛容差 (dB)
        max_iterations: 最大迭代次数

    Returns:
        (所需EIRP_dBW, 调试信息字典)

    Example:
        >>> def margin_func(eirp):
        ...     # 简化的余量计算: margin = EIRP - 20
        ...     return eirp - 20
        >>> eirp, info = find_eirp_for_target_margin(5.0, margin_func, 0, 40)
        >>> print(f"{eirp:.2f} dBW")  # 应该接近 25.0 dBW
    """
    low = eirp_min
    high = eirp_max

    # 检查边界条件
    margin_at_min = calculate_margin_func(low)
    margin_at_max = calculate_margin_func(high)

    # 如果最大EIRP也无法达到目标余量
    if margin_at_max < target_margin:
        return eirp_max, {
            'iterations': 0,
            'final_margin': margin_at_max,
            'error': abs(margin_at_max - target_margin),
            'converged': False,
            'reason': 'max_eirp_insufficient'
        }

    # 如果最小EIRP就已经超过目标余量
    if margin_at_min > target_margin:
        return eirp_min, {
            'iterations': 0,
            'final_margin': margin_at_min,
            'error': abs(margin_at_min - target_margin),
            'converged': margin_at_min - target_margin < tolerance,
            'reason': 'min_eirp_exceeded'
        }

    for i in range(max_iterations):
        mid = (low + high) / 2
        current_margin = calculate_margin_func(mid)

        if abs(current_margin - target_margin) < tolerance:
            return mid, {
                'iterations': i + 1,
                'final_margin': current_margin,
                'error': abs(current_margin - target_margin),
                'converged': True,
                'reason': 'converged'
            }

        # EIRP ↑ → margin ↑
        if current_margin < target_margin:
            low = mid
        else:
            high = mid

        if high - low < 0.001:  # EIRP精度 0.001 dB
            break

    final_eirp = (low + high) / 2
    final_margin = calculate_margin_func(final_eirp)

    return final_eirp, {
        'iterations': i + 1,
        'final_margin': final_margin,
        'error': abs(final_margin - target_margin),
        'converged': abs(final_margin - target_margin) < tolerance,
        'reason': 'max_iterations_reached'
    }


def calculate_margin_for_eirp(
    eirp_sl: float,
    pfd: float,
    gm2_tx: float,
    sat_gt: float,
    downlink_loss: float,
    rx_loss_ar: float,
    rx_gt: float,
    noise_bw: float,
    cn_th: float,
    current_eirp_sl: float,  # 当前EIRP，用于计算调整量
    # 干扰参数
    ci_im: float,
    ci_u_as: float,
    ci_d_as: float,
    ci_u_xp: float,
    ci_d_xp: float
) -> float:
    """
    给定卫星载波EIRP计算系统余量

    注意: 调整EIRP时，上行C/N和下行C/N都会变化
    - 下行C/N直接受EIRP影响
    - 上行C/N通过PFD调整间接影响（EIRP调整量 = PFD调整量）

    Args:
        eirp_sl: 卫星载波EIRP (dBW)
        pfd: 原始功率通量密度 (dB(W/m²))
        gm2_tx: 发射天线单位面积增益 (dB/m²)
        sat_gt: 卫星G/T (dB/K)
        downlink_loss: 下行自由空间损耗 (dB)
        rx_loss_ar: 接收站损耗 (dB)
        rx_gt: 地球站G/T (dB/K)
        noise_bw: 噪声带宽 (Hz)
        cn_th: 门限载噪比 (dB)
        current_eirp_sl: 当前EIRP (dBW)，用于计算EIRP调整量
        ci_im: 互调干扰载干比 (dB)
        ci_u_as: 上行邻星干扰载干比 (dB)
        ci_d_as: 下行邻星干扰载干比 (dB)
        ci_u_xp: 上行交叉极化干扰载干比 (dB)
        ci_d_xp: 下行交叉极化干扰载干比 (dB)

    Returns:
        系统余量 (dB)
    """
    from .clear_sky import calculate_downlink_cn, calculate_uplink_cn, calculate_system_cn
    from .constants import BOLTZMANN_CONSTANT_DB

    # 计算EIRP调整量
    eirp_adjustment = eirp_sl - current_eirp_sl

    # 调整后的PFD（PFD调整量 = EIRP调整量）
    pfd_adjusted = pfd + eirp_adjustment

    # 计算调整后的上行C/N
    cn_u = calculate_uplink_cn(pfd_adjusted, gm2_tx, sat_gt, noise_bw)

    # 计算下行C/N (使用给定的EIRP)
    cn_d = calculate_downlink_cn(eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw)

    # 系统总C/N (功率叠加)
    cn_t = calculate_system_cn(cn_u, cn_d, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp)

    # 余量
    margin = cn_t - cn_th

    return margin


def adjust_satellite_eirp(
    target_margin: float,
    current_eirp_sl: float,
    max_eirp_ss: float,
    # 固定参数
    pfd: float,
    gm2_tx: float,
    sat_gt: float,
    downlink_loss: float,
    rx_loss_ar: float,
    rx_gt: float,
    noise_bw: float,
    cn_th: float,
    # 干扰参数（移除cn_u，现在在margin_func中计算）
    ci_im: float,
    ci_u_as: float,
    ci_d_as: float,
    ci_u_xp: float,
    ci_d_xp: float,
    # 搜索参数
    tolerance: float = 0.01,
    max_iterations: int = 50
) -> Dict:
    """
    调整卫星EIRP以实现目标系统余量

    注意: 调整EIRP时，上行C/N和下行C/N都会变化
    - 下行C/N直接受EIRP影响
    - 上行C/N通过PFD调整间接影响（EIRP调整量 = PFD调整量）

    Args:
        target_margin: 目标系统余量 (dB)
        current_eirp_sl: 当前载波EIRP (dBW)
        max_eirp_ss: 卫星饱和EIRP (dBW)，作为EIRP上限
        ...其他参数

    Returns:
        调整结果字典:
        {
            'adjusted_eirp_sl': float,      # 调整后的EIRP (dBW)
            'eirp_adjustment': float,        # EIRP调整量 (dB)
            'final_margin': float,           # 最终余量 (dB)
            'iterations': int,               # 迭代次数
            'converged': bool,               # 是否收敛
            'error': float,                  # 误差 (dB)
            'reason': str                    # 原因说明
        }
    """
    # 定义余量计算函数
    def margin_func(eirp: float) -> float:
        return calculate_margin_for_eirp(
            eirp_sl=eirp,
            pfd=pfd,
            gm2_tx=gm2_tx,
            sat_gt=sat_gt,
            downlink_loss=downlink_loss,
            rx_loss_ar=rx_loss_ar,
            rx_gt=rx_gt,
            noise_bw=noise_bw,
            cn_th=cn_th,
            current_eirp_sl=current_eirp_sl,  # 传入当前EIRP用于计算调整量
            ci_im=ci_im,
            ci_u_as=ci_u_as,
            ci_d_as=ci_d_as,
            ci_u_xp=ci_u_xp,
            ci_d_xp=ci_d_xp
        )

    # 搜索范围
    eirp_min = max(-10, current_eirp_sl - 20)  # 当前EIRP以下20dB
    eirp_max = max_eirp_ss                     # 不能超过饱和EIRP

    # 二分查找
    adjusted_eirp, info = find_eirp_for_target_margin(
        target_margin=target_margin,
        calculate_margin_func=margin_func,
        eirp_min=eirp_min,
        eirp_max=eirp_max,
        tolerance=tolerance,
        max_iterations=max_iterations
    )

    return {
        'adjusted_eirp_sl': adjusted_eirp,
        'eirp_adjustment': adjusted_eirp - current_eirp_sl,
        'final_margin': info['final_margin'],
        'iterations': info['iterations'],
        'converged': info['converged'],
        'error': info['error'],
        'reason': info['reason']
    }
