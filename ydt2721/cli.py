#!/usr/bin/env python3
"""
YDT 2721 卫星链路计算软件 - CLI命令行界面
"""

import argparse
import sys
import os
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721 import (
    complete_link_budget,
    MarkdownReportGenerator,
    ExcelReportGenerator,
    JSONExporter,
    PDFReportGenerator,
    setup_chinese_fonts,
    FontManager,
)
from ydt2721.core.param_manager import ParameterValidator, ParameterManager
from ydt2721.core.satellite import calculate_sfd, calculate_antenna_gain_per_area
from ydt2721.core.earth_station import calculate_antenna_pointing, calculate_antenna_gain, calculate_satellite_distance
from ydt2721.core.space_loss import calculate_free_space_loss
from ydt2721.core.reverse_calc import (
    calculate_uplink_power_from_upc,
    invert_availability_from_rain_attenuation,
    analyze_power_margin,
)
from ydt2721.models.dataclass import (
    SatelliteParams,
    CarrierParams,
    EarthStationParams,
)
from ydt2721.core.constants import LIGHT_SPEED


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='YDT 2721 卫星链路计算软件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用配置文件计算
  %(prog)s calculate --config params.json

  # 生成所有格式报告
  %(prog)s calculate --config params.json --output report

  # 交互式输入
  %(prog)s interactive

  # 验证参数
  %(prog)s validate --config params.json

计算模式:
  --calc-mode power
    根据可用度需求计算所需功放功率（默认模式）

  --calc-mode availability
    根据预留的 UPC 补偿量计算可达可用度
    需要配合 --upc-reserved 参数使用

  --upc-reserved dB
    预留的 UPC 补偿量 (dB)，仅在 availability 模式下使用

  --hpa-power watts
    指定功放功率 (W)，分析给定功放可支持的可用度
    可与 power 或 availability 模式配合使用

降雨衰减模型:
  使用 ITU-Rpy 完整标准计算（高精度，包含气体、云、闪烁衰减）
  - 计算速度: ~5ms
  - 精度: ±10%%
  - 功能: 气体 + 云 + 降雨 + 闪烁衰减
  - 依赖: itur, numpy, scipy, pyproj, astropy

推荐使用场景:
  - 精确工程计算
  - 商用链路设计
  - 正式报告生成

注意:
  - ITU-Rpy 需要安装: pip install itur
  - 更多信息请参考: ITURPY_SUMMARY.md

字体设置:
  首次生成PDF报告前，建议运行: ydt2721 font setup
  这将下载开源中文字体 (Source Han Sans / 思源黑体)
  字体将保存在用户目录下的 ~/.ydt2721/fonts/
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # calculate命令
    calc_parser = subparsers.add_parser('calculate', help='执行链路计算')
    calc_parser.add_argument(
        '--config', '-c',
        type=str,
        help='参数配置文件（JSON格式）'
    )
    calc_parser.add_argument(
        '--output', '-o',
        type=str,
        default='report',
        help='输出文件前缀（默认: report）'
    )
    calc_parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['all', 'markdown', 'excel', 'json', 'pdf'],
        default='all',
        help='输出格式（默认: all）'
    )
    calc_parser.add_argument(
        '--no-validate',
        action='store_true',
        help='跳过参数验证'
    )
    calc_parser.add_argument(
        '--calc-mode',
        type=str,
        choices=['power', 'availability'],
        default='power',
        help='计算模式: power=根据可用度计算功率, availability=根据UPC计算可用度 (默认: power)'
    )
    calc_parser.add_argument(
        '--upc-reserved',
        type=float,
        default=None,
        help='预留的UPC补偿量 (dB)，仅在availability模式下使用'
    )
    calc_parser.add_argument(
        '--hpa-power',
        type=float,
        default=None,
        help='指定功放功率 (W)，用于分析给定功放可支持的可用度'
    )
    calc_parser.add_argument(
        '--target-margin',
        type=float,
        default=None,
        help='目标系统余量 (dB)，调整EIRP以实现目标余量'
    )
    calc_parser.add_argument(
        '--station-height',
        type=float,
        default=0.0,
        help='地球站海拔高度 (km)，默认0'
    )
    calc_parser.add_argument(
        '--print-json',
        action='store_true',
        help='在控制台输出JSON结果'
    )
    calc_parser.add_argument(
        '--setup-fonts',
        action='store_true',
        help='在生成报告前下载中文字体'
    )

    # interactive命令
    interactive_parser = subparsers.add_parser('interactive', help='交互式计算')
    interactive_parser.add_argument(
        '--output', '-o',
        type=str,
        default='report',
        help='输出文件前缀（默认: report）'
    )
    interactive_parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['all', 'markdown', 'excel', 'json', 'pdf'],
        default='all',
        help='输出格式（默认: all）'
    )

    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证参数配置')
    validate_parser.add_argument(
        '--config', '-c',
        type=str,
        required=True,
        help='参数配置文件（JSON格式）'
    )

    # template命令
    template_parser = subparsers.add_parser('template', help='生成参数模板')
    template_parser.add_argument(
        '--output', '-o',
        type=str,
        default='template.json',
        help='输出文件路径（默认: template.json）'
    )

    # font命令
    font_parser = subparsers.add_parser('font', help='中文字体管理')
    font_subparsers = font_parser.add_subparsers(dest='font_command', help='字体子命令')

    # font setup命令
    font_setup_parser = font_subparsers.add_parser('setup', help='下载并设置中文字体')
    font_setup_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制重新下载字体'
    )

    # font info命令
    font_info_parser = font_subparsers.add_parser('info', help='显示字体状态信息')

    # font remove命令
    font_remove_parser = font_subparsers.add_parser('remove', help='删除已下载的字体文件')

    return parser


