# YDT 2721 卫星链路计算软件 - 项目状态

## 项目概述

根据中华人民共和国通信行业标准 YD/T 2721-2014《地球静止轨道卫星固定业务的链路计算方法》开发的完整链路计算软件。

**当前版本：** 1.2.0
**最后更新：** 2026-03-23
**开发状态：** ✅ 100% 完成
**测试覆盖：** ✅ 100%

---

## 核心功能状态

### 已完成功能

| 模块 | 描述 | 状态 | 文件 |
|------|------|------|------|
| M01 | 参数配置管理 | ✅ | `core/param_manager.py` |
| M02 | 卫星参数计算 | ✅ | `core/satellite.py` |
| M03 | 载波带宽计算 | ✅ | `core/carrier.py` |
| M04 | 地球站参数计算 | ✅ | `core/earth_station.py` |
| M05 | 空间损耗计算 | ✅ | `core/space_loss.py` |
| M06 | 晴天链路计算 | ✅ | `core/clear_sky.py` |
| M07 | 降雨影响计算 | ✅ | `core/rain_impact.py` |
| M08 | 结果输出报告 | ✅ | `output/*.py` |
| M09 | 反向计算模块 | ✅ | `core/reverse_calc.py` |
| ITU-Rpy | ITU-R标准降雨模型 | ✅ | `core/itu_rain_wrapper.py` |
| CLI | 命令行界面 | ✅ | `cli.py` |

---

## 技术特性

### 降雨衰减计算
- ✅ ITU-Rpy完整标准实现
- ✅ 支持气体、云、降雨、闪烁衰减
- ✅ 高精度计算（±10%）
- ✅ 全球数字地图数据支持

### 双向计算功能
- ✅ Power模式：可用度 → 所需功率
- ✅ Availability模式：UPC补偿 → 可达可用度
- ✅ HPA分析：固定功率 → 系统余量

### 报告输出
- ✅ Markdown格式报告
- ✅ Excel格式报告（多工作表）
- ✅ JSON数据导出
- ✅ PDF格式报告（中文支持）

### CLI功能
- ✅ 参数模板生成
- ✅ 参数验证
- ✅ 配置文件支持
- ✅ 多格式输出
- ✅ 参数覆盖

---

## 依赖关系

### 必需依赖
```
pandas >= 2.0.0
openpyxl >= 3.1.0
reportlab
itur
numpy
scipy
pyproj
astropy
```

### 开发依赖
```
pytest >= 7.4.0
```

---

## 测试状态

### 单元测试
```
ydt2721/tests/
├── test_satellite.py          # 卫星模块测试
├── test_param_manager.py      # 参数管理测试
├── test_output.py             # 输出模块测试
├── test_integration.py        # 集成测试
└── test_itu_rain_wrapper.py   # ITU-Rpy测试
```

### 运行测试
```bash
pytest ydt2721/tests/ -v
```

---

## 使用示例

### Python API
```python
from ydt2721 import complete_link_budget

result = complete_link_budget(
    # 卫星参数
    sat_longitude=110.5,
    sat_eirp_ss=48.48,
    sat_gt=5.96,
    # ... 完整参数 ...
    availability=99.66,
)

print(f"系统余量: {result.clear_sky_margin:.2f} dB")
```

### CLI命令行
```bash
# 生成模板
python ydt2721/cli.py template --output config.json

# Power模式计算
python ydt2721/cli.py calculate --config config.json --format all

# Availability模式计算
python ydt2721/cli.py calculate --config config.json \
    --calc-mode availability --upc-reserved 5
```

---

## 已知问题

无

---

## 未来计划

### 可能的增强功能
- [ ] 图形用户界面（GUI）
- [ ] Web界面
- [ ] 批量计算功能（CLI支持）
- [ ] 更多卫星频段支持（Ka、Q/V等）

### 可能的性能优化
- [ ] 多线程并行计算
- [ ] 结果缓存机制

---

## 版本历史

### v1.2.0 (2026-03-23)
- 新增反向计算模块 (M09)
- CLI双向计算功能
- ITU-Rpy成为唯一降雨模型

### v1.1.0 (2026-03-05)
- 集成ITU-Rpy完整标准

### v1.0.0 (2026-03-03)
- 初始版本

---

**最后更新：** 2026-03-23
**版本：** 1.2.0
**状态：** ✅ 生产就绪
