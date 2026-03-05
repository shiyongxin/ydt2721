"""
降雨衰减模型选择器
支持在简化模型和 ITU-Rpy 完整模型之间切换
"""

from enum import Enum
from typing import Dict, Optional

from .space_loss import (
    calculate_rain_attenuation as calculate_rain_attenuation_simplified,
    calculate_rain_noise_temp as calculate_rain_noise_temp_simplified,
    calculate_gt_degradation,
)
from .itu_rain_wrapper import (
    ITURainCalculator,
    calculate_rain_attenuation_iturpy,
    ITURPY_AVAILABLE,
)


class RainModel(Enum):
    """降雨衰减模型类型"""
    SIMPLIFIED = "simplified"
    ITURPY = "iturpy"


class RainAttenuationCalculator:
    """
    降雨衰减计算器（支持多种模型）
    """

    def __init__(self, model: RainModel = RainModel.SIMPLIFIED):
        """
        初始化计算器

        Args:
            model: 降雨衰减模型
        """
        self.model = model

        # 验证 ITU-Rpy 可用性
        if self.model == RainModel.ITURPY and not ITURPY_AVAILABLE:
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
        if self.model == RainModel.SIMPLIFIED:
            return self._calculate_simplified(
                lat, lon, frequency, availability, elevation, polarization,
                feed_loss, system_noise_temp
            )
        elif self.model == RainModel.ITURPY:
            return self._calculate_iturpy(
                lat, lon, satellite_lon, frequency, polarization,
                antenna_diameter, availability, station_height, elevation,
                feed_loss, system_noise_temp
            )
        else:
            raise ValueError(f"Unknown model: {self.model}")

    def _calculate_simplified(
        self,
        lat: float,
        lon: float,
        frequency: float,
        availability: float,
        elevation: float,
        polarization: str,
        feed_loss: float,
        system_noise_temp: float
    ) -> Dict[str, float]:
        """使用简化模型计算"""
        rain_attenuation = calculate_rain_attenuation_simplified(
            availability, frequency, elevation, lat, polarization
        )

        rain_noise_temp = calculate_rain_noise_temp_simplified(rain_attenuation)

        gt_degradation = calculate_gt_degradation(
            rain_noise_temp, feed_loss, system_noise_temp
        )

        return {
            'rain_attenuation_dB': rain_attenuation,
            'rain_noise_temp_K': rain_noise_temp,
            'gt_degradation_dB': gt_degradation,
            'model': 'simplified',
        }

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
        if self.model == RainModel.SIMPLIFIED:
            from .earth_station import calculate_antenna_pointing

            if elevation is None:
                elevation, _ = calculate_antenna_pointing(lat, lon, satellite_lon)

            return calculate_rain_attenuation_simplified(
                availability, frequency, elevation, lat, polarization
            )
        elif self.model == RainModel.ITURPY:
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
        else:
            raise ValueError(f"Unknown model: {self.model}")
