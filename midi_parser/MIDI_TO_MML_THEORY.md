# MIDI 1.0 技术参考 — midi_parser 开发用

> 整理自 MIDI 1.0 详细规范 (MMA/AMEI)

---

## 1. SMF（标准 MIDI 文件）结构

```text
[MThd] 头部块
  - Format:  0=单轨, 1=多轨同步, 2=多轨异步
  - Tracks:  MTrk 块数量
  - Division: 每四分音符的 tick 数（PPQN，通常 480）

[MTrk] 轨道块（×N）
  - 由 [delta-time (VLQ)] + [事件] 序列组成
  - delta-time = 距上一事件的 tick 数（0 = 同时发生）
```

### Delta-Time（可变长度编码 VLQ）

```text
值          编码
0x00        → 0x00
0x7F        → 0x7F
0x80        → 0x81, 0x00
0x2000      → 0xC0, 0x00
0x3FFF      → 0xFF, 0x7F
0x100000    → 0xC0, 0x80, 0x00
```

---

## 2. 通道语音消息

| 状态字节 | 消息类型         | 数据 1           | 数据 2           |
|----------|-----------------|-----------------|-----------------|
| `0x8n`   | Note Off（关音符）| 音符号 (0-127)  | 力度 (0-127)    |
| `0x9n`   | Note On（开音符） | 音符号 (0-127)  | 力度 (0-127)，0=关 |
| `0xAn`   | 复音触后         | 音符号 (0-127)  | 压力 (0-127)    |
| `0xBn`   | 控制变更 (CC)    | CC# (0-127)     | 值 (0-127)      |
| `0xCn`   | 音色变更         | 音色号 (0-127)  | —               |
| `0xDn`   | 通道触后         | 压力 (0-127)    | —               |
| `0xEn`   | 弯音轮           | LSB (0-127)     | MSB (0-127)     |

`n` = MIDI 通道 (0-15)。弯音中心值 = 0x2000 (8192)。

### MIDI 音符号 → 音名

```text
音符  0  = C-1   （最低）
音符 60  = C4    （中央 C）
音符 69  = A4    （440 Hz 标准音）
音符 127 = G9    （最高）

公式: 八度 = (note // 12) - 1, 音高 = note % 12
音名: C C# D D# E F F# G G# A A# B
索引: 0 1  2 3  4 5 6  7 8  9 10 11
```

---

## 3. 控制变更 (CC) — 完整列表

### 连续控制器 (0-31 MSB, 32-63 LSB)

| CC# | 名称             | PMD MML 映射          |
|-----|------------------|-----------------------|
| 0   | 音色组选择 MSB    | —                     |
| 1   | 调制轮            | `M` LFO（见下方策略）  |
| 2   | 呼吸控制器        | —                     |
| 4   | 脚踏控制器        | —                     |
| 5   | 滑音时间          | `{}` 滑音速度参考      |
| 6   | 数据输入 MSB      | —                     |
| **7**   | **通道音量**  | **`V` (0-127 直接映射)** |
| 8   | 平衡              | —                     |
| **10**  | **声像 (Pan)** | **`p`（见映射表）**    |
| **11**  | **expression** | **`V`（按比例缩放）**  |
| 12  | 效果控制 1        | —                     |
| 13  | 效果控制 2        | —                     |

### Pan CC#10 → PMD `p` 映射

```text
MIDI Pan 0-127:
  < 64    → p2  (左声道)
  = 64    → p3  (居中)
  > 64    → p1  (右声道)
  
PMD p 值: 0=无, 1=右, 2=左, 3=居中
```

### CC#1 调制轮 → PMD `M` LFO 映射

```text
MIDI CC#1 (Modulation Wheel): 0-127
  0     → M0,0,0,0  (LFO 关闭)
  1-127 → M0,<speed>,<depth>,<depth>

算法:
  depth = cc1_value / 4     (0-31，FNUM 单位)
  speed = 4                 (固定速度，适合通用 vibrato)
  
只在 CC#1 值变化时输出 M 命令。
CC#1=0 时输出 M0,0,0,0 关闭 LFO。
```

### 开关控制器 (64-69)

| CC# | 名称          | PMD MML 映射 |
|-----|---------------|-------------|
| 64  | 延音踏板       | `&` 连音（见下方策略）|
| 65  | 滑音开关       | `{}` 滑音  |
| 66  | 持续踏板       | —           |
| 67  | 柔音踏板       | —           |
| 68  | 连音           | `&`（连音符） |
| 69  | 持续 2         | —           |

### CC#64 延音踏板 → 音符延长策略

```text
算法:
1. 踏板踩下 (CC#64 ≥ 64): 标记 sustain_on = True
2. 踏板踩下期间，所有 note_off 不立即结束音符
   → 音符延长直到踏板释放或下一个同音 note_on
3. 踏板释放 (CC#64 < 64): 所有被 hold 的音符立即 off
4. MML 转换: 延长的音符用 & 连音实现
   原始: c4 (踏板踩下) r4 → 变为: c4&c4 (合并为 c2)
```

