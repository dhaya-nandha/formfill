NL = "¶"  # marks a line break between words


def text_to_words(text):
    """Resume text -> list of words, with NL between non-empty lines."""
    words = []
    for line in [l for l in text.splitlines() if l.strip()]:
        if words:
            words.append(NL)
        words.extend(line.split())
    return words


def make_windows(words, maxw=100):
    """Cut words into (start, end) windows of at most maxw words, only at line breaks
    (a single line longer than maxw is cut hard)."""
    lines, s = [], 0
    for i, w in enumerate(words + [NL]):
        if w == NL:
            lines.append((s, i))
            s = i + 1
    wins, cur_s, cur_e = [], None, None
    for s, e in lines:
        pieces = [(a, min(a + maxw, e)) for a in range(s, e, maxw)]
        for a, b in pieces:
            if cur_s is None:
                cur_s, cur_e = a, b
            elif b - cur_s <= maxw:
                cur_e = b
            else:
                wins.append((cur_s, cur_e))
                cur_s, cur_e = a, b
    if cur_s is not None:
        wins.append((cur_s, cur_e))
    return [(a, b) for a, b in wins if b > a]