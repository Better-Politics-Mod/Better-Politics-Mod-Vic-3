"""
Parses the pop_weight block of every interest group and renders it as a flowchart
annotated with the range of values the weight can take at each step.

The weight is evaluated with interval arithmetic:
  * Numbers are exact.
  * `modifier:` references are bounded by summing every place the modifier is granted
    (laws, amendments, static modifiers, character traits, ...). Laws in the same law
    group are mutually exclusive, so each law group contributes at most one law's value.
    Static modifiers can be grouped into mutually exclusive sets in STATIC_MODIFIER_EXCLUSIVE_GROUPS.
  * Script values (common/script_values) are evaluated recursively.
  * Everything else (pop/country variables, game values like literacy_rate) must be given a
    range in MANUAL_RANGES below. Anything not listed is treated as unbounded and reported.

The pop_weight is evaluated once per pop type allowed by pop_potential and per combination of
CONTEXT_FLAGS, so conditions such as `is_pop_type` and `is_in_government` are resolved exactly
instead of widening the range.

Usage:
    python3 pop_weight_flowchart.py                 # all IGs
    python3 pop_weight_flowchart.py ig_armed_forces # selected IGs
    python3 pop_weight_flowchart.py --vanilla "/path/to/Victoria 3/game"

Writes output/pop_weight_flowchart.html and one Mermaid file per IG to output/mmd/.
"""

import argparse
import glob
import html
import itertools
import json
import math
import os
import re
import sys
from collections import defaultdict

CWD = os.path.dirname(os.path.abspath(__file__))
MOD_PATH = os.path.join(CWD, "..", "..", "better-politics-mod")
DEFAULT_VANILLA_PATH = os.path.expanduser("~/.steam/steam/steamapps/common/Victoria 3/game")
OUTPUT_DIR = os.path.join(CWD, "output")

INF = math.inf

# --------------------------------------------------------------------------------------------
# Manual configuration
# --------------------------------------------------------------------------------------------

# Ranges for values that can't be derived from the script. Keys are the last segment of the
# reference (`owner.var:bpm_political_stability` -> `var:bpm_political_stability`).
# None means "not decided yet": the value is treated as unbounded and reported at the end.
MANUAL_RANGES = {
    # Pop values
    "literacy_rate": (0.0, 1.0),
    "wealth": (1, 99),
    "standard_of_living": (1, 99),
    "pop_radical_fraction": (0.0, 1.0),
    "pop_loyalist_fraction": (0.0, 1.0),
    "self_ownership_fraction": (0.0, 1.0),
    # Character values
    "popularity": (-100, 100),
    # Country variables
    "var:bpm_political_stability": (0, 100),
    "var:bpm_consciousness_labor": (0, 100),
    "var:bpm_consciousness_liberal": (0, 100),
    "var:bpm_agrarian_socialism_power": (0, 100),
    "var:bpm_je_syndicalism": (0, 100),
    "var:independence_from_church_variable": (0, 200),
    "var:bpm_ig_agitator_popularity_var": (1.0, 2.0),
    # Global variables
    "global_var:bpm_je_march_to_radicalism_progress": (0, 120),
    "global_var:bpm_agrarian_socialism_power_global": (0, 100),
}

# Conditions that are enumerated rather than left ambiguous. Every combination is evaluated
# separately so their effects stay correlated across the whole pop_weight.
CONTEXT_FLAGS = {
    "is_in_government": [True, False],
    "is_at_war": [True, False],
}

# Static modifiers of which at most one can be active at once.
STATIC_MODIFIER_EXCLUSIVE_GROUPS = [
    ["military_wages_very_low", "military_wages_low", "military_wages_medium",
     "military_wages_high", "military_wages_very_high"],
]

# Static modifiers that are always applied (contribute their exact value, never 0).
STATIC_MODIFIER_ALWAYS_ON = {"base_values"}

# (min, max) multiplier for static modifiers applied through `add_modifier = { multiplier = ... }`.
# Static modifiers found being applied with a multiplier but not listed here are reported, and
# counted at their unscaled value.
STATIC_MODIFIER_MULTIPLIERS = {
    # "bpm_springtime_modifier_name": (0, 100),
}

# Direct override of a modifier's total range, bypassing source analysis.
MODIFIER_OVERRIDES = {
    # "interest_group_in_government_attraction_mult": (-0.5, 0.5),
}

# Modifiers the game itself multiplies the pop_weight by. A `divide = { ... }` reading only these
# undoes that multiplication in the script; it is skipped, so the range shown is the weight the game
# ends up using.
ENGINE_APPLIED_MODIFIER_RE = re.compile(r"^interest_group_(ig_\w+_)?pop_attraction_mult$")

# A modifier read more than once by a pop_weight (e.g. divided out of the final value and added to
# a multiplier) must take the same value everywhere. Such modifiers are pinned: the pop_weight is
# evaluated once per piece of their range, so every read sees the same piece. Ranges with at most
# CORRELATION_SPLITS achievable values are enumerated exactly, others are cut into that many pieces
# (`*_mult` modifiers geometrically in 1 + x, finer close to -100%). The number of pieces shrinks
# until the combinations of all pinned modifiers of a pop_weight fit CORRELATION_MAX_COMBINATIONS.
CORRELATION_SPLITS = 24
CORRELATION_MAX_COMBINATIONS = 600

# Directories under common/ scanned for modifier sources, and how sources in them combine.
#   "law_group": exclusive within a law group
#   "static":    see STATIC_MODIFIER_* settings
#   "independent": every object may be active at the same time
SOURCE_DIRS = {
    "laws": "law_group",
    "static_modifiers": "static",
}
# Every other directory under common/ is scanned too and treated as "independent".

STRATA_ORDER = {"lower": 0, "middle": 1, "upper": 2}

# --------------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------------

OPERATORS = ("?=", "<=", ">=", "!=", "==", "=", "<", ">")
TOKEN_RE = re.compile(r'\s+|#[^\n]*|"[^"]*"|\?=|<=|>=|!=|==|[={}<>]|[^\s={}<>#"]+')


def tokenize(text):
    tokens = []
    for m in TOKEN_RE.finditer(text):
        t = m.group(0)
        if t[0].isspace() or t[0] == "#":
            continue
        tokens.append(t)
    return tokens


def parse_block(tokens, pos):
    entries = []
    n = len(tokens)
    while pos < n:
        t = tokens[pos]
        if t == "}":
            return entries, pos + 1
        if t in OPERATORS or t == "{":
            pos += 1
            continue
        key = t
        pos += 1
        op = None
        if pos < n and tokens[pos] in OPERATORS:
            op = tokens[pos]
            pos += 1
        if op is None:
            # Bare word inside a list block (e.g. `ideologies = { a b c }`)
            entries.append(Entry(key, None, None))
            continue
        if pos < n and tokens[pos] == "{":
            value, pos = parse_block(tokens, pos + 1)
        elif pos < n:
            value = tokens[pos]
            pos += 1
            # Typed values such as hsv{ ... } or rgb{ ... }
            if pos < n and tokens[pos] == "{" and value.isalpha():
                _, pos = parse_block(tokens, pos + 1)
        else:
            value = None
        entries.append(Entry(key, op, value))
    return entries, pos


class Entry:
    __slots__ = ("k", "op", "v")

    def __init__(self, k, op, v):
        self.k, self.op, self.v = k, op, v

    def __repr__(self):
        return f"Entry({self.k!r}, {self.op!r}, {self.v!r})"