### 音色控制器 (70-79)

| CC# | 名称              | PMD MML 映射 |
|-----|-------------------|-------------|
| 71  | 共鸣/音色          | —           |
| 72  | 释放时间           | —           |
| 73  | 起音时间           | —           |
| 74  | 亮度/截止频率       | —           |

### 通道模式 (120-127)

| CC# | 名称              |
|-----|--------------------|
| 120 | 所有声音关闭        |
| 121 | 重置所有控制器      |
| 123 | 所有音符关闭        |
| 124 | Omni 模式关        |
| 125 | Omni 模式开        |
| 126 | 单声道模式开        |
| 127 | 复音模式开          |

---

## 4. Meta 事件（仅 SMF，状态 `0xFF`）

| 类型 | 名称         | 数据              | PMD MML 映射         |
|------|-------------|-------------------|---------------------|
| 0x01 | 文本         | ASCII 字符串      | `;` 注释             |
| 0x02 | 版权         | ASCII 字符串      | —                   |
| 0x03 | 轨道名       | ASCII 字符串      | `#Title` / `;` 注释  |
| 0x04 | 乐器名       | ASCII 字符串      | `;` 注释             |
| 0x05 | 歌词         | ASCII 字符串      | —                   |
| 0x06 | 标记         | ASCII 字符串      | `;` 注释             |
| **0x20** | **MIDI 通道前缀** | 通道 (0-15) | 通道路由            |
| **0x51** | **设置速度**      | 3 字节（μs/拍）| **`t` / `#Tempo`** |
| **0x58** | **拍号**          | nn/dd/cc/bb | `; time_sig` 注释  |
| 0x59 | 调号         | sf/mi             | `;` 注释             |
| 0x2F | 轨道结束      | —                 | （必须存在）          |

### 速度计算

```text
tempo_us = 3 字节大端值（微秒/拍）
BPM = 60,000,000 / tempo_us
默认: 500000 μs = 120 BPM
```

---

## 5. 力度 → PMD 音量映射

```text
MIDI velocity: 0-127
PMD v 命令:    0-15  （粗糙，FM/PSG 通道用，通过音量表映射）
PMD V 命令:    0-127 （精细，FM/PSG 通道）
               0-255 （PCM 通道，v*16 扩展）

映射方案:
  v = velocity // 8        (0-15，简单映射)
  V = velocity             (0-127，直接映射，FM/PSG)
  V = velocity * 2         (0-254，PCM 通道)
```

---

## 6. 音色变更 → PMD `@` 映射

```text
MIDI program: 0-127（GM 乐器编号）
PMD @:        音色编号（设备相关）

直接映射: @ = program_number
通道 9（鼓组）使用不同的乐器映射表。
```

### MIDI Ch9 鼓组 → PMD `\` 节奏映射

PMD 节奏音源有 6 种内置乐器，MIDI GM Drum Map (note 35-81) 需要映射到这 6 种：

```text
PMD 节奏乐器:
  \b = Bass Drum（大鼓）
  \s = Snare Drum（军鼓）
  \c = Cymbal（钹）
  \h = Hi-Hat（踩镲）
  \t = Tom（嗵鼓）
  \i = Rim Shot（边击）

MIDI GM Drum → PMD 映射:
  Note 35-36 (Acoustic/Electric Bass Drum) → \b
  Note 37     (Side Stick)                  → \i
  Note 38-40 (Snare/Clap)                  → \s
  Note 41-43 (Low Tom/Floor Tom)            → \t
  Note 44     (Pedal Hi-Hat)                → \h
  Note 45     (Low Tom)                     → \t
  Note 46     (Open Hi-Hat)                 → \h
  Note 47-48 (Mid Tom)                      → \t
  Note 49     (Crash Cymbal 1)              → \c
  Note 50     (High Tom)                    → \t
  Note 51     (Ride Cymbal 1)               → \c
  Note 52     (Chinese Cymbal)              → \c
  Note 53     (Ride Bell)                   → \c
  Note 54     (Tambourine)                  → \i
  Note 55     (Splash Cymbal)               → \c
  Note 56     (Cowbell)                     → \i
  Note 57     (Crash Cymbal 2)              → \c
  Note 59     (Ride Cymbal 2)               → \c
  其他        → ; 注释（不支持的鼓打）

节奏音长: 鼓组通常不需要音长，PMD 用 c<长度> 作为节奏间隔。
鼓力度: 每个乐器可通过 \v 独立设置 (0-15)。
```

## 7. 弯音轮 → PMD 音高控制（完整方案）

### PMD 音高系统架构（来自 PMDDotNET 驱动源码）

PMD 的最终音高由四个分量叠加：

```text
final_pitch = FNUM + detune + LFO + portamento
```

对应 PMD.cs `otodasi()` 函数（L6391-6460）：
- `partWk[di].fnum`      ← 基础音高（由音名 + 八度决定）
- `partWk[di].detune`    ← D 命令设置的静态偏移
- `partWk[di].lfodat`    ← M 命令的周期性 LFO 值
- `partWk[di].porta_num` ← `{}` 滑音的插值增量

