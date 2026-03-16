"""
ITU-Rpy 库封装模块
将 ITU-Rpy 的接口适配到 ydt2721 的参数体系
"""

import astropy.units as u
from typing import Dict, Tuple, Optional

try:
    import itur
    ITURPY_AVAILABLE = True
except ImportError:
    ITURPY_AVAILABLE = False


class ITURainCalculator:
    """
    ITU-Rpy 降雨衰减计算器封装
    """

    def __init__(
        self,
        lat: float,
        lon: float,
        satellite_lon: float,
        frequency: float,
        polarization: str,
        antenna_diameter: float,
        elevation: Optional[float] = None,
        station_height: float = 0.0
    ):
        """
        初始化计算器

        Args:
            lat: 纬度（度）
            lon: 经度（度）
            satellite_lon: 卫星经度（度）
            frequency: 频率（GHz）
            polarization: 极化方式 ('H' 或 'V')
            antenna_diameter: 天线直径（米）
            elevation: 仰角（度），可选，不指定则自动计算
            station_height: 地球站海拔（km）
        """
        if not ITURPY_AVAILABLE:
            raise ImportError("ITU-Rpy not installed. Run: pip install itur")

        self.lat = lat
        self.lon = lon
        self.satellite_lon = satellite_lon
        self.frequency = frequency * u.GHz
        self.polarization = polarization.upper()
        self.antenna_diameter = antenna_diameter * u.m
        self.station_height = station_height

        # 计算仰角（如果未提供）
        if elevation is None:
            from .earth_station import calculate_antenna_pointing
            elevation, _ = calculate_antenna_pointing(lat, lon, satellite_lon)
        self.elevation = elevation

    def calculate_atmospheric_attenuation(
        self,
        availability: float,
        return_contributions: bool = False
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算大气衰减（总衰减或各分量）

        Args:
            availability: 系统可用度（%）
            return_contributions: 是否返回各分量

        Returns:
            (总衰减, 分量字典)
        """
        # 转换为超时概率
        p = 100 - availability # 转换为不可用性百分比

        # 计算总大气衰减
        if return_contributions:
            Ag, Ac, Ar, As, At = itur.atmospheric_attenuation_slant_path(
                self.lat,
                self.lon,
                self.frequency,
                self.elevation,
                p,
                self.antenna_diameter,
                return_contributions=True
            )

            contributions = {
                'gas': float(Ag.value),
                'cloud': float(Ac.value),
                'rain': float(Ar.value),
                'scintillation': float(As.value),
                'total': float(At.value)
            }

            return float(At.value), contributions
        else:
            At = itur.atmospheric_attenuation_slant_path(
                self.lat,
                self.lon,
                self.frequency,
                self.elevation,
                p,
                self.antenna_diameter
            )
            return float(At.value), {}

    def calculate_rain_attenuation(
        self,
        availability: float
    ) -> float:
        """
        计算降雨衰减

        Args:
            availability: 系统可用度（%）

        Returns:
            降雨衰减（dB）
        """
        p = 100 - availability  # 转换为不可用性百分比

        Ar = itur.rain_attenuation(
            lat=self.lat,
            lon=self.lon,
            f=self.frequency,
            el=self.elevation,
            hs=self.station_height,
            p=p
        )

        return float(Ar.value)

    def calculate_gas_attenuation(
        self,
        availability: float = 99.9,
        rho: Optional[float] = None,
        P: Optional[float] = None,
        T: Optional[float] = None
    ) -> float:
        """
        计算气体衰减

        Args:
            availability: 系统可用度（%），用于计算水汽密度
            rho: 水汽密度（g/m³），可选
            P: 气压（hPa），可选
            T: 温度（°C），可选

        Returns:
            气体衰减（dB）
        """
        # 使用自动计算的大气参数（如果未提供）
        if rho is None or P is None or T is None:
            p = 100 - availability  # 转换为不可用性百分比
            rho_p = itur.surface_water_vapour_density(
                self.lat, self.lon, p, self.station_height
            )
            P_val = itur.standard_pressure(self.lat, self.station_height)
            T_val = itur.surface_mean_temperature(self.lat, self.lon)

            rho = float(rho_p.value) if rho is None else rho
            P = float(P_val.value) if P is None else P
            T = float(T_val.value) if T is None else T

        Ag = itur.gaseous_attenuation_slant_path(
            f=self.frequency,
            el=self.elevation,
            rho=rho * u.g / u.m**3,
            P=P * u.hPa,
            T=T * u.deg_C
        )

        return float(Ag.value)

    def calculate_cloud_attenuation(
        self,
        availability: float = 99.9
    ) -> float:
        """
        计算云衰减

        Args:
            availability: 系统可用度（%）

        Returns:
            云衰减（dB）
        """
        p = 100 - availability  # 转换为不可用性百分比

        Ac = itur.cloud_attenuation(
            lat=self.lat,
            lon=self.lon,
            el=self.elevation,
            f=self.frequency,
            p=p
        )

        return float(Ac.value)

    def calculate_scintillation_attenuation(
        self,
        availability: float = 99.9
    ) -> float:
        """
        计算闪烁衰减

        Args:
            availability: 系统可用度（%）

        Returns:
            闪烁衰减（dB）
        """
        p = 100 - availability  # 转换为不可用性百分比

        As = itur.scintillation_attenuation(
            lat=self.lat,
            lon=self.lon,
            f=self.frequency,
            el=self.elevation,
            p=p,
            D=self.antenna_diameter
        )

        return float(As.value)

    def calculate_rain_noise_temp(
        self,
        rain_attenuation: float,
        medium_temp: float = 260.0
    ) -> float:
        """
        计算降雨噪声温度

        Args:
            rain_attenuation: 降雨衰减（dB）
            medium_temp: 有效介质温度（K）

        Returns:
            降雨噪声温度（K）
        """
        return medium_temp * (1 - 1 / (10 ** (rain_attenuation / 10)))

    def get_atmospheric_parameters(
        self,
        availability: float = 99.9
    ) -> Dict[str, float]:
        """
        获取大气参数

        Args:
            availability: 系统可用度（%）

        Returns:
            大气参数字典
        """
        p = 100 - availability  # 转换为不可用性百分比

        # 计算各种大气参数
        hs = itur.topographic_altitude(self.lat, self.lon)
        T = itur.surface_mean_temperature(self.lat, self.lon)
        P = itur.standard_pressure(hs)  # 参数是高度，不是纬度
        rho_p = itur.surface_water_vapour_density(self.lat, self.lon, p, hs)

        R001 = itur.models.itu837.rainfall_rate(self.lat, self.lon, p)
        h_rain = itur.models.itu839.rain_height(self.lat, self.lon)
        R_prob = itur.models.itu618.rain_attenuation_probability(
            self.lat, self.lon, self.elevation, self.station_height
        )

        # 转换温度单位：ITU-Rpy 返回 K，转换为 °C
        T_celsius = (float(T.value) - 273.15) if hasattr(T, 'value') else (T - 273.15)

        return {
            'elevation_km': float(hs.value),
            'surface_temp_C': T_celsius,
            'pressure_hPa': float(P.value),
            'water_vapor_density_g_m3': float(rho_p.value),
            'rain_rate_mm_h': float(R001.value),
            'rain_height_km': float(h_rain.value),
            'rain_attenuation_probability_pct': float(R_prob.value),
        }

    def calculate_attenuation_curve(
        self,
        availability_range: list,
        component: str = 'total'
    ) -> Dict[float, float]:
        """
        计算衰减随概率变化的曲线

        Args:
            availability_range: 可用度列表，如 [99.9, 99.5, 99.0]
            component: 衰减分量 ('total', 'rain', 'gas', 'cloud', 'scintillation')

        Returns:
            {availability: attenuation} 字典
        """
        results = {}

        for avail in availability_range:
            if component == 'total':
                att, _ = self.calculate_atmospheric_attenuation(avail, False)
            elif component == 'rain':
                att = self.calculate_rain_attenuation(avail)
            elif component == 'gas':
                att = self.calculate_gas_attenuation(avail)
            elif component == 'cloud':
                att = self.calculate_cloud_attenuation(avail)
            elif component == 'scintillation':
                att = self.calculate_scintillation_attenuation(avail)
            else:
                raise ValueError(f"Unknown component: {component}")

            results[avail] = att

        return results


def calculate_rain_attenuation_iturpy(
    lat: float,
    lon: float,
    satellite_lon: float,
    frequency: float,
    polarization: str,
    antenna_diameter: float,
    availability: float,
    station_height: float = 0.0,
    elevation: Optional[float] = None
) -> Dict[str, float]:
    """
    便捷函数：使用 ITU-Rpy 计算降雨衰减

    Args:
        lat: 纬度（度）
        lon: 经度（度）
        satellite_lon: 卫星经度（度）
        frequency: 频率（GHz）
        polarization: 极化方式 ('H' 或 'V')
        antenna_diameter: 天线直径（米）
        availability: 系统可用度（%）
        station_height: 地球站海拔（km）
        elevation: 仰角（度），可选

    Returns:
        计算结果字典
    """
    if not ITURPY_AVAILABLE:
        raise ImportError("ITU-Rpy not installed. Run: pip install itur")

    calculator = ITURainCalculator(
        lat=lat,
        lon=lon,
        satellite_lon=satellite_lon,
        frequency=frequency,
        polarization=polarization,
        antenna_diameter=antenna_diameter,
        elevation=elevation,
        station_height=station_height
    )

    # 计算总衰减和各分量
    total_att, contributions = calculator.calculate_atmospheric_attenuation(
        availability, return_contributions=True
    )

    # 计算降雨噪声温度
    rain_noise_temp = calculator.calculate_rain_noise_temp(
        contributions['rain']
    )

    # 获取大气参数
    atmospheric_params = calculator.get_atmospheric_parameters(availability)

    return {
        'rain_attenuation_dB': contributions['rain'],
        'gas_attenuation_dB': contributions['gas'],
        'cloud_attenuation_dB': contributions['cloud'],
        'scintillation_attenuation_dB': contributions['scintillation'],
        'total_attenuation_dB': total_att,
        'rain_noise_temp_K': rain_noise_temp,
        'elevation_km': atmospheric_params['elevation_km'],
        'rain_rate_mm_h': atmospheric_params['rain_rate_mm_h'],
        'rain_height_km': atmospheric_params['rain_height_km'],
        'rain_attenuation_probability_pct': atmospheric_params['rain_attenuation_probability_pct'],
    }
