import json

import matplotlib
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.eval_fm import RES, ROOT, load_split
from src.schema import CLASS_NAMES, CLASS2ID, PROFILE_FIELDS

matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODEL_DIR = ROOT / "models" / "field_matcher"
TARGET_PRECISION = 0.98
PROFILE_IDS = {CLASS2ID[c] for c in PROFILE_FIELDS}
MAXLEN = 48

tok = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()


def probs_for(texts):
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 128):
            enc = tok(texts[i:i + 128], truncation=True, max_length=MAXLEN,
                      padding=True, return_tensors="pt")
            out.append(torch.softmax(model(**enc).logits, dim=1).numpy())
    return np.concatenate(out)


def stats(conf, pred, true, tau):
    """Auto-fill decision for each row, then precision and coverage."""
    is_profile = np.isin(pred, list(PROFILE_IDS))
    auto = is_profile & (conf >= tau)
    n_auto = int(auto.sum())
    if n_auto == 0:
        return {"tau": float(tau), "coverage": 0.0, "precision": None, "auto": 0}
    correct = (pred[auto] == true[auto]).sum()
    return {"tau": float(tau), "coverage": float(n_auto / len(true)),
            "precision": float(correct / n_auto), "auto": n_auto}


def sweep(conf, pred, true):
    taus = np.round(np.arange(0.30, 1.0001, 0.01), 2)
    return [stats(conf, pred, true, t) for t in taus]


def choose_tau(curve):
    """Smallest tau whose precision is at least the target, using val only."""
    ok = [c for c in curve if c["precision"] is not None and c["precision"] >= TARGET_PRECISION]
    return min(ok, key=lambda c: c["tau"]) if ok else None


def main():
    val = load_split("val")
    test_a = load_split("test_a")

    pv = probs_for(val["text"].tolist())
    yv = val["label_id"].values
    conf_v, pred_v = pv.max(1), pv.argmax(1)

    curve_val = sweep(conf_v, pred_v, yv)
    chosen = choose_tau(curve_val)
    if chosen is None:
        print("No threshold reaches the target precision on val. Report this honestly.")
        return
    tau = chosen["tau"]

    report = {"target_precision": TARGET_PRECISION, "tau_fm": tau,
              "chosen_on": "val only", "val_at_tau": stats(conf_v, pred_v, yv, tau),
              "curve_val": curve_val}

    if test_a is not None:
        pt = probs_for(test_a["text"].tolist())
        yt = test_a["label_id"].values
        report["test_a_at_tau"] = stats(pt.max(1), pt.argmax(1), yt, tau)
        report["curve_test_a"] = sweep(pt.max(1), pt.argmax(1), yt)

    with open(RES / "fm_threshold.json", "w") as f:
        json.dump(report, f, indent=1)
    with open(MODEL_DIR / "fm_config.json", "w") as f:
        json.dump({"tau_fm": tau, "target_precision": TARGET_PRECISION,
                   "chosen_on": "val only"}, f, indent=1)

    print(f"tau_fm = {tau:.2f} (smallest threshold with val precision >= {TARGET_PRECISION})")
    print(f"  val    : precision {report['val_at_tau']['precision']:.3f}, "
          f"coverage {report['val_at_tau']['coverage']:.3f}, auto {report['val_at_tau']['auto']}")
    if "test_a_at_tau" in report:
        t = report["test_a_at_tau"]
        prec = "n/a" if t["precision"] is None else f"{t['precision']:.3f}"
        print(f"  test_a : precision {prec}, coverage {t['coverage']:.3f}, auto {t['auto']}")

    taus = [c["tau"] for c in curve_val]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(taus, [c["precision"] or np.nan for c in curve_val], label="val precision", color="C0")
    ax.plot(taus, [c["coverage"] for c in curve_val], label="val coverage", color="C1")
    if "curve_test_a" in report:
        ax.plot(taus, [c["precision"] or np.nan for c in report["curve_test_a"]],
                "--", label="test_a precision", color="C0", alpha=0.6)
        ax.plot(taus, [c["coverage"] for c in report["curve_test_a"]],
                "--", label="test_a coverage", color="C1", alpha=0.6)
    ax.axhline(TARGET_PRECISION, color="gray", linestyle=":", label="target precision 0.98")
    ax.axvline(tau, color="red", linestyle=":", label=f"tau_fm = {tau:.2f}")
    ax.set_xlabel("confidence threshold tau")
    ax.set_ylabel("value")
    ax.set_title("Precision vs coverage for auto-fill")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RES / "fm_coverage_curve.png", dpi=130)
    print("Saved results/fm_threshold.json, results/fm_coverage_curve.png and models/field_matcher/fm_config.json")


if __name__ == "__main__":
    main()