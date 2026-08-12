# 接入指南页：步骤截图与正文同宽

## 目标

接入指南里的截图外框，应与同页架构双栏、下方代码模板的左右边缘对齐，而不是缩在步骤编号右侧。

## 结构

- 步骤编号与说明放在「步骤头」一行网格里。  
- 截图 `figure` 作为步骤的**直接子节点**，宽度 100%，不要嵌在编号列旁的正文列里。  
- 可用 `next/image`，但样式上强制 `width: 100%; height: auto`。

## CSS 陷阱

全局 `.guide-body ol { padding-left: … }` 比 `.guide-steps { padding: 0 }` 更具体，会把整个步骤列表（含截图）整体缩进。必须再写：

`.guide-body ol.guide-steps { padding-left: 0; }`

不要依赖负 margin 把图「拉回」——易与图片组件、变量继承叠出仍不对齐的结果。
