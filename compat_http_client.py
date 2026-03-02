#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small http.client compatibility shim for Python 2/3."""

try:
    from http.client import HTTPSConnection, HTTPConnection
except Exception:  # Python 2
    from httplib import HTTPSConnection, HTTPConnection

__all__ = ["HTTPSConnection", "HTTPConnection"]
