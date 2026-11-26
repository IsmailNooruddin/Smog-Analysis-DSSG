"""Checks that every decimal number in manuscript_m5.json comes from docs/tables/*.csv,
m4_params.json or m5_params.json (same rule as check_numbers_m4.py).

A number matches when some table value, raw or times 100 (percentages), lies within half a unit of
its last shown digit. Unmatched numbers are printed with their context for a manual check (constants
such as the 0.05 band, the 0.10/0.25 PSI cut-offs or the index weights).

Run from the repository root:
    python docs/manuscript/check_numbers_m5.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
doc = json.loads((ROOT / "docs" / "manuscript" / "manuscript_m5.json").read_text(encoding="utf-8"))


def walk(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)
    elif isinstance(v, (int, float)) and not isinstance(v, bool):
        yield float(v)


vals = []
for f in sorted((ROOT / "docs" / "tables").glob("*.csv")):
    d = pd.read_csv(f)
    for c in d.columns:
        vals.append(pd.to_numeric(d[c], errors="coerce").dropna().to_numpy(dtype=float))
for name in ["m4_params.json", "m5_params.json"]:
    vals.append(np.array(list(walk(json.loads((ROOT / "Dataset" / "clean" / name).read_text(encoding="utf-8"))))))
vals = np.concatenate(vals)
vals = vals[np.isfinite(vals)]
pool = np.concatenate([vals, 100 * vals])

texts = []
for b in doc["blocks"]:
    if b["t"] in ("ieee_refs", "section"):
        continue
    for k in ["text", "caption", "note"]:
        if b.get(k):
            texts.append(b[k])
    texts += b.get("items", [])
    for r in b.get("rows", []):
        texts.append(" | ".join(r))

num = re.compile(r"(?<![\w.])[−-]?\d{1,3}(?:,\d{3})*\.\d+")
checked, missing = 0, []
for t in texts:
    for m in num.finditer(t):
        s = m.group(0)
        dec = len(s.split(".")[1])
        x = float(s.replace("−", "-").replace(",", ""))
        checked += 1
        tol = 0.5 * 10 ** -dec + 1e-9
        if not np.any(np.abs(np.abs(pool) - abs(x)) <= tol):
            missing.append((s, t[max(0, m.start() - 60): m.end() + 30].replace("\n", " ")))

print(f"{checked} decimal numbers checked, {len(missing)} not found in the tables:")
for s, ctx in missing:
    print(f"  {s:>10}  …{ctx}…")
