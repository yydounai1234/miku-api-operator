# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import base64
from compat_urllib_parse import urlencode, urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_get_pub_list(marker=None, limit=None, name=None):
    """
    测试获取 pub 转推任务列表接口

    Args:
        marker (str | None): 翻页游标
        limit (int | None): 返回数量上限，最大 1000
        name (str | None): 任务名称/描述模糊匹配
    """

    # 接口信息
    method = "GET"
    host = "pub-manager.mikudns.com"
    path = "/tasks"

    query_params = {}
    if marker is not None:
        query_params["marker"] = marker
    if limit is not None:
        query_params["limit"] = str(limit)
    if name is not None:
        query_params["name"] = name

    query_string = urlencode(query_params)
    url = "https://{}{}".format(host, path) + ("?{}".format(query_string) if query_string else "")
    print("Sending request to: {}".format(url))

    # 无请求体
    body = "{}"

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
        body=data if data else None,
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
    print("Testing get pub task list API...")
    response = test_get_pub_list(marker=None, limit=100, name=None)
    print("响应内容: {}".format(response))
