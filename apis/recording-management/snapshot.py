# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import base64
import json
from compat_urllib_parse import urlencode, urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_snapshot(
    bucket_name,
    stream_name,
    time=None,
    fname=None,
    img_format=None,
    pipeline=None,
    notify=None,
    delete_after_days=None,
):
    """
    保存直播截图。

    Args:
        bucket_name (str): 空间名称，会拼入 host `<bucket>.mls.cn-east-1.qiniumiku.com`
        stream_name (str): 流名称，作为路径 `/<StreamName>`
        time (int | None): 截图时间戳，未指定则为当前时间
        fname (str | None): 文件名，未指定随机生成
        img_format (str | None): jpg 或 png
        pipeline (str | None): 队列名
        notify (str | None): 回调地址，指定则为异步
        delete_after_days (int | None): 生命周期，0 为永久
    """

    method = "POST"
    host = "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)
    path = "/{}".format(stream_name)

    query_params = {
        "snapshot": "",
    }
    query_string = urlencode(query_params)
    url = "http://{}{}?{}".format(host, path, query_string)
    print("Sending request to: {}".format(url))

    body_dict = {}
    if time is not None:
        body_dict["time"] = time
    if fname is not None:
        body_dict["fname"] = fname
    if img_format is not None:
        body_dict["format"] = img_format
    if pipeline is not None:
        body_dict["pipeline"] = pipeline
    if notify is not None:
        body_dict["notify"] = notify
    if delete_after_days is not None:
        body_dict["deleteAfterDays"] = delete_after_days

    body = json.dumps(body_dict)

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
    bucket_name = "sdk-miku-test"
    stream_name = "test-yydounai27"

    print("Testing snapshot API for stream: {}".format(stream_name))
    response = test_snapshot(
        bucket_name=bucket_name,
        stream_name=stream_name,
        fname="snapshot-demo2",
        img_format="jpg",
        pipeline="",
        notify="",
        delete_after_days=40,
    )
    print("响应内容: {}".format(response))
