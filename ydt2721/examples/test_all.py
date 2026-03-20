"""
完整链路计算测试 - YDT 2721
使用详细设计中的直接参数值进行测试
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721 import complete_link_budget
from ydt2721.core.clear_sky import (
    calculate_downlink_cn,
    calculate_uplink_cn,
    calculate_satellite_power_allocation,
    calculate_threshold_cn,
    calculate_margin,
    calculate_system_cn,
)
from ydt2721.core.earth_station import calculate_earth_station_gt
from ydt2721.core.constants import BOLTZMANN_CONSTANT_DB


def test_downlink_cn_direct():
    """直接测试下行C/N计算"""
    # 使用详细设计2.5.2节中的示例值
    cn_d = calculate_downlink_cn(
        eirp_sl=27.19,
        loss_d=206.03,
        loss_ar=0.5,
        gt_e=24.53,
        noise_bandwidth=1600000
    )
    print(f"✅ 下行C/N计算: {cn_d:.2f} dB")
    assert abs(cn_d - 11.7) < 0.1, f"Expected ~11.7, got {cn_d}"


def test_uplink_cn_direct():
    """直接测试上行C/N计算"""
    # 使用详细设计中的示例值
    cn_u = calculate_uplink_cn(
        pfd=-114.25,
        gm2=44.53,
        gt_s=5.96,
        noise_bandwidth=1600000
    )
    print(f"✅ 上行C/N计算: {cn_u:.2f} dB")
    assert abs(cn_u - 13.7) < 0.1, f"Expected ~13.7, got {cn_u}"


def test_system_cn_direct():
    """直接测试系统C/N计算"""
    cn_t = calculate_system_cn(
        cn_u=13.7,
        cn_d=11.7,
        ci_im=15.0,
        ci_u_as=25.91,
        ci_d_as=21.51,
        ci_u_xp=19.11,
        ci_d_xp=19.35
    )
    print(f"✅ 系统C/N计算: {cn_t:.2f} dB")
    assert abs(cn_t - 7.58) < 0.1, f"Expected ~7.58, got {cn_t}"


def test_threshold_cn_direct():
    """直接测试门限C/N计算"""
    cn_th = calculate_threshold_cn(
        ebno_th=4.5,
        info_rate=2000000,
        noise_bandwidth=1600000
    )
    print(f"✅ 门限C/N计算: {cn_th:.2f} dB")
    assert abs(cn_th - 5.47) < 0.1, f"Expected ~5.47, got {cn_th}"


def test_margin_direct():
    """直接测试余量计算"""
    margin = calculate_margin(
        cn_system=7.58,
        cn_th=5.47
    )
    print(f"✅ 系统余量计算: {margin:.2f} dB")
    assert abs(margin - 2.11) < 0.01, f"Expected ~2.11, got {margin}"


def test_satellite_power_allocation():
    """测试卫星功率分配计算"""
    eirp_sl, pfd, bo_il, bo_ol = calculate_satellite_power_allocation(
        eirp_ss=48.48,
        bo_o=3,
        sfd=-89.96,
        bandwidth_ratio=0.0346,
        bo_i=6
    )
    print(f"✅ 卫星载波EIRP: {eirp_sl:.2f} dBW")
    print(f"✅ 卫星PFD: {pfd:.2f} dB(W/m²)")
    print(f"✅ 输入回退: {bo_il:.2f} dB")
    print(f"✅ 输出回退: {bo_ol:.2f} dB")


def test_full_link_budget():
    """测试完整链路计算（使用简化场景）"""
    print("\n" + "="*60)
    print("完整链路计算测试")
    print("="*60 + "\n")

    result = complete_link_budget(
        # 卫星参数
        sat_longitude=110.5,
        sat_eirp_ss=48.48,
        sat_gt=5.96,
        sat_gt_ref=0,
        sat_sfd_ref=-84,
        sat_bo_i=6,
        sat_bo_o=3,
        sat_transponder_bw=54000000,

        # 载波参数
        info_rate=2000000,
        fec_rate=0.75,
        modulation='QPSK',
        spread_gain=1,
        ebno_th=4.5,
        alpha1=1.2,
        alpha2=1.4,

        # 发射站参数（北京）
        tx_station_name='北京',
        tx_lat=39.92,
        tx_lon=116.45,
        tx_antenna_diameter=4.5,
        tx_efficiency=0.65,
        tx_frequency=14.25,
        tx_polarization='V',
        tx_feed_loss=1.5,
        tx_loss_at=0.5,
        upc_max=5.0,

        # 接收站参数（乌鲁木齐）
        rx_station_name='乌鲁木齐',
        rx_lat=43.77,
        rx_lon=87.68,
        rx_antenna_diameter=1.8,
        rx_efficiency=0.65,
        rx_frequency=12.50,
        rx_polarization='H',
        rx_feed_loss=0.2,
        rx_loss_ar=0.5,
        rx_antenna_noise_temp=35,
        rx_receiver_noise_temp=75,

        # 系统参数
        availability=99.66,
    )

    # 验证带宽计算
    assert abs(result.symbol_rate - 1333333) < 1000, f"符号速率错误: {result.symbol_rate}"
    assert abs(result.noise_bandwidth - 1600000) < 1000, f"噪声带宽错误: {result.noise_bandwidth}"
    assert abs(result.bandwidth_ratio - 3.46) < 0.1, f"带宽占用比错误: {result.bandwidth_ratio}"

    # 验证地球站参数
    assert abs(result.elevation - 34.59) < 0.1, f"仰角错误: {result.elevation}"
    assert abs(result.azimuth - 148.69) < 0.1, f"方位角错误: {result.azimuth}"

    print(f"📊 符号速率: {result.symbol_rate:.0f} symbol/s")
    print(f"📊 噪声带宽: {result.noise_bandwidth:.0f} Hz")
    print(f"📊 分配带宽: {result.allocated_bandwidth:.0f} Hz")
    print(f"📊 带宽占用比: {result.bandwidth_ratio:.2f}%")
    print(f"📊 接收仰角: {result.elevation:.2f}°")
    print(f"📊 接收方位角: {result.azimuth:.2f}°")
    print(f"📊 上行损耗: {result.uplink_loss:.2f} dB")
    print(f"📊 下行损耗: {result.downlink_loss:.2f} dB")
    print(f"📊 卫星载波EIRP: {result.satellite_eirp:.2f} dBW")
    print(f"📊 上行C/N: {result.clear_sky_cn_u:.2f} dB")
    print(f"📊 下行C/N: {result.clear_sky_cn_d:.2f} dB")
    print(f"📊 系统C/N: {result.clear_sky_cn_t:.2f} dB")
    print(f"📊 门限C/N: {result.cn_th:.2f} dB")
    print(f"📊 晴天系统余量: {result.clear_sky_margin:.2f} dB")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("YDT 2721 卫星链路计算 - 单元测试")
    print("="*60 + "\n")

    print("测试1: 下行C/N计算")
    test_downlink_cn_direct()

    print("\n测试2: 上行C/N计算")
    test_uplink_cn_direct()

    print("\n测试3: 系统C/N计算")
    test_system_cn_direct()

    print("\n测试4: 门限C/N计算")
    test_threshold_cn_direct()

    print("\n测试5: 系统余量计算")
    test_margin_direct()

    print("\n测试6: 卫星功率分配")
    test_satellite_power_allocation()

    print("\n测试7: 完整链路计算")
    test_full_link_budget()

    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60 + "\n")
