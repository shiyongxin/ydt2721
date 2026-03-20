"""
降雨衰减模型计算器
使用 ITU-Rpy 完整模型
"""

from typing import Dict, Optional

from .itu_rain_wrapper import (
    ITURainCalculator,
    calculate_rain_attenuation_iturpy,
    ITURPY_AVAILABLE,
)
from .space_loss import (
    calculate_gt_degradation,
)


class RainAttenuationCalculator:
    """
    降雨衰减计算器（使用 ITU-Rpy 模型）
    """

    def __init__(self):
        """
        初始化计算器
        """
        # 验证 ITU-Rpy 可用性
        if not ITURPY_AVAILABLE:
            raise ImportError(
                "ITU-Rpy not installed. Install it with: pip install itur"
            )

    def calculate(
        self,
        lat: float,
        lon: float,
        satellite_lon: float,
        frequency: float,
        polarization: str,
        antenna_diameter: float,
        availability: float,
        station_height: float = 0.0,
        elevation: Optional[float] = None,
        feed_loss: float = 0.2,
        system_noise_temp: float = 110.0
    ) -> Dict[str, float]:
        """
        计算降雨衰减和相关参数

        Args:
            lat: 纬度（度）
            lon: 经度（度）
            satellite_lon: 卫星经度（度）
            frequency: 频率（GHz）
            polarization: 极化方式
            antenna_diameter: 天线直径（米）
            availability: 系统可用度（%）
            station_height: 地球站海拔（km）
            elevation: 仰角（度），可选
            feed_loss: 馈线损耗（dB）
            system_noise_temp: 系统噪声温度（K）

        Returns:
            计算结果字典
        """
        return self._calculate_iturpy(
            lat, lon, satellite_lon, frequency, polarization,
            antenna_diameter, availability, station_height, elevation,
            feed_loss, system_noise_temp
        )

    def _calculate_iturpy(
        self,
        lat: float,
        lon: float,
        satellite_lon: float,
        frequency: float,
        polarization: str,
        antenna_diameter: float,
        availability: float,
        station_height: float,
        elevation: Optional[float],
        feed_loss: float,
        system_noise_temp: float
    ) -> Dict[str, float]:
        """使用 ITU-Rpy 计算"""
        result = calculate_rain_attenuation_iturpy(
            lat=lat,
            lon=lon,
            satellite_lon=satellite_lon,
            frequency=frequency,
            polarization=polarization,
            antenna_diameter=antenna_diameter,
            availability=availability,
            station_height=station_height,
            elevation=elevation
        )

        # 计算G/T下降（ITU-Rpy 不提供此功能）
        gt_degradation = calculate_gt_degradation(
            result['rain_noise_temp_K'],
            feed_loss,
            system_noise_temp
        )

        result['gt_degradation_dB'] = gt_degradation
        result['model'] = 'iturpy'

        return result

    def calculate_rain_attenuation_only(
        self,
        lat: float,
        lon: float,
        satellite_lon: float,
        frequency: float,
        polarization: str,
        antenna_diameter: float,
        availability: float,
        station_height: float = 0.0,
        elevation: Optional[float] = None
    ) -> float:
        """
        只计算降雨衰减（不含噪声温度和 G/T 下降）

        Args:
            lat: 纬度（度）
            lon: 经度（度）
            satellite_lon: 卫星经度（度）
            frequency: 频率（GHz）
            polarization: 极化方式
            antenna_diameter: 天线直径（米）
            availability: 系统可用度（%）
            station_height: 地球站海拔（km）
            elevation: 仰角（度），可选

        Returns:
            降雨衰减（dB）
        """
        calc = ITURainCalculator(
            lat=lat,
            lon=lon,
            satellite_lon=satellite_lon,
            frequency=frequency,
            polarization=polarization,
            antenna_diameter=antenna_diameter,
            elevation=elevation,
            station_height=station_height
        )

        return calc.calculate_rain_attenuation(availability)
