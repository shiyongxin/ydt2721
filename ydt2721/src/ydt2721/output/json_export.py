"""
M08: JSON数据导出
"""

import json
from typing import Dict, Any
from datetime import datetime


class JSONExporter:
    """JSON数据导出器"""

    @staticmethod
    def export(
        input_params: Dict[str, Any],
        result: Any,
        output_path: str,
        pretty: bool = True
    ) -> bool:
        """
        导出JSON格式数据

        Args:
            input_params: 输入参数
            result: 计算结果
            output_path: 输出文件路径
            pretty: 是否格式化输出

        Returns:
            bool: 是否成功
        """
        try:
            # 构建完整的导出数据结构
            export_data = {
                'metadata': {
                    'version': '1.0.0',
                    'timestamp': datetime.now().isoformat(),
                    'standard': 'YD/T 2721-2014',
                },
                'input_parameters': JSONExporter._convert_params_to_dict(input_params),
                'calculation_results': JSONExporter._convert_result_to_dict(result),
                'summary': {
                    'allocated_bandwidth_mhz': round(result.allocated_bandwidth / 1e6, 2),
                    'bandwidth_ratio_percent': round(result.bandwidth_ratio, 2),
                    'power_ratio_percent': round(result.clear_sky_power_ratio, 2),
                    'carrier_transmit_power_clear_sky_w': round(result.clear_sky_power_el_W, 2),
                    'carrier_transmit_power_uplink_rain_w': round(result.uplink_rain_power_el_W, 2),
                    'hpa_saturation_power_w': round(result.calculated_hpa_power_rain_W, 2),
                    'margin_clear_sky_db': round(result.clear_sky_margin, 2),
                    'margin_uplink_rain_db': round(result.uplink_rain_margin, 2),
                    'margin_downlink_rain_db': round(result.downlink_rain_margin, 2),
                },
                'reverse_calculation': {
                    'uplink_rain_attenuation_db': round(result.uplink_rain_attenuation, 4),
                    'required_upc_margin_db': round(result.calculated_upc_margin, 4),
                    'carrier_transmit_power_clear_w': round(result.calculated_power_el_clear_W, 4),
                    'carrier_transmit_power_rain_w': round(result.calculated_power_el_rain_W, 4),
                    'hpa_saturation_power_w': round(result.calculated_hpa_power_rain_W, 4),
                    'upc_sufficient': result.upc_sufficient,
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, f, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False

    @staticmethod
    def _convert_params_to_dict(params: Dict[str, Any]) -> Dict[str, Any]:
        """将参数转换为字典"""
        result = {
            'satellite': params.get('satellite', {}),
            'carrier': params.get('carrier', {}),
            'tx_station': params.get('tx_station', {}),
            'rx_station': params.get('rx_station', {}),
            'system': params.get('system', {}),
        }
        # Include reverse calculation result if available
        if '_reverse_calc_result' in params:
            result['_reverse_calc_result'] = params['_reverse_calc_result']
        return result

    @staticmethod
    def _convert_result_to_dict(result: Any) -> Dict[str, Any]:
        """将计算结果转换为字典"""
        return {
            'bandwidth': {
                'transmission_rate_bps': round(result.transmission_rate, 2),
                'symbol_rate_bps': round(result.symbol_rate, 2),
                'noise_bandwidth_hz': round(result.noise_bandwidth, 2),
                'allocated_bandwidth_hz': round(result.allocated_bandwidth, 2),
                'bandwidth_ratio_percent': round(result.bandwidth_ratio, 2),
            },
            'earth_station': {
                'tx_antenna_gain_dbi': round(result.tx_antenna_gain, 2),
                'rx_antenna_gain_dbi': round(result.rx_antenna_gain, 2),
                'rx_gt_db_k': round(result.rx_gt, 2),
                'elevation_deg': round(result.elevation, 2),
                'azimuth_deg': round(result.azimuth, 2),
            },
            'space_loss': {
                'uplink_loss_db': round(result.uplink_loss, 2),
                'downlink_loss_db': round(result.downlink_loss, 2),
            },
            'clear_sky': {
                'satellite_eirp_dbw': round(result.satellite_eirp, 2),
                'pfd_dbw_m2': round(result.pfd, 2),
                'uplink_cn_db': round(result.clear_sky_cn_u, 2),
                'downlink_cn_db': round(result.clear_sky_cn_d, 2),
                'system_cn_db': round(result.clear_sky_cn_t, 2),
                'threshold_cn_db': round(result.cn_th, 2),
                'margin_db': round(result.clear_sky_margin, 2),
                'carrier_transmit_power_w': round(result.clear_sky_power_el_W, 2),
                'hpa_saturation_power_w': round(result.clear_sky_hpa_power_W, 2),
                'power_ratio_percent': round(result.clear_sky_power_ratio, 2),
            },
            'uplink_rain': {
                'margin_db': round(result.uplink_rain_margin, 2),
                'carrier_transmit_power_w': round(result.uplink_rain_power_el_W, 2),
                'hpa_saturation_power_w': round(result.uplink_rain_hpa_power_W, 2),
            },
            'downlink_rain': {
                'margin_db': round(result.downlink_rain_margin, 2),
            },
            'interference': {
                'im_ci_db': round(result.cn_im, 2),
                'u_as_ci_db': round(result.cn_u_as, 2),
                'd_as_ci_db': round(result.cn_d_as, 2),
                'u_xp_ci_db': round(result.cn_u_xp, 2),
                'd_xp_ci_db': round(result.cn_d_xp, 2),
            },
            'reverse_calculation': {
                'uplink_rain_attenuation_db': round(result.uplink_rain_attenuation, 4),
                'required_upc_margin_db': round(result.calculated_upc_margin, 4),
                'carrier_transmit_power_clear_w': round(result.calculated_power_el_clear_W, 4),
                'carrier_transmit_power_rain_w': round(result.calculated_power_el_rain_W, 4),
                'hpa_saturation_power_w': round(result.calculated_hpa_power_rain_W, 4),
                'upc_sufficient': result.upc_sufficient,
            },
        }

    @staticmethod
    def import_template(filepath: str) -> Dict[str, Any]:
        """
        从JSON文件导入参数模板

        Args:
            filepath: JSON文件路径

        Returns:
            参数字典
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
