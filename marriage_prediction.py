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
import pprint

# ---------------------------------------------------------------------------
# ❶  KNOBS  – dial these to make the algorithm stricter or more relaxed
# ---------------------------------------------------------------------------

@dataclass
class Knobs:
    # Houses that PROMISE marriage
    marriage_houses: Tuple[int, ...] = (2, 7, 11)

    # Houses that flat-out DENY marriage
    obstruction_houses: Tuple[int, ...] = (1, 6, 10)

    # Houses that merely DELAY (default weight = 50 % of a denial)
    delay_houses: Tuple[int, ...] = (8, 12)
    delay_scale: float = 0.5          # 0 → ignore, 1 → treat like full obstruction

    # Natural significators (karakas) that deserve a *bonus*
    karaka_planets: Tuple[str, ...] = ("Venus",)
    karaka_bonus: float = 0         # added **after** planet already promises marriage

    # Weights for kinds of signification
    weight_owner:    float = 1.0
    weight_occupant: float = 1.0
    weight_star_lord: float = 1.2
    weight_sub:       float = 1.4
    weight_subsub:    float = 1.6
    weight_aspect:    float = 0.7

    # Dasha multipliers
    maha_mult:   float = 1.5
    antara_mult: float = 1.2
    prati_mult:  float = 1.0

    # Negative-handling knobs
    neg_scale: float        = 0.6
    ignore_neg_if_pos: bool = True

    threshold: float = 4.0
    max_aspect_orb: float = 3.0
    require_promise: bool = True


default_knobs = Knobs()

# ---------------------------------------------------------------------------
# ❷  INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _collect_planet_scores(kp_data: dict, knobs: Knobs) -> Dict[str, float]:
    """
    Build a planet → score table that more faithfully follows KP rules:
      • separates ‘promise’ (2-7-11) from ‘obstruction’ (1-6-8-10-12)
      • fixes the tight-aspect bug (houses are integers, owners are planets!)
      • treats Rahu / Ketu as *agents* of their star-lord (ignores own rulership)
      • gives Venus (or any planet in `karaka_planets`) a bonus
      • separates ‘delay’ houses (8, 12) from outright obstacles (1, 6, 10)
    """

    pos, neg = {}, {}

    # 1.  Per-planet promise / obstruction / delay tallies -------------------
    for rec in kp_data["planet_significators"]:
        p = rec["Planet"]


        # Rahu / Ketu: drop their own rulership; keep star-lord data
        ruled_houses = [] if p in ("Rahu", "Ketu") else rec["planetRuledHouses"]

        print(rec["Planet"], rec["subLordHouseSignifications"])

        # — favourable houses —
        fav  = sum(knobs.weight_owner     for h in ruled_houses                       if h in knobs.marriage_houses)
        fav += sum(knobs.weight_occupant  for h in [rec["occupiedHouse"]]             if h in knobs.marriage_houses)
        fav += sum(knobs.weight_star_lord for h in rec["starLordRuledHouses"]         if h in knobs.marriage_houses)
        fav += sum(knobs.weight_sub       for h in rec["subLordHouseSignifications"]  if h in knobs.marriage_houses)
        fav += sum(knobs.weight_subsub    for h in rec["subSubLordHouseSignifications"]
                                                                                if h in knobs.marriage_houses)

        # —— karaka bonus (NEW) ——
        if p in knobs.karaka_planets and fav > 0:
            fav += knobs.karaka_bonus

        # — outright obstructing houses —
        bad  = sum(knobs.weight_owner     for h in ruled_houses                       if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_occupant  for h in [rec["occupiedHouse"]]             if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_star_lord for h in rec["starLordRuledHouses"]         if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_sub       for h in rec["subLordHouseSignifications"]  if h in knobs.obstruction_houses)
        bad += sum(knobs.weight_subsub    for h in rec["subSubLordHouseSignifications"]
                                                                                if h in knobs.obstruction_houses)

        # — delaying houses (scaled) (NEW) —
        bad_delay  = sum(knobs.weight_owner     for h in ruled_houses                       if h in knobs.delay_houses)
        bad_delay += sum(knobs.weight_occupant  for h in [rec["occupiedHouse"]]             if h in knobs.delay_houses)
        bad_delay += sum(knobs.weight_star_lord for h in rec["starLordRuledHouses"]         if h in knobs.delay_houses)
        bad_delay += sum(knobs.weight_sub       for h in rec["subLordHouseSignifications"]  if h in knobs.delay_houses)
        bad_delay += sum(knobs.weight_subsub    for h in rec["subSubLordHouseSignifications"]
                                                                                if h in knobs.delay_houses)
        bad += bad_delay * knobs.delay_scale

        pos[p], neg[p] = fav, bad

    # 2.  Tight aspects to house owners --------------------------------------
    house_owner = {h["House"]: h["HouseOwner"] for h in kp_data["house_significators"]}

    for asp in kp_data.get("aspects", []):
        if asp["AspectOrb"] > knobs.max_aspect_orb:          # too wide → ignore
            continue

        p1, p2 = asp["P1"], asp["P2"]
        orb_score = knobs.weight_aspect * (knobs.max_aspect_orb - asp["AspectOrb"]) / knobs.max_aspect_orb

        # check which houses *each* counterpart owns
        for p, q in ((p1, p2), (p2, p1)):
            houses_q_owns = [h for h, owner in house_owner.items() if owner == q]
            if not houses_q_owns:
                continue
            if any(h in knobs.marriage_houses for h in houses_q_owns):
                pos[p] = pos.get(p, 0) + orb_score
            if any(h in knobs.obstruction_houses for h in houses_q_owns):
                neg[p] = neg.get(p, 0) + orb_score
            if any(h in knobs.delay_houses for h in houses_q_owns):
                neg[p] = neg.get(p, 0) + orb_score * knobs.delay_scale

    # 3.  Collapse to a net score per planet ---------------------------------
    final = {}
    for pl in pos.keys() | neg.keys():
        good = pos.get(pl, 0.0)
        bad  = neg.get(pl, 0.0) * knobs.neg_scale
        if knobs.ignore_neg_if_pos and good > 0:
            final[pl] = good                       # keep positives intact
        else:
            final[pl] = good - bad                 # net difference
    return final

