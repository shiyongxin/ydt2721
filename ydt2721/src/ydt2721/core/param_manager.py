"""
M01: 参数配置管理模块
"""

import math
from typing import Dict, Any, Optional, List
from ..models.dataclass import (
    SatelliteParams,
    CarrierParams,
    EarthStationParams,
    InterferenceParams,
)


class ParameterValidator:
    """参数验证器"""

    # 参数范围定义
    RANGES = {
        # 经纬度
        'longitude': (-180, 180),
        'latitude': (-90, 90),

        # 天线参数
        'antenna_diameter': (0.1, 50),  # 米
        'efficiency': (0.1, 1.0),

        # 频率（GHz）
        'frequency': (1, 40),

        # 损耗（dB）
        'feed_loss': (0, 10),
        'loss_at': (0, 10),
        'loss_ar': (0, 10),

        # 噪声温度（K）
        'noise_temp': (0, 500),

        # 编码率
        'fec_rate': (0.001, 1.0),

        # 扩频增益
        'spread_gain': (1, 1000),

        # Eb/No门限
        'ebno_threshold': (0, 30),

        # 系统可用度
        'uplink_availability': (90, 99.999),
        'downlink_availability': (90, 99.999),

        # 卫星参数
        'sat_eirp_ss': (30, 70),
        'sat_gt': (-10, 20),
        'sat_bo_i': (0, 15),
        'sat_bo_o': (0, 15),
        'sat_sfd_ref': (-120, -60),

        # 转发器带宽
        'transponder_bw': (1e6, 200e6),
    }

    @classmethod
    def validate_range(cls, name: str, value: float,
                       min_val: Optional[float] = None,
                       max_val: Optional[float] = None) -> bool:
        """
        验证参数范围

        Args:
            name: 参数名称
            value: 参数值
            min_val: 最小值（可选）
            max_val: 最大值（可选）

        Returns:
            bool: 是否有效

        Raises:
            ValueError: 参数超出范围
        """
        # 使用预定义范围
        if name in cls.RANGES:
            min_val, max_val = cls.RANGES[name]

        if min_val is not None and value < min_val:
            raise ValueError(f"{name} ({value}) 小于最小值 {min_val}")

        if max_val is not None and value > max_val:
            raise ValueError(f"{name} ({value}) 大于最大值 {max_val}")

        return True

    @classmethod
    def validate_modulation(cls, modulation: str) -> bool:
        """验证调制方式"""
        valid_modulations = ['BPSK', 'QPSK', '8PSK', '16QAM']
        modulation = modulation.upper()
        if modulation not in valid_modulations:
            raise ValueError(f"无效的调制方式: {modulation}，支持: {valid_modulations}")
        return True

    @classmethod
    def validate_polarization(cls, polarization: str) -> bool:
        """验证极化方式"""
        valid_polarizations = ['V', 'H', 'LH', 'RH']
        if polarization.upper() not in valid_polarizations:
            raise ValueError(f"无效的极化方式: {polarization}，支持: {valid_polarizations}")
        return True

    @classmethod
    def validate_fec_rate(cls, fec_rate: float) -> bool:
        """验证FEC编码率"""
        # 常见的FEC编码率
        common_rates = [1/2, 2/3, 3/4, 5/6, 7/8]
        # 允许一定的误差
        for rate in common_rates:
            if abs(fec_rate - rate) < 0.01:
                return True
        # 如果不是常见值，也允许，但要警告
        if 0 < fec_rate <= 1:
            return True
        raise ValueError(f"FEC编码率必须在 0-1 之间: {fec_rate}")

    @classmethod
    def validate_satellite_params(cls, params: SatelliteParams) -> List[str]:
        """验证卫星参数"""
        errors = []

        try:
            cls.validate_range('longitude', params.longitude)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('sat_eirp_ss', params.eirp_ss)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('sat_gt', params.gt_s)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('sat_sfd_ref', params.sfd_ref)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('sat_bo_i', params.bo_i)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('sat_bo_o', params.bo_o)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('transponder_bw', params.transponder_bw)
        except ValueError as e:
            errors.append(str(e))

        return errors

    @classmethod
    def validate_carrier_params(cls, params: CarrierParams) -> List[str]:
        """验证载波参数"""
        errors = []

        try:
            cls.validate_range('info_rate', params.info_rate, min_val=100, max_val=1e9)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_fec_rate(params.fec_rate)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_modulation(params.modulation)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('spread_gain', params.spread_gain)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('ebno_threshold', params.ebno_threshold)
        except ValueError as e:
            errors.append(str(e))

        return errors

    @classmethod
    def validate_earth_station_params(cls, params: EarthStationParams) -> List[str]:
        """验证地球站参数"""
        errors = []

        try:
            cls.validate_range('longitude', params.longitude)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('latitude', params.latitude)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('antenna_diameter', params.antenna_diameter)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('efficiency', params.efficiency)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('frequency', params.frequency)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_polarization(params.polarization)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('feed_loss', params.feed_loss)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('noise_temp', params.antenna_noise_temp)
        except ValueError as e:
            errors.append(str(e))

        try:
            cls.validate_range('noise_temp', params.receiver_noise_temp)
        except ValueError as e:
            errors.append(str(e))

        return errors

    @classmethod
    def validate_all_params(
        cls,
        satellite: SatelliteParams,
        carrier: CarrierParams,
        tx_station: EarthStationParams,
        rx_station: EarthStationParams,
        uplink_availability: float,
        downlink_availability: float
    ) -> List[str]:
        """验证所有参数"""
        all_errors = []

        all_errors.extend(cls.validate_satellite_params(satellite))
        all_errors.extend(cls.validate_carrier_params(carrier))
        all_errors.extend(cls.validate_earth_station_params(tx_station))
        all_errors.extend(cls.validate_earth_station_params(rx_station))

        try:
            cls.validate_range('uplink_availability', uplink_availability)
        except ValueError as e:
            all_errors.append(str(e))

        try:
            cls.validate_range('downlink_availability', downlink_availability)
        except ValueError as e:
            all_errors.append(str(e))

        return all_errors