def parse_file(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return parse_block(tokenize(f.read()), 0)[0]


def find(entries, key):
    for e in entries:
        if e.k == key:
            return e
    return None


def merged_files(rel_dir, vanilla_path, contains=None):
    """Files of a common/ directory in load order. Mod files replace vanilla files of the same name."""
    files = {}
    for base in ([vanilla_path] if vanilla_path else []) + [MOD_PATH]:
        for path in glob.glob(os.path.join(base, "common", rel_dir, "**", "*.txt"), recursive=True):
            files[os.path.relpath(path, os.path.join(base, "common", rel_dir))] = path
    result = []
    for name in sorted(files):
        path = files[name]
        if contains is not None:
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
            if not any(c in text for c in contains):
                continue
        result.append(path)
    return result


DB_PREFIXES = ("INJECT_OR_CREATE:", "REPLACE_OR_CREATE:", "TRY_INJECT:", "TRY_REPLACE:", "INJECT:", "REPLACE:")


def load_database(rel_dir, vanilla_path, contains=None):
    """Loads top-level objects of a directory, applying INJECT:/REPLACE: semantics."""
    db = {}
    for path in merged_files(rel_dir, vanilla_path, contains):
        for e in parse_file(path):
            if not isinstance(e.v, list):
                continue
            name, mode = e.k, "define"
            for p in DB_PREFIXES:
                if name.startswith(p):
                    name, mode = name[len(p):], p.rstrip(":").split("_")[-1].lower()
                    break
            if mode in ("inject", "create") and name in db:
                db[name] = db[name] + e.v
            else:
                db[name] = list(e.v)
    return db


# --------------------------------------------------------------------------------------------
# Intervals
# --------------------------------------------------------------------------------------------

class Interval:
    __slots__ = ("lo", "hi")

    def __init__(self, lo, hi=None):
        self.lo = lo
        self.hi = lo if hi is None else hi

    @staticmethod
    def unbounded():
        return Interval(-INF, INF)

    def __add__(self, o):
        return Interval(self.lo + o.lo, self.hi + o.hi)

    def __sub__(self, o):
        return Interval(self.lo - o.hi, self.hi - o.lo)

    def __mul__(self, o):
        def m(a, b):
            return 0.0 if a == 0 or b == 0 else a * b
        p = [m(self.lo, o.lo), m(self.lo, o.hi), m(self.hi, o.lo), m(self.hi, o.hi)]
        return Interval(min(p), max(p))

    def __truediv__(self, o):
        if o.lo <= 0 <= o.hi:
            # Paradox script returns the dividend for a division by zero; anything near zero blows up.
            return Interval.unbounded() if (o.lo, o.hi) != (0, 0) else Interval(self.lo, self.hi)
        return self * Interval(1 / o.hi, 1 / o.lo)

    def clamp_min(self, o):  # `min = x`: the result is at least x
        return Interval(max(self.lo, o.lo), max(self.hi, o.lo))

    def clamp_max(self, o):  # `max = x`: the result is at most x
        return Interval(min(self.lo, o.hi), min(self.hi, o.hi))

    def hull(self, o):
        if o is None:
            return self
        return Interval(min(self.lo, o.lo), max(self.hi, o.hi))

    def is_exact(self):
        return self.lo == self.hi

    def __str__(self):
        if self.is_exact():
            return fmt(self.lo)
        return f"[{fmt(self.lo)}, {fmt(self.hi)}]"


def fmt(x):
    if x == INF:
        return "∞"
    if x == -INF:
        return "-∞"
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.4g}"


def hull_all(intervals):
    result = None
    for i in intervals:
        result = i if result is None else result.hull(i)
    return result


# --------------------------------------------------------------------------------------------
# Modifier sources
# --------------------------------------------------------------------------------------------

NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")


def collect_occurrences(entries, names, out):
    for e in entries:
        if isinstance(e.v, list):
            collect_occurrences(e.v, names, out)
        elif e.k in names and isinstance(e.v, str) and NUMBER_RE.match(e.v):
            out.append((e.k, float(e.v)))


class ModifierSources:
    def __init__(self, names, vanilla_path):
        self.names = set(names)
        self.vanilla_path = vanilla_path
        # modifier -> list of {"name", "kind", "group", "options": [Interval], "note"}
        self.groups = {}
        self.warnings = []
        self._scan()

    def _scan(self):
        found = defaultdict(list)  # modifier -> [(category, kind, object, value)]
        common_dirs = set()
        for base in ([self.vanilla_path] if self.vanilla_path else []) + [MOD_PATH]:
            for d in glob.glob(os.path.join(base, "common", "*")):
                if os.path.isdir(d):
                    common_dirs.add(os.path.basename(d))

        law_db = load_database("laws", self.vanilla_path)
        laws_by_group = defaultdict(list)
        for law, body in law_db.items():
            g = find(body, "group")
            laws_by_group[g.v if g else f"<unknown group of {law}>"].append(law)

        for d in sorted(common_dirs):
            kind = SOURCE_DIRS.get(d, "independent")
            db = law_db if d == "laws" else load_database(d, self.vanilla_path, contains=self.names)
            for obj, body in db.items():
                occ = []
                collect_occurrences(body, self.names, occ)
                for mod, value in occ:
                    found[mod].append((d, kind, obj, value))

        multiplied = self._find_multiplied_static_modifiers()

        for mod in self.names:
            groups = []
            law_values = defaultdict(dict)
            static_values = {}
            for d, kind, obj, value in found[mod]:
                if kind == "law_group":
                    law_values[d][obj] = value
                elif kind == "static":
                    static_values[obj] = value
                else:
                    groups.append({"name": f"{d}/{obj}", "kind": d,
                                   "options": [Interval(0), Interval(value)], "laws": None})

            for d, values in law_values.items():
                by_group = defaultdict(dict)
                for law, value in values.items():
                    g = find(law_db[law], "group")
                    by_group[g.v if g else f"<unknown group of {law}>"][law] = value
                for g, members in by_group.items():
                    options = [Interval(v) for v in members.values()]
                    if any(l not in members for l in laws_by_group[g]) or g.startswith("<unknown"):
                        options.append(Interval(0))
                    groups.append({"name": g, "kind": "law group", "options": options,
                                   "laws": members})

            remaining = dict(static_values)
            for exclusive in STATIC_MODIFIER_EXCLUSIVE_GROUPS:
                members = {s: remaining.pop(s) for s in exclusive if s in remaining}
                if members:
                    options = [self._static_option(s, v, multiplied) for s, v in members.items()]
                    options.append(Interval(0))
                    groups.append({"name": " | ".join(members), "kind": "exclusive static modifiers",
                                   "options": options, "laws": None})
            for s, v in remaining.items():
                opt = self._static_option(s, v, multiplied)
                options = [opt] if s in STATIC_MODIFIER_ALWAYS_ON else [opt, Interval(0)]
                groups.append({"name": s, "kind": "static modifier", "options": options, "laws": None})

            self.groups[mod] = groups

    def _static_option(self, name, value, multiplied):
        if name in STATIC_MODIFIER_MULTIPLIERS:
            return Interval(value) * Interval(*STATIC_MODIFIER_MULTIPLIERS[name])
        if name in multiplied:
            self.warnings.append(
                f"Static modifier '{name}' is applied with a multiplier somewhere; set its range in "
                f"STATIC_MODIFIER_MULTIPLIERS (counted unscaled for now)")
        return Interval(value)

    def _find_multiplied_static_modifiers(self):
        """Names of static modifiers applied with `add_modifier = { name = X multiplier = ... }`."""
        result = set()
        pattern = re.compile(r"name\s*=\s*([\w.:]+)[^{}]*?multiplier\s*=|multiplier\s*=[^{}]*?name\s*=\s*([\w.:]+)")
        for base in ([self.vanilla_path] if self.vanilla_path else []) + [MOD_PATH]:
            for path in glob.glob(os.path.join(base, "**", "*.txt"), recursive=True):
                if "/common/static_modifiers/" in path:
                    continue
                try:
                    with open(path, encoding="utf-8-sig", errors="replace") as f:
                        text = f.read()
                except OSError:
                    continue
                if "multiplier" not in text:
                    continue
                for m in pattern.finditer(text):
                    result.add(m.group(1) or m.group(2))
        return result

    def range(self, mod):
        if mod in MODIFIER_OVERRIDES:
            return Interval(*MODIFIER_OVERRIDES[mod])
        total = Interval(0)
        for g in self.groups.get(mod, []):
            total = total + hull_all(g["options"])
        return total

    def achievable(self, mod, limit):
        """Every value the modifier can take, or None if there are more than `limit` (or they
        aren't exact)."""
        if mod in MODIFIER_OVERRIDES:
            return None
        sums = {0.0}
        for g in self.groups.get(mod, []):
            if not all(o.is_exact() for o in g["options"]):
                return None
            sums = {round(s + o.lo, 9) for s in sums for o in g["options"]}
            if len(sums) > limit:
                return None
        return sorted(sums)

    def pieces(self, mod, n):
        """Intervals covering the modifier's range, at most n of them."""
        points = self.achievable(mod, n)
        if points is not None:
            return [Interval(p) for p in points]
        r = self.range(mod)
        if n <= 1 or not math.isfinite(r.lo) or not math.isfinite(r.hi) or r.is_exact():
            return [r]
        floor = 0.01  # 1 + x below this is a factor of (almost) zero
        if mod.endswith("_mult") and 1 + r.hi > floor:
            bounds = []
            lo = r.lo
            if 1 + r.lo < floor:
                bounds.append(r.lo)
                lo = floor - 1
                n -= 1
            a, b = 1 + lo, 1 + r.hi
            bounds += [a * (b / a) ** (i / n) - 1 for i in range(n)] + [r.hi]
        else:
            bounds = [r.lo + (r.hi - r.lo) * i / n for i in range(n)] + [r.hi]
        return [Interval(lo, hi) for lo, hi in zip(bounds, bounds[1:])]


