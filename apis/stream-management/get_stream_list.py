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


def test_get_stream_list(
    bucket_name,
    prefix=None,
    offset=None,
    limit=None,
    domain=None,
    start=None,
    end=None,
    bucket_id=None,
    is_forbid=None,
):
    """
    测试列举流列表接口

    Args:
        bucket_name (str): 流所属的空间名称
        prefix (str | None): 流名前缀
        offset (int | None): 游标
        limit (int | None): 返回条数
        domain (str | None): 推流域名（与 bucket_id 至少二选一）
        start (int | None): 最近一次推流开始时间（Unix 秒级）
        end (int | None): 最近一次推流结束时间（Unix 秒级）
        bucket_id (str | None): bucketId（与 domain 至少二选一）
        is_forbid (bool | None): 是否只查询被封禁流
    """

    # 接口信息
    method = "GET"
    host = "mls.cn-east-1.qiniumiku.com"
    path = "/"

    query_params = {}
    if prefix is not None:
        query_params["prefix"] = prefix
    if offset is not None:
        query_params["offset"] = str(offset)
    if limit is not None:
        query_params["limit"] = str(limit)
    if domain is not None:
        query_params["domain"] = domain
    if start is not None:
        query_params["start"] = str(start)
    if end is not None:
        query_params["end"] = str(end)
    if bucket_id is not None:
        query_params["bucketId"] = bucket_id
    if is_forbid is not None:
        query_params["isForbid"] = str(is_forbid).lower()

    query_string = urlencode(query_params)
    url = "http://{}{}?streamlist&{}".format(host, path, query_string)
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
    # 测试列举流列表，替换为实际空间名称和查询参数
    bucket_name = "sdk-miku-test"
    domain = "miku-test-publish.qnsdk.com"
    print("Testing get stream list API with bucket name: {}".format(bucket_name))
    response = test_get_stream_list(
        bucket_name=bucket_name,
        prefix=None,
        offset=0,
        limit=10,
        domain=domain,
        start=None,
        end=None,
        bucket_id=None,
        is_forbid=None,
    )
    print("响应内容: {}".format(response))