def load_config(config_file: str) -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_config(config: dict) -> bool:
    """验证配置文件"""
    validator = ParameterValidator()

    # 构建参数对象
    try:
        satellite = SatelliteParams(**config.get('satellite', {}))
        carrier = CarrierParams(**config.get('carrier', {}))
        tx_station = EarthStationParams(**config.get('tx_station', {}))
        rx_station = EarthStationParams(**config.get('rx_station', {}))
        system = config.get('system', {})
        uplink_availability = system.get('uplink_availability', 99.9)
        downlink_availability = system.get('downlink_availability', 99.9)

        errors = validator.validate_all_params(satellite, carrier, tx_station, rx_station, uplink_availability, downlink_availability)

        if errors:
            print("❌ 参数验证失败：")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("✅ 参数验证通过")
            return True

    except Exception as e:
        print(f"❌ 参数解析错误: {e}")
        return False


def execute_reverse_calculation(config: dict, output_prefix: str, output_format: str,
                                 upc_reserved: float, station_height: float = 0.0) -> bool:
    """执行反向计算：根据UPC补偿量计算可达可用度"""
    # 提取参数
    sat = config.get('satellite', {})
    tx = config.get('tx_station', {})
    system = config.get('system', {})

    # 卫星参数
    sat_sfd_ref = sat.get('sfd_ref', 0)
    sat_gt = sat.get('gt_s', 0)
    sat_gt_ref = sat.get('gt_s_ref', 0)
    sat_bo_i = sat.get('bo_i', 6)
    sat_longitude = sat.get('longitude', 0)

    # 发射站参数
    tx_lat = tx.get('latitude', 0)
    tx_lon = tx.get('longitude', 0)
    tx_frequency = tx.get('frequency', 14.25)
    tx_polarization = tx.get('polarization', 'V')
    tx_antenna_diameter = tx.get('antenna_diameter', 4.5)
    tx_efficiency = tx.get('efficiency', 0.65)
    tx_loss_at = tx.get('loss_at', 0.5)

    # 计算所需参数
    sat_sfd = calculate_sfd(sat_sfd_ref, sat_gt, sat_gt_ref)
    gm2_tx = calculate_antenna_gain_per_area(tx_frequency * 1e9)

    # 计算仰角和距离
    tx_elevation, _ = calculate_antenna_pointing(tx_lat, tx_lon, sat_longitude)
    tx_distance = calculate_satellite_distance(tx_lat, tx_lon, sat_longitude)
    uplink_loss = calculate_free_space_loss(tx_frequency * 1e3, tx_distance)

    # 根据预留UPC反推可用度
    print("\n正在执行反向计算...")
    print(f"计算模式: 根据UPC补偿量计算可用度")
    print(f"降雨衰减模型: ITU-Rpy")
    print(f"预留UPC补偿量: {upc_reserved} dB")

    # 计算雨天可补偿的降雨衰减
    upc_max = tx.get('upc_max_comp', 5.0)
    if upc_reserved > upc_max:
        print(f"警告: 预留UPC ({upc_reserved} dB) 超过最大UPC ({upc_max} dB)")
        print(f"   实际可用的UPC补偿量: {upc_max} dB")
        upc_reserved = upc_max

    # 可补偿的降雨衰减
    compensable_rain_att = upc_reserved

    # 反推可用度
    availability, details = invert_availability_from_rain_attenuation(
        target_rain_att=compensable_rain_att,
        lat=tx_lat,
        lon=tx_lon,
        satellite_lon=sat_longitude,
        frequency=tx_frequency,
        polarization=tx_polarization,
        antenna_diameter=tx_antenna_diameter,
        elevation=tx_elevation,
        station_height=station_height,
        rain_model='iturpy'
    )

    # 计算功放参数需求
    power_result = calculate_uplink_power_from_upc(
        upc_reserved=upc_reserved,
        sfd=sat_sfd,
        bo_il=sat_bo_i,
        gm2=gm2_tx,
        loss_u=uplink_loss,
        loss_at=tx_loss_at
    )

    # 计算天线增益
    tx_wavelength = LIGHT_SPEED / (tx_frequency * 1e9)
    tx_antenna_gain = calculate_antenna_gain(tx_antenna_diameter, tx_wavelength, tx_efficiency)

    # 晴天功放功率
    eirp_el_clear = power_result['eirp_el_clear_dBW']
    hpa_power_clear_dbw = eirp_el_clear - tx_antenna_gain + tx.get('feed_loss', 1.5)
    hpa_power_clear_w = 10 ** (hpa_power_clear_dbw / 10)

    # 雨天功放功率
    eirp_el_rain = power_result['eirp_el_rain_dBW']
    hpa_power_rain_dbw = eirp_el_rain - tx_antenna_gain + tx.get('feed_loss', 1.5)
    hpa_power_rain_w = 10 ** (hpa_power_rain_dbw / 10)

    # 显示结果
    print("\n📊 计算结果：")
    print(f"\n  【可用度分析】")
    print(f"  可达上行可用度: {availability:.4f} %")
    print(f"  对应不可用度: {details['unavailability']:.4f} %")
    print(f"  可补偿降雨衰减: {compensable_rain_att:.4f} dB")
    print(f"  计算误差: {details['error_dB']:.4f} dB")

    print(f"\n  【功放功率需求】")
    print(f"  晴天功放功率: {hpa_power_clear_w:.4f} W ({hpa_power_clear_dbw:.2f} dBW)")
    print(f"  雨天功放功率: {hpa_power_rain_w:.4f} W ({hpa_power_rain_dbw:.2f} dBW)")
    print(f"  雨天功率增加: {power_result['eirp_increase_dB']:.2f} dB")
    print(f"  功率增加倍数: {hpa_power_rain_w / hpa_power_clear_w:.2f}x")

    print(f"\n  【EIRP】")
    print(f"  晴天EIRP: {power_result['eirp_el_clear_dBW']:.2f} dBW")
    print(f"  雨天EIRP: {power_result['eirp_el_rain_dBW']:.2f} dBW")

    # 生成JSON报告
    if output_format in ['all', 'json']:
        result = {
            'calculation_mode': 'availability_from_upc',
            'rain_model': 'iturpy',
            'upc_reserved_dB': upc_reserved,
            'availability': {
                'uplink': availability,
                'unavailability': details['unavailability'],
                'compensable_rain_attenuation_dB': compensable_rain_att
            },
            'hpa_power': {
                'clear_sky_W': hpa_power_clear_w,
                'clear_sky_dBW': hpa_power_clear_dbw,
                'rain_W': hpa_power_rain_w,
                'rain_dBW': hpa_power_rain_dbw,
                'increase_dB': power_result['eirp_increase_dB'],
                'increase_ratio': hpa_power_rain_w / hpa_power_clear_w
            },
            'eirp': {
                'clear_sky_dBW': power_result['eirp_el_clear_dBW'],
                'rain_dBW': power_result['eirp_el_rain_dBW']
            },
            'details': details
        }

        json_file = f"{output_prefix}.json"
        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n  ✅ JSON报告: {json_file}")

    print("\n✅ 完成！")
    return True


