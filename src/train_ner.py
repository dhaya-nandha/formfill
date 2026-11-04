import csv
import json
import random
import time

import matplotlib
import numpy as np
import torch
import transformers
from seqeval.metrics import classification_report, f1_score
from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                          get_linear_schedule_with_warmup)

from src.schema import NER_ID2TAG, NER_TAG2ID, NER_TAGS

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, RES = ROOT / "data" / "ner", ROOT / "results"
MODEL_DIR = ROOT / "models" / "ner"
RES.mkdir(exist_ok=True)

BASE = "dslim/bert-base-NER"
SEED, LR, BATCH, EPOCHS, MAXLEN, WARMUP, WD = 42, 3e-5, 16, 4, 320, 0.10, 0.01

print("torch", torch.__version__, "| transformers", transformers.__version__)
assert torch.cuda.is_available(), "CUDA GPU not found"
dev_gpu = torch.device("cuda")
print("GPU:", torch.cuda.get_device_name(0))
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
rng = random.Random(SEED)

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForTokenClassification.from_pretrained(
    BASE, num_labels=len(NER_TAGS), id2label=NER_ID2TAG, label2id=NER_TAG2ID,
    ignore_mismatched_sizes=True).to(dev_gpu)


def load(split):
    return json.load(open(DATA / f"{split}.json", encoding="utf-8"))


def encode(examples):
    enc = tok([e["words"] for e in examples], is_split_into_words=True,
              truncation=True, max_length=MAXLEN)
    feats, trunc = [], 0
    for i, e in enumerate(examples):
        wids, prev, lab = enc.word_ids(i), None, []
        for w in wids:
            lab.append(-100 if (w is None or w == prev) else NER_TAG2ID[e["labels"][w]])
            prev = w
        seen = max((w for w in wids if w is not None), default=-1) + 1
        trunc += seen < len(e["words"])
        feats.append({"input_ids": enc["input_ids"][i], "labels": lab, "word_ids": wids})
    return feats, trunc


def collate(batch):
    m = max(len(b["input_ids"]) for b in batch)
    ids = torch.full((len(batch), m), tok.pad_token_id, dtype=torch.long)
    att = torch.zeros((len(batch), m), dtype=torch.long)
    lab = torch.full((len(batch), m), -100, dtype=torch.long)
    for i, b in enumerate(batch):
        n = len(b["input_ids"])
        ids[i, :n] = torch.tensor(b["input_ids"])
        att[i, :n] = 1
        lab[i, :n] = torch.tensor(b["labels"])
    return ids.to(dev_gpu), att.to(dev_gpu), lab.to(dev_gpu)


def evaluate(feats, examples):
    model.eval()
    y_true, y_pred, losses = [], [], []
    with torch.no_grad():
        for i in range(0, len(feats), 64):
            batch = feats[i:i + 64]
            ids, att, lab = collate(batch)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                out = model(input_ids=ids, attention_mask=att, labels=lab)
            losses.append(out.loss.item())
            pred = out.logits.float().argmax(-1).cpu().numpy()
            for j, f in enumerate(batch):
                ex = examples[i + j]
                pw = ["O"] * len(ex["words"])
                for k, w in enumerate(f["word_ids"]):
                    if w is not None and f["labels"][k] != -100:
                        pw[w] = NER_ID2TAG[int(pred[j, k])]
                y_pred.append(pw)
                y_true.append(ex["labels"])
    return float(np.mean(losses)), float(f1_score(y_true, y_pred)), y_true, y_pred


train_ex, dev_ex, test_ex = load("train"), load("dev"), load("test")
tr_f, tr_trunc = encode(train_ex)
dv_f, dv_trunc = encode(dev_ex)
te_f, te_trunc = encode(test_ex)
print(f"windows: train {len(tr_f)}, dev {len(dv_f)}, test {len(te_f)}")
print(f"truncated windows at max_length {MAXLEN}: train {tr_trunc}, dev {dv_trunc}, test {te_trunc}")

opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WD)
steps = ((len(tr_f) + BATCH - 1) // BATCH) * EPOCHS
sched = get_linear_schedule_with_warmup(opt, int(WARMUP * steps), steps)

log, best = [], -1.0
for epoch in range(1, EPOCHS + 1):
    t0 = time.time()
    model.train()
    order = list(range(len(tr_f)))
    rng.shuffle(order)
    losses = []
    for i in range(0, len(order), BATCH):
        ids, att, lab = collate([tr_f[k] for k in order[i:i + BATCH]])
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        opt.zero_grad()
        losses.append(loss.item())
    dev_loss, dev_f1, _, _ = evaluate(dv_f, dev_ex)
    row = {"epoch": epoch, "train_loss": float(np.mean(losses)), "dev_loss": dev_loss,
           "dev_entity_f1": dev_f1, "seconds": round(time.time() - t0, 1)}
    log.append(row)
    print(row)
    if dev_f1 > best:
        best = dev_f1
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(MODEL_DIR)
        tok.save_pretrained(MODEL_DIR)

with open(RES / "ner_training_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(log[0]))
    w.writeheader()
    w.writerows(log)
ep = [r["epoch"] for r in log]
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(ep, [r["train_loss"] for r in log], label="train loss")
ax[0].plot(ep, [r["dev_loss"] for r in log], label="dev loss")
ax[0].set_xlabel("epoch")
ax[0].legend()
ax[1].plot(ep, [r["dev_entity_f1"] for r in log], color="green")
ax[1].set_xlabel("epoch")
ax[1].set_title("dev entity F1 (synthetic)")
fig.tight_layout()
fig.savefig(RES / "ner_training_curves.png", dpi=130)

model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR).to(dev_gpu)
metrics = {"note": "SYNTHETIC data only", "best_dev_entity_f1": best}
for name, feats, ex in [("dev", dv_f, dev_ex), ("test", te_f, test_ex)]:
    _, f1, yt, yp = evaluate(feats, ex)
    rep = classification_report(yt, yp, output_dict=True, zero_division=0)
    metrics[name] = {"entity_f1": f1, "per_type": {
        k: {m: float(v[m]) for m in ("precision", "recall", "f1-score")} | {"support": int(v["support"])}
        for k, v in rep.items() if k in ("NAME", "COLLEGE", "DEGREE", "BRANCH", "LOCATION", "SKILL")}}
    print(f"\n=== {name} (SYNTHETIC) overall entity F1 = {f1:.3f} ===")
    for k, v in metrics[name]["per_type"].items():
        print(f"  {k:9} P {v['precision']:.3f}  R {v['recall']:.3f}  F1 {v['f1-score']:.3f}  n={v['support']}")
with open(RES / "ner_metrics.json", "w") as f:
    json.dump(metrics, f, indent=1)
print("\nSaved model to models/ner and metrics to results/ner_metrics.json")