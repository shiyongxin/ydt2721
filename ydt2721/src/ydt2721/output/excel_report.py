"""
M08: Excel格式报告生成器
"""

import pandas as pd
from typing import Dict, Any
from datetime import datetime


class ExcelReportGenerator:
    """Excel格式报告生成器"""

    @staticmethod
    def generate(
        input_params: Dict[str, Any],
        result: Any,
        output_path: str
    ) -> bool:
        """
        生成Excel格式报告

        Args:
            input_params: 输入参数
            result: 计算结果
            output_path: 输出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 基本信息
                ExcelReportGenerator._write_summary_sheet(writer, input_params, result)

                # 输入参数
                ExcelReportGenerator._write_input_sheets(writer, input_params)

                # 计算结果
                ExcelReportGenerator._write_result_sheets(writer, result)

            return True
        except Exception as e:
            print(f"生成Excel报告失败: {e}")
            return False

    @staticmethod
    def _write_summary_sheet(writer, input_params: Dict[str, Any], result: Any):
        """写入汇总表"""
        data = [
            ['计算时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['软件版本', '1.0.0'],
            ['', ''],
            ['主要输出参数', ''],
            ['载波分配带宽', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
            ['载波带宽占用比', f"{result.bandwidth_ratio:.2f}%"],
            ['载波卫星功率占用比', f"{result.clear_sky_power_ratio:.2f}%"],
            ['功放发射功率（晴天）', f"{result.clear_sky_hpa_power:.2f} W"],
            ['功放发射功率（上行降雨）', f"{result.uplink_rain_hpa_power:.2f} W"],
            ['系统余量（晴天）', f"{result.clear_sky_margin:.2f} dB"],
            ['系统余量（上行降雨）', f"{result.uplink_rain_margin:.2f} dB"],
            ['系统余量（下行降雨）', f"{result.downlink_rain_margin:.2f} dB"],
        ]

        df = pd.DataFrame(data, columns=['参数', '数值'])
        df.to_excel(writer, sheet_name='汇总', index=False)

    @staticmethod
    def _write_input_sheets(writer, input_params: Dict[str, Any]):
        """写入输入参数表"""

        # 卫星参数
        satellite = input_params.get('satellite', {})
        df_sat = pd.DataFrame([
            ['卫星经度', f"{satellite.get('longitude', 0)}°"],
            ['饱和EIRP', f"{satellite.get('eirp_ss', 0)} dBW"],
            ['G/T值', f"{satellite.get('gt_s', 0)} dB/K"],
            ['参考点G/T', f"{satellite.get('gt_s_ref', 0)} dB/K"],
            ['参考点SFD', f"{satellite.get('sfd_ref', 0)} dB(W/m²)"],
            ['输入回退', f"{satellite.get('bo_i', 0)} dB"],
            ['输出回退', f"{satellite.get('bo_o', 0)} dB"],
            ['转发器带宽', f"{satellite.get('transponder_bw', 0)/1e6:.2f} MHz"],
        ], columns=['参数', '数值'])
        df_sat.to_excel(writer, sheet_name='卫星参数', index=False)

        # 载波参数
        carrier = input_params.get('carrier', {})
        df_carrier = pd.DataFrame([
            ['信息速率', f"{carrier.get('info_rate', 0)/1e6:.2f} Mbps"],
            ['FEC编码率', f"{carrier.get('fec_rate', 0):.3f}"],
            ['FEC编码方式', carrier.get('fec_type', '-')],
            ['扩频增益', f"{carrier.get('spread_gain', 1)}"],
            ['调制方式', carrier.get('modulation', '-')],
            ['Eb/No门限', f"{carrier.get('ebno_threshold', 0)} dB"],
            ['α₁', f"{carrier.get('alpha1', 1.2)}"],
            ['α₂', f"{carrier.get('alpha2', 1.4)}"],
        ], columns=['参数', '数值'])
        df_carrier.to_excel(writer, sheet_name='载波参数', index=False)

        # 发射站参数
        tx_station = input_params.get('tx_station', {})
        df_tx = pd.DataFrame([
            ['站名', tx_station.get('name', '-')],
            ['经度', f"{tx_station.get('longitude', 0)}°"],
            ['纬度', f"{tx_station.get('latitude', 0)}°"],
            ['天线口径', f"{tx_station.get('antenna_diameter', 0)} m"],
            ['天线效率', f"{tx_station.get('efficiency', 0):.2f}"],
            ['上行频率', f"{tx_station.get('frequency', 0)} GHz"],
            ['极化方式', tx_station.get('polarization', '-')],
            ['馈线损耗', f"{tx_station.get('feed_loss', 0)} dB"],
            ['损耗因子', f"{tx_station.get('loss_at', 0)} dB"],
            ['UPC最大补偿', f"{tx_station.get('upc_max_comp', 0)} dB"],
        ], columns=['参数', '数值'])
        df_tx.to_excel(writer, sheet_name='发射站参数', index=False)

        # 接收站参数
        rx_station = input_params.get('rx_station', {})
        df_rx = pd.DataFrame([
            ['站名', rx_station.get('name', '-')],
            ['经度', f"{rx_station.get('longitude', 0)}°"],
            ['纬度', f"{rx_station.get('latitude', 0)}°"],
            ['天线口径', f"{rx_station.get('antenna_diameter', 0)} m"],
            ['天线效率', f"{rx_station.get('efficiency', 0):.2f}"],
            ['下行频率', f"{rx_station.get('frequency', 0)} GHz"],
            ['极化方式', rx_station.get('polarization', '-')],
            ['馈线损耗', f"{rx_station.get('feed_loss', 0)} dB"],
            ['损耗因子', f"{rx_station.get('loss_ar', 0)} dB"],
            ['天线噪声温度', f"{rx_station.get('antenna_noise_temp', 0)} K"],
            ['接收机噪声温度', f"{rx_station.get('receiver_noise_temp', 0)} K"],
        ], columns=['参数', '数值'])
        df_rx.to_excel(writer, sheet_name='接收站参数', index=False)

        # 系统参数
        system = input_params.get('system', {})
        df_sys = pd.DataFrame([
            ['系统可用度', f"{system.get('availability', 0):.3f}%"],
        ], columns=['参数', '数值'])
        df_sys.to_excel(writer, sheet_name='系统参数', index=False)

    @staticmethod
    def _write_result_sheets(writer, result: Any):
        """写入计算结果表"""

        # 带宽计算
        df_bw = pd.DataFrame([
            ['传输速率', f"{result.transmission_rate/1e6:.2f} Mbps"],
            ['符号速率', f"{result.symbol_rate/1e6:.2f} Msym/s"],
            ['载波噪声带宽', f"{result.noise_bandwidth/1e6:.2f} MHz"],
            ['载波分配带宽', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
            ['带宽占用比', f"{result.bandwidth_ratio:.2f}%"],
        ], columns=['参数', '数值'])
        df_bw.to_excel(writer, sheet_name='带宽计算', index=False)

        # 地球站参数
        df_es = pd.DataFrame([
            ['发射天线增益', f"{result.tx_antenna_gain:.2f} dBi"],
            ['接收天线增益', f"{result.rx_antenna_gain:.2f} dBi"],
            ['接收站G/T', f"{result.rx_gt:.2f} dB/K"],
            ['仰角', f"{result.elevation:.2f}°"],
            ['方位角', f"{result.azimuth:.2f}°"],
        ], columns=['参数', '数值'])
        df_es.to_excel(writer, sheet_name='地球站参数', index=False)

        # 空间损耗
        df_sl = pd.DataFrame([
            ['上行自由空间损耗', f"{result.uplink_loss:.2f} dB"],
            ['下行自由空间损耗', f"{result.downlink_loss:.2f} dB"],
        ], columns=['参数', '数值'])
        df_sl.to_excel(writer, sheet_name='空间损耗', index=False)

        # 晴天链路
        df_clear = pd.DataFrame([
            ['卫星载波EIRP', f"{result.satellite_eirp:.2f} dBW"],
            ['卫星PFD', f"{result.pfd:.2f} dB(W/m²)"],
            ['上行C/N', f"{result.clear_sky_cn_u:.2f} dB"],
            ['下行C/N', f"{result.clear_sky_cn_d:.2f} dB"],
            ['系统C/N', f"{result.clear_sky_cn_t:.2f} dB"],
            ['门限C/N', f"{result.cn_th:.2f} dB"],
            ['系统余量', f"{result.clear_sky_margin:.2f} dB"],
            ['功放发射功率', f"{result.clear_sky_hpa_power:.2f} W"],
            ['功率占用比', f"{result.clear_sky_power_ratio:.2f}%"],
        ], columns=['参数', '数值'])
        df_clear.to_excel(writer, sheet_name='晴天链路', index=False)

        # 上行降雨
        df_uplink_rain = pd.DataFrame([
            ['系统余量', f"{result.uplink_rain_margin:.2f} dB"],
            ['功放发射功率', f"{result.uplink_rain_hpa_power:.2f} W"],
        ], columns=['参数', '数值'])
        df_uplink_rain.to_excel(writer, sheet_name='上行降雨', index=False)

        # 下行降雨
        df_downlink_rain = pd.DataFrame([
            ['系统余量', f"{result.downlink_rain_margin:.2f} dB"],
        ], columns=['参数', '数值'])
        df_downlink_rain.to_excel(writer, sheet_name='下行降雨', index=False)

        # 干扰结果
        df_interference = pd.DataFrame([
            ['互调干扰C/I', f"{result.cn_im:.2f} dB"],
            ['上行邻星干扰C/I', f"{result.cn_u_as:.2f} dB"],
            ['下行邻星干扰C/I', f"{result.cn_d_as:.2f} dB"],
            ['上行交叉极化干扰C/I', f"{result.cn_u_xp:.2f} dB"],
            ['下行交叉极化干扰C/I', f"{result.cn_d_xp:.2f} dB"],
        ], columns=['参数', '数值'])
        df_interference.to_excel(writer, sheet_name='干扰结果', index=False)
