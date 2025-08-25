from prometheus_client import Gauge

try:
    # rouge_score は pip のモジュール名が rouge_score
    from rouge_score import rouge_scorer
except Exception:
    rouge_scorer = None

ROUGE_L = Gauge("rouge_l_score", "ROUGE-L score", ["role"])


def compute_rouge_l(hyp: str, ref: str) -> float:
    if rouge_scorer is None:
        return 0.0
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    s = scorer.score(ref, hyp)["rougeL"].fmeasure
    return float(s)


def update(role: str, hyp: str, ref: str):
    try:
        s = compute_rouge_l(hyp, ref)
    except Exception:
        s = 0.0
    ROUGE_L.labels(role).set(s)