# --------------------------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------------------------

ARITH_OPS = {"value", "add", "subtract", "multiply", "divide", "min", "max"}
IGNORED_KEYS = {"desc", "format", "save_temporary_scope_as", "save_scope_as", "save_temporary_value_as"}
CHAIN_KEYS = ("if", "else_if", "else")
LOGIC_KEYS = {"AND", "OR", "NOT", "NOR", "NAND"}
CMP = {
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b, "=": lambda a, b: a == b, "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def ref_key(ref):
    return ref.split(".")[-1]


def is_engine_divide(e):
    """True for a `divide = { ... }` that only divides out modifiers the game applies itself."""
    if e.k != "divide" or not isinstance(e.v, list):
        return False
    refs = set()
    collect_refs(e.v, refs)
    mods = {ref_key(r)[len("modifier:"):] for r in refs if ref_key(r).startswith("modifier:")}
    return bool(mods) and all(ENGINE_APPLIED_MODIFIER_RE.match(m) for m in mods)


def iter_chains(entries):
    """Groups an entry list into single entries and if/else_if/else chains."""
    i, n = 0, len(entries)
    while i < n:
        e = entries[i]
        if e.k == "if":
            chain = [e]
            i += 1
            while i < n and entries[i].k in ("else_if", "else"):
                chain.append(entries[i])
                i += 1
                if chain[-1].k == "else":
                    break
            yield chain
        else:
            yield e
            i += 1


class Context:
    def __init__(self, pop_type, strata, flags):
        self.pop_type = pop_type
        self.strata = strata
        self.flags = flags

    def label(self):
        parts = [self.pop_type]
        parts += [f"{k}={'yes' if v else 'no'}" for k, v in self.flags.items()]
        return ", ".join(parts)


class Evaluator:
    def __init__(self, script_values, modifiers, strata_of):
        self.script_values = script_values
        self.modifiers = modifiers
        self.strata_of = strata_of
        self.records = {}          # id(entry) -> Interval after the step
        self.reached = defaultdict(int)  # id(branch entry) -> times taken
        self.merges = {}           # id(first entry of an if chain) -> Interval after the chain
        self.operands = {}         # id(entry) -> Interval of the entry's operand
        self.unset = defaultdict(set)    # reference -> places used
        self.unknown_ops = set()
        self.stack = []

    # ---- values -------------------------------------------------------------------------

    def resolve(self, ref, ctx, env):
        if NUMBER_RE.match(ref):
            return Interval(float(ref))
        key = ref_key(ref)
        if key in env:
            return env[key]
        if key.startswith("modifier:"):
            return self.modifiers.range(key[len("modifier:"):])
        if key in MANUAL_RANGES:
            r = MANUAL_RANGES[key]
            if r is None:
                self.unset[key].add(self.stack[-1] if self.stack else "?")
                return Interval.unbounded()
            return Interval(*r)
        if key in self.script_values:
            if key in self.stack:
                self.unset[key].add("recursive script value")
                return Interval.unbounded()
            self.stack.append(key)
            try:
                return self.eval_block(self.script_values[key], ctx, env, None)
            finally:
                self.stack.pop()
        self.unset[key].add(self.stack[-1] if self.stack else "?")
        return Interval.unbounded()

    def operand(self, e, ctx, env):
        if isinstance(e.v, list):
            return self.eval_block(e.v, ctx, env, None)
        return self.resolve(e.v, ctx, env)

    def apply(self, acc, e, ctx, env):
        x = self.operand(e, ctx, env)
        self.operands[id(e)] = x.hull(self.operands.get(id(e)))
        if e.k == "value":
            return x
        acc = acc if acc is not None else Interval(0)
        if e.k == "add":
            return acc + x
        if e.k == "subtract":
            return acc - x
        if e.k == "multiply":
            return acc * x
        if e.k == "divide":
            return acc / x
        if e.k == "min":
            return acc.clamp_min(x)
        if e.k == "max":
            return acc.clamp_max(x)
        raise AssertionError(e.k)

    def eval_block(self, entries, ctx, env, acc):
        """Applies a block of script value operations to acc (None = start of a fresh value)."""
        for item in iter_chains(entries):
            if isinstance(item, list):
                acc = self.eval_chain(item, ctx, env, acc)
                continue
            e = item
            if is_engine_divide(e):
                self.record(e, acc)
            elif e.k in ARITH_OPS:
                acc = self.apply(acc, e, ctx, env)
                self.record(e, acc)
            elif e.k in IGNORED_KEYS or e.k == "limit":
                continue
            elif isinstance(e.v, list):
                # Scope change (owner = { ... }, scope:interest_group = { ... }): same accumulator
                acc = self.eval_block(e.v, ctx, env, acc)
                self.record(e, acc)
            else:
                self.unknown_ops.add(e.k)
        return acc if acc is not None else Interval(0)

    def eval_chain(self, chain, ctx, env, acc):
        results = []
        can_fall_through = True
        for branch in chain:
            body = branch.v if isinstance(branch.v, list) else []
            if branch.k == "else":
                truth, env_true, env_false = True, env, env
            else:
                limit = find(body, "limit")
                truth, env_true, env_false = self.condition(limit.v if limit else [], ctx, env)
            if truth is not False:
                self.reached[id(branch)] += 1
                r = self.eval_block(body, ctx, env_true, acc)
                self.record(branch, r)
                results.append(r)
            if truth is True:
                can_fall_through = False
                break
            env = env_false
        if can_fall_through:
            results.append(acc if acc is not None else Interval(0))
        result = hull_all(results)
        self.merges[id(chain[0])] = result.hull(self.merges.get(id(chain[0])))
        return result

    def record(self, e, value):
        if value is not None:
            self.records[id(e)] = value.hull(self.records.get(id(e)))

    # ---- conditions -----------------------------------------------------------------------
    # Returns (truth, env_if_true, env_if_false); truth is True/False/None (unknown).

    def condition(self, entries, ctx, env):
        if isinstance(entries, str):
            return None, env, env
        if len(entries) == 1:
            return self.leaf(entries[0], ctx, env)
        return self.combine("AND", entries, ctx, env), env, env

    def combine(self, op, entries, ctx, env):
        truths = [self.leaf(e, ctx, env)[0] for e in entries]
        if op in ("AND", "NOT", "NAND"):
            r = False if False in truths else (True if all(t is True for t in truths) else None)
        else:
            r = True if True in truths else (False if all(t is False for t in truths) else None)
        if op in ("NOT", "NOR", "NAND"):
            r = None if r is None else not r
        return r

    def leaf(self, e, ctx, env):
        k, op, v = e.k, e.op, e.v
        if k in LOGIC_KEYS and isinstance(v, list):
            return self.combine(k, v, ctx, env), env, env
        if isinstance(v, list):
            # Scope change inside a trigger: implicit AND
            if k == "limit":
                return self.condition(v, ctx, env)
            if len(v) == 1:
                return self.leaf(v[0], ctx, env)
            return self.combine("AND", v, ctx, env), env, env
        if k == "is_pop_type" and op == "=":
            return ctx.pop_type == v, env, env
        if k == "strata" and op in CMP and v in STRATA_ORDER and ctx.strata in STRATA_ORDER:
            return CMP[op](STRATA_ORDER[ctx.strata], STRATA_ORDER[v]), env, env
        if k in ctx.flags and op == "=" and v in ("yes", "no"):
            return ctx.flags[k] == (v == "yes"), env, env
        if k == "always" and v in ("yes", "no"):
            return v == "yes", env, env
        if op in CMP and isinstance(v, str) and NUMBER_RE.match(v):
            return self.compare(k, op, float(v), ctx, env)
        return None, env, env

    def compare(self, ref, op, number, ctx, env):
        key = ref_key(ref)
        manual = key in env or (key in MANUAL_RANGES and MANUAL_RANGES[key] is not None)
        if not manual:
            return None, env, env
        r = self.resolve(ref, ctx, env)
        if op in ("<", "<="):
            true_r = Interval(r.lo, min(r.hi, number)) if r.lo <= number else None
            false_r = Interval(max(r.lo, number), r.hi) if r.hi >= number else None
        elif op in (">", ">="):
            true_r = Interval(max(r.lo, number), r.hi) if r.hi >= number else None
            false_r = Interval(r.lo, min(r.hi, number)) if r.lo <= number else None
        else:
            return None, env, env
        if op in ("<", ">") and true_r is not None and true_r.is_exact() and true_r.lo == number:
            true_r = None
        if op in ("<=", ">=") and false_r is not None and false_r.is_exact() and false_r.lo == number:
            false_r = None
        if true_r is None:
            return False, env, env
        if false_r is None:
            return True, env, env
        return None, {**env, key: true_r}, {**env, key: false_r}


# --------------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------------

def render_condition(entries, depth=0):
    if isinstance(entries, str):
        return entries
    parts = []
    for e in entries:
        if isinstance(e.v, list):
            inner = render_condition(e.v, depth + 1)
            parts.append(f"{e.k}({inner})" if e.k in LOGIC_KEYS else f"{e.k}: {inner}")
        elif e.op is None:
            parts.append(e.k)
        else:
            parts.append(f"{e.k} {e.op} {e.v}")
    return ", ".join(parts)


def mm_text(s, limit=110):
    if len(s) > limit:
        s = s[:limit - 1] + "…"
    s = html.escape(s, quote=False)
    return s.replace('"', "#quot;")


# Runs of operations are split into several nodes past this many label lines.
MAX_NODE_LINES = 12

# Node classes of the .mmd files (light theme). The HTML page swaps in the set matching its theme.
CLASS_DEFS = [
    "classDef unreached fill:#eee,stroke:#bbb,color:#999,stroke-dasharray:4 3",
    "classDef modifier fill:#e8f1ff,stroke:#5b8def,color:#1d1d1f",
    "classDef unset fill:#fff1e0,stroke:#e08a1e,color:#1d1d1f",
    "classDef terminal fill:#e9f7ec,stroke:#3a9a55,color:#1d1d1f",
    "classDef inlined fill:#f6f3fb,stroke:#9b7fd1",
    "classDef header fill:#ffffff,stroke:#9b7fd1,color:#1d1d1f",
]

OP_SYMBOLS = {"value": "=", "add": "+", "subtract": "−", "multiply": "×", "divide": "÷",
              "min": "≥", "max": "≤"}


def short_ref(ref, limit=52):
    """Display form of a value reference: scope prefixes and `modifier:` dropped (modifiers are
    coloured instead), long names shortened in the middle."""
    if NUMBER_RE.match(ref):
        return ref
    key = ref_key(ref)
    if key.startswith("modifier:"):
        key = key[len("modifier:"):]
    if len(key) > limit:
        key = key[:limit // 2 - 1] + "…" + key[-(limit // 2):]
    return key


NODE_PLACEHOLDER_RE = re.compile(r"^%%node:(\w+)$", re.M)


def expand_chart(template, nodes, expanded=()):
    """Fills the node placeholders of a chart template, with full labels for `expanded` nodes."""
    def fill(m):
        n = nodes[m.group(1)]
        return f'{m.group(1)}{n["o"]}"{n["f"] if m.group(1) in expanded else n["s"]}"{n["c"]}'
    return NODE_PLACEHOLDER_RE.sub(fill, template)


class FlowchartBuilder:
    """Builds a chart template: node definitions are `%%node:<id>` placeholders (Mermaid comments),
    filled from `self.nodes` with either the shortened or the full label by expand_chart."""

    def __init__(self, ev, modifiers, script_values, inline=()):
        self.ev = ev
        self.modifiers = modifiers
        self.script_values = script_values
        self.inline = set(inline)  # script values drawn inside the chart instead of as a reference
        self.lines = []
        self.nodes = {}
        self.full = False
        self.counter = itertools.count()

    def node_id(self):
        return f"n{next(self.counter)}"

    def text(self, s, limit=110):
        return mm_text(s, 100000 if self.full else limit)

    def ref(self, r):
        return mm_text(r if self.full else short_ref(r), 100000)

    def node(self, label, shape="rect", cls=None):
        """`label` is a function returning the label text, called once shortened and once in full."""
        nid = self.node_id()
        open_, close = {"rect": ("[", "]"), "round": ("(", ")"), "hexagon": ("{{", "}}"),
                        "stadium": ("([", "])")}[shape]
        short = label()
        self.full = True
        try:
            full = label()
        finally:
            self.full = False
        self.nodes[nid] = {"o": open_, "c": close, "s": short, "f": full}
        self.lines.append(f"%%node:{nid}")
        if cls:
            self.lines.append(f"class {nid} {cls}")
        return nid

    def edge(self, a, b, label=None, dotted=False):
        arrow = "-.->" if dotted else "-->"
        if label:
            self.lines.append(f'{a} {arrow}|"{label}"| {b}')
        else:
            self.lines.append(f"{a} {arrow} {b}")

    def rng(self, e):
        r = self.ev.records.get(id(e))
        return str(r) if r is not None else "unreached"

    def operand_range(self, e):
        r = self.ev.operands.get(id(e))
        return str(r) if r is not None else "unreached"

    def build(self, title, entries):
        self.lines = ["flowchart TD"] + CLASS_DEFS
        start = self.node(lambda: self.text(title), "stadium", "terminal")
        last, _, _ = self.block(entries, start)
        return "\n".join(self.lines), self.nodes, last

    # ---- folding ----------------------------------------------------------------------------
    # An "item" is either an entry or an if/else_if/else chain (a list of entries).

    @staticmethod
    def is_drawn(item):
        if isinstance(item, list):
            return True
        return not (item.k in IGNORED_KEYS or item.k == "limit"
                    or (item.k not in ARITH_OPS and not isinstance(item.v, list)))

    @staticmethod
    def is_zero_start(item):
        return (not isinstance(item, list) and item.k == "value" and isinstance(item.v, str)
                and NUMBER_RE.match(item.v) and float(item.v) == 0)

    def items(self, entries):
        """Drawn items of a block, without the redundant leading `value = 0`."""
        result = [i for i in iter_chains(entries) if self.is_drawn(i)]
        if result and self.is_zero_start(result[0]):
            result = result[1:]
        return result

    def foldable(self, item):
        """True if an item can be drawn as lines inside a node: plain operations, blocks
        without branching, and an `if` without else/else_if around such a body."""
        if isinstance(item, list):
            return len(item) == 1 and isinstance(item[0].v, list) and self.is_simple(item[0].v)
        if not isinstance(item.v, list):
            return not self.is_inlined(item)
        return self.is_simple(item.v)

    def is_inlined(self, e):
        return isinstance(e.v, str) and ref_key(e.v) in self.inline

    def is_simple(self, entries):
        return all(self.foldable(i) for i in self.items(entries))

    def result(self, item):
        r = self.ev.merges.get(id(item[0])) if isinstance(item, list) else self.ev.records.get(id(item))
        return str(r) if r is not None else None

    def refs(self, item, out):
        if isinstance(item, list):
            for b in item:
                self.refs(b, out)
        elif isinstance(item.v, list):
            for x in item.v:
                self.refs(x, out)
        elif isinstance(item.v, str):
            out.append(ref_key(item.v))
        return out

    # ---- lines ------------------------------------------------------------------------------

    def item_lines(self, item, indent=""):
        sub = indent + "&nbsp;&nbsp;"
        if isinstance(item, list):
            limit = find(item[0].v, "limit")
            cond = render_condition(limit.v) if limit else "?"
            return [f"{indent}<i>{self.text(cond, 90)} ?</i>"] + self.lines_for(item[0].v, sub)
        e = item
        if not isinstance(e.v, list):
            line = f"{indent}<b>{OP_SYMBOLS.get(e.k, e.k)}</b> {self.ref(e.v)}"
            if not NUMBER_RE.match(e.v):
                line += f" <i>∈ {self.operand_range(e)}</i>"
            return [line]
        if is_engine_divide(e):
            refs = sorted({short_ref(r) for r in self.refs(e, []) if r.startswith("modifier:")})
            return [f"{indent}<s>÷ (1 + {self.text(' + '.join(refs))})</s> <i>skipped: applied by the game</i>"]
        desc = find(e.v, "desc")
        name = f" <i>{self.text(desc.v.strip(chr(34)), 40)}</i>" if desc else ""
        if e.k not in ARITH_OPS:
            return [f"{indent}<u>{self.text(e.k)}</u>:"] + self.lines_for(e.v, sub)
        sym = OP_SYMBOLS[e.k]
        inner = self.items(e.v)
        if len(inner) == 1 and not isinstance(inner[0], list) and inner[0].k == "value" \
                and not isinstance(inner[0].v, list):
            # `add = { desc = X value = Y }` reads as a single operation
            line = self.item_lines(inner[0], indent)[0].replace("<b>=</b>", f"<b>{sym}</b>", 1)
            return [line + name]
        head = f"{indent}<b>{sym}</b> (…){name} <i>= {self.operand_range(e)}</i>"
        return [head] + self.lines_for(e.v, sub)

    def lines_for(self, entries, indent):
        return [l for i in self.items(entries) for l in self.item_lines(i, indent)]

    def items_lines(self, items):
        lines = []
        for item in items:
            item_lines = self.item_lines(item)
            r = self.result(item)
            r = f"<b>{r}</b>" if r is not None else "unreached"
            single_value = (not isinstance(item, list) and item.k == "value" and not isinstance(item.v, list)
                            and self.result(item) == self.operand_range(item))
            if single_value:
                pass  # `= 5 → 5` says nothing new
            elif len(item_lines) == 1:
                item_lines[0] += f" → {r}"
            else:
                item_lines.append(f"→ {r}")
            lines += item_lines
        return lines

    def items_node(self, items):
        result = self.result(items[-1])
        keys = [k for i in items for k in self.refs(i, [])]
        if result is None:
            cls = "unreached"
        elif any(k in self.ev.unset for k in keys):
            cls = "unset"
        elif any(k.startswith("modifier:") for k in keys):
            cls = "modifier"
        else:
            cls = None
        return self.node(lambda: "<br/>".join(self.items_lines(items)), "rect", cls)

    # ---- structure --------------------------------------------------------------------------

    def block(self, entries, prev, prev_label=None, dotted=False):
        """Renders a block after node `prev`. Returns (last node, unconsumed edge label, dotted).

        Runs of foldable items (see `foldable`) become a single node; only real branching
        (else_if/else chains, or conditions around branching bodies) is drawn as a graph."""
        pending = []
        pending_lines = 0

        def flush():
            nonlocal prev, prev_label, dotted, pending_lines
            if pending:
                nid = self.items_node(pending)
                pending_lines = 0
                self.edge(prev, nid, prev_label, dotted)
                prev, prev_label, dotted = nid, None, False
                pending.clear()

        for item in self.items(entries):
            if self.foldable(item):
                size = len(self.item_lines(item))
                if pending and pending_lines + size > MAX_NODE_LINES:
                    flush()
                pending.append(item)
                pending_lines += size
                continue
            flush()
            if isinstance(item, list):
                prev, prev_label, dotted = self.chain(item, prev, prev_label, dotted)
            elif self.is_inlined(item):
                prev, prev_label, dotted = self.inlined(item, prev, prev_label, dotted)
            else:
                prev, prev_label, dotted = self.subblock(item, prev, prev_label, dotted)
        flush()
        return prev, prev_label, dotted

    def subblock(self, e, prev, prev_label, dotted):
        desc = find(e.v, "desc")
        if e.k in ARITH_OPS:
            title = OP_SYMBOLS[e.k] + (f" {desc.v.strip(chr(34))}" if desc else "")
        else:
            title = e.k
        inner = self.items(e.v)
        if len(inner) == 1 and not isinstance(inner[0], list) and inner[0].k == "value" \
                and self.is_inlined(inner[0]):
            # `multiply = { value = <inlined script value> }`: one subgraph for both
            return self.inlined(inner[0], prev, prev_label, dotted, title, e)
        if e.k in ARITH_OPS:
            title += f" → {self.rng(e)}"
        return self.group(title, e.v, prev, prev_label, dotted)

    def inlined(self, e, prev, prev_label, dotted, title=None, outer=None):
        """A reference to a script value in `self.inline`, drawn as a subgraph holding its body.
        `title`/`outer` describe an enclosing `op = { value = <script value> }` block."""
        name = ref_key(e.v)
        if title is None:
            title = OP_SYMBOLS[e.k] if e.k in ARITH_OPS else e.k
        title += f" {name} ∈ {self.operand_range(e)}"
        step = outer if outer is not None else e
        if step.k in ARITH_OPS and step.k != "value":
            title += f" → {self.rng(step)}"
        return self.group(title, self.script_values[name], prev, prev_label, dotted, "inlined")

    def group(self, title, entries, prev, prev_label, dotted, cls=None):
        """A subgraph around a block. Its title is a header node rather than the subgraph label,
        whose position Mermaid doesn't keep clear of nested subgraphs."""
        sid = self.node_id()
        self.lines.append(f'subgraph {sid}[" "]')
        self.lines.append("direction TB")
        if cls:
            self.lines.append(f"class {sid} {cls}")
        head = self.node(lambda: f"<b>{self.text(title)}</b>", "round", "header")
        self.edge(prev, head, prev_label, dotted)
        last, label, dotted = self.block(entries, head)
        self.lines.append("end")
        return last, label, dotted

    def chain(self, chain, prev, prev_label, dotted):
        ends = []
        cur, cur_label = prev, prev_label
        for branch in chain:
            body = branch.v if isinstance(branch.v, list) else []
            reached = self.ev.reached.get(id(branch), 0) > 0
            if branch.k == "else":
                ends.append(self.block(body, cur, cur_label, not reached))
                cur = None
                break
            limit = find(body, "limit")
            cond = render_condition(limit.v) if limit else "?"
            d = self.node(lambda cond=cond: self.text(cond, 90), "hexagon", None if reached else "unreached")
            self.edge(cur, d, cur_label, dotted)
            dotted = False
            ends.append(self.block(body, d, "yes", not reached))
            cur, cur_label = d, "no"
        merge_range = self.ev.merges.get(id(chain[0]))
        merge = self.node(lambda: f"→ <b>{merge_range if merge_range else 'unreached'}</b>", "round",
                          None if merge_range else "unreached")
        for end, label, dotted_edge in ends:
            self.edge(end, merge, label, dotted_edge)
        if cur is not None:
            self.edge(cur, merge, cur_label)
        return merge, None, False


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------

def load_strata(vanilla_path):
    strata_of = {}
    db = load_database("social_classes", vanilla_path)
    for cls, body in db.items():
        h = find(body, "social_hierarchy")
        if h and h.v != "default_social_hierarchy":
            continue
        s = find(body, "strata")
        prof = find(body, "allowed_professions")
        if s and prof and isinstance(prof.v, list):
            for p in prof.v:
                strata_of[p.k] = s.v
    if not strata_of:
        strata_of = {
            "aristocrats": "upper", "capitalists": "upper",
            "academics": "middle", "bureaucrats": "middle", "clergymen": "middle", "engineers": "middle",
            "farmers": "middle", "officers": "middle", "shopkeepers": "middle",
            "clerks": "lower", "laborers": "lower", "machinists": "lower", "peasants": "lower",
            "slaves": "lower", "soldiers": "lower",
        }
    return strata_of


def collect_refs(entries, out):
    for e in entries:
        if isinstance(e.v, list):
            collect_refs(e.v, out)
        elif isinstance(e.v, str):
            out.add(e.v)
            out.add(e.k)


def reachable_script_values(entries, script_values):
    """Script values referenced by `entries`, directly or through other script values."""
    refs = set()
    collect_refs(entries, refs)
    queue = [ref_key(r) for r in refs if ref_key(r) in script_values]
    seen = set()
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        sv_refs = set()
        collect_refs(script_values[name], sv_refs)
        queue += [ref_key(r) for r in sv_refs if ref_key(r) in script_values]
    return seen


def count_modifier_reads(entries, script_values, counts, stack=()):
    """Counts how often each modifier is read when evaluating `entries`, following script values
    as many times as they are referenced."""
    for e in entries:
        if is_engine_divide(e):
            continue
        if isinstance(e.v, list):
            count_modifier_reads(e.v, script_values, counts, stack)
        elif isinstance(e.v, str):
            key = ref_key(e.v)
            if key.startswith("modifier:"):
                counts[key[len("modifier:"):]] += 1
            elif key in script_values and key not in stack:
                count_modifier_reads(script_values[key], script_values, counts, stack + (key,))
    return counts


def correlated_pieces(mods, modifiers):
    """{modifier: [Interval]} for the modifiers to pin, within CORRELATION_MAX_COMBINATIONS."""
    n = CORRELATION_SPLITS
    while True:
        pieces = {m: modifiers.pieces(m, n) for m in mods}
        if n <= 1 or math.prod(len(p) for p in pieces.values()) <= CORRELATION_MAX_COMBINATIONS:
            return pieces
        n -= 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("igs", nargs="*", help="interest groups to render (default: all)")
    parser.add_argument("--vanilla", default=DEFAULT_VANILLA_PATH,
                        help="path to the Victoria 3 'game' directory, used for vanilla laws/modifiers")
    parser.add_argument("--out", default=OUTPUT_DIR, help="output directory")
    args = parser.parse_args()

    vanilla = args.vanilla if args.vanilla and os.path.isdir(args.vanilla) else None
    if not vanilla:
        print(f"warning: vanilla game not found at {args.vanilla!r}; vanilla laws and law groups "
              f"are unknown, so injected laws can't be grouped", file=sys.stderr)

    igs = load_database("interest_groups", vanilla)
    script_values = load_database("script_values", vanilla)
    strata_of = load_strata(vanilla)
    pop_types = sorted(strata_of)

    selected = args.igs or sorted(k for k, v in igs.items() if find(v, "pop_weight"))
    missing = [i for i in selected if i not in igs]
    if missing:
        sys.exit(f"unknown interest groups: {', '.join(missing)}")

    # Script values reached by each pop weight. Those reached by a single interest group are drawn
    # inside its flowchart, the others in their own section.
    reached = {}
    for ig, body in igs.items():
        pw = find(body, "pop_weight")
        if pw and isinstance(pw.v, list):
            reached[ig] = reachable_script_values(pw.v, script_values)
    users = defaultdict(set)
    for ig, svs in reached.items():
        for sv in svs:
            users[sv].add(ig)

    # Every modifier referenced by the selected pop weights, including through script values
    modifiers_of = {}
    for ig in selected:
        pw = find(igs[ig], "pop_weight")
        if not pw or not isinstance(pw.v, list):
            continue
        refs = set()
        collect_refs(pw.v, refs)
        for sv in reached[ig]:
            collect_refs(script_values[sv], refs)
        modifiers_of[ig] = sorted({ref_key(r)[9:] for r in refs if ref_key(r).startswith("modifier:")})
    modifier_names = {m for mods in modifiers_of.values() for m in mods}

    print(f"Scanning modifier sources for {len(modifier_names)} modifiers...", file=sys.stderr)
    modifiers = ModifierSources(modifier_names, vanilla)
    ev = Evaluator(script_values, modifiers, strata_of)

    flag_names = list(CONTEXT_FLAGS)
    flag_combos = [dict(zip(flag_names, vals)) for vals in itertools.product(*CONTEXT_FLAGS.values())]

    results = []
    used_modifiers = set()
    used_script_values = set()
    for ig in selected:
        body = igs[ig]
        pw = find(body, "pop_weight")
        if not pw or not isinstance(pw.v, list):
            continue
        potential = find(body, "pop_potential")
        mods = modifiers_of[ig]
        used_modifiers.update(mods)
        inline = {sv for sv in reached[ig] if users[sv] == {ig}}
        used_script_values.update(reached[ig] - inline)

        reads = count_modifier_reads(pw.v, script_values, defaultdict(int))
        pinned = correlated_pieces(sorted(m for m, c in reads.items() if c > 1), modifiers)
        pinned = {m: p for m, p in pinned.items() if len(p) > 1}  # a single value needs no pinning
        pin_envs = [{f"modifier:{m}": p for m, p in zip(pinned, combo)}
                    for combo in itertools.product(*pinned.values())]

        table = {}
        for pt in pop_types:
            for flags in flag_combos:
                ctx = Context(pt, strata_of.get(pt), flags)
                if potential and isinstance(potential.v, list):
                    truth = ev.condition(potential.v, ctx, {})[0]
                    if truth is False:
                        continue
                weight = None
                for env in pin_envs:
                    ev.stack = [ig]
                    weight = ev.eval_block(pw.v, ctx, env, None).hull(weight)
                # The game treats negative weights as 0
                table[(pt, tuple(flags.values()))] = weight.clamp_min(Interval(0))
        results.append({"ig": ig, "pw": pw.v, "table": table, "modifiers": mods, "inline": inline,
                        "pinned": pinned})

    os.makedirs(os.path.join(args.out, "mmd"), exist_ok=True)
    sections = []
    for res in results:
        fb = FlowchartBuilder(ev, modifiers, script_values, res["inline"])
        chart, nodes, last = fb.build(res["ig"], res["pw"])
        end = hull_all(res["table"].values())
        chart += f'\nfinal(["final pop_weight ∈ {end} (clamped to ≥ 0)"])\n{last} --> final\nclass final terminal\n'
        with open(os.path.join(args.out, "mmd", f"{res['ig']}.mmd"), "w", encoding="utf-8") as f:
            f.write(expand_chart(chart, nodes))
        res["chart"] = chart
        res["nodes"] = nodes
        res["end"] = end
        sections.append(res)

    sv_charts = []
    for name in sorted(used_script_values):
        fb = FlowchartBuilder(ev, modifiers, script_values)
        chart, nodes, _ = fb.build(name, script_values[name])
        with open(os.path.join(args.out, "mmd", f"script_value_{name}.mmd"), "w", encoding="utf-8") as f:
            f.write(expand_chart(chart, nodes))
        sv_charts.append({"name": name, "chart": chart, "nodes": nodes})

    out_html = os.path.join(args.out, "pop_weight_flowchart.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(render_html(sections, sv_charts, modifiers, sorted(used_modifiers), ev,
                            flag_names, flag_combos, pop_types))

    # Report
    print(f"Wrote {out_html}", file=sys.stderr)
    for res in sections:
        print(f"  {res['ig']:<40} {res['end']}", file=sys.stderr)
    if ev.unset:
        print("\nValues without a range (treated as unbounded) - set them in MANUAL_RANGES:", file=sys.stderr)
        for k in sorted(ev.unset):
            print(f"  {k}  (used in: {', '.join(sorted(ev.unset[k]))})", file=sys.stderr)
    if ev.unknown_ops:
        print(f"\nIgnored unknown script value keys: {', '.join(sorted(ev.unknown_ops))}", file=sys.stderr)
    for w in sorted(set(modifiers.warnings)):
        print(f"warning: {w}", file=sys.stderr)


def render_html(sections, sv_charts, modifiers, used_modifiers, ev, flag_names, flag_combos, pop_types):
    def esc(s):
        return html.escape(str(s))

    parts = []
    for res in sections:
        rows = []
        header = "".join(
            f"<th>{esc(', '.join(f'{k}={chr(10003) if v else chr(10007)}' for k, v in combo.items()))}</th>"
            for combo in flag_combos)
        for pt in pop_types:
            cells = [res["table"].get((pt, tuple(c.values()))) for c in flag_combos]
            if all(c is None for c in cells):
                continue
            rows.append(f"<tr><th>{esc(pt)}</th>" + "".join(
                f"<td>{esc(c) if c is not None else '—'}</td>" for c in cells) + "</tr>")
        mod_html = "".join(render_modifier(m, modifiers) for m in res["modifiers"])
        pinned = "".join(
            f"<li><code>{esc(m)}</code> — "
            + (f"{len(p)} values" if all(i.is_exact() for i in p) else f"{len(p)} pieces of {esc(modifiers.range(m))}")
            + "</li>" for m, p in res["pinned"].items())
        pinned_html = (f"<p class='note'>Read more than once, so evaluated with one value shared by every "
                       f"read:</p><ul class='note'>{pinned}</ul>") if pinned else ""
        parts.append(f"""
<details class="ig" data-chart="{esc(json.dumps(res['chart']))}" data-nodes="{esc(json.dumps(res['nodes']))}">
  <summary><span class="name">{esc(res['ig'])}</span><span class="range">{esc(res['end'])}</span></summary>
  <div class="body">
    <h3>Final value by pop type</h3>
    <div class="scroll"><table><tr><th>pop type</th>{header}</tr>{''.join(rows)}</table></div>
    {'<h3>Correlated modifiers</h3>' + pinned_html if pinned_html else ''}
    {'<h3>Modifier sources</h3>' + mod_html if mod_html else ''}
    <h3>Flowchart</h3>
    <div class="chart"></div>
  </div>
</details>""")

    sv_parts = "".join(f"""
<details class="ig" data-chart="{esc(json.dumps(sv['chart']))}" data-nodes="{esc(json.dumps(sv['nodes']))}">
  <summary><span class="name">{esc(sv['name'])}</span></summary>
  <div class="body"><div class="chart"></div></div>
</details>""" for sv in sv_charts)

    all_mods = "".join(render_modifier(m, modifiers) for m in used_modifiers)
    unset = "".join(f"<li><code>{esc(k)}</code> — used in {esc(', '.join(sorted(v)))}</li>"
                    for k, v in sorted(ev.unset.items()))
    unset_html = (f"<div class='warn'><b>Unbounded values</b> (set them in <code>MANUAL_RANGES</code>):"
                  f"<ul>{unset}</ul></div>") if unset else ""
    manual = "".join(f"<tr><td><code>{esc(k)}</code></td><td>{esc(Interval(*v) if v else 'unset')}</td></tr>"
                     for k, v in MANUAL_RANGES.items())

    return HTML_TEMPLATE.format(
        sections="".join(parts), script_values=sv_parts, modifiers=all_mods,
        unset=unset_html, manual=manual, flags=esc(", ".join(flag_names)),
        class_defs=json.dumps(CLASS_DEFS))


def render_modifier(mod, modifiers):
    groups = modifiers.groups.get(mod, [])
    rows = []
    for g in groups:
        if g["laws"]:
            opts = ", ".join(f"{l} = {fmt(v)}" for l, v in g["laws"].items())
            if any(o.is_exact() and o.lo == 0 for o in g["options"]):
                opts += ", other laws = 0"
        else:
            opts = ", ".join(str(o) for o in g["options"])
        rows.append(f"<tr><td>{html.escape(g['kind'])}</td><td><code>{html.escape(g['name'])}</code></td>"
                    f"<td>{html.escape(opts)}</td><td>{hull_all(g['options'])}</td></tr>")
    override = " (overridden in MODIFIER_OVERRIDES)" if mod in MODIFIER_OVERRIDES else ""
    if not rows:
        rows.append("<tr><td colspan=4><i>no sources found</i></td></tr>")
    return (f"<details class='mod'><summary class='modname'><code>{html.escape(mod)}</code> ∈ "
            f"<b>{modifiers.range(mod)}</b>{override} <span class='note'>· {len(groups)} sources</span></summary>"
            f"<div class='scroll'><table><tr><th>kind</th><th>source</th><th>options (one active)</th>"
            f"<th>contribution</th></tr>{''.join(rows)}</table></div></details>")


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IG Pop Weights</title>
<style>
:root {{ color-scheme:light; --bg:#fbfbfa; --fg:#1d1d1f; --muted:#6b6b70; --line:#dedede; --card:#fff;
  --accent:#3a6fd8; --warn:#fff4e5; --warn-line:#f0c88a; --code:#f1f1f3; --hover:#f4f4f6; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ color-scheme:dark; --bg:#141417; --fg:#e6e6e9; --muted:#a0a0a8; --line:#34343b;
    --card:#1c1c20; --accent:#86a8ff; --warn:#33270f; --warn-line:#6b5020; --code:#26262c; --hover:#24242a; }}
}}
:root[data-theme="dark"] {{ color-scheme:dark; --bg:#141417; --fg:#e6e6e9; --muted:#a0a0a8; --line:#34343b;
  --card:#1c1c20; --accent:#86a8ff; --warn:#33270f; --warn-line:#6b5020; --code:#26262c; --hover:#24242a; }}
body {{ background:var(--bg); color:var(--fg); font:14px/1.5 system-ui, sans-serif; margin:0; padding:24px 16px; }}
main {{ max-width:1400px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 4px; }}
h2 {{ font-size:17px; margin:32px 0 8px; }}
h3 {{ font-size:13px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin:18px 0 6px; }}
p.lead {{ color:var(--muted); margin:0 0 16px; max-width:80ch; }}
details.ig {{ background:var(--card); border:1px solid var(--line); border-radius:8px; margin:8px 0; }}
details.ig > summary {{ cursor:pointer; padding:10px 14px; display:flex; justify-content:space-between; gap:12px;
  border-radius:8px; }}
details.ig > summary:hover {{ background:var(--hover); }}
details.ig > summary .name {{ font-weight:600; }}
details.ig > summary .range {{ font-variant-numeric:tabular-nums; color:var(--accent); }}
.body {{ padding:0 14px 14px; }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; font-variant-numeric:tabular-nums; font-size:13px; }}
th, td {{ border-bottom:1px solid var(--line); padding:4px 10px; text-align:left; white-space:nowrap; }}
.mod {{ margin:4px 0; }}
.mod[open] {{ margin-bottom:14px; }}
.modname {{ cursor:pointer; margin-bottom:4px; }}
.warn {{ background:var(--warn); border:1px solid var(--warn-line); border-radius:8px; padding:10px 14px; margin:12px 0; }}
.note {{ color:var(--muted); margin:4px 0; }}
header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }}
.themes {{ display:flex; border:1px solid var(--line); border-radius:6px; overflow:hidden; font-size:12px; }}
.themes button {{ font:inherit; color:var(--muted); background:var(--card); border:0; padding:3px 10px; cursor:pointer; }}
.themes button + button {{ border-left:1px solid var(--line); }}
.themes button[aria-pressed="true"] {{ color:var(--fg); background:var(--hover); font-weight:600; }}
.chartwrap {{ position:relative; }}
.chart {{ overflow:auto; max-height:85vh; border:1px solid var(--line); border-radius:6px; cursor:grab; background:var(--card); }}
.chart.dragging {{ cursor:grabbing; user-select:none; }}
.chart svg {{ max-width:none !important; display:block; }}
.chart .node foreignObject div, .chart .node .nodeLabel {{ text-align:left !important; }}
.chart .node.expandable {{ cursor:pointer; }}
.chart .node.expandable:hover > rect, .chart .node.expandable:hover > polygon {{ stroke-width:2px !important; }}
.zoombar {{ display:flex; gap:4px; align-items:center; margin:0 0 6px; font-size:12px; color:var(--muted); }}
.zoombar button {{ font:inherit; color:var(--fg); background:var(--card); border:1px solid var(--line);
  border-radius:4px; padding:2px 8px; cursor:pointer; }}
