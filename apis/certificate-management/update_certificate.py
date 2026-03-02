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

def test_update_certificate(bucket_name, domain, cert_name, update_data):
    """
    测试更新证书接口
    
    Args:
        bucket_name (str): 空间名称
        domain (str): 域名
        cert_name (str): 证书名称
        update_data (dict): 更新数据
    """
    
    # 接口信息
    method = "PATCH"
    host = "{}.mls.cn-east-1.qiniumiku.com".format(bucket_name)
    path = "/?domainCertificate&domain={}&certName={}".format(domain, cert_name)
    
    url = "http://{}{}".format(host, path)
    print("Sending request to: {}".format(url))
    
    # 将更新数据转换为JSON字符串
    body = json.dumps(update_data)
    
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
    # 测试更新证书，替换 "test-bucket-name" 为你想要使用的空间名称
    bucket_name = "test-bucket-name"
    domain = "test-bucket-play.qnsdk.com"
    cert_name = "testbucketplay.qnsdk.com"
    print("Testing update certificate API with bucket name: {}, domain: {}, cert name: {}".format(bucket_name, domain, cert_name))
    
    # 示例更新数据（请根据实际需求修改）
    update_data = {
        "cert": "-----BEGIN CERTIFICATE-----\nMIIG8DCCBNigAwIBAgIQCsX1iYTWkU1natYyBrvWWzANBgkqhkiG9w0BAQsFADBb\nMQswCQYDVQQGEwJDTjElMCMGA1UEChMcVHJ1c3RBc2lhIFRlY2hub2xvZ2llcywg\nSW5jLjElMCMGA1UEAxMcVHJ1c3RBc2lhIERWIFRMUyBSU0EgQ0EgMjAyNTAeFw0y\nNTExMDUwMDAwMDBaFw0yNjAyMDIyMzU5NTlaMCkxJzAlBgNVBAMTHnBpbGktbGl2\nZS1oZGwudmlkZW8udWxlY2RuLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCC\nAQoCggEBAL7jv1amJWoqzINNfMhnMv0ADJjdaXHTJhLe0w2GBWpxDHpBnkuQvsCR\n5bnEHZWwwb3Y/5bLVC1h8lD3jBUB2YoHMV/LHbljeLuG55QRdyRyyNQq2Jq6kkQL\nFM9B2c6V1Wim1+Y8gpxivVrRhXqlCICuiSpSWDL5b81eRmjWGX+N+Ulf3bAUNrmS\n8YRl5eFN2tkUEUa6uD6e8gIINWFXvmdCJt+2lE+lFnZlSIKFVa2I18TVoIeiGLeh\nZOVHGljmvbaeY+3QKB+jvlIPBQBqjGjdDHv57kjXgc7VRGs5dX2dKNR9nwq9NjgY\ngHgirGNU/HmLleXn93y22zhkB8g6sGcCAwEAAaOCAuAwggLcMB8GA1UdIwQYMBaA\nFLQSKKW0wB2fKXFpPNkRlkp1aVDAMB0GA1UdDgQWBBQk2Dy57psTNzi/gY4yRrqz\nNJhuvjApBgNVHREEIjAggh5waWxpLWxpdmUtaGRsLnZpZGVvLnVsZWNkbi5jb20w\nPgYDVR0gBDcwNTAzBgZngQwBAgEwKTAnBggrBgEFBQcCARYbaHR0cDovL3d3dy5k\naWdpY2VydC5jb20vQ1BTMA4GA1UdDwEB/wQEAwIFoDATBgNVHSUEDDAKBggrBgEF\nBQcDATB5BggrBgEFBQcBAQRtMGswJAYIKwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmRp\nZ2ljZXJ0LmNvbTBDBggrBgEFBQcwAoY3aHR0cDovL2NhY2VydHMuZGlnaWNlcnQu\nY29tL1RydXN0QXNpYURWVExTUlNBQ0EyMDI1LmNydDAMBgNVHRMBAf8EAjAAMIIB\nfwYKKwYBBAHWeQIEAgSCAW8EggFrAWkAdgCWl2S/VViXrfdDh2g3CEJ36fA61fak\n8zZuRqQ/D8qpxgAAAZpTWTKpAAAEAwBHMEUCIC00CeOFg7owMxZWO86rmD06KQ2z\nP494IMPdH+aKxPnWAiEAzZy03U486YzIyXG0PjcowF1ZE6Ey8E/d8yGh9xBrAOwA\ndgBkEcRspBLsp4kcogIuALyrTygH1B41J6vq/tUDyX3N8AAAAZpTWTK3AAAEAwBH\nMEUCICgN/vx1WfMSkldsrc9WDmeh4DN18Ulav2LrnXRT66SuAiEA/cBHWqTMv26t\n//+oJLCoeqVFVboruyMeH/P5e5ZHUgUAdwBJnJtp3h187Pw23s2HZKa4W68Kh4AZ\n0VVS++nrKd34wwAAAZpTWTLKAAAEAwBIMEYCIQC7MQR9zitb7/mE8oJOoRcAWAAd\nNb7fX8QYJ2gyVXg/1AIhAICGyy5EeSCaM9gsxSvhZwP1/XCcXhoewITGw5lUe7v0\nMA0GCSqGSIb3DQEBCwUAA4ICAQCz9zG6hm1RzEKgkYcDzyuvSn0mvroFstDPyqi8\nZ31QiGpCCuXLOObprKnZIYl7bLquS/g8fSZdqDc2RrK2l5JmhNwnPY/CAS/sMScb\nMMUcgeaKgt1MIGppL7ODj1VadO0yyItmUt+2+iKkWZhxSM/GpvsDZ6e7os38y2Gh\nJIg3RpIQOF3ZoR40WavIScZhpdeGAKGRu5jE2PvIiW+k3MApla54+KOHKMvD+IE6\n1CnRl74aXGVnPxJEXxTtVmvqdFP/vIcLXVZVSzAlKndx/mv7j2BOlz41pyv0OLjm\nDukFrAkbupPyW+jx4zCw4wMFzUIFG37aUo/ofNVIFnOvgJp7khu25UvZddN/jVV9\nhFpZ0Agu+V1W12iFNiMRnnTl+MhL9vTv4SBDbOnkcwd32BFWdCPNvw1BIFM2v9Mi\n6OC5gaVjRkH8OaEdGUMEbPqwwUlXxi2xAfgsrPaR7Zzxtu4kEliPJFqiG3qa0QVK\n1DH+U7Whw+PllC1UtPocTWdL7bmU18hpLO+EVEWt7wtcDMCaeAaVQUSj7v3AXMAs\n9TMcikQnhkPLjXHp0ePd5rjYOdCk6tf36NDjaiIp6D/EKZqHdy9L3TGtpVTXjrMj\nAigg1jpnet5JisN0FGfvhJef3Eq2q9vwwpxoJISmfz+0yEDllLkMgh7zI7Kd+fWe\n/1Mx2Q==\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\nMIIFnjCCBIagAwIBAgIQCSYyO0lk42hGFRLe8aXVLDANBgkqhkiG9w0BAQsFADBh\nMQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3\nd3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBH\nMjAeFw0yNTAxMDgwMDAwMDBaFw0zNTAxMDcyMzU5NTlaMFsxCzAJBgNVBAYTAkNO\nMSUwIwYDVQQKExxUcnVzdEFzaWEgVGVjaG5vbG9naWVzLCBJbmMuMSUwIwYDVQQD\nExxUcnVzdEFzaWEgRFYgVExTIFJTQSBDQSAyMDI1MIICIjANBgkqhkiG9w0BAQEF\nAAOCAg8AMIICCgKCAgEA0fuEmuBIsN6ZZVq+gRobMorOGIilTCIfQrxNpR8FUZ9R\n/GfbiekbiIKphQXEZ7N1uBnn6tXUuZ32zl6jPkZpHzN/Bmgk1BWSIzVc0npMzrWq\n/hrbk5+KddXJdsNpeG1+Q8lc8uVMBrztnxaPb7Rh7yQCsMrcO4hgVaqLJWkVvEfW\nULtoCHQnNaj4IroG6VxQf1oArQ8bPbwpI02lieSahRa78FQuXdoGVeQcrkhtVjZs\nON98vq5fPWZX2LFv7e5J6P9IHbzvOl8yyQjv+2/IOwhNSkaXX3bI+//bqF9XW/p7\n+gsUmHiK5YsvLjmXcvDmoDEGrXMzgX31Zl2nJ+umpRbLjwP8rxYIUsKoEwEdFoto\nAid59UEBJyw/GibwXQ5xTyKD/N6C8SFkr1+myOo4oe1UB+YgvRu6qSxIABo5kYdX\nFodLP4IgoVJdeUFs1Usa6bxYEO6EgMf5lCWt9hGZszvXYZwvyZGq3ogNXM7eKyi2\n20WzJXYMmi9TYFq2Fa95aZe4wki6YhDhhOO1g0sjITGVaB73G+JOCI9yJhv6+REN\nD40ZpboUHE8JNgMVWbG1isAMVCXqiADgXtuC+tmJWPEH9cR6OuJLEpwOzPfgAbnn\n2MRu7Tsdr8jPjTPbD0FxblX1ydW3RG30vwLF5lkTTRkHG9epMgpPMdYP7nY/08MC\nAwEAAaOCAVYwggFSMBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFLQSKKW0\nwB2fKXFpPNkRlkp1aVDAMB8GA1UdIwQYMBaAFE4iVCAYlebjbuYP+vq5Eu0GF485\nMA4GA1UdDwEB/wQEAwIBhjAdBgNVHSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIw\ndgYIKwYBBQUHAQEEajBoMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2Vy\ndC5jb20wQAYIKwYBBQUHMAKGNGh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9E\naWdpQ2VydEdsb2JhbFJvb3RHMi5jcnQwQgYDVR0fBDswOTA3oDWgM4YxaHR0cDov\nL2NybDMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0R2xvYmFsUm9vdEcyLmNybDARBgNV\nHSAECjAIMAYGBFUdIAAwDQYJKoZIhvcNAQELBQADggEBAJ4a3svh316GY2+Z7EYx\nmBIsOwjJSnyoEfzx2T699ctLLrvuzS79Mg3pPjxSLlUgyM8UzrFc5tgVU3dZ1sFQ\nI4RM+ysJdvIAX/7Yx1QbooVdKhkdi9X7QN7yVkjqwM3fY3WfQkRTzhIkM7mYIQbR\nr+y2Vkju61BLqh7OCRpPMiudjEpP1kEtRyGs2g0aQpEIqKBzxgitCXSayO1hoO6/\n71ts801OzYlqYW9OQQQ2GCJyFbD6XHDjdpn+bWUxTKWaMY0qedSCbHE3Kl2QEF0C\nynZ7SbC03yR+gKZQDeTXrNP1kk5Qhe7jSXgw+nhbspe0q/M1ZcNCz+sPxeOwdCcC\ngJE=\n-----END CERTIFICATE-----",
        "priKey": "-----BEGIN PRIVATE KEY-----\n\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+YzG5hLmEZpUB\nrEG4WwDsu3nsBvfkr7pAA6nsNdqjOMrTdCpidf0xmnxh1l5BERJ+sNmdydJMfUZD\nf0RFw7yk9mLBf5RjNxxXFBWglaD8oGv2jXpFeRSqX5I9eP/nxKbubNaDVRgiGncn\nAHr3tfEgnw73sagyrrBYh0QCXWDqWZ7/CQWxKI5SjE3AgiuZe1rSodPFNAP1bBPu\nehXXnBSYlqEoZPliecxs+F3FFZkEgiskdkwYeahEPqWrsY3VjOSlqxrTKqGwdDkg\nzuE4qjVp92A7gj0RoqjlD9Q6B65qkC9QNVAwLvzFmY4wRt/IMFfEbJZ4aDTCZ+50\n6Lno1wcNAgMBAAECggEACwuCJPsYMCArYM93eJR+9zzhE9pLo062hWQxBW0SZAm1\napMAqnmh2LDXqm1fRnMRGZx043yD4MAbxWqqsUlrtj48+HDIUQEvebXGk2xazI0Z\n9lG62DDwC/pDZ6GPZwi3jnlt8GyNW90hMHgMqjY56OSRX7lEwrvzqw8d2O1F5BJ5\nC88PLoBGS7jo0l0KAa7vvCQvqTxBW8hQlaCgykCM+CVFUUIE4e/DXvuCtvB/Jrv/\nIG0I6BdBJ1TO51modWxrAOJAGNC+VP5fDMzgpycy4UO8s/1MDRNMr9UolWStVhVY\nv7JbS07cgIwEFN4KKvQRpOFZG2q6Tmmy1c0B9PSBGQKBgQD/3vLoCLS3alKZckSU\nH/2xAPcJ9mPWeL1DcDDieKrBDv4tOXIFR8IaFMlCxNIpqz7qkwHow9BISmzRs7S2\nC9/m+ARej+WIzsfmNMqaydKkPUf6avXnNLdMQZG6EUlT0si4Iob5FjczaLZyvuuA\n0Mt9gk+Xs5JC0zWW8qd+JrgsqwKBgQC+e8lsmhRxPAqI24O6Te4mCwpHn/R/XIUL\nE6764vWwJAqNFJDFyEIuDWKReg33ab/T3UK9wB09DtSBaGVbSJtSKTCztQGNYqLC\neyvnW1NSqIlKF4RjK3kuXzoz19vuZ6hNOiFptTowjotDPpRmTl9KgXlgfCCRkkbc\nl61i8tarJwKBgQCDE45ySYtybngz/XKeQykuFOV46AzLIP0r3/xa+B/ZWLnjJwt/\nIvyPadiUaMmU6RIJDxgqSq2XavEGGD5aCAlChAmQ+7xFclC7YI3t77gFxRLreQHR\n2JKR8QEbRaG/3DpRAfcNAVFz94+HhsCUM+IawLfPagFiVFqeol4lZOZykwKBgFth\nZzACeuwXsbYWGQu3dxgpE7VotxKif/DgcIFLgDIQGD+2Lf20JIuTQEYqF6kpwi0R\naIM/Nsej5a5vNrCkFF9GA2cy3pvFRe+mx1kmJsLwt2wj/A7XPDtS08krNQcaE1N5\nH65mkpPYzlZkHy01S+GiW2g+JCGx2uzYlwVxGirhAoGBANvysFVEvwSmqgnGCsFv\nQHD3S50nGHiDR+xShD+O0q8J3UBl7HPyWOjiHl5KvYkm0xhzyOwAZNV6r1Pgx0vE\nGJKCNgmyOmS7vJroL/YipO0ihdz2wRRYb4BYU41aoxKoMjFWT0/Bp866RraN2bfM\nPc/jxKA5lmMeYRehm3LyXEuh\n-----END PRIVATE KEY-----",
        "expireCheckEnable": True
    }
    
    print("\n--- 更新证书 ---")
    response = test_update_certificate(bucket_name, domain, cert_name, update_data)
    print("响应内容: {}".format(response))