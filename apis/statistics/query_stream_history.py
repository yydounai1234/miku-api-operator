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


def test_query_stream_history(
    start,
    end,
    stream,
    domain=None,
    bucket=None,
    granularity="1min",
):
    """
    查询流历史数据。

    Args:
        start (int): 起始时间 Unix 秒级
        end (int): 结束时间 Unix 秒级
        stream (str): 流名
        domain (str | None): 推流域名，domain/bucket 二选一
        bucket (str | None): 空间名称，domain/bucket 二选一
        granularity (str): 粒度，默认 1min，可选 1min/5min/hour/day
    """

    if not domain and not bucket:
        raise ValueError("domain 和 bucket 需至少提供一个")

    method = "GET"
    # 若提供 bucket，则 host 使用 <bucket>.mls...，否则使用公共域名
    host = "mls.cn-east-1.qiniumiku.com"
    path = "/"

    query_params = {
        "streamStats": "",
        "start": str(start),
        "end": str(end),
        "stream": stream,
        "g": granularity,
    }
    if domain:
        query_params["domain"] = domain
    if bucket:
        query_params["bucket"] = bucket

    query_string = urlencode(query_params)
    url = "http://{}{}?{}".format(host, path, query_string)
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
    # 替换为真实的时间戳/域名/流名
    start_time = 1768186800
    end_time = 1768190790
    stream_name = "test-yydounai27"
    # domain_name = "example.push.com"
    bucket_name = "sdk-miku-test"

    print("Testing stream history API with stream: {}".format(stream_name))
    response = test_query_stream_history(
        start=start_time,
        end=end_time,
        stream=stream_name,
        bucket=bucket_name,
        granularity="1min",
    )
    print("响应内容: {}".format(response))
