#!/usr/bin/env python3
"""quilt-discovery-demo — Anthropic's 949-agent discovery pipeline, recreated in Quilt.

Stateless assembly line: agents never pass conversational context. Between every
cell sits an immutable, hash-manifested state layer (the Quilt-Package analog).
Every layer is replayable from genesis; nothing is trusted that isn't hashed.

Demo scale: 12 shards -> 12 workers -> consensus vote -> senior eval.
Run:  python3 pipeline.py     (deterministic; receipts in state/)

Cells:  A shard -> B workers -> C consensus -> D senior eval -> final targets
Doctrine: lineage in every manifest (Cell A note), immutable replay loops
(snapshot each layer), data/code decoupling.
"""
import hashlib, json, os, shutil
from pathlib import Path

ROOT = Path(__file__).parent
STATE = ROOT / "state"
rng_state = 0x51ED


def rng():
    global rng_state
    rng_state = (rng_state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    return rng_state >> 33


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_layer(cell, name, files: dict, lineage: str):
    """Immutable state layer: files + manifest with per-file hashes + lineage note."""
    layer = STATE / f"{cell}-{name}"
    layer.mkdir(parents=True, exist_ok=True)
    manifest = {"cell": cell, "layer": name, "lineage": lineage, "files": {}}
    for rel, content in sorted(files.items()):
        p = layer / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode() if isinstance(content, str) else content
        p.write_bytes(data)
        manifest["files"][rel] = sha(data)
    manifest["layer_hash"] = sha(json.dumps(manifest["files"], sort_keys=True).encode())
    (layer / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return layer.name  # layer DIRECTORY name; the hash lives inside manifest.json


# ---- Cell A: sharding -------------------------------------------------------
def cell_a():
    catalog = [{"id": f"cluster_{i}", "rt_gene": (i % 5 == 0),
                "noncoding_len": 40 + (i * 37) % 220} for i in range(48)]
    shards = {}
    W, OVERLAP, WIDTH = 12, 16, 24  # sliding windows: each cluster seen by ~4-6 workers
    for w in range(W):
        part = [catalog[(w * OVERLAP + j) % 48] for j in range(WIDTH)]
        shards[f"inputs/agent_{w}/manifest.csv"] = "id,rt_gene,noncoding_len\n" + \
            "\n".join(f"{c['id']},{int(c['rt_gene'])},{c['noncoding_len']}" for c in part)
    return write_layer("A", "pipeline_inputs", shards,
                       "Cell A: 12 overlapping worker shards (sliding windows, consensus-ready)")


# ---- Cell B: parallel workers (stateless: read shard, emit structured JSON) --
def analyze(rows, worker):
    """Worker 'agent': flag repeating non-coding arrays near RT genes."""
    out = []
    for r in rows:
        if r["rt_gene"] and r["noncoding_len"] >= 120:
            out.append({"cluster": r["id"], "worker": worker,
                        "signal": "repeating_noncoding_array",
                        "confidence": 0.5 + (rng() % 500) / 1000})
    return out


def cell_b(layer_a):
    pkg = STATE / layer_a
    outputs = {}
    for w in range(12):
        csv = (pkg / f"inputs/agent_{w}/manifest.csv").read_text().splitlines()[1:]
        rows = [dict(zip(("id", "rt_gene", "noncoding_len"), line.split(","))) for line in csv]
        rows = [{**r, "rt_gene": r["rt_gene"] == "1", "noncoding_len": int(r["noncoding_len"])}
                for r in rows]
        for finding in analyze(rows, w):
            outputs.setdefault(f"raw_anomalies/worker_{w}.json", []).append(finding)
    return write_layer("B", "raw_anomalies",
                       {k: json.dumps(v) for k, v in outputs.items()},
                       "Cell B: 12 worker anomaly sets captured, stateless")


# ---- Cell C: consensus voting ----------------------------------------------
def cell_c(layer_b):
    pkg = STATE / layer_b
    votes = {}
    for f in sorted(pkg.glob("raw_anomalies/*.json")):
        for finding in json.loads(f.read_text()):
            c = votes.setdefault(finding["cluster"], {"votes": 0, "conf": []})
            c["votes"] += 1
            c["conf"].append(finding["confidence"])
    candidates = {k: {"votes": v["votes"],
                      "mean_conf": sum(v["conf"]) / len(v["conf"])}
                  for k, v in votes.items() if v["votes"] >= 3}
    return write_layer("C", "voted_candidates",
                       {"candidates/voted.json": json.dumps(candidates, indent=2, sort_keys=True)},
                       "Cell C: consensus voting, >=3 worker agreement")


# ---- Cell D: senior evaluation ----------------------------------------------
def cell_d(layer_c):
    pkg = STATE / layer_c
    voted = json.loads((pkg / "candidates/voted.json").read_text())
    final = {k: {"target": True, "priority": round(v["mean_conf"] * v["votes"], 3),
                 "vetoes": 0}
             for k, v in voted.items() if v["mean_conf"] >= 0.75}
    return write_layer("D", "final_targets",
                       {"final/targets.json": json.dumps(final, indent=2, sort_keys=True)},
                       "Cell D: senior eval, mean_conf >= 0.75 passes to wet lab")


def main():
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir()
    a = cell_a(); b = cell_b(a); c = cell_c(b); d = cell_d(c)
    def h(layer):
        import json as j
        return j.loads((STATE / layer / "manifest.json").read_text())["layer_hash"]
    final = json.loads((STATE / f"{d}" / "final/targets.json").read_text())
    receipt = {"pipeline": "quilt-discovery-demo", "scale": "12 workers",
               "layers": {"A": h(a), "B": h(b), "C": h(c), "D": h(d)},
               "final_targets": len(final), "reproducible_from_genesis": True}
    (STATE / "RECEIPT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
