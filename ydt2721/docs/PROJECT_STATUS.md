# YDT 2721 卫星链路计算软件 - 开发完成报告

## 项目概述

根据中华人民共和国通信行业标准 YD/T 2721-2014《地球静止轨道卫星固定业务的链路计算方法》开发的完整链路计算软件。

## 已完成功能

### 核心计算模块（M02-M07）

✅ **M02: 卫星参数计算**
- 卫星SFD计算
- 天线孔径单位面积增益计算

✅ **M03: 载波带宽计算**
- 传输速率计算
- 符号速率计算（支持BPSK/QPSK/8PSK/16QAM）
- 载波噪声带宽和分配带宽计算
- 带宽占用比计算

✅ **M04: 地球站参数计算**
- 天线增益计算
- 仰角/方位角计算
- 地球站与卫星距离计算
- 地球站G/T值计算

✅ **M05: 空间损耗计算**
- 自由空间传播损耗计算
- 降雨衰减计算（简化版，参考YD/T 984）
- 降雨噪声温度计算
- G/T下降计算

✅ **M06: 晴天链路计算**
- 卫星功率分配计算
- 上行/下行C/N计算
- 干扰C/I计算（互调、邻星、交叉极化）
- 系统总C/N计算（功率叠加法）
- 门限C/N和系统余量计算
- 地球站发射参数计算
- 功率占用比计算

✅ **M07: 降雨影响计算**
- 上行降雨影响计算（含UPC补偿）
- 下行降雨影响计算

### 数据结构（Models）

✅ 定义完整的数据结构：
- SatelliteParams（卫星参数）
- CarrierParams（载波参数）
- EarthStationParams（地球站参数）
- InterferenceParams（干扰参数）
- LinkBudgetResult（链路计算结果）
- CalculationInput（完整输入参数）

### 主计算函数

✅ `complete_link_budget()` - 整合所有计算模块的完整链路计算

## 项目结构

```
ydt2721/
├── src/
│   └── ydt2721/
│       ├── __init__.py
│       ├── calculator.py              # 主计算函数
│       ├── constants.py               # 物理常数和默认参数
│       ├── core/                      # 核心计算模块
│       │   ├── __init__.py
│       │   ├── satellite.py           # M02
│       │   ├── carrier.py             # M03
│       │   ├── earth_station.py       # M04
│       │   ├── space_loss.py          # M05
│       │   ├── clear_sky.py           # M06
│       │   └── rain_impact.py         # M07
│       └── models/                    # 数据模型
│           ├── __init__.py
│           └── dataclass.py
├── examples/
│   ├── demo.py                        # 基本使用示例
│   └── test_all.py                    # 完整单元测试
├── tests/
│   ├── __init__.py
│   └── test_satellite.py              # 卫星模块测试
├── docs/
├── README.md
├── pyproject.toml
├── setup.py
└── requirements.txt
```

## 测试结果

### 单元测试（examples/test_all.py）

✅ 所有核心算法单元测试通过：

| 测试项 | 预期值 | 实际值 | 状态 |
|--------|--------|--------|------|
| 下行C/N计算 | 11.7 dB | 11.75 dB | ✅ |
| 上行C/N计算 | 13.7 dB | 13.74 dB | ✅ |
| 系统C/N计算 | 7.58 dB | 7.56 dB | ✅ |
| 门限C/N计算 | 5.47 dB | 5.47 dB | ✅ |
| 系统余量计算 | 2.11 dB | 2.11 dB | ✅ |
| 卫星功率分配 | - | - | ✅ |
| 符号速率 | 1.33 Msym/s | 1.33 Msym/s | ✅ |
| 噪声带宽 | 1.6 MHz | 1.6 MHz | ✅ |
| 带宽占用比 | 3.46% | 3.46% | ✅ |
| 接收仰角 | 34.59° | 34.59° | ✅ |
| 接收方位角 | 148.69° | 148.69° | ✅ |

### 运行测试

```bash
cd ydt2721
python3 examples/test_all.py
```

## 待完成功能

### M01: 参数配置管理模块
⏳ 参数验证和默认值设置
⏳ 参数模板管理

### M08: 结果输出报告模块
⏳ Markdown格式报告生成
⏳ PDF格式报告生成（需选择库）
⏳ Excel格式报告生成
⏳ JSON数据导出

### 其他
⏳ CLI命令行界面
⏳ 完整的单元测试（所有模块）
⏳ 使用文档
⏳ API文档

## 使用示例

```python
from ydt2721 import complete_link_budget

result = complete_link_budget(
    # 卫星参数
    sat_longitude=110.5,
    sat_eirp_ss=48.48,
    sat_gt=5.96,
    sat_gt_ref=0,
    sat_sfd_ref=-84,
    sat_bo_i=6,
    sat_bo_o=3,
    sat_transponder_bw=54000000,

    # 载波参数
    info_rate=2000000,          # 信息速率 2 Mbps
    fec_rate=0.75,              # FEC编码率 3/4
    modulation='QPSK',
    spread_gain=1,
    ebno_th=4.5,
    alpha1=1.2,
    alpha2=1.4,

    # 发射站参数
    tx_station_name='北京',
    tx_lat=39.92,
    tx_lon=116.45,
    tx_antenna_diameter=4.5,
    tx_efficiency=0.65,
    tx_frequency=14.25,
    tx_polarization='V',
    tx_feed_loss=1.5,
    tx_loss_at=0.5,
    upc_max=5.0,

    # 接收站参数
    rx_station_name='乌鲁木齐',
    rx_lat=43.77,
    rx_lon=87.68,
    rx_antenna_diameter=1.8,
    rx_efficiency=0.65,
    rx_frequency=12.50,
    rx_polarization='H',
    rx_feed_loss=0.2,
    rx_loss_ar=0.5,
    rx_antenna_noise_temp=35,
    rx_receiver_noise_temp=75,

    # 系统参数
    availability=99.66,
)

# 查看结果
print(f"符号速率: {result.symbol_rate:.0f} symbol/s")
print(f"系统余量: {result.clear_sky_margin:.2f} dB")
```

## 技术说明

### 重要常数

- 光速 c = 3×10⁸ m/s
- 玻尔兹曼常数 k = -228.6 dB(W/(K·Hz))
- 地球半径 R_E = 6378 km
- 卫星高度 H_E = 35786.6 km
- 地面环境温度 T₀ = 290K
- 有效介质温度 T_m = 260K

### 支持的调制方式

- BPSK（调制指数 n=1）
- QPSK（调制指数 n=2）
- 8PSK（调制指数 n=3）
- 16QAM（调制指数 n=4）

### 支持的极化方式

- V: 垂直极化
- H: 水平极化
- LH: 左旋圆极化
- RH: 右旋圆极化

## 精度和性能

- 计算精度：小数点后2位
- 单次计算时间：< 1秒
- 内存占用：< 200MB

## 参考资料

1. YD/T 2721-2014 地球静止轨道卫星固定业务的链路计算方法
2. YD/T 984 卫星通信链路大气和降雨衰减计算方法
3. ITU-R相关标准

## 版本信息

- **版本号：** 1.0.0
- **开发日期：** 2026-03-03
- **开发者：** 编程新 💻
- **完成度：** ~70%（核心计算模块已完成）

---

**注意：** 完整链路计算的结果取决于具体的场景参数（卫星位置、地球站位置、工作频率等）。建议根据实际应用场景调整参数。
