# 密云地下水与湖泊分子转化结果

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

各包内的 README 说明了输入、质量筛选、注释字段和局限性。源文件没有 C13 同位素指示列，因而无法核实同位素过滤；源文件没有 Class 列，注释表用 None 占位。没有进行 RI、marker 或溯源分析。
