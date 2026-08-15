# Sample data

Ten ready-to-POST MCP `tools/call` requests for `remember_memory`, spanning a mix of
`preference` / `fact` / `note` / `task` kinds so a subsequent `recall_memory` or
`list_memories` has real variety to search over. Each file is a complete JSON-RPC
request body — no editing needed, just POST it as-is.

Use these to exercise the memory lifecycle without hand-writing payloads: **POST**
each file to store a memory, then **GET it back** via `recall_memory` (semantic
search) or `list_memories` (plain listing).

## Prerequisites

- A running Total Recall MCP endpoint — local (`http://localhost:4646`) or a
  deployed cloud ALB endpoint (see the [AWS deployment](../README.md#aws-deployment)
  and [Validate from cloud](../README.md#validate-from-cloud) sections of the
  project README).
- If the endpoint requires auth (`HTTP_AUTH_MODE=github`), a bearer token — see
  [`../scripts/get_github_token.sh`](../scripts/get_github_token.sh).

## POST: store all 10 sample memories

```bash
ENDPOINT="http://localhost:4646"          # or your cloud ALB endpoint
TOKEN=""                                  # set if the endpoint requires auth, e.g. TOKEN=$(../scripts/get_github_token.sh)

for f in sample_data/*.json; do
  echo "POST ${f}"
  curl -sS -X POST "${ENDPOINT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"} \
    -d @"${f}"
  echo
done
```

Or POST a single file:

```bash
curl -sS -X POST "${ENDPOINT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"} \
  -d @sample_data/01_dark_mode_preference.json
```

## GET: recall or list the memories back

**Semantic search** (`recall_memory` — finds relevant memories by meaning, not exact text):

```bash
curl -sS -X POST "${ENDPOINT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"} \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"recall_memory","arguments":{"query":"what editor theme does the user like","limit":5}}}'
```

**Plain listing** (`list_memories` — newest first, optionally filtered by `kind`):

```bash
curl -sS -X POST "${ENDPOINT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"} \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_memories","arguments":{"kind":"note","limit":20}}}'
```

## Files

| File | Kind | Content |
|---|---|---|
| `01_dark_mode_preference.json` | preference | Dark mode across apps/IDEs |
| `02_answer_style_preference.json` | preference | Prefers concise, bullet-point answers |
| `03_primary_language_fact.json` | fact | Primary language: Python (+ Go for CLIs) |
| `04_hackathon_project_fact.json` | fact | Building Total Recall MCP |
| `05_timezone_fact.json` | fact | Timezone: US Eastern |
| `06_deploy_review_note.json` | note | Review ARM64/Graviton Terraform fix before deploy |
| `07_https_hardening_note.json` | note | ALB is HTTP-only; needs ACM + HTTPS for real production |
| `08_cockroachdb_serverless_preference.json` | preference | Prefers CockroachDB Serverless for demos |
| `09_github_identity_fact.json` | fact | GitHub login → principal id mapping |
| `10_rotate_token_task.json` | task | Rotate demo GitHub PAT after recording |

## Cleanup

`remember_memory`'s response includes a memory `id`. To delete a sample memory,
call `forget_memory` with that id:

```bash
curl -sS -X POST "${ENDPOINT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"} \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"forget_memory","arguments":{"memory_id":"<id-from-remember-response>"}}}'
```
