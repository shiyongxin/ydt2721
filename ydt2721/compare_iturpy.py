#!/usr/bin/env python3
"""
对比简化模型和 ITU-Rpy 的降雨衰减计算结果

用法:
    python3 compare_iturpy.py
"""

import json
from typing import Dict, List
import sys


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(label: str, value: float, unit: str = "dB"):
    """格式化打印结果"""
    print(f"{label:30} : {value:10.2f} {unit}")


def compare_models():
    """对比简化模型和 ITU-Rpy"""
    print_section("ITU-Rpy 对比测试")

    # 检查 ITU-Rpy 是否可用
    try:
        import itur
        import astropy.units as u
        print("✅ ITU-Rpy 已安装\n")
    except ImportError:
        print("❌ ITU-Rpy 未安装")
        print("请运行: pip install itur\n")
        sys.exit(1)

    # 导入 ydt2721 模块
    try:
        from ydt2721 import complete_link_budget
        from ydt2721.core.space_loss import calculate_rain_attenuation
        print("✅ ydt2721 模块加载成功\n")
    except ImportError:
        print("❌ ydt2721 模块未找到")
        print("请先安装: pip install -e .\n")
        sys.exit(1)

    # 测试参数（标准案例）
    print("测试参数:")
    print("-" * 70)
    print("卫星经度         : 110.5° E")
    print("上行频率         : 14.25 GHz")
    print("下行频率         : 12.50 GHz")
    print("发射站（北京）   : 39.92° N, 116.45° E")
    print("接收站（乌鲁木齐）: 43.77° N, 87.68° E")
    print("系统可用度       : 99.66%\n")

    # 测试用例
    test_cases = [
        {"availability": 99.9, "label": "99.9%"},
        {"availability": 99.5, "label": "99.5%"},
        {"availability": 99.0, "label": "99.0%"},
        {"availability": 95.0, "label": "95.0%"},
    ]

    results = []

    for case in test_cases:
        availability = case["availability"]
        label = case["label"]

        print_section(f"可用度: {label}")

        # 计算仰角
        from ydt2721.core.earth_station import calculate_antenna_pointing

        tx_elevation, _ = calculate_antenna_pointing(39.92, 116.45, 110.5)
        rx_elevation, _ = calculate_antenna_pointing(43.77, 87.68, 110.5)

        print(f"仰角:")
        print(f"  发射站（北京）: {tx_elevation:.2f}°")
        print(f"  接收站（乌鲁木齐）: {rx_elevation:.2f}°\n")

        # 1. 简化模型 - ydt2721
        print("1. 简化模型 (ydt2721 现有实现)")
        print("-" * 70)

        tx_rain_simplified = calculate_rain_attenuation(
            availability=availability,
            frequency=14.25,
            elevation=tx_elevation,
            latitude=39.92,
            pol='V'
        )

        rx_rain_simplified = calculate_rain_attenuation(
            availability=availability,
            frequency=12.50,
            elevation=rx_elevation,
            latitude=43.77,
            pol='H'
        )

        print_result("上行降雨衰减", tx_rain_simplified)
        print_result("下行降雨衰减", rx_rain_simplified)

        # 2. ITU-Rpy 模型
        print("\n2. ITU-Rpy 模型")
        print("-" * 70)

        p = (100 - availability) / 100

        # 上行
        tx_rain_iturpy = itur.rain_attenuation(
            lat=39.92,
            lon=116.45,
            f=14.25 * u.GHz,
            el=tx_elevation,
            hs=0.1,  # 北京海拔约 100m
            p=p
        )

        # 下行
        rx_rain_iturpy = itur.rain_attenuation(
            lat=43.77,
            lon=87.68,
            f=12.50 * u.GHz,
            el=rx_elevation,
            hs=0.8,  # 乌鲁木齐海拔约 800m
            p=p
        )

        print_result("上行降雨衰减", float(tx_rain_iturpy.value))
        print_result("下行降雨衰减", float(rx_rain_iturpy.value))

        # 3. 总大气衰减（ITU-Rpy）
        print("\n3. ITU-Rpy 总大气衰减（含所有分量）")
        print("-" * 70)

        # 上行
        tx_ag, tx_ac, tx_ar, tx_as, tx_at = itur.atmospheric_attenuation_slant_path(
            lat=39.92,
            lon=116.45,
            f=14.25 * u.GHz,
            el=tx_elevation,
            p=p,
            D=4.5 * u.m,
            return_contributions=True
        )

        print(f"上行总衰减:")
        print_result("  气体衰减", float(tx_ag.value))
        print_result("  云衰减", float(tx_ac.value))
        print_result("  降雨衰减", float(tx_ar.value))
        print_result("  闪烁衰减", float(tx_as.value))
        print_result("  总衰减", float(tx_at.value))

        # 下行
        rx_ag, rx_ac, rx_ar, rx_as, rx_at = itur.atmospheric_attenuation_slant_path(
            lat=43.77,
            lon=87.68,
            f=12.50 * u.GHz,
            el=rx_elevation,
            p=p,
            D=1.8 * u.m,
            return_contributions=True
        )

        print(f"\n下行总衰减:")
        print_result("  气体衰减", float(rx_ag.value))
        print_result("  云衰减", float(rx_ac.value))
        print_result("  降雨衰减", float(rx_ar.value))
        print_result("  闪烁衰减", float(rx_as.value))
        print_result("  总衰减", float(rx_at.value))

        # 4. 对比分析
        print("\n4. 对比分析")
        print("-" * 70)

        tx_rain_simplified_val = float(tx_rain_simplified)
        tx_rain_iturpy_val = float(tx_rain_iturpy.value)

        rx_rain_simplified_val = float(rx_rain_simplified)
        rx_rain_iturpy_val = float(rx_rain_iturpy.value)

        # 上行对比
        tx_ratio = tx_rain_iturpy_val / tx_rain_simplified_val if tx_rain_simplified_val > 0 else 0
        tx_diff = abs(tx_rain_iturpy_val - tx_rain_simplified_val)

        print(f"上行降雨衰减对比:")
        print(f"  简化模型        : {tx_rain_simplified_val:.2f} dB")
        print(f"  ITU-Rpy         : {tx_rain_iturpy_val:.2f} dB")
        print(f"  差异            : {tx_diff:.2f} dB ({tx_ratio:.2f}x)")

        # 下行对比
        rx_ratio = rx_rain_iturpy_val / rx_rain_simplified_val if rx_rain_simplified_val > 0 else 0
        rx_diff = abs(rx_rain_iturpy_val - rx_rain_simplified_val)

        print(f"\n下行降雨衰减对比:")
        print(f"  简化模型        : {rx_rain_simplified_val:.2f} dB")
        print(f"  ITU-Rpy         : {rx_rain_iturpy_val:.2f} dB")
        print(f"  差异            : {rx_diff:.2f} dB ({rx_ratio:.2f}x)")

        # 保存结果
        results.append({
            "availability": label,
            "tx_rain_simplified": round(tx_rain_simplified_val, 2),
            "tx_rain_iturpy": round(tx_rain_iturpy_val, 2),
            "tx_rain_ratio": round(tx_ratio, 2),
            "tx_rain_diff": round(tx_diff, 2),
            "rx_rain_simplified": round(rx_rain_simplified_val, 2),
            "rx_rain_iturpy": round(rx_rain_iturpy_val, 2),
            "rx_rain_ratio": round(rx_ratio, 2),
            "rx_rain_diff": round(rx_diff, 2),
            "tx_total_attenuation": round(float(tx_at.value), 2),
            "rx_total_attenuation": round(float(rx_at.value), 2),
        })

    # 生成总结报告
    print_section("总结报告")

    print("\n降雨衰减对比表:")
    print("-" * 70)
    print(f"{'可用度':<10} {'上行简化':<10} {'上行ITU':<10} {'上行比率':<10} {'下行简化':<10} {'下行ITU':<10} {'下行比率':<10}")
    print("-" * 70)

    for r in results:
        print(f"{r['availability']:<10} "
              f"{r['tx_rain_simplified']:<10} "
              f"{r['tx_rain_iturpy']:<10} "
              f"{r['tx_rain_ratio']:<10} "
              f"{r['rx_rain_simplified']:<10} "
              f"{r['rx_rain_iturpy']:<10} "
              f"{r['rx_rain_ratio']:<10}")

    print("\n总大气衰减（ITU-Rpy）:")
    print("-" * 70)
    print(f"{'可用度':<10} {'上行总衰减':<15} {'下行总衰减':<15}")
    print("-" * 70)

    for r in results:
        print(f"{r['availability']:<10} "
              f"{r['tx_total_attenuation']:<15} "
              f"{r['rx_total_attenuation']:<15}")

    # 保存 JSON 报告
    print("\n保存结果到 compare_iturpy_results.json...")
    with open("compare_iturpy_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ 完成")

    # 建议
    print_section("建议")

    print("""
1. 简化模型适用于:
   - 快速原型设计
   - 初步参数评估
   - 频率迭代测试

2. ITU-Rpy 适用于:
   - 精确工程计算
   - 正式报告生成
   - 商用链路设计

3. 差异说明:
   - ITU-Rpy 考虑了完整的 ITU-R P.837, P.838, P.618 标准
   - 简化模型使用近似公式，误差可达 ±50%
   - ITU-Rpy 的精度约为 ±10%

4. 建议:
   - 开发阶段使用简化模型（速度快）
   - 最终报告使用 ITU-Rpy（精度高）
   - 两种模型都计算，对比验证
    """)


if __name__ == "__main__":
    compare_models()
