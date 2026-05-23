#!/usr/bin/env python3
"""
绘制各站点可用度-雨衰量曲线图

功能：
  - 计算多个站点在不同可用度下的雨衰量
  - 生成可用度-雨衰量曲线图

用法：
    python plot_availability_attenuation.py --station-dir gwstation --availability-min 98 --availability-max 99.9 --step 0.1 --output chart.png
"""

import argparse
import sys
import os
import json
import numpy as np
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from matplotlib import rcParams

from ydt2721.core.itu_rain_wrapper import calculate_rain_attenuation_iturpy
from ydt2721.core.earth_station import calculate_antenna_pointing


def convert_to_native(obj):
    """将numpy类型转换为Python原生类型"""
    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.int_, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float64, np.float32)):
        return float(obj)
    return obj


# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
rcParams['axes.unicode_minus'] = False


def load_station_configs(station_dir: str) -> list:
    """加载目录下所有站点配置"""
    configs = []
    dir_path = Path(station_dir)

    if not dir_path.exists():
        print(f"❌ 目录不存在: {station_dir}")
        return configs

    for json_file in dir_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                config['_file_name'] = json_file.stem
                configs.append(config)
        except Exception as e:
            print(f"⚠️  跳过 {json_file}: {e}")

    return configs


def calculate_attenuation_curve(
    lat: float,
    lon: float,
    satellite_lon: float,
    frequency: float,
    polarization: str,
    antenna_diameter: float,
    availability_range: list,
    station_height: float = 0.0
) -> dict:
    """计算给定可用度范围的衰减曲线"""
    # 计算仰角
    elevation, _ = calculate_antenna_pointing(lat, lon, satellite_lon)

    results = {
        'availability': [],
        'rain_attenuation': [],
        'total_attenuation': [],
        'gas_attenuation': [],
        'cloud_attenuation': [],
        'scintillation_attenuation': [],
        'elevation': elevation
    }

    for avail in availability_range:
        try:
            result = calculate_rain_attenuation_iturpy(
                lat=lat,
                lon=lon,
                satellite_lon=satellite_lon,
                frequency=frequency,
                polarization=polarization,
                antenna_diameter=antenna_diameter,
                availability=avail,
                station_height=station_height,
                elevation=elevation
            )

            results['availability'].append(avail)
            results['rain_attenuation'].append(result['rain_attenuation_dB'])
            results['total_attenuation'].append(result['total_attenuation_dB'])
            results['gas_attenuation'].append(result['gas_attenuation_dB'])
            results['cloud_attenuation'].append(result['cloud_attenuation_dB'])
            results['scintillation_attenuation'].append(result['scintillation_attenuation_dB'])

        except Exception as e:
            print(f"    ⚠️  可用度 {avail}% 计算失败: {e}")

    return results


def plot_availability_attenuation(
    station_data: dict,
    output_file: str,
    availability_range: list,
    upc_max: float = None,
    satellite_lon: float = None,
    frequency: float = None,
    polarization: str = None,
    antenna_diameter: float = None
):
    """绘制可用度-雨衰量曲线图"""

    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 8))

    # 颜色映射
    colors = plt.cm.tab10(np.linspace(0, 1, len(station_data)))

    for idx, (station_name, data) in enumerate(station_data.items()):
        ax.plot(
            data['availability'],
            data['rain_attenuation'],
            label=station_name,
            color=colors[idx],
            linewidth=2,
            marker='o',
            markersize=3,
            markevery=5
        )

    # 绘制UPC最大补偿线
    if upc_max is not None:
        ax.axhline(
            y=upc_max,
            color='red',
            linestyle='--',
            linewidth=1.5,
            label=f'UPC最大补偿 ({upc_max} dB)'
        )

        # 找到超过UPC的区间
        for station_name, data in station_data.items():
            avail_array = np.array(data['availability'])
            rain_array = np.array(data['rain_attenuation'])
            over_upc = rain_array > upc_max

            if np.any(over_upc):
                # 找到第一个超过UPC的点
                first_over_idx = np.argmax(over_upc)
                ax.axvline(
                    x=avail_array[first_over_idx],
                    color=colors[idx],
                    linestyle=':',
                    linewidth=1,
                    alpha=0.5
                )

    # 设置坐标轴
    ax.set_xlabel('上行可用度 (%)', fontsize=12)
    ax.set_ylabel('雨衰量 (dB)', fontsize=12)

    # 构建标题
    title_parts = []
    if satellite_lon:
        title_parts.append(f'卫星: {satellite_lon}°E')
    if frequency:
        title_parts.append(f'频率: {frequency}GHz')
    if polarization:
        title_parts.append(f'{polarization}极化')
    if antenna_diameter:
        title_parts.append(f'{antenna_diameter}m天线')

    title = '各站点可用度-雨衰量曲线'
    if title_parts:
        title += f'\n({" | ".join(title_parts)})'
    ax.set_title(title, fontsize=14)

    # 设置范围
    ax.set_xlim(availability_range[0], availability_range[-1])
    ax.set_ylim(bottom=0)

    # 网格
    ax.grid(True, linestyle='--', alpha=0.7)

    # 图例
    ax.legend(
        loc='upper left',
        bbox_to_anchor=(1.02, 1),
        fontsize=9,
        title='站点'
    )

    # 调整布局
    plt.tight_layout()

    # 保存
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 图表已保存: {output_file}")

    # 同时保存为PDF（高清）
    pdf_file = output_file.replace('.png', '.pdf')
    plt.savefig(pdf_file, bbox_inches='tight')
    print(f"✅ PDF已保存: {pdf_file}")

    plt.close()


