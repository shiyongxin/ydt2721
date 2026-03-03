"""
单元测试 - 卫星参数计算模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ydt2721.core.satellite import calculate_sfd, calculate_antenna_gain_per_area


def test_calculate_sfd():
    """测试卫星SFD计算"""
    result = calculate_sfd(-84, 5.96, 0)
    assert abs(result - (-89.96)) < 0.01, f"Expected -89.96, got {result}"
    print(f"✅ SFD计算测试通过: {result:.2f} dB(W/m²)")


def test_antenna_gain_per_area():
    """测试天线单位面积增益计算"""
    result = calculate_antenna_gain_per_area(14.25e9)
    assert abs(result - 44.53) < 0.1, f"Expected ~44.53, got {result}"
    print(f"✅ 天线增益计算测试通过: {result:.2f} dB/m²")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