当 detune 超出当前八度 FNUM 范围时，`fm_block_calc()` 自动调整 BLOCK（八度）。

### PMD 可用的 4 种音高控制命令

| MML 命令 | 含义 | 参数 | 运行时行为 |
|----------|------|------|-----------|
| `D<n>` | 静态失谐 | 有符号整数（FNUM 偏移） | 固定加到 FNUM 上，直到下次 D |
| `DD<n>` | 相对失谐 | 有符号增量 | 累加到当前 detune |
| `M<d>,<depth>,<speed>` | 音高 LFO | delay/深度/速度 | 周期性三角波调制 FNUM |
| `{note1 note2}` | 滑音 (Portamento) | 两个音符 | 在音符时长内线性插值音高 |

### MIDI Pitch Bend → PMD 映射策略

MIDI pitch bend 是 14-bit 值 (0-16383)，中心 = 8192，每帧可变化。
默认弯音范围 (bend range) = ±2 半音。

#### 策略 1: 静态弯音 → `D` 命令

适用：弯音在音符开始时设置，期间不变化。

```text
算法:
1. 在 note_on 时刻读取当前 pitch_bend 值
2. 如果 bend == 8192（中心），跳过
3. 计算 FNUM 偏移:
   bend_semitones = (bend - 8192) / 8192.0 * bend_range
   D_value = round(bend_semitones * FNUM_per_semitone)
4. 在音符前插入 D<value>

FNUM 每半音约 = 0x26A / 12 ≈ 51（FM）
示例: bend = 12288 → +1 半音 → D51
```

#### 策略 2: 连续弯音 → 音符拆分 + `{}`滑音

适用：弯音在音符期间连续变化（如吉他推弦）。

```text
算法:
1. 收集音符期间所有 pitch_bend 事件
2. 计算起始音高和结束音高（含弯音）
3. 如果起止差 ≥ 1 半音:
   → 使用 {起始音 结束音} 滑音
   起始音 = 原始音名 + round(start_bend)
   结束音 = 原始音名 + round(end_bend)
4. 如果起止差 < 1 半音:
   → 退化为策略 1（D 命令取平均值）

示例: C4 开始，pitch bend 从 8192 升至 16383（+2 半音）
  → {c d}4  （从 C4 滑到 D4）
```

#### 策略 3: 周期性弯音 → `M` LFO

适用：弯音呈现规律振荡（如揉弦/vibrato）。

```text
检测算法:
1. 在音符时长内采样所有 pitch_bend 值
2. 检测是否存在周期性模式:
   - 计算过零点数量（经过 8192 中心的次数）
   - 如果过零点 ≥ 4 且分布均匀 → 判定为 vibrato
3. 提取 LFO 参数:
   depth = max(|bend - 8192|) 转换为 FNUM 单位
   speed = 音符 tick 数 / 半周期数
   delay = 第一个过零点的 tick 位置
4. 输出: M<delay>,<depth>,<speed>

示例: 在 480 ticks 内做 4 次振荡，幅度 ±30:
  → M0,30,60  （无延迟，深度 30，速度 60）
```

### 实现优先级

```text
优先级  策略               难度   效果
 1      静态 D 命令         低     覆盖 80% 场景
 2      滑音 {} 拆分        中     处理推弦/滑音
 3      M LFO 检测         高     处理揉弦

建议: 先实现策略 1，后续可选择性添加策略 2/3。
不可映射的复杂弯音 → 输出 ; 注释提示用户手动调整。
```

---

## 8. 门限时间 (Gate Time) → PMD `q` / `Q` 映射

门限时间 = 音符实际发音时长占理论时长的比例。
MIDI 中没有显式的 gate time 参数，需要从 note_on 到 note_off 的实际时长与量化后的理论音长对比计算。

```text
gate_ratio = actual_ticks / quantized_ticks

PMD q 命令: q0-q8（每级 = 12.5%）
  q8 = 100%  连音（legato）
  q7 = 87.5%
  q6 = 75%
  q5 = 62.5%
  q4 = 50%   断奏（staccato）
  q3 = 37.5%
  q2 = 25%
  q1 = 12.5%
  q0 = 极短

映射: q = round(gate_ratio * 8)
默认: q8（全时值发音）

PMD Q 命令: Q<ticks>（从音符末尾减去的静音 tick 数）
  Q0  = 全时值发音（等于 q8）
  Q48 = 末尾减去 48 tick（更精确的控制）

映射: Q = quantized_ticks - actual_ticks
```

### 计算示例

```text
四分音符 = 480 ticks (量化后)
实际 note_on→note_off = 360 ticks

gate_ratio = 360 / 480 = 0.75 → q6
或: Q = 480 - 360 = 120 → Q120
```

---

## 9. 音符时长量化

### 标准音长（按 PPQN 计算的 tick 数）

```text
MML 音长  拍数    tick数(PPQN=480)
1         4.0     1920    全音符
2         2.0     960     二分音符
4         1.0     480     四分音符
8         0.5     240     八分音符
16        0.25    120     十六分音符
32        0.125   60      三十二分音符
64        0.0625  30      六十四分音符
```