def execute_power_margin_analysis(config: dict, output_prefix: str,
                                    hpa_power_w: float, station_height: float = 0.0) -> bool:
    """分析给定功放功率可支持的可用度"""
    # 提取参数
    sat = config.get('satellite', {})
    tx = config.get('tx_station', {})

    # 卫星参数
    sat_sfd_ref = sat.get('sfd_ref', 0)
    sat_gt = sat.get('gt_s', 0)
    sat_gt_ref = sat.get('gt_s_ref', 0)
    sat_bo_i = sat.get('bo_i', 6)
    sat_longitude = sat.get('longitude', 0)

    # 发射站参数
    tx_lat = tx.get('latitude', 0)
    tx_lon = tx.get('longitude', 0)
    tx_frequency = tx.get('frequency', 14.25)
    tx_polarization = tx.get('polarization', 'V')
    tx_antenna_diameter = tx.get('antenna_diameter', 4.5)
    tx_efficiency = tx.get('efficiency', 0.65)
    tx_feed_loss = tx.get('feed_loss', 1.5)
    tx_loss_at = tx.get('loss_at', 0.5)
    upc_max = tx.get('upc_max_comp', 5.0)

    # 计算所需参数
    sat_sfd = calculate_sfd(sat_sfd_ref, sat_gt, sat_gt_ref)
    gm2_tx = calculate_antenna_gain_per_area(tx_frequency * 1e9)

    # 计算仰角和距离
    tx_elevation, _ = calculate_antenna_pointing(tx_lat, tx_lon, sat_longitude)
    tx_distance = calculate_satellite_distance(tx_lat, tx_lon, sat_longitude)
    uplink_loss = calculate_free_space_loss(tx_frequency * 1e3, tx_distance)

    # 计算天线增益
    tx_wavelength = LIGHT_SPEED / (tx_frequency * 1e9)
    tx_antenna_gain = calculate_antenna_gain(tx_antenna_diameter, tx_wavelength, tx_efficiency)

    print("\n正在分析功放功率余量...")
    print(f"降雨衰减模型: ITU-Rpy")
    print(f"指定功放功率: {hpa_power_w:.4f} W")

    # 分析功放余量
    result = analyze_power_margin(
        hpa_power_w=hpa_power_w,
        antenna_gain=tx_antenna_gain,
        feed_loss=tx_feed_loss,
        sfd=sat_sfd,
        bo_il=sat_bo_i,
        gm2=gm2_tx,
        loss_u=uplink_loss,
        loss_at=tx_loss_at,
        upc_max=upc_max,
        lat=tx_lat,
        lon=tx_lon,
        satellite_lon=sat_longitude,
        frequency=tx_frequency,
        polarization=tx_polarization,
        antenna_diameter=tx_antenna_diameter,
        elevation=tx_elevation,
        station_height=station_height,
        rain_model='iturpy'
    )

    # 显示结果
    print("\n📊 分析结果：")
    print(f"\n  【功放参数】")
    print(f"  功放功率: {result['hpa_power_W']:.4f} W ({result['hpa_power_dBW']:.2f} dBW)")
    print(f"  晴天EIRP: {result['eirp_el_clear_dBW']:.2f} dBW")

    print(f"\n  【UPC余量】")
    print(f"  UPC余量: {result['upc_margin_dB']:.2f} dB")
    print(f"  可用UPC: {result['upc_available_dB']:.2f} dB")
    print(f"  限制因素: {result['upc_limited_by']}")

    print(f"\n  【可达可用度】")
    print(f"  可达上行可用度: {result['supported_availability']:.4f} %")
    print(f"  对应不可用度: {result['unavailability']:.4f} %")
    print(f"  可补偿降雨衰减: {result['compensable_rain_attenuation_dB']:.4f} dB")

    # 生成JSON报告
    json_file = f"{output_prefix}.json"
    import json
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ JSON报告: {json_file}")

    print("\n✅ 完成！")
    return True


