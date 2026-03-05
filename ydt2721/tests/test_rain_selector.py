"""
降雨模型选择器测试
"""

import pytest
import sys


@pytest.mark.skipif(
    not __import__('ydt2721.core.itu_rain_wrapper', fromlist=['ITURPY_AVAILABLE']).ITURPY_AVAILABLE,
    reason="ITU-Rpy not installed"
)
class TestRainSelector:
    """降雨模型选择器测试"""

    def test_init_simplified(self):
        """测试初始化（简化模型）"""
        from ydt2721.core.rain_selector import RainAttenuationCalculator, RainModel

        calc = RainAttenuationCalculator(model=RainModel.SIMPLIFIED)
        assert calc.model == RainModel.SIMPLIFIED

    def test_init_iturpy(self):
        """测试初始化（ITU-Rpy 模型）"""
        from ydt2721.core.rain_selector import RainAttenuationCalculator, RainModel

        calc = RainAttenuationCalculator(model=RainModel.ITURPY)
        assert calc.model == RainModel.ITURPY

    def test_calculate_simplified(self):
        """测试简化模型计算"""
        from ydt2721.core.rain_selector import RainAttenuationCalculator, RainModel

        calc = RainAttenuationCalculator(model=RainModel.SIMPLIFIED)

        result = calc.calculate(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9,
            station_height=0.0,
            elevation=34.59,
            feed_loss=0.2,
            system_noise_temp=110.0
        )

        assert 'rain_attenuation_dB' in result
        assert 'rain_noise_temp_K' in result
        assert 'gt_degradation_dB' in result
        assert result['model'] == 'simplified'
        assert result['rain_attenuation_dB'] > 0

    def test_calculate_iturpy(self):
        """测试 ITU-Rpy 模型计算"""
        from ydt2721.core.rain_selector import RainAttenuationCalculator, RainModel

        calc = RainAttenuationCalculator(model=RainModel.ITURPY)

        result = calc.calculate(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9,
            station_height=0.0,
            elevation=34.59,
            feed_loss=0.2,
            system_noise_temp=110.0
        )

        assert 'rain_attenuation_dB' in result
        assert 'rain_noise_temp_K' in result
        assert 'gt_degradation_dB' in result
        assert result['model'] == 'iturpy'
        assert result['rain_attenuation_dB'] > 0

    def test_calculate_rain_attenuation_only(self):
        """测试只计算降雨衰减"""
        from ydt2721.core.rain_selector import RainAttenuationCalculator, RainModel

        # 简化模型
        calc_simplified = RainAttenuationCalculator(model=RainModel.SIMPLIFIED)
        att_simplified = calc_simplified.calculate_rain_attenuation_only(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9,
            station_height=0.0,
            elevation=34.59
        )
        assert att_simplified > 0

        # ITU-Rpy
        calc_iturpy = RainAttenuationCalculator(model=RainModel.ITURPY)
        att_iturpy = calc_iturpy.calculate_rain_attenuation_only(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9,
            station_height=0.0,
            elevation=34.59
        )
        assert att_iturpy > 0


@pytest.mark.skipif(
    not __import__('ydt2721.core.itu_rain_wrapper', fromlist=['ITURPY_AVAILABLE']).ITURPY_AVAILABLE,
    reason="ITU-Rpy not installed"
)
class TestIntegrationWithCalculator:
    """与主计算器的集成测试"""

    def test_complete_link_budget_with_simplified(self):
        """测试完整链路计算（简化模型）"""
        from ydt2721 import complete_link_budget

        result = complete_link_budget(
            sat_longitude=110.5,
            sat_eirp_ss=48.48,
            sat_gt=5.96,
            sat_gt_ref=0,
            sat_sfd_ref=-84,
            sat_bo_i=6,
            sat_bo_o=3,
            sat_transponder_bw=54000000,

            info_rate=2000000,
            fec_rate=0.75,
            modulation='QPSK',
            spread_gain=1,
            ebno_th=4.5,
            alpha1=1.2,
            alpha2=1.4,

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

            availability=99.66,
            rain_model='simplified'
        )

        assert result.rain_model == 'simplified'
        assert result.clear_sky_margin > 0

    def test_complete_link_budget_with_iturpy(self):
        """测试完整链路计算（ITU-Rpy 模型）"""
        from ydt2721 import complete_link_budget

        result = complete_link_budget(
            sat_longitude=110.5,
            sat_eirp_ss=48.48,
            sat_gt=5.96,
            sat_gt_ref=0,
            sat_sfd_ref=-84,
            sat_bo_i=6,
            sat_bo_o=3,
            sat_transponder_bw=54000000,

            info_rate=2000000,
            fec_rate=0.75,
            modulation='QPSK',
            spread_gain=1,
            ebno_th=4.5,
            alpha1=1.2,
            alpha2=1.4,

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

            availability=99.66,
            rain_model='iturpy'
        )

        assert result.rain_model == 'iturpy'
        assert result.clear_sky_margin > 0
        # ITU-Rpy 应该返回额外的衰减分量
        assert result.rx_gas_attenuation >= 0
        assert result.rx_cloud_attenuation >= 0
        assert result.rx_scintillation_attenuation >= 0
