# 数学书桌 / Math Desk

考前「查漏 + 计算提速」用的可打印练习（Word / PDF）。  
学校已有课和日常作业，这里**不是**每天必练的第二套作业。

对外名称：**数学书桌 / Math Desk**（与 English Desk、Chinese Desk 一套命名）。  
**主色：天蓝色**（卷头、品牌行统一用天蓝）。

## 定位

| 做 | 不做 |
| --- | --- |
| 限时口算冲刺（2 / 3 / 5 分钟） | 每天额外刷大卷 |
| 单元迷你查漏、错题重练 | 复杂 App |
| 少量竖式练熟练与工整 | 口算与思维题混成一张大卷 |
| 可打印 Word / PDF | 替代学校正式单元卷 |

孩子用**番茄钟**自己计时。进步看 **「2 分钟正确题数」**。

## 考前怎么用

1. **提速**  
   打印 `printables/oral/` 口算冲刺纸 → 限时做 → 铃响停笔 → 写「完成几题 / 正确几题」。

2. **查漏**  
   对照学校进度，用 `printables/unit-tests/` 或迷你查漏纸测一轮；批改后只订正错题。

3. **错题分类**  
   计算错 / 概念错尽量分开重练（见 `drills/`）。思维应用题用短思维纸，不和口算混印。

## 目录

```
Math Desk/
├── README.md
├── units/                 ← 各单元说明 + 教材
│   └── _textbook/         ← 人教版四上 PDF
├── drills/
│   ├── oral/              ← 口算（提速）
│   ├── vertical/          ← 少量竖式
│   └── thinking/          ← 短思维纸（与口算分开）
├── printables/
│   ├── oral/              ← 可打印口算
│   ├── unit-tests/        ← 单元测试高清 Word/PDF
│   └── templates/         ← 查漏迷你纸模板
├── answers/               ← 参考答案
├── scripts/               ← 生成脚本（天蓝主题）
├── _source/unit-tests/    ← 原始扫描图
└── test/                  ← 你放入的原始图（可继续往这丢）
```

## 单元测试入库状态

| 单元 | 内容 | 卷面 | 打印文件 | 答案 |
| --- | --- | --- | --- | --- |
| U1 | 大数的认识 | 完整 4 页 | `printables/unit-tests/U1_…` | `answers/U1_…-参考答案.md` |
| U2 | 角的度量 | 完整 4 页 | `printables/unit-tests/U2_…` | `answers/U2_…-参考答案.md` |
| U3 | 三位数乘两位数 | **仅 1–2 页** | `…U3_…_部分` | `answers/U3-U5_部分答案与题型重难点.md` |
| U4 | 数量关系 | **仅 1–2 页** | `…U4_…_部分` | 同上 |
| U5 | 平行四边形和梯形 | **仅 1–2 页** | `…U5_…_部分` | 同上 |

高清卷由扫描图**拆页放大**生成，内容与 JPG/PNG 一致，便于打印与核对。

## 当前示例 · 口算

| 文件 | 说明 |
| --- | --- |
| `printables/oral/oral-g4a-sprint-02min-01.docx` | 2 分钟口算冲刺（36 题） |
| `printables/oral/oral-g4a-sprint-02min-01.pdf` | 同上 PDF |
| `answers/oral-g4a-sprint-02min-01-参考答案.md` | 答案 |

## 打印建议

- 单元卷、口算纸优先打 **PDF**；要改字用 **Word**。
- A4；答案另打或做完再看 `answers/`。
- 主色天蓝：电子版卷头为蓝色；黑白打印不影响做题。

## 重新生成

```bash
python scripts/gen_unit_test_hd.py
python scripts/gen_oral_sprint.py
python scripts/gen_unit_calc_template.py
```

## 接下来

- 补上 U3–U5 第 3–4 页扫描 → 再跑高清入库  
- 按真实教材细化迷你查漏纸、错题重练纸、3/5 分钟口算变式  
