# 管理台签发表单：避开 macOS 通讯录自动填充

## 现象

「使用者姓名」一类字段在 macOS / Safari（及部分 Chromium）会弹出 **通讯录（Contacts）** 自动填充。`autocomplete="off"` 经常无效。提交后系统浮层还可能残留在下一页（例如 Key 已生成页）上方。

## 禁止做法

不要用额外的 honeypot（假 name/email）输入框挡自动填充。本站表单是底边线样式，假隐藏输入仍会画出多余输入行，用户会看到「多了两个框」。

## 推荐组合

- 首焦前 `readonly`，focus 后再可编辑  
- `autocomplete="one-time-code"`（或其它非 name 语义）  
- 字段 `name` 避免 `name` / `displayName` 等通讯录敏感名（可用产品自定义名）  
- 提交成功后 `blur` 再切换到结果页，给 WebKit 一点时间收起浮层  

实现参考组件名：NonContactTextInput。E2E 填写前须先 click 再 fill（只 fill 可能打在仍只读的框上）。
