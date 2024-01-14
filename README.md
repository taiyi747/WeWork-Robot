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

登录企业微信管理后台（[企业微信注册](https://open.work.weixin.qq.com/help2/pc/15422)）

![](https://ooo.0x0.ooo/2024/01/13/OvMqRb.png)
![](https://ooo.0x0.ooo/2024/01/13/OvM59l.png)

创建一个应用
![](https://ooo.0x0.ooo/2024/01/13/OvMWds.png)
![](https://ooo.0x0.ooo/2024/01/13/OvMoFP.png)

点击设置API接收
![](https://ooo.0x0.ooo/2024/01/13/OvMkaK.png)
![](https://ooo.0x0.ooo/2024/01/13/OvMLeI.png)
从这里获取secret，会发到手机，保存起来
### Python
确保你已经安装了Python环境，然后执行以下命令来安装AI WeWork Robot：

```bash
git clone https://github.com/taiyi747/WeWork-Robot.git
cd WeWork-Robot
pip3 install -r requirements.txt
```

编辑config.py

```
sToken = 对应上面保存的Token
sEncodingAESKey = 对应上面保存的EncodingAESKey
sCorpID = 对应企业微信管理后台——我的企业下面的企业ID
sCorpsecret= 对应应用的secret
gemini_key = 从谷歌获取的key
```
保存，启动程序
```bash
python3 main.py
```

回到应用管理
![](https://ooo.0x0.ooo/2024/01/13/OvMEGD.png)

保存提示成功即可，找到企业可信IP，把你的ip添加进去
![](https://ooo.0x0.ooo/2024/01/13/OvMUyB.png)

最后，当年你随机问机器人一个问题，成功回复即成功
![](https://ooo.0x0.ooo/2024/01/13/OvMG3F.png)

# Tips
1. 如你所见GitHub上大部分使用企业微信的代码，都在一两年，甚至三四年前断更
2. 企业微信官方的仓库加解密所用代码也不适用于python3（新的加解密代码来源于GitHub大佬仓库）
3. 这是一条完全符合微信规定的接入方式，另外学业繁忙（有事提issues）

