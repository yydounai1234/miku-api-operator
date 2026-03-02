#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hmac
import hashlib
import base64
import json
from compat_urllib_parse import urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK（从环境变量读取）
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_update_transcoding_template(template_body, host=None):
    """
    更新实时流转码模板。

    Args:
        host (str): 服务域名，默认 mls.cn-east-1.qiniumiku.com
        template_body (dict): 模板内容，字段参考“更新实时流转码模板”文档
    """

    method = "PATCH"
    service_host = host or "mls.cn-east-1.qiniumiku.com"
    path = "/?codecTemplate"
    url = "http://{}{}".format(service_host, path)
    print("Sending request to: {}".format(url))

    body = json.dumps(template_body)

    signature = generate_signature(method, url, body, AK, SK)
    print("生成的签名: {}".format(signature))

    response = send_http_request(url, method, body, signature, 30)
    return response


def generate_signature(method, url, body, ak, sk):
    parsed_url = urlparse(url)

    data = method + " " + parsed_url.path

    if parsed_url.query:
        data += "?" + parsed_url.query

    data += "\nHost: " + parsed_url.hostname
    data += "\nContent-Type: application/json"

    if body:
        data += "\n\n" + body
    print(data)

    hmac_sha1 = hmac.new(sk.encode("utf-8"), data.encode("utf-8"), hashlib.sha1)
    hmac_result = hmac_sha1.digest()

    sign = "Qiniu " + ak + ":" + base64_url_safe_encode(hmac_result)
    return sign


def send_http_request(url, method, data, signature, timeout):
    parsed_url = urlparse(url)

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
    # 示例请求体，可按需调整字段
    template_body = {
        "name": "my480p1",
        "desc": "480pPPP实现",
        "smart": False,
        "profile": {
            "videoWidth": 640,
            "videoHigh": 480,
            "ab": 128,
            "ar": 44100,
            "vcodec": "libx264",
        },
    }

    print("--- 更新实时流转码模板 ---")
    response = test_update_transcoding_template(template_body)
    print("响应内容: {}".format(response))