### 附点音符（×1.5）

```text
MML       拍数        tick数(480)
2.        3.0         1440
4.        1.5         720
8.        0.75        360
16.       0.375       180
32.       0.1875      90
```

### 双附点音符（×1.75）

```text
MML       拍数        tick数(480)
2..       3.5         1680
4..       1.75        840
8..       0.875       420
```

### 三连音（×2/3）

```text
MML 音长    拍数        tick数(480)
t4 (4/3)    0.667       320
t8 (8/3)    0.333       160
t16 (16/3)  0.167       80
```

### 连音符分解算法

```text
当音符时长不匹配单个音长时：
1. 找到最大的标准/附点音长 ≤ 剩余时长
2. 输出音符加 & 连音符
3. 减去已匹配的时长，重复直到余量 = 0

例: 720 ticks = 480 + 240 → "c4&c8"
例: 600 ticks = 480 + 120 → "c4&c16"
```

---

## 9. MIDI 通道 → PMD 声部映射

## 9. PMD 声部结构与通道映射

### PMD 完整声部表（来自 PW.cs part_table）

```text
OPN2 音源结构:
┌─────────────────────────────────────┐
│ FM1  (A)  ─ 第一组FM, ch1          │
│ FM2  (B)  ─ 第一组FM, ch2          │
│ FM3  (C)  ─ 第一组FM, ch3 ★可扩展  │
│ FM4  (D)  ─ 第二组FM, ch1          │
│ FM5  (E)  ─ 第二组FM, ch2          │
│ FM6  (F)  ─ 第二组FM, ch3          │
│ SSG1 (G)  ─ PSG/SSG 通道1          │
│ SSG2 (H)  ─ PSG/SSG 通道2          │
│ SSG3 (I)  ─ PSG/SSG 通道3          │
│ ADPCM(J)  ─ PCM 通道               │
│ Rhythm(K) ─ 节奏音源(鼓组)         │
└─────────────────────────────────────┘
```

### FM3 扩展通道模式（効果音モード）

OPN/OPN2 的 FM3 通道具有特殊模式：4 个运算器 (Operator/Slot) 可独立设置频率，
相当于将 1 个 FM 通道拆分为最多 4 个独立音高的声部。

```text
#FM3Extend <part1><part2><part3>

FM3 (C) 正常模式: 4 个 slot 共用同一频率
FM3 (C) 扩展模式: 4 个 slot 各自独立频率
  Slot1 → C   (原始声部)
  Slot2 → <part1> (通过 #FM3Extend 指定)
  Slot3 → <part2>
  Slot4 → <part3>

ch3mode 寄存器 (OPN reg 0x27):
  0x3F = 扩展模式 (效果音モード)
  0x00 = 正常模式
```

> **对 MIDI 转换的影响**: FM3 扩展模式允许增加 3 个额外的 FM 声部。
> 如果 MIDI 文件超过 6 个 FM 通道，可以启用此模式获得最多 9 个 FM 声部。
> 但需要注意：扩展 slot 共用同一个 FM 音色参数，只有频率独立。

### MIDI 通道 → PMD 声部映射

| MIDI 通道 | 典型用途 | PMD 声部 | 音源类型 |
|-----------|---------|---------|---------|
| 0 | FM | A | FM1 |
| 1 | FM | B | FM2 |
| 2 | FM | C | FM3 (Slot1) |
| 3 | FM | D | FM4 |
| 4 | FM | E | FM5 |
| 5 | FM | F | FM6 |
| 6 | PSG | G | SSG1 |
| 7 | PSG | H | SSG2 |
| 8 | PSG | I | SSG3 |
| **9** | **打击乐/鼓组** | **K** | **Rhythm** |
| 10 | PCM/采样 | J | ADPCM |
| 11 | FM3 Slot2 ★ | C 扩展1 | FM3 扩展 |
| 12 | FM3 Slot3 ★ | C 扩展2 | FM3 扩展 |
| 13 | FM3 Slot4 ★ | C 扩展3 | FM3 扩展 |
| 14-15 | 溢出/忽略 | — | 注释提示 |

> ★ = 仅当 ch11-13 被使用时自动启用

### FM3Extend 自动检测

```text
算法:
1. 预扫描 MIDI 文件，统计每个通道的 note_on 事件数
2. 如果 ch11/12/13 中任何一个有 note_on 事件:
   → 自动启用 FM3 扩展模式
   → 输出 #FM3Extend 指令，分配声部名
3. 映射关系:
   ch2  → C   (FM3 Slot1，主声部)
   ch11 → 扩展声部1 (FM3 Slot2)
   ch12 → 扩展声部2 (FM3 Slot3)
   ch13 → 扩展声部3 (FM3 Slot4)
4. 如果 ch11-13 均无事件:
   → 正常模式，ch11-15 全部忽略

MML 输出示例（启用扩展时）:
  #FM3Extend XYZ   ; X/Y/Z 为扩展 slot 的声部字母
  C  c4d4e4...     ; FM3 Slot1 (来自 MIDI ch2)
  X  g4a4b4...     ; FM3 Slot2 (来自 MIDI ch11)
  Y  e4f4g4...     ; FM3 Slot3 (来自 MIDI ch12)
  Z  c4c4c4...     ; FM3 Slot4 (来自 MIDI ch13)
```

