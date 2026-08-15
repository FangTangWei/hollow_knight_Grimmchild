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

python -m PyInstaller Grimmchild.spec --workpath "%TEMP%\gc_work" --distpath ".\dist" --clean --noconfirm
```

| 文件 | 操作 |
|------|------|
| `Grimmchild.spec` | 只需修改其中第十行 `ROOT = r'需要打包的文件所在路径'` |

打包完成后，在 `dist/` 目录下找到 `Grimmchild.exe` 即可运行。

---

## 项目结构
<details>
<summary>点击展开查看目录</summary>

```
Grimmchild
├─ AudioClip
│  ├─ 1Grimmbat_attack_yelp_1~3.mp3
│  ├─ 1Grimmbat_attack_yelp_4.mp3
│  ├─ 2Grimmbat_attack_yelp_1~3.mp3
│  ├─ 2Grimmbat_attack_yelp_4.mp3
│  ├─ Grimm Epic Layer.mp3
│  ├─ grimm_teleport_out.mp3
│  ├─ Grimm.mp3
│  ├─ Grimmbat_idle_1~3.mp3
│  ├─ Grimmbat_idle_4.mp3
│  ├─ grimmchild_fireball_shoot.mp3
│  └─ grimmchild_fly_loop.mp3
├─ Grimmchild Anim
│  ├─ 001.Idle 4
│  │  ├─ 001-00-121.png
│  │  ├─ 001-01-009.png
│  │  ├─ 001-02-000.png
│  │  ├─ 001-03-003.png
│  │  ├─ 001-04-001.png
│  │  ├─ 001-05-016.png
│  │  └─ 001-06-005.png
│  ├─ 002.Idle 2
│  │  ├─ 002-00-106.png
│  │  ├─ 002-01-002.png
│  │  ├─ 002-02-013.png
│  │  ├─ 002-03-015.png
│  │  ├─ 002-04-006.png
│  │  ├─ 002-05-008.png
│  │  └─ 002-06-004.png
│  ├─ 003.Idle 1
│  │  ├─ 003-00-116.png
│  │  ├─ 003-01-012.png
│  │  ├─ 003-02-014.png
│  │  ├─ 003-03-010.png
│  │  ├─ 003-04-011.png
│  │  └─ 003-05-007.png
│  ├─ 004.Antic 4
│  │  ├─ 004-00-026.png
│  │  ├─ 004-01-025.png
│  │  ├─ 004-02-027.png
│  │  └─ 004-03-030.png
│  ├─ 005.Shoot 4
│  │  ├─ 005-00-017.png
│  │  └─ 005-01-023.png
│  ├─ 006.Antic 2
│  │  ├─ 006-00-019.png
│  │  ├─ 006-01-018.png
│  │  ├─ 006-02-024.png
│  │  └─ 006-03-020.png
│  ├─ 007.Shoot 2
│  │  ├─ 007-00-022.png
│  │  ├─ 007-01-029.png
│  │  └─ 007-02-021.png
│  ├─ 008.Sleep 4
│  │  ├─ 008-00-037.png
│  │  ├─ 008-01-038.png
│  │  └─ 008-02-031.png
│  ├─ 009.Wake 4
│  │  ├─ 009-00-038.png
│  │  └─ 009-01-037.png
│  ├─ 010.Sleep 2
│  │  ├─ 010-00-033.png
│  │  ├─ 010-01-032.png
│  │  └─ 010-02-039.png
│  ├─ 011.Wake 2
│  │  ├─ 011-00-032.png
│  │  └─ 011-01-033.png
│  ├─ 012.Sleep 1
│  │  ├─ 012-00-034.png
│  │  ├─ 012-01-035.png
│  │  └─ 012-02-036.png
│  ├─ 013.Wake 1
│  │  ├─ 013-00-035.png
│  │  └─ 013-01-034.png
│  ├─ 014.Tele Out 4
│  │  ├─ 014-00-062.png
│  │  ├─ 014-01-044.png
│  │  ├─ 014-02-057.png
│  │  ├─ 014-03-040.png
│  │  └─ 014-04-049.png
│  ├─ 015.Tele In 4
│  │  ├─ 015-00-049.png
│  │  ├─ 015-01-040.png
│  │  ├─ 015-02-057.png
│  │  ├─ 015-03-044.png
│  │  ├─ 015-04-062.png
│  │  └─ 015-05-047.png
│  ├─ 016.Tele Out 2
│  │  ├─ 016-00-061.png
│  │  ├─ 016-01-052.png
│  │  ├─ 016-02-045.png
│  │  ├─ 016-03-056.png
│  │  └─ 016-04-055.png
│  ├─ 017.Tele In 2
│  │  ├─ 017-00-087.png
│  │  ├─ 017-01-056.png
│  │  ├─ 017-02-045.png
│  │  ├─ 017-03-052.png
│  │  ├─ 017-04-061.png
│  │  ├─ 017-05-043.png
│  │  └─ 017-06-046.png
│  ├─ 018.Tele Out 1
│  │  ├─ 018-00-050.png
│  │  ├─ 018-01-053.png
│  │  ├─ 018-02-054.png
│  │  ├─ 018-03-060.png
│  │  ├─ 018-04-048.png
│  │  └─ 018-05-041.png
│  ├─ 019.Tele In 1
│  │  ├─ 019-00-041.png
│  │  ├─ 019-01-048.png
│  │  ├─ 019-02-060.png
│  │  ├─ 019-03-054.png
│  │  ├─ 019-04-053.png
│  │  └─ 019-05-050.png
│  ├─ 020.TurnToIdle 4
│  │  └─ 020-00-065.png
│  ├─ 021.TurnToIdle 2
│  │  └─ 021-00-064.png
│  ├─ 022.TurnToIdle 1
│  │  └─ 022-01-068.png
│  ├─ 023.Idle 3
│  │  ├─ 023-00-112.png
│  │  ├─ 023-01-072.png
│  │  ├─ 023-02-069.png
│  │  ├─ 023-03-074.png
│  │  ├─ 023-04-073.png
│  │  ├─ 023-05-070.png
│  │  └─ 023-06-071.png
│  ├─ 024.Antic 3
│  │  ├─ 024-00-075.png
│  │  ├─ 024-01-081.png
│  │  ├─ 024-02-078.png
│  │  └─ 024-03-076.png
│  ├─ 025.Shoot 3
│  │  ├─ 025-00-077.png
│  │  ├─ 025-01-080.png
│  │  └─ 025-02-079.png
│  ├─ 026.Sleep 3
│  │  ├─ 026-00-082.png
│  │  ├─ 026-01-083.png
│  │  └─ 026-02-084.png
│  ├─ 027.Wake 3
│  │  ├─ 027-00-083.png
│  │  └─ 027-01-082.png
│  ├─ 028.Tele In 3
│  │  ├─ 028-00-087.png
│  │  ├─ 028-01-085.png
│  │  ├─ 028-02-089.png
│  │  ├─ 028-03-091.png
│  │  ├─ 028-04-088.png
│  │  ├─ 028-05-090.png
│  │  └─ 028-06-086.png
│  ├─ 029.Tele Out 3
│  │  ├─ 029-00-088.png
│  │  ├─ 029-01-091.png
│  │  ├─ 029-02-089.png
│  │  ├─ 029-03-085.png
│  │  └─ 029-04-049.png
│  ├─ 030.TurnToIdle 3
│  │  └─ 030-00-093.png
│  ├─ 031.Fly 1
│  │  ├─ 031-00-114.png
│  │  ├─ 031-01-100.png
│  │  ├─ 031-02-116.png
│  │  ├─ 031-03-107.png
│  │  ├─ 031-04-111.png
│  │  └─ 031-05-103.png
│  ├─ 032.Fly 2
│  │  ├─ 032-00-102.png
│  │  ├─ 032-01-109.png
│  │  ├─ 032-02-058.png
│  │  ├─ 032-03-105.png
│  │  ├─ 032-04-106.png
│  │  ├─ 032-05-104.png
│  │  └─ 032-06-051.png
│  ├─ 033.Fly 3
│  │  ├─ 033-00-101.png
│  │  ├─ 033-01-099.png
│  │  ├─ 033-02-110.png
│  │  ├─ 033-03-097.png
│  │  ├─ 033-04-112.png
│  │  ├─ 033-05-118.png
│  │  └─ 033-06-115.png
│  ├─ 034.Fly 4
│  │  ├─ 034-00-119.png
│  │  ├─ 034-01-121.png
│  │  ├─ 034-02-117.png
│  │  ├─ 034-03-120.png
│  │  ├─ 034-04-113.png
│  │  └─ 034-05-108.png
│  ├─ 035.Burst
│  │  ├─ 035-00-092.png
│  │  ├─ 035-01-095.png
│  │  └─ 035-02-096.png
│  ├─ 036.Flameball
│  │  ├─ 036-00-123.png
│  │  ├─ 036-01-131.png
│  │  ├─ 036-02-132.png
│  │  ├─ 036-03-133.png
│  │  ├─ 036-04-134.png
│  │  ├─ 036-05-124.png
│  │  ├─ 036-06-125.png
│  │  └─ 036-07-126.png
│  └─ 037.Flameball Impact
│     ├─ 037-00-127.png
│     ├─ 037-01-128.png
│     ├─ 037-02-129.png
│     └─ 037-03-130.png
├─ FlameConsumed.ico
└─ Grimmchild.py
```

</details>

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
