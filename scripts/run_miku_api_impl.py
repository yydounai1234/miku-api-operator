#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import io
import json
import os
import re
import sys

try:
    import importlib.util as importlib_util
except Exception:
    importlib_util = None
try:
    import imp
except Exception:
    imp = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))
API_MAP_PATH = os.path.join(SKILL_DIR, "references", "api_map.json")
DEFAULT_CONFIG_PATH = os.path.join(SKILL_DIR, "config.json")

# Ensure helper modules under skill root are importable (for API scripts too).
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

LEGACY_ACTION_ALIASES = {
    "live-stream-transcoding-template/add_transcoding_templete": "live-stream-transcoding-template/add_transcoding_template",
    "live-stream-transcoding-template/delete_transcoding_templete": "live-stream-transcoding-template/delete_transcoding_template",
    "live-stream-transcoding-template/get_templete_info": "live-stream-transcoding-template/get_template_info",
    "live-stream-transcoding-template/get_templete_list": "live-stream-transcoding-template/get_template_list",
    "live-stream-transcoding-template/update_transcoding_templete": "live-stream-transcoding-template/update_transcoding_template",
}

VERB_ALIASES = {
    "list": ["list", "列表", "列出", "查询", "查看"],
    "get": ["get", "查询", "查看", "获取", "详情"],
    "query": ["query", "查询", "获取"],
    "create": ["create", "创建", "新建", "新增"],
    "add": ["add", "添加", "新增"],
    "update": ["update", "修改", "更新", "配置"],
    "edit": ["edit", "编辑", "修改"],
    "delete": ["delete", "删除", "移除"],
    "bind": ["bind", "绑定"],
    "unbind": ["unbind", "解绑", "取消绑定"],
    "start": ["start", "启动", "开始"],
    "stop": ["stop", "停止", "关闭"],
    "upload": ["upload", "上传"],
    "rename": ["rename", "重命名"],
    "ban": ["ban", "禁用", "封禁"],
    "unban": ["unban", "解禁", "解除封禁"],
    "resolve": ["resolve", "解析", "dns", "httpdns"],
}

NOUN_ALIASES = {
    "bucket": ["bucket", "buckets", "空间", "hub"],
    "stream": ["stream", "流", "流名"],
    "domain": ["domain", "域名"],
    "certificate": ["certificate", "cert", "证书"],
    "recording": ["recording", "录制"],
    "merge": ["merge", "混流"],
    "transcoding": ["transcoding", "转码"],
    "template": ["template", "模版", "模板"],
    "pub": ["pub", "转推"],
    "task": ["task", "任务"],
    "apikey": ["apikey", "api key", "密钥"],
    "stat": ["stat", "统计", "流量", "日志"],
    "dns": ["dns", "httpdns", "解析"],
    "play": ["play", "播放"],
    "publish": ["publish", "推流"],
}


def _read_text(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def to_text(value):
    if value is None:
        return u""
    try:
        return value.decode("utf-8")  # py2 bytes
    except Exception:
        return u"{}".format(value)


def load_api_map():
    data = json.loads(_read_text(API_MAP_PATH))
    actions = dict((item["action"], item) for item in data["actions"])
    return data, actions


def parse_params(args):
    if args.params_file:
        return json.loads(_read_text(args.params_file))
    if args.params_json:
        return json.loads(args.params_json)
    return {}


def load_config(config_path):
    if not os.path.exists(config_path):
        return {}
    data = json.loads(_read_text(config_path))
    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object: {}".format(config_path))
    return data


def apply_credentials(args, config):
    if args.ak:
        os.environ["Access_key"] = args.ak
    elif not os.getenv("Access_key"):
        cfg_ak = config.get("Access_key") or config.get("ak") or config.get("access_key")
        if cfg_ak:
            os.environ["Access_key"] = str(cfg_ak)

    if args.sk:
        os.environ["Secret_key"] = args.sk
    elif not os.getenv("Secret_key"):
        cfg_sk = config.get("Secret_key") or config.get("sk") or config.get("secret_key")
        if cfg_sk:
            os.environ["Secret_key"] = str(cfg_sk)


def normalize_text(text):
    return to_text(text).strip().lower()


def split_words(text):
    return re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_]+", normalize_text(text))