.zoombar .pct {{ min-width:4ch; text-align:right; font-variant-numeric:tabular-nums; }}
code {{ font-size:12px; background:var(--code); border-radius:3px; padding:0 3px; }}
</style>
</head>
<body>
<main>
<header>
<h1>Interest group pop weights</h1>
<div class="themes" role="group" aria-label="Theme"><button data-theme="auto">Auto</button><button data-theme="light">Light</button><button data-theme="dark">Dark</button></div>
</header>
<p class="lead">Each interest group's <code>pop_weight</code>, evaluated with interval arithmetic once per pop type
allowed by <code>pop_potential</code> and per combination of <code>{flags}</code>. Node labels show the range of the
running value after each step (over every evaluation that reached it). <code>modifier:</code> ranges sum every
source, taking at most one law per law group. A modifier read more than once by a pop weight takes the same value at
every read. Divisions by <code>1 + interest_group_…pop_attraction_mult</code> are skipped: they undo the multiplication the
game applies afterwards, so the result is the weight the game uses. Script values used by a single interest group are drawn inside its flowchart.</p>
{unset}
<h2>Interest groups</h2>
{sections}
<h2>Referenced script values</h2>
{script_values}
<h2>Modifiers</h2>
{modifiers}
<h2>Manual ranges</h2>
<table>{manual}</table>
</main>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<script>
// Theme: follows the system unless Light or Dark is picked (remembered in this browser).
const THEMES = {{
  light: {{
    vars: {{ background:'#ffffff', primaryColor:'#ffffff', primaryBorderColor:'#a2a2aa', primaryTextColor:'#1d1d1f',
      lineColor:'#8a8a92', clusterBkg:'#f5f5f7', clusterBorder:'#cfcfd5', edgeLabelBackground:'#ffffff',
      titleColor:'#1d1d1f', textColor:'#1d1d1f' }},
    classes: {class_defs},
  }},
  dark: {{
    vars: {{ background:'#1c1c20', primaryColor:'#26262c', primaryBorderColor:'#5c5c66', primaryTextColor:'#e6e6e9',
      lineColor:'#85858f', clusterBkg:'#202025', clusterBorder:'#3e3e47', edgeLabelBackground:'#1c1c20',
      titleColor:'#e6e6e9', textColor:'#e6e6e9' }},
    classes: [
      'classDef unreached fill:#222227,stroke:#46464f,color:#7a7a84,stroke-dasharray:4 3',
      'classDef modifier fill:#1a2843,stroke:#5b8def,color:#e6e6e9',
      'classDef unset fill:#382812,stroke:#e08a1e,color:#e6e6e9',
      'classDef terminal fill:#15301f,stroke:#3a9a55,color:#e6e6e9',
      'classDef inlined fill:#231f2c,stroke:#7d66b3',
      'classDef header fill:#2b2638,stroke:#7d66b3,color:#e6e6e9',
    ],
  }},
}};
const systemDark = window.matchMedia('(prefers-color-scheme: dark)');
let themePref = 'auto';
try {{ themePref = localStorage.getItem('theme') || 'auto'; }} catch (e) {{}}
const theme = () => themePref === 'auto' ? (systemDark.matches ? 'dark' : 'light') : themePref;
const renderers = [];

