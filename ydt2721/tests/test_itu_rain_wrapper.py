"""
ITU-Rpy 封装模块测试
"""

import pytest
import sys


class TestITURpyAvailable:
    """测试 ITU-Rpy 是否可用"""

    def test_iturpy_import(self):
        """测试 ITU-Rpy 导入"""
        try:
            import itur
            assert True
        except ImportError:
            pytest.skip("ITU-Rpy not installed")

    def test_wrapper_import(self):
        """测试封装模块导入"""
        try:
            from ydt2721.core.itu_rain_wrapper import (
                ITURainCalculator,
                calculate_rain_attenuation_iturpy,
                ITURPY_AVAILABLE,
            )
            assert True
        except ImportError as e:
            pytest.skip(f"Cannot import wrapper: {e}")


@pytest.mark.skipif(
    not __import__('ydt2721.core.itu_rain_wrapper', fromlist=['ITURPY_AVAILABLE']).ITURPY_AVAILABLE,
    reason="ITU-Rpy not installed"
)
class TestITURainCalculator:
    """ITU-Rpy 封装测试"""

    def test_init(self):
        """测试初始化"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )
        assert calc.lat == 39.92
        assert calc.lon == 116.45
        assert calc.satellite_lon == 110.5
        assert calc.frequency.value == 14.25
        assert calc.polarization == 'V'
        assert calc.antenna_diameter.value == 4.5
        assert calc.station_height == 0.0
        assert calc.elevation > 0  # 应该自动计算仰角

    def test_init_with_elevation(self):
        """测试初始化（指定仰角）"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            elevation=45.0
        )
        assert calc.elevation == 45.0

    def test_calculate_rain_attenuation(self):
        """测试降雨衰减计算"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        att = calc.calculate_rain_attenuation(availability=99.9)
        assert att > 0  # 衰减应该大于0
        assert att < 100  # 衰减不应该过大

    def test_calculate_rain_attenuation_different_availability(self):
        """测试不同可用度的降雨衰减"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        # ITU-Rpy 计算的是超过该值的概率为 p
        # 更高的可用度（更小的 p）对应更大的极端降雨
        att_999 = calc.calculate_rain_attenuation(availability=99.9)
        att_950 = calc.calculate_rain_attenuation(availability=99.5)
        att_990 = calc.calculate_rain_attenuation(availability=99.0)

        # 更高的可用度（99.9% > 99.5%）应该对应更大的衰减
        assert att_999 > att_950
        # 更低的可用度（99.0% < 99.5%）应该对应更小的衰减
        assert att_990 < att_950

    def test_calculate_atmospheric_attenuation_without_contributions(self):
        """测试大气衰减计算（不含分量）"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        att, contributions = calc.calculate_atmospheric_attenuation(
            availability=99.9,
            return_contributions=False
        )

        assert att > 0
        assert contributions == {}  # 不应该返回分量

    def test_calculate_atmospheric_attenuation_with_contributions(self):
        """测试大气衰减计算（含分量）"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        att, contributions = calc.calculate_atmospheric_attenuation(
            availability=99.9,
            return_contributions=True
        )

        assert 'rain' in contributions
        assert 'gas' in contributions
        assert 'cloud' in contributions
        assert 'scintillation' in contributions
        assert 'total' in contributions

        # 各分量应该大于0
        assert contributions['rain'] >= 0
        assert contributions['gas'] >= 0
        assert contributions['cloud'] >= 0
        assert contributions['scintillation'] >= 0

        # 总衰减应该等于各分量之和（近似）
        total_contrib = sum(contributions[k] for k in ['rain', 'gas', 'cloud', 'scintillation'])
        assert abs(total_contrib - contributions['total']) < 2.0  # 允许一定误差

    def test_calculate_gas_attenuation(self):
        """测试气体衰减计算"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        ag = calc.calculate_gas_attenuation(availability=99.9)
        assert ag >= 0
        assert ag < 10  # 气体衰减通常较小

    def test_calculate_cloud_attenuation(self):
        """测试云衰减计算"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        ac = calc.calculate_cloud_attenuation(availability=99.9)
        assert ac >= 0
        assert ac < 5  # 云衰减通常较小

    def test_calculate_scintillation_attenuation(self):
        """测试闪烁衰减计算"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        as_att = calc.calculate_scintillation_attenuation(availability=99.9)
        assert as_att >= 0
        assert as_att < 1  # 闪烁衰减通常很小

    def test_calculate_rain_noise_temp(self):
        """测试降雨噪声温度计算"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        # 测试不同降雨衰减
        for rain_att in [1, 5, 10, 20]:
            noise_temp = calc.calculate_rain_noise_temp(rain_att)
            assert noise_temp > 0
            assert noise_temp < 260  # 不应该超过介质温度

    def test_get_atmospheric_parameters(self):
        """测试获取大气参数"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        params = calc.get_atmospheric_parameters(availability=99.9)

        assert 'elevation_km' in params
        assert 'surface_temp_C' in params
        assert 'pressure_hPa' in params
        assert 'water_vapor_density_g_m3' in params
        assert 'rain_rate_mm_h' in params
        assert 'rain_height_km' in params
        assert 'rain_attenuation_probability_pct' in params

        # 验证数值范围
        assert params['elevation_km'] >= -500  # 最低海拔
        assert params['surface_temp_C'] > -50
        assert params['surface_temp_C'] < 60
        assert params['pressure_hPa'] > 500
        assert params['pressure_hPa'] < 1100
        assert params['rain_rate_mm_h'] >= 0
        assert params['rain_height_km'] > 0
        assert params['rain_attenuation_probability_pct'] >= 0

    def test_calculate_attenuation_curve(self):
        """测试衰减曲线计算"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        availabilities = [99.9, 99.5, 99.0]

        # 测试总衰减
        results = calc.calculate_attenuation_curve(availabilities, component='total')
        assert len(results) == 3
        assert 99.9 in results
        assert 99.5 in results
        assert 99.0 in results
        for avail, att in results.items():
            assert att > 0

        # 测试降雨衰减
        rain_results = calc.calculate_attenuation_curve(availabilities, component='rain')
        assert len(rain_results) == 3
        for avail, att in rain_results.items():
            assert att > 0

        # 测试气体衰减
        gas_results = calc.calculate_attenuation_curve(availabilities, component='gas')
        assert len(gas_results) == 3

    def test_invalid_component(self):
        """测试无效的衰减分量"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5
        )

        with pytest.raises(ValueError):
            calc.calculate_attenuation_curve([99.9], component='invalid')

    def test_polarization_case_insensitive(self):
        """测试极化方式不区分大小写"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator

        calc1 = ITURainCalculator(
            lat=39.92, lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='h',  # 小写
            antenna_diameter=4.5
        )

        calc2 = ITURainCalculator(
            lat=39.92, lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='H',  # 大写
            antenna_diameter=4.5
        )

        assert calc1.polarization == 'H'
        assert calc2.polarization == 'H'


