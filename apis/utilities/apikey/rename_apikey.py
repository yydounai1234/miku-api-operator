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


def test_rename_apikey(apikey_id, new_name):
    """
    重命名 apikey。

    Args:
        apikey_id (str): apikey 的 id
        new_name (str): 新的 apikey 名称
    """

    method = "POST"
    host = "mls.cn-east-1.qiniumiku.com"
    path = "/"

    query_params = {
        "apikeyRename": "",
    }
    query_string = urlencode(query_params)
    url = "http://{}{}?{}".format(host, path, query_string)
    print("Sending request to: {}".format(url))

    body = json.dumps({"id": apikey_id, "name": new_name})

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
    apikey_id = "f756f547-7d1d-46c1-b026-df925c3244c0"
    new_name = "miku-test"

    print("Testing rename apikey API with id: {}".format(apikey_id))
    response = test_rename_apikey(apikey_id, new_name)
    print("响应内容: {}".format(response))