function applyTheme() {{
  if (themePref === 'auto') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = themePref;
  document.querySelectorAll('.themes button').forEach(b => b.setAttribute('aria-pressed', b.dataset.theme === themePref));
  mermaid.initialize({{ startOnLoad:false, theme:'base', maxTextSize: 1000000, maxEdges: 5000,
    themeVariables: {{ ...THEMES[theme()].vars, fontSize: '11px' }},
    flowchart: {{ htmlLabels:true, useMaxWidth:false, nodeSpacing:12, rankSpacing:16, padding:4, wrappingWidth:320,
      diagramPadding:4, subGraphTitleMargin: {{ top:2, bottom:2 }} }}, securityLevel:'loose' }});
  renderers.forEach(r => r());
}}
document.querySelector('.themes').addEventListener('click', ev => {{
  if (!ev.target.dataset.theme) return;
  themePref = ev.target.dataset.theme;
  try {{ localStorage.setItem('theme', themePref); }} catch (e) {{}}
  applyTheme();
}});
systemDark.addEventListener('change', () => {{ if (themePref === 'auto') applyTheme(); }});
applyTheme();

// Zoom: buttons, ctrl/cmd + wheel, and drag to pan. Starts fitted to the panel's width.
// Clicking a node whose text was shortened re-renders the chart with that node's full text.
const NODE_RE = /^%%node:(\\w+)$/gm;
const CLASSDEF_RE = /^classDef .*$/gm;

