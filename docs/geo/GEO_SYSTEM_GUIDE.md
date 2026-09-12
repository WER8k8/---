# GEO 基因表达数据分析系统 — 技术文档与用户手册

## 一、系统概述

基于 NCBI GEO (Gene Expression Omnibus) 数据库的完整生物信息学分析平台，集成到优丁建材超级管理员后台。

### 技术栈
| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI |
| 数据处理 | NumPy, Pandas, SciPy, Scikit-learn |
| 可视化 | SVG (热图/火山图/PCA) + Matplotlib |
| 前端 | Vue 3 + Ant Design Vue + ECharts |
| 数据源 | NCBI E-utilities API + GEO FTP |

---

## 二、核心功能模块

### 1. 数据检索与下载
- **NCBI E-utilities 搜索**: 按关键词搜索 GEO DataSets
- **数据下载**: 从 GEO FTP 下载 SOFT 格式表达矩阵
- **演示模式**: NCBI 不可用时自动生成演示数据集 (200 基因 × 12 样本)

### 2. 数据预处理
- **清洗**: 移除全零/NaN 行
- **标准化**: 分位数标准化 (quantile) / Z-score / MinMax / Log2
- **算法参考**: R limma 包的 quantile normalization

### 3. 差异表达分析
- **统计检验**: Welch's t-test (不等方差)
- **多重假设校正**: Benjamini-Hochberg FDR
- **筛选标准**: |log2FC| > 1 且 p-adjusted < 0.05

### 4. 聚类分析
- **层次聚类**: Ward's method + Euclidean distance
- **K-means**: Scikit-learn 实现

### 5. 可视化
- **火山图**: log2FC vs -log10(p-value)，显著基因红/蓝标注
- **热图**: Top N 差异基因表达矩阵
- **PCA 降维图**: 样本分布，处理组/对照组着色

### 6. 结果导出
- **CSV**: 表达矩阵 / 差异基因列表 / 聚类结果
- **PDF 报告**: HTML 格式，含完整统计与基因列表

---

## 三、API 参考

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/v1/super-admin/geo/search?query=...` | 搜索 GEO 数据集 |
| POST | `/api/v1/super-admin/geo/download` | 下载数据集 |
| POST | `/api/v1/super-admin/geo/preprocess` | 数据预处理 |
| POST | `/api/v1/super-admin/geo/de-analysis` | 差异表达分析 |
| POST | `/api/v1/super-admin/geo/clustering` | 聚类分析 |
| GET | `/api/v1/super-admin/geo/visualization/volcano` | 火山图数据 |
| GET | `/api/v1/super-admin/geo/visualization/heatmap` | 热图数据 |
| GET | `/api/v1/super-admin/geo/visualization/pca` | PCA 数据 |
| GET | `/api/v1/super-admin/geo/export/csv` | 导出 CSV |
| GET | `/api/v1/super-admin/geo/export/pdf` | 导出 PDF 报告 |
| POST | `/api/v1/super-admin/geo/full-pipeline` | 一键全流程 |

---

## 四、用户操作指南

### 快速开始
1. 登录超级管理员后台 → 侧栏 "生信分析" → "GEO基因分析"
2. 搜索 GEO 数据集（如: `cancer`）或点击 "加载演示数据"
3. 点击 "一键全流程" 自动完成全部分析
4. 查看差异表达基因列表、火山图、PCA 图
5. 导出 CSV/PDF 报告

### 使用真实 GEO 数据
1. 在 NCBI GEO 搜索目标数据集 GDS ID
2. 在搜索框输入 GDS ID
3. 系统自动下载并解析表达矩阵
4. 后续分析流程同演示模式
