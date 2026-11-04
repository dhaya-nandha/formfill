import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from src.eval_fm import RES, evaluate, load_split, print_summary, print_weak_classes

SEED = 42
C_GRID = [1, 3, 10, 30, 100]

train, val = load_split("train"), load_split("val")
tests = {"val": val, "test_a": load_split("test_a"), "test_b": load_split("test_b")}
tests = {k: v for k, v in tests.items() if v is not None}
y_train, y_val = train["label_id"].values, val["label_id"].values


def fit_best(Xtr, Xval, name):
    best = None
    for C in C_GRID:
        clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced")
        clf.fit(Xtr, y_train)
        f1 = f1_score(y_val, clf.predict(Xval), average="macro", zero_division=0)
        print(f"  {name}: C={C:<4} val macro-F1 = {f1:.3f}")
        if best is None or f1 > best[0]:
            best = (f1, C, clf)
    print(f"  {name}: chosen C = {best[1]} (picked on val only)")
    return best[1], best[2]


def run(name, featurize):
    Xtr = featurize(train["text"].tolist())
    Xval = featurize(val["text"].tolist())
    C, clf = fit_best(Xtr, Xval, name)
    out = {"variant": name, "C": C, "sets": {}}
    for s, df in tests.items():
        X = Xval if s == "val" else featurize(df["text"].tolist())
        pred = clf.predict(X)
        out["sets"][s] = evaluate(df["label_id"].values, pred, tag=f"{name}_{s}")
    print_summary(name, out["sets"])
    if "test_a" in out["sets"]:
        print_weak_classes(out["sets"]["test_a"])
    with open(RES / f"fm_metrics_{name}.json", "w") as f:
        json.dump(out, f, indent=1)


np.random.seed(SEED)

# Variant A: TF-IDF char n-grams + Logistic Regression
tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=True, sublinear_tf=True)
tfidf.fit(train["text"].tolist())
run("A_tfidf", lambda texts: tfidf.transform(texts))

# Variant B: frozen MiniLM embeddings + Logistic Regression
from sentence_transformers import SentenceTransformer

st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
run("B_frozen", lambda texts: st.encode(texts, batch_size=64, show_progress_bar=False,
                                        normalize_embeddings=True))
print("\nDone. Metrics in results/fm_metrics_A_tfidf.json and fm_metrics_B_frozen.json")