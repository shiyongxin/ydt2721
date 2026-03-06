"""
M08: PDF格式报告生成器（简化版，使用默认字体）
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from typing import Dict, Any
from datetime import datetime


class PDFReportGenerator:
    """PDF格式报告生成器"""

    @staticmethod
    def generate(
        input_params: Dict[str, Any],
        result: Any,
        output_path: str
    ) -> bool:
        """
        生成PDF格式报告（英文版本，避免中文字体问题）

        Args:
            input_params: 输入参数
            result: 计算结果
            output_path: 输出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 创建样式
            styles = PDFReportGenerator._create_styles()

            # 创建内容列表
            story = []

            # 标题
            story.append(Paragraph("YDT 2721 Satellite Link Budget Report", styles['Title']))
            story.append(Spacer(1, 0.5*cm))

            # 基本信息
            story.append(Paragraph("1. Network General Information", styles['Heading1']))
            story.append(PDFReportGenerator._create_header_table(input_params, result))
            story.append(Spacer(1, 0.3*cm))

            # 输入参数
            story.append(Paragraph("2. Input Parameters Summary", styles['Heading1']))
            story.extend(PDFReportGenerator._create_input_params_tables(input_params))
            story.append(Spacer(1, 0.3*cm))

            # 分页
            story.append(PageBreak())

            # 计算结果
            story.append(Paragraph("3. Calculation Results", styles['Heading1']))
            story.extend(PDFReportGenerator._create_result_tables(result, input_params))
            story.append(Spacer(1, 0.3*cm))

            # 主要输出参数
            story.append(Paragraph("4. Main Output Parameters Summary", styles['Heading1']))
            story.append(PDFReportGenerator._create_summary_table(result))
            story.append(Spacer(1, 0.3*cm))

            # 结论与建议
            story.append(Paragraph("5. Conclusion and Recommendations", styles['Heading1']))
            story.extend(PDFReportGenerator._create_conclusion(result))

            # 生成PDF
            doc.build(story)

            return True
        except Exception as e:
            print(f"生成PDF报告失败: {e}")
            return False

    @staticmethod
    def _create_styles():
        """创建文档样式"""
        styles = getSampleStyleSheet()
        # 修改标题样式
        styles['Title'].fontSize = 18
        styles['Heading1'].fontSize = 14
        styles['Heading2'].fontSize = 12
        styles['Normal'].fontSize = 10
        return styles

    @staticmethod
    def _create_header_table(input_params: Dict[str, Any], result: Any) -> Table:
        """创建头部表格"""
        satellite = input_params.get('satellite', {})
        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})

        data = [
            ['Calculation Time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Software Version', '1.0.0'],
            ['Satellite Longitude', f"{satellite.get('longitude', 0)}°"],
            ['Tx Station', f"{tx_station.get('name', 'Unknown')}"],
            ['Rx Station', f"{rx_station.get('name', 'Unknown')}"],
        ]

        table = Table(data, colWidths=[5*cm, 6*cm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return table

    @staticmethod
    def _create_input_params_tables(input_params: Dict[str, Any]) -> list:
        """创建输入参数表格列表"""
        tables = []
        sample_styles = getSampleStyleSheet()

        # 卫星参数
        tables.append(Paragraph("2.1 Satellite Parameters", style=sample_styles['Heading2']))
        satellite = input_params.get('satellite', {})
        sat_data = [
            ['Parameter', 'Value'],
            ['Longitude', f"{satellite.get('longitude', 0)}°"],
            ['Saturated EIRP', f"{satellite.get('eirp_ss', 0)} dBW"],
            ['G/T', f"{satellite.get('gt_s', 0)} dB/K"],
            ['Input Back-off', f"{satellite.get('bo_i', 0)} dB"],
            ['Output Back-off', f"{satellite.get('bo_o', 0)} dB"],
        ]
        sat_table = Table(sat_data, colWidths=[5*cm, 5*cm])
        sat_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(sat_table)

        tables.append(Spacer(1, 0.2*cm))

        # 载波参数
        tables.append(Paragraph("2.2 Carrier Parameters", style=sample_styles['Heading2']))
        carrier = input_params.get('carrier', {})
        carrier_data = [
            ['Parameter', 'Value'],
            ['Info Rate', f"{carrier.get('info_rate', 0)/1e6:.2f} Mbps"],
            ['FEC Rate', f"{carrier.get('fec_rate', 0):.3f}"],
            ['Modulation', carrier.get('modulation', '-')],
            ['Eb/No Threshold', f"{carrier.get('ebno_threshold', 0)} dB"],
        ]
        carrier_table = Table(carrier_data, colWidths=[5*cm, 5*cm])
        carrier_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(carrier_table)

        tables.append(Spacer(1, 0.2*cm))

        # 地球站参数
        tables.append(Paragraph("2.3 Earth Station Parameters", style=sample_styles['Heading2']))
        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})
        es_data = [
            ['Parameter', 'Tx Station', 'Rx Station'],
            ['Station Name', tx_station.get('name', '-'), rx_station.get('name', '-')],
            ['Longitude', f"{tx_station.get('longitude', 0)}°", f"{rx_station.get('longitude', 0)}°"],
            ['Latitude', f"{tx_station.get('latitude', 0)}°", f"{rx_station.get('latitude', 0)}°"],
            ['Antenna Diameter', f"{tx_station.get('antenna_diameter', 0)} m", f"{rx_station.get('antenna_diameter', 0)} m"],
            ['Frequency', f"{tx_station.get('frequency', 0)} GHz", f"{rx_station.get('frequency', 0)} GHz"],
        ]
        es_table = Table(es_data, colWidths=[4*cm, 3*cm, 3*cm])
        es_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(es_table)

        return tables

    @staticmethod
    def _create_result_tables(result: Any, input_params: Dict[str, Any] = None) -> list:
        """创建计算结果表格列表"""
        tables = []
        sample_styles = getSampleStyleSheet()

        # 带宽计算
        tables.append(Paragraph("3.1 Carrier Bandwidth", style=sample_styles['Heading2']))
        bw_data = [
            ['Parameter', 'Value'],
            ['Transmission Rate', f"{result.transmission_rate/1e6:.2f} Mbps"],
            ['Symbol Rate', f"{result.symbol_rate/1e6:.2f} Msym/s"],
            ['Noise Bandwidth', f"{result.noise_bandwidth/1e6:.2f} MHz"],
            ['Allocated Bandwidth', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
            ['Bandwidth Ratio', f"{result.bandwidth_ratio:.2f}%"],
        ]
        bw_table = Table(bw_data, colWidths=[5*cm, 5*cm])
        bw_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(bw_table)

        tables.append(Spacer(1, 0.2*cm))

        # 链路性能
        tables.append(Paragraph("3.2 Link Performance", style=sample_styles['Heading2']))
        link_data = [
            ['Parameter', 'Clear Sky', 'Uplink Rain', 'Downlink Rain'],
            ['Margin (dB)', f"{result.clear_sky_margin:.2f}", f"{result.uplink_rain_margin:.2f}", f"{result.downlink_rain_margin:.2f}"],
            ['HPA Power (W)', f"{result.clear_sky_hpa_power:.2f}", f"{result.uplink_rain_hpa_power:.2f}", '-'],
        ]
        link_table = Table(link_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        link_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(link_table)

        # 反向计算结果（从可用度计算的UPC余量和功放功率）
        tables.append(Spacer(1, 0.2*cm))
        tables.append(Paragraph("3.3 UPC Margin and HPA Power Calculation", style=sample_styles['Heading2']))
        reverse_power_data = [
            ['Parameter', 'Value'],
            ['Uplink Rain Attenuation', f"{result.uplink_rain_attenuation:.4f} dB"],
            ['Required UPC Margin', f"**{result.calculated_upc_margin:.4f} dB**"],
            ['HPA Power (Clear Sky)', f"**{result.calculated_hpa_power_clear:.4f} W**"],
            ['HPA Power (Rain)', f"**{result.calculated_hpa_power_rain:.4f} W**"],
            ['UPC Sufficient', 'Yes' if result.upc_sufficient else 'No'],
        ]
        reverse_power_table = Table(reverse_power_data, colWidths=[5*cm, 5*cm])
        reverse_power_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(reverse_power_table)

        # 旧的UPC到可用度反向计算（保留兼容性）
        if input_params and input_params.get('_reverse_calc_result'):
            tables.append(Spacer(1, 0.2*cm))
            tables.append(Paragraph("3.3 Reverse Calculation (UPC to Availability)", style=sample_styles['Heading2']))
            reverse_calc = input_params.get('_reverse_calc_result')
            reverse_data = [
                ['Parameter', 'Value'],
                ['Reserved UPC Compensation', f"{reverse_calc.get('upc_reserved_dB', 0):.2f} dB"],
                ['Achievable Uplink Availability', f"{reverse_calc.get('availability', 0):.4f}%"],
                ['Corresponding Unavailability', f"{reverse_calc.get('unavailability', 0):.4f}%"],
                ['Compensable Rain Attenuation', f"{reverse_calc.get('compensable_rain_attenuation_dB', 0):.4f} dB"],
            ]
            reverse_table = Table(reverse_data, colWidths=[5*cm, 5*cm])
            reverse_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
            tables.append(reverse_table)

        return tables

    @staticmethod
    def _create_summary_table(result: Any) -> Table:
        """创建汇总表格"""
        data = [
            ['Main Output Parameter', 'Value'],
            ['Allocated Bandwidth', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
            ['Bandwidth Ratio', f"{result.bandwidth_ratio:.2f}%"],
            ['Power Ratio', f"{result.clear_sky_power_ratio:.2f}%"],
            ['Required UPC Margin', f"**{result.calculated_upc_margin:.2f} dB**"],
            ['HPA Power (Clear Sky)', f"**{result.calculated_hpa_power_clear:.2f} W**"],
            ['HPA Power (Rain)', f"**{result.calculated_hpa_power_rain:.2f} W**"],
            ['System Margin (Clear Sky)', f"{result.clear_sky_margin:.2f} dB"],
        ]

        table = Table(data, colWidths=[5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return table

    @staticmethod
    def _create_conclusion(result: Any) -> list:
        """创建结论内容"""
        contents = []

        # 根据余量生成结论
        min_margin = min(result.clear_sky_margin, result.uplink_rain_margin, result.downlink_rain_margin)

        # 系统性能评估
        if min_margin >= 3:
            conclusion = "System margin is sufficient ({:.2f} dB), link performance is good.".format(min_margin)
        elif min_margin >= 1:
            conclusion = "System margin basically meets requirements ({:.2f} dB). Consider increasing antenna diameter or transmission power.".format(min_margin)
        else:
            conclusion = "System margin is insufficient ({:.2f} dB). Must increase antenna diameter, improve transmission power, or adjust other parameters.".format(min_margin)

        contents.append(Paragraph(conclusion, getSampleStyleSheet()['Normal']))
        contents.append(Spacer(1, 0.3*cm))

        # UPC和功放功率评估
        upc_conclusion = "UPC Margin and HPA Power Assessment: "
        if result.upc_sufficient:
            upc_conclusion += "Current configuration meets availability requirements. "
        else:
            upc_conclusion += "Required UPC margin is {:.2f} dB. HPA power needs to be adjusted to {:.2f} W (clear sky) and {:.2f} W (rain). ".format(
                result.calculated_upc_margin, result.calculated_hpa_power_clear, result.calculated_hpa_power_rain
            )

        contents.append(Paragraph(upc_conclusion, getSampleStyleSheet()['Normal']))

        return contents
