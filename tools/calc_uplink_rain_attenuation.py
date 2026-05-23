#!/usr/bin/env python3
"""
根据上行可用度要求计算对应的雨衰量

功能：
  - 输入：上行可用度要求 (%)
  - 输出：对应的雨衰量 (dB)，以及详细的分解衰减分量

用法：
    python calc_uplink_rain_attenuation.py --config params.json --availability 99.95

    python calc_uplink_rain_attenuation.py --lat 39.92 --lon 116.45 --sat-lon 110.5 \\
        --frequency 14.25 --polarization V --antenna-diameter 4.5 --availability 99.95
"""

import argparse
import sys
import os
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721.core.itu_rain_wrapper import calculate_rain_attenuation_iturpy
from ydt2721.core.earth_station import calculate_antenna_pointing
from ydt2721.core.reverse_calc import calculate_required_hpa_for_availability


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='根据上行可用度要求计算对应的雨衰量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用配置文件
  %(prog)s --config params.json --availability 99.95

  # 直接指定参数
  %(prog)s --lat 39.92 --lon 116.45 --sat-lon 110.5 --frequency 14.25 \\
          --polarization V --antenna-diameter 4.5 --availability 99.95

  # 计算功放需求
  %(prog)s --config params.json --availability 99.95 --calc-mode power
        """
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='参数配置文件（JSON格式）'
    )
    parser.add_argument(
        '--availability', '-a',
        type=float,
        required=True,
        help='目标上行可用度 (%%)，例如: 99.95'
    )

    # 地理位置参数
    parser.add_argument(
        '--lat',
        type=float,
        help='发射站纬度 (度)'
    )
    parser.add_argument(
        '--lon',
        type=float,
        help='发射站经度 (度)'
    )
    parser.add_argument(
        '--sat-lon',
        type=float,
        help='卫星经度 (度)'
    )

    # 链路参数
    parser.add_argument(
        '--frequency',
        type=float,
        help='上行频率 (GHz)'
    )
    parser.add_argument(
        '--polarization', '-p',
        type=str,
        choices=['H', 'V', 'h', 'v'],
        help='极化方式 (H 或 V)'
    )
    parser.add_argument(
        '--antenna-diameter',
        type=float,
        help='天线直径 (米)'
    )
    parser.add_argument(
        '--station-height',
        type=float,
        default=0.0,
        help='地球站海拔高度 (km)，默认: 0'
    )
    parser.add_argument(
        '--elevation',
        type=float,
        help='仰角 (度)，不指定则自动计算'
    )

    # UPC参数
    parser.add_argument(
        '--upc-max',
        type=float,
        default=5.0,
        help='UPC最大补偿能力 (dB)，默认: 5.0'
    )

    # 计算模式
    parser.add_argument(
        '--calc-mode',
        type=str,
        choices=['rain', 'power'],
        default='rain',
        help='计算模式: rain=仅计算雨衰量, power=同时计算功放需求'
    )

    # 输出参数
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='输出JSON文件路径（可选）'
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='在控制台输出JSON结果'
    )

    return parser


def load_config(config_file: str) -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_params_from_config(config: dict) -> dict:
    """从配置中提取所需参数"""
    tx = config.get('tx_station', {})
    sat = config.get('satellite', {})

    return {
        'lat': tx.get('latitude'),
        'lon': tx.get('longitude'),
        'sat_lon': sat.get('longitude'),
        'frequency': tx.get('frequency'),
        'polarization': tx.get('polarization'),
        'antenna_diameter': tx.get('antenna_diameter'),
        'upc_max': tx.get('upc_max_comp', 5.0),
    }


def calculate_rain_attenuation_from_availability(
    lat: float,
    lon: float,
    satellite_lon: float,
    frequency: float,
    polarization: str,
    antenna_diameter: float,
    availability: float,
    station_height: float = 0.0,
    elevation: float = None
) -> dict:
    """
    根据上行可用度计算雨衰量

    Args:
        lat: 纬度 (度)
        lon: 经度 (度)
        satellite_lon: 卫星经度 (度)
        frequency: 频率 (GHz)
        polarization: 极化方式
        antenna_diameter: 天线直径 (m)
        availability: 目标上行可用度 (%)
        station_height: 站高度 (km)
        elevation: 仰角 (度)，可选

    Returns:
        包含各衰减分量的字典
    """
    # 计算仰角（如果未提供）
    if elevation is None:
        elevation, _ = calculate_antenna_pointing(lat, lon, satellite_lon)

    # 使用ITU-Rpy计算衰减
    result = calculate_rain_attenuation_iturpy(
        lat=lat,
        lon=lon,
        satellite_lon=satellite_lon,
        frequency=frequency,
        polarization=polarization,
        antenna_diameter=antenna_diameter,
        availability=availability,
        station_height=station_height,
        elevation=elevation
    )

    return result


def print_result(availability: float, result: dict, upc_max: float = 5.0, calc_mode: str = 'rain'):
    """打印计算结果"""
    print("\n" + "=" * 60)
    print("📊 根据上行可用度计算雨衰量结果")
    print("=" * 60)

    print(f"\n  【输入参数】")
    print(f"  目标上行可用度: {availability:.4f} %")
    print(f"  不可用度: {100 - availability:.4f} %")

    print(f"\n  【降雨衰减分量】")
    print(f"  降雨衰减: {result['rain_attenuation_dB']:.2f} dB")
    print(f"  气体衰减: {result['gas_attenuation_dB']:.2f} dB")
    print(f"  云衰减:   {result['cloud_attenuation_dB']:.2f} dB")
    print(f"  闪烁衰减: {result['scintillation_attenuation_dB']:.4f} dB")
    print(f"  总衰减:   {result['total_attenuation_dB']:.2f} dB")

    print(f"\n  【降雨参数】")
    print(f"  降雨率 (0.01%%): {result['rain_rate_mm_h']:.2f} mm/h")
    print(f"  雨高: {result['rain_height_km']:.2f} km")
    print(f"  降雨概率: {result['rain_attenuation_probability_pct']:.2f} %%")

    # UPC分析
    rain_att = result['rain_attenuation_dB']
    upc_used = min(rain_att, upc_max)
    residual_att = rain_att - upc_used
    upc_sufficient = rain_att <= upc_max

    print(f"\n  【UPC补偿分析】")
    print(f"  UPC最大补偿能力: {upc_max:.2f} dB")
    print(f"  所需UPC补偿量: {rain_att:.2f} dB")
    print(f"  实际UPC补偿量: {upc_used:.2f} dB")
    print(f"  剩余未补偿衰减: {residual_att:.2f} dB")
    print(f"  UPC是否足够: {'✅ 是' if upc_sufficient else '❌ 否'}")

    if calc_mode == 'power' and upc_sufficient:
        print(f"\n  【功放功率需求】")
        # 晴天功率（估算）
        print(f"  注: 需配合完整链路参数计算实际功放需求")


def main():
    """主函数"""
    # 修复Windows控制台编码问题
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = create_parser()
    args = parser.parse_args()

    # 参数收集
    if args.config:
        config = load_config(args.config)
        params = extract_params_from_config(config)
    else:
        params = {}

    # 命令行参数覆盖配置
    if args.lat is not None:
        params['lat'] = args.lat
    if args.lon is not None:
        params['lon'] = args.lon
    if args.sat_lon is not None:
        params['sat_lon'] = args.sat_lon
    if args.frequency is not None:
        params['frequency'] = args.frequency
    if args.polarization is not None:
        params['polarization'] = args.polarization.upper() if isinstance(args.polarization, str) else args.polarization
    if args.antenna_diameter is not None:
        params['antenna_diameter'] = args.antenna_diameter
    if args.upc_max is not None:
        params['upc_max'] = args.upc_max

    # 检查必需参数
    required = ['lat', 'lon', 'sat_lon', 'frequency', 'polarization', 'antenna_diameter']
    missing = [k for k in required if k not in params or params[k] is None]
    if missing:
        print(f"❌ 缺少必需参数: {', '.join(missing)}")
        print("💡 使用 --config 指定配置文件，或直接指定参数")
        return 1

    # 计算雨衰量
    result = calculate_rain_attenuation_from_availability(
        lat=params['lat'],
        lon=params['lon'],
        satellite_lon=params['sat_lon'],
        frequency=params['frequency'],
        polarization=params['polarization'],
        antenna_diameter=params['antenna_diameter'],
        availability=args.availability,
        station_height=args.station_height,
        elevation=args.elevation
    )

    # 打印结果
    print_result(args.availability, result, params.get('upc_max', 5.0), args.calc_mode)

    # 如果需要功放分析
    if args.calc_mode == 'power':
        try:
            power_result = calculate_required_hpa_for_availability(
                target_availability=args.availability,
                sfd=0,  # 需要从配置获取
                bo_il=0,
                gm2=0,
                loss_u=0,
                loss_at=0,
                lat=params['lat'],
                lon=params['lon'],
                satellite_lon=params['sat_lon'],
                frequency=params['frequency'],
                polarization=params['polarization'],
                antenna_diameter=params['antenna_diameter'],
                elevation=args.elevation,
                station_height=args.station_height,
                upc_max=params.get('upc_max', 5.0),
                rain_model='iturpy'
            )
        except Exception as e:
            print(f"\n⚠️  功放分析需要完整链路参数，请提供配置文件")

    # 输出JSON
    output_data = {
        'input': {
            'availability': args.availability,
            'lat': params['lat'],
            'lon': params['lon'],
            'satellite_lon': params['sat_lon'],
            'frequency_ghz': params['frequency'],
            'polarization': params['polarization'],
            'antenna_diameter_m': params['antenna_diameter'],
            'station_height_km': args.station_height,
        },
        'result': {
            'rain_attenuation_dB': result['rain_attenuation_dB'],
            'gas_attenuation_dB': result['gas_attenuation_dB'],
            'cloud_attenuation_dB': result['cloud_attenuation_dB'],
            'scintillation_attenuation_dB': result['scintillation_attenuation_dB'],
            'total_attenuation_dB': result['total_attenuation_dB'],
            'rain_rate_mm_h': result['rain_rate_mm_h'],
            'rain_height_km': result['rain_height_km'],
            'rain_attenuation_probability_pct': result['rain_attenuation_probability_pct'],
        },
        'upc_analysis': {
            'upc_max_dB': params.get('upc_max', 5.0),
            'required_upc_dB': result['rain_attenuation_dB'],
            'upc_sufficient': result['rain_attenuation_dB'] <= params.get('upc_max', 5.0),
        }
    }

    if args.print_json:
        print("\n" + "=" * 60)
        print("📄 JSON 输出")
        print("=" * 60)
        print(json.dumps(output_data, indent=2, ensure_ascii=False))

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ JSON结果已保存: {args.output}")

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)