def _promise_of_marriage(kp_data: dict, planet_scores: Dict[str,float], knobs: Knobs) -> bool:
    """
    Returns True if the chart contains a basic 'promise' per standard KP rules:
      – Sub-lord of 7th cusp must signify at least one of 2,7,11
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
    Return every Vimshottari slice whose three lords *each* give a positive,
    obstruction-free promise of marriage and whose weighted sum beats the
    threshold.  (Transits, sookshma, etc. are **intentionally ignored**.)
    """
    # 1. Planet-level scores -------------------------------------------------
    planet_score = _collect_planet_scores(kp_data, knobs)

    # 2. Promise gate --------------------------------------------------------
    if knobs.require_promise and not _promise_of_marriage(kp_data, planet_score, knobs):
        return []                      # “No promise → no timing.”

    # 3. Evaluate every MD / AD / PD slice ----------------------------------
    output = []
    for row in dasha_table:
        md, ad, pd = (row["mahadasha"], row["antardasha"], row["pratyantardasha"])
        md_score, ad_score, pd_score = (planet_score.get(md, 0.0),
                                        planet_score.get(ad, 0.0),
                                        planet_score.get(pd, 0.0))

        # --- KP insists each lord must individually ‘support’ marriage -----
        if md_score <= 0 or ad_score <= 0:
            continue                    # skip – fails the purity test

        score = (knobs.maha_mult   * md_score +
                 knobs.antara_mult * ad_score +
                 knobs.prati_mult  * pd_score)

        if score >= knobs.threshold:
            output.append(dict(
                start_date=row["start_date"],
                end_date=row["end_date"],
                score=round(score, 3),
                why=(f"{md}-MD ({md_score:+.2f}), "
                     f"{ad}-AD ({ad_score:+.2f}), "
                     f"{pd}-PD ({pd_score:+.2f})")
            ))

    # 4.  Best → worst
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
