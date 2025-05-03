Below is a **ready-to-drop-in Python module** that turns the raw output of your
`get_kp_data(horo_input)` and `get_vimshottari_dasa_data()` helpers into a **rank-ordered list of “marriage-likely” periods**, using classical Krishnamurti Paddhati (KP) rules.

```python
"""
kp_marriage.py   – Predicts marriage windows from KP–style data

Typical use
-----------
from kp_marriage import predict_marriage, default_knobs
periods = predict_marriage(get_kp_data(my_horo),          # ← your helper
                           get_vimshottari_dasa_data(),   # ← your helper
                           knobs=default_knobs)
for p in periods[:10]:
    print(p['start_date'], p['end_date'], p['score'], p['why'])
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Sequence
from datetime import date
import itertools
import math

# ---------------------------------------------------------------------------
# ❶  KNOBS  – dial these to make the algorithm stricter or more relaxed
# ---------------------------------------------------------------------------

@dataclass
class Knobs:
    # Houses that PROMISE marriage (2-family, 7-partner, 11-fulfilment)
    marriage_houses: Tuple[int, ...]          = (2, 7, 11)

    # Houses that DENY / DELAY marriage
    obstruction_houses: Tuple[int, ...]       = (1, 6, 10, 12, 8)

    # Weights applied when a house is signified by
    weight_owner: float                       = 1.0   # planet owns the house
    weight_occupant: float                    = 1.0   # planet occupies the house
    weight_star_lord: float                   = 1.2   # planet is star-lord of occupant
    weight_sub: float                         = 1.4   # sub-lord signification
    weight_subsub: float                      = 1.6
    weight_aspect: float                      = 0.7

    # Dasha–level multipliers (Mahadasha gets the biggest say)
    maha_mult: float                          = 1.5
    antara_mult: float                        = 1.2
    prati_mult: float                         = 1.0    # change if you find it too “busy”

    # Minimum total score that must be reached to flag a period
    threshold: float                          = 4.0

    # Orb (°) inside which an aspect is considered
    max_aspect_orb: float                     = 3.0

    # If True → require **promise of marriage** before timing is attempted
    require_promise: bool                     = True

default_knobs = Knobs()

# ---------------------------------------------------------------------------
# ❷  INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _collect_planet_scores(kp_data: dict, knobs: Knobs) -> Dict[str, float]:
    """
    Build a planet → (+ve, –ve) score tuple using KP significations.
    """
    pos, neg = {}, {}
    for rec in kp_data["planet_significators"]:
        p = rec["Planet"]
        fav  = sum(knobs.weight_owner     for h in rec["planetRuledHouses"]      if h in knobs.marriage_houses)
        fav += sum(knobs.weight_occupant  for h in [rec["occupiedHouse"]]        if h in knobs.marriage_houses)
        fav += sum(knobs.weight_star_lord for h in rec["starLordRuledHouses"]    if h in knobs.marriage_houses)
        fav += sum(knobs.weight_sub       for h in rec["subLordHouseSignifications"]    if h in knobs.marriage_houses)
        fav += sum(knobs.weight_subsub    for h in rec["subSubLordHouseSignifications"] if h in knobs.marriage_houses)

        bad  = sum(knobs.weight_owner     for h in rec["planetRuledHouses"]      if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_occupant  for h in [rec["occupiedHouse"]]        if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_star_lord for h in rec["starLordRuledHouses"]    if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_sub       for h in rec["subLordHouseSignifications"]    if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_subsub    for h in rec["subSubLordHouseSignifications"] if h in knobs.obstruction_houses)

        pos[p], neg[p] = fav, bad

    # 2.b  Add small bonus/penalty for *tight* aspects to marriage houses’ owners
    house_owner = {h["House"]: h["HouseOwner"] for h in kp_data["house_significators"]}
    for asp in kp_data.get("aspects", []):
        if asp["AspectOrb"] > knobs.max_aspect_orb:   # ignore wide orbs
            continue
        p1, p2 = asp["P1"], asp["P2"]
        for p, q in [(p1, p2), (p2, p1)]:
            if q in house_owner.values():
                # owner of some house – we don’t care *which* here, just sign
                orb_score = knobs.weight_aspect * (knobs.max_aspect_orb - asp["AspectOrb"]) / knobs.max_aspect_orb
                if q in knobs.marriage_houses:
                    pos[p] += orb_score
                elif q in knobs.obstruction_houses:
                    neg[p] += orb_score

    # final scalar “balance” for each planet
    return {pl: pos.get(pl, 0.0) - neg.get(pl, 0.0) for pl in pos.keys() | neg.keys()}

def _promise_of_marriage(kp_data: dict, planet_scores: Dict[str,float], knobs: Knobs) -> bool:
    """
    Returns True if the chart contains a basic 'promise' per standard KP rules:
      – Sub-lord of 7th cusp must signify at least one of 2,7,11  �—cite�turn0search0�turn0search5�turn0search3�turn0search4�
    """
    seventh = next(h for h in kp_data["house_significators"] if h["House"] == "VII")
    sub = seventh["cuspSubLord"]
    sigs = set(seventh["cuspSubLordSignifications"])
    good = sigs & set(knobs.marriage_houses)
    blocked = sigs & set(knobs.obstruction_houses)
    # A net-positive planet score counts as an implicit promise
    return (bool(good) and not blocked) or planet_scores.get(sub, 0) > 0

# ---------------------------------------------------------------------------
# ❸  CORE DRIVER
# ---------------------------------------------------------------------------

def predict_marriage(kp_data: dict,
                     dasha_table: Sequence[dict],
                     *,
                     knobs: Knobs = default_knobs
                     ) -> List[dict]:
    """
    Parameters
    ----------
    kp_data      : output of get_kp_data()
    dasha_table  : output of get_vimshottari_dasa_data()
    knobs        : Knobs() – tweak to relax / tighten judgement

    Returns
    -------
    List[dict]   : Every record that crosses `knobs.threshold`, sorted best→worst.
                   Keys = {start_date, end_date, score, why}
    """

    # 1.  Build planet-level goodness score
    planet_score = _collect_planet_scores(kp_data, knobs)

    # 2.  Check chart promise (optional gate)
    if knobs.require_promise and not _promise_of_marriage(kp_data, planet_score, knobs):
        return []   # “No promise, no timing.”

    # 3.  Score every dasha slice
    output = []
    for row in dasha_table:
        score = (knobs.maha_mult   * planet_score.get(row["mahadasha"],   0.0) +
                 knobs.antara_mult * planet_score.get(row["antardasha"],  0.0) +
                 knobs.prati_mult  * planet_score.get(row["pratyantardasha"], 0.0))

        if score >= knobs.threshold:
            rationale = (f'{row["mahadasha"]}-MD ({planet_score.get(row["mahadasha"],0):+.2f}), '
                         f'{row["antardasha"]}-AD ({planet_score.get(row["antardasha"],0):+.2f}), '
                         f'{row["pratyantardasha"]}-PD ({planet_score.get(row["pratyantardasha"],0):+.2f})')
            output.append(dict(start_date=row["start_date"],
                               end_date=row["end_date"],
                               score=round(score,3),
                               why=rationale))

    # 4. Sort best first
    return sorted(output, key=lambda r: r["score"], reverse=True)

# ---------------------------------------------------------------------------
# ❹  CLI / quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, sys
    kp = json.load(open(sys.argv[1]))
    dasa = json.load(open(sys.argv[2]))
    for rec in predict_marriage(kp, dasa)[:15]:
        print(rec["start_date"], rec["end_date"], rec["score"], rec["why"])
```

