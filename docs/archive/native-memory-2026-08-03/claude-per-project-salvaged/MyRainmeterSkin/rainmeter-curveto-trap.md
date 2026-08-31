**Rainmeter Shape Path 的 `CurveTo` 是三次贝塞尔, 参数顺序与 SVG 完全相反:**
- Rainmeter: `CurveTo endX,endY, control1X,control1Y, control2X,control2Y` (终点在前, 控制点在后)
- SVG path: `C control1x,control1y control2x,control2y endx,endy` (控制点在前, 终点在后)

官方例: `Path MyPath = 35,39.39 | CurveTo 19,54.28, 35,47.62, 27.84,54.28`
= 从(35,39.39) 画到终点(19,54.28), 控制点(35,47.62)和(27.84,54.28)。

**踩坑**: 把 v5 SVG 纹章(Dock.ini 的 Undertaker斗篷/肋骨/镰刃, Fox脸, Snake身)
直接按 SVG 思维转成 Rainmeter CurveTo → 参数顺序错 → 曲线渲染严重走样。
首轮落地(commit 0eb6038)就犯了这个错, 需修正。
