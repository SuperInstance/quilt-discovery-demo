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

## The GAN trio (Casey, 03:52 + 04:04: instead of Claude — our systems, cheaply)

Three paths, one shared substrate (Cell A identical in all — layer hash `9a3c4856…` — so every
difference is mechanism):

| path | Cell B emits | consensus operator | targets |
|---|---|---|---|
| `pipeline.py` (claude-shaped) | JSON records | vote tally, mean ≥ 0.75 | {15, 20, 35, 40} |
| `pipeline_jev.py` (moth+jev) | phase-writes into one interference field | emergent resonance, no voter | {10, 15, 20, 35, 45} + REFUSED 5 |
| `pipeline_bft.py` (quorum) | signed ballots | 7-of-12 committee, f=3 Byzantine, median ≥ 0.70 | {10, 20, 40} |

**The certainty map:** core {20} (all three) · frontier {10, 15, 35, 40} (exactly two) ·
lone {45} (jev only) · typed refusal {5} (jev refuses where others silently drop).
All deterministic; receipts: claude `ab86c231…`, jev `c20f67a2…`, bft `b3158bd2…` (byte-identical
across independent runs). Idea log (documented as built, per standing order): **DOC.md**.

Key receipts-caught defects (design lessons, kept honest): disjoint shards make consensus
impossible (fixed: sliding-window overlap); tally-quorum with mean fails under Byzantine flips
(fixed: median — fault tolerance is a flip-invariant statistic, not a bigger quorum).

## Production practices carried over (blueprint §Best Practices)

1. **Lineage tracking** — every manifest carries a `lineage` note (the cell's commit message).
2. **Immutable replay loops** — every intermediate layer is a snapshotted, hashed directory.
3. **Data/code decoupling** — agent logic in this file; all evolving state in `state/` layers.

Blueprint: `recreate_pipeline_quilt.md`. Fleet doctrine: cellularized demo — this repo stands alone.
Featured on the PurplePincher supersite.