> **注意**: FM3 扩展 slot 共用同一个 FM 音色（@指令），只有频率独立。

---

## 10. MIDI CC 自动化 → MML 转换策略

MIDI CC 事件（CC#7 音量、CC#10 声像、CC#11 Expression）可以在**任意 tick 位置**发生，
形成连续的自动化曲线。但 PMD MML 是**离散指令**，只能在音符间插入控制命令。

```text
MIDI 世界:  CC#7 逐 tick 变化 → 平滑渐变曲线
PMD 世界:   V / ( / ) 命令 → 离散阶梯变化

关键: 必须将连续 CC 曲线量化为离散 MML 命令
```

### 10.1 音量自动化 (CC#7 + CC#11)

#### 有效音量计算

MIDI 的最终音量由 CC#7 (Volume) 和 CC#11 (Expression) 共同决定：

```text
effective_volume = (CC#7 × CC#11) / 127

CC#7  = 通道基础音量（通常整首曲子不变或缓慢变化）
CC#11 = 表情音量（用于乐句内的动态变化）

PMD 映射: V = effective_volume = (cc7 * cc11) / 127
```

#### 量化算法

```text
算法: Note-Boundary Volume Quantization
1. 收集当前通道的所有 CC#7 和 CC#11 事件，按 tick 排序
2. 维护状态: current_cc7 = 127, current_cc11 = 127
3. 对于每个音符 note_on:
   a. 查找此 note_on 之前最近的 CC#7/CC#11 值
   b. 计算: new_vol = (cc7 * cc11) / 127
   c. 如果 new_vol ≠ last_output_vol:
      → 在音符前插入 V<new_vol>
      → 更新 last_output_vol
   d. 如果 new_vol == last_output_vol:
      → 不输出（去重）

优化: 如果一个音符期间 CC#7/CC#11 持续变化（渐变）:
  → 将音符拆分为多段，每段插入 V
  → 或使用 PMD (^<n> / )^<n> 每音符自动增减
```

#### PMD 音量渐变工具

```text
方案 A: 逐音符插入 V 命令（精确但冗长）
  V120 c8 V115 d8 V110 e8 V105 f8
  
方案 B: 使用 (^n / )^n 每音符自动增减（紧凑）
  (^5      ; 每个音符自动 volume -5
  V120 c8d8e8f8  
  (^0      ; 停止自动减量
  
  对应: V120→V115→V110→V105（每个音自动递减）

方案 C: 大跨度直接设置 V
  当 ΔV > 20 时，直接 V<n> 而不用 (^

选择策略:
  |ΔV| ≤ 3 per note  → 方案 B  (^<n> 或 )^<n>
  |ΔV| > 3 per note  → 方案 A  逐个 V
  单次跳变            → 方案 C  直接 V
```

### 10.2 声像自动化 (CC#10)

PMD 只有 3 个声像位置 (p1=右, p2=左, p3=中)，无法实现 MIDI 的 128 级连续扫像。

```text
转换策略:
  CC#10 变化时，只在跨越区间边界时输出 p 命令:
  
  区间:
    0-42   → p2 (左)
    43-85  → p3 (中)  
    86-127 → p1 (右)
    
  去重: 如果新 p 值与上次相同，不输出

高级: PMD px 扩展声像命令
  px<n>[,<delay>]  (opcode 0xC3)
  可用于更精细的声像控制（如果目标平台支持）
```

### 10.3 CC 事件去重与稀疏化

```text
规则:
1. 连续相同值: 绝对不重复输出
2. 微小变化: |ΔV| ≤ 2 且在同一音符内 → 忽略
3. 快速变化: 在单个音符时长内有多次 CC → 只取最后一个值
4. 音符间隙: 休止符期间的 CC 变化 → 累积到下个音符

示例:
  MIDI: CC#7=100 @tick50, CC#7=98 @tick55, CC#7=96 @tick60
        note_on @tick64
  MML:  V96 c8    (只输出 note_on 时刻的最终值)
```

### 10.4 音符分割实现渐变

当一个长音符期间 CC 持续变化时，需要将音符拆分：

```text
原始 MIDI:
  note_on C4 @tick0, duration=192 ticks (全音符)
  CC#7: 100@0, 80@48, 60@96, 40@144

MML 转换 (全音符 = c1, 四分之一 = c4):
  V100 c4 & V80 c4 & V60 c4 & V40 c4
  
  用 & 连音保持音符不断开，每段重新设置 V。

判断条件:
  音符持续期间 |ΔV| > 10 → 需要拆分
  拆分粒度: 不小于 1/16 音符（避免过度碎片化）
```

---

## 11. Tick 分辨率转换与 `#Zenlen`

### MIDI 与 PMD 的 Tick 体系

