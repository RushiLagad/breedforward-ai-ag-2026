"""Record SHA-256 checksums and sizes of the input files so two machines can prove they ran on the same data.
Writes results_summary/input_checksums.csv (hashes only; no data). Run from the repo root.

    python src/checksums.py
"""
import hashlib, os, glob
import pandas as pd

FILES = sorted(glob.glob("data/*.csv") + glob.glob("data/*.xlsx") + glob.glob("data/ImputedPopulations*/*.csv"))
rows = []
for f in FILES:
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    rows.append(dict(file=f.replace(os.sep, "/"), bytes=os.path.getsize(f), sha256=h.hexdigest()))
out = pd.DataFrame(rows)
out.to_csv("results_summary/input_checksums.csv", index=False)
print(f"{len(out)} files hashed -> results_summary/input_checksums.csv")
print(out[~out.file.str.contains("ImputedPopulations")].to_string(index=False))
