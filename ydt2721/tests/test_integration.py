"""
集成测试 - 完整计算流程
"""

import pytest
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721 import complete_link_budget
from ydt2721.core.param_manager import ParameterValidator, ParameterManager
from ydt2721.models.dataclass import SatelliteParams, CarrierParams, EarthStationParams
from ydt2721.output import (
    MarkdownReportGenerator,
    ExcelReportGenerator,
    JSONExporter,
)


class TestCompleteWorkflow:
    """测试完整工作流程"""

    def test_full_calculation_workflow(self, tmp_path):
        """测试完整计算流程"""
        # 1. 创建参数对象
        satellite = SatelliteParams(
            longitude=110.5,
            eirp_ss=48.48,
            gt_s=5.96,
            gt_s_ref=0,
            sfd_ref=-84,
            bo_i=6,
            bo_o=3,
            transponder_bw=54000000,
        )

        carrier = CarrierParams(
            info_rate=2000000,
            fec_rate=0.75,
            fec_type='DVB-S2',
            spread_gain=1,
            modulation='QPSK',
            modulation_index=2,
            ebno_threshold=4.5,
            alpha1=1.2,
            alpha2=1.4,
        )

        tx_station = EarthStationParams(
            name='北京',
            longitude=116.45,
            latitude=39.92,
            antenna_diameter=4.5,
            efficiency=0.65,
            frequency=14.25,
            polarization='V',
            feed_loss=1.5,
            antenna_noise_temp=35,
            receiver_noise_temp=75,
        )

        rx_station = EarthStationParams(
            name='乌鲁木齐',
            longitude=87.68,
            latitude=43.77,
            antenna_diameter=1.8,
            efficiency=0.65,
            frequency=12.50,
            polarization='H',
            feed_loss=0.2,
            antenna_noise_temp=35,
            receiver_noise_temp=75,
        )

        # 2. 验证参数
        errors = ParameterValidator.validate_all_params(
            satellite, carrier, tx_station, rx_station, 99.66, 99.66
        )
        assert len(errors) == 0

        # 3. 执行计算
        result = complete_link_budget(
            sat_longitude=satellite.longitude,
            sat_eirp_ss=satellite.eirp_ss,
            sat_gt=satellite.gt_s,
            sat_gt_ref=satellite.gt_s_ref,
            sat_sfd_ref=satellite.sfd_ref,
            sat_bo_i=satellite.bo_i,
            sat_bo_o=satellite.bo_o,
            sat_transponder_bw=satellite.transponder_bw,

            info_rate=carrier.info_rate,
            fec_rate=carrier.fec_rate,
            modulation=carrier.modulation,
            spread_gain=carrier.spread_gain,
            ebno_th=carrier.ebno_threshold,
            alpha1=carrier.alpha1,
            alpha2=carrier.alpha2,

            tx_station_name=tx_station.name,
            tx_lat=tx_station.latitude,
            tx_lon=tx_station.longitude,
            tx_antenna_diameter=tx_station.antenna_diameter,
            tx_efficiency=tx_station.efficiency,
            tx_frequency=tx_station.frequency,
            tx_polarization=tx_station.polarization,
            tx_feed_loss=tx_station.feed_loss,
            tx_loss_at=tx_station.loss_at if hasattr(tx_station, 'loss_at') else 0.5,
            upc_max=tx_station.upc_max_comp if hasattr(tx_station, 'upc_max_comp') else 5.0,

            rx_station_name=rx_station.name,
            rx_lat=rx_station.latitude,
            rx_lon=rx_station.longitude,
            rx_antenna_diameter=rx_station.antenna_diameter,
            rx_efficiency=rx_station.efficiency,
            rx_frequency=rx_station.frequency,
            rx_polarization=rx_station.polarization,
            rx_feed_loss=rx_station.feed_loss,
            rx_loss_ar=rx_station.loss_ar if hasattr(rx_station, 'loss_ar') else 0.5,
            rx_antenna_noise_temp=rx_station.antenna_noise_temp,
            rx_receiver_noise_temp=rx_station.receiver_noise_temp,

            uplink_availability=99.66,
            downlink_availability=99.66,
        )

        # 4. 验证计算结果
        assert result.symbol_rate > 0
        assert result.noise_bandwidth > 0
        assert result.bandwidth_ratio > 0
        assert result.elevation >= 0
        assert result.elevation <= 90

        # 5. 生成所有报告
        output_prefix = tmp_path / "integration_test"

        # Markdown
        md_file = str(output_prefix) + ".md"
        input_params = {
            'satellite': {
                'longitude': satellite.longitude,
                'sat_eirp_ss': satellite.eirp_ss,
                'sat_gt': satellite.gt_s,
                'sat_gt_ref': satellite.gt_s_ref,
                'sat_sfd_ref': satellite.sfd_ref,
                'sat_bo_i': satellite.bo_i,
                'sat_bo_o': satellite.bo_o,
                'sat_transponder_bw': satellite.transponder_bw,
            },
            'carrier': {
                'info_rate': carrier.info_rate,
                'fec_rate': carrier.fec_rate,
                'fec_type': carrier.fec_type,
                'spread_gain': carrier.spread_gain,
                'modulation': carrier.modulation,
                'ebno_th': carrier.ebno_threshold,
                'alpha1': carrier.alpha1,
                'alpha2': carrier.alpha2,
            },
            'tx_station': {
                'station_name': tx_station.name,
                'longitude': tx_station.longitude,
                'latitude': tx_station.latitude,
                'antenna_diameter': tx_station.antenna_diameter,
                'efficiency': tx_station.efficiency,
                'frequency': tx_station.frequency,
                'polarization': tx_station.polarization,
                'feed_loss': tx_station.feed_loss,
                'loss_at': tx_station.loss_at if hasattr(tx_station, 'loss_at') else 0.5,
                'upc_max_comp': tx_station.upc_max_comp if hasattr(tx_station, 'upc_max_comp') else 5.0,
            },
            'rx_station': {
                'station_name': rx_station.name,
                'longitude': rx_station.longitude,
                'latitude': rx_station.latitude,
                'antenna_diameter': rx_station.antenna_diameter,
                'efficiency': rx_station.efficiency,
                'frequency': rx_station.frequency,
                'polarization': rx_station.polarization,
                'feed_loss': rx_station.feed_loss,
                'loss_ar': rx_station.loss_ar if hasattr(rx_station, 'loss_ar') else 0.5,
                'antenna_noise_temp': rx_station.antenna_noise_temp,
                'receiver_noise_temp': rx_station.receiver_noise_temp,
            },
            'system': {
                'uplink_availability': 99.66,
                'downlink_availability': 99.66,
            },
        }

        MarkdownReportGenerator.generate(input_params, result, md_file)
        assert Path(md_file).exists()

        # Excel
        excel_file = str(output_prefix) + ".xlsx"
        ExcelReportGenerator.generate(input_params, result, excel_file)
        assert Path(excel_file).exists()

        # JSON
        json_file = str(output_prefix) + ".json"
        JSONExporter.export(input_params, result, json_file)
        assert Path(json_file).exists()

        # 验证JSON内容
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        assert json_data['metadata']['version'] == '1.0.0'
        assert 'summary' in json_data