def generate_summary_table(station_data: dict, availability_points: list, upc_max: float) -> dict:
    """生成汇总表数据"""
    summary = {}

    key_availability = [99.0, 99.5, 99.7, 99.9]

    for station_name, data in station_data.items():
        summary[station_name] = {
            'upc_max_dB': upc_max,
            'attenuation_at_key_points': {}
        }

        avail_array = np.array(data['availability'])
        rain_array = np.array(data['rain_attenuation'])

        for target_avail in key_availability:
            # 找到最接近的可用度
            idx = np.argmin(np.abs(avail_array - target_avail))
            actual_avail = float(avail_array[idx])
            rain_att = float(rain_array[idx])

            exceeds_upc = bool(rain_att > upc_max)

            summary[station_name]['attenuation_at_key_points'][f'{target_avail}%'] = {
                'rain_attenuation_dB': round(rain_att, 2),
                'exceeds_upc': exceeds_upc
            }

        # 找到超过UPC的临界可用度
        over_upc = rain_array > upc_max
        if np.any(over_upc):
            first_over_idx = np.argmax(over_upc)
            critical_avail = float(avail_array[first_over_idx])
            summary[station_name]['critical_availability_above_upc'] = round(critical_avail, 3)
        else:
            summary[station_name]['critical_availability_above_upc'] = None

    return summary


def print_summary_table(summary: dict):
    """打印汇总表"""
    print("\n" + "=" * 100)
    print("📊 各站点雨衰量汇总表 (卫星: 87.5°E, 频率: 52GHz, RH极化, 13m天线)")
    print("=" * 100)

    print(f"\n{'站点':<20} | {'99.0%':<12} | {'99.5%':<12} | {'99.7%':<12} | {'99.9%':<12} | {'超UPC临界'}")
    print("-" * 100)

    for station_name, data in summary.items():
        row = f"{station_name:<18} |"

        for avail in ['99.0%', '99.5%', '99.7%', '99.9%']:
            att_data = data['attenuation_at_key_points'][avail]
            att = att_data['rain_attenuation_dB']
            exceeds = "⚠️" if att_data['exceeds_upc'] else ""
            row += f" {att:>6.2f} dB {exceeds:<3} |"

        critical = data.get('critical_availability_above_upc')
        if critical:
            row += f" {critical:.2f}%"
        else:
            row += " -"

        print(row)

    print("-" * 100)
    print("⚠️  表示雨衰量超过UPC最大补偿能力")


