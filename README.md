# quilt-discovery-demo

**Anthropic's 949-agent genetic-discovery pipeline, recreated in Quilt — as a live, deterministic, receipted demo.**

The original succeeded by avoiding conversational context-passing: a *stateless assembly line* where
every agent tier reads inputs from and writes outputs to a structured, shared state layer. This demo
reproduces that architecture at honest scale (12 workers) with the fleet's receipts discipline:
between every cell sits an **immutable, hash-manifested state layer**, replayable from genesis,
where nothing is trusted that isn't hashed.

```
[ genome catalog ] → (Layer A: pipeline_inputs)   → Cell A: sharding (overlapping windows)
                   → (Layer B: raw_anomalies)    → Cell B: 12 stateless workers
                   → (Layer C: voted_candidates) → Cell C: consensus voting (≥3 agreement)
                   → (Layer D: final_targets)    → Cell D: senior eval (mean_conf ≥ 0.75)
                   → RECEIPT.json
```

## Run it

```bash
python3 pipeline.py    # stdlib only; receipts land in state/
```

## Verified

- **Deterministic replay:** two independent runs produce byte-identical receipts
  (sha256 of stdout `ab86c231…` both times). Layer hashes A–D are content-derived;
  the pipeline is reproducible from genesis, not from snapshots.
- **Consensus works because sharding overlaps:** sliding-window shards give each cluster
  4–6 worker sightings; disjoint shards would make voting structurally impossible
  (self-caught: first version returned 0 targets — a real design defect, receipted here).
- **Final output:** 4 targets pass senior evaluation.

## The GAN pair (Casey, 03:52: instead of Claude — our systems, cheaply)

**`pipeline_jev.py`** runs the same four cells through Moth workers and JEV lanes:
findings are *phase-writes* into a shared interference field (Cell B), consensus is *emergent
resonance* — no voter exists (Cell C), and evaluation emits typed JEV lanes with **REFUSED rows
keeping raw receipts** instead of fabricated scores (Cell D; the jeviter#14 law made structural).
Cell A is byte-identical to the claude path (same layer hash `9a3c4856…`) so every downstream
difference is attributable to mechanism. Deterministic: receipt `c20f67a2…` across runs.

**The paths disagree on the frontier — that disagreement is the finding:**
claude-path targets {15,20,35,40} vs jev-path {10,15,20,35,45}; cluster_5 (6 sightings, amplitude −13)
got **REFUSED: CONTESTED_POLARITY** — workers saw the same thing and judged it oppositely, a fact
vote-counting destroys by tallying. Idea log (documented as built, per standing order): **DOC.md**.

## Production practices carried over (blueprint §Best Practices)

1. **Lineage tracking** — every manifest carries a `lineage` note (the cell's commit message).
2. **Immutable replay loops** — every intermediate layer is a snapshotted, hashed directory.
3. **Data/code decoupling** — agent logic in this file; all evolving state in `state/` layers.

Blueprint: `recreate_pipeline_quilt.md`. Fleet doctrine: cellularized demo — this repo stands alone.
Featured on the PurplePincher supersite.
