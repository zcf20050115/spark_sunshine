APPId = "9d3813fc"
APIKey = "e9e735265d4890aa8238a5a7b1fe4680"
APISecret = "NWYyMTMyZWI3OWQxN2IxNDJhNzgzMGZh"

# 请求数据
request_data = {
    "header": {
        "app_id": "123",
        "status":0
    },
    "parameter": {
        "oral": {
            "oral_level": "high",
            "spark_assist": 1,
            "scenarized": 0
        },
        "tts": {
            "vcn": "x4_lingxiaoxuan_oral",
            "volume": 50,
            "speed": 50,
            "pitch": 50,
            "bgs": 0,
            "rhy": 0,
            "audio": {
                "encoding": "lame",
                "sample_rate": 16000,
                "channels": 1,
                "bit_depth": 16,
                "frame_size": 0
            },
            "pybuf": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain"
            }
        }
    },
    "payload": {
        "text": {
            "encoding": "utf8",
            "compress": "raw",
            "format": "plain",
            "status": 0,
            "seq": 0,
            "text": "./resource/input/1.txt"
        }, 
        "user_text": {
            "encoding": "utf8",
            "compress": "raw",
            "format": "plain",
            "status": 0,
            "seq": 0,
            "text": "./resource/input/1.txt"
        }
    }
}

# 请求地址
request_url = "ws://cbm01.cn-huabei-1.xf-yun.com/v1/private/medd90fec"

# 用于快速定位响应值

response_path_list = ['$..payload.pybuf', '$..payload.audio', ]