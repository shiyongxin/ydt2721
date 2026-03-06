"""
单元测试 - 输出模块（M08）
"""

import pytest
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721 import complete_link_budget
from ydt2721.output import (
    MarkdownReportGenerator,
    ExcelReportGenerator,
    JSONExporter,
)


@pytest.fixture
def sample_input_params():
    """示例输入参数"""
    return {
        'satellite': {
            'longitude': 110.5,
            'sat_eirp_ss': 48.48,
            'sat_gt': 5.96,
            'sat_gt_ref': 0,
            'sat_sfd_ref': -84,
            'sat_bo_i': 6,
            'sat_bo_o': 3,
            'sat_transponder_bw': 54000000,
        },
        'carrier': {
            'info_rate': 2000000,
            'fec_rate': 0.75,
            'fec_type': 'DVB-S2',
            'spread_gain': 1,
            'modulation': 'QPSK',
            'ebno_th': 4.5,
            'alpha1': 1.2,
            'alpha2': 1.4,
        },
        'tx_station': {
            'station_name': '北京',
            'longitude': 116.45,
            'latitude': 39.92,
            'antenna_diameter': 4.5,
            'efficiency': 0.65,
            'frequency': 14.25,
            'polarization': 'V',
            'feed_loss': 1.5,
            'loss_at': 0.5,
            'upc_max_comp': 5.0,
        },
        'rx_station': {
            'station_name': '乌鲁木齐',
            'longitude': 87.68,
            'latitude': 43.77,
            'antenna_diameter': 1.8,
            'efficiency': 0.65,
            'frequency': 12.50,
            'polarization': 'H',
            'feed_loss': 0.2,
            'loss_ar': 0.5,
            'antenna_noise_temp': 35,
            'receiver_noise_temp': 75,
        },
        'system': {
            'uplink_availability': 99.66,
            'downlink_availability': 99.66,
        },
    }


@pytest.fixture
def sample_result(sample_input_params):
    """示例计算结果"""
    params = sample_input_params

    result = complete_link_budget(
        sat_longitude=params['satellite']['longitude'],
        sat_eirp_ss=params['satellite']['sat_eirp_ss'],
        sat_gt=params['satellite']['sat_gt'],
        sat_gt_ref=params['satellite']['sat_gt_ref'],
        sat_sfd_ref=params['satellite']['sat_sfd_ref'],
        sat_bo_i=params['satellite']['sat_bo_i'],
        sat_bo_o=params['satellite']['sat_bo_o'],
        sat_transponder_bw=params['satellite']['sat_transponder_bw'],

        info_rate=params['carrier']['info_rate'],
        fec_rate=params['carrier']['fec_rate'],
        modulation=params['carrier']['modulation'],
        spread_gain=params['carrier']['spread_gain'],
        ebno_th=params['carrier']['ebno_th'],
        alpha1=params['carrier']['alpha1'],
        alpha2=params['carrier']['alpha2'],

        tx_station_name=params['tx_station']['station_name'],
        tx_lat=params['tx_station']['latitude'],
        tx_lon=params['tx_station']['longitude'],
        tx_antenna_diameter=params['tx_station']['antenna_diameter'],
        tx_efficiency=params['tx_station']['efficiency'],
        tx_frequency=params['tx_station']['frequency'],
        tx_polarization=params['tx_station']['polarization'],
        tx_feed_loss=params['tx_station']['feed_loss'],
        tx_loss_at=params['tx_station']['loss_at'],
        upc_max=params['tx_station']['upc_max_comp'],

        rx_station_name=params['rx_station']['station_name'],
        rx_lat=params['rx_station']['latitude'],
        rx_lon=params['rx_station']['longitude'],
        rx_antenna_diameter=params['rx_station']['antenna_diameter'],
        rx_efficiency=params['rx_station']['efficiency'],
        rx_frequency=params['rx_station']['frequency'],
        rx_polarization=params['rx_station']['polarization'],
        rx_feed_loss=params['rx_station']['feed_loss'],
        rx_loss_ar=params['rx_station']['loss_ar'],
        rx_antenna_noise_temp=params['rx_station']['antenna_noise_temp'],
        rx_receiver_noise_temp=params['rx_station']['receiver_noise_temp'],

        uplink_availability=params['system']['uplink_availability'],
        downlink_availability=params['system']['downlink_availability'],
    )

    return result


class TestMarkdownReportGenerator:
    """测试Markdown报告生成器"""

    def test_generate_content(self, sample_input_params, sample_result):
        """测试生成Markdown内容"""
        content = MarkdownReportGenerator.generate(
            sample_input_params,
            sample_result,
            output_path=None
        )

        assert '# YDT 2721 卫星链路计算报告' in content
        assert '## 二、输入参数汇总' in content
        assert '## 三、计算结果' in content
        assert '## 四、主要输出参数汇总' in content
        assert '## 五、结论与建议' in content

    def test_generate_file(self, sample_input_params, sample_result, tmp_path):
        """测试生成Markdown文件"""
        output_file = tmp_path / "test_report.md"

        content = MarkdownReportGenerator.generate(
            sample_input_params,
            sample_result,
            output_path=str(output_file)
        )

        assert output_file.exists()
        assert '# YDT 2721 卫星链路计算报告' in content


class TestExcelReportGenerator:
    """测试Excel报告生成器"""

    def test_generate_excel(self, sample_input_params, sample_result, tmp_path):
        """测试生成Excel文件"""
        output_file = tmp_path / "test_report.xlsx"

        success = ExcelReportGenerator.generate(
            sample_input_params,
            sample_result,
            str(output_file)
        )

        assert success
        assert output_file.exists()


class TestJSONExporter:
    """测试JSON导出器"""

    def test_export_json(self, sample_input_params, sample_result, tmp_path):
        """测试导出JSON文件"""
        output_file = tmp_path / "test_report.json"

        success = JSONExporter.export(
            sample_input_params,
            sample_result,
            str(output_file)
        )

        assert success
        assert output_file.exists()

        # 验证JSON结构
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'input_parameters' in data
        assert 'calculation_results' in data
        assert 'summary' in data

        # 验证metadata
        assert data['metadata']['version'] == '1.0.0'
        assert data['metadata']['standard'] == 'YD/T 2721-2014'

        # 验证summary
        assert 'allocated_bandwidth_mhz' in data['summary']
        assert 'margin_clear_sky_db' in data['summary']

    def test_import_template(self, tmp_path):
        """测试导入JSON模板"""
        # 创建测试模板
        template = {
            'name': '测试模板',
            'satellite': {'longitude': 110.5},
            'carrier': {'modulation': 'QPSK'},
        }

        template_file = tmp_path / "template.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f)

        # 导入
        imported = JSONExporter.import_template(str(template_file))

        assert imported['name'] == '测试模板'
        assert imported['satellite']['longitude'] == 110.5


class TestReportIntegration:
    """测试报告生成集成"""

    def test_generate_all_formats(self, sample_input_params, sample_result, tmp_path):
        """测试生成所有格式的报告"""
        output_prefix = tmp_path / "test_report"

        # Markdown
        md_file = str(output_prefix) + ".md"
        MarkdownReportGenerator.generate(sample_input_params, sample_result, md_file)
        assert Path(md_file).exists()

        # Excel
        excel_file = str(output_prefix) + ".xlsx"
        ExcelReportGenerator.generate(sample_input_params, sample_result, excel_file)
        assert Path(excel_file).exists()

        # JSON
        json_file = str(output_prefix) + ".json"
        JSONExporter.export(sample_input_params, sample_result, json_file)
        assert Path(json_file).exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
