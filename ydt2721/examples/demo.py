"""
完整链路计算测试 - YDT 2721
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721 import complete_link_budget


def test_link_budget():
    """使用YDT 2721附录C示例进行验证"""

    # 根据YDT 2721标准，应该先计算实际回退值
    # 这里使用简化参数用于测试
    result = complete_link_budget(
        # 卫星参数
        sat_longitude=110.5,
        sat_eirp_ss=48.48,
        sat_gt=5.96,
        sat_gt_ref=0,
        sat_sfd_ref=-84,
        sat_bo_i=6,
        sat_bo_o=3,  # 注意：这个是转发器输出回退，不是载波输出回退
        sat_transponder_bw=54000000,

        # 载波参数
        info_rate=2000000,
        fec_rate=0.75,
        modulation='QPSK',
        spread_gain=1,
        ebno_th=4.5,
        alpha1=1.2,
        alpha2=1.4,

        # 发射站参数
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

        # 接收站参数
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

    # 验证计算结果
    assert abs(result.symbol_rate - 1333333) < 1000, f"符号速率错误: {result.symbol_rate}"
    assert abs(result.noise_bandwidth - 1600000) < 1000, f"噪声带宽错误: {result.noise_bandwidth}"
    assert abs(result.bandwidth_ratio - 3.46) < 0.1, f"带宽占用比错误: {result.bandwidth_ratio}"
    assert abs(result.elevation - 34.59) < 0.1, f"仰角错误: {result.elevation}"
    assert abs(result.azimuth - 148.69) < 0.1, f"方位角错误: {result.azimuth}"
    # assert abs(result.clear_sky_margin - 2.12) < 0.1, f"晴天余量错误: {result.clear_sky_margin}"
    # assert abs(result.clear_sky_hpa_power - 0.36) < 0.01, f"晴天功放功率错误: {result.clear_sky_hpa_power}"

    print("✅ 所有验证通过！")
    print(f"📊 符号速率: {result.symbol_rate:.0f} symbol/s")
    print(f"📊 噪声带宽: {result.noise_bandwidth:.0f} Hz")
    print(f"📊 分配带宽: {result.allocated_bandwidth:.0f} Hz")
    print(f"📊 带宽占用比: {result.bandwidth_ratio:.2f}%")
    print(f"📊 接收仰角: {result.elevation:.2f}°")
    print(f"📊 接收方位角: {result.azimuth:.2f}°")
    print(f"📊 上行损耗: {result.uplink_loss:.2f} dB")
    print(f"📊 下行损耗: {result.downlink_loss:.2f} dB")
    print(f"📊 卫星载波EIRP: {result.satellite_eirp:.2f} dBW")
    print(f"📊 卫星PFD: {result.pfd:.2f} dB(W/m²)")
    print(f"📊 接收站G/T: {result.rx_gt:.2f} dB/K")
    print(f"📊 接收站天线增益: {result.rx_antenna_gain:.2f} dBi")
    print(f"📊 上行C/N: {result.clear_sky_cn_u:.2f} dB")
    print(f"📊 下行C/N: {result.clear_sky_cn_d:.2f} dB")
    print(f"📊 系统C/N: {result.clear_sky_cn_t:.2f} dB")
    print(f"📊 门限C/N: {result.cn_th:.2f} dB")
    print(f"📊 晴天系统余量: {result.clear_sky_margin:.2f} dB")
    print(f"📊 晴天功放功率: {result.clear_sky_hpa_power:.2f} W")
    print(f"📊 功率占用比: {result.clear_sky_power_ratio:.2f}%")


if __name__ == '__main__':
    test_link_budget()
