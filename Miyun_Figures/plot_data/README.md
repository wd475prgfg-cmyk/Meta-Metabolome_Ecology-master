# 精简版绘图：中文宋体，英文及数字Times New Roman

本次只改变图形排版，不改变任何数据、候选名单、色阶或计数。

删除所有整句说明、脚注、总标题、右侧候选数量与峰强说明段落；保留轴标签、图例、分子式、数值和必要色标。热图单元格数值依然是原始峰强/10^6，颜色依然是log10原始峰强，未检出仍为灰色和横线；这些解释放到图注中，不再写进图内。

## 服务器运行

```bash
cd /home/h3057/cxy/Miyun-N/picture
mkdir -p fonts
# 将自己的宋体simsun.ttc和Times New Roman的times.ttf放入fonts/
python3 render_two_figures.py --data two_figures_plot_data.xlsx --font fonts/simsun.ttc --latin-font fonts/times.ttf --out figures_clean
```

默认会自动查找fonts目录和系统中已安装的两款字体；--font/--latin-font可省略。PDF嵌入字体，SVG文字转路径，避免换电脑后字体被替换。Matplotlib优先用Times New Roman绘制英文/数字，中文逐字回退宋体。

当前云端缺少两款指定字体，已核验精简布局，版式预览在 ../clean_preview 中，采用Noto Serif CJK JP与Liberation Serif，**不是正式宋体/TNR成品**。如需在缺少字体时查看排版，必须显式加--preview，且查看font_status.json确认实际字体。正式模式不会静默使用替代字体。

实际SFTP服务器并未由助手登录或改写；GitHub提供更新脚本，由用户在服务器终端下载执行。

---

# 两张图的原始作图数据

## 在服务器直接画这两张图（新增）

render_two_figures.py才是绘图脚本，export_two_figures_data.py是上游分析环境的数据导出工具；独立服务器不要运行后者。

如果已上传Excel，把render_two_figures.py和two_figures_plot_data.xlsx放在同一目录，执行：

```bash
python3 -m pip install numpy matplotlib openpyxl
python3 render_two_figures.py --data two_figures_plot_data.xlsx
```

如果解压了整个CSV数据包，在该目录执行：

```bash
python3 render_two_figures.py
```

默认在数据旁边的figures目录生成两张图，每张各有PNG/PDF/SVG。服务器不弹图窗是正常的。新版正式出图要求宋体和Times New Roman；缺少时会明确报错。将simsun.ttc和times.ttf放入fonts目录，或显式指定：

```bash
python3 render_two_figures.py --data two_figures_plot_data.xlsx --font /path/to/simsun.ttc --latin-font /path/to/times.ttf
```

脚本不依赖原分析服务器/workspace目录。已实际测试从Excel读取并生成两图。

下载 two_figures_plot_data.xlsx 即可，10个sheet也分别提供CSV。

## 图1：连接次数分布+RI/marker柱状图

- 左图：01_degree_percent.csv；第一列是分类，Lake/Sediment/Groundwater三列是百分数，直接做分组柱状图。百分数已为0–100，不要再次乘100。
- 02_degree_counts.csv是对应分子数，09_degree_long.csv是原始长表，04_all_molecule_degrees.csv是每个分子实际连接数，可独立重算分布。
- 右图：03_RI_marker_pools.csv，取RI_pool_k_le_1及marker_pool_k_eq_0两列。对应Lake 215/117、Sediment 157/94、Groundwater 264/138。marker是RI子集，两柱不能相加。

## 图2：Lake候选峰强热图

- 05_heatmap_raw.csv：原始峰强整数矩阵，行顺序完全对应截图，前19行地下水、后6行沉积物。
- 06_heatmap_log10.csv：颜色矩阵，使用这张表画热图，按全图共同最小/最大值确定色阶，不作行归一化。
- 07_heatmap_labels.csv：格内文字，原始峰强除以10^6，保留两位小数。
- 空白表示未检出，显示灰色和横线；不能填0后取log10。
- 08_original_peak_records.csv：25个分子在来源和Lake中的筛后原始峰记录，包含样本名、实测m/z、原始峰强、来源工作簿、sheet、Excel行号。CSV保留精确十进制文本。

本交付复现用户截图19+6的已有图，不使用后续17个或双规则交集10个替换。候选零连接指来源筛后中位质量网络；Lake检出不是稳定性验证。峰强未经归一化，不解释为来源氮贡献比例。
