# YDT 2721 卫星链路计算程序 - C/N 计算过程分析

## 目录

- [一、上行C/N 和 下行C/N 计算过程](#一上行cn-和-下行cn-计算过程)
  - [1. 晴天C/N计算](#1-晴天cn计算)
  - [2. 降雨情况下的C/N计算](#2-降雨情况下的cn计算)
- [二、系统总C/N计算](#二系统总cn计算)
- [三、余量调整过程](#三余量调整过程)
- [四、完整计算流程总结](#四完整计算流程总结)
- [五、关键文件索引](#五关键文件索引)

---

## 一、上行C/N 和 下行C/N 计算过程

### 1. 晴天C/N计算

#### 上行C/N（晴天）

**公式：**

```
C/N_u = PFD - G_m² + G/T_s - 10×lg(BW_n) - k
```

**参数说明：**

| 参数 | 说明 | 单位 |
|------|------|------|
| PFD | 功率通量密度 | dB(W/m²) |
| G_m² | 天线孔径单位面积增益 | dB/m² |
| G/T_s | 卫星品质因数 | dB/K |
| BW_n | 噪声带宽 | Hz |
| k | 玻尔兹曼常数 | -228.6 dB/K |

**PFD计算：**

```
PFD = SFD - BO_il - (EIRP_ss - BO_o - EIRP_sl)
```

**代码位置：** [`clear_sky.py:42-65`](ydt2721/src/ydt2721/core/clear_sky.py#L42-L65)

```python
def calculate_uplink_cn(pfd: float, gm2: float, gt_s: float,
                         noise_bandwidth: float) -> float:
    """
    计算上行链路C/N

    C/N_u = PFD_s - G_m² + G/T_s - 10 × lg(BW_n) - k
    """
    cn_u = (pfd - gm2 + gt_s -
            10 * math.log10(noise_bandwidth) -
            BOLTZMANN_CONSTANT_DB)
    return cn_u
```

#### 下行C/N（晴天）

**公式：**

```
C/N_d = EIRP_sl - L_d - L_ar + G/T_e - 10×lg(BW_n) - k
```

**参数说明：**

| 参数 | 说明 | 单位 |
|------|------|------|
| EIRP_sl | 卫星载波EIRP | dBW |
| L_d | 下行自由空间损耗 | dB |
| L_ar | 接收站损耗 | dB |
| G/T_e | 地球站品质因数 | dB/K |
| BW_n | 噪声带宽 | Hz |
| k | 玻尔兹曼常数 | -228.6 dB/K |

**代码位置：** [`clear_sky.py:68-92`](ydt2721/src/ydt2721/core/clear_sky.py#L68-L92)

```python
def calculate_downlink_cn(eirp_sl: float, loss_d: float, loss_ar: float,
                           gt_e: float, noise_bandwidth: float) -> float:
    """
    计算下行链路C/N

    C/N_d = EIRP_sl - L_d - L_ar + G/T_e - 10 × lg(BW_n) - k
    """
    cn_d = (eirp_sl - loss_d - loss_ar + gt_e -
            10 * math.log10(noise_bandwidth) -
            BOLTZMANN_CONSTANT_DB)
    return cn_d
```

---

### 2. 降雨情况下的C/N计算

#### 降雨衰减计算

使用 **ITU-Rpy** 库计算完整的降雨衰减模型，包括：

| 分量 | 说明 |
|------|------|
| A_rain | 降雨衰减 |
| A_gas | 气体衰减 |
| A_cloud | 云衰减 |
| A_scintillation | 闪烁衰减 |
| T_rain_noise | 降雨噪声温度 |

**代码位置：** [`itu_rain_wrapper.py:324-390`](ydt2721/src/ydt2721/core/itu_rain_wrapper.py#L324-L390)

```python
def calculate_rain_attenuation_iturpy(
    lat: float, lon: float, satellite_lon: float,
    frequency: float, polarization: str,
    antenna_diameter: float, availability: float,
    station_height: float = 0.0, elevation: Optional[float] = None
) -> Dict[str, float]:
    """
    使用 ITU-Rpy 计算降雨衰减
    """
    calculator = ITURainCalculator(...)
    total_att, contributions = calculator.calculate_atmospheric_attenuation(
        availability, return_contributions=True
    )
    rain_noise_temp = calculator.calculate_rain_noise_temp(contributions['rain'])
    return {
        'rain_attenuation_dB': contributions['rain'],
        'gas_attenuation_dB': contributions['gas'],
        'cloud_attenuation_dB': contributions['cloud'],
        'scintillation_attenuation_dB': contributions['scintillation'],
        'rain_noise_temp_K': rain_noise_temp,
        ...
    }
```

#### 上行降雨C/N（含UPC补偿）

上行降雨时使用 **UPC（上行功率控制）** 进行补偿：

**公式：**

```
# UPC实际补偿量
A_UPC = min(A_pu, A_UPC_max)

# 调整后的卫星载波EIRP
EIRP_sl = EIRP_ss - BO_ol - A_pu + A_UPC

# 调整后的地球站EIRP
EIRP_el = SFD_s - BO_il - G_m² + L_u + L_at + A_UPC
```

**参数说明：**

| 参数 | 说明 |
|------|------|
| A_pu | 上行降雨衰减 |
| A_UPC_max | UPC最大补偿能力 |
| EIRP_ss | 卫星饱和EIRP |
| BO_ol | 输出回退 |
| SFD_s | 卫星饱和通量密度 |
| BO_il | 输入回退 |

**代码位置：** [`rain_impact.py:9-47`](ydt2721/src/ydt2721/core/rain_impact.py#L9-L47)

```python
def calculate_uplink_rain_impact(eirp_ss: float, bo_ol: float,
                                  rain_attenuation: float, upc_max: float,
                                  sfd: float, bo_il: float, gm2: float,
                                  loss_u: float, loss_at: float) -> tuple:
    """
    计算上行降雨影响

    A_UPC = min(A_pu, A_UPC,max)
    EIRP_sl = EIRP_ss - BO_ol - A_pu + A_UPC
    EIRP_el = SFD_s - BO_il - G_m² + L_u + L_at + A_UPC
    """
    upc_compensation = min(rain_attenuation, upc_max)
    eirp_sl = eirp_ss - bo_ol - rain_attenuation + upc_compensation
    eirp_el = sfd - bo_il - gm2 + loss_u + loss_at + upc_compensation
    return upc_compensation, eirp_sl, eirp_el
```

#### 下行降雨C/N

**公式：**

```
C/N_d = EIRP_sl - L_d - L_ar - A_pd + G/T_e - Δ(G/T_e) - 10×lg(BW_n) - k
```

**新增参数：**

| 参数 | 说明 |
|------|------|
| A_pd | 下行降雨衰减 |
| Δ(G/T_e) | G/T下降量（由降雨噪声温度导致） |

**代码位置：** [`rain_impact.py:50-76`](ydt2721/src/ydt2721/core/rain_impact.py#L50-L76)

```python
def calculate_downlink_rain_cn(eirp_sl: float, loss_d: float, loss_ar: float,
                                rain_attenuation: float, gt_e: float,
                                gt_degradation: float, noise_bandwidth: float) -> float:
    """
    计算下行降雨时的下行链路C/N

    C/N_d = EIRP_sl - L_d - L_ar - A_pd + G/T_e - Δ(G/T_e) - 10 × lg(BW_n) - k
    """
    cn_d = (eirp_sl - loss_d - loss_ar - rain_attenuation + gt_e - gt_degradation
            - 10 * math.log10(noise_bandwidth) - BOLTZMANN_CONSTANT_DB)
    return cn_d
```

---

## 二、系统总C/N计算

### 系统C/N（功率叠加）

**公式：**

```
1/(C/N_T) = 1/(C/N_u) + 1/(C/N_d) + 1/(C/I_im) + 1/(C/I_u_as) + 1/(C/I_d_as) + 1/(C/I_u_xp) + 1/(C/I_d_xp)

C/N_T = 10×lg(C/N_T)
```

**干扰分量说明：**

| 分量 | 说明 |
|------|------|
| C/N_u | 上行载噪比 |
| C/N_d | 下行载噪比 |
| C/I_im | 互调干扰载干比 |
| C/I_u_as | 上行邻星干扰载干比 |
| C/I_d_as | 下行邻星干扰载干比 |
| C/I_u_xp | 上行交叉极化干扰载干比 |
| C/I_d_xp | 下行交叉极化干扰载干比 |

**代码位置：** [`clear_sky.py:127-172`](ydt2721/src/ydt2721/core/clear_sky.py#L127-L172)

```python
def calculate_system_cn(cn_u: float, cn_d: float, ci_im: float,
                        ci_u_as: float, ci_d_as: float,
                        ci_u_xp: float, ci_d_xp: float) -> float:
    """
    计算链路系统C/N（功率叠加）

    1/(c/n_T) = Σ 1/(c/n_i)
    C/N_T = 10 × lg(c/n_T)
    """
    # 转换为真数
    cn_u_linear = 10 ** (cn_u / 10)
    cn_d_linear = 10 ** (cn_d / 10)
    ci_im_linear = 10 ** (ci_im / 10)
    # ... 其他分量

    # 计算总载噪比真数
    inv_cn_total = (1 / cn_u_linear + 1 / cn_d_linear +
                    1 / ci_im_linear + 1 / ci_u_as_linear +
                    1 / ci_d_as_linear + 1 / ci_u_xp_linear +
                    1 / ci_d_xp_linear)

    cn_total_linear = 1 / inv_cn_total
    cn_total_db = 10 * math.log10(cn_total_linear)
    return cn_total_db
```

### 系统余量

**公式：**

```
M = C/N_T - C/N_th
```

其中 `C/N_th` 为门限载噪比：

```
C/N_th = E_b/N_o,th + 10×lg(R_b) - 10×lg(BW_n)
```

**代码位置：** [`clear_sky.py:198-215`](ydt2721/src/ydt2721/core/clear_sky.py#L198-L215)

```python
def calculate_margin(cn_system: float, cn_th: float) -> float:
    """
    计算系统余量

    M = C/N_T - C/N_th
    """
    return cn_system - cn_th
```

---

## 三、余量调整过程

当设置了目标余量（target_margin）时，程序通过 **二分查找** 调整卫星EIRP来实现目标余量。

### 核心原理

```
EIRP ↑ → C/N_d ↑ → C/N_T ↑ → margin ↑
EIRP ↓ → C/N_d ↓ → C/N_T ↓ → margin ↓
```

### 余量计算函数

**代码位置：** [`margin_adjuster.py:103-159`](ydt2721/src/ydt2721/core/margin_adjuster.py#L103-L159)

```python
def calculate_margin_for_eirp(eirp_sl: float, ...) -> float:
    """
    给定卫星载波EIRP计算系统余量
    注意: 只调整下行EIRP，上行C/N保持不变
    """
    from .clear_sky import calculate_downlink_cn, calculate_system_cn

    # 计算下行C/N (使用给定的EIRP)
    cn_d = calculate_downlink_cn(eirp_sl, downlink_loss, rx_loss_ar, rx_gt, noise_bw)

    # 系统总C/N (功率叠加)
    cn_t = calculate_system_cn(cn_u, cn_d, ci_im, ci_u_as, ci_d_as, ci_u_xp, ci_d_xp)

    # 余量
    margin = cn_t - cn_th
    return margin
```

### 二分查找算法

**代码位置：** [`margin_adjuster.py:42-100`](ydt2721/src/ydt2721/core/margin_adjuster.py#L42-L100)

```python
def find_eirp_for_target_margin(
    target_margin: float,
    calculate_margin_func: Callable[[float], float],
    eirp_min: float = -10.0,
    eirp_max: float = 60.0,
    tolerance: float = 0.01,
    max_iterations: int = 50
) -> Tuple[float, Dict]:
    """
    通过二分查找找到实现目标余量所需的EIRP
    """
    low = eirp_min
    high = eirp_max

    for i in range(max_iterations):
        mid = (low + high) / 2
        current_margin = calculate_margin_func(mid)

        if abs(current_margin - target_margin) < tolerance:
            return mid, {...}  # 收敛

        # EIRP ↑ → margin ↑
        if current_margin < target_margin:
            low = mid   # 需要更高EIRP
        else:
            high = mid  # 需要更低EIRP

        if high - low < 0.001:  # EIRP精度 0.001 dB
            break

    final_eirp = (low + high) / 2
    return final_eirp, {...}
```

### 调整后的功率计算

**代码位置：** [`calculator.py:526-541`](ydt2721/src/ydt2721/calculator.py#L526-L541)

```python
# EIRP调整量
eirp_adjustment = adjustment['eirp_adjustment']

# 调整后的载波发射功率
adjusted_power_el_dBW = power_el_dBW + eirp_adjustment
adjusted_power_el_W = 10 ** (adjusted_power_el_dBW / 10)

# 调整后的功放功率
adjusted_hpa_power_dBW = adjusted_power_el_dBW + tx_hpa_bo
adjusted_hpa_power_W = 10 ** (adjusted_hpa_power_dBW / 10)

# 调整后的功率占用比
eirp_adjustment_linear = 10 ** (eirp_adjustment / 10)
adjusted_power_ratio = power_ratio * eirp_adjustment_linear
```

---

## 四、完整计算流程总结

```
┌─────────────────────────────────────────────────────────────────┐
│                    YDT 2721 链路计算流程                        │
└─────────────────────────────────────────────────────────────────┘

1. 计算载波参数
   ├── 符号速率 = 传输速率 / 扩频增益 / 调制指数
   ├── 噪声带宽 = 符号速率 × 滚降系数
   └── 占用带宽 = 噪声带宽 × 带宽占用比

2. 计算地球站参数
   ├── 天线增益 G = η × (π×D/λ)²
   ├── 仰角、方位角
   ├── 卫星距离
   └── G/T = G - 10×lg(T_sys)

3. 计算空间损耗
   ├── 上行自由空间损耗 L_u
   └── 下行自由空间损耗 L_d

4. 计算降雨衰减（ITU-Rpy）
   ├── 上行降雨衰减 A_pu
   ├── 下行降雨衰减 A_pd
   ├── 气体衰减 A_gas
   ├── 云衰减 A_cloud
   ├── 闪烁衰减 A_scintillation
   └── 降雨噪声温度 T_rain_noise

5. 卫星功率分配
   ├── EIRP_sl = EIRP_ss - BO_o + 10×lg(带宽占用比)
   ├── PFD = SFD - BO_il - (EIRP_ss - BO_o - EIRP_sl)
   ├── BO_il = SFD - PFD
   └── BO_ol = EIRP_ss - EIRP_sl

6. 晴天链路计算
   ├── 上行C/N = PFD - G_m² + G/T_s - 10×lg(BW_n) - k
   ├── 下行C/N = EIRP_sl - L_d - L_ar + G/T_e - 10×lg(BW_n) - k
   ├── 系统C/N = 功率叠加(1/C/N_u + 1/C/N_d + 1/C/I...)
   └── 余量 = C/N_T - C/N_th

7. 上行降雨计算
   ├── UPC补偿 = min(降雨衰减, UPC_max)
   ├── 地球站EIRP += UPC补偿
   └── 余量调整（考虑UPC是否足够）

8. 下行降雨计算
   ├── 下行C/N = EIRP_sl - L_d - L_ar - A_pd + G/T_e - Δ(G/T_e) - 10×lg(BW_n) - k
   └── 重新计算系统余量

9. 余量调整（如果设置了target_margin）
   ├── 二分查找实现目标余量所需的EIRP
   ├── 调整卫星EIRP
   ├── 重新计算上行/下行C/N和余量
   └── 计算调整后的功率
```

---

## 五、关键文件索引

| 功能 | 文件位置 |
|------|----------|
| 上行C/N计算 | [`clear_sky.py:42-65`](ydt2721/src/ydt2721/core/clear_sky.py#L42-L65) |
| 下行C/N计算 | [`clear_sky.py:68-92`](ydt2721/src/ydt2721/core/clear_sky.py#L68-L92) |
| 系统C/N计算 | [`clear_sky.py:127-172`](ydt2721/src/ydt2721/core/clear_sky.py#L127-L172) |
| 门限C/N计算 | [`clear_sky.py:175-195`](ydt2721/src/ydt2721/core/clear_sky.py#L175-L195) |
| 系统余量计算 | [`clear_sky.py:198-215`](ydt2721/src/ydt2721/core/clear_sky.py#L198-L215) |
| 上行降雨处理 | [`rain_impact.py:9-47`](ydt2721/src/ydt2721/core/rain_impact.py#L9-L47) |
| 下行降雨C/N | [`rain_impact.py:50-76`](ydt2721/src/ydt2721/core/rain_impact.py#L50-L76) |
| 余量调整算法 | [`margin_adjuster.py:9-249`](ydt2721/src/ydt2721/core/margin_adjuster.py#L9-L249) |
| 二分查找EIRP | [`margin_adjuster.py:42-100`](ydt2721/src/ydt2721/core/margin_adjuster.py#L42-L100) |
| ITU-Rpy降雨计算 | [`itu_rain_wrapper.py:324-390`](ydt2721/src/ydt2721/core/itu_rain_wrapper.py#L324-L390) |
| 完整链路预算 | [`calculator.py:152-582`](ydt2721/src/ydt2721/calculator.py#L152-L582) |
| UPC和功率计算 | [`calculator.py:48-119`](ydt2721/src/ydt2721/calculator.py#L48-L119) |

---

## 附录：常量定义

**物理常量** - [`constants.py`](ydt2721/src/ydt2721/core/constants.py)

| 常量 | 值 | 说明 |
|------|-----|------|
| LIGHT_SPEED | 299792458 m/s | 光速 |
| BOLTZMANN_CONSTANT_DB | -228.6 dB/K | 玻尔兹曼常数 |
| MODULATION_INDEX | QPSK=2, 8PSK=3 | 调制指数 |

---

*文档生成时间: 2026-03-24*
*基于YDT 2721卫星链路计算程序源码分析*
