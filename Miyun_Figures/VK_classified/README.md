# 三组 VK 分类图

本包仅包含地下水、湖水、沉积物三个组的VK图，不包含逐样本12面板图。

主图从左到右：Groundwater地下水6286式；Lake湖水5214式；Sediment沉积物4923式。图中仅保留组名，不显示a/b/c面板字母。每个面板内按经验VK区域着色，统一灰色虚线框、图例和坐标。点按分子式计数，不按峰强加权。

主图为实测m/z200–900且峰强>0后组内合并去重的分子式，没有先筛N/H/C。另提供独立的N>0且H/C<1.5网络输入版，分子式数量依次为2419、1828、1595；不能把筛后图当作完整组成分布。

## 经验分区边界

参考图片未提供数值边界或原文，以下是本次明确采用的操作性规则，不能声称与原文参数完全一致。`-like`表示“样”区域，不能单凭VK位置认定具体结构或生物来源。

|区域标签|中文|O/C|H/C|
|---|---|---|---|
|Lipids-like|脂质样|0≤O/C<0.30|1.50≤H/C≤2.00|
|Aliphatic/Peptides-like|脂肪族/肽样|0.30≤O/C<0.67|1.50≤H/C≤2.20|
|Lignin-like|木质素样|0.10≤O/C<0.67|0.70≤H/C<1.50|
|Carbohydrates-like|碳水化合物样|0.67≤O/C≤1.20|1.50≤H/C≤2.40|
|Unsaturated hydrocarbons-like|不饱和烃样|0≤O/C<0.10|0.70≤H/C<1.50|
|Condensed aromatics-like|缩合芳香物样|0≤O/C<0.67|0.20≤H/C<0.70|
|Tannins-like|单宁样|0.67≤O/C≤1.20|0.50≤H/C<1.50|
|Unclassified|未分类|不属于上述区域|不属于上述区域|

边界无重叠，按表内半开/闭区间判断。坐标上限按实际数据扩展至覆盖全部分子，不因参考图H/C上限约2.5而隐藏更高H/C的实测分子。虚线框的画线本身没有开/闭边界含义，以规则表和代码为准。

## 字体与运行

preview_classified_vk为布局预览，因为云端缺少宋体和Times New Roman，实际使用Noto Serif CJK JP与Liberation Serif。它不是指定字体的正式成品；字体记录见plot_metadata.json。

下载本包后解压到服务器 /home/h3057/cxy/Miyun-N/picture/VK_classified/，沿用已有字体：

```bash
cd /home/h3057/cxy/Miyun-N/picture/VK_classified
python3 plot_vk_classified.py --font ../fonts/simsun.ttc --latin-font ../fonts/times.ttf
```

生成figures_vk_classified目录，各有PNG（300dpi）、PDF及SVG。PDF嵌入字体，SVG文字转路径。脚本只需要matplotlib和Python标准库，group_molecules.csv是必需绘图数据，请勿只上传脚本。

主输入group_molecules.csv包含原元素数及质量，输出group_molecules_classified.csv带O/C、H/C和区域归类，VK_region_statistics.csv为逐面板类别数量及百分比。校验清单见SHA256SUMS.txt。
