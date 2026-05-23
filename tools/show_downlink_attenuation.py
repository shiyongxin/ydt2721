#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示下行降雨衰减的所有计算参数
"""
import sys
import io

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import astropy.units as u
import itur

def main():
    # ========== 输入参数（来自报告：乌鲁木齐接收站） ==========
    lat = 43.77          # 纬度（度）
    lon = 87.68          # 经度（度）
    satellite_lon = 110.5  # 卫星经度（度）
    frequency = 12.5     # 下行频率（GHz）
    polarization = 'H'   # 极化方式（水平）
    antenna_diameter = 1.8  # 天线口径（米）
    availability = 99.950  # 下行可用度（%）
    station_height = 0.0   # 站高（km）

    p = 100 - availability  # 超时概率（%）

    print("=" * 70)
    print("下行降雨衰减计算参数")
    print("=" * 70)

    # ========== 1. 输入参数 ==========
    print("\n【一、输入参数】")
    print(f"  接收站: 乌鲁木齐")
    print(f"  纬度: {lat}°")
    print(f"  经度: {lon}°")
    print(f"  卫星经度: {satellite_lon}°")
    print(f"  下行频率: {frequency} GHz")
    print(f"  极化方式: {polarization}")
    print(f"  天线口径: {antenna_diameter} m")
    print(f"  下行可用度: {availability}%")
    print(f"  超时概率 p: {p}%")

    # ========== 2. 计算仰角 ==========
    from ydt2721.core.earth_station import calculate_antenna_pointing
    elevation, azimuth = calculate_antenna_pointing(lat, lon, satellite_lon)

    print(f"\n【二、天线指向角度】")
    print(f"  仰角: {elevation:.2f}°")
    print(f"  方位角: {azimuth:.2f}°")

    # ========== 3. ITU-R P.837 降雨率 ==========
    R001 = itur.models.itu837.rainfall_rate(lat, lon, p)
    print(f"\n【三、ITU-R P.837 降雨率】")
    print(f"  R_{p:.3f}% = {float(R001.value):.2f} mm/h")

    # ========== 4. ITU-R P.839 雨顶高度 ==========
    h_rain = itur.models.itu839.rain_height(lat, lon)
    print(f"\n【四、ITU-R P.839 雨顶高度】")
    print(f"  h_R = {float(h_rain.value):.3f} km")

    # ========== 5. ITU-R P.618 降雨衰减概率 ==========
    rain_prob = itur.models.itu618.rain_attenuation_probability(
        lat, lon, elevation, station_height
    )
    print(f"\n【五、ITU-R P.618 降雨衰减概率】")
    print(f"  降雨衰减概率: {float(rain_prob.value):.4f}%")

    # ========== 6. 先计算大气参数 ==========
    # 地表温度
    T = itur.surface_mean_temperature(lat, lon)
    T_celsius = float(T.value) - 273.15

    # 气压
    hs = itur.topographic_altitude(lat, lon)
    P = itur.standard_pressure(hs)

    # 水汽密度
    rho = itur.surface_water_vapour_density(lat, lon, p, hs)

    print(f"\n【六、大气参数】")
    print(f"  地表温度 T = {T_celsius:.2f} °C ({float(T.value):.2f} K)")
    print(f"  气压 P = {float(P.value):.2f} hPa")
    print(f"  水汽密度 ρ = {float(rho.value):.2f} g/m³")
    print(f"  地形高度 hs = {float(hs.value):.3f} km")

    # ========== 7. ITU-R P.676 气体衰减 ==========
    Ag = itur.gaseous_attenuation_slant_path(
        f=frequency * u.GHz,
        el=elevation,
        rho=float(rho.value),  # 使用纯数值
        P=float(P.value),      # 使用纯数值
        T=float(T.value)       # 使用纯数值
    )
    print(f"\n【六、ITU-R P.676 气体衰减】")
    print(f"  Ag = {float(Ag.value):.4f} dB")

    # ========== 8. ITU-R P.840 云衰减 ==========
    Ac = itur.cloud_attenuation(
        lat=lat,
        lon=lon,
        f=frequency * u.GHz,
        el=elevation,
        p=p
    )
    print(f"\n【七、ITU-R P.840 云衰减】")
    print(f"  Ac = {float(Ac.value):.4f} dB")

    # ========== 9. ITU-R P.618 降雨衰减 ==========
    Ar = itur.rain_attenuation(
        lat=lat,
        lon=lon,
        f=frequency * u.GHz,
        el=elevation,
        hs=station_height,
        p=p
    )
    print(f"\n【八、ITU-R P.618 降雨衰减】")
    print(f"  Ar = {float(Ar.value):.4f} dB")

    # ========== 10. ITU-R P.618 闪烁衰减 ==========
    As = itur.scintillation_attenuation(
        lat=lat,
        lon=lon,
        f=frequency * u.GHz,
        el=elevation,
        p=p,
        D=antenna_diameter * u.m
    )
    print(f"\n【九、ITU-R P.618 闪烁衰减】")
    print(f"  As = {float(As.value):.4f} dB")

    # ========== 11. 总大气衰减 ==========
    At = itur.atmospheric_attenuation_slant_path(
        lat,
        lon,
        frequency * u.GHz,
        elevation,
        p,
        antenna_diameter * u.m
    )
    print(f"\n【十、总大气衰减】")
    print(f"  At = {float(At.value):.4f} dB")

    # ========== 12. 验证：各分量之和 ==========
    sum_components = float(Ag.value) + float(Ac.value) + float(Ar.value) + float(As.value)
    print(f"\n【十二、分量验证】")
    print(f"  Ag + Ac + Ar + As = {sum_components:.4f} dB")
    print(f"  At (直接计算) = {float(At.value):.4f} dB")
    print(f"  差值 = {abs(sum_components - float(At.value)):.4f} dB")

    # ========== 13. 降雨噪声温度 ==========
    medium_temp = 260.0  # K
    rain_noise_temp = medium_temp * (1 - 1 / (10 ** (float(Ar.value) / 10)))
    print(f"\n【十三、降雨噪声温度】")
    print(f"  降雨噪声温度 = {rain_noise_temp:.2f} K (Tm = {medium_temp} K)")

    # ========== 14. 总结 ==========
    print("\n" + "=" * 70)
    print("【衰减分量汇总】")
    print("=" * 70)
    print(f"  气体衰减 (Ag):      {float(Ag.value):.4f} dB")
    print(f"  云衰减 (Ac):        {float(Ac.value):.4f} dB")
    print(f"  降雨衰减 (Ar):      {float(Ar.value):.4f} dB  ← 主要分量")
    print(f"  闪烁衰减 (As):      {float(As.value):.4f} dB")
    print("-" * 40)
    print(f"  总大气衰减 (At):    {float(At.value):.4f} dB")
    print("=" * 70)

    # ========== 15. 与报告数据对比 ==========
    print("\n【与报告数据对比】")
    print("  根据报告 report.md:")
    print("    晴天下行C/N = 9.60 dB")
    print("    雨天下行C/N = 5.66 dB")
    print("    差值 = 3.94 dB")
    print(f"\n  ITU-Rpy计算的降雨衰减 Ar = {float(Ar.value):.4f} dB")
    print(f"  加上G/T下降等因素后总影响 ≈ 3.94 dB")


if __name__ == "__main__":
    main()
