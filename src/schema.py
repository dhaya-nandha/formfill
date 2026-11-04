import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.json"


def load_schema(path=SCHEMA_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SCHEMA = load_schema()

CLASS_NAMES = [c["name"] for c in SCHEMA["classes"]]
PROFILE_FIELDS = [c["name"] for c in SCHEMA["classes"] if c["kind"] == "profile"]
NON_FILL_CLASSES = [c["name"] for c in SCHEMA["classes"] if c["kind"] == "non_fill"]
CLASS2ID = {name: i for i, name in enumerate(CLASS_NAMES)}
ID2CLASS = {i: name for name, i in CLASS2ID.items()}

QUESTION_TYPES = SCHEMA["question_types"]
NER_TAGS = SCHEMA["ner_tags"]
NER_TAG2ID = {t: i for i, t in enumerate(NER_TAGS)}
NER_ID2TAG = {i: t for t, i in NER_TAG2ID.items()}
INDIAN_STATES = SCHEMA["indian_states"]
BRANCH_ALIASES = SCHEMA["branch_aliases"]
DEGREE_ALIASES = SCHEMA["degree_aliases"]


def validate():
    assert len(CLASS_NAMES) == 17, "need 17 classes"
    assert len(PROFILE_FIELDS) == 15, "need 15 profile fields"
    assert NON_FILL_CLASSES == ["open_text", "unsupported"]
    assert len(NER_TAGS) == 13, "need 13 NER tags"
    assert len(set(CLASS_NAMES)) == 17, "duplicate class names"
    ids = [c["id"] for c in SCHEMA["classes"]]
    assert ids == list(range(17)), "class ids must be 0..16 in order"
    return True


validate()

if __name__ == "__main__":
    print("classes:", len(CLASS_NAMES))
    print("profile fields:", len(PROFILE_FIELDS))
    print("ner tags:", len(NER_TAGS))
    print("states:", len(INDIAN_STATES))
    print("OK")