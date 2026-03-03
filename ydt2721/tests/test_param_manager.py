"""
单元测试 - 参数配置管理模块（M01）
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721.core.param_manager import ParameterValidator, ParameterManager
from ydt2721.models.dataclass import SatelliteParams, CarrierParams, EarthStationParams


class TestParameterValidator:
    """测试参数验证器"""

    def test_validate_range_valid(self):
        """测试有效范围验证"""
        assert ParameterValidator.validate_range('longitude', 116.45)
        assert ParameterValidator.validate_range('latitude', 39.92)
        assert ParameterValidator.validate_range('antenna_diameter', 4.5)
        assert ParameterValidator.validate_range('frequency', 14.25)

    def test_validate_range_invalid(self):
        """测试无效范围验证"""
        with pytest.raises(ValueError):
            ParameterValidator.validate_range('longitude', 200)

        with pytest.raises(ValueError):
            ParameterValidator.validate_range('latitude', 100)

        with pytest.raises(ValueError):
            ParameterValidator.validate_range('antenna_diameter', 0)

    def test_validate_modulation(self):
        """测试调制方式验证"""
        assert ParameterValidator.validate_modulation('QPSK')
        assert ParameterValidator.validate_modulation('BPSK')

        with pytest.raises(ValueError):
            ParameterValidator.validate_modulation('INVALID')

    def test_validate_polarization(self):
        """测试极化方式验证"""
        assert ParameterValidator.validate_polarization('V')
        assert ParameterValidator.validate_polarization('H')

        with pytest.raises(ValueError):
            ParameterValidator.validate_polarization('X')

    def test_validate_fec_rate(self):
        """测试FEC编码率验证"""
        assert ParameterValidator.validate_fec_rate(0.75)
        assert ParameterValidator.validate_fec_rate(0.5)
        assert ParameterValidator.validate_fec_rate(0.667)

        # 允许非标准值但在范围内
        assert ParameterValidator.validate_fec_rate(0.8)

        with pytest.raises(ValueError):
            ParameterValidator.validate_fec_rate(1.5)

    def test_validate_satellite_params(self):
        """测试卫星参数验证"""
        params = SatelliteParams(
            longitude=110.5,
            eirp_ss=48.48,
            gt_s=5.96,
            gt_s_ref=0,
            sfd_ref=-84,
            bo_i=6,
            bo_o=3,
            transponder_bw=54000000,
        )

        errors = ParameterValidator.validate_satellite_params(params)
        assert len(errors) == 0

    def test_validate_satellite_params_invalid(self):
        """测试无效卫星参数验证"""
        params = SatelliteParams(
            longitude=200,  # 无效
            eirp_ss=48.48,
            gt_s=5.96,
            gt_s_ref=0,
            sfd_ref=-84,
            bo_i=6,
            bo_o=3,
            transponder_bw=54000000,
        )

        errors = ParameterValidator.validate_satellite_params(params)
        assert len(errors) > 0

    def test_validate_carrier_params(self):
        """测试载波参数验证"""
        params = CarrierParams(
            info_rate=2000000,
            fec_rate=0.75,
            fec_type='DVB-S2',
            spread_gain=1,
            modulation='QPSK',
            modulation_index=2,
            ebno_threshold=4.5,
            alpha1=1.2,
            alpha2=1.4,
        )

        errors = ParameterValidator.validate_carrier_params(params)
        assert len(errors) == 0

    def test_validate_earth_station_params(self):
        """测试地球站参数验证"""
        params = EarthStationParams(
            name='北京',
            longitude=116.45,
            latitude=39.92,
            antenna_diameter=4.5,
            efficiency=0.65,
            frequency=14.25,
            polarization='V',
            feed_loss=1.5,
            antenna_noise_temp=35,
            receiver_noise_temp=75,
        )

        errors = ParameterValidator.validate_earth_station_params(params)
        assert len(errors) == 0

    def test_validate_all_params(self):
        """测试完整参数验证"""
        satellite = SatelliteParams(
            longitude=110.5,
            eirp_ss=48.48,
            gt_s=5.96,
            gt_s_ref=0,
            sfd_ref=-84,
            bo_i=6,
            bo_o=3,
            transponder_bw=54000000,
        )

        carrier = CarrierParams(
            info_rate=2000000,
            fec_rate=0.75,
            fec_type='DVB-S2',
            spread_gain=1,
            modulation='QPSK',
            modulation_index=2,
            ebno_threshold=4.5,
            alpha1=1.2,
            alpha2=1.4,
        )

        tx_station = EarthStationParams(
            name='北京',
            longitude=116.45,
            latitude=39.92,
            antenna_diameter=4.5,
            efficiency=0.65,
            frequency=14.25,
            polarization='V',
            feed_loss=1.5,
            antenna_noise_temp=35,
            receiver_noise_temp=75,
        )

        rx_station = EarthStationParams(
            name='乌鲁木齐',
            longitude=87.68,
            latitude=43.77,
            antenna_diameter=1.8,
            efficiency=0.65,
            frequency=12.50,
            polarization='H',
            feed_loss=0.2,
            antenna_noise_temp=35,
            receiver_noise_temp=75,
        )

        errors = ParameterValidator.validate_all_params(
            satellite, carrier, tx_station, rx_station, 99.66
        )

        assert len(errors) == 0


class TestParameterManager:
    """测试参数管理器"""

    def test_apply_defaults(self):
        """测试应用默认值"""
        params = {
            'satellite': {'longitude': 110.5},
            'carrier': {},
            'tx_station': {},
            'rx_station': {},
        }

        result = ParameterManager.apply_defaults(params)

        # 检查carrier的默认值
        assert 'spread_gain' in result
        assert result['spread_gain'] == 1
        assert result['alpha1'] == 1.2
        assert result['alpha2'] == 1.4

    def test_create_template(self):
        """测试创建模板"""
        template = ParameterManager.create_template('测试模板')

        assert template['name'] == '测试模板'
        assert 'satellite' in template
        assert 'carrier' in template
        assert 'tx_station' in template
        assert 'rx_station' in template

    def test_save_and_load_template(self, tmp_path):
        """测试保存和加载模板"""
        template = ParameterManager.create_template('测试模板')

        # 保存
        filepath = tmp_path / "template.json"
        ParameterManager.save_template(template, str(filepath))

        assert filepath.exists()

        # 加载
        loaded_template = ParameterManager.load_template(str(filepath))

        assert loaded_template['name'] == '测试模板'
        assert 'satellite' in loaded_template


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
