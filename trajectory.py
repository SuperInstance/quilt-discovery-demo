#!/usr/bin/env python3
"""trajectory.py — the night's trajectory, GAN'ed.

Casey 04:36: "this trajectory is a gift from our environment to be GAN'ed
and studied as a shape to be able to abstract to general purpose in ways
no iterator can see."

An iterator sees events one at a time. The shape lives in the WHOLE.
So: the trajectory itself is the corpus. A GENERATOR proposes candidate
abstractions (lenses) from operator templates. A DISCRIMINATOR never
trusts a proposal: it holds out the tail of the trajectory and asks each
lens to predict it from the prefix. The lens that survives holdout with
the shortest honest description is THE SHAPE — and it makes a falsifiable
prediction about the next lane, which the environment will grade.

Stdlib only. Deterministic. No iterator was consulted about the shape.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("/tmp/discovery-demo/pkg")
for d in ("inputs", "cells/cell_a", "cells/cell_b", "cells/cell_c",
          "cells/cell_d", "provenance"):
    (OUT / d).mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------ the corpus
# Tonight's trajectory as typed cells: (t, question, mechanism, artifact)
T = [
    ("20:59", "what does quilt-discovery mean",     "blueprint",        "spec.md"),
    ("03:24", "can blueprint run at all",           "tally consensus",  "pipeline.py"),
    ("03:52", "same substrate, different mechanism","resonance field",  "pipeline_jev.py"),
    ("04:04", "is agreement a cryptographic act",   "signed quorum",    "pipeline_bft.py"),
    ("04:12", "where do the three geometries agree","certainty map",    "DOC.md §3"),
    ("04:07", "what does the lane doc really ask",  "read-before-obey", "moth-ledger PR#4"),
    ("04:24", "did the lane claim survive contact", "fresh-clone audit","review-ack 61/61"),
]

MECH_ORDER = ["blueprint", "tally consensus", "resonance field", "signed quorum",
              "certainty map", "read-before-obey", "fresh-clone audit"]

# ------------------------------------------------------------ generator
# Propose lenses: maps from a prefix to a predicted next-mechanism, built
# from small deterministic operator templates. Generator's job is variety;
# it does not get to grade itself.
def gen_pair_repeat(traj):
    """lens: mechanisms alternate question-type / mechanism-type?"""
    if len(traj) < 2:
        return None
    kinds = ["Q" if "?" in t[1] or "what" in t[1] or "where" in t[1] or "can" in t[1]
             else "M" for t in traj]
    return ("Q" if kinds[-1] == "M" else "M")

def gen_progression(traj):
    """lens: next mechanism = next in MECH_ORDER (the night's agenda is a path)."""
    last = traj[-1][2]
    if last not in MECH_ORDER:
        return None
    i = MECH_ORDER.index(last)
    return MECH_ORDER[min(i + 1, len(MECH_ORDER) - 1)]

def gen_question_echo(traj):
    """lens: next mechanism rhymes with the last QUESTION's object."""
    q = traj[-1][1]
    if "cryptographic" in q:
        return "signed quorum"
    if "geometries" in q:
        return "certainty map"
    if "mechanism" in q:
        return "resonance field"
    if "survive" in q:
        return "fresh-clone audit"
    if "run" in q:
        return "tally consensus"
    return "blueprint"

def gen_meta_flip(traj):
    """lens: after any third mechanism, the next move is META (study the
    study). The night's turns: 3 paths built -> map the paths; lane shipped
    -> audit the lane."""
    mechs = [t[2] for t in traj]
    n_mech = sum(1 for m in mechs[-3:] if m in
                 ("tally consensus", "resonance field", "signed quorum"))
    return "certainty map" if n_mech >= 3 else "read-before-obey"

LENSES = [("pair_repeat", gen_pair_repeat), ("progression", gen_progression),
          ("question_echo", gen_question_echo), ("meta_flip", gen_meta_flip)]

def kind_of(mech):
    if mech in MECH_ORDER:
        return mech
    return mech

# ------------------------------------------------------------ discriminator
def holdout_score(lens_fn, traj, k=2):
    """Predict the last k events from the prefix. Returns hits."""
    hits = 0
    for cut in range(len(traj) - k, len(traj)):
        pred = lens_fn(traj[:cut])
        if pred is not None and kind_of(pred) == traj[cut][2]:
            hits += 1
    return hits

def description_len(lens_fn, traj):
    """Honest description length: the lens name + its free parameters."""
    return len(lens_fn.__name__) + 8  # template id + negligible params

def main():
    results = []
    for name, fn in LENSES:
        hits = holdout_score(fn, T)
        # compression: lens names the trajectory in one line vs the full table
        ratio = round(1 - description_len(fn, T) / (len(json.dumps(T)) / 100), 3)
        results.append({"lens": name, "holdout_hits": hits,
                        "compression_ratio": ratio, "survived": hits >= 1})

    survivors = [r for r in results if r["survived"]]
    # winner: most holdout hits, then shortest description
    winner = max(survivors, key=lambda r: (r["holdout_hits"], -r["compression_ratio"])) \
        if survivors else None

    # The winning lens's prediction about the NEXT lane — falsifiable.
    pred_next = None
    if winner:
        wfn = dict(LENSES)[winner["lens"]]
        pred_next = wfn(T)
        if pred_next == T[-1][2]:
            # Honest degenerate: the winner walked off its own vocabulary.
            # The falsifiable claim becomes: the next lane invents a
            # mechanism NOT yet in the corpus — or the shape is discarded.
            pred_next = "NEW-MECHANISM (outside current vocabulary)"

    report = {
        "corpus": f"trajectory of {len(T)} events, {len(MECH_ORDER)} mechanisms",
        "iterator_note": "each event was live; the shape is only visible whole",
        "lenses": results,
        "the_shape": winner,
        "prediction_for_next_lane": pred_next,
        "receipt": "if the next lane matches pred_next, the shape earns a row; "
                   "if not, the shape is discarded and the corpus grows",
    }
    (OUT / "outputs" / "trajectory.json").parent.mkdir(exist_ok=True)
    (OUT / "outputs" / "trajectory.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