def score_action(intent, item):
    intent_l = normalize_text(intent)
    tokens = split_words(intent)
    action = item["action"]
    action_name = action.split("/")[-1]
    fields = " ".join([
        action,
        item["file"],
        item["function"],
        " ".join(item["required"]),
        " ".join(item["optional"]),
    ]).lower()
    score = 0

    if action_name in intent_l:
        score += 10
    if action in intent_l:
        score += 12

    for token in tokens:
        if token in fields:
            score += 2

    action_words = action_name.split("_")
    for word in action_words:
        normalized_word = word[:-1] if word.endswith("s") else word
        for alias in VERB_ALIASES.get(word, []):
            if alias in intent_l:
                score += 4
        if normalized_word != word:
            for alias in VERB_ALIASES.get(normalized_word, []):
                if alias in intent_l:
                    score += 4
        for alias in NOUN_ALIASES.get(word, []):
            if alias in intent_l:
                score += 4
        if normalized_word != word:
            for alias in NOUN_ALIASES.get(normalized_word, []):
                if alias in intent_l:
                    score += 4

    module = action.split("/")[0]
    module_aliases = {
        "bucket-management": ["空间", "bucket"],
        "stream-management": ["流", "stream"],
        "domain-management": ["域名", "domain"],
        "certificate-management": ["证书", "certificate", "cert"],
        "recording-management": ["录制", "recording", "截图", "snapshot"],
        "live-stream-transcoding-template": ["转码", "模板", "模版", "template"],
        "pub-relay": ["转推", "pub", "任务"],
        "statistics": ["统计", "流量", "日志", "history", "stat"],
        "utilities": ["工具", "播放", "推流", "apikey", "api key"],
    }
    for alias in module_aliases.get(module, []):
        if alias in intent_l:
            score += 3

    query_words = {"获取", "查询", "查看", "列表", "list", "get", "query"}
    mutate_words = {"创建", "新建", "新增", "更新", "修改", "删除", "绑定", "解绑", "启动", "停止", "create", "update", "delete"}
    action_set = set(action_words)
    has_query_intent = any((w in intent_l) for w in query_words)
    has_mutate_intent = any((w in intent_l) for w in mutate_words)
    action_is_query = bool(action_set & {"get", "list", "query"})
    action_is_mutate = bool(action_set & {"create", "add", "update", "edit", "delete", "bind", "unbind", "start", "stop", "upload", "rename", "ban", "unban"})
    if has_query_intent and action_is_query:
        score += 5
    if has_query_intent and action_is_mutate:
        score -= 4
    if has_mutate_intent and action_is_mutate:
        score += 5
    if has_mutate_intent and action_is_query:
        score -= 2

    if "列表" in intent_l:
        if "list" in action_set:
            score += 6
        if "get" in action_set or "query" in action_set:
            score -= 3

    return score


def resolve_intent(actions, intent, topk=5):
    ranked = []
    for key, item in actions.items():
        s = score_action(intent, item)
        if s > 0:
            ranked.append((s, key))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return ranked[:topk]


def load_callable(file_rel, func_name):
    candidates = [os.path.join(SKILL_DIR, file_rel), os.path.join(PROJECT_ROOT, file_rel)]
    file_path = None
    for c in candidates:
        if os.path.exists(c):
            file_path = c
            break
    if file_path is None:
        raise IOError("Script not found: {}".format(file_rel))

    module_name = "miku_api_" + re.sub(r"[^0-9a-zA-Z_]", "_", str(file_rel))

    if importlib_util is not None:
        spec = importlib_util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot import script: {}".format(file_path))
        module = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif imp is not None:
        module = imp.load_source(module_name, file_path)
    else:
        raise RuntimeError("No available module loader for {}".format(file_path))

    func = getattr(module, func_name, None)
    if func is None:
        raise AttributeError("Function {} not found in {}".format(func_name, file_path))
    return func


def print_actions(actions):
    for key in sorted(actions):
        item = actions[key]
        required = ",".join(item["required"]) if item["required"] else "-"
        optional = ",".join(item["optional"]) if item["optional"] else "-"
        print("{}\n  file: {}\n  required: {}\n  optional: {}".format(key, item["file"], required, optional))


