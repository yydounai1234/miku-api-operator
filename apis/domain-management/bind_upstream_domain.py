# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import base64
import compat_urllib_parse
import json
from compat_urllib_parse import urlparse
from compat_http_client import HTTPSConnection, HTTPConnection

# 你的 AK 和 SK
AK = os.getenv("Access_key")
SK = os.getenv("Secret_key")

def test_bind_upstream_domain(bucket_name, domain, domain_type):
    """
    测试绑定上行域名接口
    
    Args:
        bucket_name (str): 空间名称
        domain (str): 要绑定的域名
        domain_type (str): 域名类型（pushRtmp：rtmp 推流域名；whip：whip 推流域名；pushSrt：srt 推流域名）
    """
    
    # 接口信息
    method = "POST"
    host = "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)
    path = "/?pushDomain"
    
    url = "http://{}{}".format(host, path)
    print("Sending request to: {}".format(url))
    
    # 构造请求体
    body_data = {
        "domain": domain,
        "type": domain_type
    }
    body = json.dumps(body_data)
    
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
    # 测试绑定上行域名，替换为实际的空间名称和域名信息
    bucket_name = "test-bucket-name"
    domain = "test-bucket-publish.qnsdk.com"
    domain_type = "pushRtmp"  # pushRtmp, whip, pushSrt
    
    print("Testing bind upstream domain API with bucket name: {}".format(bucket_name))
    print("Domain: {}, Type: {}".format(domain, domain_type))
    
    response = test_bind_upstream_domain(bucket_name, domain, domain_type)
    print("响应内容: {}".format(response))