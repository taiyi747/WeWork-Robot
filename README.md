# AI WeWork Robot

AI WeWork Robot是一个基于Python的企业微信机器人，能够接入GPT、Gemini等大型语言模型。默认配置为Gemini-Pro，它可以帮助企业自动化处理信息，提供智能回复等功能。

## 特性

- 自动回复消息
- 接入多种大语言模型
- 支持自定义消息处理逻辑
- 基于企业微信应用API
- SLA99.99999999999%

## 使用环境

- Python 3.9+
- 企业微信管理员

## Quick Start

### 企业微信后台

登录企业微信管理后台（[注册企业微信]([注册企业微信-帮助中心-企业微信 (qq.com)](https://open.work.weixin.qq.com/help2/pc/15422))）

![](https://ooo.0x0.ooo/2024/01/13/OvMqRb.png)
![](https://ooo.0x0.ooo/2024/01/13/OvM59l.png)
创建一个应用
![](https://ooo.0x0.ooo/2024/01/13/OvMWds.png)
![](https://ooo.0x0.ooo/2024/01/13/OvMoFP.png)
点击设置API接收
![](https://ooo.0x0.ooo/2024/01/13/OvMkaK.png)
确保你已经安装了Python环境，然后执行以下命令来安装AI WeWork Robot：

```bash
git clone https://github.com/taiyi747/WeWork-Robot.git
cd WeWork-Robot
pip install -r requirements.txt
```




# Tips

如你所见GitHub上大部分使用企业微信的代码，都在一两年，甚至三四年前断更
企业微信官方的仓库加解密所用代码也不适用于python3（新的加解密代码来源于GitHub大佬仓库）
这是一条完全符合微信规定的接入方式，另外学业繁忙（有事提issues）

