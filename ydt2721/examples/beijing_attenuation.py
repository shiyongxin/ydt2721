"""
对比 Simplified 和 ITU-Rpy 模型的雨衰减计算
输出中间变量用于对比分析
"""

import sys
import os
# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721.core.space_loss import (
    calculate_rain_rate,
    calculate_specific_attenuation,
    calculate_effective_path_length,
    calculate_rain_attenuation as calculate_rain_attenuation_simplified,
    calculate_rain_noise_temp,
    calculate_gt_degradation,
)
from ydt2721.core.earth_station import calculate_antenna_pointing
from ydt2721.core.rain_selector import RainModel, RainAttenuationCalculator


def calculate_simplified_model(
    availability: float,
    frequency: float,
    latitude: float,
    longitude: float,
    satellite_lon: float,
    polarization: str
):
    """Simplified 模型计算"""
    print("\n" + "="*70)
    print("[Simplified] 模型计算过程")
    print("="*70)

    # 步骤1: 转换可用度
    unavailability = 100 - availability
    print(f"\n[步骤1] 可用度转换")
    print(f"  输入可用度: {availability}%")
    print(f"  不可用度 p: {unavailability}%")

    # 计算仰角
    elevation, azimuth = calculate_antenna_pointing(latitude, longitude, satellite_lon)

    # 步骤2: 计算降雨率
    rain_rate = calculate_rain_rate(unavailability, latitude)
    print(f"\n[步骤2] 降雨率计算")
    print(f"  纬度: {latitude} deg")
    print(f"  纬度分区: 温带 (a=15, b=0.28)")
    print(f"  公式: R = a * p^(-b)")
    print(f"  R = 15 * {unavailability}^(-0.28)")
    print(f"  降雨率: {rain_rate:.2f} mm/h")

    # 步骤3: 计算比衰减
    specific_att = calculate_specific_attenuation(frequency, rain_rate, polarization)
    print(f"\n[步骤3] 比衰减计算")
    print(f"  频率: {frequency} GHz")
    print(f"  k = 0.08 (>=10GHz)")
    print(f"  alpha = 1.1")
    if polarization.upper() == 'H':
        print(f"  H极化修正: k * 1.1")
    print(f"  公式: gamma = k * R^alpha")
    print(f"  gamma = {0.08 if polarization.upper() != 'H' else 0.088:.3f} * {rain_rate:.2f}^1.1")
    print(f"  比衰减: {specific_att:.3f} dB/km")

    # 步骤4: 计算有效路径长度
    eff_length = calculate_effective_path_length(elevation, rain_rate)
    print(f"\n[步骤4] 有效路径长度计算")
    print(f"  仰角: {elevation:.2f} deg")
    print(f"  基础长度: L_base = 5 / sin({elevation:.2f} deg) = {5 / (elevation * 3.14159 / 180):.2f} km")
    print(f"  减缩因子: r = 1 / (1 + L_base/20)")
    print(f"  有效长度: {eff_length:.3f} km")

    # 步骤5: 计算总降雨衰减
    rain_att = specific_att * eff_length
    print(f"\n[步骤5] 降雨衰减")
    print(f"  公式: A_rain = gamma * L_eff")
    print(f"  A_rain = {specific_att:.3f} * {eff_length:.3f}")
    print(f"  降雨衰减: {rain_att:.2f} dB")

    # 步骤6: 计算噪声温度
    rain_noise = calculate_rain_noise_temp(rain_att, 260)
    print(f"\n[步骤6] 降雨噪声温度")
    print(f"  公式: T_rain = 260 * (1 - 10^(-A/10))")
    print(f"  T_rain = 260 * (1 - 10^(-{rain_att:.2f}/10))")
    print(f"  噪声温度: {rain_noise:.2f} K")

    # 步骤7: 计算G/T下降
    feed_loss = 0.2
    system_noise_temp = 110
    gt_deg = calculate_gt_degradation(rain_noise, feed_loss, system_noise_temp)
    print(f"\n[步骤7] G/T下降")
    print(f"  馈线损耗: {feed_loss} dB")
    print(f"  系统噪声温度: {system_noise_temp} K")
    print(f"  G/T下降: {gt_deg:.2f} dB")

    return {
        'unavailability': unavailability,
        'rain_rate': rain_rate,
        'specific_attenuation': specific_att,
        'effective_length': eff_length,
        'rain_attenuation': rain_att,
        'rain_noise_temp': rain_noise,
        'gt_degradation': gt_deg,
        'elevation': elevation,
    }


