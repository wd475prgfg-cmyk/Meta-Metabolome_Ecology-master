# 密云地下水合并后重算

当前地下水结果：[查看文件与计算说明](GW_合并后重算/README.md) · [下载 Excel](GW_合并后重算/地下水六样合并_N大于0_HC小于1.5_转化次数.xlsx) · [下载结果与代码 ZIP](GW_合并后重算/地下水六样合并_N大于0_HC小于1.5_转化次数_结果与代码.zip)

六个地下水样本先按分子式合并，以已检出实测 m/z 的中位数代表每式，沿用 200–900 Da 范围，再筛选 N > 0 且 H/C < 1.5，最后只在筛后集合中计算一次转化网络。质量差匹配用整数实现 ±0.000010 Da 闭区间，避免边界浮点漏匹配。

2,419 个分子式、39,904 个匹配峰对；转化次数 ≤1 为 263 个（=0 为 138 个，=1 为 125 个）。这里的次数限定于筛后的网络；候选尚未与其他来源端元排重，未确定端元独有 marker。Lake 为受体，本轮不参与地下水网络。

上一版 `GW_候选marker` 下载目录已按用户要求移除。下方及其他旧目录保留原逐样本计算资料；本轮地下水统计请使用上方“合并后重算”文件。

## 原逐样本分子转化资料

基于用户提供的地下水工作簿与 Lake.zip，按原转化数据库和 ±0.000010 Da 质量差规则计算。仅执行分子转化：地下水 6 个样本，514,654 个匹配峰对；湖泊 50 个样本，5,637,768 个匹配峰对。

下载下列 6 个 ZIP，在 Windows 上**全部解压到** `C:\Users\86152\Desktop\氮素溯源\2026.10开题\miyun`。每个湖泊包含 10 个样本的原始 7 列和带分子式的 23 列逐样本 CSV；GW 包含 6 个地下水样本。CSV 可用 Excel 打开。

| 文件 | 样本数 | 匹配峰对 | 大小 |
| --- | ---: | ---: | ---: |
| [Miyun_GW_Transformations.zip](Miyun_GW_Transformations.zip) | 6 | 514,654 | 22.1 MB |
| [Miyun_Lake_Transformations_part01_of_05.zip](Miyun_Lake_Transformations_part01_of_05.zip) | 10 | 1,154,098 | 49.4 MB |
| [Miyun_Lake_Transformations_part02_of_05.zip](Miyun_Lake_Transformations_part02_of_05.zip) | 10 | 1,159,772 | 49.2 MB |
| [Miyun_Lake_Transformations_part03_of_05.zip](Miyun_Lake_Transformations_part03_of_05.zip) | 10 | 998,645 | 42.0 MB |
| [Miyun_Lake_Transformations_part04_of_05.zip](Miyun_Lake_Transformations_part04_of_05.zip) | 10 | 1,121,097 | 47.7 MB |
| [Miyun_Lake_Transformations_part05_of_05.zip](Miyun_Lake_Transformations_part05_of_05.zip) | 10 | 1,204,156 | 51.1 MB |

[查看 56 个样本的汇总](sample_summary.csv) · [下载汇总 Excel](sample_summary.xlsx) · [查看运行代码](run_miyun_transformations.py) · [查看分包样本对应表](bundle_manifest.csv)

各包内的 README 说明了输入、质量筛选、注释字段和局限性。源文件没有 C13 同位素指示列，因而无法核实同位素过滤；源文件没有 Class 列，注释表用 None 占位。这些原逐样本转化包本身未进行 RI、marker 或溯源分析。