```text
MIDI: ticks_per_beat 由 SMF header 定义（常见值: 480, 960, 120, 96）
PMD:  #Zenlen 定义全音符的 tick 数（默认 96）
      → 四分音符 = Zenlen/4 = 24 ticks
      → 八分音符 = Zenlen/8 = 12 ticks

转换公式:
  pmd_ticks = midi_ticks × (zenlen / 4) / midi_ticks_per_beat
  
  例: MIDI tpb=480, PMD zenlen=96
  pmd = midi_ticks × 24 / 480 = midi_ticks / 20

建议: #Zenlen 可设为更高值（如 192/384）来提高分辨率
      但 PMD 编译器最大 Zenlen = 255 (byte)
```

### 推荐 #Zenlen 选择

```text
默认使用 #Zenlen 192

MIDI tpb=480 → #Zenlen 192 (缩放因子 48/480 = 1/10)
MIDI tpb=960 → #Zenlen 192 (缩放因子 48/960 = 1/20)
MIDI tpb=120 → #Zenlen 192 (缩放因子 48/120 = 2/5)
MIDI tpb=96  → #Zenlen 192 (缩放因子 48/96 = 1/2)

原则: 固定使用 192，除非有特殊精度需求
```

---

## 12. 复音 → 单音转换（Polyphony Resolution）

PMD 每个声部严格单声道，但 MIDI 通道允许同时发多个音。

### 检测与处理

```text
情况 1: 和弦（多音同时 note_on）
  MIDI: C4+E4+G4 同时
  策略: 
    优先级: 取最高音 G4（旋律通常在高音）
    或: 将和弦拆分到多个 PMD 声部（如果有空闲通道）

情况 2: 重叠音符（legato，前音未 off 就开始新音）
  MIDI: C4 on → D4 on → C4 off → D4 off
  策略: 在新 note_on 时截断前一个音
  MML:  c<计算长度> d<计算长度>

情况 3: 延音踏板导致的堆叠
  已在 CC#64 策略中处理（只保留最新音）
```

### 复音拆分算法

```text
算法:
1. 预扫描通道，检测同时发声的最大音数
2. 如果 max_polyphony == 1: 无需处理
3. 如果 max_polyphony == 2-3: 
   → 尝试拆分到空闲 PMD 声部
   → 或用最高音优先策略
4. 如果 max_polyphony > 3:
   → 输出警告注释
   → 只保留最高音

实现: 维护 active_notes 集合
  note_on:  如果 active_notes 非空 → 截断最低音或分配新声部
  note_off: 从 active_notes 移除
```

---

## 13. 速度变更与循环检测

### 13.1 MIDI Tempo 变更 → PMD `t` 命令

```text
MIDI: meta event 0x51 (set_tempo) 可在任意 tick 出现
PMD:  t<BPM> 命令可在任意声部的任意位置插入

转换:
  BPM = 60000000 / tempo_microseconds
  → t<BPM>  (BPM ≥ 18，PMD 限制)

放置策略:
  1. tempo 变更插入到主声部（A 通道）对应 tick 位置
  2. 如果该 tick 在音符中间 → 拆分音符，插入 t 命令
  3. 相对变速: t+<n> / t-<n> 可用于微调
```

### 13.2 循环检测（Loop Detection）

MIDI 没有原生循环标记，但可以通过模式匹配检测：

```text
PMD 循环命令:
  L         无限循环从此处开始（全曲循环点）
  [n ... ]  重复 n 次
  [n ... : ... ]  重复 n 次，最后一次跳过 : 后的内容

检测策略:
  Phase 1: 被动检测
    - 检查 MIDI meta marker 事件中是否包含 "loop" 标记
    - 某些 DAW 会在 marker 中标注循环点
    
  Phase 2: 模式匹配（可选，复杂度高）
    - 比较通道的音符序列，寻找重复 pattern
    - 如果后半段 = 前半段 → 用 L 标记循环点
    
  Phase 3: 用户指定
    - 提供 CLI 参数让用户手动指定循环起始 tick
    - --loop-start <tick> → 在该 tick 插入 L 命令

默认行为: 不插入循环，完整输出所有音符
```

---

## 14. MIDI RPN 与弯音范围

### Pitch Bend Range (RPN 0x0000)

MIDI 的弯音轮范围默认 ±2 半音，但可通过 RPN 修改：

```text
设置弯音范围的 CC 序列:
  CC#101 = 0  (RPN MSB)
  CC#100 = 0  (RPN LSB)  → 选择 RPN 0x0000 (Pitch Bend Sensitivity)
  CC#6 = n    (Data Entry MSB) → 弯音范围 = ±n 半音
  CC#38 = c   (Data Entry LSB) → 弯音范围精调 = ±c/100 半音

常见值:
  n=2  → ±2 半音（GM 默认）
  n=12 → ±1 八度（某些音源的预设）
  n=24 → ±2 八度

在 D 失谐转换中的影响:
  D = (pitch_bend - 8192) × bend_range / 8192
  
  如果 bend_range=2:  D = (pb-8192) × 2 / 8192
  如果 bend_range=12: D = (pb-8192) × 12 / 8192

必须正确解析 RPN 才能得到准确的 D 值！
```

