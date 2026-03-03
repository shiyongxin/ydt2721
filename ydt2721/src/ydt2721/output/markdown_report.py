"""
M08: Markdown格式报告生成器
"""

from typing import Dict, Any
from datetime import datetime


class MarkdownReportGenerator:
    """Markdown格式报告生成器"""

    @staticmethod
    def generate(
        input_params: Dict[str, Any],
        result: Any,
        output_path: str = None
    ) -> str:
        """
        生成Markdown格式报告

        Args:
            input_params: 输入参数
            result: 计算结果
            output_path: 输出文件路径（可选）

        Returns:
            Markdown格式报告内容
        """
        md_lines = []

        # 标题
        md_lines.append("# YDT 2721 卫星链路计算报告\n")

        # 基本信息
        md_lines.append(MarkdownReportGenerator._generate_header(input_params, result))

        # 输入参数
        md_lines.append(MarkdownReportGenerator._generate_input_params(input_params))

        # 计算结果
        md_lines.append(MarkdownReportGenerator._generate_results(result))

        # 主要输出参数
        md_lines.append(MarkdownReportGenerator._generate_summary(result))

        # 结论与建议
        md_lines.append(MarkdownReportGenerator._generate_conclusion(result))

        md_content = '\n'.join(md_lines)

        # 保存到文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

        return md_content

    @staticmethod
    def _generate_header(input_params: Dict[str, Any], result: Any) -> str:
        """生成报告头部"""
        header = ["## 一、网络一般信息\n"]
        header.append(f"- **计算时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        header.append(f"- **软件版本:** 1.0.0\n")

        satellite = input_params.get('satellite', {})
        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})

        header.append(f"- **卫星经度:** {satellite.get('longitude', 0)}°\n")
        header.append(f"- **发射站:** {tx_station.get('name', '未知')}（{tx_station.get('antenna_diameter', 0)}m）\n")
        header.append(f"- **接收站:** {rx_station.get('name', '未知')}（{rx_station.get('antenna_diameter', 0)}m）\n")

        header.append("\n")
        return ''.join(header)

    @staticmethod
    def _generate_input_params(input_params: Dict[str, Any]) -> str:
        """生成输入参数部分"""
        section = ["## 二、输入参数汇总\n"]

        # 卫星参数
        section.append("### 2.1 卫星参数\n")
        satellite = input_params.get('satellite', {})
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['卫星经度', '饱和EIRP', 'G/T值', '参考点G/T', '参考点SFD',
                    '输入回退', '输出回退', '转发器带宽'],
            '数值': [
                f"{satellite.get('longitude', 0)}°",
                f"{satellite.get('eirp_ss', 0)} dBW",
                f"{satellite.get('gt_s', 0)} dB/K",
                f"{satellite.get('gt_s_ref', 0)} dB/K",
                f"{satellite.get('sfd_ref', 0)} dB(W/m²)",
                f"{satellite.get('bo_i', 0)} dB",
                f"{satellite.get('bo_o', 0)} dB",
                f"{satellite.get('transponder_bw', 0)/1e6:.2f} MHz",
            ]
        }))

        # 载波参数
        section.append("### 2.2 载波传输参数\n")
        carrier = input_params.get('carrier', {})
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['信息速率', 'FEC编码率', 'FEC编码方式', '扩频增益',
                    '调制方式', 'Eb/No门限', 'α₁', 'α₂'],
            '数值': [
                f"{carrier.get('info_rate', 0)/1e6:.2f} Mbps",
                f"{carrier.get('fec_rate', 0):.3f}",
                f"{carrier.get('fec_type', '-')}",
                f"{carrier.get('spread_gain', 1)}",
                f"{carrier.get('modulation', '-')}",
                f"{carrier.get('ebno_threshold', 0)} dB",
                f"{carrier.get('alpha1', 1.2)}",
                f"{carrier.get('alpha2', 1.4)}",
            ]
        }))

        # 发射站参数
        section.append("### 2.3 发射地球站参数\n")
        tx_station = input_params.get('tx_station', {})
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['站名', '经度', '纬度', '天线口径', '天线效率',
                    '上行频率', '极化方式', '馈线损耗', '损耗因子', 'UPC最大补偿'],
            '数值': [
                tx_station.get('name', '-'),
                f"{tx_station.get('longitude', 0)}°",
                f"{tx_station.get('latitude', 0)}°",
                f"{tx_station.get('antenna_diameter', 0)} m",
                f"{tx_station.get('efficiency', 0):.2f}",
                f"{tx_station.get('frequency', 0)} GHz",
                tx_station.get('polarization', '-'),
                f"{tx_station.get('feed_loss', 0)} dB",
                f"{tx_station.get('loss_at', 0)} dB",
                f"{tx_station.get('upc_max_comp', 0)} dB",
            ]
        }))

        # 接收站参数
        section.append("### 2.4 接收地球站参数\n")
        rx_station = input_params.get('rx_station', {})
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['站名', '经度', '纬度', '天线口径', '天线效率',
                    '下行频率', '极化方式', '馈线损耗', '损耗因子',
                    '天线噪声温度', '接收机噪声温度'],
            '数值': [
                rx_station.get('name', '-'),
                f"{rx_station.get('longitude', 0)}°",
                f"{rx_station.get('latitude', 0)}°",
                f"{rx_station.get('antenna_diameter', 0)} m",
                f"{rx_station.get('efficiency', 0):.2f}",
                f"{rx_station.get('frequency', 0)} GHz",
                rx_station.get('polarization', '-'),
                f"{rx_station.get('feed_loss', 0)} dB",
                f"{rx_station.get('loss_ar', 0)} dB",
                f"{rx_station.get('antenna_noise_temp', 0)} K",
                f"{rx_station.get('receiver_noise_temp', 0)} K",
            ]
        }))

        # 系统参数
        section.append("### 2.5 系统参数\n")
        system = input_params.get('system', {})
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['系统可用度'],
            '数值': [f"{system.get('availability', 0):.3f}%"],
        }))

        section.append("\n")
        return ''.join(section)

    @staticmethod
    def _generate_results(result: Any) -> str:
        """生成计算结果部分"""
        section = ["## 三、计算结果\n"]

        # 带宽计算
        section.append("### 3.1 载波带宽计算\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['传输速率', '符号速率', '载波噪声带宽', '载波分配带宽', '带宽占用比'],
            '数值': [
                f"{result.transmission_rate/1e6:.2f} Mbps",
                f"{result.symbol_rate/1e6:.2f} Msym/s",
                f"{result.noise_bandwidth/1e6:.2f} MHz",
                f"{result.allocated_bandwidth/1e6:.2f} MHz",
                f"{result.bandwidth_ratio:.2f}%",
            ]
        }))

        # 地球站参数
        section.append("### 3.2 地球站参数计算\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['发射天线增益', '接收天线增益', '接收站G/T', '仰角', '方位角'],
            '数值': [
                f"{result.tx_antenna_gain:.2f} dBi",
                f"{result.rx_antenna_gain:.2f} dBi",
                f"{result.rx_gt:.2f} dB/K",
                f"{result.elevation:.2f}°",
                f"{result.azimuth:.2f}°",
            ]
        }))

        # 空间损耗
        section.append("### 3.3 空间损耗计算\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['上行自由空间损耗', '下行自由空间损耗'],
            '数值': [
                f"{result.uplink_loss:.2f} dB",
                f"{result.downlink_loss:.2f} dB",
            ]
        }))

        # 链路性能
        section.append("### 3.4 链路性能分析\n")

        # 晴天
        section.append("#### 3.4.1 晴天状态\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['上行C/N', '下行C/N', '系统C/N', '门限C/N', '系统余量',
                    '功放发射功率', '功率占用比'],
            '数值': [
                f"{result.clear_sky_cn_u:.2f} dB",
                f"{result.clear_sky_cn_d:.2f} dB",
                f"{result.clear_sky_cn_t:.2f} dB",
                f"{result.cn_th:.2f} dB",
                f"**{result.clear_sky_margin:.2f} dB**",
                f"{result.clear_sky_hpa_power:.2f} W",
                f"{result.clear_sky_power_ratio:.2f}%",
            ]
        }))

        # 上行降雨
        section.append("#### 3.4.2 上行降雨状态\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['系统余量', '功放发射功率'],
            '数值': [
                f"**{result.uplink_rain_margin:.2f} dB**",
                f"{result.uplink_rain_hpa_power:.2f} W",
            ]
        }))

        # 下行降雨
        section.append("#### 3.4.3 下行降雨状态\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['系统余量'],
            '数值': [f"**{result.downlink_rain_margin:.2f} dB**"],
        }))

        section.append("\n")
        return ''.join(section)

    @staticmethod
    def _generate_summary(result: Any) -> str:
        """生成主要输出参数汇总"""
        section = ["## 四、主要输出参数汇总\n"]
        section.append("- 载波分配带宽: **" + f"{result.allocated_bandwidth/1e6:.2f} MHz**\n")
        section.append("- 载波带宽占用比: **" + f"{result.bandwidth_ratio:.2f}%**\n")
        section.append("- 载波卫星功率占用比: **" + f"{result.clear_sky_power_ratio:.2f}%**\n")
        section.append("- 载波所需地球站功放发射功率（晴天）: **" + f"{result.clear_sky_hpa_power:.2f} W**\n")
        section.append("- 载波所需地球站功放发射功率（上行降雨）: **" + f"{result.uplink_rain_hpa_power:.2f} W**\n")
        section.append("- 系统余量（晴天）: **" + f"{result.clear_sky_margin:.2f} dB**\n")
        section.append("- 系统余量（上行降雨）: **" + f"{result.uplink_rain_margin:.2f} dB**\n")
        section.append("- 系统余量（下行降雨）: **" + f"{result.downlink_rain_margin:.2f} dB**\n")
        section.append("\n")
        return ''.join(section)

    @staticmethod
    def _generate_conclusion(result: Any) -> str:
        """生成结论与建议"""
        section = ["## 五、结论与建议\n"]

        # 根据余量自动生成结论
        margins = {
            '晴天': result.clear_sky_margin,
            '上行降雨': result.uplink_rain_margin,
            '下行降雨': result.downlink_rain_margin,
        }

        min_margin = min(margins.values())
        worst_case = [k for k, v in margins.items() if v == min_margin][0]

        section.append("### 5.1 系统性能评估\n")
        section.append(f"- 最坏情况: {worst_case}\n")
        section.append(f"- 最小系统余量: {min_margin:.2f} dB\n")

        if min_margin >= 3:
            section.append("- **结论:** 系统余量充足，链路性能良好 ✅\n")
        elif min_margin >= 1:
            section.append("- **结论:** 系统余量基本满足要求 ⚠️\n")
            section.append("- **建议:** 考虑增加天线口径或提高发射功率\n")
        else:
            section.append("- **结论:** 系统余量不足，链路可靠性不满足要求 ❌\n")
            section.append("- **建议:** 必须增加天线口径、提高发射功率或调整其他参数\n")

        section.append("\n")
        return ''.join(section)

    @staticmethod
    def _format_table(data: Dict[str, list]) -> str:
        """格式化Markdown表格"""
        keys = list(data.keys())
        rows = len(data[keys[0]])

        # 表头
        table = "| " + " | ".join(keys) + " |\n"
        table += "| " + " | ".join(["---"] * len(keys)) + " |\n"

        # 数据行
        for i in range(rows):
            row_values = [data[k][i] for k in keys]
            table += "| " + " | ".join(str(v) for v in row_values) + " |\n"

        table += "\n"
        return table
