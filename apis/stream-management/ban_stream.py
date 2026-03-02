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


def test_ban_stream(bucket_name, stream_key, forbidden_till=0):
    """
    测试封禁流接口

    Args:
        bucket_name (str): 流所属的空间名称
        stream_key (str): 流名称
        forbidden_till (int | None): 禁播结束时间，Unix 秒级时间戳。
            0 表示永久封禁，-1 表示解除封禁，默认 0。
    """

    # 接口信息
    method = "POST"
    host = "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)
    path = "/{}".format(stream_key)
    # forbid 无值参数，bucket/streamKey 按文档放在查询串中
    url = "http://{}{}?forbid&bucket={}&streamKey={}".format(host, path, bucket_name, stream_key)
    print("Sending request to: {}".format(url))

    # 请求体
    body_dict = {}
    if forbidden_till is not None:
        body_dict["forbiddenTill"] = forbidden_till
    body = json.dumps(body_dict)

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
        body=data,
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
    # 测试封禁流，替换为实际空间名称和流名称
    bucket_name = "sdk-miku-test"
    stream_key = "yydounai-test"
    forbidden_till = 0  # 0 永久封禁，-1 解除封禁
    print(
        "Testing ban stream API with bucket name: {}, stream key: {}, forbiddenTill: {}".format(bucket_name, stream_key, forbidden_till)
    )
    response = test_ban_stream(bucket_name, stream_key, forbidden_till)
    print("响应内容: {}".format(response))