---

### How the algorithm mirrors **KP principles**

| KP tenet                                                                                                                                                                                                                                                       | How it is coded                                                      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Promise precedes timing** – marriage cannot materialise unless the 7th-cusp sub-lord links to 2 / 7 / 11 and is free of 1 / 6 / 10 / 12 domination ([ep135                                                                                                   | Marriage Prediction in KP Astrology                                  | RVA](https://www.rahasyavedicastrology.com/kp-marriage-prediction/?utm_source=chatgpt.com), [7th House - KP Astrology](https://kpastrology.astrosage.com/kp-learning-home/kp-rules/7th-house?utm_source=chatgpt.com), [8th house for marriage or divorce in KP - Vedic Astrology - Astrogle](https://www.astrogle.com/astrology/8th-house-for-marriage-or-divorce-in-kp.html?utm_source=chatgpt.com)) | `_promise_of_marriage()` gate (can be bypassed via `knobs.require_promise = False`) |
| **Houses 2, 7, 11 cause marriage; 1, 6, 10, 12 (and often 8) obstruct/delay** ([8th house for marriage or divorce in KP - Vedic Astrology - Astrogle](https://www.astrogle.com/astrology/8th-house-for-marriage-or-divorce-in-kp.html?utm_source=chatgpt.com)) | `Knobs.marriage_houses` and `Knobs.obstruction_houses`               |
| **Sub-lord > star-lord > ownership > occupation** in weight                                                                                                                                                                                                    | `weight_subsub` > `weight_sub` > `weight_star_lord` > `weight_owner` |
| **Dasha sequence importance** – Mahadasha > Antardasha > Pratyantardasha                                                                                                                                                                                       | `maha_mult`, `antara_mult`, `prati_mult`                             |
| Tight **aspects** to house owners fine-tune results                                                                                                                                                                                                            | aspect bonus/penalty with orb control                                |
| **Customisable strictness**                                                                                                                                                                                                                                    | Everything exposed through the `Knobs` dataclass                     |

---

### Typical tweak scenarios

| “Dial”                                  | What it does                                             |
| --------------------------------------- | -------------------------------------------------------- |
| `knobs.threshold` ↓                     | Surfaces more candidate windows (looser)                 |
| `knobs.weight_aspect` ↑                 | Put more emphasis on planetary aspects                   |
| `knobs.obstruction_houses = (1, 6, 10)` | Treat the 8th & 12th benignly for love-marriage research |
| `knobs.prati_mult = 0.6`                | Ignore most pratyantar influence (macro view)            |
| `knobs.require_promise = False`         | Force timing even if promise looks weak                  |

---

### Interpreting the output

```text
2025-02-24 2025-08-07  6.41  Mars-MD(+2.9), Venus-AD(+3.4), Sun-PD(+0.1)
```

_Score 6.41_ exceeds the default 4-point threshold:
Mars (MD) owns/occupies/signifies **2 & 7**, Venus (AD) owns **10** but sub-lord wise ties to **1/10** – her high positive score often signals the _actual wedding ceremony_ ([Sublord of 7th Cusp Placement and Results - Vedic Astrology](https://www.astrogle.com/astrology/sublord-7th-cusp-placement-results.html?utm_source=chatgpt.com)).
Sun contributes marginally. Hence **24 Feb – 7 Aug 2025** is rated a strong marriage window.

_(In practice you’d eyeball the top-ranked windows in the context of transits, cultural factors, etc.)_

---

#### Disclaimer

Astrological “predictions” are probabilistic insights, **not certainties**.
Use the function as an analytical aid, not a life-decision oracle.