def execute_reverse_calculation_inline(config: dict, upc_reserved: float,
                                         station_height: float) -> dict:
    """执行反向计算（内联版本，返回结果字典）"""
    sat = config.get('satellite', {})
    tx = config.get('tx_station', {})

    sat_sfd_ref = sat.get('sfd_ref', 0)
    sat_gt = sat.get('gt_s', 0)
    sat_gt_ref = sat.get('gt_s_ref', 0)
    sat_bo_i = sat.get('bo_i', 6)
    sat_longitude = sat.get('longitude', 0)

    tx_lat = tx.get('latitude', 0)
    tx_lon = tx.get('longitude', 0)
    tx_frequency = tx.get('frequency', 14.25)
    tx_polarization = tx.get('polarization', 'V')
    tx_antenna_diameter = tx.get('antenna_diameter', 4.5)

    sat_sfd = calculate_sfd(sat_sfd_ref, sat_gt, sat_gt_ref)
    gm2_tx = calculate_antenna_gain_per_area(tx_frequency * 1e9)

    tx_elevation, _ = calculate_antenna_pointing(tx_lat, tx_lon, sat_longitude)
    tx_distance = calculate_satellite_distance(tx_lat, tx_lon, sat_longitude)
    uplink_loss = calculate_free_space_loss(tx_frequency * 1e3, tx_distance)

    print("\n" + "="*60)
    print("反向计算：根据UPC补偿量计算可达可用度")
    print("="*60)
    print(f"降雨衰减模型: ITU-Rpy")
    print(f"预留UPC补偿量: {upc_reserved} dB")

    upc_max = tx.get('upc_max_comp', 5.0)
    if upc_reserved > upc_max:
        print(f"⚠️  警告: 预留UPC ({upc_reserved} dB) 超过最大UPC ({upc_max} dB)")
        print(f"   实际可用的UPC补偿量: {upc_max} dB")
        upc_reserved = upc_max

    compensable_rain_att = upc_reserved

    availability, details = invert_availability_from_rain_attenuation(
        target_rain_att=compensable_rain_att,
        lat=tx_lat,
        lon=tx_lon,
        satellite_lon=sat_longitude,
        frequency=tx_frequency,
        polarization=tx_polarization,
        antenna_diameter=tx_antenna_diameter,
        elevation=tx_elevation,
        station_height=station_height,
        rain_model='iturpy'
    )

    print(f"\n  【可用度分析】")
    print(f"  可达上行可用度: {availability:.4f} %")
    print(f"  对应不可用度: {details['unavailability']:.4f} %")
    print(f"  可补偿降雨衰减: {compensable_rain_att:.4f} dB")

    return {
        'availability': availability,
        'unavailability': details['unavailability'],
        'compensable_rain_attenuation_dB': compensable_rain_att,
        'upc_reserved_dB': upc_reserved,
        'details': details
    }


