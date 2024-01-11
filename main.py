from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, TypeAdapter
from starlette.requests import Request
from typing import TypeVar, Generic, Type, Any
from xml.etree.ElementTree import fromstring
import xml.etree.cElementTree as ET
from WXBizMsgCrypt import WXBizMsgCrypt
from config import sCorpID, sEncodingAESKey, sToken
import httpx
import asyncio
import func
import time
import sys
import traceback


async def consume_queue():
    while True:
        # 从队列中获取数据
        data_to_process = await queue.get()
        FromUserName = data_to_process["FromUserName"]
        content_recived = data_to_process["content_recived"]
        AgentID = data_to_process["AgentID"]
        try:
            send_codes = await func.chat_msg(FromUserName, content_recived, AgentID)
            print(send_codes)
            print("任务处理完成")
        except Exception as e:
            print(traceback.format_exc())
            print("报错：", e)
        # 标记当前任务已完成
        print("下一位")
        queue.task_done()


queue = asyncio.Queue()


# 用fastapi的生命周期，跑一个队列
async def app_lifespan(app):
    # 队列
    consume_task = asyncio.create_task(consume_queue())
    try:
        yield
    finally:
        print(1)


app = FastAPI(lifespan=app_lifespan)

# 创建登录会话
wxcpt = WXBizMsgCrypt(sToken, sEncodingAESKey, sCorpID)


# 以下为接受XML格式数据部分
T = TypeVar("T", bound=BaseModel)


class Item(BaseModel):
    ToUserName: str
    AgentID: str
    Encrypt: str


class XmlBody(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    async def __call__(self, request: Request) -> T:
        if "/xml" in request.headers.get("Content-Type", ""):
            body = await request.body()
            doc = fromstring(body)
            dict_data = {node.tag: node.text for node in list(doc)}
        else:
            body = await request.body()
            dict_data = json.loads(body)

        # 使用 TypeAdapter.validate_python 替代 parse_obj_as
        return TypeAdapter(self.model_class).validate_python(dict_data)


# 接受消息模版
Recived_Temp = """<xml> 
   <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
   <AgentID><![CDATA[%(AgentID)s]]></AgentID>
   <Encrypt><![CDATA[%(Encrypt)s]]></Encrypt>
</xml>"""

# 发送消息模版
Send_Temp = """<xml>
   <ToUserName>%(ToUserName)s</ToUserName>
   <FromUserName>%(FromUserName)s</FromUserName> 
   <CreateTime>%(timestamp)s</CreateTime>
   <MsgType>text</MsgType>
   <Content>%(content)s</Content>
</xml>"""


# 回调验证部分
@app.get("/wechat")
async def Verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    sVerifyMsgSig = msg_signature
    sVerifyTimeStamp = timestamp
    sVerifyNonce = nonce
    sVerifyEchoStr = echostr
    ret, sReplyEchoStr = wxcpt.VerifyURL(
        sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr
    )
    if ret != 0:
        print("ERR: DecryptMsg ret: " + str(ret))
        sys.exit(1)
    return int(sReplyEchoStr)


# 消息接收部分
@app.post("/wechat")
async def main(
    msg_signature: str,
    timestamp: str,
    nonce: str,
    q: str = None,
    item: Item = Depends(XmlBody(Item)),
):
    Recived_dict = {
        "ToUserName": item.ToUserName,
        "AgentID": item.AgentID,
        "Encrypt": item.Encrypt,
    }
    ReqData = Recived_Temp % Recived_dict
    ret, sMsg = wxcpt.DecryptMsg(
        sPostData=ReqData,
        sMsgSignature=msg_signature,
        sTimeStamp=timestamp,
        sNonce=nonce,
    )
    if ret != 0:
        print("ERR: DecryptMsg ret: " + str(ret))
        sys.exit(1)
    xml_tree = ET.fromstring(sMsg)
    sMsgType = xml_tree.find("MsgType").text
    # 判断消息类型
    if sMsgType == "text":
        # 从消息内容中取值
        content_recived = xml_tree.find("Content").text
        FromUserName = xml_tree.find("FromUserName").text
        ToUserName = xml_tree.find("ToUserName").text
        AgentID = xml_tree.find("AgentID").text
        print(
            "消息类型：",
            sMsgType,
            "|发送人：",
            FromUserName,
            "|内容：",
            content_recived,
            "ID:",
            AgentID,
        )
        # 消息处理部分
        cmd_list = ["ping", "help"]
        # 可用于短时间（5s内）内可以处理好的特殊指令内容，
        if content_recived in cmd_list:
            Send_dict = {
                "ToUserName": ToUserName,
                "FromUserName": FromUserName,
                "timestamp": timestamp,
                "content": content_recived,
            }
            sRespData = Send_Temp % Send_dict
            ret, sEncryptMsg = wxcpt.EncryptMsg(
                sReplyMsg=sRespData, sNonce=nonce, timestamp=timestamp
            )
            return sEncryptMsg
        else:
            try:
                data = {
                    "username": FromUserName,
                    "recived_msg": content_recived,  # 确保键名与你的接收端一致
                }
                await queue.put(
                    {
                        "FromUserName": FromUserName,
                        "content_recived": content_recived,
                        "AgentID": AgentID,
                    }
                )
                print("任务+1")
            except Exception as e:
                print(e)

    else:
        print("消息类型：", sMsgType)


# 启动服务
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6880)
