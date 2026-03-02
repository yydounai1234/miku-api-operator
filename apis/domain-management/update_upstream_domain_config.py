# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import base64
import compat_urllib_parse
import json
from compat_urllib_parse import urlparse, quote
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")

def test_update_upstream_domain_config(bucket_name, domain, config_data, fields=None):
    """
    测试修改上行域名配置接口
    
    Args:
        bucket_name (str): 空间名称
        domain (str): 域名
        config_data (dict): 配置数据
        fields (str): 可选，指定更新的具体字段，目前支持：iplimit
    """
    
    # 接口信息
    method = "PATCH"
    host = "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)
    
    # 构建查询参数，对域名进行URL编码
    query_params = "pushDomainConfig&name={}".format(quote(domain))
    if fields:
        query_params += "&fields={}".format(fields)
    path = "/?{}".format(query_params)
    
    url = "http://{}{}".format(host, path)
    print("Sending request to: {}".format(url))
    
    # PATCH请求需要JSON格式的配置数据
    body = json.dumps(config_data)
    
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
    hmac_sha1 = hmac.new(sk.encode('utf-8'), data.encode('utf-8'), hashlib.sha1)
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
        "Authorization": signature
    }
    
    conn.request(method, parsed_url.path + ("?" + parsed_url.query if parsed_url.query else ""), 
                 body=data, headers=headers)
    
    response = conn.getresponse()
    response_body = response.read().decode('utf-8')
    
    conn.close()
    
    return "HTTP {}: {}".format(response.status, response_body)

def base64_url_safe_encode(data):
    encoded = base64.b64encode(data).decode('utf-8')
    encoded = encoded.replace('+', '-').replace('/', '_')
    return encoded

if __name__ == "__main__":
    # 测试修改上行域名配置，替换为实际的空间名称和域名
    bucket_name = "test-bucket-name"
    domain = "test-bucket-publish.qnsdk.com"
    
    print("Testing update upstream domain config API with bucket name: {}, domain: {}".format(bucket_name, domain))
    
    # 示例配置数据（请根据实际需求修改）
    config_data = {
        "type": "pushRtmp",
        "auth": {
            "enable": True,
            "type":"test",
            "primaryKey": "QXV0aG9yaXphdGlvbg",
            "secondaryKey": "QXV0aG9yaXphdGlvbg",
            "expireSeconds": 120
        },
        "certificateID": "",
        "httpsEnable": False
    }
    
    # 不带fields参数的请求
    print("\n--- 修改上行域名配置（不带fields参数） ---")
    response1 = test_update_upstream_domain_config(bucket_name, domain, config_data)
    print("响应内容: {}".format(response1))
    
    # 带fields参数的请求
    print("\n--- 修改上行域名配置（带fields参数） ---")
    response2 = test_update_upstream_domain_config(bucket_name, domain, config_data, fields="iplimit")
    print("响应内容: {}".format(response2))