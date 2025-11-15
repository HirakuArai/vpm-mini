/ask update_north_star 仕様メモ（M-2）
1. 目的と位置づけ

フェーズ:

開発フェーズ: Phase 2 後半（Runner + /ask / Goal-M2）

記憶フェーズ: M-2（ルール運用 → 半自動化）

ゴール:

直近の Evidence / PR / Guard 結果をもとに、

STATE/current_state.md（人間向け 北極星）

data/vpm_memory_min.json（VPM 向け 北極星）

に対する「更新候補パッチ」を /ask で自動生成する。

この段階では「AI は案だけ出す / 適用は人間が行う」。

2. インターフェース（/ask の呼び方）

GitHub Issue / PR コメントの 1 行目:

/ask update_north_star

2 行目以降に、AI に渡すコンテキストを貼る:

最近の Evidence / PR / Guard 結果の要約 JSON（CONTEXT_JSON）を 1 つ貼る。

この M-2 入口では、CONTEXT_JSON は手作業または簡単なスクリプトからのコピペでよい。

例:

/ask update_north_star
下記コンテキストをもとに、STATE と vpm_memory_min.json の更新案を出してください。

CONTEXT_JSON:
{ ... }

3. 入力フォーマット（CONTEXT_JSON）
3.1 フィールド構成（暫定）

CONTEXT_JSON は、最低限以下の形を想定する。

{
  "recent_evidence_runs": [
    {
      "id": "apply_hello_dev_20251115T183901Z",
      "type": "codex_run",
      "reports_dir": "reports/codex_runs/apply_hello_dev_20251115T183901Z",  # pragma: allowlist secret (sample reports dir)
      "summary": "kind vpm-mini 上で hello-ksvc を S5 apply。READY=True を確認済み。",
      "status": "success",
      "related_files": [
        "infra/k8s/overlays/dev/hello-ksvc.yaml"
      ],
      "timestamp": "2025-11-15T18:39:01+09:00"
    }
  ],
  "recent_prs": [
    {
      "number": 719,
      "title": "Fix: executor kubectl subcmd detection",
      "state": "merged",
      "labels": ["ops", "runner", "ssot"],
      "merged_at": "2025-11-10T00:00:00Z",
      "summary": "RUN_MODE=exec で main 直 push をやめ、reports/** 生成のみに限定。"
    }
  ],
  "current_state_excerpt": "STATE/current_state.md の関連部分の抜粋テキスト",
  "current_memory_excerpt": {
    "goal_m2": {
      "runner_pipe": {
        "s5_apply": {
          "evidence_loop": "done"
        }
      },
      "last_successful_s5_apply": {
        "id": "hello_s5_apply_success_20251115",
        "reports_dir": "reports/codex_runs/apply_hello_dev_20251115T183901Z"  # pragma: allowlist secret (sample reports dir)
      }
    }
  },
  "notes_from_human": "人間が補足したいことがあればここに自由記述"
}


必須フィールド（暫定）:

recent_evidence_runs（配列だが 1 件でもよい）

recent_prs（空配列可）

current_state_excerpt（関連する STATE の抜粋）

current_memory_excerpt（関連するメモリ部分）

ここでは JSON の内容は人間が作る前提。
自動生成パイプは M-3 以降に実装する。

4. 出力フォーマット（AI が返すべき形）

AI は、必ず以下の JSON だけを返す（説明テキストは rationale に埋め込む）。

{
  "state_patch": [
    {
      "match_heading": "Goal-M2 / Hello S5 成功ルート Evidence",
      "operation": "append_after_heading",
      "markdown": "- 2025-11-15: Hello S5 の S5 apply 成功 run (apply_hello_dev_20251115T183901Z) を正式な証跡として登録済み。"
    }
  ],
  "memory_patch": {
    "merge": {
      "goal_m2": {
        "runner_pipe": {
          "s5_apply": {
            "evidence_loop": "done"
          }
        },
        "last_successful_s5_apply": {
          "id": "hello_s5_apply_success_20251115",
          "manifest": "infra/k8s/overlays/dev/hello-ksvc.yaml",
          "reports_dir": "reports/codex_runs/apply_hello_dev_20251115T183901Z",  # pragma: allowlist secret (sample reports dir)
          "note": "Hello S5 apply success (kind vpm-mini, READY=True)",
          "updated_at": "2025-11-15T00:00:00Z"
        }
      }
    }
  },
  "rationale": [
    "Hello S5 成功 run が reports/** に存在し、STATE の該当セクションにまだ記述がなければ追記する。",
    "vpm_memory_min.json では、goal_m2.runner_pipe.s5_apply.evidence_loop を done にし、last_successful_s5_apply を今回の run で上書きする。"
  ],
  "warnings": [
    "current_state_excerpt に既に同等の記述がある場合、state_patch を適用しないでください。",
    "他の run が同日に存在する場合、どれを last_successful とみなすか人間で確認してください。"
  ]
}

4.1 state_patch の解釈ルール（人間向け）

match_heading:

STATE/current_state.md 内の見出し（行頭 ## 等）と文字列一致を試みる。

人間が手で探し、「この見出しの直下に markdown を追記する」ための目印。

operation:

第一段階（M-2）では以下を想定:

append_after_heading: 見出しの直後に markdown を追記。

replace_section: 見出し行〜次の同レベル見出しを markdown で差し替える。

実際の編集は人間がエディタで行う。

4.2 memory_patch の解釈ルール（人間向け）

merge:

data/vpm_memory_min.json のルートに対してディープマージとして解釈する想定。

配列更新や削除などが必要になった場合は、将来的に json_patch など別形式を追加する。

5. DoD（M2-1 としての完了条件）

docs/memory/update_north_star_spec.md が main ブランチに追加されている。

このファイルは、/ask 実行時に参照される仕様として自己完結している。

対応 PR の説明文に、

Phase M-2 の入口として、

/ask update_north_star の入出力仕様を追加したこと
が記載されている。
