[English](https://github.com/jayjoolee/photo-trip-timeline/blob/main/README.md) | 简体中文 | [한국어](https://github.com/jayjoolee/photo-trip-timeline/blob/main/README.ko.md)

<h1 align="center">photo-trip-timeline</h1>

<p align="center">
从你的 Apple 照片中自动识别每一段旅行，生成可分享的 Markdown 旅行时间线 ——<br>
<b>只含地名，你的 GPS 坐标永远不会离开你的 Mac。</b>
</p>

<p align="center">
<a href="https://github.com/jayjoolee/photo-trip-timeline/actions/workflows/ci.yml"><img src="https://github.com/jayjoolee/photo-trip-timeline/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
<a href="https://github.com/jayjoolee/photo-trip-timeline/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
<a href="https://github.com/jayjoolee/photo-trip-timeline/blob/main/CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs welcome"></a>
</p>

<p align="center">
<img src="https://raw.githubusercontent.com/jayjoolee/photo-trip-timeline/main/assets/demo.gif" alt="phototrips --demo" width="800">
</p>

你去旅行，拍了几百张照片 —— 可游记却总也写不出来，因为整理太麻烦。其实你的 iPhone
已经为每张照片打上了**时间**和**位置**，Apple 照片也早已把坐标转换成了**地名**。
`photo-trip-timeline` 在本地读取这些信息，判断哪些照片属于同一段旅行，并写出一份清晰的
逐日时间线 —— **而且分享出去的文件里绝不会出现任何坐标。**

**[安装](#安装) · [快速开始](#快速开始) · [隐私设计](#隐私设计) · [工作原理](#工作原理)**

```markdown
# Photo Travel Timeline

## Busan 2-day trip — 2024.05.03–05.04 (2 days, 142 photos)
Haeundae Beach → Gamcheon Culture Village → Jagalchi Market
- Day 1 (05.03): Haeundae Beach — 51 photos
- Day 2 (05.04): Gamcheon Culture Village, Jagalchi Market — 91 photos
```

*（用 `phototrips --demo` 立刻试试 —— 无需照片库。中文输出用 `--lang zh`。）*

## 功能特性

- 🔒 **坐标永不离开你的 Mac** —— `timeline.md` 只含地名；写入时的断言会在任何形似
  经纬度的字符串混入时直接中止运行。
- 🏠 **失败即停的住所识别** —— 若无法高置信度地确定你的住所，工具会停下来询问，而不是
  擅自猜测、从而泄露一个接近住所的位置。
- 🗺️ **自动行程切分** —— 以住所为基准的边界（回家、间隔、航班级跳变、陆路长距离移动）；
  海外旅途中安静的休息日不会把一段旅行切开。
- 📍 **逐日路线** —— 将每段旅行中到访的不同地点聚类，排成可读的路线，并标注每天的照片数。
- 🌏 **多语言输出** —— `--lang en | ko | zh` 切换时间线语言；本 README 提供英文、简体中文、한국어。
- 🧪 **值得信赖** —— 算法核心不依赖 `osxphotos`，由 31 个测试在合成数据上覆盖，无需 Mac。

## 安装

```bash
git clone https://github.com/jayjoolee/photo-trip-timeline
cd photo-trip-timeline
pip install -e .
```

需要装有 Apple 照片 App 的 macOS、Python ≥ 3.10，以及 `osxphotos`（会自动安装）。
已在 Apple 照片库版本 5001 上验证；`osxphotos` 也能读取其他版本。

## 快速开始

```bash
# 自动识别住所，写出 ./output/{timeline.md, trips.json}
phototrips

# 立即查看示例输出，无需读取你的照片库：
phototrips --demo
```

## 用法

```bash
phototrips --lang zh                 # 中文时间线（en | ko | zh；默认 en）
phototrips --since 2022-07-01        # 只处理某日期及之后的照片
phototrips --library /path/to/X.photoslibrary

# 若无法高置信度识别住所，工具会拒绝猜测。二选一：
phototrips --home-lat 37.5665 --home-lon 126.9780   # 直接告诉它你的住所
phototrips --no-coords                              # 或只输出地名

phototrips --include-names           # 在 trips.json 中包含人物姓名（默认关闭）
```

多组 `--home-lat/--home-lon`（配合可选的 `--home-from/--home-until`）可处理这段时间内搬过家的情况。

它会写出两个文件：

- **`timeline.md`** —— 可分享、可读的时间线。**只含地名，绝无坐标**，可放心粘贴进博客草稿。
- **`trips.json`** —— 结构化记录（已被 gitignore），作为博客草稿步骤的输入。

### 博客草稿

`phototrips draft` 会把一段旅行变成一个**提示包（prompt pack）**：一个 Markdown 文件，
打包该旅行的事实（日期、逐日路线、重点地点、该放哪些照片）和一份写作风格指南，可直接粘贴进
Claude / ChatGPT 生成草稿。无需 API key，且提示包只含地名 —— 绝无坐标。

```bash
phototrips draft --trip auto                 # 照片最多的那段旅行
phototrips draft --trip 2025-02-24-rome       # 按 id 指定某段旅行
phototrips draft --all --style my-voice.md    # 所有旅行，按你自己的风格
phototrips draft --lang en                     # 提示包语言（ko | en；默认 ko）
```

用 `--style path/to/your-style.md` 注入你自己的文风；内置默认风格在 `styles/default.md`。
提示包写入 `output/drafts/`（已被 gitignore）。

## 隐私设计

这个工具会读取你的照片、知道你住在哪里。它从设计上就为保护隐私而建：

- **`timeline.md` 绝不含数字坐标** —— 只含地名，由写入时断言强制保证。
- **住所识别失败即停** —— 置信度低时停下询问，而非擅自猜测并泄露接近住所的坐标。
- **`trips.json`、照片库、`output/` 均被 gitignore**，并有 `pre-commit` 钩子阻止提交它们或任何形似坐标的字符串。
- **人物姓名为可选项**（`--include-names`）；默认只记录数量。
- **无网络请求** —— 反向地理编码使用 Apple 本地的地名；不发起任何外部调用。

详见 [SECURITY.md](https://github.com/jayjoolee/photo-trip-timeline/blob/main/SECURITY.md)。安装提交防护：`pip install pre-commit && pre-commit install`。

## 为什么不用现成的工具？

不少项目能从照片提取 GPS 或在地图上打点（[osxphotos](https://github.com/RhetTbull/osxphotos)、
[mappics](https://github.com/antodippo/mappics) 等）。但它们都没有回答旅行博主真正关心的问题：
*“哪些照片是同一段旅行，这段旅行逐日都去了哪里？”* —— 而且不会把你的住所标在地图上。

## 工作原理

1. **提取**（`osxphotos`）—— 直接从照片库读取每张照片的时间、GPS 和 Apple 的地名层级。
   不做外部地理编码，全程本地。
2. **切分为旅行** —— 关键步骤。照片是稀疏的，单纯的密度聚类找不到行程边界。这里把“旅行”
   定义为离家在外的时间；住所附近的日常照片只作为边界，不构成旅行。在一段在外的时间里，
   仍会按长间隔、航班级跳变和陆路长距离移动进行切分。
3. **行程内地点聚类**（DBSCAN）—— 找出你到访的不同地点，并排成路线。
4. **命名与汇总** —— 由地点推导行程名称，挑选代表性照片（基于 Apple 本地的美学评分），
   渲染时间线与 JSON。

只有 `extract.py` 接触 `osxphotos`；其后的一切都在普通数据上运行，因此测试套件无需 Mac 即可覆盖整个算法。

## 配置

各项阈值（离家距离、间隔小时数、跳变/长途距离、地点聚类半径等）以带注释的默认值写在
`config.py` 中，并可从命令行覆盖。运行 `phototrips --help` 查看完整列表。

## 参与贡献

欢迎 PR —— 详见 [CONTRIBUTING.md](https://github.com/jayjoolee/photo-trip-timeline/blob/main/CONTRIBUTING.md)。
`pytest` 无需 Mac 或照片库即可运行整套测试。**切勿在 issue 或 PR 中粘贴真实坐标** ——
请用 `phototrips --demo` 或 `tests/` 中的合成数据复现。

## 路线图

- **博客草稿** ✅ —— `phototrips draft` 已上线（见上文）。下一步：配置 API key 后可直接调用
  LLM 生成，以及按旅行导出照片。
- 本地化的行程*标题*（目前为英文）、可选的地图输出（`folium`）、PyPI 发布。

## 许可证

MIT —— 见 [LICENSE](https://github.com/jayjoolee/photo-trip-timeline/blob/main/LICENSE)。

---

<sub>英文 `README.md` 为权威版本；翻译可能滞后。</sub>
<!-- translated from README.md -->