---

## 附录 A: PMD MML 完整命令参考（来自 VMML2VGM）

> 以下所有参数范围均从 PMDDotNET 编译器源码 `mc.cs` 验证。

### A.1 音符与休止符

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `c d e f g a b` | `c[+/-]<长度>` | 音符，+/- 为升降号 | note_on/note_off |
| `r` | `r<长度>` | 休止符 | 音符间间隙 |
| `&` | `c4&c8` | 连音（tie），延长音符时长 | 长音符分解 |
| `&&` | `c4&&d4` | 滑奏（slur），不重新触键 | — |

### A.2 八度控制

| 命令 | 格式 | 范围 | 说明 | MIDI 数据源 |
|------|------|------|------|------------|
| `o` | `o<n>` | 1-8 | 设置当前八度 | note // 12 |
| `>` | `>` | — | 八度上升 | 音符跨八度时 |
| `<` | `<` | — | 八度下降 | 音符跨八度时 |

### A.3 音长控制

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `l` | `l<n>` | 默认音长（1/2/4/8/16/32/64） | 量化后的主要音长 |
| `l=` | `l=<n>` | 修改直前音长 | — |
| `l-` | `l-<n>` | 直前音长减算 | — |
| `l^` | `l^<n>` | 直前音长乘算 | — |
| `C` | `C<n>` | 全音符的 tick 数（默认 96） | ticks_per_beat × 4 |

### A.4 音量控制

| 命令 | 格式 | 范围 | 说明 | MIDI 数据源 |
|------|------|------|------|------------|
| `v` | `v<n>` | 0-15 | FM/PSG 粗糙音量 | velocity // 8 |
| `V` | `V<n>` | 0-127 (FM/PSG) / 0-255 (PCM) | 精细音量 | velocity 直接映射 |
| `v+n` / `v-n` | | | 相对音量增减 | velocity 变化 |
| `)` | `)` 或 `)<n>` | | 音量上升（默认+1） | — |
| `(` | `(` 或 `(<n>` | | 音量下降（默认-1） | — |

### A.5 速度与时序

| 命令 | 格式 | 范围 | 说明 | MIDI 数据源 |
|------|------|------|------|------------|
| `t` | `t<n>` | 18-255 | 设置 BPM 速度 | meta set_tempo |
| `T` | `T<n>` | | TimerB 直接设定 | — |
| `t+n` / `t-n` | | | 相对速度变化 | — |

### A.6 门限时间（Gate Time）

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `q` | `q<n>` | 基于 clock 的门限（n/8 比例） | actual_ticks / quantized_ticks |
| `q n-m` | `q3-5` | 随机门限范围 | — |
| `q ,n` | `q ,<n>` | 最小门限 tick 设定 | — |
| `Q` | `Q<n>` | 从音符末尾减去 n tick 的静音 | quantized - actual |
| `Q%` | `Q%<n>` | 百分比门限 | — |

### A.7 失谐（Detune）

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `D` | `D<n>` | 静态失谐（FNUM 偏移） | pitch_bend（静态） |
| `DD` | `DD<n>` | 相对失谐（累加） | pitch_bend 变化 |
| `DM` | `DM<n>` | Master Detune（全局） | — |
| `DX` | `DX<n>` | 扩展 Detune 模式 | — |

### A.8 LFO 与滑音

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `M` | `M<delay>,<depth>,<speed>` | 音高 LFO（三角波） | pitch_bend 周期性振荡 |
| `MA` | `MA...` | 音高 LFO（类型 A） | — |
| `MB` | `MB...` | 音高 LFO（类型 B） | — |
| `MD` | `MD<n>` | LFO 深度设定 | — |
| `MP` | `MP<a>[,<b>][,<c>]` | Portamento LFO 设定 | — |
| `MW` | `MW<n>` | LFO 波形选择 | — |
| `MX` | `MX<n>` | LFO 速度扩展模式 | — |
| `MM` | `MM<n>` | LFO Mask 设定 | — |
| `*` | `*<n>` | LFO 开关 | — |
| `{note note}` | `{c d}4` | 音高滑音（Portamento） | pitch_bend 连续变化 |
| `{{note note}}` | `{{c d e}}4` | 分散和音（Arpeggio） | — |

### A.9 乐器与音色

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `@` | `@<n>` | 设置乐器/音色号 | program_change |

### A.10 声像（Pan）

| 命令 | 格式 | 范围 | 说明 | MIDI 数据源 |
|------|------|------|------|------------|
| `p` | `p<n>` | 0-3 | 声像设定 | CC#10 |
| `px` | `px<n>[,<m>]` | | 扩展声像 | — |

> p 值: 0=无声, 1=右, 2=左, 3=居中

### A.11 转调

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `_` | `_<n>` | 转调（半音数） | — |
| `__` | `__<n>` | 相对转调 | — |
| `_M` | `_M<n>` | Master 转调（全局） | — |
| `_{` | `_{note=note}` | 音名映射指定 | — |

