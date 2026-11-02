# Shoreline 分子转化结果

这是根据上传的 `Meta-Metabolome_Ecology-master.zip` 和 PPT 第 1–5 页完成的分子转化结果。22 个样本共得到 91,379 条逐样本峰对。

- [合并 Excel 表](All_Samples_Annotated_Transformations.xlsx)：23 列，包含质量、元素、分子式、类别、质量差和转化名称。打开文件页面后选择 **Download raw file** 下载。
- [全部结果和代码 ZIP](Molecular_Transformation_Results.zip)：包含逐样本 CSV、注释表、汇总、说明和运行代码。
- [样本汇总](sample_summary.csv)：22 个样本的匹配峰对数，可以在 GitHub 上直接预览。
- [运行代码](run_molecular_transformations.py)：可在 GitHub 上直接查看。

输入使用压缩包已处理的 Data/Mol 文件以及 `Transformation_Database_07-2020.csv`。匹配遵循原 R 脚本的 ±0.000010 Da 闭区间规则；同一峰对有多个匹配时采用数据库中最后一条。未执行 PPT 第 6 页以后的 RI、marker 和溯源分析。

## 文件校验 SHA-256

- `All_Samples_Annotated_Transformations.xlsx`：`8a3cf070253c68afc6e2a877dd32391ebe97adae6eb1fec750a28787e1336fe1`
- `Molecular_Transformation_Results.zip`：`f16b1a74b489eafb1ebb7b1234b3729b1b35a13fe718af0585bdb110ecc9185b`
- `run_molecular_transformations.py`：`e46c32f864f4225c685a88c22a1b83f5cae48427a1c77c793939e656dc049dfc`
- `sample_summary.csv`：`df2bba6707363e630079aba93f4b090e046ca74b18578eea6f7abcee8bf0f995`
