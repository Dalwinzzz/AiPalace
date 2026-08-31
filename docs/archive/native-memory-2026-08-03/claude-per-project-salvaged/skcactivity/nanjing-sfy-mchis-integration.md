南京建邺·江苏省妇幼健康信息系统（臻鼎 mchis，Apache Axis2 SOAP，端点 `http://IP:端口/mchis-controller/services/Mchis`）的对接通用口径——2026-07 落地「儿童身高体重评价」时实测定论，**同一 mchis 系统的其他接口可直接复用**：

- **传输**：SOAP 1.1，`targetNamespace=http://webservice.zhending.com`，schema `elementFormDefault=qualified`（参数元素必须带命名空间前缀 `m:`）。注意：`.../mchis-web/` 是前端页面、不是对接端点；`?wsdl` 也受签名校验。
- **签名**：login 与业务调用的 URL 都要带 `?sign=base64({"sign":MD5(系统密钥+时间+随机数),"time":..,"nonce":..,"orgCode":..})`；三值**直接拼接无分隔符**、time 为**毫秒时间戳**、nonce 随机数字。系统密钥/orgCode 由妇幼提供；`separator` 非空即"认证失败，签名错误"。
- **登录**：`login(loginCode,password)` operation，返回 `data.token` **直接用**——服务端**未实现** `getRealToken`（调了报 does not implement），别走换取链路。
- **业务 operation**：`saveData`/`getData`/`deleteData` 都是 `(token, json)`，json=`{source,remark,operate,data}`，由 `operate` 区分业务。
- **儿童身高体重评价**：WSDL **无** `calPhysiqueEvaluate` operation，实测走 **`getData(token,json)`**、json 内 `operate=calPhysiqueEvaluate`；返回 data 的评价系数是**字符串**、且多出 `heightFlag/weightFlag/heigWeigFlag/heightWeightFatEval` 等扩展字段，故**原样透传裸 data**（JSONObject），不强类型映射。

**落地**：代码在 `com.iktapp.skc.activity.third.njsfy`（见 [[third-party-integration-package]]），正式接口 `POST /physicalAppointment/njsfy/physique/evaluate`，配置前缀 `njsfy.mchis.*`，最小必配 5 项：`enabled=true`/`endpoint`/`system-key`/`org-code`/`login-code`/`password`（其余默认值即实测正确值）。全过程与最终态归档在 `docs/njsfy-省妇幼身高体重评价对接方案.md`。

**Why**：签名/登录/token/operation 口径是整个 mchis 系统通用的，对接其孕产妇/计生等其他接口时可省去重新探测。
**How to apply**：新接口通常只需改 `soap.cal-method`（走哪个 operation）+ json 的 `operate` + 入参/返回结构；签名/登录/token 层不动。
