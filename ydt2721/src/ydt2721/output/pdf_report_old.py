"""
M08: PDF格式报告生成器
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import Dict, Any
from datetime import datetime
import os


class PDFReportGenerator:
    """PDF格式报告生成器"""

    @staticmethod
    def generate(
        input_params: Dict[str, Any],
        result: Any,
        output_path: str
    ) -> bool:
        """
        生成PDF格式报告

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
            story.append(Paragraph("YDT 2721 卫星链路计算报告", styles['Title']))
            story.append(Spacer(1, 0.5*cm))

            # 基本信息
            story.append(Paragraph("一、网络一般信息", styles['Heading1']))
            story.append(PDFReportGenerator._create_header_table(input_params, result, styles))
            story.append(Spacer(1, 0.3*cm))

            # 输入参数
            story.append(Paragraph("二、输入参数汇总", styles['Heading1']))
            story.append(PDFReportGenerator._create_input_params_tables(input_params, styles))
            story.append(Spacer(1, 0.3*cm))

            # 分页
            story.append(PageBreak())

            # 计算结果
            story.append(Paragraph("三、计算结果", styles['Heading1']))
            story.append(PDFReportGenerator._create_result_tables(result, styles))
            story.append(Spacer(1, 0.3*cm))

            # 主要输出参数
            story.append(Paragraph("四、主要输出参数汇总", styles['Heading1']))
            story.append(PDFReportGenerator._create_summary_table(result, styles))
            story.append(Spacer(1, 0.3*cm))

            # 结论与建议
            story.append(Paragraph("五、结论与建议", styles['Heading1']))
            story.append(PDFReportGenerator._create_conclusion(result, styles))

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

        # 添加中文支持（如果系统中有的话）
        chinese_font_loaded = False
        try:
            # 尝试使用系统中的中文字体
            fonts = [
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                '/System/Library/Fonts/Supplemental/PingFang.ttc',  # macOS
                '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # macOS (可能支持中文)
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
                'C:\\Windows\\Fonts\\msyh.ttc',  # Windows
            ]
            for font in fonts:
                if os.path.exists(font):
                    pdfmetrics.registerFont(TTFont('Chinese', font))
                    chinese_font_loaded = True
                    break

            if chinese_font_loaded:
                # 自定义样式
                styles.add(ParagraphStyle(
                    name='ChineseTitle',
                    parent=styles['Heading1'],
                    fontName='Chinese',
                    fontSize=18,
                    spaceAfter=12,
                ))
                styles.add(ParagraphStyle(
                    name='ChineseHeading',
                    parent=styles['Heading2'],
                    fontName='Chinese',
                    fontSize=14,
                    spaceAfter=8,
                ))
                styles.add(ParagraphStyle(
                    name='ChineseNormal',
                    parent=styles['Normal'],
                    fontName='Chinese',
                    fontSize=10,
                ))

                # 使用中文样式
                styles['Title'] = styles['ChineseTitle']
                styles['Heading1'] = styles['ChineseHeading']
                styles['Heading2'] = styles['ChineseHeading']
                styles['Normal'] = styles['ChineseNormal']
        except:
            pass  # 使用默认样式

        return styles

    @staticmethod
    def _create_header_table(input_params: Dict[str, Any], result: Any, styles) -> Table:
        """创建头部表格"""
        satellite = input_params.get('satellite', {})
        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})

        data = [
            ['计算时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['软件版本', '1.0.0'],
            ['卫星经度', f"{satellite.get('longitude', 0)}°"],
            ['发射站', f"{tx_station.get('name', '未知')}"],
            ['接收站', f"{rx_station.get('name', '未知')}"],
        ]

        # 使用默认字体或中文字体
        font_name = styles['Normal'].fontName if 'Chinese' in styles['Normal'].fontName else 'Helvetica'

        table = Table(data, colWidths=[4*cm, 6*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return table

    @staticmethod
    def _get_font_name(styles) -> str:
        """获取字体名称（中文或默认）"""
        return styles['Normal'].fontName if 'Chinese' in styles['Normal'].fontName else 'Helvetica'

    @staticmethod
    def _create_input_params_tables(input_params: Dict[str, Any], styles) -> list:
        """创建输入参数表格列表"""
        tables = []

        # 卫星参数
        tables.append(Paragraph("2.1 卫星参数", styles['Heading2']))
        satellite = input_params.get('satellite', {})
        sat_data = [
            ['参数', '数值'],
            ['卫星经度', f"{satellite.get('longitude', 0)}°"],
            ['饱和EIRP', f"{satellite.get('eirp_ss', 0)} dBW"],
            ['G/T值', f"{satellite.get('gt_s', 0)} dB/K"],
            ['输入回退', f"{satellite.get('bo_i', 0)} dB"],
            ['输出回退', f"{satellite.get('bo_o', 0)} dB"],
        ]
        sat_table = Table(sat_data, colWidths=[5*cm, 5*cm])
        sat_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(sat_table)

        tables.append(Spacer(1, 0.2*cm))

        # 载波参数
        tables.append(Paragraph("2.2 载波参数", styles['Heading2']))
        carrier = input_params.get('carrier', {})
        carrier_data = [
            ['参数', '数值'],
            ['信息速率', f"{carrier.get('info_rate', 0)/1e6:.2f} Mbps"],
            ['FEC编码率', f"{carrier.get('fec_rate', 0):.3f}"],
            ['调制方式', carrier.get('modulation', '-')],
            ['Eb/No门限', f"{carrier.get('ebno_threshold', 0)} dB"],
        ]
        carrier_table = Table(carrier_data, colWidths=[5*cm, 5*cm])
        carrier_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(carrier_table)

        tables.append(Spacer(1, 0.2*cm))

        # 地球站参数
        tables.append(Paragraph("2.3 地球站参数", styles['Heading2']))
        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})
        es_data = [
            ['参数', '发射站', '接收站'],
            ['站名', tx_station.get('name', '-'), rx_station.get('name', '-')],
            ['经度', f"{tx_station.get('longitude', 0)}°", f"{rx_station.get('longitude', 0)}°"],
            ['纬度', f"{tx_station.get('latitude', 0)}°", f"{rx_station.get('latitude', 0)}°"],
            ['天线口径', f"{tx_station.get('antenna_diameter', 0)} m", f"{rx_station.get('antenna_diameter', 0)} m"],
            ['频率', f"{tx_station.get('frequency', 0)} GHz", f"{rx_station.get('frequency', 0)} GHz"],
        ]
        es_table = Table(es_data, colWidths=[4*cm, 3*cm, 3*cm])
        es_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(es_table)

        return tables

    @staticmethod
    def _create_result_tables(result: Any, styles) -> list:
        """创建计算结果表格列表"""
        tables = []

        # 带宽计算
        tables.append(Paragraph("3.1 载波带宽", styles['Heading2']))
        bw_data = [
            ['参数', '数值'],
            ['传输速率', f"{result.transmission_rate/1e6:.2f} Mbps"],
            ['符号速率', f"{result.symbol_rate/1e6:.2f} Msym/s"],
            ['载波噪声带宽', f"{result.noise_bandwidth/1e6:.2f} MHz"],
            ['载波分配带宽', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
            ['带宽占用比', f"{result.bandwidth_ratio:.2f}%"],
        ]
        bw_table = Table(bw_data, colWidths=[5*cm, 5*cm])
        bw_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(bw_table)

        tables.append(Spacer(1, 0.2*cm))

        # 链路性能
        tables.append(Paragraph("3.2 链路性能", styles['Heading2']))
        link_data = [
            ['参数', '晴天', '上行降雨', '下行降雨'],
            ['系统余量 (dB)', f"{result.clear_sky_margin:.2f}", f"{result.uplink_rain_margin:.2f}", f"{result.downlink_rain_margin:.2f}"],
            ['功放功率 (W)', f"{result.clear_sky_hpa_power:.2f}", f"{result.uplink_rain_hpa_power:.2f}", '-'],
        ]
        link_table = Table(link_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        link_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        tables.append(link_table)

        return tables

    @staticmethod
    def _create_summary_table(result: Any, styles) -> Table:
        """创建汇总表格"""
        data = [
            ['主要输出参数', '数值'],
            ['载波分配带宽', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
            ['载波带宽占用比', f"{result.bandwidth_ratio:.2f}%"],
            ['载波卫星功率占用比', f"{result.clear_sky_power_ratio:.2f}%"],
            ['功放发射功率（晴天）', f"{result.clear_sky_hpa_power:.2f} W"],
            ['系统余量（晴天）', f"{result.clear_sky_margin:.2f} dB"],
        ]

        table = Table(data, colWidths=[5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return table

    @staticmethod
    def _create_conclusion(result: Any, styles) -> list:
        """创建结论内容"""
        contents = []

        # 根据余量生成结论
        min_margin = min(result.clear_sky_margin, result.uplink_rain_margin, result.downlink_rain_margin)

        if min_margin >= 3:
            conclusion = "系统余量充足（{:.2f} dB），链路性能良好。".format(min_margin)
        elif min_margin >= 1:
            conclusion = "系统余量基本满足要求（{:.2f} dB）。建议考虑增加天线口径或提高发射功率。".format(min_margin)
        else:
            conclusion = "系统余量不足（{:.2f} dB）。必须增加天线口径、提高发射功率或调整其他参数。".format(min_margin)

        contents.append(Paragraph(conclusion, styles['Normal']))

        return contents
