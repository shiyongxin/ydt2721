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


def calculate_required_upc_and_power(
    uplink_rain_att: float,
    sfd: float,
    bo_il: float,
    gm2_tx: float,
    uplink_loss: float,
    tx_loss_at: float,
    tx_antenna_gain: float,
    tx_feed_loss: float,
    upc_max: float,
    hpa_bo: float = 3.0,
) -> dict:
    """
    根据上行降雨衰减计算所需的UPC余量和功放功率

    Args:
        uplink_rain_att: 上行降雨衰减 (dB)
        sfd: 卫星SFD (dB(W/m²))
        bo_il: 输入回退 (dB)
        gm2_tx: 发射天线单位面积增益 (dB/m²)
        uplink_loss: 上行自由空间损耗 (dB)
        tx_loss_at: 发射站损耗 (dB)
        tx_antenna_gain: 发射天线增益 (dBi)
        tx_feed_loss: 发射馈线损耗 (dB)
        upc_max: 当前配置的UPC最大补偿量 (dB)
        hpa_bo: 地球站功放回退 (dB)

    Returns:
        dict: 包含所需UPC余量、载波发射功率、功放输出功率等信息的字典
    """
    # 所需UPC余量等于降雨衰减量
    required_upc = uplink_rain_att

    # 晴天EIRP
    eirp_el_clear = sfd - bo_il - gm2_tx + uplink_loss + tx_loss_at

    # 雨天EIRP (含UPC补偿)
    eirp_el_rain = eirp_el_clear + required_upc

    # 晴天载波所需发射功率
    power_el_clear_dBW = eirp_el_clear - tx_antenna_gain + tx_feed_loss
    power_el_clear_W = 10 ** (power_el_clear_dBW / 10)

    # 晴天功放输出功率（考虑回退）
    hpa_power_clear_dBW = power_el_clear_dBW + hpa_bo
    hpa_power_clear_W = 10 ** (hpa_power_clear_dBW / 10)

    # 雨天载波所需发射功率
    power_el_rain_dBW = eirp_el_rain - tx_antenna_gain + tx_feed_loss
    power_el_rain_W = 10 ** (power_el_rain_dBW / 10)

    # 雨天功放输出功率（考虑回退）
    hpa_power_rain_dBW = power_el_rain_dBW + hpa_bo
    hpa_power_rain_W = 10 ** (hpa_power_rain_dBW / 10)

    # UPC是否足够
    upc_sufficient = required_upc <= upc_max

    return {
        'required_upc_margin': required_upc,
        'calculated_power_el_clear_dBW': power_el_clear_dBW,
        'calculated_power_el_clear_W': power_el_clear_W,
        'calculated_hpa_power_clear_dBW': hpa_power_clear_dBW,
        'calculated_hpa_power_clear_W': hpa_power_clear_W,
        'calculated_power_el_rain_dBW': power_el_rain_dBW,
        'calculated_power_el_rain_W': power_el_rain_W,
        'calculated_hpa_power_rain_dBW': hpa_power_rain_dBW,
        'calculated_hpa_power_rain_W': hpa_power_rain_W,
        'upc_sufficient': upc_sufficient,
        'eirp_el_clear_dBW': eirp_el_clear,
        'eirp_el_rain_dBW': eirp_el_rain,
    }


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
    uplink_availability: float,  # 上行链路可用度 (%)
    downlink_availability: float,  # 下行链路可用度 (%)
    rain_model: str = 'iturpy',  # 降雨模型：仅支持 'iturpy'
    tx_hpa_bo: float = 3.0,  # 地球站功放回退 (dB)
    target_margin: float = 0.0,  # 目标系统余量 (dB), 0表示不启用余量调整

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

    # 降雨衰减（使用 ITU-Rpy）
    from .core.itu_rain_wrapper import calculate_rain_attenuation_iturpy

    # 上行降雨衰减（ITU-Rpy）
    tx_rain_result = calculate_rain_attenuation_iturpy(
        lat=tx_lat,
        lon=tx_lon,
        satellite_lon=sat_longitude,
        frequency=tx_frequency,
        polarization=tx_polarization,
        antenna_diameter=tx_antenna_diameter,
        availability=uplink_availability,
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
        availability=downlink_availability,
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

    result.uplink_loss = uplink_loss
    result.downlink_loss = downlink_loss
    result.rain_model = rain_model

    # 存储上行降雨衰减用于反向计算
    result.uplink_rain_attenuation = uplink_rain_att

    # ========== 4.5 卫星功率分配（需要在反向计算之前完成）==========
    # 注意：必须先计算卫星功率分配，得到实际的bo_il值
    eirp_sl, pfd, bo_il, bo_ol = calculate_satellite_power_allocation(
        sat_eirp_ss, sat_bo_o, sat_sfd, bw_ratio / 100, sat_bo_i
    )
    result.satellite_eirp = eirp_sl
    result.pfd = pfd

    # ========== 4.6 反向计算：从可用度计算所需UPC余量和功放功率 ==========
    # 使用计算后的bo_il而不是配置的sat_bo_i
    reverse_calc = calculate_required_upc_and_power(
        uplink_rain_att=uplink_rain_att,
        sfd=sat_sfd,
        bo_il=bo_il,  # 使用卫星功率分配后的bo_il
        gm2_tx=gm2_tx,
        uplink_loss=uplink_loss,
        tx_loss_at=tx_loss_at,
        tx_antenna_gain=tx_antenna_gain,
        tx_feed_loss=tx_feed_loss,
        upc_max=upc_max,
        hpa_bo=tx_hpa_bo,
    )
    result.calculated_upc_margin = reverse_calc['required_upc_margin']
    result.calculated_power_el_clear_dBW = reverse_calc['calculated_power_el_clear_dBW']
    result.calculated_power_el_clear_W = reverse_calc['calculated_power_el_clear_W']
    result.calculated_hpa_power_clear_dBW = reverse_calc['calculated_hpa_power_clear_dBW']
    result.calculated_hpa_power_clear_W = reverse_calc['calculated_hpa_power_clear_W']
    result.calculated_power_el_rain_dBW = reverse_calc['calculated_power_el_rain_dBW']
    result.calculated_power_el_rain_W = reverse_calc['calculated_power_el_rain_W']
    result.calculated_hpa_power_rain_dBW = reverse_calc['calculated_hpa_power_rain_dBW']
    result.calculated_hpa_power_rain_W = reverse_calc['calculated_hpa_power_rain_W']
    result.upc_sufficient = reverse_calc['upc_sufficient']
    result.required_upc_margin = reverse_calc['required_upc_margin']

    # ========== 5. 晴天链路计算 ==========
    # 计算固定大气衰减（气体、云、闪烁）作为晴天链路的一部分
    # 这些衰减相对稳定，不随降雨动态变化
    tx_fixed_attenuation = (tx_rain_result.get('gas_attenuation_dB', 0) +
                            tx_rain_result.get('cloud_attenuation_dB', 0) +
                            tx_rain_result.get('scintillation_attenuation_dB', 0))
    rx_fixed_attenuation = (rx_rain_result.get('gas_attenuation_dB', 0) +
                            rx_rain_result.get('cloud_attenuation_dB', 0) +
                            rx_rain_result.get('scintillation_attenuation_dB', 0))

    # 上行C/N（减去固定大气衰减）
    cn_u = calculate_uplink_cn(pfd, gm2_tx, sat_gt, noise_bw) - tx_fixed_attenuation

    # 下行C/N（减去固定大气衰减）
    cn_d = calculate_downlink_cn(eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw) - rx_fixed_attenuation

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
    power_el_dBW, power_el_W, hpa_power_dBW, hpa_power_W, _, _ = calculate_hpa_power(
        eirp_el, tx_antenna_gain, tx_feed_loss, noise_bw, tx_hpa_bo
    )

    # 功率占用比
    power_ratio = calculate_power_ratio(eirp_sl, sat_eirp_ss, sat_bo_o)

    result.clear_sky_cn_u = cn_u
    result.clear_sky_cn_d = cn_d
    result.clear_sky_cn_t = cn_t
    result.clear_sky_margin = margin
    result.clear_sky_power_el_dBW = power_el_dBW
    result.clear_sky_power_el_W = power_el_W
    result.clear_sky_hpa_power_dBW = hpa_power_dBW
    result.clear_sky_hpa_power_W = hpa_power_W
    result.clear_sky_power_ratio = power_ratio

    # ========== 6. 上行降雨计算 ==========
    upc_comp, eirp_sl_rain_u, eirp_el_rain_u = calculate_uplink_rain_impact(
        sat_eirp_ss, bo_ol, uplink_rain_att, upc_max,
        sat_sfd, bo_il, gm2_tx, uplink_loss, tx_loss_at
    )

    # 重新计算上行降雨时的系统C/N
    # (简化处理，UPC足够时余量基本不变)
    margin_uplink_rain = margin if upc_comp >= uplink_rain_att else margin - (uplink_rain_att - upc_comp)

    power_el_dBW_rain, power_el_W_rain, hpa_power_dBW_rain, hpa_power_W_rain, _, _ = calculate_hpa_power(
        eirp_el_rain_u, tx_antenna_gain, tx_feed_loss, noise_bw, tx_hpa_bo
    )

    result.uplink_rain_margin = margin_uplink_rain
    result.uplink_rain_power_el_dBW = power_el_dBW_rain
    result.uplink_rain_power_el_W = power_el_W_rain
    result.uplink_rain_hpa_power_dBW = hpa_power_dBW_rain
    result.uplink_rain_hpa_power_W = hpa_power_W_rain

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
    result.downlink_rain_cn_d = cn_d_rain
    result.downlink_rain_cn_t = cn_t_rain
    result.downlink_rain_power_ratio = power_ratio  # 下行降雨时功率占用比不变

    # ========== 8. 余量调整 (可选) ==========
    if target_margin > 0:
        from .core.margin_adjuster import adjust_satellite_eirp

        result.margin_adjustment_enabled = True
        result.target_margin = target_margin

        # 调整卫星EIRP以实现目标余量
        adjustment = adjust_satellite_eirp(
            target_margin=target_margin,
            current_eirp_sl=eirp_sl,
            max_eirp_ss=sat_eirp_ss,
            # 固定参数
            pfd=pfd,
            gm2_tx=gm2_tx,
            sat_gt=sat_gt,
            downlink_loss=downlink_loss,
            rx_loss_ar=rx_loss_ar,
            rx_gt=rx_gt,
            noise_bw=noise_bw,
            cn_th=cn_th,
            # 干扰参数（移除cn_u，现在在margin_func中计算）
            ci_im=ci_im,
            ci_u_as=ci_u_as,
            ci_d_as=ci_d_as,
            ci_u_xp=ci_u_xp,
            ci_d_xp=ci_d_xp
        )

        result.adjusted_eirp_sl = adjustment['adjusted_eirp_sl']
        result.final_margin = adjustment['final_margin']
        result.margin_iterations = adjustment['iterations']

        # 计算调整后的功率
        # EIRP调整量
        eirp_adjustment = adjustment['eirp_adjustment']

        # 调整后的载波发射功率
        result.adjusted_power_el_dBW = power_el_dBW + eirp_adjustment
        result.adjusted_power_el_W = 10 ** (result.adjusted_power_el_dBW / 10)

        # 调整后的功放功率
        result.adjusted_hpa_power_dBW = result.adjusted_power_el_dBW + tx_hpa_bo
        result.adjusted_hpa_power_W = 10 ** (result.adjusted_hpa_power_dBW / 10)

        # 调整后的功率占用比（根据EIRP调整量按比例调整）
        # EIRP调整量是dB值，需要转换为线性比例
        eirp_adjustment_linear = 10 ** (eirp_adjustment / 10)
        result.adjusted_power_ratio = power_ratio * eirp_adjustment_linear

        # ========== 计算调整后的C/N值和余量 ==========

        # 1. 晴天状态：使用调整后的EIRP重新计算上行C/N、下行C/N和系统C/N
        # 上行C/N会随EIRP调整而变化（因为地球站发射功率变化）
        # PFD调整量与EIRP调整量相同
        pfd_adjusted = pfd + eirp_adjustment
        result.adjusted_clear_sky_cn_u = calculate_uplink_cn(pfd_adjusted, gm2_tx, sat_gt, noise_bw)

        result.adjusted_clear_sky_cn_d = calculate_downlink_cn(
            result.adjusted_eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw
        )
        result.adjusted_clear_sky_cn_t = calculate_system_cn(
            result.adjusted_clear_sky_cn_u, result.adjusted_clear_sky_cn_d, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
        )

        # 2. 上行降雨状态：使用调整后的EIRP重新计算余量和功率
        # 注意：上行降雨时，UPC补偿上行C/N，但下行C/N会因为EIRP调整而变化
        cn_d_uplink_rain_adj = calculate_downlink_cn(
            result.adjusted_eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw
        )
        # 上行降雨时，UPC补偿使上行C/N恢复到晴天水平
        cn_t_uplink_rain_adj = calculate_system_cn(
            result.adjusted_clear_sky_cn_u, cn_d_uplink_rain_adj, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
        )
        result.adjusted_uplink_rain_margin = cn_t_uplink_rain_adj - cn_th

        # 计算调整后的上行降雨功率
        # 雨天EIRP = 晴天EIRP + UPC补偿量
        # 调整后的雨天EIRP = 调整后的晴天EIRP + UPC补偿量
        upc_comp = min(uplink_rain_att, upc_max)
        eirp_el_rain_adjusted = result.adjusted_power_el_dBW + tx_antenna_gain - tx_feed_loss + upc_comp
        # 但实际上雨天发射功率 = 调整后的晴天发射功率 + UPC补偿
        result.adjusted_uplink_rain_power_el_dBW = result.adjusted_power_el_dBW + upc_comp
        result.adjusted_uplink_rain_power_el_W = 10 ** (result.adjusted_uplink_rain_power_el_dBW / 10)
        # 雨天功放功率
        result.adjusted_uplink_rain_hpa_power_dBW = result.adjusted_uplink_rain_power_el_dBW + tx_hpa_bo
        result.adjusted_uplink_rain_hpa_power_W = 10 ** (result.adjusted_uplink_rain_hpa_power_dBW / 10)

        # 3. 下行降雨状态：使用调整后的EIRP重新计算余量
        cn_d_downlink_rain_adj = calculate_downlink_rain_cn(
            result.adjusted_eirp_sl, downlink_loss, rx_loss_ar, downlink_rain_att,
            rx_gt, gt_degradation, noise_bw
        )
        cn_t_downlink_rain_adj = calculate_system_cn(
            result.adjusted_clear_sky_cn_u, cn_d_downlink_rain_adj, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
        )
        result.adjusted_downlink_rain_margin = cn_t_downlink_rain_adj - cn_th
        result.adjusted_downlink_rain_cn_d = cn_d_downlink_rain_adj
        result.adjusted_downlink_rain_cn_t = cn_t_downlink_rain_adj
        result.adjusted_downlink_rain_power_ratio = power_ratio  # 下行降雨时功率占用比不变

    return result
