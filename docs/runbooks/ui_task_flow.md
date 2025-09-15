# UI Task Flow (Trial Mode)

## 目的
最小UI `/ui/task` と API `/api/v1/tasks` で入力→保存→Evidence（md+jsonl）を自動化し、摩擦を計測可能にする。

## 手順（ローカル）
```bash
uvicorn app.__init__:app --reload --port 8080
open http://127.0.0.1:8080/ui/task
```

## API確認
```bash
curl -s -X POST http://127.0.0.1:8080/api/v1/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"Trial input","description":"first run","priority":"mid","tags":["trial","ui"]}'
```

## Evidence
`reports/trial_tasks/<trace_id>_YYYYMMDD_HHMMSS.md` と `reports/trial_tasks/tasks_YYYYMMDD.jsonl`