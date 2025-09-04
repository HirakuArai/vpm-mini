# E2E Human Review (worst 5 of 10)

## 1. id=ex09 (sim≈0.333)

**raw**

> 計測: X-Dur-Ms の中央値が 1s 未満かを監視する（p50 < 1s）。

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

## 2. id=ex05 (sim≈0.370)

**raw**

> 運用: reports に X-Dur-Ms の p50/p95/avg を集計して保存する。

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

## 3. id=ex07 (sim≈0.540)

**raw**

> 検証: kubectl apply を --dry-run=client で実行し、manifest の妥当性を検査。

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

## 4. id=ex01 (sim≈0.582)

**raw**

> 会議: Phase 2 の完了報告。Knative と Hello KService の READY を確認。

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

## 5. id=ex06 (sim≈0.704)

**raw**

> 検証: kourier-system/knative-serving の全DeploymentがAvailableかを確認した。

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