class ParameterManager:
    """参数管理器 - 处理默认值和模板"""

    # 默认参数值
    DEFAULTS = {
        'satellite': {
            'adj_sat_longitude': None,
        },
        'carrier': {
            'spread_gain': 1,
            'alpha1': 1.2,
            'alpha2': 1.4,
        },
        'tx_station': {
            'efficiency': 0.65,
            'feed_loss': 1.5,
            'loss_at': 0.5,
            'upc_max_comp': 5.0,
        },
        'rx_station': {
            'efficiency': 0.65,
            'feed_loss': 0.2,
            'loss_ar': 0.5,
            'antenna_noise_temp': 35,
            'receiver_noise_temp': 75,
        },
        'system': {
            'uplink_availability': 99.9,
            'downlink_availability': 99.9,
            'target_margin': 0.0,  # 目标系统余量 (dB), 0表示不启用
        },
    }

    @classmethod
    def apply_defaults(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """应用默认值"""
        result = params.copy()

        for category, defaults in cls.DEFAULTS.items():
            for key, default_value in defaults.items():
                if key not in result or result[key] is None:
                    result[key] = default_value

        return result

    @classmethod
    def create_template(cls, name: str) -> Dict[str, Any]:
        """创建参数模板"""
        return {
            'name': name,
            'satellite': cls.DEFAULTS['satellite'].copy(),
            'carrier': cls.DEFAULTS['carrier'].copy(),
            'tx_station': cls.DEFAULTS['tx_station'].copy(),
            'rx_station': cls.DEFAULTS['rx_station'].copy(),
            'system': cls.DEFAULTS['system'].copy(),
        }

    @classmethod
    def save_template(cls, template: Dict[str, Any], filepath: str):
        """保存参数模板到JSON文件"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_template(cls, filepath: str) -> Dict[str, Any]:
        """从JSON文件加载参数模板"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