def execute_calculation(config: dict, output_prefix: str, output_format: str, print_json: bool = False,
                       skip_validation: bool = False,
                       calc_mode: str = 'power', upc_reserved: float = None,
                       hpa_power: float = None, station_height: float = 0.0,
                       target_margin: float = None) -> bool:
    """执行链路计算"""
    config = json.loads(json.dumps(config))

    # 参数覆盖：--upc-reserved 覆盖配置文件中的 upc_max_comp
    if upc_reserved is not None:
        if 'tx_station' not in config:
            config['tx_station'] = {}
        config['tx_station']['upc_max_comp'] = upc_reserved

    # 存储反向计算结果
    reverse_calc_result = None

    # 处理 availability 计算模式
    if calc_mode == 'availability' and upc_reserved is not None:
        reverse_calc_result = execute_reverse_calculation_inline(
            config, upc_reserved, station_height
        )
        # 将计算出的可用度更新到配置中
        if 'system' not in config:
            config['system'] = {}
        config['system']['uplink_availability'] = reverse_calc_result['availability']

    # 处理 --hpa-power 功放余量分析
    if hpa_power is not None:
        sat = config.get('satellite', {})
        tx = config.get('tx_station', {})

        sat_sfd_ref = sat.get('sfd_ref', 0)
        sat_gt = sat.get('gt_s', 0)
        sat_gt_ref = sat.get('gt_s_ref', 0)
        sat_bo_i = sat.get('bo_i', 6)
        sat_longitude = sat.get('longitude', 0)

        tx_lat = tx.get('latitude', 0)
        tx_lon = tx.get('longitude', 0)
        tx_frequency = tx.get('frequency', 14.25)
        tx_polarization = tx.get('polarization', 'V')
        tx_antenna_diameter = tx.get('antenna_diameter', 4.5)
        tx_efficiency = tx.get('efficiency', 0.65)
        tx_feed_loss = tx.get('feed_loss', 1.5)
        tx_loss_at = tx.get('loss_at', 0.5)
        upc_max = tx.get('upc_max_comp', 5.0)

        sat_sfd = calculate_sfd(sat_sfd_ref, sat_gt, sat_gt_ref)
        gm2_tx = calculate_antenna_gain_per_area(tx_frequency * 1e9)

        tx_elevation, _ = calculate_antenna_pointing(tx_lat, tx_lon, sat_longitude)
        tx_distance = calculate_satellite_distance(tx_lat, tx_lon, sat_longitude)
        uplink_loss = calculate_free_space_loss(tx_frequency * 1e3, tx_distance)

        tx_wavelength = LIGHT_SPEED / (tx_frequency * 1e9)
        tx_antenna_gain = calculate_antenna_gain(tx_antenna_diameter, tx_wavelength, tx_efficiency)

        print("\n" + "="*60)
        print("🔧 功放功率余量分析")
        print("="*60)
        print(f"🔧 指定功放功率: {hpa_power:.4f} W")

        margin_result = analyze_power_margin(
            hpa_power_w=hpa_power,
            antenna_gain=tx_antenna_gain,
            feed_loss=tx_feed_loss,
            sfd=sat_sfd,
            bo_il=sat_bo_i,
            gm2=gm2_tx,
            loss_u=uplink_loss,
            loss_at=tx_loss_at,
            upc_max=upc_max,
            lat=tx_lat,
            lon=tx_lon,
            satellite_lon=sat_longitude,
            frequency=tx_frequency,
            polarization=tx_polarization,
            antenna_diameter=tx_antenna_diameter,
            elevation=tx_elevation,
            station_height=station_height,
            rain_model='iturpy'
        )

        print(f"\n  【功放参数】")
        print(f"  功放功率: {margin_result['hpa_power_W']:.4f} W ({margin_result['hpa_power_dBW']:.2f} dBW)")
        print(f"  晴天EIRP: {margin_result['eirp_el_clear_dBW']:.2f} dBW")

        print(f"\n  【UPC余量】")
        print(f"  UPC余量: {margin_result['upc_margin_dB']:.2f} dB")
        print(f"  可用UPC: {margin_result['upc_available_dB']:.2f} dB")
        print(f"  限制因素: {margin_result['upc_limited_by']}")

        print(f"\n  【可达可用度】")
        print(f"  可达上行可用度: {margin_result['supported_availability']:.4f} %")
        print(f"  对应不可用度: {margin_result['unavailability']:.4f} %")
        print(f"  可补偿降雨衰减: {margin_result['compensable_rain_attenuation_dB']:.4f} dB")

    # 验证参数
    if not skip_validation:
        if not validate_config(config):
            return False

    # 提取参数
    sat = config.get('satellite', {})
    carrier = config.get('carrier', {})
    tx = config.get('tx_station', {})
    rx = config.get('rx_station', {})
    system = config.get('system', {})
    interference = config.get('interference', {})

    # 执行计算
    print("\n正在执行链路计算...")
    print(f"降雨衰减模型: ITU-Rpy")
    result = complete_link_budget(
        # 卫星参数
        sat_longitude=sat.get('longitude', 0),
        sat_eirp_ss=sat.get('eirp_ss', 0),
        sat_gt=sat.get('gt_s', 0),
        sat_gt_ref=sat.get('gt_s_ref', 0),
        sat_sfd_ref=sat.get('sfd_ref', 0),
        sat_bo_i=sat.get('bo_i', 6),
        sat_bo_o=sat.get('bo_o', 3),
        sat_transponder_bw=sat.get('transponder_bw', 54000000),

        # 载波参数
        info_rate=carrier.get('info_rate', 2000000),
        fec_rate=carrier.get('fec_rate', 0.75),
        modulation=carrier.get('modulation', 'QPSK'),
        spread_gain=carrier.get('spread_gain', 1),
        ebno_th=carrier.get('ebno_threshold', 4.5),
        alpha1=carrier.get('alpha1', 1.2),
        alpha2=carrier.get('alpha2', 1.4),

        # 发射站参数
        tx_station_name=tx.get('name', '发射站'),
        tx_lat=tx.get('latitude', 0),
        tx_lon=tx.get('longitude', 0),
        tx_antenna_diameter=tx.get('antenna_diameter', 4.5),
        tx_efficiency=tx.get('efficiency', 0.65),
        tx_frequency=tx.get('frequency', 14.25),
        tx_polarization=tx.get('polarization', 'V'),
        tx_feed_loss=tx.get('feed_loss', 1.5),
        tx_loss_at=tx.get('loss_at', 0.5),
        upc_max=tx.get('upc_max_comp', 5.0),
        tx_hpa_bo=tx.get('hpa_bo', 3.0),

        # 接收站参数
        rx_station_name=rx.get('name', '接收站'),
        rx_lat=rx.get('latitude', 0),
        rx_lon=rx.get('longitude', 0),
        rx_antenna_diameter=rx.get('antenna_diameter', 1.8),
        rx_efficiency=rx.get('efficiency', 0.65),
        rx_frequency=rx.get('frequency', 12.50),
        rx_polarization=rx.get('polarization', 'H'),
        rx_feed_loss=rx.get('feed_loss', 0.2),
        rx_loss_ar=rx.get('loss_ar', 0.5),
        rx_antenna_noise_temp=rx.get('antenna_noise_temp', 35),
        rx_receiver_noise_temp=rx.get('receiver_noise_temp', 75),

        # 系统参数
        uplink_availability=system.get('uplink_availability', 99.9),
        downlink_availability=system.get('downlink_availability', 99.9),
        rain_model='iturpy',  # ITU-Rpy 模型
        # CLI参数优先级最高，然后是配置文件
        target_margin=target_margin if target_margin is not None else system.get('target_margin', 0.0),  # 目标余量

        # 干扰参数（可选）
        ci0_im=interference.get('ci0_im'),
        ci0_u_as=interference.get('ci0_u_as'),
        ci0_d_as=interference.get('ci0_d_as'),
        ci0_u_xp=interference.get('ci0_u_xp'),
        ci0_d_xp=interference.get('ci0_d_xp'),
        adj_sat_lon=sat.get('adj_sat_longitude'),
    )

    # 显示关键结果
    print("\n" + "="*60)
    print("📊 完整链路计算结果")
    print("="*60)
    print(f"  符号速率: {result.symbol_rate/1e6:.2f} Msym/s")
    print(f"  带宽占用比: {result.bandwidth_ratio:.2f}%")
    print(f"  仰角: {result.elevation:.2f}°")
    print(f"  晴天系统余量: {result.clear_sky_margin:.2f} dB")
    print(f"  上行降雨余量: {result.uplink_rain_margin:.2f} dB")
    print(f"  下行降雨余量: {result.downlink_rain_margin:.2f} dB")
    print(f"  晴天载波发射功率: {result.clear_sky_power_el_W:.4f} W ({result.clear_sky_power_el_dBW:.2f} dBW)")
    print(f"  晴天功放输出功率: {result.clear_sky_hpa_power_W:.4f} W ({result.clear_sky_hpa_power_dBW:.2f} dBW)")
    print(f"  上行雨天载波发射功率: {result.uplink_rain_power_el_W:.4f} W ({result.uplink_rain_power_el_dBW:.2f} dBW)")
    print(f"  上行雨天功放输出功率: {result.uplink_rain_hpa_power_W:.4f} W ({result.uplink_rain_hpa_power_dBW:.2f} dBW)")

    # 显示余量调整结果
    if result.margin_adjustment_enabled:
        print("\n" + "-"*60)
        print("🎯 余量调整结果")
        print("-"*60)
        print(f"  目标余量: {result.target_margin:.2f} dB")
        print(f"  原始余量: {result.clear_sky_margin:.2f} dB")
        print(f"  调整后余量: {result.final_margin:.2f} dB")
        print(f"  调整后EIRP: {result.adjusted_eirp_sl:.2f} dBW")
        print(f"  EIRP调整量: {result.adjusted_eirp_sl - result.satellite_eirp:.2f} dB")
        print(f"  调整后发射功率: {result.adjusted_power_el_W:.4f} W ({result.adjusted_power_el_dBW:.2f} dBW)")
        print(f"  调整后功放功率: {result.adjusted_hpa_power_W:.4f} W ({result.adjusted_hpa_power_dBW:.2f} dBW)")
        print(f"  迭代次数: {result.margin_iterations}")
        # 使用容差判断（0.01 dB）
        if result.final_margin < result.target_margin - 0.01:
            print(f"  ⚠️  未达到目标余量 (误差: {result.target_margin - result.final_margin:.2f} dB)")
        else:
            print(f"  ✅ 达到目标余量")

    # 生成报告
    print("\n📝 生成报告...")
    success = True

    # 将反向计算结果添加到配置中，供报告生成器使用
    if reverse_calc_result:
        config['_reverse_calc_result'] = reverse_calc_result

    # 从result对象中提取反向计算结果（主要计算模式）
    # 检查result是否有反向计算的字段
    if hasattr(result, 'calculated_upc_margin') and result.calculated_upc_margin > 0:
        # 创建反向计算结果字典供报告使用
        config['_reverse_calc_result'] = {
            'uplink_rain_attenuation_dB': result.uplink_rain_attenuation,
            'upc_reserved_dB': result.calculated_upc_margin,
            'availability': system.get('uplink_availability', 99.9),
            'unavailability': 100 - system.get('uplink_availability', 99.9),
            'compensable_rain_attenuation_dB': result.calculated_upc_margin,
            'required_upc_margin_db': result.calculated_upc_margin,
            'calculated_power_el_clear_dBW': result.calculated_power_el_clear_dBW,
            'calculated_power_el_clear_W': result.calculated_power_el_clear_W,
            'calculated_hpa_power_clear_dBW': result.calculated_hpa_power_clear_dBW,
            'calculated_hpa_power_clear_W': result.calculated_hpa_power_clear_W,
            'calculated_power_el_rain_dBW': result.calculated_power_el_rain_dBW,
            'calculated_power_el_rain_W': result.calculated_power_el_rain_W,
            'calculated_hpa_power_rain_dBW': result.calculated_hpa_power_rain_dBW,
            'calculated_hpa_power_rain_W': result.calculated_hpa_power_rain_W,
            'upc_sufficient': result.upc_sufficient,
        }

    if output_format in ['all', 'markdown']:
        md_file = f"{output_prefix}.md"
        MarkdownReportGenerator.generate(config, result, md_file)
        print(f"  ✅ Markdown报告: {md_file}")

    if output_format in ['all', 'excel']:
        excel_file = f"{output_prefix}.xlsx"
        ExcelReportGenerator.generate(config, result, excel_file)
        print(f"  ✅ Excel报告: {excel_file}")

    if output_format in ['all', 'json']:
        json_file = f"{output_prefix}.json"
        # 如果有反向计算结果，合并到JSON输出中
        export_data = {
            'metadata': {
                'version': '1.0.0',
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'standard': 'YD/T 2721-2014',
            },
            'input_parameters': JSONExporter._convert_params_to_dict(config),
            'calculation_results': JSONExporter._convert_result_to_dict(result),
        }
        if reverse_calc_result:
            export_data['reverse_calculation'] = reverse_calc_result

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        if print_json:
            print("\n" + "="*60)
            print("📄 JSON 输出")
            print("="*60)
            print(json.dumps(export_data, indent=2, ensure_ascii=False))
        print(f"  ✅ JSON数据: {json_file}")

    if output_format in ['all', 'pdf']:
        pdf_file = f"{output_prefix}.pdf"
        PDFReportGenerator.generate(config, result, pdf_file)
        print(f"  ✅ PDF报告: {pdf_file}")

    if success:
        print("\n✅ 完成！")
    else:
        print("\n❌ 报告生成失败")

    return success


