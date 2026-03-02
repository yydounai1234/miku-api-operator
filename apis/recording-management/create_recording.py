#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import hmac
import hashlib
import base64
from compat_urllib_parse import quote, urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK（从环境变量读取）
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")


def test_create_recording_file(
    bucket_name,
    stream_name,
    start_time,
    end_time,
    fmt="m3u8",
    fname=None,
    pipeline=None,
    expire_days=None,
    first_segment_type=None,
    persistent_delete_after_days=None,
    notify=None,
    host=None,
    timeout=30,
):
    """
    生成指定时间范围录制文件。

    Args:
        bucket_name (str): 空间名称，用于拼接 host（示例使用 cn-east-1 区域）
        stream_name (str): 流名称（用于路径部分）
        start_time (int): 开始时间
        end_time (int): 结束时间
        fmt (str): 录制格式，默认为 m3u8，可选 flv/mp4
        fname (str): 录制文件名
        pipeline (str): 异步处理队列
        expire_days (int): ts 文件过期时间
        first_segment_type (int): 第一个分片类型过滤
        persistent_delete_after_days (int): 生成文件生命周期
        notify (str): 生成完成后的回调地址
        host (str): 服务域名，默认 mls.cn-east-1.qiniumiku.com
        timeout (int): 请求超时
    """

    method = "POST"
    service_host = host or "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)

    # stream_name 作为 path，需 URL 编码
    path = "/{}?recordingFile".format(quote(stream_name))
    url = "http://{}{}".format(service_host, path)
    print("Sending request to: {}".format(url))

    body = {
        "startTime": start_time,
        "endTime": end_time,
        "format": fmt,
    }

    if fname is not None:
        body["fname"] = fname
    if pipeline is not None:
        body["pipeline"] = pipeline
    if expire_days is not None:
        body["expireDays"] = expire_days
    if first_segment_type is not None:
        body["firstSegmentType"] = first_segment_type
    if persistent_delete_after_days is not None:
        body["persistentDeleteAfterDays"] = persistent_delete_after_days
    if notify is not None:
        body["notify"] = notify

    body_json = json.dumps(body)

    signature = generate_signature(method, url, body_json, AK, SK)
    print("生成的签名: {}".format(signature))

    response = send_http_request(url, method, body_json, signature, timeout)
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

    print("--- 生成指定时间范围录制文件 ---")
    response = test_create_recording_file(
        bucket_name,
        stream_name,
        start_time=1768186800,
        end_time=1768190790,
        fmt="m3u8",
        fname="test/3/1701766353000-1701766699000.m3u8",
    )
    print("响应内容: {}".format(response))
