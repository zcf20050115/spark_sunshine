#!/usr/bin/env python3
# -*-coding:utf-8 -*-
import ssl
import _thread as thread
import time
import jsonpath
import websocket
import base64
import openpyxl
import os
import glob
import datetime
import hashlib
import hmac
import json
import pyaudio
import numpy as np
import wave

from sample import ne_utils, aipass_client
from data import *
from urllib.parse import urlparse
from urllib.parse import urlencode
from time import mktime
from wsgiref.handlers import format_date_time
from playsound import playsound
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
   
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#   

 
STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识
 
 
class Ws_Param(object):
    # 初始化
    ne_utils.del_file('./resource/output')
    ne_utils.del_file('./resource/input')
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
 
        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}
 
    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
 
        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
 
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        return url
 
 
# 收到websocket消息的处理
def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
 
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
 
            if result == '。' or result == '.。' or result == ' .。' or result == ' 。':
                pass
            else:
                t.insert(END, result)  
                print("%s" % (result))
                time.sleep(2)
                with open(r"./resource/input/0.txt",'a',encoding='utf-8') as file0:   
                     print('%s' % result.splitlines(),file=file0) 
 
    except Exception as e:
        print("receive msg,but parse exception:", e)
 
 
# 收到websocket错误的处理
def on_error(ws, error):
    print("###error###", error)
 
 
# 收到websocket关闭的处理
def on_close(ws):
    pass
    # print("### closed ###")
 
 
# 收到websocket连接建立的处理
def on_open(ws):
    def run():
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
        CHUNK = 520  # 定义数据流块
        FORMAT = pyaudio.paInt16  # 16bit编码格式
        CHANNELS = 1  # 单声道
        RATE = 16000  # 16000采样频率
        # 实例化pyaudio对象
        p = pyaudio.PyAudio()  # 录音
        # 创建音频流
        # 使用这个对象去打开声卡，设置采样深度、通道数、采样率、输入和采样点缓存数量
        stream = p.open(format=FORMAT,  # 音频流wav格式
                        channels=CHANNELS,  # 单声道
                        rate=RATE,  # 采样率16000
                        input=True,
                        frames_per_buffer=CHUNK)
 
        print("- - - - - - - Start Recording - - - - - - - ")
 
        for i in range(0, int(RATE / CHUNK * 60)):
            # # 读出声卡缓冲区的音频数据
            buf = stream.read(CHUNK)
            if not buf:
                status = STATUS_LAST_FRAME
            if status == STATUS_FIRST_FRAME:
 
                d = {"common": wsParam.CommonArgs,
                     "business": wsParam.BusinessArgs,
                     "data": {"status": 0, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                d = json.dumps(d)
                ws.send(d)
                status = STATUS_CONTINUE_FRAME
                # 中间帧处理
            elif status == STATUS_CONTINUE_FRAME:
                d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                ws.send(json.dumps(d))
 
            # 最后一帧处理
            elif status == STATUS_LAST_FRAME:
                d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                ws.send(json.dumps(d))
                time.sleep(1)
                break
 
        stream.stop_stream()  # 暂停录制
        stream.close()  # 终止流
        p.terminate()  # 终止pyaudio会话
        ws.close()
 
    thread.start_new_thread(run, ())
 
 
def run():
    global wsParam
    # 讯飞接口
    wsParam = Ws_Param(APPID='9d3813fc',
                       APIKey='e9e735265d4890aa8238a5a7b1fe4680',
                       APISecret='NWYyMTMyZWI3OWQxN2IxNDJhNzgzMGZh')
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=2)
 
 
# TODO 记得修改 APPID、APIKey、APISecret
 
from tkinter import *
import threading  # 多线程
import tkinter
 

 
# t = threading.Thread(target=run)
 
 
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
 
 
window = Tk()
window.geometry('500x350')
window.title('Spark_startlink_by张超峰')
t = Text(window, bg='white') 
t.pack()


tkinter.Button(window, text='开始', command=lambda: thread_it(run, )).place(x=230, y=315)
 
window.mainloop()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
   
time.sleep(10)

#SparkLite
class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, gpt_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(gpt_url).netloc
        self.path = urlparse(gpt_url).path
        self.gpt_url = gpt_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.gpt_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, query=ws.query, domain=ws.domain))
    ws.send(data)


# 收到websocket消息的处理
def on_message(ws, message):
    # print(message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content,end='')
        with open(r"./resource/input/1.txt",'a',encoding='utf-8') as file0:   
         print('%s' % content.splitlines(),end='',file=file0) 
         


def gen_params(appid, query, domain):
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234",           
            # "patch_id": []    #接入微调模型，对应服务发布后的resourceid          
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 0.5,
                "max_tokens": 4096,
                "auditing": "default",
            }
        },
        "payload": {
            "message": {
                "text": [{"role": "user", "content": query}]
            }
        }
    }
    return data


def main(appid, api_secret, api_key, gpt_url, domain, query):
    wsParam = Ws_Param(appid, api_key, api_secret, gpt_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()

    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = appid
    ws.query = query
    ws.domain = domain
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

with open("./resource/input/0.txt", "r",encoding='utf-8') as f:  #打开文件
  demo = f.readline()  #读取文件
  print(demo)

if __name__ == "__main__":
    main(
        appid="9d3813fc",
        api_secret="NWYyMTMyZWI3OWQxN2IxNDJhNzgzMGZh",
        api_key="e9e735265d4890aa8238a5a7b1fe4680",
        # gpt_url="wss://spark-api.xf-yun.com/v3.5/chat",    # Max   
        # Spark_url = "ws://spark-api.xf-yun.com/v3.1/chat"  # Pro
        # gpt_url = "ws://spark-api.xf-yun.com/v1.1/chat",   # Lite
        gpt_url = "wss://spark-api.xf-yun.com/v4.0/chat",    # 4.0Ultra
        # domain="generalv3.5",    # Max
        # domain = "generalv3"     # Pro
        # domain = "general",      # Lite
        domain = "4.0Ultra",       # 4.0Ultra
        query = demo
    )


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
   
time.sleep(10) 

# TTS
# 收到websocket连接建立的处理
def on_open(ws):
    def run():
        exist_audio = jsonpath.jsonpath(request_data, "$.payload.*.audio")
        exist_video = jsonpath.jsonpath(request_data, "$.payload.*.video")
        multi_mode = True if exist_audio and exist_video else False

        frame_rate = None
        if jsonpath.jsonpath(request_data, "$.payload.*.frame_rate"):
            frame_rate = jsonpath.jsonpath(request_data, "$.payload.*.frame_rate")[0]
        time_interval = 40
        if frame_rate:
            time_interval = round((1 / frame_rate) * 1000)

        media_path2data = aipass_client.prepare_req_data(request_data)
        
        aipass_client.send_ws_stream(ws, request_data, media_path2data, multi_mode, time_interval)

    thread.start_new_thread(run, ())


# 收到websocket消息的处理
def on_message(ws, message):
    aipass_client.deal_message(ws, message)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    print("### 执行结束，连接自动关闭 ###")


if __name__ == '__main__':
    # 程序启动的时候设置APPID
    request_data['header']['app_id'] = APPId
    auth_request_url = ne_utils.build_auth_request_url(request_url, "GET", APIKey, APISecret)
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(auth_request_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


def rename_files(directory, pattern, new_name):
    files = glob.glob(os.path.join(directory, pattern))
    for old_file in files:
        new_file = os.path.join(directory, new_name)
        os.rename(old_file, new_file)
 

rename_files('./resource/output', 'audio.lame', 'audio.mp3')
playsound('./resource/output/audio.mp3')