@pytest.mark.skipif(
    not __import__('ydt2721.core.itu_rain_wrapper', fromlist=['ITURPY_AVAILABLE']).ITURPY_AVAILABLE,
    reason="ITU-Rpy not installed"
)
class TestConvenienceFunction:
    """便捷函数测试"""

    def test_calculate_rain_attenuation_iturpy(self):
        """测试便捷函数"""
        from ydt2721.core.itu_rain_wrapper import calculate_rain_attenuation_iturpy

        result = calculate_rain_attenuation_iturpy(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9
        )

        assert 'rain_attenuation_dB' in result
        assert 'gas_attenuation_dB' in result
        assert 'cloud_attenuation_dB' in result
        assert 'scintillation_attenuation_dB' in result
        assert 'total_attenuation_dB' in result
        assert 'rain_noise_temp_K' in result
        assert 'rain_rate_mm_h' in result
        assert 'rain_height_km' in result

        # 验证数值
        assert result['rain_attenuation_dB'] >= 0
        assert result['gas_attenuation_dB'] >= 0
        assert result['cloud_attenuation_dB'] >= 0
        assert result['scintillation_attenuation_dB'] >= 0
        assert result['total_attenuation_dB'] > 0
        assert result['rain_noise_temp_K'] >= 0
        assert result['rain_rate_mm_h'] >= 0
        assert result['rain_height_km'] > 0

    def test_convenience_function_with_elevation(self):
        """测试便捷函数（指定仰角）"""
        from ydt2721.core.itu_rain_wrapper import calculate_rain_attenuation_iturpy

        result = calculate_rain_attenuation_iturpy(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9,
            elevation=45.0
        )

        assert 'rain_attenuation_dB' in result

    def test_convenience_function_different_locations(self):
        """测试不同位置的便捷函数"""
        from ydt2721.core.itu_rain_wrapper import calculate_rain_attenuation_iturpy

        # 北京
        result_beijing = calculate_rain_attenuation_iturpy(
            lat=39.92, lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9
        )

        # 乌鲁木齐
        result_urumqi = calculate_rain_attenuation_iturpy(
            lat=43.77, lon=87.68,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            availability=99.9
        )

        # 两个位置的结果应该不同
        assert abs(result_beijing['rain_attenuation_dB'] - result_urumqi['rain_attenuation_dB']) > 0.1


@pytest.mark.skipif(
    not __import__('ydt2721.core.itu_rain_wrapper', fromlist=['ITURPY_AVAILABLE']).ITURPY_AVAILABLE,
    reason="ITU-Rpy not installed"
)
class TestIntegration:
    """集成测试"""

    def test_integration_with_ydt2721(self):
        """测试与 ydt2721 的集成"""
        from ydt2721.core.itu_rain_wrapper import ITURainCalculator
        from ydt2721.core.earth_station import calculate_antenna_pointing

        # 使用 ydt2721 计算仰角
        elevation, azimuth = calculate_antenna_pointing(39.92, 116.45, 110.5)

        # 使用 ITU-Rpy 计算衰减
        calc = ITURainCalculator(
            lat=39.92,
            lon=116.45,
            satellite_lon=110.5,
            frequency=14.25,
            polarization='V',
            antenna_diameter=4.5,
            elevation=elevation  # 使用 ydt2721 计算的仰角
        )

        att = calc.calculate_rain_attenuation(availability=99.9)
        assert att > 0
