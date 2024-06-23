#!/usr/bin/env python
# -*- encoding:utf-8 -*-

""" 对企业微信发送给企业后台的消息加解密示例代码.
@copyright: Copyright (c) 1998-2014 Tencent Inc.
"""

# ------------------------------------------------------------------------
import logging
import base64
import random
import hashlib
import time
import struct
from Crypto.Cipher import AES
import xml.etree.cElementTree as ET
import socket

import ierror


class FormatException(Exception):
    pass


def throw_exception(message, exception_class=FormatException):
    """自定义异常抛出函数"""
    raise exception_class(message)


class SHA1:
    """计算企业微信的消息签名接口"""

    @staticmethod
    def getSHA1(token, timestamp, nonce, encrypt):
        """用SHA1算法生成安全签名
        @param token:  票据
        @param timestamp: 时间戳
        @param encrypt: 密文
        @param nonce: 随机字符串
        @return: 安全签名
        """
        try:
            sortlist = sorted([token, timestamp, nonce, encrypt])
            sha = hashlib.sha1()
            sha.update("".join(sortlist).encode())
            return ierror.WXBizMsgCrypt_OK, sha.hexdigest()
        except Exception as e:
            logging.getLogger().error(e)
            return ierror.WXBizMsgCrypt_ComputeSignature_Error, None


class XMLParse:
    """提供提取消息格式中的密文及生成回复消息格式的接口"""

    # XML消息模板
    AES_TEXT_RESPONSE_TEMPLATE = """<xml>
<Encrypt><![CDATA[%(msg_encrypt)s]]></Encrypt>
<MsgSignature><![CDATA[%(msg_signature)s]]></MsgSignature>
<TimeStamp>%(timestamp)s</TimeStamp>
<Nonce><![CDATA[%(nonce)s]]></Nonce>
</xml>"""

    @staticmethod
    def extract(xmltext):
        """提取XML数据包中的加密消息
        @param xmltext: 待提取的XML字符串
        @return: 提取出的加密消息字符串
        """
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            return ierror.WXBizMsgCrypt_OK, encrypt.text
        except Exception as e:
            logging.getLogger().error(e)
            return ierror.WXBizMsgCrypt_ParseXml_Error, None

    @staticmethod
    def generate(encrypt, signature, timestamp, nonce):
        """生成XML消息
        @param encrypt: 加密后的消息密文
        @param signature: 安全签名
        @param timestamp: 时间戳
        @param nonce: 随机字符串
        @return: 生成的XML字符串
        """
        resp_dict = {
            'msg_encrypt': encrypt,
            'msg_signature': signature,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        return XMLParse.AES_TEXT_RESPONSE_TEMPLATE % resp_dict


class PKCS7Encoder:
    """提供基于PKCS7算法的加解密接口"""

    block_size = 32

    @staticmethod
    def encode(text):
        """对需要加密的明文进行填充补位
        @param text: 需要进行填充补位操作的明文
        @return: 补齐明文字符串
        """
        text_length = len(text)
        amount_to_pad = PKCS7Encoder.block_size - (text_length % PKCS7Encoder.block_size)
        pad = chr(amount_to_pad)
        return text + (pad * amount_to_pad).encode()

    @staticmethod
    def decode(decrypted):
        """删除解密后明文的补位字符
        @param decrypted: 解密后的明文
        @return: 删除补位字符后的明文
        """
        pad = ord(decrypted[-1])
        return decrypted[:-pad] if 1 <= pad <= 32 else decrypted


class Prpcrypt:
    """提供接收和推送给企业微信消息的加解密接口"""

    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC

    def encrypt(self, text, receiveid):
        """对明文进行加密
        @param text: 需要加密的明文
        @return: 加密得到的字符串
        """
        text = text.encode()
        random_str = self._get_random_str()
        text = random_str + struct.pack("I", socket.htonl(len(text))) + text + receiveid.encode()
        text = PKCS7Encoder.encode(text)
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        try:
            ciphertext = cryptor.encrypt(text)
            return ierror.WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception as e:
            logging.getLogger().error(e)
            return ierror.WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text, receiveid):
        """对解密后的明文进行补位删除
        @param text: 密文
        @return: 删除填充补位后的明文
        """
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        try:
            decrypted_text = cryptor.decrypt(base64.b64decode(text))
        except Exception as e:
            logging.getLogger().error(e)
            return ierror.WXBizMsgCrypt_DecryptAES_Error, None

        try:
            pad = decrypted_text[-1]
            content = decrypted_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4:xml_len+4]
            from_receiveid = content[xml_len+4:]
        except Exception as e:
            logging.getLogger().error(e)
            return ierror.WXBizMsgCrypt_IllegalBuffer, None

        if from_receiveid.decode('utf8') != receiveid:
            return ierror.WXBizMsgCrypt_ValidateCorpid_Error, None
        return ierror.WXBizMsgCrypt_OK, xml_content

    @staticmethod
    def _get_random_str():
        """随机生成16位字符串"""
        return str(random.randint(1000000000000000, 9999999999999999)).encode()


class WXBizMsgCrypt:
    """企业微信消息加解密"""

    def __init__(self, sToken, sEncodingAESKey, sReceiveId):
        try:
            self.key = base64.b64decode(sEncodingAESKey + "=")
            assert len(self.key) == 32
        except:
            throw_exception("[error]: EncodingAESKey unvalid !", FormatException)
        self.m_sToken = sToken
        self.m_sReceiveId = sReceiveId

    def VerifyURL(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp, sNonce, sEchoStr)
        if ret != 0:
            return ret, None
        if signature != sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None

        pc = Prpcrypt(self.key)
        return pc.decrypt(sEchoStr, self.m_sReceiveId)

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(sReplyMsg, self.m_sReceiveId)
        if ret != 0:
            return ret, None
        encrypt = encrypt.decode('utf8')
        timestamp = timestamp or str(int(time.time()))
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, timestamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        return ret, XMLParse.generate(encrypt, signature, timestamp, sNonce)

    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        xmlParse = XMLParse()
        ret, encrypt = xmlParse.extract(sPostData)
        if ret != 0:
            return ret, None
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        if signature != sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        return pc.decrypt(encrypt, self.m_sReceiveId)