def generate_template(output_file: str):
    """生成参数模板"""
    template = ParameterManager.create_template('默认模板')

    # 添加示例值
    template['satellite'].update({
        'longitude': 110.5,
        'eirp_ss': 48.48,
        'gt_s': 5.96,
        'gt_s_ref': 0,
        'sfd_ref': -84,
        'bo_i': 6,
        'bo_o': 3,
        'transponder_bw': 54000000,
    })

    template['carrier'].update({
        'info_rate': 2000000,
        'fec_rate': 0.75,
        'fec_type': 'DVB-S2',
        'modulation': 'QPSK',
        'modulation_index': 2,
        'ebno_threshold': 4.5,
    })

    template['tx_station'].update({
        'name': '北京',
        'latitude': 39.92,
        'longitude': 116.45,
        'antenna_diameter': 4.5,
        'efficiency': 0.65,
        'frequency': 14.25,
        'polarization': 'V',
        'feed_loss': 1.5,
        'antenna_noise_temp': 35,
        'receiver_noise_temp': 75,
        'loss_at': 0.5,
        'upc_max_comp': 5.0,
        'hpa_bo': 3.0,
    })

    template['rx_station'].update({
        'name': '乌鲁木齐',
        'latitude': 43.77,
        'longitude': 87.68,
        'antenna_diameter': 1.8,
        'efficiency': 0.65,
        'frequency': 12.50,
        'polarization': 'H',
        'feed_loss': 0.2,
        'antenna_noise_temp': 35,
        'receiver_noise_temp': 75,
        'loss_ar': 0.5,
    })

    ParameterManager.save_template(template, output_file)
    print(f"✅ 参数模板已生成: {output_file}")


