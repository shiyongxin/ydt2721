"""
M03: 载波带宽计算模块
"""

from .constants import MODULATION_INDEX


def calculate_transmission_rate(info_rate: float, fec_rate: float) -> float:
    """
    计算传输速率

    R_t = R_b / σ_FEC

    Args:
        info_rate: 信息速率, 单位bit/s
        fec_rate: FEC编码率 (如0.75表示3/4)

    Returns:
        传输速率, 单位bit/s

    Example:
        >>> calculate_transmission_rate(2000000, 0.75)
        2666666.67
    """
    return info_rate / fec_rate


def calculate_symbol_rate(transmission_rate: float, spread_gain: int,
                         modulation: str) -> float:
    """
    计算符号速率

    R_c = R_t × M
    R_s = R_c / n

    Args:
        transmission_rate: 传输速率, 单位bit/s
        spread_gain: 扩频增益
        modulation: 调制方式 (BPSK/QPSK/8PSK/16QAM)

    Returns:
        符号速率, 单位symbol/s

    Example:
        >>> calculate_symbol_rate(2666667, 1, 'QPSK')
        1333333.5
    """
    chip_rate = transmission_rate * spread_gain
    modulation_index = MODULATION_INDEX.get(modulation.upper(), 2)
    return chip_rate / modulation_index


def calculate_carrier_bandwidth(symbol_rate: float, alpha1: float, alpha2: float,
                                 transponder_bw: float) -> tuple:
    """
    计算载波带宽参数

    BW_n = R_s × α₁
    BW_a = R_s × α₂
    η_BW = (BW_a / BW_tr) × 100%

    Args:
        symbol_rate: 符号速率, 单位symbol/s
        alpha1: 噪声带宽因子
        alpha2: 分配带宽因子
        transponder_bw: 转发器带宽, 单位Hz

    Returns:
        (噪声带宽, 分配带宽, 带宽占用比)

    Example:
        >>> calculate_carrier_bandwidth(1333333, 1.2, 1.4, 54000000)
        (1600000, 1866666, 3.46)
    """
    noise_bw = symbol_rate * alpha1
    allocated_bw = symbol_rate * alpha2
    bw_ratio = (allocated_bw / transponder_bw) * 100
    return noise_bw, allocated_bw, bw_ratio