def calculate_iturpy_model(
    availability: float,
    frequency: float,
    latitude: float,
    longitude: float,
    satellite_lon: float,
    polarization: str
):
    """ITU-Rpy 模型计算"""
    print("\n" + "="*70)
    print("[ITU-Rpy] 模型计算过程")
    print("="*70)

    # 计算仰角
    elevation, azimuth = calculate_antenna_pointing(latitude, longitude, satellite_lon)

    # 步骤1: 转换可用度
    p = 100 - availability
    print(f"\n[步骤1] 可用度转换")
    print(f"  输入可用度: {availability}%")
    print(f"  超时概率 p: {p}%")

    # 创建计算器
    from ydt2721.core.itu_rain_wrapper import ITURainCalculator
    calc = ITURainCalculator(
        lat=latitude,
        lon=longitude,
        satellite_lon=satellite_lon,
        frequency=frequency,
        polarization=polarization,
        antenna_diameter=1.8,
        elevation=elevation,
        station_height=0.05
    )

    # 步骤2: 获取大气参数
    print(f"\n[步骤2] 大气参数 (ITU-R 数字地图)")
    atmo_params = calc.get_atmospheric_parameters(availability)
    print(f"  站址海拔: {atmo_params['elevation_km']:.3f} km")
    print(f"  地面温度: {atmo_params['surface_temp_C']:.1f} C")
    print(f"  气压: {atmo_params['pressure_hPa']:.1f} hPa")
    print(f"  水汽密度: {atmo_params['water_vapor_density_g_m3']:.1f} g/m^3")
    print(f"  降雨率: {atmo_params['rain_rate_mm_h']:.2f} mm/h (ITU-R P.837)")
    print(f"  雨顶高度: {atmo_params['rain_height_km']:.2f} km (ITU-R P.839)")

    # 步骤3: 计算各衰减分量
    print(f"\n[步骤3] 衰减分量计算")

    # 降雨衰减
    rain_att = calc.calculate_rain_attenuation(availability)
    print(f"\n  降雨衰减 (ITU-R P.618 + P.837 + P.838 + P.839):")
    print(f"    A_rain = {rain_att:.2f} dB")

    # 气体衰减
    gas_att = calc.calculate_gas_attenuation(availability)
    print(f"\n  气体衰减 (ITU-R P.676):")
    print(f"    A_gas = {gas_att:.2f} dB")

    # 云衰减
    cloud_att = calc.calculate_cloud_attenuation(availability)
    print(f"\n  云衰减 (ITU-R P.840):")
    print(f"    A_cloud = {cloud_att:.2f} dB")

    # 闪烁衰减
    scint_att = calc.calculate_scintillation_attenuation(availability)
    print(f"\n  闪烁衰减 (ITU-R P.618):")
    print(f"    A_scint = {scint_att:.2f} dB")

    # 总衰减
    total_att = rain_att + gas_att + cloud_att + scint_att
    print(f"\n  总大气衰减:")
    print(f"    A_total = {rain_att:.2f} + {gas_att:.2f} + {cloud_att:.2f} + {scint_att:.2f}")
    print(f"    A_total = {total_att:.2f} dB")

    # 步骤4: 计算噪声温度
    rain_noise = calc.calculate_rain_noise_temp(rain_att, 260)
    print(f"\n[步骤4] 降雨噪声温度")
    print(f"  T_rain = {rain_noise:.2f} K")

    # 步骤5: 计算G/T下降
    feed_loss = 0.2
    system_noise_temp = 110
    gt_deg = calculate_gt_degradation(rain_noise, feed_loss, system_noise_temp)
    print(f"\n[步骤5] G/T下降")
    print(f"  G/T下降: {gt_deg:.2f} dB")

    return {
        'unavailability': p,
        'rain_rate': atmo_params['rain_rate_mm_h'],
        'rain_height': atmo_params['rain_height_km'],
        'rain_attenuation': rain_att,
        'gas_attenuation': gas_att,
        'cloud_attenuation': cloud_att,
        'scintillation_attenuation': scint_att,
        'total_attenuation': total_att,
        'rain_noise_temp': rain_noise,
        'gt_degradation': gt_deg,
        'elevation': elevation,
    }


