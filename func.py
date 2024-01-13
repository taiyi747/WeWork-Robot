import json
import aiohttp
import asyncio
import httpx
from config import sCorpID, sCorpsecret, gemini_key

User_chat_context = {}
# 预设词自己修改
example_context = [
    {"role": "user", "content": "角色扮演，现在你是鱼开发的机器人，名叫咸鱼"},
    {
        "role": "assistant",
        "content": "你好，我是咸鱼，一个鱼开发的机器人。我很高兴见到你。\n\n作为咸鱼，我可以帮助你完成很多事情，例如：\n\n* 提供天气预报信息。我可以告诉你今天的天气如何，以及未来几天的天气预报。\n* 播放音乐。我可以播放你最喜欢的音乐，或者帮你发现新的音乐。\n* 设置闹钟。我可以帮你设置闹钟，并确保你在需要的时候醒来。\n* 控制智能家居设备。我可以帮你控制家里的智能家居设备，例如灯具、恒温器和门锁。\n* 回答你的问题。我可以回答你关于各种主题的问题，包括天气、历史、科学、文化等等。\n\n我还在不断学习和成长，希望能成为你生活中越来越有用的帮手。\n\n如果你有任何问题或请求，请随时告诉我。我很乐意为你服务。",
    },
]
access_token = httpx.get(
    f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={sCorpID}&corpsecret={sCorpsecret}"
).text
access_token = eval(access_token)["access_token"]
print("access_token：" + access_token)


async def access_tokens():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={sCorpID}&corpsecret={sCorpsecret}"
        )
        return response.json()["access_token"]


async def Gemini_chat(original_format):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    context = [
        {
            "role": "model" if entry["role"] == "assistant" else entry["role"],
            "parts": [{"text": entry["content"]}],
        }
        for entry in original_format
    ]
    data = json.dumps({"contents": context})

    params = {"key": gemini_key}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url, headers=headers, data=data, params=params
            ) as response:
                response_data = await response.text()
                response_data = eval(response_data)
                print(response_data["candidates"][0]["content"]["parts"][0]["text"])
        return response_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(response_data)
        return response_data


async def chat_msg(to_user_id: str, recived_msg: str, agentid: str):
    global access_token
    name = to_user_id
    print()
    if recived_msg == "new":
        User_chat_context[agentid] = example_context.copy()
        result = "已重置上下文"
    if agentid in User_chat_context:
        User_chat_context[agentid].append({"role": "user", "content": recived_msg})
        result = await Gemini_chat(User_chat_context[agentid])
        User_chat_context[agentid].append({"role": "assistant", "content": result})
    else:
        User_chat_context[agentid] = example_context.copy()
        User_chat_context[agentid].append({"role": "user", "content": recived_msg})
        result = await Gemini_chat(User_chat_context[agentid])
        User_chat_context[agentid].append({"role": "assistant", "content": result})

    print("请求结果：", result)
    send_data = json.dumps(
        {
            "touser": name,
            "msgtype": "text",
            "agentid": agentid,
            "text": {"content": result},
        }
    )
    async with httpx.AsyncClient() as client:
        send_code = await client.post(
            f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}",
            data=send_data,
        )
        send_response_data = send_code.json()  # 使用.json()解析响应数据
        # 检查是否有错误码，且不为0，需要重新获取access_token
        if send_response_data["errcode"] != 0:
            access_token = await access_tokens()  # 重新获取access_token
            print(access_token)
            # 使用新的access_token重新发送请求
            send_code = await client.post(
                f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}",
                data=send_data,
            )
    # 返回新的状态码
    return send_code.status_code
