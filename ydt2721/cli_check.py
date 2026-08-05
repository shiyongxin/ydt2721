#!/usr/bin/env python3
"""
YDT 2721 卫星链路计算检查程序 - 输出所有中间参数
保持与 cli.py 相同的计算流程，但输出详细的中间参数

注意：本文件是调试专用工具（仅供开发排查中间参数），
不被任何测试/示例/CI 引用，正式使用请通过 cli.py。
"""

import argparse
import sys
import os
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721.core.param_manager import ParameterValidator, ParameterManager
from ydt2721.core.satellite import calculate_sfd, calculate_antenna_gain_per_area
from ydt2721.core.carrier import calculate_transmission_rate, calculate_symbol_rate, calculate_carrier_bandwidth
from ydt2721.core.earth_station import (
    calculate_antenna_pointing,
    calculate_antenna_gain,
    calculate_satellite_distance,
    calculate_earth_station_gt,
)
from ydt2721.core.space_loss import calculate_free_space_loss, calculate_gt_degradation
from ydt2721.core.clear_sky import (
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
from ydt2721.core.rain_impact import calculate_uplink_rain_impact, calculate_downlink_rain_cn
from ydt2721.models.dataclass import (
    SatelliteParams,
    CarrierParams,
    EarthStationParams,
)
from ydt2721.core.constants import LIGHT_SPEED, MODULATION_INDEX


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title):
    """打印子节标题"""
    print("\n" + "-" * 50)
    print(f"  {title}")
    print("-" * 50)


def print_param(name, value, unit="", indent="  "):
    """打印参数"""
    if isinstance(value, float):
        if abs(value) < 0.01 or abs(value) >= 10000:
            print(f"{indent}{name}: {value:.6e} {unit}")
        else:
            print(f"{indent}{name}: {value:.4f} {unit}")
    else:
        print(f"{indent}{name}: {value} {unit}")


