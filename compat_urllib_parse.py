#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small urllib.parse compatibility shim for Python 2/3."""

try:
    from urllib.parse import urlencode, urlparse, quote
except Exception:  # Python 2
    from urllib import urlencode, quote
    from urlparse import urlparse

__all__ = ["urlencode", "urlparse", "quote"]
