#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import ast
import io
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
APIS_ROOT = os.path.join(SKILL_DIR, "apis")
OUTPUT = os.path.join(SKILL_DIR, "references", "api_map.json")


def _read_text(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_source(path):
    with io.open(path, "rb") as f:
        return f.read()


def _write_text(path, content):
    with io.open(path, "w", encoding="utf-8") as f:
        try:
            content = content.decode("utf-8")
        except Exception:
            pass
        f.write(content)


def _rel_posix(path, base):
    return os.path.relpath(path, base).replace(os.sep, "/")


def _iter_py_files(root):
    for base, _, files in os.walk(root):
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def extract_action(py_file):
    rel = _rel_posix(py_file, SKILL_DIR)
    rel_api = _rel_posix(py_file, APIS_ROOT)
    source = _read_source(py_file)
    module = ast.parse(source)

    target = None
    functions = [n for n in module.body if isinstance(n, ast.FunctionDef)]
    for node in functions:
        if node.name.startswith("test_"):
            target = node
            break
    if target is None and len(functions) == 1:
        target = functions[0]
    if target is None:
        return None

    args = []
    for a in target.args.args:
        if hasattr(a, "arg"):
            args.append(a.arg)
        elif hasattr(a, "id"):
            args.append(a.id)
    defaults = target.args.defaults
    required_count = len(args) - len(defaults)

    parts = rel_api.split("/")
    stem = os.path.splitext(parts[-1])[0]
    if len(parts) == 3:
        action = "{}/{}/{}".format(parts[0], parts[1], os.path.splitext(parts[2])[0])
    else:
        action = "{}/{}".format(parts[0], stem)

    return {
        "action": action,
        "file": rel,
        "function": target.name,
        "required": args[:required_count],
        "optional": args[required_count:],
    }


def main():
    actions = {}
    for py in sorted(_iter_py_files(APIS_ROOT)):
        data = extract_action(py)
        if data:
            actions[data["action"]] = data

    payload = {
        "version": 1,
        "notes": [
            "params must be JSON object mapped to function keyword arguments",
            "set environment variables Access_key and Secret_key before execution",
        ],
        "actions": [actions[k] for k in sorted(actions)],
    }

    _write_text(OUTPUT, json.dumps(payload, ensure_ascii=False, indent=2))
    print("updated {} with {} actions".format(OUTPUT, len(payload["actions"])))


if __name__ == "__main__":
    main()
