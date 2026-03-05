"""
主计算函数 - 整合所有计算模块
"""

import math
from .models.dataclass import LinkBudgetResult

# 导入所有计算模块
from .core.satellite import (
    calculate_sfd,
    calculate_antenna_gain_per_area,
)
from .core.carrier import (
    calculate_transmission_rate,
    calculate_symbol_rate,
    calculate_carrier_bandwidth,
)
from .core.earth_station import (
    calculate_antenna_gain,
    calculate_antenna_pointing,
    calculate_satellite_distance,
    calculate_earth_station_gt,
)
from .core.space_loss import (
    calculate_free_space_loss,
    calculate_rain_attenuation,
    calculate_rain_attenuation_with_model,
    calculate_rain_noise_temp,
    calculate_gt_degradation,
)
from .core.clear_sky import (
    calculate_satellite_power_allocation,
    calculate_uplink_cn,
    calculate_downlink_cn,
    calculate_interference_ci,
    calculate_system_cn,
    calculate_threshold_cn,
    calculate_margin,
    calculate_earth_station_eirp,
    calculate_hpa_power,
    calculate_power_ratio,
)
from .core.rain_impact import (
    calculate_uplink_rain_impact,
    calculate_downlink_rain_cn,
)
from .core.constants import LIGHT_SPEED, MODULATION_INDEX


def calculate_off_axis_gain(antenna_diameter: float, frequency: float,
                             angle: float) -> float:
    """
    计算天线偏轴增益（简化版）
    完整实现需参考ITU-R S.580-6

    Args:
        antenna_diameter: 天线口径, 单位m
        frequency: 频率, 单位Hz
        angle: 偏轴角度, 单位度

    Returns:
        偏轴增益, 单位dBi
    """
    wavelength = LIGHT_SPEED / frequency
    # D/λ
    d_lambda = antenna_diameter / wavelength

    if angle < 0:
        angle = abs(angle)

    # 简化计算
    if angle <= 0:
        return calculate_antenna_gain(antenna_diameter, wavelength, 0.65)

    # 远场旁瓣增益近似
    gain = 10 * math.log10(max(1, 1000 * (wavelength / antenna_diameter) ** 2))
    return max(0, gain)


