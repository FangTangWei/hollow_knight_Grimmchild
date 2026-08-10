# hollow_knight_Grimmchild

我将《空洞骑士》中的格林之子，做成了一个桌宠。 / I turned the Grimmchild from Hollow Knight into a little desk pet.

![格林之子桌宠图标](https://github.com/FangTangWei/hollow_knight_Grimmchild/blob/main/FlameConsumed.ico)

![Stars](https://img.shields.io/github/stars/FangTangWei/hollow_knight_Grimmchild?style=social)
![Forks](https://img.shields.io/github/forks/FangTangWei/hollow_knight_Grimmchild?style=social)
![License](https://img.shields.io/github/license/FangTangWei/hollow_knight_Grimmchild)
![Repo Size](https://img.shields.io/github/repo-size/FangTangWei/hollow_knight_Grimmchild)
![Python](https://img.shields.io/badge/Python-3.14%2B-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-41CD52?logo=qt&logoColor=white)
![Visitors](https://visitor-badge.laobi.icu/badge?page_id=FangTangWei.hollow_knight_Grimmchild)

---

> 一款基于 Python 制作的 Windows 桌面智能宠物，拥有完整计时逻辑、自主行为与桌面生态互动，可自主成长、休眠、瞬移、繁育、对战。

---

## 基础运行规则

桌宠固定 **60 帧/秒**，1 帧 = 1/60 秒，所有倒计时逐帧递减计算，动作计时精准稳定。

---

## 单只宠物独立行为规则

### 1. 进阶成长

仅飞行、待机状态累计成长时间，成长周期为 **1–5 分钟**，最高可自动成长至 4 阶。
击杀同类可**即时升级 1 级**，不受计时限制。

### 2. 作息休眠

宠物闲逛结束后，经过 **10–30 秒** 冷却自动进入睡眠状态。
单次睡眠时长 **10–60 秒**，睡眠结束自动苏醒、恢复活动。

### 3. 瞬移机动

每 **10–30 秒** 冷却完成一次自主瞬移，宠物可在桌面自由穿梭。

### 4. 攻击限制

每次攻击结束后固定 **3 秒攻击冷却**，冷却期间无法再次发起攻击。

---

## 全局桌面生态规则

### 1. 繁育新增

系统每 **10 分 25 秒** 自动尝试分裂生成新宠物。
自动生成条件：桌面宠物数量 **小于 4 只**。
支持右键**手动分裂**，无冷却、直接生成新宠物。

### 2. 全局对战

系统每 **3 分 7.5 秒** 触发一轮全场随机对战。

触发条件：
- 桌面宠物数量 ≥ 2 只
- 宠物无攻击冷却

条件不满足则自动跳过本轮攻击。

---

## 动画与音效

- **37 套动画序列**：空闲（4 种）、飞行（4 种）、射击、前摇、瞬移出入、睡眠/唤醒、火焰球、爆发等
- **11 种游戏原声音效**：包含飞行循环、攻击、瞬移、火焰球射击、背景音乐等

---

## 环境要求

- Windows 操作系统
- Python **3.14+**
- PyQt5

---

## 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/FangTangWei/hollow_knight_Grimmchild.git
cd hollow_knight_Grimmchild

# 2. 安装依赖
pip install PyQt5

# 3. 运行
python Grimmchild.py
```

---

## 打包为 EXE

使用 PyInstaller 将项目打包成单个可执行文件：

```bash
pip install pyinstaller

pyinstaller -w --onefile -i "FlameConsumed.ico" --add-data "AudioClip;AudioClip" --add-data "Grimmchild Anim;Grimmchild Anim" Grimmchild.py
```

| 参数 | 说明 |
|------|------|
| `-w` | 无控制台窗口（桌面应用） |
| `--onefile` | 打包为单个 EXE 文件 |
| `-i` | 指定应用图标 |
| `--add-data` | 将音频和动画资源打包进 EXE |

打包完成后，在 `dist/` 目录下找到 `Grimmchild.exe` 即可运行。

---

## 项目结构

```
Grimmchild
├── Grimmchild.py              # 主程序入口
├── FlameConsumed.ico          # 应用图标
├── AudioClip/                 # 音效文件
│   ├── Grimm.mp3              # 格林主题曲
│   ├── Grimm Epic Layer.mp3   # 格林史诗层
│   ├── grimmchild_fly_loop.mp3          # 飞行循环音效
│   ├── grimmchild_fireball_shoot.mp3     # 火焰球射击
│   ├── grimm_teleport_out.mp3            # 瞬移离开
│   ├── Grimmbat_idle_1~3.mp3             # 静止音效
│   ├── Grimmbat_idle_4.mp3
│   ├── 1Grimmbat_attack_yelp_1~3.mp3     # 攻击音效
│   ├── 1Grimmbat_attack_yelp_4.mp3
│   ├── 2Grimmbat_attack_yelp_1~3.mp3
│   └── 2Grimmbat_attack_yelp_4.mp3
└── Grimmchild Anim/           # 动画帧（37 套动画序列）
    ├── 001.Idle 4 ~ 003.Idle 1             # 空闲动画（4 种）
    ├── 004.Antic 4 ~ 007.Shoot 2           # 攻击前摇 & 射击
    ├── 008.Sleep 4 ~ 013.Wake 1            # 睡眠 & 唤醒
    ├── 014.Tele Out 4 ~ 019.Tele In 1      # 瞬移出入
    ├── 020.TurnToIdle 4 ~ 022.TurnToIdle 1 # 转回空闲
    ├── 023.Idle 3 ~ 030.TurnToIdle 3       # 第三形态动画
    ├── 031.Fly 1 ~ 034.Fly 4               # 飞行动画（4 种）
    ├── 035.Burst                           # 爆发
    ├── 036.Flameball                       # 火焰球
    └── 037.Flameball Impact                # 火焰球撞击
```

---

## 使用的库

| 库 | 用途 |
|---|---|
| `sys` / `os` | 系统路径与文件操作 |
| `random` / `math` | 随机行为与数学计算 |
| `PyQt5.QtWidgets` | 窗口、系统托盘、菜单 |
| `PyQt5.QtCore` | 定时器、坐标、矩形区域 |
| `PyQt5.QtGui` | 图像渲染、变换、图标 |
| `PyQt5.QtMultimedia` | 音效与背景音乐播放 |

---

## 素材提取

游戏中的图片和音频素材通过以下工具从《空洞骑士》游戏文件中提取：

- **[AssetStudioModGUI](https://github.com/aelurum/AssetStudio)** — 提取精灵帧动画（PNG 序列）和音效（MP3）
- **Game Object Dump** — 导出角色动画数据，辅助动画帧分类与命名

---

## 许可证

本项目仅供学习与交流使用。游戏素材版权归 Team Cherry（《空洞骑士》开发商）所有。

---

## 鸣谢

- [Team Cherry](https://www.teamcherry.com.au/) — 《空洞骑士》开发商
- 格林之子原作角色设计 & 音效素材来源
- [AssetStudioModGUI](https://github.com/aelurum/AssetStudio) — Unity 资源提取工具
- Game Object Dump — 动画数据导出工具
