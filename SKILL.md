---
name: miku-api-operator
description: 将自然语言需求映射到本地 Miku API 示例脚本并按结构化参数安全执行。用户用中文描述创建/查询/更新/删除 Miku 资源（空间、流、域名、证书、录制、转码模板、转推任务、统计、API Key）时使用。
metadata:
  {
    "openclaw":
      {
        "emoji": "📍",
        "requires": {"bins": ["python"], "env": ["Access_key", "Secret_key"] }
      }
  }
---

# Miku API 操作器

使用此 skill 将业务描述转换为可执行的 API 调用。API 脚本已内置在 `apis/` 目录中，skill 可独立分发使用。

## 先读

1. 读取 `references/api_map.json`，定位 `action -> file -> function -> required/optional`。
2. 仅在参数语义不清晰时读取命中的脚本文件。
3. 统一通过 `scripts/run_miku_api.py` 执行，不修改脚本 `__main__` 块。
4. 项目新增/删除接口脚本后，运行 `scripts/sync_api_map.py` 同步映射。

## 执行流程

1. 从用户描述中提取意图。
2. 在 `references/api_map.json` 中匹配一个 action。
3. 按函数关键字参数名构造 JSON 对象。
4. 若缺少必填参数，只追问缺失字段。
5. 准备 AK/SK（必须）：

```bash
export Access_key='你的AK'
export Secret_key='你的SK'
```

或在 `skills/miku-api-operator/config.json` 中配置：

```json
{
  "Access_key": "你的AK",
  "Secret_key": "你的SK"
}
```

6. 执行：

```bash
python skills/miku-api-operator/scripts/run_miku_api.py \
  --action "<action>" \
  --params-json '<json-object>'
```

或直接给中文意图自动匹配 action：

```bash
python skills/miku-api-operator/scripts/run_miku_api.py \
  --intent "获取空间列表" \
  --params-json '{}' \
  --ak "<AK>" \
  --sk "<SK>"
```

或使用命令参数显式传入：

```bash
python skills/miku-api-operator/scripts/run_miku_api.py \
  --action "<action>" \
  --params-json '<json-object>' \
  --ak "<AK>" \
  --sk "<SK>"
```

7. 返回：
- 已选择 action
- 请求参数（对敏感字段脱敏）
- 原始 API 响应（`HTTP xxx: ...`）

## 辅助发现

- 列出全部 action：
```bash
python skills/miku-api-operator/scripts/run_miku_api.py --list
```

- 按关键字搜索 action：
```bash
python skills/miku-api-operator/scripts/run_miku_api.py --search "转推"
```

- 从项目脚本重建接口映射（全量整合）：
```bash
python skills/miku-api-operator/scripts/sync_api_map.py
```
脚本会扫描 `skills/miku-api-operator/apis/**/*.py` 并重建映射。

- Python 兼容说明：
  - 需要可用的 Python 3 运行时（`python --version` 为 3.x）。

## 约束

- 执行前要求环境变量存在：`Access_key`、`Secret_key`。
- 不接受无凭证执行 action 调用。缺少 AK/SK 时先提示补齐，再继续。
- 回复中不得输出完整私钥、证书、Token。
- 仅在用户意图不清时拒绝破坏性操作；意图明确则按请求执行。
- 默认一步只执行一个 action，除非用户明确要求批量。
