#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hmac
import hashlib
import base64
from compat_urllib_parse import urlencode, urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK（从环境变量读取）
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_get_transcoding_template_list(content=None, limit=None, offset=None, host=None):
    """
    获取实时流转码模板列表。

    Args:
        content (str): 搜索内容（例如模板名称关键字）
        limit (int): 返回数量限制，默认20，最大100
        offset (int): 分页偏移值
        host (str): 服务域名，默认 mls.cn-east-1.qiniumiku.com
    """

    method = "GET"
    service_host = host or "mls.cn-east-1.qiniumiku.com"

    query = {}
    if content:
        query["content"] = content
    if limit is not None:
        query["limit"] = limit
    if offset is not None:
        query["offset"] = offset

    # 固定字段 codecTemplate 直接拼接，其余参数使用 urlencode
    encoded_query = urlencode(query)
    if encoded_query:
        path = "/?codecTemplates&{}".format(encoded_query)
    else:
        path = "/?codecTemplates"

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
    # 示例：按关键字搜索并分页
    print("--- 获取实时流转码模板列表 ---")
    response = test_get_transcoding_template_list(content="p", offset=0, limit=10)
    print("响应内容: {}".format(response))
