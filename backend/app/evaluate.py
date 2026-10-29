"""Score the extractor on hand-labelled cases.   Run:  python -m app.evaluate"""
import sys
import time

from . import extract, resolve
from .eval_cases import CASES
from .schemas import Article


def key_name(x: str) -> str:
    n = resolve.norm(x)
    return resolve.norm(resolve.SEED_INDEX.get(n, x))


def name_match(a: str, b: str) -> bool:
    return a == b or (min(len(a), len(b)) >= 4 and (a in b or b in a))


def rel_match(p: tuple, g: tuple) -> bool:
    return p[0] == g[0] and name_match(p[2], g[2]) and (p[0] == "AFFECTS" or name_match(p[1], g[1]))


def norm_rel(rel: str, src: str, tgt: str) -> tuple:
    return (rel, key_name(src), key_name(tgt))


def score_case(preds: list, gold: list, optional: list | tuple = ()) -> tuple[int, list, list]:
    """Return (true positives, false positives, missed gold relations)."""
    gold_left, tp, fp = list(gold), 0, []
    for p in preds:
        hit = next((g for g in gold_left if rel_match(p, g)), None)
        if hit is not None:
            gold_left.remove(hit)
            tp += 1
        elif any(rel_match(p, o) for o in optional) or any(rel_match(p, g) for g in gold):
            continue  # optional, or a duplicate of something already matched
        else:
            fp.append(p)
    return tp, fp, gold_left


def main(delay: float = 4.0) -> None:
    tot_tp = tot_fp = tot_fn = errors = 0
    neg_total = neg_clean = 0
    for case in CASES:
        art = Article(url=f"eval://{case['id']}", title=case["id"], text=case["text"])
        try:
            result, _ = resolve.resolve(extract.extract(art), [])
        except Exception as exc:
            errors += 1
            print(f"[ERROR] {case['id']}: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        preds = [norm_rel(r.relation.value, r.source, r.target) for r in result.relations]
        gold = [norm_rel(*g) for g in case["gold"]]
        opt = [norm_rel(*o) for o in case.get("optional", [])]
        tp, fp, fn = score_case(preds, gold, opt)
        tot_tp, tot_fp, tot_fn = tot_tp + tp, tot_fp + len(fp), tot_fn + len(fn)
        if not gold:
            neg_total += 1
            neg_clean += 0 if fp else 1
        status = "ok " if not fp and not fn else "!! "
        print(f"{status}{case['id']:<18} tp={tp} fp={len(fp)} missed={len(fn)}")
        for p in fp:
            print(f"      extra : {p}")
        for g in fn:
            print(f"      missed: {g}")
        time.sleep(delay)

    precision = tot_tp / (tot_tp + tot_fp) if tot_tp + tot_fp else 0.0
    recall = tot_tp / (tot_tp + tot_fn) if tot_tp + tot_fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    print("\n==== RESULTS ====")
    print(f"cases: {len(CASES)} (errors: {errors})")
    print(f"precision: {precision:.2f}   recall: {recall:.2f}   F1: {f1:.2f}")
    if neg_total:
        print(f"negative cases handled correctly: {neg_clean}/{neg_total}")
    if errors:
        print("WARNING: some cases failed (rate limit?). Re-run to get complete numbers.")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 4.0)