def load_config(config_file: str) -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def execute_calculation_with_detail(
    config: dict,
    target_margin: float = 0.0,
    station_height: float = 0.0,
) -> bool:
    """执行详细链路计算，输出所有中间参数"""

    # 提取参数
    sat = config.get('satellite', {})
    carrier = config.get('carrier', {})
    tx = config.get('tx_station', {})
    rx = config.get('rx_station', {})
    system = config.get('system', {})
    interference = config.get('interference', {})

    print_section("YDT 2721 卫星链路计算 - 详细中间参数输出")

    # ==================== 0. 输入参数 ====================
    print_section("0. 输入参数")

    print_subsection("卫星参数")
    print_param("卫星经度", sat.get('longitude', 0), "°")
    print_param("卫星饱和EIRP", sat.get('eirp_ss', 0), "dBW")
    print_param("卫星饱和G/T值", sat.get('gt_s', 0), "dB/K")
    print_param("卫星G/T参考频率", sat.get('gt_s_ref', 0), "GHz")
    print_param("饱和通量密度参考值", sat.get('sfd_ref', 0), "dB(W/m²)")
    print_param("输入回退", sat.get('bo_i', 6), "dB")
    print_param("输出回退", sat.get('bo_o', 3), "dB")
    print_param("转发器带宽", sat.get('transponder_bw', 54000000), "Hz")

    print_subsection("载波参数")
    print_param("信息速率", carrier.get('info_rate', 2000000), "bps")
    print_param("FEC编码率", carrier.get('fec_rate', 0.75))
    print_param("调制方式", carrier.get('modulation', 'QPSK'))
    print_param("扩频增益", carrier.get('spread_gain', 1))
    print_param("Eb/N0门限", carrier.get('ebno_threshold', 4.5), "dB")
    print_param("滚降系数α1", carrier.get('alpha1', 1.2))
    print_param("滚降系数α2", carrier.get('alpha2', 1.4))

    print_subsection("发射站参数")
    print_param("站名", tx.get('name', '发射站'))
    print_param("纬度", tx.get('latitude', 0), "°")
    print_param("经度", tx.get('longitude', 0), "°")
    print_param("天线口径", tx.get('antenna_diameter', 4.5), "m")
    print_param("天线效率", tx.get('efficiency', 0.65))
    print_param("发射频率", tx.get('frequency', 14.25), "GHz")
    print_param("极化方式", tx.get('polarization', 'V'))
    print_param("馈线损耗", tx.get('feed_loss', 1.5), "dB")
    print_param("AT损耗", tx.get('loss_at', 0.5), "dB")
    print_param("UPC最大补偿", tx.get('upc_max_comp', 5.0), "dB")
    print_param("功放回退", tx.get('hpa_bo', 3.0), "dB")

    print_subsection("接收站参数")
    print_param("站名", rx.get('name', '接收站'))
    print_param("纬度", rx.get('latitude', 0), "°")
    print_param("经度", rx.get('longitude', 0), "°")
    print_param("天线口径", rx.get('antenna_diameter', 1.8), "m")
    print_param("天线效率", rx.get('efficiency', 0.65))
    print_param("接收频率", rx.get('frequency', 12.50), "GHz")
    print_param("极化方式", rx.get('polarization', 'H'))
    print_param("馈线损耗", rx.get('feed_loss', 0.2), "dB")
    print_param("AR损耗", rx.get('loss_ar', 0.5), "dB")
    print_param("天线噪声温度", rx.get('antenna_noise_temp', 35), "K")
    print_param("接收机噪声温度", rx.get('receiver_noise_temp', 75), "K")

    print_subsection("系统参数")
    print_param("上行可用度", system.get('uplink_availability', 99.9), "%")
    print_param("下行可用度", system.get('downlink_availability', 99.9), "%")
    print_param("目标余量", target_margin, "dB")

    # ==================== 1. 卫星参数计算 ====================
    print_section("1. 卫星参数计算 (M02)")

    sat_sfd_ref = sat.get('sfd_ref', 0)
    sat_gt = sat.get('gt_s', 0)
    sat_gt_ref = sat.get('gt_s_ref', 0)
    tx_frequency = tx.get('frequency', 14.25)
    rx_frequency = rx.get('frequency', 12.50)

    print_subsection("1.1 卫星SFD计算")
    print_param("输入 SFD参考值(sfd_ref)", sat_sfd_ref, "dB(W/m²)")
    print_param("输入 卫星G/T(sat_gt)", sat_gt, "dB/K")
    print_param("输入 G/T参考频率(sat_gt_ref)", sat_gt_ref, "GHz")

    sat_sfd = calculate_sfd(sat_sfd_ref, sat_gt, sat_gt_ref)
    print_param("输出 卫星SFD", sat_sfd, "dB(W/m²)")

    print_subsection("1.2 天线单位面积增益计算")
    print_param("发射频率", tx_frequency, "GHz")
    gm2_tx = calculate_antenna_gain_per_area(tx_frequency * 1e9)
    print_param("发射天线单位面积增益", gm2_tx, "dB/m²")

    print_param("接收频率", rx_frequency, "GHz")
    gm2_rx = calculate_antenna_gain_per_area(rx_frequency * 1e9)
    print_param("接收天线单位面积增益", gm2_rx, "dB/m²")

    # ==================== 2. 载波带宽计算 ====================
    print_section("2. 载波带宽计算 (M03)")

    info_rate = carrier.get('info_rate', 2000000)
    fec_rate = carrier.get('fec_rate', 0.75)
    spread_gain = carrier.get('spread_gain', 1)
    modulation = carrier.get('modulation', 'QPSK')
    alpha1 = carrier.get('alpha1', 1.2)
    alpha2 = carrier.get('alpha2', 1.4)
    sat_transponder_bw = sat.get('transponder_bw', 54000000)

    print_subsection("2.1 传输速率计算")
    print_param("输入 信息速率", info_rate, "bps")
    print_param("输入 FEC编码率", fec_rate)

    transmission_rate = calculate_transmission_rate(info_rate, fec_rate)
    print_param("输出 传输速率", transmission_rate, "bps")

    print_subsection("2.2 符号速率计算")
    print_param("输入 传输速率", transmission_rate, "bps")
    print_param("输入 扩频增益", spread_gain)
    print_param("输入 调制方式", modulation)
    mod_index = MODULATION_INDEX.get(modulation, 2)
    print_param("输出 调制指数", mod_index)

    symbol_rate = calculate_symbol_rate(transmission_rate, spread_gain, modulation)
    print_param("输出 符号速率", symbol_rate, "baud")
    print_param("符号速率", symbol_rate / 1e6, "Msym/s")

    print_subsection("2.3 载波带宽计算")
    print_param("输入 符号速率", symbol_rate, "baud")
    print_param("输入 滚降系数α1", alpha1)
    print_param("输入 滚降系数α2", alpha2)
    print_param("输入 转发器带宽", sat_transponder_bw, "Hz")

    noise_bw, allocated_bw, bw_ratio = calculate_carrier_bandwidth(
        symbol_rate, alpha1, alpha2, sat_transponder_bw
    )
    print_param("输出 噪声带宽", noise_bw, "Hz")
    print_param("输出 噪声带宽", noise_bw / 1e6, "MHz")
    print_param("输出 分配带宽", allocated_bw, "Hz")
    print_param("输出 分配带宽", allocated_bw / 1e6, "MHz")
    print_param("输出 带宽占用比", bw_ratio, "%")

    # ==================== 3. 地球站参数计算 ====================
    print_section("3. 地球站参数计算 (M04)")

    # 发射站参数
    tx_lat = tx.get('latitude', 0)
    tx_lon = tx.get('longitude', 0)
    tx_antenna_diameter = tx.get('antenna_diameter', 4.5)
    tx_efficiency = tx.get('efficiency', 0.65)
    tx_polarization = tx.get('polarization', 'V')

    # 接收站参数
    rx_lat = rx.get('latitude', 0)
    rx_lon = rx.get('longitude', 0)
    rx_antenna_diameter = rx.get('antenna_diameter', 1.8)
    rx_efficiency = rx.get('efficiency', 0.65)
    rx_polarization = rx.get('polarization', 'H')
    rx_feed_loss = rx.get('feed_loss', 0.2)
    rx_antenna_noise_temp = rx.get('antenna_noise_temp', 35)
    rx_receiver_noise_temp = rx.get('receiver_noise_temp', 75)

    sat_longitude = sat.get('longitude', 0)

    print_subsection("3.1 发射站参数")
    print_param("输入 发射频率", tx_frequency, "GHz")
    tx_wavelength = LIGHT_SPEED / (tx_frequency * 1e9)
    print_param("输出 波长", tx_wavelength, "m")

    print_param("输入 天线口径", tx_antenna_diameter, "m")
    print_param("输入 天线效率", tx_efficiency)
    print_param("输入 波长", tx_wavelength, "m")

    tx_antenna_gain = calculate_antenna_gain(tx_antenna_diameter, tx_wavelength, tx_efficiency)
    print_param("输出 天线增益", tx_antenna_gain, "dBi")

    print_param("输入 发射站纬度", tx_lat, "°")
    print_param("输入 发射站经度", tx_lon, "°")
    print_param("输入 卫星经度", sat_longitude, "°")

    tx_elevation, tx_azimuth = calculate_antenna_pointing(tx_lat, tx_lon, sat_longitude)
    print_param("输出 仰角", tx_elevation, "°")
    print_param("输出 方位角", tx_azimuth, "°")

    tx_distance = calculate_satellite_distance(tx_lat, tx_lon, sat_longitude)
    print_param("输出 卫星距离", tx_distance, "km")

    print_subsection("3.2 接收站参数")
    print_param("输入 接收频率", rx_frequency, "GHz")
    rx_wavelength = LIGHT_SPEED / (rx_frequency * 1e9)
    print_param("输出 波长", rx_wavelength, "m")

    print_param("输入 天线口径", rx_antenna_diameter, "m")
    print_param("输入 天线效率", rx_efficiency)
    print_param("输入 波长", rx_wavelength, "m")

    rx_antenna_gain = calculate_antenna_gain(rx_antenna_diameter, rx_wavelength, rx_efficiency)
    print_param("输出 天线增益", rx_antenna_gain, "dBi")

    print_param("输入 接收站纬度", rx_lat, "°")
    print_param("输入 接收站经度", rx_lon, "°")
    print_param("输入 卫星经度", sat_longitude, "°")

    rx_elevation, rx_azimuth = calculate_antenna_pointing(rx_lat, rx_lon, sat_longitude)
    print_param("输出 仰角", rx_elevation, "°")
    print_param("输出 方位角", rx_azimuth, "°")

    rx_distance = calculate_satellite_distance(rx_lat, rx_lon, sat_longitude)
    print_param("输出 卫星距离", rx_distance, "km")

    print_param("输入 天线增益", rx_antenna_gain, "dBi")
    print_param("输入 馈线损耗", rx_feed_loss, "dB")
    print_param("输入 天线噪声温度", rx_antenna_noise_temp, "K")
    print_param("输入 接收机噪声温度", rx_receiver_noise_temp, "K")

    rx_gt = calculate_earth_station_gt(
        rx_antenna_gain, rx_feed_loss,
        rx_antenna_noise_temp, rx_receiver_noise_temp
    )
    print_param("输出 地球站G/T", rx_gt, "dB/K")

    # ==================== 4. 空间损耗计算 ====================
    print_section("4. 空间损耗计算 (M05)")

    print_subsection("4.1 自由空间损耗")
    print_param("输入 发射频率", tx_frequency, "GHz (= " + str(tx_frequency * 1e3) + " MHz)")
    print_param("输入 发射站距离", tx_distance, "km")

    uplink_loss = calculate_free_space_loss(tx_frequency * 1e3, tx_distance)
    print_param("输出 上行自由空间损耗", uplink_loss, "dB")

    print_param("输入 接收频率", rx_frequency, "GHz (= " + str(rx_frequency * 1e3) + " MHz)")
    print_param("输入 接收站距离", rx_distance, "km")

    downlink_loss = calculate_free_space_loss(rx_frequency * 1e3, rx_distance)
    print_param("输出 下行自由空间损耗", downlink_loss, "dB")

    print_subsection("4.2 降雨衰减计算 (ITU-Rpy)")
    from ydt2721.core.itu_rain_wrapper import calculate_rain_attenuation_iturpy

    uplink_availability = system.get('uplink_availability', 99.9)
    downlink_availability = system.get('downlink_availability', 99.9)

    print_param("输入 纬度", tx_lat, "°")
    print_param("输入 经度", tx_lon, "°")
    print_param("输入 卫星经度", sat_longitude, "°")
    print_param("输入 频率", tx_frequency, "GHz")
    print_param("输入 极化", tx_polarization)
    print_param("输入 天线口径", tx_antenna_diameter, "m")
    print_param("输入 可用度", uplink_availability, "%")
    print_param("输入 站海拔", station_height, "km")
    print_param("输入 仰角", tx_elevation, "°")

    tx_rain_result = calculate_rain_attenuation_iturpy(
        lat=tx_lat,
        lon=tx_lon,
        satellite_lon=sat_longitude,
        frequency=tx_frequency,
        polarization=tx_polarization,
        antenna_diameter=tx_antenna_diameter,
        availability=uplink_availability,
        station_height=station_height,
        elevation=tx_elevation
    )
    uplink_rain_att = tx_rain_result['rain_attenuation_dB']

    print_param("输出 上行降雨衰减", uplink_rain_att, "dB")
    print_param("  气体衰减", tx_rain_result.get('gas_attenuation_dB', 0), "dB")
    print_param("  云衰减", tx_rain_result.get('cloud_attenuation_dB', 0), "dB")
    print_param("  闪烁衰减", tx_rain_result.get('scintillation_attenuation_dB', 0), "dB")

    print_param("输入 纬度", rx_lat, "°")
    print_param("输入 经度", rx_lon, "°")
    print_param("输入 卫星经度", sat_longitude, "°")
    print_param("输入 频率", rx_frequency, "GHz")
    print_param("输入 极化", rx_polarization)
    print_param("输入 天线口径", rx_antenna_diameter, "m")
    print_param("输入 可用度", downlink_availability, "%")
    print_param("输入 站海拔", station_height, "km")
    print_param("输入 仰角", rx_elevation, "°")

    rx_rain_result = calculate_rain_attenuation_iturpy(
        lat=rx_lat,
        lon=rx_lon,
        satellite_lon=sat_longitude,
        frequency=rx_frequency,
        polarization=rx_polarization,
        antenna_diameter=rx_antenna_diameter,
        availability=downlink_availability,
        station_height=station_height,
        elevation=rx_elevation
    )
    downlink_rain_att = rx_rain_result['rain_attenuation_dB']
    rain_noise_temp = rx_rain_result['rain_noise_temp_K']

    print_param("输出 下行降雨衰减", downlink_rain_att, "dB")
    print_param("  气体衰减", rx_rain_result.get('gas_attenuation_dB', 0), "dB")
    print_param("  云衰减", rx_rain_result.get('cloud_attenuation_dB', 0), "dB")
    print_param("  闪烁衰减", rx_rain_result.get('scintillation_attenuation_dB', 0), "dB")
    print_param("  降雨噪声温度", rain_noise_temp, "K")

    print_subsection("4.3 G/T下降计算")
    rx_feed_loss_linear = 10 ** (rx_feed_loss / 10)
    print_param("馈线损耗线性值", rx_feed_loss_linear)

    rx_system_noise_temp = (rx_antenna_noise_temp / rx_feed_loss_linear +
                            (1 - 1 / rx_feed_loss_linear) * 290 +
                            rx_receiver_noise_temp)
    print_param("系统噪声温度", rx_system_noise_temp, "K")

    print_param("输入 降雨噪声温度", rain_noise_temp, "K")
    print_param("输入 馈线损耗", rx_feed_loss, "dB")
    print_param("输入 系统噪声温度", rx_system_noise_temp, "K")

    gt_degradation = calculate_gt_degradation(
        rain_noise_temp, rx_feed_loss, rx_system_noise_temp
    )
    print_param("输出 G/T下降", gt_degradation, "dB")

    # ==================== 5. 卫星功率分配 ====================
    print_section("5. 卫星功率分配")

    sat_eirp_ss = sat.get('eirp_ss', 0)
    sat_bo_o = sat.get('bo_o', 3)
    sat_bo_i = sat.get('bo_i', 6)

    print_param("输入 卫星饱和EIRP", sat_eirp_ss, "dBW")
    print_param("输入 输出回退", sat_bo_o, "dB")
    print_param("输入 卫星SFD", sat_sfd, "dB(W/m²)")
    print_param("输入 带宽占用比", bw_ratio / 100, "")
    print_param("输入 输入回退", sat_bo_i, "dB")

    eirp_sl, pfd, bo_il, bo_ol = calculate_satellite_power_allocation(
        sat_eirp_ss, sat_bo_o, sat_sfd, bw_ratio / 100, sat_bo_i
    )
    print_param("输出 卫星EIRP", eirp_sl, "dBW")
    print_param("输出 通量密度", pfd, "dB(W/m²)")
    print_param("输出 实际输入回退", bo_il, "dB")
    print_param("输出 实际输出回退", bo_ol, "dB")

    # ==================== 6. 反向计算：UPC余量和功放功率 ====================
    print_section("6. 反向计算：UPC余量和功放功率")

    tx_loss_at = tx.get('loss_at', 0.5)
    tx_feed_loss = tx.get('feed_loss', 1.5)
    upc_max = tx.get('upc_max_comp', 5.0)
    tx_hpa_bo = tx.get('hpa_bo', 3.0)

    print_param("输入 上行降雨衰减", uplink_rain_att, "dB")
    print_param("输入 卫星SFD", sat_sfd, "dB(W/m²)")
    print_param("输入 实际输入回退", bo_il, "dB")
    print_param("输入 发射天线单位面积增益", gm2_tx, "dB/m²")
    print_param("输入 上行自由空间损耗", uplink_loss, "dB")
    print_param("输入 AT损耗", tx_loss_at, "dB")
    print_param("输入 发射天线增益", tx_antenna_gain, "dBi")
    print_param("输入 发射馈线损耗", tx_feed_loss, "dB")
    print_param("输入 UPC最大补偿", upc_max, "dB")
    print_param("输入 功放回退", tx_hpa_bo, "dB")

    # 所需UPC余量等于降雨衰减量
    required_upc = uplink_rain_att

    # 晴天EIRP
    eirp_el_clear = sat_sfd - bo_il - gm2_tx + uplink_loss + tx_loss_at

    # 雨天EIRP (含UPC补偿)
    eirp_el_rain = eirp_el_clear + required_upc

    # 晴天载波所需发射功率
    power_el_clear_dBW = eirp_el_clear - tx_antenna_gain + tx_feed_loss
    power_el_clear_W = 10 ** (power_el_clear_dBW / 10)

    # 晴天功放输出功率（考虑回退）
    hpa_power_clear_dBW = power_el_clear_dBW + tx_hpa_bo
    hpa_power_clear_W = 10 ** (hpa_power_clear_dBW / 10)

    # 雨天载波所需发射功率
    power_el_rain_dBW = eirp_el_rain - tx_antenna_gain + tx_feed_loss
    power_el_rain_W = 10 ** (power_el_rain_dBW / 10)

    # 雨天功放输出功率（考虑回退）
    hpa_power_rain_dBW = power_el_rain_dBW + tx_hpa_bo
    hpa_power_rain_W = 10 ** (hpa_power_rain_dBW / 10)

    upc_sufficient = required_upc <= upc_max

    print_param("输出 所需UPC余量", required_upc, "dB")
    print_param("输出 晴天EIRP", eirp_el_clear, "dBW")
    print_param("输出 雨天EIRP", eirp_el_rain, "dBW")
    print_param("输出 晴天载波发射功率", power_el_clear_dBW, "dBW (" + str(power_el_clear_W) + " W)")
    print_param("输出 晴天功放输出功率", hpa_power_clear_dBW, "dBW (" + str(hpa_power_clear_W) + " W)")
    print_param("输出 雨天载波发射功率", power_el_rain_dBW, "dBW (" + str(power_el_rain_W) + " W)")
    print_param("输出 雨天功放输出功率", hpa_power_rain_dBW, "dBW (" + str(hpa_power_rain_W) + " W)")
    print_param("输出 UPC是否足够", upc_sufficient, "")

    # ==================== 7. 晴天链路计算 ====================
    print_section("7. 晴天链路计算 (M06)")

    print_subsection("7.1 固定大气衰减")
    tx_fixed_attenuation = (tx_rain_result.get('gas_attenuation_dB', 0) +
                            tx_rain_result.get('cloud_attenuation_dB', 0) +
                            tx_rain_result.get('scintillation_attenuation_dB', 0))
    print_param("发射站固定大气衰减", tx_fixed_attenuation, "dB")
    print_param("  气体衰减", tx_rain_result.get('gas_attenuation_dB', 0), "dB")
    print_param("  云衰减", tx_rain_result.get('cloud_attenuation_dB', 0), "dB")
    print_param("  闪烁衰减", tx_rain_result.get('scintillation_attenuation_dB', 0), "dB")

    rx_fixed_attenuation = (rx_rain_result.get('gas_attenuation_dB', 0) +
                            rx_rain_result.get('cloud_attenuation_dB', 0) +
                            rx_rain_result.get('scintillation_attenuation_dB', 0))
    print_param("接收站固定大气衰减", rx_fixed_attenuation, "dB")
    print_param("  气体衰减", rx_rain_result.get('gas_attenuation_dB', 0), "dB")
    print_param("  云衰减", rx_rain_result.get('cloud_attenuation_dB', 0), "dB")
    print_param("  闪烁衰减", rx_rain_result.get('scintillation_attenuation_dB', 0), "dB")

    print_subsection("7.2 上行C/N计算")
    print_param("输入 通量密度", pfd, "dB(W/m²)")
    print_param("输入 发射天线单位面积增益", gm2_tx, "dB/m²")
    print_param("输入 卫星G/T", sat_gt, "dB/K")
    print_param("输入 噪声带宽", noise_bw, "Hz")

    cn_u_raw = calculate_uplink_cn(pfd, gm2_tx, sat_gt, noise_bw)
    print_param("输出 上行C/N(未减大气衰减)", cn_u_raw, "dB")

    cn_u = cn_u_raw - tx_fixed_attenuation
    print_param("输出 上行C/N", cn_u, "dB")

    print_subsection("7.3 下行C/N计算")
    rx_loss_ar = rx.get('loss_ar', 0.5)

    print_param("输入 卫星EIRP", eirp_sl, "dBW")
    print_param("输入 下行自由空间损耗", downlink_loss, "dB")
    print_param("输入 AR损耗", rx_loss_ar, "dB")
    print_param("输入 地球站G/T", rx_gt, "dB/K")
    print_param("输入 噪声带宽", noise_bw, "Hz")

    cn_d_raw = calculate_downlink_cn(eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw)
    print_param("输出 下行C/N(未减大气衰减)", cn_d_raw, "dB")

    cn_d = cn_d_raw - rx_fixed_attenuation
    print_param("输出 下行C/N", cn_d, "dB")

    print_subsection("7.4 干扰C/I计算")
    ci0_im = interference.get('ci0_im')
    ci0_u_as = interference.get('ci0_u_as')
    ci0_d_as = interference.get('ci0_d_as')
    ci0_u_xp = interference.get('ci0_u_xp')
    ci0_d_xp = interference.get('ci0_d_xp')
    adj_sat_lon = sat.get('adj_sat_longitude')

    if ci0_im is not None:
        print_param("输入 C/I(镜像)", ci0_im, "dB")
        ci_im = calculate_interference_ci(ci0_im, bo_ol, noise_bw)
        print_param("输出 C/I(镜像)", ci_im, "dB")
    else:
        ci_im = 99
        print_param("C/I(镜像)", ci_im, "dB (默认)")

    if ci0_u_as is not None:
        print_param("输入 C/I(上行邻星)", ci0_u_as, "dB")
        ci_u_as = calculate_interference_ci(ci0_u_as, bo_il, noise_bw)
        print_param("输出 C/I(上行邻星)", ci_u_as, "dB")
    else:
        ci_u_as = 99
        print_param("C/I(上行邻星)", ci_u_as, "dB (默认)")

    if ci0_d_as is not None:
        print_param("输入 C/I(下行邻星)", ci0_d_as, "dB")
        if adj_sat_lon is not None:
            topocentric_angle = 1.1 * abs(adj_sat_lon - sat_longitude)
            print_param("  顶心角", topocentric_angle, "°")
            # 计算偏轴增益（简化）
            wavelength = LIGHT_SPEED / (rx_frequency * 1e9)
            d_lambda = rx_antenna_diameter / wavelength
            off_axis_gain_rx = 10 * __import__('math').log10(max(1, 1000 * (wavelength / rx_antenna_diameter) ** 2))
            print_param("  偏轴增益", off_axis_gain_rx, "dBi")
        else:
            off_axis_gain_rx = 0
            print_param("  偏轴增益", off_axis_gain_rx, "dBi (未提供邻星经度)")
        ci_d_as = calculate_interference_ci(
            ci0_d_as, bo_ol, noise_bw, rx_antenna_gain, off_axis_gain_rx, 'downlink_adjacent'
        )
        print_param("输出 C/I(下行邻星)", ci_d_as, "dB")
    else:
        ci_d_as = 99
        print_param("C/I(下行邻星)", ci_d_as, "dB (默认)")

    if ci0_u_xp is not None:
        print_param("输入 C/I(上行交叉极化)", ci0_u_xp, "dB")
        ci_u_xp = calculate_interference_ci(ci0_u_xp, bo_il, noise_bw)
        print_param("输出 C/I(上行交叉极化)", ci_u_xp, "dB")
    else:
        ci_u_xp = 99
        print_param("C/I(上行交叉极化)", ci_u_xp, "dB (默认)")

    if ci0_d_xp is not None:
        print_param("输入 C/I(下行交叉极化)", ci0_d_xp, "dB")
        ci_d_xp = calculate_interference_ci(ci0_d_xp, bo_ol, noise_bw)
        print_param("输出 C/I(下行交叉极化)", ci_d_xp, "dB")
    else:
        ci_d_xp = 99
        print_param("C/I(下行交叉极化)", ci_d_xp, "dB (默认)")

    print_subsection("7.5 系统总C/N计算")
    print_param("输入 上行C/N", cn_u, "dB")
    print_param("输入 下行C/N", cn_d, "dB")
    print_param("输入 C/I(镜像)", ci_im, "dB")
    print_param("输入 C/I(上行邻星)", ci_u_as, "dB")
    print_param("输入 C/I(下行邻星)", ci_d_as, "dB")
    print_param("输入 C/I(上行交叉极化)", ci_u_xp, "dB")
    print_param("输入 C/I(下行交叉极化)", ci_d_xp, "dB")

    cn_t = calculate_system_cn(cn_u, cn_d, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp)
    print_param("输出 系统总C/N", cn_t, "dB")

    print_subsection("7.6 门限C/N和余量计算")
    ebno_th = carrier.get('ebno_threshold', 4.5)

    print_param("输入 Eb/N0门限", ebno_th, "dB")
    print_param("输入 信息速率", info_rate, "bps")
    print_param("输入 噪声带宽", noise_bw, "Hz")

    cn_th = calculate_threshold_cn(ebno_th, info_rate, noise_bw)
    print_param("输出 门限C/N", cn_th, "dB")

    print_param("输入 系统总C/N", cn_t, "dB")
    print_param("输入 门限C/N", cn_th, "dB")

    margin = calculate_margin(cn_t, cn_th)
    print_param("输出 晴天系统余量", margin, "dB")

    print_subsection("7.7 地球站发射参数")
    print_param("输入 卫星SFD", sat_sfd, "dB(W/m²)")
    print_param("输入 实际输入回退", bo_il, "dB")
    print_param("输入 发射天线单位面积增益", gm2_tx, "dB/m²")
    print_param("输入 上行自由空间损耗", uplink_loss, "dB")
    print_param("输入 AT损耗", tx_loss_at, "dB")

    eirp_el = calculate_earth_station_eirp(sat_sfd, bo_il, gm2_tx, uplink_loss, tx_loss_at)
    print_param("输出 地球站EIRP", eirp_el, "dBW")

    print_param("输入 EIRP", eirp_el, "dBW")
    print_param("输入 天线增益", tx_antenna_gain, "dBi")
    print_param("输入 馈线损耗", tx_feed_loss, "dB")
    print_param("输入 噪声带宽", noise_bw, "Hz")
    print_param("输入 功放回退", tx_hpa_bo, "dB")

    power_el_dBW, power_el_W, hpa_power_dBW, hpa_power_W, _, _ = calculate_hpa_power(
        eirp_el, tx_antenna_gain, tx_feed_loss, noise_bw, tx_hpa_bo
    )
    print_param("输出 载波发射功率", power_el_dBW, "dBW (" + str(power_el_W) + " W)")
    print_param("输出 功放输出功率", hpa_power_dBW, "dBW (" + str(hpa_power_W) + " W)")

    print_subsection("7.8 功率占用比")
    print_param("输入 卫星EIRP", eirp_sl, "dBW")
    print_param("输入 卫星饱和EIRP", sat_eirp_ss, "dBW")
    print_param("输入 输出回退", sat_bo_o, "dB")

    power_ratio = calculate_power_ratio(eirp_sl, sat_eirp_ss, sat_bo_o)
    print_param("输出 功率占用比", power_ratio, "%")

    # ==================== 8. 上行降雨计算 ====================
    print_section("8. 上行降雨计算 (M07)")

    print_param("输入 卫星饱和EIRP", sat_eirp_ss, "dBW")
    print_param("输入 实际输出回退", bo_ol, "dB")
    print_param("输入 上行降雨衰减", uplink_rain_att, "dB")
    print_param("输入 UPC最大补偿", upc_max, "dB")
    print_param("输入 卫星SFD", sat_sfd, "dB(W/m²)")
    print_param("输入 实际输入回退", bo_il, "dB")
    print_param("输入 发射天线单位面积增益", gm2_tx, "dB/m²")
    print_param("输入 上行自由空间损耗", uplink_loss, "dB")
    print_param("输入 AT损耗", tx_loss_at, "dB")

    upc_comp, eirp_sl_rain_u, eirp_el_rain_u = calculate_uplink_rain_impact(
        sat_eirp_ss, bo_ol, uplink_rain_att, upc_max,
        sat_sfd, bo_il, gm2_tx, uplink_loss, tx_loss_at
    )
    print_param("输出 UPC补偿量", upc_comp, "dB")
    print_param("输出 雨天卫星EIRP", eirp_sl_rain_u, "dBW")
    print_param("输出 雨天地球站EIRP", eirp_el_rain_u, "dBW")

    # 上行降雨时的余量
    margin_uplink_rain = margin if upc_comp >= uplink_rain_att else margin - (uplink_rain_att - upc_comp)
    print_param("输出 上行降雨余量", margin_uplink_rain, "dB")

    print_param("输入 雨天地球站EIRP", eirp_el_rain_u, "dBW")
    print_param("输入 天线增益", tx_antenna_gain, "dBi")
    print_param("输入 馈线损耗", tx_feed_loss, "dB")
    print_param("输入 噪声带宽", noise_bw, "Hz")
    print_param("输入 功放回退", tx_hpa_bo, "dB")

    power_el_dBW_rain, power_el_W_rain, hpa_power_dBW_rain, hpa_power_W_rain, _, _ = calculate_hpa_power(
        eirp_el_rain_u, tx_antenna_gain, tx_feed_loss, noise_bw, tx_hpa_bo
    )
    print_param("输出 上行降雨载波发射功率", power_el_dBW_rain, "dBW (" + str(power_el_W_rain) + " W)")
    print_param("输出 上行降雨功放输出功率", hpa_power_dBW_rain, "dBW (" + str(hpa_power_W_rain) + " W)")

    # ==================== 9. 下行降雨计算 ====================
    print_section("9. 下行降雨计算 (M07)")

    print_param("输入 卫星EIRP", eirp_sl, "dBW")
    print_param("输入 下行自由空间损耗", downlink_loss, "dB")
    print_param("输入 AR损耗", rx_loss_ar, "dB")
    print_param("输入 下行降雨衰减", downlink_rain_att, "dB")
    print_param("输入 地球站G/T", rx_gt, "dB/K")
    print_param("输入 G/T下降", gt_degradation, "dB")
    print_param("输入 噪声带宽", noise_bw, "Hz")

    cn_d_rain = calculate_downlink_rain_cn(
        eirp_sl, downlink_loss, rx_loss_ar, downlink_rain_att,
        rx_gt, gt_degradation, noise_bw
    )
    print_param("输出 下行降雨下行C/N", cn_d_rain, "dB")

    # 重新计算系统C/N
    cn_t_rain = calculate_system_cn(
        cn_u, cn_d_rain, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
    )
    print_param("输出 下行降雨系统总C/N", cn_t_rain, "dB")

    margin_downlink_rain = calculate_margin(cn_t_rain, cn_th)
    print_param("输出 下行降雨余量", margin_downlink_rain, "dB")

    # ==================== 10. 余量调整 (可选) ====================
    if target_margin > 0:
        print_section("10. 余量调整")

        print_param("输入 目标余量", target_margin, "dB")
        print_param("输入 当前卫星EIRP", eirp_sl, "dBW")
        print_param("输入 卫星饱和EIRP", sat_eirp_ss, "dBW")
        print_param("输入 通量密度", pfd, "dB(W/m²)")
        print_param("输入 门限C/N", cn_th, "dB")

        from ydt2721.core.margin_adjuster import adjust_satellite_eirp

        adjustment = adjust_satellite_eirp(
            target_margin=target_margin,
            current_eirp_sl=eirp_sl,
            max_eirp_ss=sat_eirp_ss,
            pfd=pfd,
            gm2_tx=gm2_tx,
            sat_gt=sat_gt,
            downlink_loss=downlink_loss,
            rx_loss_ar=rx_loss_ar,
            rx_gt=rx_gt,
            noise_bw=noise_bw,
            cn_th=cn_th,
            ci_im=ci_im,
            ci_u_as=ci_u_as,
            ci_d_as=ci_d_as,
            ci_u_xp=ci_u_xp,
            ci_d_xp=ci_d_xp
        )

        print_param("输出 调整后卫星EIRP", adjustment['adjusted_eirp_sl'], "dBW")
        print_param("输出 调整后余量", adjustment['final_margin'], "dB")
        print_param("输出 EIRP调整量", adjustment['eirp_adjustment'], "dB")
        print_param("输出 迭代次数", adjustment['iterations'], "")

        eirp_adjustment = adjustment['eirp_adjustment']

        # 调整后的载波发射功率
        adjusted_power_el_dBW = power_el_dBW + eirp_adjustment
        adjusted_power_el_W = 10 ** (adjusted_power_el_dBW / 10)
        print_param("输出 调整后载波发射功率", adjusted_power_el_dBW, "dBW (" + str(adjusted_power_el_W) + " W)")

        # 调整后的功放功率
        adjusted_hpa_power_dBW = adjusted_power_el_dBW + tx_hpa_bo
        adjusted_hpa_power_W = 10 ** (adjusted_hpa_power_dBW / 10)
        print_param("输出 调整后功放功率", adjusted_hpa_power_dBW, "dBW (" + str(adjusted_hpa_power_W) + " W)")

        # 调整后的功率占用比
        eirp_adjustment_linear = 10 ** (eirp_adjustment / 10)
        adjusted_power_ratio = power_ratio * eirp_adjustment_linear
        print_param("输出 调整后功率占用比", adjusted_power_ratio, "%")

        # 调整后的C/N值
        pfd_adjusted = pfd + eirp_adjustment
        adjusted_cn_u = calculate_uplink_cn(pfd_adjusted, gm2_tx, sat_gt, noise_bw)
        print_param("输出 调整后上行C/N", adjusted_cn_u, "dB")

        adjusted_cn_d = calculate_downlink_cn(
            adjustment['adjusted_eirp_sl'], downlink_loss, rx_loss_ar, rx_gt, noise_bw
        )
        print_param("输出 调整后下行C/N", adjusted_cn_d, "dB")

        adjusted_cn_t = calculate_system_cn(
            adjusted_cn_u, adjusted_cn_d, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
        )
        print_param("输出 调整后系统总C/N", adjusted_cn_t, "dB")

        # 上行降雨时
        upc_comp = min(uplink_rain_att, upc_max)
        adjusted_uplink_rain_power_el_dBW = adjusted_power_el_dBW + upc_comp
        adjusted_uplink_rain_power_el_W = 10 ** (adjusted_uplink_rain_power_el_dBW / 10)
        print_param("输出 调整后上行降雨载波发射功率", adjusted_uplink_rain_power_el_dBW, "dBW (" + str(adjusted_uplink_rain_power_el_W) + " W)")

        adjusted_uplink_rain_hpa_power_dBW = adjusted_uplink_rain_power_el_dBW + tx_hpa_bo
        adjusted_uplink_rain_hpa_power_W = 10 ** (adjusted_uplink_rain_hpa_power_dBW / 10)
        print_param("输出 调整后上行降雨功放功率", adjusted_uplink_rain_hpa_power_dBW, "dBW (" + str(adjusted_uplink_rain_hpa_power_W) + " W)")

        # 下行降雨时
        cn_d_downlink_rain_adj = calculate_downlink_rain_cn(
            adjustment['adjusted_eirp_sl'], downlink_loss, rx_loss_ar, downlink_rain_att,
            rx_gt, gt_degradation, noise_bw
        )
        cn_t_downlink_rain_adj = calculate_system_cn(
            adjusted_cn_u, cn_d_downlink_rain_adj, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp
        )
        margin_downlink_rain_adj = cn_t_downlink_rain_adj - cn_th
        print_param("输出 调整后下行降雨余量", margin_downlink_rain_adj, "dB")

    # ==================== 总结 ====================
    print_section("总结")
    print_subsection("晴天结果")
    print_param("符号速率", symbol_rate / 1e6, "Msym/s")
    print_param("带宽占用比", bw_ratio, "%")
    print_param("仰角", rx_elevation, "°")
    print_param("晴天系统余量", margin, "dB")
    print_param("晴天载波发射功率", power_el_W, "W (" + str(power_el_dBW) + " dBW)")
    print_param("晴天功放输出功率", hpa_power_W, "W (" + str(hpa_power_dBW) + " dBW)")

    print_subsection("上行降雨结果")
    print_param("上行降雨衰减", uplink_rain_att, "dB")
    print_param("UPC补偿量", upc_comp, "dB")
    print_param("上行降雨余量", margin_uplink_rain, "dB")
    print_param("上行降雨载波发射功率", power_el_W_rain, "W (" + str(power_el_dBW_rain) + " dBW)")
    print_param("上行降雨功放输出功率", hpa_power_W_rain, "W (" + str(hpa_power_dBW_rain) + " dBW)")

    print_subsection("下行降雨结果")
    print_param("下行降雨衰减", downlink_rain_att, "dB")
    print_param("下行降雨余量", margin_downlink_rain, "dB")

    print("\n" + "=" * 70)
    print("  计算完成")
    print("=" * 70)

    return True


def main():
    """主函数"""
    # 修复Windows控制台编码问题
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='YDT 2721 卫星链路计算检查程序 - 输出所有中间参数'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        required=True,
        help='参数配置文件（JSON格式）'
    )
    parser.add_argument(
        '--target-margin',
        type=float,
        default=0.0,
        help='目标系统余量 (dB)，默认0'
    )
    parser.add_argument(
        '--station-height',
        type=float,
        default=0.0,
        help='地球站海拔高度 (km)，默认0'
    )

    args = parser.parse_args()

    # 加载配置文件
    config = load_config(args.config)

    # 执行详细计算
    execute_calculation_with_detail(
        config,
        target_margin=args.target_margin,
        station_height=args.station_height
    )


if __name__ == '__main__':
    main()
