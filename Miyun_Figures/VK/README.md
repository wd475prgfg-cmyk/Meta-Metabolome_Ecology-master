# 密云 VK 图

横轴O/C，纵轴H/C，按原始元素数计算。每组每个分子式一个点，不按峰强加权。相同比值的不同分子式可重叠，不对坐标加抖动。

- 01_VK_all_molecules：m/z200–900、峰强>0后按分子式合并，尚未筛N/H/C。Lake 5214、Sediment 4923、Groundwater 6286个。灰色横线仅表示H/C=1.5筛选边界，不是物质分类边界。
- 02_VK_network_filtered：进一步筛N>0且H/C<1.5的实际网络输入。Lake1828、Sediment1595、Groundwater2419个。
- 03_VK_Lake_candidates：灰色为Lake背景，蓝色圆点是地下水来源候选19个，橙色三角是沉积物来源候选6个；均在Lake检出。保留既有19+6规则，不改用17或双规则交集10个。

本目录preview_vk为版式预览。云端缺少宋体和Times New Roman，预览使用Noto Serif CJK JP和Liberation Serif；不是指定字体成品。正式脚本会使用用户自己的两款字体。

## 在用户服务器正式绘制

把plot_vk.py和vk_plot_data.xlsx放入 /home/h3057/cxy/Miyun-N/picture/，沿用已有fonts/simsun.ttc和fonts/times.ttf：

```bash
cd /home/h3057/cxy/Miyun-N/picture
python3 plot_vk.py --data vk_plot_data.xlsx --font fonts/simsun.ttc --latin-font fonts/times.ttf --out figures_vk
```

若只使用服务器已经存在的two_figures_plot_data.xlsx，也支持绘制“筛后网络VK”和“筛后Lake背景+候选VK”，但不能伪装成完整数据分布：

```bash
python3 plot_vk.py --data two_figures_plot_data.xlsx --font fonts/simsun.ttc --latin-font fonts/times.ttf --out figures_vk_filtered
```

代码从分子式计算缺少的O/C，不需要重新运行转化分析。不从VK区域直接判定具体化合物结构、反应或来源贡献。原始输入数据见Excel/CSV。plot_metadata.json记录实际使用字体与分子式数量。
