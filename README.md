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

## Production practices carried over (blueprint §Best Practices)

1. **Lineage tracking** — every manifest carries a `lineage` note (the cell's commit message).
2. **Immutable replay loops** — every intermediate layer is a snapshotted, hashed directory.
3. **Data/code decoupling** — agent logic in this file; all evolving state in `state/` layers.

Blueprint: `recreate_pipeline_quilt.md`. Fleet doctrine: cellularized demo — this repo stands alone.
Featured on the PurplePincher supersite.
