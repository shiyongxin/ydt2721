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

        # 反向计算结果（如果有）
        reverse_calc = input_params.get('_reverse_calc_result')
        if reverse_calc:
            md_lines.append(MarkdownReportGenerator._generate_reverse_calculation(reverse_calc))

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
            '参数': ['上行链路可用度', '下行链路可用度'],
            '数值': [
                f"{system.get('uplink_availability', 0):.3f}%",
                f"{system.get('downlink_availability', 0):.3f}%",
            ],
        }))

        section.append("\n")
        return ''.join(section)

    @staticmethod
    def _generate_results(result: Any) -> str:
        """生成计算结果部分"""
        section = ["## 三、计算结果\n"]

        # 反向计算结果（从可用度计算的UPC余量和功放功率）
        section.append("### 3.1 功放功率与UPC余量计算结果\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['上行降雨衰减', '所需UPC余量', '晴天功放功率', '雨天功放功率', 'UPC是否满足'],
            '数值': [
                f"{result.uplink_rain_attenuation:.4f} dB",
                f"**{result.calculated_upc_margin:.4f} dB**",
                f"{result.calculated_hpa_power_clear:.4f} W",
                f"{result.calculated_hpa_power_rain:.4f} W",
                "✅ 满足" if result.upc_sufficient else "❌ 不满足 (需要调整UPC或功放)",
            ]
        }))

        # 带宽计算
        section.append("### 3.2 载波带宽计算\n")
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
        section.append("### 3.3 地球站参数计算\n")
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
        section.append("### 3.4 空间损耗计算\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['上行自由空间损耗', '下行自由空间损耗'],
            '数值': [
                f"{result.uplink_loss:.2f} dB",
                f"{result.downlink_loss:.2f} dB",
            ]
        }))

        # 链路性能
        section.append("### 3.5 链路性能分析\n")

        # 晴天
        section.append("#### 3.5.1 晴天状态\n")
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
        section.append("#### 3.5.2 上行降雨状态\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['系统余量', '功放发射功率'],
            '数值': [
                f"**{result.uplink_rain_margin:.2f} dB**",
                f"{result.uplink_rain_hpa_power:.2f} W",
            ]
        }))

        # 下行降雨
        section.append("#### 3.5.3 下行降雨状态\n")
        section.append(MarkdownReportGenerator._format_table({
            '参数': ['系统余量'],
            '数值': [f"**{result.downlink_rain_margin:.2f} dB**"],
        }))

        section.append("\n")
        return ''.join(section)

    @staticmethod
    def _generate_reverse_calculation(reverse_calc: Dict[str, Any]) -> str:
        """生成反向计算结果部分"""
        section = ["### 3.5 反向计算结果（根据UPC补偿量计算可用度）\n"]

        section.append(MarkdownReportGenerator._format_table({
            '参数': ['预留UPC补偿量', '可达上行可用度', '对应不可用度', '可补偿降雨衰减'],
            '数值': [
                f"{reverse_calc.get('upc_reserved_dB', 0):.2f} dB",
                f"**{reverse_calc.get('availability', 0):.4f}%**",
                f"{reverse_calc.get('unavailability', 0):.4f}%",
                f"{reverse_calc.get('compensable_rain_attenuation_dB', 0):.4f} dB",
            ]
        }))

        # 详细信息
        details = reverse_calc.get('details', {})
        if details:
            section.append("#### 计算详情\n")
            section.append(f"- 计算的降雨衰减: {details.get('rain_attenuation_dB', 0):.4f} dB\n")
            section.append(f"- 目标降雨衰减: {details.get('target_rain_attenuation_dB', 0):.4f} dB\n")
            section.append(f"- 计算误差: {details.get('error_dB', 0):.6f} dB\n")

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
        section.append("- 系统余量（晴天C/N）: **" + f"{result.clear_sky_margin:.2f} dB**\n")
        section.append("- 系统余量（上行降雨C/N）: **" + f"{result.uplink_rain_margin:.2f} dB**\n")
        section.append("- 系统余量（下行降雨C/N）: **" + f"{result.downlink_rain_margin:.2f} dB**\n")
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

        # UPC和功放功率评估
        section.append("\n### 5.2 UPC余量与功放功率需求\n")
        section.append(f"- 上行降雨衰减: {result.uplink_rain_attenuation:.4f} dB\n")
        section.append(f"- **所需UPC余量: {result.calculated_upc_margin:.4f} dB**\n")
        section.append(f"- **晴天功放功率: {result.calculated_hpa_power_clear:.4f} W**\n")
        section.append(f"- **雨天功放功率: {result.calculated_hpa_power_rain:.4f} W**\n")

        if result.upc_sufficient:
            section.append("- **UPC评估:** 当前配置可满足可用度要求 ✅\n")
        else:
            section.append("- **UPC评估:** 需要调整配置以满足可用度要求 ⚠️\n")
            section.append(f"- **建议:** 将UPC余量调整为至少 {result.calculated_upc_margin:.2f} dB\n")
            section.append(f"- **建议:** 雨天功放功率需要至少 {result.calculated_hpa_power_rain:.4f} W\n")

        section.append("\n### 5.3 总体结论\n")

        # 评估系统整体性能
        # 如果所有余量都是正值，说明系统可用
        all_positive = all(m >= 0 for m in margins.values())
        # 如果最小余量>=3，系统性能良好
        excellent = min_margin >= 3
        # 如果UPC不满足，需要调整
        upc_ok = result.upc_sufficient

        if excellent and upc_ok:
            section.append("- **结论:** 系统配置合理，链路性能良好，满足可用度要求 ✅\n")
        elif all_positive and upc_ok:
            section.append(f"- **结论:** 系统可用，但{worst_case}余量偏低({min_margin:.2f} dB) ⚠️\n")
            section.append(f"- **建议:** 可考虑优化{worst_case}链路性能以提高系统余量\n")
        elif all_positive and not upc_ok:
            section.append("- **结论:** 系统基本可用，但UPC能力不足 ⚠️\n")
            section.append(f"- **建议:** 将UPC余量调整为至少 {result.calculated_upc_margin:.2f} dB\n")
        elif not all_positive:
            section.append("- **结论:** 系统配置需要调整 ❌\n")
            section.append("- **建议:** 必须增加UPC余量、功放功率或调整其他参数\n")
        else:
            section.append("- **结论:** 系统配置需要调整 ❌\n")
            section.append("- **建议:** 必须增加UPC余量、功放功率或调整其他参数\n")

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
