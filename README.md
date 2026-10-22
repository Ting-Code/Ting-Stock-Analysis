# Ting-Stock-Analysis

A 股单票复盘页生成器：输入股票名称或代码，自动拉取行情与季报，生成可在浏览器打开的交互式 HTML 复盘页。

定位是**个人学习 / 自媒体内容生产辅助**（科普与历史复盘），不是荐股或交易系统。

## 能做什么

第一版聚焦**单票**（板块后续再做），一次生成包含：

| 模块 | 内容 |
|------|------|
| A. 行情 K 线 | 前复权日线；页内切换日 / 周 / 月 / 季；可缩放拖动 |
| B. 季度财报 | 营收、归母净利、扣非净利（累计报表已拆成单季） |
| C. 估值序列 | 以季报发布日**次月月末收盘价**为锚，计算 TTM 扣非动态 PE，并标注 PB、股息率；与现价分位对比 |

生成结果为独立 HTML，方便跨端预览，也适合作为后续「母版 + 数据包」内容工作台的展示壳。

## 快速开始

### 环境

- Python 3.10+
- 网络可访问 BaoStock、东方财富相关接口（经 AkShare）

```bash
pip install -r requirements.txt
```

### 生成复盘页

```bash
python scripts/generate_stock_html.py 宁德时代
# 或
python scripts/generate_stock_html.py 300750
```

输出文件在 `output/` 目录（已加入 `.gitignore`，不会提交到仓库），用浏览器打开即可。

可选：早期 Streamlit 试做入口

```bash
streamlit run app.py
```

## 目录结构

```text
Ting-Stock-Analysis/
├── docs/方案.md              # 产品方向与分析口径
├── scripts/generate_stock_html.py
├── src/
│   ├── market.py             # BaoStock 日线与周期重采样
│   ├── fundamentals.py       # 季报 / 分红（AkShare）
│   ├── valuation.py          # TTM 扣非 PE、PB、股息率
│   ├── render_report.py      # HTML 母版渲染
│   └── ...
├── output/                   # 本地生成物（不入库）
├── app.py                    # Streamlit 试验入口
└── requirements.txt
```

## 关键口径（已确认）

- 行情：**前复权**
- 估值锚定价：季报 `NOTICE` 日所在月的**下一个自然月**，取该月**最后一个交易日收盘价**
- 动态 PE：锚定日价格 / 每股 **TTM 扣非**（近 4 个单季扣非之和）
- 股息率：近 12 个月已实施现金分红 / 价格
- 范围：第一版只做单票

更完整的产品方案见 [`docs/方案.md`](docs/方案.md)。

## 数据来源

- 行情：[BaoStock](http://baostock.com/)
- 财报 / 分红：东方财富（经 [AkShare](https://github.com/akfamily/akshare)）

接口与字段可能变更，结果请与交易所 / 巨潮等官方披露交叉核对。

## 路线图（简）

- [x] 单票 HTML 复盘页（K 线 + 季报 + 估值序列）
- [ ] 模板化文字解读 / 口播要点区
- [ ] 年限筛选与更多图表积木
- [ ] 板块分析（第二版）
- [ ] 本地数据缓存，减少重复拉取

## 给协作者 / AI

别人克隆本仓库后，用 Cursor（或其他能读仓库的 AI）即可按同一套方式出页：

1. 打开项目，确保 AI 能读到根目录 **`AGENTS.md`**（以及 `.cursor/rules/`）。  
2. 安装依赖：`pip install -r requirements.txt`  
3. 对 AI 说（可直接复制）：

```text
请阅读 AGENTS.md 与 docs/方案.md，用本仓库现有流水线为「宁德时代」生成复盘 HTML，
不要从零手写页面。生成后告诉我 output 路径，并简述 PE/PB/股息率与口径。
```

4. 或本地直接跑：`python scripts/generate_stock_html.py <名称或代码>`

AI 应复用 `src/*` 流水线与 HTML 母版，而不是每次新写一页静态假数据。更细的约定见 [`AGENTS.md`](AGENTS.md)、[`docs/AI协作指南.md`](docs/AI协作指南.md)。

## 免责声明

本项目仅供学习、研究与内容复盘参考，**不构成任何投资建议**。股市有风险，决策请独立判断并自行承担责任。作者不对依据本项目信息产生的任何盈亏负责。

## 使用说明

本仓库为个人学习与内容复盘用途，**不授权商用**。未经作者书面许可，请勿用于商业产品或付费服务。
