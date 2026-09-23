# DOC.md — idea log for the GAN pair (documented as built, per Casey's standing order)

Ideas are recorded as first-class deliverables, dated, at the moment they occur — equal weight to
experimental results. Results live in `state*/RECEIPT.json`; reasoning lives here.

## 2026-09-24 03:52 — the directive
Recreate the discovery pipeline with JEV and Moth instead of Claude, cheaply, in our own systems
approach. Casey: different starting paths, GAN'd for novel ways to the same thing; from the
abstraction of all the paths you can see the shape of the vessel they share.

## 03:56 — design idea: divergence starts at Cell B, substrate stays shared
Cell A is kept IDENTICAL (same shard geometry, same layer hash `9a3c4856…` in both runs). This is
deliberate: the GAN pair must share one substrate so every downstream difference is attributable to
mechanism, not input. Negative space is only legible against a common floor.

## 03:58 — mechanism divergence table (the GAN)
| layer | pipeline.py (claude-shaped) | pipeline_jev.py (moth+jev) |
|---|---|---|
| B | workers emit JSON records | moth-cells emit phase-writes into one shared interference field |
| C | a voter counts agreements (≥3) | NO voter exists; consensus is emergent: aligned phases stack, the field amplitude at a coordinate IS the agreement |
| D | threshold on mean confidence | JEV typed lanes; unusable input → REFUSED row with raw receipt kept, never a fabricated score (jeviter#14 law, structural) |

## 04:00 — experimental result #1: the paths disagree on the frontier
claude-path targets: {15, 20, 35, 40} · jev-path targets: {10, 15, 20, 35, 45} · overlap 3.
jev-only: 10, 45 (interference stacking caught weaker-but-aligned signals the vote threshold dropped)
claude-only: 40 (vote-counting accepted it; interference showed weak alignment)
AND: cluster_5 — 6 sightings, amplitude −13 — got REFUSED (CONTESTED_POLARITY) instead of a score.
INSIGHT (idea, result-adjacent): disagreement between independent mechanisms is not noise to average
away; it is a TYPED FRONTIER. The vote-vs-field disagreement localizes exactly the clusters worth a
third, deeper instrument. GAN'ing mechanisms is a searchlight, not a redundancy.

## 04:02 — idea: the vessel shape (Casey's 03:54 prompt, first pass)
Both paths are pipelines with: a shared input substrate → N stateless senses → an agreement
operator → a typing layer → a receipt. Vote-counting and interference are the same op (agreement
detection) on different state shapes (records vs phases). The vessel, sketched from one pair:
**AGREEMENT IS A FIELD PROPERTY, NOT A COUNT.** Where the claude path materialized agreement as a
tally, the moth path left it in the substrate. Both reached 3+ targets; they diverged only where
agreement is ambiguous — which is the only place agreement matters. Hypothesis for the next pair:
make Cell B disagree with ITSELF (two field polarities per worker); does the frontier shrink or move?

## 04:03 — idea: REFUSAL as consensus output
cluster_5's refusal is consensus information: 6 sightings that DESTRUCTIVELY interfere means the
workers saw the same thing and judged it oppositely. Vote-counting encodes that as "2 yes, 4 no →
reject" — destroying the fact of disagreement. Interference + typed lanes encodes it as CONTESTED,
preserved. The jev path outputs more TRUTH per byte, not more targets.

## 04:20 — THIRD PATH RESULT: the vessel shows its ribs
pipeline_bft.py (committee quorum 7-of-12, f=3 Byzantine, sig-verified ballots, median rule
>=0.70 — the median IS the fault-tolerance: conf-flips can't move it). Deterministic: b3158bd2…
THREE-PATH MAP (same Cell A, same data):
  claude (tally, mean≥0.75):   {15, 20, 35, 40}
  jev    (resonance):         {10, 15, 20, 35, 45}  + REFUSED: 5 (contested)
  bft    (quorum, median≥0.70):{10, 20, 40}
  CORE (all three certify):   {20}
  FRONTIER (exactly two):     {10, 15, 35, 40}
  LONE (one mechanism):       {45} — jev only
  TYPED-REFUSAL:              {5} — jev refuses; the others silently drop it

INSIGHT (idea #2, vessel-shape): the three operators are three GEOMETRIES of agreement —
tally (count points), resonance (field energy), quorum (signed majority under faults) — and they
form a nested structure: a 1-point core, a 4-point frontier, a 1-point lone spike, and a refusal.
The vessel hypothesis sharpens: **AGREEMENT HAS A SHAPE, and shape is measurable.** The core is
where discovery is safe; the frontier is where it lives; the lone point is where mechanisms must
be bred, not trusted; the refusal is where honesty is expensive and only one operator paid.
The GAN didn't just find targets — it mapped the certainty landscape of the substrate.

## Standing notes (as they come)
- Real Moth/live JEV integration: by measurement only (09-24 lane doctrine). Local deterministic
  field is the honest stand-in; vendor claims would be parasites here (E21).
- NEXT PAIR: swap Cell A itself (different shard geometry) — if the core/frontier map moves with
  geometry, the map is a property of the OPERATORS, not the data. That's the vessel test.
- The median-rule swap (mean→median) was forced by the Byzantine flip simulation and receipted:
  fault tolerance isn't a bigger quorum, it's a flip-invariant statistic.