### A.12 循环控制

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `[` | `[<n>` | 循环开始，n=次数 | — |
| `]` | `]` | 循环结束 | — |
| `:` | `:` | 最后一次循环时跳出 | — |
| `L` | `L` | 设置全曲循环点 | — |

### A.13 PMD 专用指令

| 命令 | 格式 | 说明 | MIDI 数据源 |
|------|------|------|------------|
| `B` | `B<n>` | 弯音幅度（0-12 半音） | — |
| `I` | `I<n>` | 音高微调 | — |
| `y` | `y<reg>,<val>` | OPN 寄存器直写 | — |
| `E` | `E<a>,<d>,<s>,<r>` | PSG 软件包络 | — |
| `EX` | `EX` | 包络速度扩展 | — |
| `w` | `w<n>` | PSG 噪声频率 | — |
| `P` | `P<n>` | PSG tone/noise/mix | — |
| `\` | `\b \s \c \h \t \i` | 节奏音源鼓组控制(K 声部) | MIDI ch9 |

### A.14 音量衰减

| 命令 | 格式 | 说明 |
|------|------|------|
| `DF` | `DF<n>` | FM 音量衰减 |
| `DS` | `DS<n>` | PSG (SSG) 音量衰减 |
| `DP` | `DP<n>` | PCM 音量衰减 |
| `DR` | `DR<n>` | 节奏音量衰减 |

### A.15 PMD `#` 指令（文件头部）

| 指令 | 说明 | MIDI 数据源 |
|------|------|------------|
| `#Title` | 曲名 | meta track_name (type 0x03) |
| `#Composer` | 作曲者 | — |
| `#Arranger` | 编曲者 | — |
| `#Memo` | 备注 | meta text (type 0x01) |
| `#Tempo` | 初始速度 | meta set_tempo (type 0x51) |
| `#Zenlen` | 全音符 tick 数（默认 96） | ticks_per_beat × 4 / 比例 |
| `#Voldown` | 默认音量衰减 | — |
| `#PCMFile` | PCM 数据文件 | — |
| `#Octave Reverse` | 反转 >/< 方向 | — |

---

## 附录 B: MIDI → PMD MML 完整映射汇总

| MIDI 事件/数据 | PMD MML 命令 | 转换算法 |
|---------------|-------------|---------|
| note_on (note, velocity) | `o<oct> c/c+/d/.../b <长度>` | 音名+八度+量化音长 |
| note_off (计算间隙) | `r<长度>` | 间隙量化为休止符 |
| velocity | `V<n>` (0-127) 或 `v<n>` (0-15) | 直接映射 / velocity//8 |
| 长音符（不匹配单一音长） | `c4&c8` | 连音符分解 |
| note duration vs quantized | `q<n>` 或 `Q<tick>` | 门限计算 |
| program_change | `@<n>` | program 直接映射 |
| CC#7 (Volume) | `V<n>` | 直接映射 |
| CC#10 (Pan) | `p<0-3>` | <64→p2, =64→p3, >64→p1 |
| CC#11 (Expression) | `V<n>` (叠加) | 与 volume 乘算 |
| pitch_bend（静态） | `D<n>` | (bend-8192)/scale |
| pitch_bend（连续） | `{note1 note2}` | 起止音高滑音 |
| pitch_bend（周期性） | `M<d>,<depth>,<speed>` | LFO 参数提取 |
| set_tempo | `t<BPM>` 或 `#Tempo` | 60000000/tempo_us |
| track_name | `#Title` | 第一个轨道名 |
| time_signature | `; 拍号注释` | 注释记录 |
| MIDI ch 0-5 | PMD A-F | FM 通道 |
| MIDI ch 6-8 | PMD G-I | SSG 通道 |
| MIDI ch 9 (note→drum) | PMD K `\b\s\c\h\t\i` | GM Drum→6种节奏 |
| MIDI ch 10 | PMD J | ADPCM |
| MIDI ch 11-13 ★ | PMD C 扩展 slot | FM3 扩展（自动检测） |
| MIDI ch 14-15 | — | 溢出忽略 |
| CC#1 (Modulation) | `M<d>,<s>,<depth>,<depth>` | LFO vibrato |
| CC#64 (Sustain) | `&` 连音延长 | 踏板→音符合并 |
| CC#65 (Portamento) | `{}` 滑音 | 滑音开关 |
| CC#7+CC#11 自动化 | `V` / `(^` / `)^` | (cc7×cc11)/127 + 渐变 |
| CC#10 自动化 | `p<0-3>` | 3 区间量化 |
| RPN 0x0000 (Bend Range) | 影响 `D` 计算 | CC#101/100/6 解析 |
| 复音 (polyphony) | 最高音优先/拆分声部 | active_notes 集合 |
| meta 0x51 (mid-song) | `t<BPM>` | 插入到 A 声部 |
| ticks_per_beat | `#Zenlen` | zenlen/4 / tpb 缩放 |
| meta marker "loop" | `L` | 循环点检测 |

