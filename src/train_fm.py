import json
import random
import time

import matplotlib
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import transformers
from sklearn.metrics import f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          get_linear_schedule_with_warmup)

from src.eval_fm import RES, ROOT, evaluate, load_split, print_summary, print_weak_classes
from src.schema import CLASS_NAMES, CLASS2ID, ID2CLASS

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_DIR = ROOT / "models" / "field_matcher"
LR, BATCH, MAX_EPOCHS, WD, WARMUP, MAXLEN, PATIENCE = 5e-5, 32, 8, 0.01, 0.10, 48, 3

print("torch", torch.__version__, "| transformers", transformers.__version__)
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
rng = random.Random(SEED)

train, val = load_split("train"), load_split("val")
tests = {"val": val, "test_a": load_split("test_a"), "test_b": load_split("test_b")}
tests = {k: v for k, v in tests.items() if v is not None}

tok = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=len(CLASS_NAMES), id2label=ID2CLASS, label2id=CLASS2ID)

counts = np.bincount(train["label_id"].values, minlength=len(CLASS_NAMES))
class_w = torch.tensor(counts.sum() / (len(CLASS_NAMES) * counts), dtype=torch.float)


def batches(texts, labels, bs, shuffle):
    idx = list(range(len(texts)))
    if shuffle:
        rng.shuffle(idx)
    for i in range(0, len(idx), bs):
        sel = idx[i:i + bs]
        enc = tok([texts[j] for j in sel], truncation=True, max_length=MAXLEN,
                  padding=True, return_tensors="pt")
        yield enc, torch.tensor([labels[j] for j in sel])


def predict(texts, labels):
    model.eval()
    all_logits = []
    with torch.no_grad():
        for enc, _ in batches(texts, labels, 128, False):
            all_logits.append(model(**enc).logits)
    return torch.cat(all_logits)


tr_x, tr_y = train["text"].tolist(), train["label_id"].tolist()
va_x, va_y = val["text"].tolist(), val["label_id"].tolist()

opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WD)
steps_per_epoch = (len(tr_x) + BATCH - 1) // BATCH
total = steps_per_epoch * MAX_EPOCHS
sched = get_linear_schedule_with_warmup(opt, int(WARMUP * total), total)

log, best_f1, best_epoch, bad = [], -1.0, 0, 0
for epoch in range(1, MAX_EPOCHS + 1):
    t0 = time.time()
    model.train()
    losses = []
    for enc, y in batches(tr_x, tr_y, BATCH, True):
        loss = F.cross_entropy(model(**enc).logits, y, weight=class_w)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        opt.zero_grad()
        losses.append(loss.item())
    logits = predict(va_x, va_y)
    val_loss = F.cross_entropy(logits, torch.tensor(va_y), weight=class_w).item()
    val_f1 = f1_score(va_y, logits.argmax(1).numpy(), average="macro", zero_division=0)
    row = {"epoch": epoch, "train_loss": float(np.mean(losses)), "val_loss": val_loss,
           "val_macro_f1": float(val_f1), "seconds": round(time.time() - t0, 1)}
    log.append(row)
    print(row)
    if val_f1 > best_f1:
        best_f1, best_epoch, bad = val_f1, epoch, 0
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(MODEL_DIR)
        tok.save_pretrained(MODEL_DIR)
    else:
        bad += 1
        if bad >= PATIENCE:
            print(f"early stop at epoch {epoch}")
            break

pd.DataFrame(log).to_csv(RES / "fm_training_log.csv", index=False)
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ep = [r["epoch"] for r in log]
ax[0].plot(ep, [r["train_loss"] for r in log], label="train loss")
ax[0].plot(ep, [r["val_loss"] for r in log], label="val loss")
ax[0].set_xlabel("epoch")
ax[0].legend()
ax[1].plot(ep, [r["val_macro_f1"] for r in log], color="green")
ax[1].set_xlabel("epoch")
ax[1].set_title("val macro-F1")
fig.tight_layout()
fig.savefig(RES / "fm_training_curves.png", dpi=130)

print(f"\nbest epoch = {best_epoch}, val macro-F1 = {best_f1:.3f}")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
out = {"variant": "C_finetuned", "best_epoch": best_epoch, "sets": {}}
for s, df in tests.items():
    logits = predict(df["text"].tolist(), df["label_id"].tolist())
    out["sets"][s] = evaluate(df["label_id"].values, logits.argmax(1).numpy(), tag=f"C_finetuned_{s}")
print_summary("C_finetuned", out["sets"])
if "test_a" in out["sets"]:
    print_weak_classes(out["sets"]["test_a"])
with open(RES / "fm_metrics_C_finetuned.json", "w") as f:
    json.dump(out, f, indent=1)
print("\nSaved model to models/field_matcher and metrics to results/")