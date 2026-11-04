from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support)

from src.schema import CLASS_NAMES

ROOT = Path(__file__).resolve().parent.parent
FM = ROOT / "data" / "fm"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)
N = len(CLASS_NAMES)


def load_split(name):
    p = FM / f"{name}.csv"
    return pd.read_csv(p, encoding="utf-8") if p.exists() else None


def evaluate(y_true, y_pred, tag=None):
    """Macro-F1 is averaged only over classes that appear in y_true."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    present = sorted(set(y_true.tolist()))
    p, r, f, s = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(N)), zero_division=0)
    result = {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=present,
                                   average="macro", zero_division=0)),
        "classes_in_set": len(present),
        "per_class": {CLASS_NAMES[i]: {"precision": float(p[i]), "recall": float(r[i]),
                                       "f1": float(f[i]), "support": int(s[i])}
                      for i in range(N)},
    }
    if tag:
        plot_confusion(y_true, y_pred, tag)
    return result


def plot_confusion(y_true, y_pred, tag):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(N)))
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(N))
    ax.set_yticks(range(N))
    ax.set_xticklabels(CLASS_NAMES, rotation=90, fontsize=8)
    ax.set_yticklabels(CLASS_NAMES, fontsize=8)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(tag)
    for i in range(N):
        for j in range(N):
            if cm[i, j]:
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=6,
                        color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(RES / f"cm_{tag}.png", dpi=130)
    plt.close(fig)


def print_summary(name, metrics_by_set):
    print(f"\n=== {name} ===")
    print(f"{'set':8}{'rows':>6}{'accuracy':>10}{'macro_F1':>10}")
    for s, m in metrics_by_set.items():
        print(f"{s:8}{m['n']:6}{m['accuracy']:10.3f}{m['macro_f1']:10.3f}")


def print_weak_classes(metrics, top=5):
    items = [(c, v["f1"], v["support"]) for c, v in metrics["per_class"].items()
             if v["support"] > 0]
    items.sort(key=lambda x: x[1])
    print("  weakest classes:", ", ".join(f"{c} (F1 {f:.2f}, n={s})" for c, f, s in items[:top]))