import json
import os
import re

CWD = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(
    CWD, "..", "..", "better-politics-mod", "common", "scripted_effects",
    "bpm_aa_interest_group_traits.txt",
)
TEMPLATE_PATH = os.path.join(CWD, "viewer_template.html")
OUTPUT_PATH = os.path.join(CWD, "traits_viewer.html")

CATEGORY_ORDER = [
    "gov", "exe", "dop", "sta", "eco", "wel", "cit", "rel", "mil", "fem", "ban", "vanilla", # should prolly get this from the code itself
]
CATEGORY_RE = re.compile(r"^bpm_trait_(" + "|".join(CATEGORY_ORDER) + r")_(.+)$")
TRAITREF_RE = CATEGORY_RE
IDEOLOGY_KEY = "bpm_ig_set_ideology"



def tokenize(text):
    tokens = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "{":
            tokens.append(("LBRACE", "{"))
            i += 1
            continue
        if c == "}":
            tokens.append(("RBRACE", "}"))
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 1
            tokens.append(("WORD", text[i:j + 1]))
            i = j + 1
            continue
        j = i
        while j < n and text[j] not in " \t\r\n{}#":
            j += 1
        tok = text[i:j]
        if tok in ("=", "?="):
            tokens.append(("OP", tok))
        else:
            tokens.append(("WORD", tok))
        i = j
    return tokens


def parse_block(tokens, pos, stop_at_rbrace):
    """Returns (entries, pos). entries is a list of {'k','op','v'} dicts,
    where 'v' is either a string (scalar) or another entries list (nested block)."""
    entries = []
    n = len(tokens)
    while pos < n:
        ttype, tval = tokens[pos]
        if stop_at_rbrace and ttype == "RBRACE":
            return entries, pos
        if ttype != "WORD":
            pos += 1
            continue
        key = tval
        pos += 1
        if pos >= n:
            break
        op = "="
        if tokens[pos][0] == "OP":
            op = tokens[pos][1]
            pos += 1
        if pos >= n:
            break
        if tokens[pos][0] == "LBRACE":
            pos += 1
            value, pos = parse_block(tokens, pos, stop_at_rbrace=True)
            if pos < n and tokens[pos][0] == "RBRACE":
                pos += 1
        else:
            value = tokens[pos][1]
            pos += 1
        entries.append({"k": key, "op": op, "v": value})
    return entries, pos


def parse_document(text):
    tokens = tokenize(text)
    entries, _ = parse_block(tokens, 0, stop_at_rbrace=False)
    return entries



def find_entry(entries, key):
    for e in entries:
        if e["k"] == key:
            return e
    return None


def without_key(entries, key):
    return [e for e in entries if e["k"] != key]


def classify_outcome(entry):
    k, op, v = entry["k"], entry["op"], entry["v"]

    if k == IDEOLOGY_KEY and isinstance(v, list):
        fields = {sub["k"]: sub["v"] for sub in v if isinstance(sub["v"], str)}
        return {
            "kind": "ideology",
            "ideologyType": fields.get("type", "?"),
            "ideologyName": fields.get("name", "?"),
        }

    m = TRAITREF_RE.match(k)
    if m:
        return {
            "kind": "traitref",
            "trait": k,
            "category": m.group(1),
            "params": v if isinstance(v, list) else None,
            "scalarValue": v if isinstance(v, str) else None,
        }

    return {"kind": "raw", "key": k, "op": op, "value": v}


def branch_from_if_like(entry, branch_type):
    body = entry["v"] if isinstance(entry["v"], list) else []
    limit_entry = find_entry(body, "limit")
    condition = limit_entry["v"] if (limit_entry and isinstance(limit_entry["v"], list)) else None
    rest = without_key(body, "limit")
    return {
        "kind": "branch",
        "branchType": branch_type,
        "condition": condition,
        "items": parse_body(rest),
    }


def parse_body(entries):
    items = []
    i, n = 0, len(entries)
    pending_guard = None

    while i < n:
        e = entries[i]
        k = e["k"]

        if k == "if":
            branch = branch_from_if_like(e, "if")
            items.append(branch)
            i += 1
            while i < n and entries[i]["k"] in ("else_if", "else"):
                e2 = entries[i]
                bt = "else_if" if e2["k"] == "else_if" else "else"
                items.append(branch_from_if_like(e2, bt))
                i += 1
            pending_guard = None

        elif k == "limit":
            condition = e["v"] if isinstance(e["v"], list) else None
            branch = {"kind": "branch", "branchType": "if", "condition": condition, "items": []}
            items.append(branch)
            pending_guard = branch
            i += 1

        elif k in ("else_if", "else"):
            bt = "else_if" if k == "else_if" else "else"
            items.append(branch_from_if_like(e, bt))
            i += 1
            pending_guard = None

        else:
            outcome = classify_outcome(e)
            if pending_guard is not None:
                pending_guard["items"].append(outcome)
            else:
                items.append(outcome)
            i += 1

    return items



def build_traits(root_entries):
    traits = {}
    order = []
    duplicates = []
    for e in root_entries:
        m = CATEGORY_RE.match(e["k"])
        if not m or not isinstance(e["v"], list):
            continue
        category, short_name = m.group(1), m.group(2)
        if e["k"] in traits:
            duplicates.append(e["k"])
        else:
            order.append(e["k"])
        traits[e["k"]] = {
            "name": e["k"],
            "category": category,
            "shortName": short_name,
            "items": parse_body(e["v"]),
        }

    for dup in duplicates:
        print(f"  WARNING: '{dup}' is defined more than once in the source file; "
              f"showing the last definition (category={traits[dup]['category']}).")

    categories = {}
    for c in CATEGORY_ORDER:
        categories[c] = [t for t in order if traits[t]["category"] == c]

    return {"traits": traits, "categoryOrder": CATEGORY_ORDER, "categories": categories}


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    root_entries = parse_document(text)
    data = build_traits(root_entries)

    n_traits = len(data["traits"])
    print(f"Parsed {n_traits} well-formed traits.")
    for c in CATEGORY_ORDER:
        print(f"  {c:8s} {len(data['categories'][c])}")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    payload = json.dumps(data, ensure_ascii=False)
    out = template.replace("__TRAITS_DATA__", payload)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