def compare_models():
    """对比两个模型"""

    # 北京参数
    latitude = 39.92
    longitude = 116.45
    satellite_lon = 110.5  # 中星10号
    frequency = 14.25      # Ku波段
    polarization = 'V'
    availability = 99.95

    print("\n" + "="*70)
    print("北京雨衰减计算对比")
    print("="*70)
    print(f"\n输入参数:")
    print(f"  位置: 北京 ({latitude} deg N, {longitude} deg E)")
    print(f"  卫星经度: {satellite_lon} deg E")
    print(f"  频率: {frequency} GHz")
    print(f"  极化: {polarization}")
    print(f"  可用度: {availability}%")

    # Simplified 模型
    result_simple = calculate_simplified_model(
        availability, frequency, latitude, longitude, satellite_lon, polarization
    )

    # ITU-Rpy 模型
    result_itur = calculate_iturpy_model(
        availability, frequency, latitude, longitude, satellite_lon, polarization
    )

    # 对比表
    print("\n" + "="*70)
    print("中间变量对比表")
    print("="*70)

    print(f"\n{'参数':<30} {'Simplified':<15} {'ITU-Rpy':<15} {'差异':<10}")
    print("-"*70)

    print(f"{'不可用度 p (%)':<30} {result_simple['unavailability']:<15.2f} {result_itur['unavailability']:<15.2f} {'-':<10}")

    print(f"{'降雨率 R (mm/h)':<30} {result_simple['rain_rate']:<15.2f} {result_itur['rain_rate']:<15.2f} {result_simple['rain_rate'] - result_itur['rain_rate']:<10.2f}")

    print(f"{'比衰减 (dB/km)':<30} {result_simple['specific_attenuation']:<15.3f} {'N/A':<15} {'-':<10}")

    print(f"{'有效路径长度 (km)':<30} {result_simple['effective_length']:<15.3f} {'N/A':<15} {'-':<10}")

    print(f"{'雨顶高度 (km)':<30} {'N/A (固定5km)':<15} {result_itur['rain_height']:<15.2f} {'-':<10}")

    print(f"{'降雨衰减 (dB)':<30} {result_simple['rain_attenuation']:<15.2f} {result_itur['rain_attenuation']:<15.2f} {result_simple['rain_attenuation'] - result_itur['rain_attenuation']:<10.2f}")

    print(f"{'气体衰减 (dB)':<30} {'N/A':<15} {result_itur['gas_attenuation']:<15.2f} {'-':<10}")

    print(f"{'云衰减 (dB)':<30} {'N/A':<15} {result_itur['cloud_attenuation']:<15.2f} {'-':<10}")

    print(f"{'闪烁衰减 (dB)':<30} {'N/A':<15} {result_itur['scintillation_attenuation']:<15.2f} {'-':<10}")

    print(f"{'总衰减 (dB)':<30} {result_simple['rain_attenuation']:<15.2f} {result_itur['total_attenuation']:<15.2f} {result_simple['rain_attenuation'] - result_itur['total_attenuation']:<10.2f}")

    print(f"{'噪声温度 (K)':<30} {result_simple['rain_noise_temp']:<15.2f} {result_itur['rain_noise_temp']:<15.2f} {result_simple['rain_noise_temp'] - result_itur['rain_noise_temp']:<10.2f}")

    print(f"{'G/T下降 (dB)':<30} {result_simple['gt_degradation']:<15.2f} {result_itur['gt_degradation']:<15.2f} {result_simple['gt_degradation'] - result_itur['gt_degradation']:<10.2f}")

    print(f"{'仰角 (度)':<30} {result_simple['elevation']:<15.2f} {result_itur['elevation']:<15.2f} {'-':<10}")

    # 结论
    print("\n" + "="*70)
    print("结论")
    print("="*70)

    rain_diff = abs(result_simple['rain_attenuation'] - result_itur['rain_attenuation'])
    total_diff = abs(result_simple['rain_attenuation'] - result_itur['total_attenuation'])

    if rain_diff < 1:
        print(f"[OK] 降雨衰减差异较小 ({rain_diff:.2f} dB)")
    else:
        print(f"[WARN] 降雨衰减差异较大 ({rain_diff:.2f} dB)")

    print(f"\n  Simplified 仅计算降雨衰减: {result_simple['rain_attenuation']:.2f} dB")
    print(f"  ITU-Rpy 计算总大气衰减: {result_itur['total_attenuation']:.2f} dB")
    print(f"    - 降雨: {result_itur['rain_attenuation']:.2f} dB")
    print(f"    - 气体: {result_itur['gas_attenuation']:.2f} dB")
    print(f"    - 云: {result_itur['cloud_attenuation']:.2f} dB")
    print(f"    - 闪烁: {result_itur['scintillation_attenuation']:.2f} dB")

    print(f"\n  额外衰减贡献: {result_itur['total_attenuation'] - result_itur['rain_attenuation']:.2f} dB")


if __name__ == '__main__':
    compare_models()