def complete_link_budget(
    # 卫星参数
    sat_longitude: float,
    sat_eirp_ss: float,
    sat_gt: float,
    sat_gt_ref: float,
    sat_sfd_ref: float,
    sat_bo_i: float,
    sat_bo_o: float,
    sat_transponder_bw: float,

    # 载波参数
    info_rate: float,
    fec_rate: float,
    modulation: str,
    spread_gain: int,
    ebno_th: float,
    alpha1: float,
    alpha2: float,

    # 发射站参数
    tx_station_name: str,
    tx_lat: float,
    tx_lon: float,
    tx_antenna_diameter: float,
    tx_efficiency: float,
    tx_frequency: float,
    tx_polarization: str,
    tx_feed_loss: float,
    tx_loss_at: float,
    upc_max: float,

    # 接收站参数
    rx_station_name: str,
    rx_lat: float,
    rx_lon: float,
    rx_antenna_diameter: float,
    rx_efficiency: float,
    rx_frequency: float,
    rx_polarization: str,
    rx_feed_loss: float,
    rx_loss_ar: float,
    rx_antenna_noise_temp: float,
    rx_receiver_noise_temp: float,

    # 系统参数
    availability: float,
    rain_model: str = 'simplified',  # 降雨模型：'simplified' 或 'iturpy'

    # 干扰参数（可选）
    ci0_im: float = None,
    ci0_u_as: float = None,
    ci0_d_as: float = None,
    ci0_u_xp: float = None,
    ci0_d_xp: float = None,
    adj_sat_lon: float = None,

) -> LinkBudgetResult:
    """
    完整的链路计算

    Returns:
        LinkBudgetResult: 包含所有计算结果
    """
    result = LinkBudgetResult(
        info_rate=info_rate,
        fec_rate=fec_rate,
        modulation=modulation
    )

    # ========== 1. 卫星参数计算 ==========
    sat_sfd = calculate_sfd(sat_sfd_ref, sat_gt, sat_gt_ref)
    gm2_tx = calculate_antenna_gain_per_area(tx_frequency * 1e9)
    gm2_rx = calculate_antenna_gain_per_area(rx_frequency * 1e9)

    # ========== 2. 载波带宽计算 ==========
    transmission_rate = calculate_transmission_rate(info_rate, fec_rate)
    symbol_rate = calculate_symbol_rate(transmission_rate, spread_gain, modulation)
    noise_bw, allocated_bw, bw_ratio = calculate_carrier_bandwidth(
        symbol_rate, alpha1, alpha2, sat_transponder_bw
    )
    result.transmission_rate = transmission_rate
    result.symbol_rate = symbol_rate
    result.noise_bandwidth = noise_bw
    result.allocated_bandwidth = allocated_bw
    result.bandwidth_ratio = bw_ratio

    # ========== 3. 地球站参数计算 ==========
    # 发射站
    tx_wavelength = LIGHT_SPEED / (tx_frequency * 1e9)
    tx_antenna_gain = calculate_antenna_gain(
        tx_antenna_diameter, tx_wavelength, tx_efficiency
    )
    tx_elevation, tx_azimuth = calculate_antenna_pointing(
        tx_lat, tx_lon, sat_longitude
    )
    tx_distance = calculate_satellite_distance(tx_lat, tx_lon, sat_longitude)

    # 接收站
    rx_wavelength = LIGHT_SPEED / (rx_frequency * 1e9)
    rx_antenna_gain = calculate_antenna_gain(
        rx_antenna_diameter, rx_wavelength, rx_efficiency
    )
    rx_elevation, rx_azimuth = calculate_antenna_pointing(
        rx_lat, rx_lon, sat_longitude
    )
    rx_distance = calculate_satellite_distance(rx_lat, rx_lon, sat_longitude)
    rx_gt = calculate_earth_station_gt(
        rx_antenna_gain, rx_feed_loss,
        rx_antenna_noise_temp, rx_receiver_noise_temp
    )

    result.tx_antenna_gain = tx_antenna_gain
    result.rx_antenna_gain = rx_antenna_gain
    result.rx_gt = rx_gt
    result.elevation = rx_elevation
    result.azimuth = rx_azimuth

    # ========== 4. 空间损耗计算 ==========
    # 频率从GHz转换为MHz: 14.25 GHz = 14250 MHz
    uplink_loss = calculate_free_space_loss(tx_frequency * 1e3, tx_distance)
    downlink_loss = calculate_free_space_loss(rx_frequency * 1e3, rx_distance)

    # 降雨衰减（根据选择的模型）
    if rain_model == 'iturpy':
        try:
            from .core.itu_rain_wrapper import calculate_rain_attenuation_iturpy

            # 上行降雨衰减（ITU-Rpy）
            tx_rain_result = calculate_rain_attenuation_iturpy(
                lat=tx_lat,
                lon=tx_lon,
                satellite_lon=sat_longitude,
                frequency=tx_frequency,
                polarization=tx_polarization,
                antenna_diameter=tx_antenna_diameter,
                availability=availability,
                station_height=0.0,  # 可以从参数中获取
                elevation=tx_elevation
            )
            uplink_rain_att = tx_rain_result['rain_attenuation_dB']

            # 下行降雨衰减（ITU-Rpy）
            rx_rain_result = calculate_rain_attenuation_iturpy(
                lat=rx_lat,
                lon=rx_lon,
                satellite_lon=sat_longitude,
                frequency=rx_frequency,
                polarization=rx_polarization,
                antenna_diameter=rx_antenna_diameter,
                availability=availability,
                station_height=0.0,  # 可以从参数中获取
                elevation=rx_elevation
            )
            downlink_rain_att = rx_rain_result['rain_attenuation_dB']
            rain_noise_temp = rx_rain_result['rain_noise_temp_K']

            # 保存ITU-Rpy的额外衰减分量
            result.tx_gas_attenuation = tx_rain_result.get('gas_attenuation_dB', 0)
            result.tx_cloud_attenuation = tx_rain_result.get('cloud_attenuation_dB', 0)
            result.tx_scintillation_attenuation = tx_rain_result.get('scintillation_attenuation_dB', 0)
            result.rx_gas_attenuation = rx_rain_result.get('gas_attenuation_dB', 0)
            result.rx_cloud_attenuation = rx_rain_result.get('cloud_attenuation_dB', 0)
            result.rx_scintillation_attenuation = rx_rain_result.get('scintillation_attenuation_dB', 0)

            # 计算G/T下降
            rx_feed_loss_linear = 10 ** (rx_feed_loss / 10)
            rx_system_noise_temp = (rx_antenna_noise_temp / rx_feed_loss_linear +
                                     (1 - 1 / rx_feed_loss_linear) * 290 +
                                     rx_receiver_noise_temp)
            gt_degradation = calculate_gt_degradation(
                rain_noise_temp, rx_feed_loss, rx_system_noise_temp
            )

        except ImportError:
            print("Warning: ITU-Rpy not installed, falling back to simplified model")
            # 回退到简化模型
            uplink_rain_att = calculate_rain_attenuation(
                availability, tx_frequency, tx_elevation, tx_lat, tx_polarization
            )
            downlink_rain_att = calculate_rain_attenuation(
                availability, rx_frequency, rx_elevation, rx_lat, rx_polarization
            )
            rain_noise_temp = calculate_rain_noise_temp(downlink_rain_att)
            rx_feed_loss_linear = 10 ** (rx_feed_loss / 10)
            rx_system_noise_temp = (rx_antenna_noise_temp / rx_feed_loss_linear +
                                     (1 - 1 / rx_feed_loss_linear) * 290 +
                                     rx_receiver_noise_temp)
            gt_degradation = calculate_gt_degradation(
                rain_noise_temp, rx_feed_loss, rx_system_noise_temp
            )
    else:
        # 使用简化模型（默认）
        uplink_rain_att = calculate_rain_attenuation(
            availability, tx_frequency, tx_elevation, tx_lat, tx_polarization
        )
        downlink_rain_att = calculate_rain_attenuation(
            availability, rx_frequency, rx_elevation, rx_lat, rx_polarization
        )

        # 降雨噪声温度和G/T下降
        rain_noise_temp = calculate_rain_noise_temp(downlink_rain_att)
        rx_feed_loss_linear = 10 ** (rx_feed_loss / 10)
        rx_system_noise_temp = (rx_antenna_noise_temp / rx_feed_loss_linear +
                                 (1 - 1 / rx_feed_loss_linear) * 290 +
                                 rx_receiver_noise_temp)
        gt_degradation = calculate_gt_degradation(
            rain_noise_temp, rx_feed_loss, rx_system_noise_temp
        )

    result.uplink_loss = uplink_loss
    result.downlink_loss = downlink_loss
    result.rain_model = rain_model

    # ========== 5. 晴天链路计算 ==========
    # 卫星功率分配
    eirp_sl, pfd, bo_il, bo_ol = calculate_satellite_power_allocation(
        sat_eirp_ss, sat_bo_o, sat_sfd, bw_ratio / 100
    )
    result.satellite_eirp = eirp_sl
    result.pfd = pfd

    # 上行C/N
    cn_u = calculate_uplink_cn(pfd, gm2_tx, sat_gt, noise_bw)

    # 下行C/N
    cn_d = calculate_downlink_cn(eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw)

    # 干扰C/I（如果提供参数）
    if ci0_im is not None:
        ci_im = calculate_interference_ci(ci0_im, bo_ol, noise_bw)
    else:
        ci_im = 99  # 默认高值，表示影响很小

    if ci0_u_as is not None:
        ci_u_as = calculate_interference_ci(ci0_u_as, bo_il, noise_bw)
    else:
        ci_u_as = 99

    if ci0_d_as is not None:
        # 需要计算偏轴增益
        if adj_sat_lon is not None:
            topocentric_angle = 1.1 * abs(adj_sat_lon - sat_longitude)
            off_axis_gain_rx = calculate_off_axis_gain(
                rx_antenna_diameter, rx_frequency * 1e9, topocentric_angle
            )
        else:
            off_axis_gain_rx = 0
        ci_d_as = calculate_interference_ci(
            ci0_d_as, bo_ol, noise_bw, rx_antenna_gain, off_axis_gain_rx, 'downlink_adjacent'
        )
    else:
        ci_d_as = 99

    if ci0_u_xp is not None:
        ci_u_xp = calculate_interference_ci(ci0_u_xp, bo_il, noise_bw)
    else:
        ci_u_xp = 99

    if ci0_d_xp is not None:
        ci_d_xp = calculate_interference_ci(ci0_d_xp, bo_ol, noise_bw)
    else:
        ci_d_xp = 99

    result.cn_im = ci_im
    result.cn_u_as = ci_u_as
    result.cn_d_as = ci_d_as
    result.cn_u_xp = ci_u_xp
    result.cn_d_xp = ci_d_xp

    # 系统总C/N
    cn_t = calculate_system_cn(cn_u, cn_d, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp)

    # 门限C/N和余量
    cn_th = calculate_threshold_cn(ebno_th, info_rate, noise_bw)
    margin = calculate_margin(cn_t, cn_th)

    result.cn_th = cn_th
    result.ebno_threshold = ebno_th

    # 地球站发射参数
    eirp_el = calculate_earth_station_eirp(sat_sfd, bo_il, gm2_tx, uplink_loss, tx_loss_at)
    hpa_power_dbw, hpa_power_w, _, _ = calculate_hpa_power(
        eirp_el, tx_antenna_gain, tx_feed_loss, noise_bw
    )

    # 功率占用比
    power_ratio = calculate_power_ratio(eirp_sl, sat_eirp_ss, sat_bo_o)

    result.clear_sky_cn_u = cn_u
    result.clear_sky_cn_d = cn_d
    result.clear_sky_cn_t = cn_t
    result.clear_sky_margin = margin
    result.clear_sky_hpa_power = hpa_power_w
    result.clear_sky_power_ratio = power_ratio

    # ========== 6. 上行降雨计算 ==========
    upc_comp, eirp_sl_rain_u, eirp_el_rain_u = calculate_uplink_rain_impact(
        sat_eirp_ss, bo_ol, uplink_rain_att, upc_max,
        sat_sfd, bo_il, gm2_tx, uplink_loss, tx_loss_at
    )

    # 重新计算上行降雨时的系统C/N
    # (简化处理，UPC足够时余量基本不变)
    margin_uplink_rain = margin if upc_comp >= uplink_rain_att else margin - (uplink_rain_att - upc_comp)

    hpa_power_dbw_rain, hpa_power_w_rain, _, _ = calculate_hpa_power(
        eirp_el_rain_u, tx_antenna_gain, tx_feed_loss, noise_bw
    )

    result.uplink_rain_margin = margin_uplink_rain
    result.uplink_rain_hpa_power = hpa_power_w_rain

    # ========== 7. 下行降雨计算 ==========
    cn_d_rain = calculate_downlink_rain_cn(
        eirp_sl, downlink_loss, rx_loss_ar, downlink_rain_att,
        rx_gt, gt_degradation, noise_bw
    )

    # 重新计算系统C/N
    cn_t_rain = calculate_system_cn(
        cn_u, cn_d_rain, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
    )
    margin_downlink_rain = calculate_margin(cn_t_rain, cn_th)

    result.downlink_rain_margin = margin_downlink_rain

    return result
