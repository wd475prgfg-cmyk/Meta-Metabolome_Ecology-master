# 此批氮浓度图的字体

`NotoSansCJK_figure_fonts.zip` 包含 `NotoSansCJK-Regular.ttc`、`NotoSansCJK-Bold.ttc` 和字体许可证。字体来自执行环境安装的 `fonts-noto-cjk` 软件包，许可证为 SIL Open Font License 1.1。此批图的中文预览使用该 TTC 的 Noto Sans CJK 字形；Matplotlib 注册 Regular 文件后识别的默认面是 Noto Sans CJK JP。

这与用户服务器中的 `fonts/simsun.ttc`（宋体）和 `fonts/times.ttf`（Times New Roman）不同。若需要按宋体和 Times New Roman 重画图，应在绘图代码中显式指定这两个文件。
