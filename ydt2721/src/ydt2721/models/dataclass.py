"""
数据结构定义
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SatelliteParams:
    """卫星参数"""
    longitude: float          # 卫星经度 (度)
    eirp_ss: float            # 饱和EIRP (dBW)
    gt_s: float               # G/T值 (dB/K)
    gt_s_ref: float           # 参考点G/T (dB/K)
    sfd_ref: float            # 参考点SFD (dB(W/m²))
    bo_i: float               # 输入回退 (dB)
    bo_o: float               # 输出回退 (dB)
    transponder_bw: float     # 转发器带宽 (Hz)
    adj_sat_longitude: Optional[float] = None  # 相邻卫星经度 (度)


@dataclass
class CarrierParams:
    """载波传输参数"""
    info_rate: float          # 信息速率 (bit/s)
    fec_rate: float           # FEC编码率
    fec_type: str             # FEC编码方式
    spread_gain: int          # 扩频增益
    modulation: str           # 调制方式
    modulation_index: int     # 调制指数
    ebno_threshold: float     # Eb/No门限 (dB)
    alpha1: float             # 噪声带宽因子
    alpha2: float             # 分配带宽因子


@dataclass
class EarthStationParams:
    """地球站参数"""
    name: str                 # 站名
    longitude: float          # 经度 (度)
    latitude: float           # 纬度 (度)
    antenna_diameter: float   # 天线口径 (m)
    efficiency: float         # 天线效率
    frequency: float          # 工作频率 (GHz)
    polarization: str         # 极化方式
    feed_loss: float          # 馈线损耗 (dB)
    antenna_noise_temp: float # 天线噪声温度 (K)
    receiver_noise_temp: float # 接收机噪声温度 (K)
    upc_max_comp: float = 5.0 # UPC最大补偿 (dB)
    loss_at: float = 0.5      # 发射站损耗 (dB)
    loss_ar: float = 0.5      # 接收站损耗 (dB)


@dataclass
class InterferenceParams:
    """干扰参数"""
    ci0_im: Optional[float] = None              # 互调干扰参数
    ci0_u_as: Optional[float] = None            # 上行邻星干扰参数
    ci0_d_as: Optional[float] = None            # 下行邻星干扰参数
    ci0_u_xp: Optional[float] = None            # 上行交叉极化干扰
    ci0_d_xp: Optional[float] = None            # 下行交叉极化干扰


@dataclass
class LinkBudgetResult:
    """链路计算结果"""
    # 输入参数
    info_rate: float
    fec_rate: float
    modulation: str

    # 带宽参数
    transmission_rate: float = 0
    symbol_rate: float = 0
    noise_bandwidth: float = 0
    allocated_bandwidth: float = 0
    bandwidth_ratio: float = 0

    # 卫星参数
    satellite_eirp: float = 0
    pfd: float = 0

    # 地球站参数
    tx_antenna_gain: float = 0
    rx_antenna_gain: float = 0
    rx_gt: float = 0
    elevation: float = 0
    azimuth: float = 0

    # 空间损耗
    uplink_loss: float = 0
    downlink_loss: float = 0

    # 晴天结果
    clear_sky_cn_u: float = 0
    clear_sky_cn_d: float = 0
    clear_sky_cn_t: float = 0
    clear_sky_margin: float = 0
    clear_sky_hpa_power: float = 0
    clear_sky_power_ratio: float = 0

    # 上行降雨结果
    uplink_rain_margin: float = 0
    uplink_rain_hpa_power: float = 0

    # 下行降雨结果
    downlink_rain_margin: float = 0

    # 干扰结果
    cn_im: float = 0
    cn_u_as: float = 0
    cn_d_as: float = 0
    cn_u_xp: float = 0
    cn_d_xp: float = 0

    # 门限
    cn_th: float = 0
    ebno_threshold: float = 0


@dataclass
class CalculationInput:
    """完整计算输入参数"""
    satellite: SatelliteParams
    carrier: CarrierParams
    tx_station: EarthStationParams
    rx_station: EarthStationParams
    availability: float  # 系统可用度 (%)
    interference: Optional[InterferenceParams] = None