function setupChart(d) {{
  const box = d.querySelector('.chart');
  const template = JSON.parse(d.dataset.chart);
  const nodes = JSON.parse(d.dataset.nodes);
  const expanded = new Set();
  const bar = document.createElement('div');
  bar.className = 'zoombar';
  bar.innerHTML = '<button data-z="fitw">Fit width</button><button data-z="fit">Fit all</button>' +
    '<button data-z="out">−</button><span class="pct"></span><button data-z="in">+</button>' +
    '<button data-z="1">100%</button><button data-z="all">Expand all</button>' +
    '<span>· click a node to show its full text · ctrl+scroll to zoom, drag to pan</span>';
  box.before(bar);
  let svg = null, w = 1, h = 1, scale = null;

  const apply = s => {{
    scale = Math.min(4, Math.max(0.05, s));
    svg.setAttribute('width', w * scale);
    svg.setAttribute('height', h * scale);
    svg.style.width = svg.style.height = '';
    bar.querySelector('.pct').textContent = Math.round(scale * 100) + '%';
  }};
  const fitw = () => Math.min(1, (box.clientWidth - 2) / w);
  const fitAll = () => Math.min(fitw(), (box.clientHeight || window.innerHeight * 0.85) / h);

  async function render() {{
    const text = template.replace(NODE_RE, (m, id) => {{
      const n = nodes[id];
      return id + n.o + '"' + (expanded.has(id) ? n.f : n.s) + '"' + n.c;
    }}).replace(CLASSDEF_RE, '') + '\\n' + THEMES[theme()].classes.join('\\n');
    const {{ svg: markup }} = await mermaid.render('chart' + (n++), text);
    const left = box.scrollLeft, top = box.scrollTop;
    box.innerHTML = markup;
    svg = box.querySelector('svg');
    w = svg.viewBox.baseVal.width; h = svg.viewBox.baseVal.height;
    svg.querySelectorAll('g.node').forEach(g => {{
      const id = (g.id.match(/^flowchart-(\\w+?)-\\d+$/) || [])[1];
      if (id && nodes[id] && nodes[id].s !== nodes[id].f) {{
        g.classList.add('expandable');
        g.dataset.nid = id;
      }}
    }});
    apply(scale ?? fitw());
    box.scrollLeft = left; box.scrollTop = top;
  }}

  bar.addEventListener('click', ev => {{
    const z = ev.target.dataset.z;
    if (z === 'fitw') apply(fitw());
    else if (z === 'fit') apply(fitAll());
    else if (z === 'in') apply(scale * 1.25);
    else if (z === 'out') apply(scale / 1.25);
    else if (z === '1') apply(1);
    else if (z === 'all') {{
      const ids = Object.keys(nodes).filter(id => nodes[id].s !== nodes[id].f);
      const collapse = ids.every(id => expanded.has(id));
      ids.forEach(id => collapse ? expanded.delete(id) : expanded.add(id));
      ev.target.textContent = collapse ? 'Expand all' : 'Collapse all';
      render();
    }}
  }});
  box.addEventListener('wheel', ev => {{
    if (!ev.ctrlKey && !ev.metaKey) return;
    ev.preventDefault();
    const r = box.getBoundingClientRect();
    const px = ev.clientX - r.left + box.scrollLeft, py = ev.clientY - r.top + box.scrollTop;
    const old = scale;
    apply(scale * (ev.deltaY < 0 ? 1.15 : 1 / 1.15));
    box.scrollLeft = px * scale / old - (ev.clientX - r.left);
    box.scrollTop = py * scale / old - (ev.clientY - r.top);
  }}, {{ passive:false }});

  let drag = null;
  box.addEventListener('pointerdown', ev => {{
    drag = {{ x: ev.clientX, y: ev.clientY, l: box.scrollLeft, t: box.scrollTop, moved: false }};
    box.classList.add('dragging');
  }});
  window.addEventListener('pointermove', ev => {{
    if (!drag) return;
    if (Math.abs(ev.clientX - drag.x) + Math.abs(ev.clientY - drag.y) > 4) drag.moved = true;
    box.scrollLeft = drag.l - (ev.clientX - drag.x);
    box.scrollTop = drag.t - (ev.clientY - drag.y);
  }});
  window.addEventListener('pointerup', ev => {{
    if (drag && !drag.moved && box.contains(ev.target)) {{
      const g = ev.target.closest('g.node.expandable');
      if (g) {{
        const id = g.dataset.nid;
        expanded.has(id) ? expanded.delete(id) : expanded.add(id);
        render();
      }}
    }}
    drag = null;
    box.classList.remove('dragging');
  }});

  renderers.push(render);
  return render();
}}

let n = 0;
document.querySelectorAll('details.ig').forEach(d => d.addEventListener('toggle', async () => {{
  const target = d.querySelector('.chart');
  if (!d.open || target.dataset.done) return;
  target.dataset.done = 1;
  try {{
    await setupChart(d);
  }} catch (e) {{ target.textContent = 'Failed to render: ' + e; }}
}}));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
