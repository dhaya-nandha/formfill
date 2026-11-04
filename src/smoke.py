import sys
import torch
import transformers
import sentence_transformers
import sklearn
import pymupdf
from transformers import AutoTokenizer, AutoModel

print("Python:", sys.version)
print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("sentence-transformers:", sentence_transformers.__version__)
print("scikit-learn:", sklearn.__version__)
print("pymupdf:", getattr(pymupdf, "VersionBind", "ok"))
print("CUDA available locally:", torch.cuda.is_available())

for name in ["sentence-transformers/all-MiniLM-L6-v2", "dslim/bert-base-NER"]:
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModel.from_pretrained(name)
    inputs = tok("Dhayanandha studies at VIT-AP", return_tensors="pt")
    out = model(**inputs)
    print(name, "-> output shape:", tuple(out.last_hidden_state.shape))

print("OK")