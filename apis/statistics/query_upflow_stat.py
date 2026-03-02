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


def test_query_upflow_stat(
    begin,
    end=None,
    granularity="5min",
    group=None,
    hub=None,
    domain=None,
    stream_name=None,
    area=None,
    select="flow",
):
    """
    查询直播上行流量。

    Args:
        begin (str): 开始时间，格式 20060102 或 20060102150405
        end (str | None): 结束时间，超过当前时间则取当前时间
        granularity (str): 时间粒度，5min/hour/day/month
        group (str | None): 分组字段，可取 hub/domain/streamName/area 等条件字段
        hub (str | None): 直播空间名
        domain (str | None): 域名
        stream_name (str | None): 流名
        area (str | None): 区域 cn/hk/tw/apac/am/emea
        select (str): 值字段，默认 flow（流量，byte）
    """

    method = "GET"
    host = "miku-statd.qiniuapi.com"
    path = "/statd/v1/traffic/stat/upflow"

    query_params = {
        "begin": begin,
        "g": granularity,
        "select": select,
    }
    if end:
        query_params["end"] = end
    if group:
        query_params["group"] = group
    if hub:
        query_params["$hub"] = hub
    if domain:
        query_params["$domain"] = domain
    if stream_name:
        query_params["$streamName"] = stream_name
    if area:
        query_params["$area"] = area

    query_string = urlencode(query_params)
    url = "https://{}{}?{}".format(host, path, query_string)
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
    # 替换为真实的时间、空间/域名等查询条件
    begin_time = "20260110"
    end_time = "20260114"
    hub_name = "sdk-miku-test"
    domain_name = "miku-test-publish.qnsdk.com"

    print("Testing upflow stat API...")
    response = test_query_upflow_stat(
        begin=begin_time,
        end=end_time,
        granularity="day",
        group=None,
        hub=hub_name,
        domain=domain_name,
        stream_name="test-yydounai27",
        select="flow"
    )
    print("响应内容: {}".format(response))