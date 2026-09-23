#!/usr/bin/env python3
"""pipeline_bft.py — third GAN path: quorum-certificate consensus (PBFT-shaped).

Same Cell A (byte-identical substrate), different agreement operator:
  Cell B  workers emit SIGNED votes (sig = sha256(worker_key || finding_hash))
  Cell C  quorum certificate: a cluster passes iff >= 2f+1 matching signed votes
          from n=12 workers (f=3 Byzantine tolerated). Workers {3,7,11} are
          Byzantine: they vote with flipped confidence, deterministically.
  Cell D  equivocation check: two conflicting quorums for one cluster -> FAULT row;
          otherwise typed PASS. Fault-tolerance is the mechanism, not noise.

GAN vertex: is agreement a FIELD PROPERTY (moth path), a TALLY (claude path),
or a CRYPTOGRAPHIC ACHIEVEMENT (this path)? Third vertex triangulates the vessel.

Run: python3 pipeline_bft.py    (receipts in state-bft/)
"""
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent
STATE = ROOT / "state-bft"
rng_state = 0xB17


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


def sign(worker, payload):
    key = sha(f"worker-{worker}-key".encode())
    return sha((key + payload).encode())[:16]


def cell_a():
    catalog = [{"id": f"cluster_{i}", "rt_gene": (i % 5 == 0),
                "noncoding_len": 40 + (i * 37) % 220} for i in range(48)]
    shards = {}
    for w in range(12):
        part = [catalog[(w * 16 + j) % 48] for j in range(24)]
        shards[f"inputs/agent_{w}/manifest.csv"] = "id,rt_gene,noncoding_len\n" + \
            "\n".join(f"{c['id']},{int(c['rt_gene'])},{c['noncoding_len']}" for c in part)
    return write_layer("A", "pipeline_inputs", shards,
                       "Cell A: identical shard geometry (shared substrate, 3rd path)")


BYZANTINE = {3, 7, 11}
N, F = 12, 3
QUORUM = 2 * F + 1  # 7


def cell_b(layer_a):
    pkg = STATE / layer_a
    votes = {}
    for w in range(N):
        lines = (pkg / f"inputs/agent_{w}/manifest.csv").read_text().splitlines()[1:]
        for line in lines:
            cid, rt, ncl = line.split(",")
            if rt == "1" and int(ncl) >= 120:
                conf = 0.5 + (rng() % 500) / 1000
                if w in BYZANTINE:
                    conf = round(1.0 - conf, 3)        # faulty workers flip confidence
                ballot = {"cluster": cid, "confidence": conf, "verdict": "SUPPORT"}
                payload = json.dumps(ballot, sort_keys=True)
                votes.setdefault(cid, []).append(
                    {"worker": w, "ballot": ballot, "sig": sign(w, payload),
                     "byzantine": w in BYZANTINE})
    return write_layer("B", "signed_votes",
                       {"votes/" + cid + ".json": json.dumps(v, indent=2, sort_keys=True)
                        for cid, v in sorted(votes.items())},
                       "Cell B: signed ballots; workers 3,7,11 Byzantine (conf flipped)")


def cell_c(layer_b):
    pkg = STATE / layer_b
    # Committee tier (blueprint-accurate): 12 seats read ALL worker reports and cast
    # signed ballots per candidate; seats 3,7,11 are Byzantine (flip their ballot).
    # A cluster is certified iff >= 2f+1 = 7 seats sign matching SUPPORT ballots.
    report = {}
    for f in sorted((pkg / "votes").glob("*.json")):
        cid = f.stem
        votes = json.loads(f.read_text())
        for v in votes:  # verify every worker signature first
            payload = json.dumps(v["ballot"], sort_keys=True)
            if sign(v["worker"], payload) == v["sig"]:
                report.setdefault(cid, []).append(v["ballot"]["confidence"])
    ballots = {}
    for cid, confs in sorted(report.items()):
        ordered = sorted(confs)
        mid = len(ordered) // 2
        median = (ordered[mid] if len(ordered) % 2
                else (ordered[mid - 1] + ordered[mid]) / 2)
        support = median >= 0.70  # median rule: Byzantine conf-flips (<=1/3) cannot move it
        for seat in range(N):
            verdict = support
            if seat in BYZANTINE:
                verdict = not support
            payload = json.dumps({"cluster": cid, "verdict": "SUPPORT" if verdict else "REJECT"},
                                 sort_keys=True)
            ballots.setdefault(cid, []).append(
                {"seat": seat, "verdict": "SUPPORT" if verdict else "REJECT",
                 "sig": sign(f"seat-{seat}", payload), "byzantine": seat in BYZANTINE})
    certs, faults = {}, []
    for cid, bs in sorted(ballots.items()):
        seen = {}
        for b in bs:  # equivocation = one seat, two different signed ballots
            if b["seat"] in seen and seen[b["seat"]] != b["verdict"]:
                faults.append({"cluster": cid, "reason": "EQUIVOCATION", "seat": b["seat"]})
            seen[b["seat"]] = b["verdict"]
        support_sigs = [b["sig"] for b in bs if b["verdict"] == "SUPPORT"]
        if len(support_sigs) >= QUORUM:
            honest = [b for b in bs if b["verdict"] == "SUPPORT" and not b["byzantine"]]
            certs[cid] = {"quorum": len(support_sigs), "certificate": support_sigs,
                          "honest_of_quorum": f"{len(honest)}/{len(support_sigs)}"}
    files = {"candidates/certified.json": json.dumps(certs, indent=2, sort_keys=True)}
    if faults:
        files["candidates/equivocations.json"] = json.dumps(faults, indent=2, sort_keys=True)
    return write_layer("C", "quorum_certificates", files,
                       f"Cell C: committee quorum={QUORUM}/{N} (f={F}); sigs verified; equivocation->FAULT")


def cell_d(layer_c):
    pkg = STATE / layer_c
    certs = json.loads((pkg / "candidates/certified.json").read_text())
    faults = json.loads((pkg / "candidates/equivocations.json").read_text()) \
        if (pkg / "candidates/equivocations.json").exists() else []
    lanes = {cid: {"lane": "PASS", "quorum_votes": c["quorum"],
                   "certificate_size": len(c["certificate"]),
                   "honest_of_quorum": c["honest_of_quorum"], "typed_by": "bft-senior"}
             for cid, c in sorted(certs.items())}
    return write_layer("D", "final_targets",
                       {"final/targets.json": json.dumps(lanes, indent=2, sort_keys=True),
                        "bft/faults.json": json.dumps(faults, indent=2, sort_keys=True)},
                       "Cell D: certified targets + equivocation FAULT rows preserved")


def main():
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir()
    a = cell_a(); b = cell_b(a); c = cell_c(b); d = cell_d(c)
    targets = json.loads((STATE / d / "final/targets.json").read_text())
    faults = json.loads((STATE / d / "bft/faults.json").read_text())

    def h(layer):
        return json.loads((STATE / layer / "manifest.json").read_text())["layer_hash"]
    receipt = {"pipeline": "quilt-discovery-bft", "gan_paths": ["pipeline.py", "pipeline_jev.py"],
               "layers": {"A": h(a), "B": h(b), "C": h(c), "D": h(d)},
               "final_targets": len(targets), "equivocation_faults": len(faults),
               "mechanism": "quorum-certificate (2f+1 of 12, f=3 Byzantine) + sig-verify"}
    (STATE / "RECEIPT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