def search_actions(actions, keyword):
    kw = keyword.lower()
    for key in sorted(actions):
        item = actions[key]
        corpus = " ".join([
            key,
            item["file"],
            item["function"],
            " ".join(item["required"]),
            " ".join(item["optional"]),
        ]).lower()
        if kw in corpus:
            print(key)


def ensure_auth_env():
    return [k for k in ("Access_key", "Secret_key") if not os.getenv(k)]


def normalize_action(action):
    if action in LEGACY_ACTION_ALIASES:
        return LEGACY_ACTION_ALIASES[action]
    return action.replace("templete", "template")


def main():
    parser = argparse.ArgumentParser(description="Run local Miku API demo functions by action key.")
    parser.add_argument("--action", help="Action key from references/api_map.json")
    parser.add_argument("--intent", help="Natural language intent. Will auto-resolve to one action.")
    parser.add_argument("--params-json", help="JSON object for function kwargs")
    parser.add_argument("--params-file", help="Path to JSON file for function kwargs")
    parser.add_argument("--list", action="store_true", help="List all available actions")
    parser.add_argument("--search", help="Search actions by keyword")
    parser.add_argument("--topk", type=int, default=5, help="Top-k candidates when resolving intent")
    parser.add_argument("--ak", help="Access_key. If set, it overrides current environment.")
    parser.add_argument("--sk", help="Secret_key. If set, it overrides current environment.")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to config.json for default credentials.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and validate only, do not call API")
    parser.add_argument("--no-auth-check", action="store_true", help="Skip Access_key/Secret_key check (use only for dry validation).")
    args = parser.parse_args()

    _, actions = load_api_map()

    if args.list:
        print_actions(actions)
        return 0

    if args.search:
        search_actions(actions, args.search)
        return 0

    resolved_candidates = []
    if (not args.action) and args.intent:
        resolved_candidates = resolve_intent(actions, args.intent, topk=args.topk)
        if not resolved_candidates:
            print("Error: cannot resolve intent: {}".format(args.intent), file=sys.stderr)
            return 2
        args.action = resolved_candidates[0][1]
        print("Resolved action: {}".format(args.action), file=sys.stderr)

    if not args.action:
        print("Error: --action is required unless using --list or --search", file=sys.stderr)
        return 2

    original_action = args.action
    args.action = normalize_action(args.action)
    if args.action != original_action:
        print("Normalized legacy action: {} -> {}".format(original_action, args.action), file=sys.stderr)

    item = actions.get(args.action)
    if item is None:
        print("Error: unknown action: {}".format(args.action), file=sys.stderr)
        return 2

    params = parse_params(args)
    if not isinstance(params, dict):
        print("Error: params must be a JSON object", file=sys.stderr)
        return 2

    missing_required = [name for name in item["required"] if name not in params]
    if missing_required:
        print("Error: missing required params: {}".format(", ".join(missing_required)), file=sys.stderr)
        return 2

    accepted = set(item["required"]) | set(item["optional"])
    extra = [name for name in params if name not in accepted]
    if extra:
        print("Error: unexpected params: {}".format(", ".join(extra)), file=sys.stderr)
        return 2

    config = load_config(args.config)
    apply_credentials(args, config)
    if args.dry_run:
        print(json.dumps({
            "resolved_action": args.action,
            "required": item["required"],
            "optional": item["optional"],
            "params": params,
            "intent_candidates": resolved_candidates,
        }, ensure_ascii=False, indent=2))
        return 0

    if not args.no_auth_check:
        missing = ensure_auth_env()
        if missing:
            print(
                "Error: missing credentials. Provide Access_key and Secret_key via env or CLI.\n"
                "Config file checked: {}\n"
                "Example:\n"
                "  Access_key='your_ak' Secret_key='your_sk' python skills/miku-api-operator/scripts/run_miku_api.py --action '<action>' --params-json '{{}}'\n"
                "or:\n"
                "  python skills/miku-api-operator/scripts/run_miku_api.py --action '<action>' --params-json '{{}}' --ak 'your_ak' --sk 'your_sk'".format(args.config),
                file=sys.stderr,
            )
            print("Missing: {}".format(", ".join(missing)), file=sys.stderr)
            return 2

    func = load_callable(item["file"], item["function"])
    result = func(**params)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
