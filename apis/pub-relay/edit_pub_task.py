# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import base64
import json
from compat_urllib_parse import urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_edit_pub_task(task_id, task_body):
    """
    测试编辑 pub 转推任务接口

    Args:
        task_id (str): 要编辑的任务 ID
        task_body (dict): 任务请求体，需包含 runType/sourceUrls/forwardUrls 等字段
    """

    # 接口信息
    method = "POST"
    host = "pub-manager.mikudns.com"
    path = "/tasks/{}".format(task_id)
    url = "https://{}{}".format(host, path)
    print("Sending request to: {}".format(url))

    body = json.dumps(task_body)

    # 生成签名
    signature = generate_signature(method, url, body, AK, SK)
    print("生成的签名: {}".format(signature))

    # 发送HTTP请求
    response = send_http_request(url, method, body, signature, 30)
    return response


def generate_signature(method, url, body, ak, sk):
    parsed_url = urlparse(url)

    # 构建签名数据
    data = method + " " + parsed_url.path

    if parsed_url.query:
        data += "?" + parsed_url.query

    data += "\nHost: " + parsed_url.hostname
    data += "\nContent-Type: application/json"

    if body:
        data += "\n\n" + body
    print(data)
    # 使用HMAC-SHA1进行签名
    hmac_sha1 = hmac.new(sk.encode("utf-8"), data.encode("utf-8"), hashlib.sha1)
    hmac_result = hmac_sha1.digest()

    sign = "Qiniu " + ak + ":" + base64_url_safe_encode(hmac_result)
    return sign


def send_http_request(url, method, data, signature, timeout):
    parsed_url = urlparse(url)

    # 检查主机名是否存在
    if not parsed_url.hostname:
        raise ValueError("Invalid URL: missing hostname")

    if parsed_url.scheme == "https":
        conn = HTTPSConnection(parsed_url.hostname, parsed_url.port or 443, timeout=timeout)
    else:
        conn = HTTPConnection(parsed_url.hostname, parsed_url.port or 80, timeout=timeout)

    headers = {
        "Content-Type": "application/json",
        "Authorization": signature,
    }

    conn.request(
        method,
        parsed_url.path + ("?" + parsed_url.query if parsed_url.query else ""),
        body=data if data else "{}",
        headers=headers,
    )

    response = conn.getresponse()
    response_body = response.read().decode("utf-8")

    conn.close()

    return "HTTP {}: {}".format(response.status, response_body)


def base64_url_safe_encode(data):
    encoded = base64.b64encode(data).decode("utf-8")
    encoded = encoded.replace("+", "-").replace("/", "_")
    return encoded


if __name__ == "__main__":
    # 示例：编辑已有任务，替换 task_id 与参数
    task_id = "1381218095_task-002"
    task_body = {
        "runType": "seek",
        "desc": "edit demo task",
        "sourceUrls": [
            {
                "url": "http://miku-test-play.qnsdk.com/sdk-miku-test/yydounai-test55.flv",
                "isp": "",
                "seek": 0,
                "videoType": 1,
                "rtspType": 0,
            }
        ],
        "forwardUrls": [
            {
                "url": "rtmp://miku-test-publish.qnsdk.com/sdk-miku-test/yydounai-test55",
                "isp": "",
            }
        ],
        "filter": {"ips": [], "area": "", "isp": ""},
        "loopTimes": 0,
        "retryTime": 60,
        "deliverStartTime": 1784947040000,
        "deliverStopTime": 1796390400000,
        "sustain": False,
        "preload": {"enable": True, "preloadTime": 1766390400000},
        "statusCallback": {
            "type": "JSON",
            "url": "https://callback.example.com",
            "vars": {
                "taskid": "$(taskID)",
                "status": "$(status)",
                "startTime": "$(startTime)",
                "stopTime": "$(stopTime)",
            },
        },
    }

    print("Testing edit pub task API...")
    response = test_edit_pub_task(task_id, task_body)
    print("响应内容: {}".format(response))
