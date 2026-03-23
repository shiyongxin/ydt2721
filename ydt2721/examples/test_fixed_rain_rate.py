"""
测试 ITU-Rpy 在固定降雨率 34.70 mm/h 下的降雨衰减计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import itur
import astropy.units as u


def test_fixed_rain_rate():
    """测试固定降雨率的 ITU-Rpy 计算"""

    # 北京参数
    lat = 39.92
    lon = 116.45
    satellite_lon = 110.5
    frequency = 14.25 * u.GHz
    polarization = 'V'
    antenna_diameter = 1.8 * u.m

    # 计算仰角
    h_sat = 35786 * u.km
    elevation = itur.utils.elevation_angle(h_sat, 0, satellite_lon, lat, lon)
    print(f"仰角: {elevation:.2f}")

    # Simplified 模型计算的降雨率
    fixed_rain_rate = 34.70  # mm/h

    print("\n" + "="*70)
    print(f"测试: ITU-Rpy 使用固定降雨率 {fixed_rain_rate} mm/h")
    print("="*70)

    # ITU-R P.838: 计算比衰减 (给定降雨率)
    # 注意: ITU-Rpy 的 rain_attenuation 函数不接受固定降雨率
    # 它会根据概率自动计算降雨率
    # 所以我们需要手动计算比衰减和路径长度

    # 方法1: 使用 ITU-R P.838 计算比衰减系数
    from itur.models.itu838 import rain_specific_attenuation_coefficients

    # 转换极化
    tau = 0 if polarization.upper() == 'V' else 90  # 极化倾角

    # 计算 k 和 alpha 系数 (f:频率, el:仰角, tau:极化倾角)
    k, alpha = rain_specific_attenuation_coefficients(
        frequency, elevation, tau
    )

    gamma_R = float(k) * (fixed_rain_rate ** float(alpha))

    print(f"\n[ITU-R P.838] 比衰减计算")
    print(f"  频率: {frequency}")
    print(f"  降雨率 R: {fixed_rain_rate} mm/h")
    print(f"  k 参数: {float(k):.4f}")
    print(f"  alpha 参数: {float(alpha):.4f}")
    print(f"  比衰减 gamma_R: {gamma_R:.3f} dB/km")

    # 对比 Simplified 的比衰减
    simple_gamma = 0.08 * (fixed_rain_rate ** 1.1)
    print(f"\n[Simplified] 比衰减对比")
    print(f"  k = 0.08, alpha = 1.1")
    print(f"  比衰减: {simple_gamma:.3f} dB/km")

    # 方法2: 计算有效路径长度
    # ITU-R P.839: 获取雨顶高度
    from itur.models.itu839 import rain_height
    HR = rain_height(lat, lon)
    HR_val = HR.value if hasattr(HR, 'value') else float(HR)
    print(f"\n[ITU-R P.839] 雨顶高度")
    print(f"  HR = {HR_val:.2f} km")

    # 计算有效路径长度 (简化)
    import math
    el_val = elevation.value if hasattr(elevation, 'value') else float(elevation)
    Ls = (HR_val - 0) / math.sin(math.radians(el_val))  # 雨顶以下路径
    print(f"\n斜路径长度: Ls = {Ls:.2f} km")

    # 减缩因子 (ITU-R P.618)
    r = 1 / (1 + Ls / (35 * math.exp(-0.015 * fixed_rain_rate)))
    Leff = Ls * r
    print(f"减缩因子: r = {r:.3f}")
    print(f"有效路径长度: Leff = {Leff:.2f} km")

    # 对比 Simplified 的路径长度
    simple_Lbase = 5 / math.sin(math.radians(el_val))
    simple_r = 1 / (1 + simple_Lbase / 20)
    simple_Leff = simple_Lbase * simple_r
    print(f"\n[Simplified] 路径长度对比")
    print(f"  基础长度: {simple_Lbase:.2f} km")
    print(f"  有效长度: {simple_Leff:.2f} km")

    # 计算总降雨衰减
    itur_rain_att = gamma_R * Leff
    simple_rain_att = simple_gamma * simple_Leff

    print(f"\n[降雨衰减对比]")
    print(f"  ITU-R (使用 Simplified 降雨率): {itur_rain_att:.2f} dB")
    print(f"  Simplified: {simple_rain_att:.2f} dB")
    print(f"  差异: {abs(itur_rain_att - simple_rain_att):.2f} dB")

    # 分析差异来源
    print(f"\n[差异分析]")
    print(f"  比衰减差异: {gamma_R:.3f} vs {simple_gamma:.3f} dB/km = {gamma_R - simple_gamma:.3f} dB/km")
    print(f"  路径长度差异: {Leff:.2f} vs {simple_Leff:.2f} km = {Leff - simple_Leff:.2f} km")

    # 使用 ITU-Rpy 的完整计算 (自动计算降雨率)
    p = 0.05  # 99.95% 可用度
    A_g, A_c, A_r, A_s, A_t = itur.atmospheric_attenuation_slant_path(
        lat, lon, frequency, elevation, p, antenna_diameter,
        return_contributions=True
    )

    print(f"\n[ITU-Rpy 自动计算] p = {p}%")
    print(f"  降雨衰减: {A_r.value:.2f} dB")
    print(f"  气体衰减: {A_g.value:.2f} dB")
    print(f"  云衰减: {A_c.value:.2f} dB")
    print(f"  闪烁衰减: {A_s.value:.2f} dB")
    print(f"  总衰减: {A_t.value:.2f} dB")


if __name__ == '__main__':
    test_fixed_rain_rate()
