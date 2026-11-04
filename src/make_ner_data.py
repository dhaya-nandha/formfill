import json
from collections import Counter
from pathlib import Path

from src.chunking import NL, make_windows, text_to_words

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "resumes_synth"
OUT = ROOT / "data" / "ner"
OUT.mkdir(parents=True, exist_ok=True)


def with_newlines(rec):
    starts = set(rec["line_starts"])
    words, labels = [], []
    for i, (t, l) in enumerate(zip(rec["tokens"], rec["labels"])):
        if i in starts and i > 0:
            words.append(NL)
            labels.append("O")
        words.append(t)
        labels.append(l)
    return words, labels


def main():
    for split in ["train", "dev", "test"]:
        examples, mismatches, ent = [], 0, Counter()
        for line in open(SRC / f"{split}.jsonl", encoding="utf-8"):
            rec = json.loads(line)
            words, labels = with_newlines(rec)
            if text_to_words(rec["text"]) != words:
                mismatches += 1
            for k, (a, b) in enumerate(make_windows(words)):
                w, l = words[a:b], labels[a:b]
                examples.append({"id": f"{rec['id']}_w{k}", "words": w, "labels": l})
                ent.update(x[2:] for x in l if x.startswith("B-"))
        with open(OUT / f"{split}.json", "w", encoding="utf-8") as f:
            json.dump(examples, f, ensure_ascii=False)
        lens = [len(e["words"]) for e in examples]
        print(f"{split:6} windows: {len(examples):5} | words per window: avg {sum(lens) / len(lens):.0f}, "
              f"max {max(lens)} | tokenization mismatches vs text: {mismatches}")
        print(f"       entities: {dict(ent)}")


if __name__ == "__main__":
    main()