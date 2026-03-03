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
)
from ydt2721.core.param_manager import ParameterValidator, ParameterManager
from ydt2721.models.dataclass import (
    SatelliteParams,
    CarrierParams,
    EarthStationParams,
)


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
        availability = config.get('system', {}).get('availability', 99.9)

        errors = validator.validate_all_params(satellite, carrier, tx_station, rx_station, availability)

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


def execute_calculation(config: dict, output_prefix: str, output_format: str,
                       skip_validation: bool = False) -> bool:
    """执行链路计算"""
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
    print("\n🔧 正在执行链路计算...")
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
        availability=system.get('availability', 99.9),

        # 干扰参数（可选）
        ci0_im=interference.get('ci0_im'),
        ci0_u_as=interference.get('ci0_u_as'),
        ci0_d_as=interference.get('ci0_d_as'),
        ci0_u_xp=interference.get('ci0_u_xp'),
        ci0_d_xp=interference.get('ci0_d_xp'),
        adj_sat_lon=sat.get('adj_sat_longitude'),
    )

    # 显示关键结果
    print("\n📊 计算结果：")
    print(f"  符号速率: {result.symbol_rate/1e6:.2f} Msym/s")
    print(f"  带宽占用比: {result.bandwidth_ratio:.2f}%")
    print(f"  仰角: {result.elevation:.2f}°")
    print(f"  晴天系统余量: {result.clear_sky_margin:.2f} dB")
    print(f"  上行降雨余量: {result.uplink_rain_margin:.2f} dB")
    print(f"  下行降雨余量: {result.downlink_rain_margin:.2f} dB")

    # 生成报告
    print("\n📝 生成报告...")
    success = True

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
        JSONExporter.export(config, result, json_file)
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
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    if args.command == 'calculate':
        if not args.config:
            print("❌ 请指定配置文件 (--config)")
            print("💡 使用 'ydt2721 template' 生成配置模板")
            return

        config = load_config(args.config)
        execute_calculation(config, args.output, args.format, args.no_validate)

    elif args.command == 'interactive':
        interactive_mode(args.output, args.format)

    elif args.command == 'validate':
        config = load_config(args.config)
        validate_config(config)

    elif args.command == 'template':
        generate_template(args.output)


if __name__ == '__main__':
    main()
