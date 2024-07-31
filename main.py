from typing import List, TypeVar, Generic, Type, Any
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, TypeAdapter
from starlette.requests import Request
from xml.etree.ElementTree import fromstring
import xml.etree.cElementTree as ET
from WXBizMsgCrypt import WXBizMsgCrypt
from config import sCorpID, sEncodingAESKey, sToken
import asyncio
import func
import json
import logging
import sys
import traceback

logging.basicConfig(level=logging.INFO)

# 定义全局队列
queue = asyncio.Queue()

# 异步处理队列中的任务
async def consume_queue(queue: asyncio.Queue) -> None:
    while True:
        data_to_process = await queue.get()
        FromUserName = data_to_process["FromUserName"]
        content_recived = data_to_process["content_recived"]
        AgentID = data_to_process["AgentID"]
        try:
            send_codes = await func.chat_msg(FromUserName, content_recived, AgentID)
            logging.info(f"任务处理完成: {send_codes}")
        except Exception as e:
            logging.error("处理任务时出错", exc_info=True)
        finally:
            queue.task_done()

# 使用FastAPI的生命周期管理队列任务
async def app_lifespan(app: FastAPI) -> None:
    consume_task = asyncio.create_task(consume_queue(queue))
    try:
        yield
    finally:
        consume_task.cancel()

app = FastAPI(lifespan=app_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

wxcpt = WXBizMsgCrypt(sToken, sEncodingAESKey, sCorpID)

# 定义接受XML格式数据的泛型类
T = TypeVar("T", bound=BaseModel)

class Item(BaseModel):
    ToUserName: str
    AgentID: str
    Encrypt: str

class XmlBody(Generic[T]):
    def __init__(self, model_class: Type[T]) -> None:
        self.model_class = model_class

    async def __call__(self, request: Request) -> T:
        if 'xml' in request.headers.get("Content-Type", ""):
            body = await request.body()
            doc = fromstring(body)
            dict_data = {node.tag: node.text for node in list(doc)}
        else:
            body = await request.body()
            dict_data = json.loads(body)
        return TypeAdapter(self.model_class).validate_python(dict_data)

Recived_Temp = """<xml> 
   <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
   <AgentID><![CDATA[%(AgentID)s]]></AgentID>
   <Encrypt><![CDATA[%(Encrypt)s]]></Encrypt>
</xml>"""

Send_Temp = """<xml>
   <ToUserName>%(ToUserName)s</ToUserName>
   <FromUserName>%(FromUserName)s</FromUserName> 
   <CreateTime>%(timestamp)s</CreateTime>
   <MsgType>text</MsgType>
   <Content>%(content)s</Content>
</xml>"""

@app.get("/")
async def Verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    sVerifyMsgSig = msg_signature
    sVerifyTimeStamp = timestamp
    sVerifyNonce = nonce
    sVerifyEchoStr = echostr
    ret, sReplyEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp,sVerifyNonce,sVerifyEchoStr)
    if( ret!=0 ):
        print("ERR: DecryptMsg ret: " + str(ret))
        sys.exit(1)
    return int(sReplyEchoStr)

@app.post("/wechat")
async def main(
    msg_signature: str,
    timestamp: str,
    nonce: str,
    q: str = None,
    item: Item = Depends(XmlBody(Item))
) -> str:
    Recived_dict = {
        'ToUserName': item.ToUserName,
        'AgentID': item.AgentID,
        'Encrypt': item.Encrypt,
    }
    ReqData = Recived_Temp % Recived_dict
    ret, sMsg = wxcpt.DecryptMsg(sPostData=ReqData, sMsgSignature=msg_signature, sTimeStamp=timestamp, sNonce=nonce)
    if ret != 0:
        logging.error(f"ERR: DecryptMsg ret: {ret}")
        return "Error in message decryption"

    xml_tree = ET.fromstring(sMsg)
    sMsgType = xml_tree.find("MsgType").text

    if sMsgType == "text":
        content_recived = xml_tree.find("Content").text
        FromUserName = xml_tree.find("FromUserName").text
        ToUserName = xml_tree.find("ToUserName").text
        AgentID = xml_tree.find("AgentID").text
        logging.info(f"消息类型：{sMsgType} | 发送人：{FromUserName} | 内容：{content_recived} | ID: {AgentID}")
        
        cmd_list = ["ping", "help"]
        if content_recived in cmd_list:
            Send_dict = {
                "ToUserName": ToUserName,
                "FromUserName": FromUserName,
                "timestamp": timestamp,
                "content": content_recived
            }
            sRespData = Send_Temp % Send_dict
            ret, sEncryptMsg = wxcpt.EncryptMsg(sReplyMsg=sRespData, sNonce=nonce, timestamp=timestamp)
            if ret != 0:
                return "Error in message encryption"
            return sEncryptMsg
        else:
            await queue.put({"FromUserName": FromUserName, "content_recived": content_recived, "AgentID": AgentID})
            logging.info("任务+1")
            return "Message received for processing"
    else:
        logging.info(f"消息类型：{sMsgType}")
        return "Unsupported message type"

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6880)
