#!/usr/bin/env python3
"""pipeline_jev.py — the discovery pipeline via Moth workers + interference consensus + JEV eval.

GAN pair to pipeline.py (the Claude-shaped path). Every layer makes a DIFFERENT choice,
so the negative space between the two runs is the shape of the vessel:

  layer        pipeline.py (claude-shaped)   pipeline_jev.py (this file)
  Cell B       stateless workers, JSON out   Moth-cells: findings are phase-writes
                                               into a shared interference field
  Cell C       vote-counting (>=3 agreement)  RESONANCE: aligned phases interfere
                                               constructively; consensus is emergent
  Cell D       senior eval, conf threshold    JEV typed lanes: PASS rows typed
                                               into final_targets; unusable input
                                               -> REFUSED row (raw receipt kept)
  state        hash-manifested dirs           same receipts discipline (substrate-
                                               independent), field states hashed

Cheap: all local, deterministic, stdlib. Vendor substrates (real Moth, live JEV)
enter by measurement only, per the 09-24 lane doctrine.

Run: python3 pipeline_jev.py    (receipts in state-jev/)
"""
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent
STATE = ROOT / "state-jev"
rng_state = 0x0DDF


def rng():
    global rng_state
    rng_state = (rng_state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    return rng_state >> 33


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_layer(cell, name, files, lineage):
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
    return layer.name


# ---- Cell A: same shard geometry (shared substrate, so divergence starts at B)
def cell_a():
    catalog = [{"id": f"cluster_{i}", "rt_gene": (i % 5 == 0),
                "noncoding_len": 40 + (i * 37) % 220} for i in range(48)]
    shards = {}
    for w in range(12):
        part = [catalog[(w * 16 + j) % 48] for j in range(24)]
        shards[f"inputs/agent_{w}/manifest.csv"] = "id,rt_gene,noncoding_len\n" + \
            "\n".join(f"{c['id']},{int(c['rt_gene'])},{c['noncoding_len']}" for c in part)
    return write_layer("A", "pipeline_inputs", shards,
                       "Cell A: identical shard geometry to pipeline.py (shared substrate)")


# ---- Cell B: Moth-cells. A finding is not a JSON record; it is a phase-write into
# a shared interference field. Each worker carries a phase signature (its id); the
# field accumulates signed integer amplitudes (Q16 mindset: exact, hashable).
GRID = 16


def cell_b(layer_a):
    pkg = STATE / layer_a
    field = [[0] * GRID for _ in range(GRID)]
    for w in range(12):
        lines = (pkg / f"inputs/agent_{w}/manifest.csv").read_text().splitlines()[1:]
        for line in lines:
            cid, rt, ncl = line.split(",")
            if rt == "1" and int(ncl) >= 120:
                idx = int(cid.split("_")[1])
                x, y = idx % GRID, (idx // GRID) % GRID
                strength = 2 + (rng() % 3)             # exact integer, never float
                phase = 1 if rng() % 3 else -1         # confidence direction: aligned
                field[y][x] += phase * strength        # sightings AGREE (not just co-occur)
    rows = [" ".join(f"{v:+d}" for v in row) for row in field]
    return write_layer("B", "moth_field", {"field/moth.txt": "\n".join(rows)},
                       "Cell B: 12 moth-cells; findings are phase-writes, not records")


# ---- Cell C: consensus by resonance. Aligned phases stack; the field's abs()
# amplitude at a cluster coordinate IS the agreement count, no voter exists.
def cell_c(layer_b):
    pkg = STATE / layer_b
    field = [[int(v) for v in line.split()] for line in
             (pkg / "field/moth.txt").read_text().splitlines()]
    resonant = {}
    for y in range(GRID):
        for x in range(GRID):
            a = field[y][x]
            idx = y * GRID + x
            if idx < 48 and abs(a) >= 3:               # resonance threshold = agreement
                resonant[f"cluster_{idx}"] = {
                    "amplitude": a,
                    "sightings": abs(a) // 2,          # ~2 energy units per sighting
                    "polarity": "aligned" if a > 0 else "contested"}
    return write_layer("C", "resonance_lines",
                       {"candidates/resonant.json": json.dumps(resonant, indent=2, sort_keys=True)},
                       "Cell C: consensus is emergent interference, not vote-counting")


# ---- Cell D: JEV typed evaluation. PASS -> typed into final_targets.
# The jeviter#14 lesson is structural here: input without usable receipts gets a
# REFUSED row with the raw artifact kept — never a fabricated score.
def cell_d(layer_c):
    pkg = STATE / layer_c
    resonant = json.loads((pkg / "candidates/resonant.json").read_text())
    lanes, refusals = {}, []
    for cid, r in sorted(resonant.items()):
        if r["polarity"] == "contested":
            refusals.append({"cluster": cid, "reason": "CONTESTED_POLARITY",
                             "raw": r})               # raw receipt kept, no score
        elif r["sightings"] < 2:
            refusals.append({"cluster": cid, "reason": "INSUFFICIENT_SIGHTINGS",
                             "raw": r})
        else:
            lanes[cid] = {"lane": "PASS", "priority": r["amplitude"],
                          "typed_by": "jev", "rule": "aligned && sightings>=2"}
    return write_layer("D", "final_targets",
                       {"final/targets.json": json.dumps(lanes, indent=2, sort_keys=True),
                        "jev/refused.json": json.dumps(refusals, indent=2, sort_keys=True)},
                       "Cell D: JEV typed lanes; REFUSED rows keep raw receipts (jeviter#14 law)")


def main():
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir()
    a = cell_a(); b = cell_b(a); c = cell_c(b); d = cell_d(c)
    targets = json.loads((STATE / d / "final/targets.json").read_text())
    refused = json.loads((STATE / d / "jev/refused.json").read_text())

    def h(layer):
        return json.loads((STATE / layer / "manifest.json").read_text())["layer_hash"]
    receipt = {"pipeline": "quilt-discovery-jev", "gan_pair": "pipeline.py",
               "layers": {"A": h(a), "B": h(b), "C": h(c), "D": h(d)},
               "final_targets": len(targets), "refused": len(refused),
               "mechanism": "interference-consensus + typed-jev-lanes"}
    (STATE / "RECEIPT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
