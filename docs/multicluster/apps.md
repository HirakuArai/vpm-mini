# Multi-Cluster GitOps (Argo CD ApplicationSet)

本書は **cluster-a / cluster-b** を Argo CD に登録し、**ApplicationSet** で `infra/gitops/apps/` を両クラスタへ同期する運用手順の要点をまとめる。

## 1. 事前準備
- Argo CD サーバ稼働（`argocd` NS）
- 2 クラスタ（例: `kind-cluster-a`, `kind-cluster-b`）に到達できる kubeconfig

## 2. クラスタ登録 & ラベル
```bash
# 例: CLI で登録（self-hosted runner から）
argocd cluster add kind-cluster-a --name cluster-a --yes
argocd cluster add kind-cluster-b --name cluster-b --yes

# Cluster Secret に region ラベルを付与（ApplicationSet の selector で使用）
kubectl -n argocd label secret $(kubectl -n argocd get secret -l argocd.argoproj.io/secret-type=cluster -o name | grep cluster-a) region=a --overwrite
kubectl -n argocd label secret $(kubectl -n argocd get secret -l argocd.argoproj.io/secret-type=cluster -o name | grep cluster-b) region=b --overwrite
```

## 3. NodePort 差別化（dev/kind）
- **cluster-a**: 31380（ingressgateway:80）
- **cluster-b**: 32380（ingressgateway:80）

```bash
# 例: cluster-b の NodePort を 32380 にパッチ
kubectl --context kind-cluster-b -n istio-system patch svc istio-ingressgateway   -p '{"spec":{"ports":[{"name":"http2","port":80,"nodePort":32380}]}}'
```

## 4. ApplicationSet 設定
- **パス**: `infra/gitops/appset/`
- **ジェネレータ**: `clusters.selector.matchExpressions` で `region ∈ {a,b}`
- **テンプレート**: `root-app-{{name}}` を自動生成（path: `infra/gitops/apps` を同期）

## 5. 検証（スクリプト）
```bash
bash scripts/phase5_appset_verify.sh
# 期待: JSON に synced=true / healthy=true / a_http_200=true / b_http_200=true
#       http://localhost:31380/hello / http://localhost:32380/hello が 200
```

## 6. 運用ポイント
- **新クラスタ**: label 付与だけで自動検出（ゼロタッチ展開）
- **重大事故時**: cluster-a/b を独立運用しつつ GitOps 状態は ApplicationSet が担保
- **監査**: `reports/phase5_appset_verify.json` を証跡として保存