class TestTemplateWorkflow:
    """测试模板工作流程"""

    def test_create_save_load_template(self, tmp_path):
        """测试创建、保存、加载模板工作流程"""
        # 1. 创建模板
        template = ParameterManager.create_template('测试工作流')

        # 2. 保存模板
        template_file = tmp_path / "workflow_template.json"
        ParameterManager.save_template(template, str(template_file))
        assert template_file.exists()

        # 3. 加载模板
        loaded_template = ParameterManager.load_template(str(template_file))
        assert loaded_template['name'] == '测试工作流'


class TestEdgeCases:
    """测试边界情况"""

    def test_minimum_margins(self):
        """测试最小余量边界"""
        # 创建一个可能导致余量很小的场景
        result = complete_link_budget(
            sat_longitude=110.5,
            sat_eirp_ss=30,  # 很小的EIRP
            sat_gt=0,
            sat_gt_ref=0,
            sat_sfd_ref=-100,
            sat_bo_i=6,
            sat_bo_o=3,
            sat_transponder_bw=54000000,

            info_rate=10000000,  # 很高的信息速率
            fec_rate=0.5,
            modulation='QPSK',
            spread_gain=1,
            ebno_th=8,
            alpha1=1.2,
            alpha2=1.4,

            tx_station_name='测试站',
            tx_lat=39.92,
            tx_lon=116.45,
            tx_antenna_diameter=1.0,  # 很小的天线
            tx_efficiency=0.5,
            tx_frequency=14.25,
            tx_polarization='V',
            tx_feed_loss=3,
            tx_loss_at=1,
            upc_max=3,

            rx_station_name='接收站',
            rx_lat=39.92,
            rx_lon=116.45,
            rx_antenna_diameter=0.6,  # 很小的天线
            rx_efficiency=0.5,
            rx_frequency=12.50,
            rx_polarization='H',
            rx_feed_loss=1,
            rx_loss_ar=1,
            rx_antenna_noise_temp=100,
            rx_receiver_noise_temp=200,

            uplink_availability=99.9,
            downlink_availability=99.9,
        )

        # 余量应该是负值或接近0
        assert result.clear_sky_margin < 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
