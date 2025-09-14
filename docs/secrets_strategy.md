# Secrets Strategy（Trial → Production）
- Trial: K8s Secret / SOPS PoC（Gitに秘匿は載せない）
- Production: クラウド Secret + 鍵レス認証（IRSA/Workload Identity 等）
- ローテーション試験: 反映時間と挙動を Evidence 記録
- 監査: 読み出しログ可視化と警報
