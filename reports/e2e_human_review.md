# E2E Human Review v2 (worst 5 of 10)

**含まれる情報**: ソース抜粋 / GitHubリンク / 期待要約 / 差分 / 判定欄

## 1. id=ex09 (sim≈0.333)

**Source**: `scripts/annotate_sources.py` L6-10  [🔗open](https://github.com/HirakuArai/vpm-mini/blob/feat/p0-semantics-sanity/scripts/annotate_sources.py#L6-L10)

```text
STOP_DIRS = {".git","node_modules",".venv","venv","__pycache__",".pytest_cache",".DS_Store",".idea",".vscode",".mypy_cache"}
TEXT_EXT  = {".md",".txt",".py",".sh",".yaml",".yml",".json",".mdx",".ini",".cfg",".toml",".sql",".go",".ts",".js",".tsx",".jsx"}
EXTRA_KEYS = {"knative","kservice","hello","ko.local","kourier","serving","configmap","secret","x-dur-ms","p50","p95","avg","gatekeeper","spiffe","do d","auto-merge","--dry-run=client",":latest"}

def iter_files(root: pathlib.Path):
```

**expected**

> レイテンシ p50 < 1s を監視。

**diff (raw vs expected)**

```diff
--- 
+++ 
@@ -1,7 +1,5 @@
-計測:
-X-Dur-Ms
-の中央値が
+レイテンシ
+p50
+<
 1s
-未満かを監視する（p50
-<
-1s）。
+を監視。
```

- [ ] Accept  /  - [ ] Revise

---

## 2. id=ex05 (sim≈0.370)

**Source**: `scripts/annotate_sources.py` L6-10  [🔗open](https://github.com/HirakuArai/vpm-mini/blob/feat/p0-semantics-sanity/scripts/annotate_sources.py#L6-L10)

```text
STOP_DIRS = {".git","node_modules",".venv","venv","__pycache__",".pytest_cache",".DS_Store",".idea",".vscode",".mypy_cache"}
TEXT_EXT  = {".md",".txt",".py",".sh",".yaml",".yml",".json",".mdx",".ini",".cfg",".toml",".sql",".go",".ts",".js",".tsx",".jsx"}
EXTRA_KEYS = {"knative","kservice","hello","ko.local","kourier","serving","configmap","secret","x-dur-ms","p50","p95","avg","gatekeeper","spiffe","do d","auto-merge","--dry-run=client",":latest"}

def iter_files(root: pathlib.Path):
```

**expected**

> レイテンシ統計（p50/p95/avg）を reports に保存。

**diff (raw vs expected)**

```diff
--- 
+++ 
@@ -1,7 +1,3 @@
-運用:
+レイテンシ統計（p50/p95/avg）を
 reports
-に
-X-Dur-Ms
-の
-p50/p95/avg
-を集計して保存する。
+に保存。
```

- [ ] Accept  /  - [ ] Revise

---

## 3. id=ex07 (sim≈0.540)

**Source**: `scripts/annotate_sources.py` L6-10  [🔗open](https://github.com/HirakuArai/vpm-mini/blob/feat/p0-semantics-sanity/scripts/annotate_sources.py#L6-L10)

```text
STOP_DIRS = {".git","node_modules",".venv","venv","__pycache__",".pytest_cache",".DS_Store",".idea",".vscode",".mypy_cache"}
TEXT_EXT  = {".md",".txt",".py",".sh",".yaml",".yml",".json",".mdx",".ini",".cfg",".toml",".sql",".go",".ts",".js",".tsx",".jsx"}
EXTRA_KEYS = {"knative","kservice","hello","ko.local","kourier","serving","configmap","secret","x-dur-ms","p50","p95","avg","gatekeeper","spiffe","do d","auto-merge","--dry-run=client",":latest"}

def iter_files(root: pathlib.Path):
```

**expected**

> K8s manifest は --dry-run=client で妥当性確認済み。

**diff (raw vs expected)**

```diff
--- 
+++ 
@@ -1,7 +1,5 @@
-検証:
-kubectl
-apply
-を
+K8s
+manifest
+は
 --dry-run=client
-で実行し、manifest
-の妥当性を検査。
+で妥当性確認済み。
```

- [ ] Accept  /  - [ ] Revise

---

## 4. id=ex01 (sim≈0.582)

**Source**: `scripts/annotate_sources.py` L6-10  [🔗open](https://github.com/HirakuArai/vpm-mini/blob/feat/p0-semantics-sanity/scripts/annotate_sources.py#L6-L10)

```text
STOP_DIRS = {".git","node_modules",".venv","venv","__pycache__",".pytest_cache",".DS_Store",".idea",".vscode",".mypy_cache"}
TEXT_EXT  = {".md",".txt",".py",".sh",".yaml",".yml",".json",".mdx",".ini",".cfg",".toml",".sql",".go",".ts",".js",".tsx",".jsx"}
EXTRA_KEYS = {"knative","kservice","hello","ko.local","kourier","serving","configmap","secret","x-dur-ms","p50","p95","avg","gatekeeper","spiffe","do d","auto-merge","--dry-run=client",":latest"}

def iter_files(root: pathlib.Path):
```

**expected**

> Phase 2 完了。Knative/Hello KService は READY=True。次は Gatekeeper 導入（外部レジストリ禁止・:latest 禁止）。

**diff (raw vs expected)**

```diff
--- 
+++ 
@@ -1,10 +1,9 @@
-会議:
 Phase
 2
-の完了報告。Knative
-と
-Hello
+完了。Knative/Hello
 KService
-の
-READY
-を確認。
+は
+READY=True。次は
+Gatekeeper
+導入（外部レジストリ禁止・:latest
+禁止）。
```

- [ ] Accept  /  - [ ] Revise

---

## 5. id=ex06 (sim≈0.704)

**Source**: `scripts/annotate_sources.py` L6-10  [🔗open](https://github.com/HirakuArai/vpm-mini/blob/feat/p0-semantics-sanity/scripts/annotate_sources.py#L6-L10)

```text
STOP_DIRS = {".git","node_modules",".venv","venv","__pycache__",".pytest_cache",".DS_Store",".idea",".vscode",".mypy_cache"}
TEXT_EXT  = {".md",".txt",".py",".sh",".yaml",".yml",".json",".mdx",".ini",".cfg",".toml",".sql",".go",".ts",".js",".tsx",".jsx"}
EXTRA_KEYS = {"knative","kservice","hello","ko.local","kourier","serving","configmap","secret","x-dur-ms","p50","p95","avg","gatekeeper","spiffe","do d","auto-merge","--dry-run=client",":latest"}

def iter_files(root: pathlib.Path):
```

**expected**

> kourier/serving の Deployments が全て Available。

**diff (raw vs expected)**

```diff
--- 
+++ 
@@ -1,3 +1,5 @@
-検証:
-kourier-system/knative-serving
-の全DeploymentがAvailableかを確認した。
+kourier/serving
+の
+Deployments
+が全て
+Available。
```

- [ ] Accept  /  - [ ] Revise

---