def interactive_mode(output_prefix: str, output_format: str):
    """交互式模式"""
    print("🚀 YDT 2721 交互式计算模式")
    print("💡 提示：输入默认配置文件路径，或按Enter跳过\n")

    config_file = input("📁 配置文件路径（可选，按Enter使用示例配置）: ").strip()

    if config_file and os.path.exists(config_file):
        config = load_config(config_file)
    else:
        # 使用示例配置
        print("📋 使用示例配置...")
        config = {}
        # 这里可以添加交互式输入逻辑
        # 为简化，使用默认示例
        from examples.test_all import complete_link_budget
        # 实际使用时会从文件加载

    if config:
        execute_calculation(config, output_prefix, output_format)
    else:
        print("❌ 未提供有效配置")


def main():
    """主函数"""
    # 修复Windows控制台编码问题
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    if args.command == 'calculate':
        # 检查是否需要设置字体
        if getattr(args, 'setup_fonts', False) or args.format in ['all', 'pdf']:
            # 检查是否有可用字体
            info = FontManager.get_font_info()
            has_downloaded = any(f['exists'] and f['valid'] for f in info['downloaded_fonts'])
            if not has_downloaded and not (info['system_fonts']['normal'] or info['system_fonts']['bold']):
                print("⚠️  未找到可用的中文字体")
                print("📥 正在下载开源中文字体...")
                setup_chinese_fonts()

        if not args.config:
            print("❌ 请指定配置文件 (--config)")
            print("💡 使用 'ydt2721 template' 生成配置模板")
            return

        config = load_config(args.config)
        execute_calculation(
            config, args.output, args.format, getattr(args, 'print_json', False), args.no_validate,
            args.calc_mode, args.upc_reserved,
            args.hpa_power, args.station_height,
            getattr(args, 'target_margin', None)
        )

    elif args.command == 'interactive':
        interactive_mode(args.output, args.format)

    elif args.command == 'validate':
        config = load_config(args.config)
        validate_config(config)

    elif args.command == 'template':
        generate_template(args.output)

    elif args.command == 'font':
        if args.font_command == 'setup':
            setup_chinese_fonts(force=getattr(args, 'force', False))
        elif args.font_command == 'info':
            info = FontManager.get_font_info()
            print("\n" + "="*50)
            print("YDT 2721 中文字体状态")
            print("="*50)
            print(f"\n系统: {info['system']}")
            print(f"字体目录: {info['font_dir']}")
            print(f"\n系统字体:")
            print(f"  普通: {'✓' if info['system_fonts']['normal'] else '✗'}")
            print(f"  粗体: {'✓' if info['system_fonts']['bold'] else '✗'}")
            print(f"\n已下载字体:")
            for font in info['downloaded_fonts']:
                status = "✓" if font['valid'] else ("✗" if font['exists'] else "?")
                print(f"  {status} {font['key']}")
                if font['exists']:
                    print(f"     路径: {font['path']}")
            print()
        elif args.font_command == 'remove':
            if FontManager.remove_downloaded_fonts():
                print("✅ 已删除下载的字体文件")
            else:
                print("❌ 删除失败")
        else:
            font_parser.print_help()


if __name__ == '__main__':
    main()
