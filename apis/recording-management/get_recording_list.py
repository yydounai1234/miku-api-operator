#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hmac
import hashlib
import base64
from compat_urllib_parse import quote, urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK（从环境变量读取）
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_get_recording_list(bucket_name, stream_name, host=None):
    """
    获取直播流的录制记录。

    Args:
        bucket_name (str): 空间名称，用于拼接 host（示例使用 cn-east-1 区域）
        stream_name (str): 流名称（用于路径部分）
        host (str): 服务域名，默认 mls.cn-east-1.qiniumiku.com
    """

    method = "GET"
    service_host = host or "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)

    # stream_name 作为 path，需 URL 编码
    path = "/{}?recordingHistory".format(quote(stream_name))
    url = "http://{}{}".format(service_host, path)
    print("Sending request to: {}".format(url))

    body = "{}"

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
        body=data if data else "",
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
    bucket_name = "sdk-miku-test"
    stream_name = "test-yydounai27"

    print("--- 查询录制记录 ---")
    response = test_get_recording_list(bucket_name, stream_name)
    print("响应内容: {}".format(response))
