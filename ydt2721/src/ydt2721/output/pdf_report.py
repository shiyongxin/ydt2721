"""
M08: PDF格式报告生成器（支持中文）
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .font_manager import FontManager, setup_chinese_fonts


class PDFReportGenerator:
    """PDF格式报告生成器（支持中文）"""

    @staticmethod
    def _convert_markdown_to_html(text: str) -> str:
        """将Markdown格式转换为ReportLab支持的HTML格式"""
        if not isinstance(text, str):
            return text

        # 直接移除 ** 标记，返回纯文本
        # 加粗效果通过 TableStyle 的字体设置来实现
        text = text.replace('**', '')

        return text

    # 注册中文字体
    @staticmethod
    def _register_chinese_fonts() -> Optional[str]:
        """
        注册中文字体

        使用 FontManager 获取字体路径，支持:
        1. 已下载的开源字体 (Source Han Sans / 思源黑体)
        2. 系统自带的中文字体
        """
        try:
            font_info = FontManager.get_font_path('normal')
            if font_info is None:
                print("⚠️ 未找到可用的中文字体")
                return None

            font_path, subfont_index = font_info

            # 生成字体注册名称
            if subfont_index is not None:
                register_name = f'ChineseFont_Normal_{subfont_index}'
                pdfmetrics.registerFont(TTFont(register_name, font_path, subfontIndex=subfont_index))
            else:
                register_name = 'ChineseFont_Normal'
                pdfmetrics.registerFont(TTFont(register_name, font_path))

            print(f"✅ 已注册中文字体: {Path(font_path).name}")
            return register_name

        except Exception as e:
            print(f"⚠️ 中文字体注册失败: {e}")
            return None

    @staticmethod
    def _register_chinese_fonts_bold() -> Optional[str]:
        """
        注册中文字体（粗体）

        使用 FontManager 获取粗体字体路径
        """
        try:
            font_info = FontManager.get_font_path('bold')
            if font_info is None:
                # 回退到普通字体
                print("⚠️ 未找到粗体中文字体，使用普通字体")
                return PDFReportGenerator.get_chinese_font()

            font_path, subfont_index = font_info

            # 生成字体注册名称
            if subfont_index is not None:
                register_name = f'ChineseFont_Bold_{subfont_index}'
                pdfmetrics.registerFont(TTFont(register_name, font_path, subfontIndex=subfont_index))
            else:
                register_name = 'ChineseFont_Bold'
                pdfmetrics.registerFont(TTFont(register_name, font_path))

            print(f"✅ 已注册中文字体（粗体）: {Path(font_path).name}")
            return register_name

        except Exception as e:
            print(f"⚠️ 中文字体（粗体）注册失败: {e}")
            return PDFReportGenerator.get_chinese_font()


    # 字体名称缓存
    _chinese_font = None
    _chinese_font_bold = None

    @staticmethod
    def get_chinese_font():
        """获取中文字体名称"""
        if PDFReportGenerator._chinese_font is None:
            PDFReportGenerator._chinese_font = PDFReportGenerator._register_chinese_fonts()
        return PDFReportGenerator._chinese_font

    @staticmethod
    def get_chinese_font_bold():
        """获取中文字体粗体名称"""
        if PDFReportGenerator._chinese_font_bold is None:
            PDFReportGenerator._chinese_font_bold = PDFReportGenerator._register_chinese_fonts_bold()
        return PDFReportGenerator._chinese_font_bold

    @staticmethod
    def generate(
        input_params: Dict[str, Any],
        result: Any,
        output_path: str
    ) -> bool:
        """
        生成PDF格式报告（支持中文）

        Args:
            input_params: 输入参数
            result: 计算结果
            output_path: 输出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            # 注册中文字体
            chinese_font = PDFReportGenerator.get_chinese_font()
            chinese_font_bold = PDFReportGenerator.get_chinese_font_bold()

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
            styles = PDFReportGenerator._create_styles(chinese_font)

            # 创建内容列表
            story = []

            # 检查是否支持中文
            use_chinese = chinese_font is not None

            # 标题
            if use_chinese:
                story.append(Paragraph("YDT 2721 卫星链路计算报告", styles['Title']))
            else:
                story.append(Paragraph("YDT 2721 Satellite Link Budget Report", styles['Title']))
            story.append(Spacer(1, 0.5*cm))

            # 基本信息
            if use_chinese:
                story.append(Paragraph("一、网络一般信息", styles['Heading1']))
            else:
                story.append(Paragraph("1. Network General Information", styles['Heading1']))
            story.append(PDFReportGenerator._create_header_table(input_params, result, use_chinese, chinese_font))
            story.append(Spacer(1, 0.3*cm))

            # 输入参数
            if use_chinese:
                story.append(Paragraph("二、输入参数汇总", styles['Heading1']))
            else:
                story.append(Paragraph("2. Input Parameters Summary", styles['Heading1']))
            story.extend(PDFReportGenerator._create_input_params_tables(input_params, use_chinese, chinese_font))
            story.append(Spacer(1, 0.3*cm))

            # 分页
            story.append(PageBreak())

            # 计算结果
            if use_chinese:
                story.append(Paragraph("三、计算结果", styles['Heading1']))
            else:
                story.append(Paragraph("3. Calculation Results", styles['Heading1']))
            story.extend(PDFReportGenerator._create_result_tables(result, input_params, use_chinese, chinese_font, chinese_font_bold))
            story.append(Spacer(1, 0.3*cm))

            # 主要输出参数
            if use_chinese:
                story.append(Paragraph("四、主要输出参数汇总", styles['Heading1']))
            else:
                story.append(Paragraph("4. Main Output Parameters Summary", styles['Heading1']))
            story.append(PDFReportGenerator._create_summary_table(result, use_chinese, chinese_font, chinese_font_bold))
            story.append(Spacer(1, 0.3*cm))

            # 结论与建议
            if use_chinese:
                story.append(Paragraph("五、结论与建议", styles['Heading1']))
            else:
                story.append(Paragraph("5. Conclusion and Recommendations", styles['Heading1']))
            story.extend(PDFReportGenerator._create_conclusion(result, use_chinese, chinese_font, chinese_font_bold))

            # 生成PDF
            doc.build(story)

            return True
        except Exception as e:
            print(f"生成PDF报告失败: {e}")
            return False

    @staticmethod
    def _create_styles(chinese_font=None):
        """创建文档样式（支持中文）"""
        styles = getSampleStyleSheet()

        # 如果有中文字体，修改样式以使用中文字体
        if chinese_font:
            # 修改标题样式
            styles['Title'].fontName = chinese_font
            styles['Title'].fontSize = 18
            styles['Heading1'].fontName = chinese_font
            styles['Heading1'].fontSize = 14
            styles['Heading2'].fontName = chinese_font
            styles['Heading2'].fontSize = 12
            styles['Normal'].fontName = chinese_font
            styles['Normal'].fontSize = 10
        else:
            # 修改标题样式（使用默认字体）
            styles['Title'].fontSize = 18
            styles['Heading1'].fontSize = 14
            styles['Heading2'].fontSize = 12
            styles['Normal'].fontSize = 10

        return styles

    @staticmethod
    def _create_header_table(input_params: Dict[str, Any], result: Any, use_chinese: bool = False, chinese_font: str = None) -> Table:
        """创建头部表格"""
        satellite = input_params.get('satellite', {})
        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})

        if use_chinese:
            data = [
                ['计算时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['软件版本', '1.0.0'],
                ['卫星经度', f"{satellite.get('longitude', 0)}°"],
                ['发射站', f"{tx_station.get('name', 'Unknown')}"],
                ['接收站', f"{rx_station.get('name', 'Unknown')}"],
            ]
        else:
            data = [
                ['Calculation Time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Software Version', '1.0.0'],
                ['Satellite Longitude', f"{satellite.get('longitude', 0)}°"],
                ['Tx Station', f"{tx_station.get('name', 'Unknown')}"],
                ['Rx Station', f"{rx_station.get('name', 'Unknown')}"],
            ]

        table = Table(data, colWidths=[5*cm, 6*cm])

        # 应用字体样式
        if chinese_font:
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
        else:
            table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

        return table

    @staticmethod
    def _create_input_params_tables(input_params: Dict[str, Any], use_chinese: bool = False, chinese_font: str = None) -> list:
        """创建输入参数表格列表（支持中文）"""
        tables = []
        sample_styles = getSampleStyleSheet()

        # 如果有中文字体，创建新的样式
        if chinese_font:
            heading2_style = ParagraphStyle(
                'Heading2_CN',
                parent=sample_styles['Heading2'],
                fontName=chinese_font,
                fontSize=12,
            )
        else:
            heading2_style = sample_styles['Heading2']

        # 卫星参数
        if use_chinese:
            tables.append(Paragraph("2.1 卫星参数", style=heading2_style))
        else:
            tables.append(Paragraph("2.1 Satellite Parameters", style=sample_styles['Heading2']))

        satellite = input_params.get('satellite', {})
        if use_chinese:
            sat_data = [
                ['参数', '数值'],
                ['卫星经度', f"{satellite.get('longitude', 0)}°"],
                ['饱和EIRP', f"{satellite.get('eirp_ss', 0)} dBW"],
                ['G/T值', f"{satellite.get('gt_s', 0)} dB/K"],
                ['输入回退', f"{satellite.get('bo_i', 0)} dB"],
                ['输出回退', f"{satellite.get('bo_o', 0)} dB"],
            ]
        else:
            sat_data = [
                ['Parameter', 'Value'],
                ['Longitude', f"{satellite.get('longitude', 0)}°"],
                ['Saturated EIRP', f"{satellite.get('eirp_ss', 0)} dBW"],
                ['G/T', f"{satellite.get('gt_s', 0)} dB/K"],
                ['Input Back-off', f"{satellite.get('bo_i', 0)} dB"],
                ['Output Back-off', f"{satellite.get('bo_o', 0)} dB"],
            ]
        sat_table = Table(sat_data, colWidths=[5*cm, 5*cm])

        # 应用字体样式
        if chinese_font:
            sat_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
        else:
            sat_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))

        tables.append(sat_table)

        tables.append(Spacer(1, 0.2*cm))

        # 载波参数
        if use_chinese:
            tables.append(Paragraph("2.2 载波参数", style=heading2_style))
        else:
            tables.append(Paragraph("2.2 Carrier Parameters", style=heading2_style))

        carrier = input_params.get('carrier', {})
        if use_chinese:
            carrier_data = [
                ['参数', '数值'],
                ['信息速率', f"{carrier.get('info_rate', 0)/1e6:.2f} Mbps"],
                ['FEC编码率', f"{carrier.get('fec_rate', 0):.3f}"],
                ['调制方式', carrier.get('modulation', '-')],
                ['Eb/No门限', f"{carrier.get('ebno_threshold', 0)} dB"],
            ]
        else:
            carrier_data = [
                ['Parameter', 'Value'],
                ['Info Rate', f"{carrier.get('info_rate', 0)/1e6:.2f} Mbps"],
                ['FEC Rate', f"{carrier.get('fec_rate', 0):.3f}"],
                ['Modulation', carrier.get('modulation', '-')],
                ['Eb/No Threshold', f"{carrier.get('ebno_threshold', 0)} dB"],
            ]
        carrier_table = Table(carrier_data, colWidths=[5*cm, 5*cm])

        # 应用字体样式
        if chinese_font:
            carrier_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
        else:
            carrier_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))

        tables.append(carrier_table)

        tables.append(Spacer(1, 0.2*cm))

        # 地球站参数
        if use_chinese:
            tables.append(Paragraph("2.3 地球站参数", style=heading2_style))
        else:
            tables.append(Paragraph("2.3 Earth Station Parameters", style=heading2_style))

        tx_station = input_params.get('tx_station', {})
        rx_station = input_params.get('rx_station', {})

        if use_chinese:
            es_data = [
                ['参数', '发射站', '接收站'],
                ['站名', tx_station.get('name', '-'), rx_station.get('name', '-')],
                ['经度', f"{tx_station.get('longitude', 0)}°", f"{rx_station.get('longitude', 0)}°"],
                ['纬度', f"{tx_station.get('latitude', 0)}°", f"{rx_station.get('latitude', 0)}°"],
                ['天线口径', f"{tx_station.get('antenna_diameter', 0)} m", f"{rx_station.get('antenna_diameter', 0)} m"],
                ['频率', f"{tx_station.get('frequency', 0)} GHz", f"{rx_station.get('frequency', 0)} GHz"],
            ]
        else:
            es_data = [
                ['Parameter', 'Tx Station', 'Rx Station'],
                ['Station Name', tx_station.get('name', '-'), rx_station.get('name', '-')],
                ['Longitude', f"{tx_station.get('longitude', 0)}°", f"{rx_station.get('longitude', 0)}°"],
                ['Latitude', f"{tx_station.get('latitude', 0)}°", f"{rx_station.get('latitude', 0)}°"],
                ['Antenna Diameter', f"{tx_station.get('antenna_diameter', 0)} m", f"{rx_station.get('antenna_diameter', 0)} m"],
                ['Frequency', f"{tx_station.get('frequency', 0)} GHz", f"{rx_station.get('frequency', 0)} GHz"],
            ]

        es_table = Table(es_data, colWidths=[4*cm, 3*cm, 3*cm])

        # 应用字体样式
        if chinese_font:
            es_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
        else:
            es_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))

        tables.append(es_table)

        return tables

    @staticmethod
    def _create_result_tables(result: Any, input_params: Dict[str, Any] = None, use_chinese: bool = False, chinese_font: str = None, chinese_font_bold: str = None) -> list:
        """创建计算结果表格列表（支持中文）"""
        tables = []
        sample_styles = getSampleStyleSheet()

        # 如果有中文字体，创建新的样式
        if chinese_font:
            heading2_style = ParagraphStyle(
                'Heading2_CN',
                parent=sample_styles['Heading2'],
                fontName=chinese_font,
                fontSize=12,
            )
        else:
            heading2_style = sample_styles['Heading2']

        # 带宽计算
        if use_chinese:
            tables.append(Paragraph("3.1 载波带宽", style=heading2_style))
            bw_data = [
                ['参数', '数值'],
                ['传输速率', f"{result.transmission_rate/1e6:.2f} Mbps"],
                ['符号速率', f"{result.symbol_rate/1e6:.2f} Msym/s"],
                ['载波噪声带宽', f"{result.noise_bandwidth/1e6:.2f} MHz"],
                ['载波分配带宽', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
                ['带宽占用比', f"{result.bandwidth_ratio:.2f}%"],
            ]
        else:
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

        # 应用字体样式
        if chinese_font:
            bw_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
        else:
            bw_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))

        tables.append(bw_table)

        tables.append(Spacer(1, 0.2*cm))

        # 链路性能
        if use_chinese:
            tables.append(Paragraph("3.2 链路性能", style=heading2_style))
            link_data = [
                ['参数', '晴天', '上行降雨', '下行降雨'],
                ['系统余量 (dB)', f"{result.clear_sky_margin:.2f}", f"{result.uplink_rain_margin:.2f}", f"{result.downlink_rain_margin:.2f}"],
                ['功放功率 (W)', f"{result.clear_sky_hpa_power:.2f}", f"{result.uplink_rain_hpa_power:.2f}", '-'],
            ]
        else:
            tables.append(Paragraph("3.2 Link Performance", style=heading2_style))
            link_data = [
                ['Parameter', 'Clear Sky', 'Uplink Rain', 'Downlink Rain'],
                ['Margin (dB)', f"{result.clear_sky_margin:.2f}", f"{result.uplink_rain_margin:.2f}", f"{result.downlink_rain_margin:.2f}"],
                ['HPA Power (W)', f"{result.clear_sky_hpa_power:.2f}", f"{result.uplink_rain_hpa_power:.2f}", '-'],
            ]
        link_table = Table(link_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])

        # 应用字体样式
        if chinese_font:
            link_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
        else:
            link_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))

        tables.append(link_table)

        # 反向计算结果（从可用度计算的UPC余量和功放功率）
        tables.append(Spacer(1, 0.2*cm))
        if use_chinese:
            tables.append(Paragraph("3.3 UPC余量和功放功率计算", style=heading2_style))
            reverse_power_data = [
                ['参数', '数值'],
                ['上行降雨衰减', f"{result.uplink_rain_attenuation:.4f} dB"],
                ['所需UPC余量', f"{result.calculated_upc_margin:.4f} dB"],
                ['晴天功放功率', f"{result.calculated_hpa_power_clear:.4f} W"],
                ['雨天功放功率', f"{result.calculated_hpa_power_rain:.4f} W"],
                ['UPC是否满足', '是' if result.upc_sufficient else '否'],
            ]
        else:
            tables.append(Paragraph("3.3 UPC Margin and HPA Power Calculation", style=heading2_style))
            reverse_power_data = [
                ['Parameter', 'Value'],
                ['Uplink Rain Attenuation', f"{result.uplink_rain_attenuation:.4f} dB"],
                ['Required UPC Margin', f"{result.calculated_upc_margin:.4f} dB"],
                ['HPA Power (Clear Sky)', f"{result.calculated_hpa_power_clear:.4f} W"],
                ['HPA Power (Rain)', f"{result.calculated_hpa_power_rain:.4f} W"],
                ['UPC Sufficient', 'Yes' if result.upc_sufficient else 'No'],
            ]
        reverse_power_table = Table(reverse_power_data, colWidths=[5*cm, 5*cm])

        # 应用字体样式，为特定行设置粗体
        if chinese_font:
            # 中文字体，为第4、5、6行设置粗体（索引3、4、5）
            if chinese_font_bold:
                reverse_power_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTNAME', (0, 3), (1, 3), chinese_font_bold),  # 第4行粗体
                    ('FONTNAME', (0, 4), (1, 4), chinese_font_bold),  # 第5行粗体
                    ('FONTNAME', (0, 5), (1, 5), chinese_font_bold),  # 第6行粗体
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
            else:
                reverse_power_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
        else:
            reverse_power_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))

        tables.append(reverse_power_table)

        # 旧的UPC到可用度反向计算（保留兼容性）
        if input_params and input_params.get('_reverse_calc_result'):
            tables.append(Spacer(1, 0.2*cm))
            if use_chinese:
                tables.append(Paragraph("3.3 链路可用度计算（UPC补偿量到可用度）", style=heading2_style))
            reverse_calc = input_params.get('_reverse_calc_result')
            if use_chinese:
                reverse_data = [
                    ['参数', '数值'],
                    ['预留UPC补偿量', f"{reverse_calc.get('upc_reserved_dB', 0):.2f} dB"],
                    ['可达上行可用度', f"{reverse_calc.get('availability', 0):.4f}%"],
                    ['对应不可用度', f"{reverse_calc.get('unavailability', 0):.4f}%"],
                    ['可补偿降雨衰减', f"{reverse_calc.get('compensable_rain_attenuation_dB', 0):.4f} dB"],
                ]
            else:
                reverse_data = [
                    ['Parameter', 'Value'],
                    ['Reserved UPC Compensation', f"{reverse_calc.get('upc_reserved_dB', 0):.2f} dB"],
                    ['Achievable Uplink Availability', f"{reverse_calc.get('availability', 0):.4f}%"],
                    ['Corresponding Unavailability', f"{reverse_calc.get('unavailability', 0):.4f}%"],
                    ['Compensable Rain Attenuation', f"{reverse_calc.get('compensable_rain_attenuation_dB', 0):.4f} dB"],
                ]
            reverse_table = Table(reverse_data, colWidths=[5*cm, 5*cm])

            # 应用字体样式
            if chinese_font:
                reverse_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
            else:
                reverse_table.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))

            tables.append(reverse_table)

        return tables

    @staticmethod
    def _create_summary_table(result: Any, use_chinese: bool = False, chinese_font: str = None, chinese_font_bold: str = None) -> Table:
        """创建汇总表格（支持中文）"""
        if use_chinese:
            data = [
                ['主要输出参数', '数值'],
                ['载波分配带宽', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
                ['带宽占用比', f"{result.bandwidth_ratio:.2f}%"],
                ['功率占用比', f"{result.clear_sky_power_ratio:.2f}%"],
                ['所需UPC余量', PDFReportGenerator._convert_markdown_to_html(f"**{result.calculated_upc_margin:.2f} dB**")],
                ['晴天功放功率', PDFReportGenerator._convert_markdown_to_html(f"**{result.calculated_hpa_power_clear:.2f} W**")],
                ['雨天功放功率', PDFReportGenerator._convert_markdown_to_html(f"**{result.calculated_hpa_power_rain:.2f} W**")],
                ['晴天系统余量', f"{result.clear_sky_margin:.2f} dB"],
            ]
        else:
            data = [
                ['Main Output Parameter', 'Value'],
                ['Allocated Bandwidth', f"{result.allocated_bandwidth/1e6:.2f} MHz"],
                ['Bandwidth Ratio', f"{result.bandwidth_ratio:.2f}%"],
                ['Power Ratio', f"{result.clear_sky_power_ratio:.2f}%"],
                ['Required UPC Margin', PDFReportGenerator._convert_markdown_to_html(f"**{result.calculated_upc_margin:.2f} dB**")],
                ['HPA Power (Clear Sky)', PDFReportGenerator._convert_markdown_to_html(f"**{result.calculated_hpa_power_clear:.2f} W**")],
                ['HPA Power (Rain)', PDFReportGenerator._convert_markdown_to_html(f"**{result.calculated_hpa_power_rain:.2f} W**")],
                ['System Margin (Clear Sky)', f"{result.clear_sky_margin:.2f} dB"],
            ]

        table = Table(data, colWidths=[5*cm, 5*cm])

        # 应用字体样式，为特定行设置粗体
        if chinese_font:
            # 中文字体，为第5、6、7行设置粗体
            if chinese_font_bold:
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTNAME', (0, 4), (1, 4), chinese_font_bold),  # 第5行粗体
                    ('FONTNAME', (0, 5), (1, 5), chinese_font_bold),  # 第6行粗体
                    ('FONTNAME', (0, 6), (1, 6), chinese_font_bold),  # 第7行粗体
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
            else:
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
        else:
            table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

        return table

    @staticmethod
    def _create_conclusion(result: Any, use_chinese: bool = False, chinese_font: str = None, chinese_font_bold: str = None) -> list:
        """创建结论内容（支持中文）"""
        contents = []

        # 根据余量生成结论
        margins = {
            'clear_sky': result.clear_sky_margin,
            'uplink_rain': result.uplink_rain_margin,
            'downlink_rain': result.downlink_rain_margin,
        }
        min_margin = min(margins.values())
        worst_case = [k for k, v in margins.items() if v == min_margin][0]

        # 评估系统整体性能
        all_positive = all(m >= 0 for m in margins.values())
        excellent = min_margin >= 3
        upc_ok = result.upc_sufficient

        # 最坏情况的中英文映射
        worst_case_mapping = {
            'clear_sky': ('晴天', 'Clear Sky'),
            'uplink_rain': ('上行降雨', 'Uplink Rain'),
            'downlink_rain': ('下行降雨', 'Downlink Rain'),
        }
        worst_case_cn, worst_case_en = worst_case_mapping.get(worst_case, ('未知', 'Unknown'))

        # 系统性能评估
        if use_chinese:
            if excellent and upc_ok:
                conclusion = "系统配置合理，链路性能良好，满足可用度要求。最小余量：{:.2f} dB（{}）。".format(min_margin, worst_case_cn)
            elif all_positive and upc_ok:
                conclusion = "系统可用，但{}余量偏低（{:.2f} dB）。建议优化{}链路性能以提高余量。".format(worst_case_cn, min_margin, worst_case_cn)
            elif all_positive and not upc_ok:
                conclusion = "系统基本可用，但UPC容量不足。所需UPC余量：{:.2f} dB。".format(result.calculated_upc_margin)
            elif not all_positive:
                conclusion = "系统配置需要调整。必须增加UPC余量、功放功率或调整其他参数。"
            else:
                conclusion = "系统配置需要调整。必须增加UPC余量、功放功率或调整其他参数。"

            # UPC和功放功率评估
            upc_conclusion = "UPC余量与功放功率需求："
            if result.upc_sufficient:
                upc_conclusion += "当前配置满足可用度要求。"
            else:
                upc_conclusion += "所需UPC余量为 {:.2f} dB。功放功率需要调整为 {:.2f} W（晴天）和 {:.2f} W（雨天）。".format(
                    result.calculated_upc_margin, result.calculated_hpa_power_clear, result.calculated_hpa_power_rain
                )
        else:
            if excellent and upc_ok:
                conclusion = "System configuration is reasonable, link performance is good, and availability requirements are met. Minimum margin: {:.2f} dB ({}).".format(min_margin, worst_case_en)
            elif all_positive and upc_ok:
                conclusion = "System is operational, but {} margin is low ({:.2f} dB). Consider optimizing {} link performance to increase margin.".format(
                    worst_case_en, min_margin, worst_case_en
                )
            elif all_positive and not upc_ok:
                conclusion = "System is basically available, but UPC capacity is insufficient. Required UPC margin: {:.2f} dB.".format(result.calculated_upc_margin)
            elif not all_positive:
                conclusion = "System configuration needs adjustment. Must increase UPC margin, HPA power, or adjust other parameters."
            else:
                conclusion = "System configuration needs adjustment. Must increase UPC margin, HPA power, or adjust other parameters."

            # UPC and HPA power assessment
            upc_conclusion = "UPC Margin and HPA Power Assessment: "
            if result.upc_sufficient:
                upc_conclusion += "Current configuration meets availability requirements. "
            else:
                upc_conclusion += "Required UPC margin is {:.2f} dB. HPA power needs to be adjusted to {:.2f} W (clear sky) and {:.2f} W (rain). ".format(
                    result.calculated_upc_margin, result.calculated_hpa_power_clear, result.calculated_hpa_power_rain
                )

        # 创建带字体的样式
        if chinese_font:
            normal_style_cn = ParagraphStyle(
                'Normal_CN',
                parent=getSampleStyleSheet()['Normal'],
                fontName=chinese_font,
                fontSize=10,
            )
        else:
            normal_style_cn = getSampleStyleSheet()['Normal']

        contents.append(Paragraph(conclusion, normal_style_cn))
        contents.append(Spacer(1, 0.3*cm))
        contents.append(Paragraph(upc_conclusion, normal_style_cn))

        return contents