def export_to_excel(station_data: dict, summary: dict, availability_range: list,
                     upc_max: float, output_file: str):
    """导出数据到Excel文件"""

    if not PANDAS_AVAILABLE:
        print("⚠️  pandas未安装，跳过Excel导出")
        return

    # 汇总表数据
    summary_rows = []
    for station_name, data in summary.items():
        row = {'站点': station_name, 'UPC最大补偿(dB)': upc_max}
        for avail, att_data in data['attenuation_at_key_points'].items():
            row[f'{avail}雨衰量(dB)'] = att_data['rain_attenuation_dB']
            row[f'{avail}超UPC'] = '是' if att_data['exceeds_upc'] else '否'

        critical = data.get('critical_availability_above_upc')
        row['超UPC临界可用度(%)'] = critical if critical else '-'
        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)

    # 完整曲线数据
    all_curves = []
    for station_name, data in station_data.items():
        for i, avail in enumerate(data['availability']):
            all_curves.append({
                '站点': station_name,
                '可用度(%)': avail,
                '降雨衰减(dB)': data['rain_attenuation'][i],
                '总衰减(dB)': data['total_attenuation'][i],
                '气体衰减(dB)': data['gas_attenuation'][i],
                '云衰减(dB)': data['cloud_attenuation'][i],
                '闪烁衰减(dB)': data['scintillation_attenuation'][i],
                '仰角(°)': data['elevation'],
                '超UPC': '是' if data['rain_attenuation'][i] > upc_max else '否'
            })

    df_curves = pd.DataFrame(all_curves)

    # 写入Excel（多个sheet）
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='汇总表', index=False)
        df_curves.to_excel(writer, sheet_name='完整曲线', index=False)

    print(f"✅ Excel已保存: {output_file}")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='绘制各站点可用度-雨衰量曲线图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --station-dir gwstation --availability-min 98 --availability-max 99.9 --step 0.1 --output chart.png

  %(prog)s --station-dir gwstation --output comparison.png --upc-max 3
        """
    )

    parser.add_argument(
        '--station-dir', '-d',
        type=str,
        required=True,
        help='站点配置文件目录'
    )
    parser.add_argument(
        '--availability-min',
        type=float,
        default=98.0,
        help='最小可用度 (%%)，默认: 98.0'
    )
    parser.add_argument(
        '--availability-max',
        type=float,
        default=99.9,
        help='最大可用度 (%%)，默认: 99.9'
    )
    parser.add_argument(
        '--step',
        type=float,
        default=0.1,
        help='可用度步进 (%%)，默认: 0.1'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='availability_attenuation.png',
        help='输出图表文件'
    )
    parser.add_argument(
        '--upc-max',
        type=float,
        default=None,
        help='UPC最大补偿能力 (dB)，默认从配置文件读取'
    )
    parser.add_argument(
        '--station-height',
        type=float,
        default=0.0,
        help='地球站海拔高度 (km)，默认: 0'
    )
    parser.add_argument(
        '--frequency',
        type=float,
        default=None,
        help='上行频率 (GHz)，覆盖配置文件中的值'
    )
    parser.add_argument(
        '--polarization',
        type=str,
        choices=['H', 'V', 'RH', 'RV', 'h', 'v', 'rh', 'rv'],
        default=None,
        help='极化方式，覆盖配置文件中的值'
    )
    parser.add_argument(
        '--antenna-diameter',
        type=float,
        default=None,
        help='天线直径 (m)，覆盖配置文件中的值'
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='输出JSON格式结果'
    )
    parser.add_argument(
        '--json-output',
        type=str,
        default=None,
        help='JSON输出文件路径'
    )
    parser.add_argument(
        '--excel-output', '-e',
        type=str,
        default=None,
        help='Excel输出文件路径'
    )

    return parser


def main():
    """主函数"""
    # 修复Windows控制台编码问题
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = create_parser()
    args = parser.parse_args()

    # 生成可用度序列
    availability_range = []
    current = args.availability_min
    while current <= args.availability_max + 1e-9:
        availability_range.append(round(current, 2))
        current += args.step

    print(f"📊 可用度范围: {availability_range[0]:.1f}% ~ {availability_range[-1]:.1f}%")
    print(f"📊 共 {len(availability_range)} 个采样点")

    # 加载站点配置
    configs = load_station_configs(args.station_dir)
    if not configs:
        print(f"❌ 未找到配置文件")
        return 1

    print(f"📁 已加载 {len(configs)} 个站点配置")

    # 计算每个站点的衰减曲线
    station_data = {}
    upc_max_global = args.upc_max

    for config in configs:
        tx = config.get('tx_station', {})
        sat = config.get('satellite', {})
        station_name = tx.get('name', config.get('_file_name', 'Unknown'))

        print(f"\n🔄 计算站点: {station_name}")

        # 获取UPC最大值
        upc_max = tx.get('upc_max_comp', args.upc_max if args.upc_max else 5.0)
        if upc_max_global is None:
            upc_max_global = upc_max

        lat = tx.get('latitude')
        lon = tx.get('longitude')
        sat_lon = sat.get('longitude')
        # 命令行参数覆盖配置文件
        frequency = args.frequency if args.frequency is not None else tx.get('frequency')
        polarization = args.polarization.upper() if args.polarization else tx.get('polarization')
        antenna_diameter = args.antenna_diameter if args.antenna_diameter is not None else tx.get('antenna_diameter')

        if not all([lat, lon, sat_lon, frequency, polarization, antenna_diameter]):
            print(f"  ⚠️  跳过: 缺少必要参数")
            continue

        results = calculate_attenuation_curve(
            lat=lat,
            lon=lon,
            satellite_lon=sat_lon,
            frequency=frequency,
            polarization=polarization,
            antenna_diameter=antenna_diameter,
            availability_range=availability_range,
            station_height=args.station_height
        )

        station_data[station_name] = results
        print(f"  ✅ 完成: 仰角 {results['elevation']:.2f}°")

    if not station_data:
        print("❌ 没有有效数据")
        return 1

    # 从实际使用的参数获取（命令行覆盖值或配置文件值）
    output_frequency = args.frequency if args.frequency is not None else (configs[0].get('tx_station', {}).get('frequency') if configs else None)
    output_polarization = args.polarization.upper() if args.polarization else (configs[0].get('tx_station', {}).get('polarization') if configs else None)
    output_antenna_diameter = args.antenna_diameter if args.antenna_diameter is not None else (configs[0].get('tx_station', {}).get('antenna_diameter') if configs else None)

    # 绘制图表
    print(f"\n📈 生成图表...")
    plot_availability_attenuation(
        station_data=station_data,
        output_file=args.output,
        availability_range=availability_range,
        upc_max=upc_max_global,
        satellite_lon=87.5,
        frequency=output_frequency,
        polarization=output_polarization,
        antenna_diameter=output_antenna_diameter
    )

    # 生成汇总表
    summary = generate_summary_table(station_data, availability_range, upc_max_global)
    print_summary_table(summary)

    # JSON输出
    if args.print_json or args.json_output:
        import datetime
        output_json = {
            'metadata': {
                'version': '1.0.0',
                'timestamp': datetime.datetime.now().isoformat(),
                'satellite_lon': 87.5,
                'frequency_ghz': output_frequency,
                'polarization': output_polarization,
                'antenna_diameter_m': output_antenna_diameter,
                'availability_range': {
                    'min': availability_range[0],
                    'max': availability_range[-1],
                    'step': args.step,
                    'points': len(availability_range)
                },
                'parameter_source': {
                    'frequency': 'command_line' if args.frequency is not None else 'config_file',
                    'polarization': 'command_line' if args.polarization else 'config_file',
                    'antenna_diameter': 'command_line' if args.antenna_diameter else 'config_file'
                }
            },
            'stations': {}
        }

        for station_name, data in station_data.items():
            output_json['stations'][station_name] = {
                'latitude': station_data[station_name].get('latitude', 0),
                'longitude': station_data[station_name].get('longitude', 0),
                'elevation_deg': round(data['elevation'], 2),
                'upc_max_dB': upc_max_global,
                'availability_curve': {
                    'availability': data['availability'],
                    'rain_attenuation_dB': data['rain_attenuation'],
                    'total_attenuation_dB': data['total_attenuation'],
                    'gas_attenuation_dB': data['gas_attenuation'],
                    'cloud_attenuation_dB': data['cloud_attenuation'],
                    'scintillation_attenuation_dB': data['scintillation_attenuation'],
                },
                'summary': summary[station_name]
            }

        if args.print_json:
            print("\n" + "=" * 60)
            print("📄 JSON 输出")
            print("=" * 60)
            print(json.dumps(output_json, indent=2, ensure_ascii=False))

        if args.json_output:
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(output_json, f, indent=2, ensure_ascii=False)
            print(f"\n✅ JSON数据已保存: {args.json_output}")

    # Excel输出
    if args.excel_output:
        export_to_excel(
            station_data=station_data,
            summary=summary,
            availability_range=availability_range,
            upc_max=upc_max_global,
            output_file=args.excel_output
        )

    print("\n✅ 完成！")
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)