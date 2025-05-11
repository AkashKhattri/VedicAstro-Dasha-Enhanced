# ============================================================
#  transit_tools.py  –  "slow-moving planet" marriage scanner
# ============================================================

from copy import deepcopy
from datetime import timedelta,datetime
from typing import List, Dict, Any, Tuple
from utility import get_planets_aspecting_houses

# ─────────────────────────────────────────────────────────────────────────
# 0-A.  Tiny helper  –  "make sure this is a datetime object"
# ─────────────────────────────────────────────────────────────────────────
def _to_dt(x):
    """Return x itself if already datetime; else parse ISO-8601 string."""
    if isinstance(x, datetime):
        return x
    elif isinstance(x, str):
        return datetime.fromisoformat(x.replace('Z', '+00:00'))
    else:
        return x

# ─────────────────────────────────────────────────────────────────────────
# 1. Date handling utilities
# ─────────────────────────────────────────────────────────────────────────
def date_ranges_overlap(a_start, a_end, b_start, b_end) -> bool:
    """True   ⟺   [a_start, a_end] ∩ [b_start, b_end] ≠ ∅"""
    a_start, a_end = _to_dt(a_start), _to_dt(a_end)
    b_start, b_end = _to_dt(b_start), _to_dt(b_end)
    return max(a_start, b_start) <= min(a_end, b_end)

def ordinal(n: int) -> str:
    """1 → 1st, 2 → 2nd … 11 → 11th (for quick console prints)."""
    return f"{n}{'tsnrhtdd'[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4]}"

# ------------------------------------------------------------------
# 2. Core builder  –  returns BOTH unique rows and simult-blocks
# ------------------------------------------------------------------
MARRIAGE_HOUSES     = {2, 7, 11}    # Match with VedicAstroAPI.py
MIN_SIMULT_PLANETS  = 2                # ≥ 2 planets = "simultaneous"


def merge_transits_for_dasha(
        *,
        transit_list:          List[Dict[str, Any]],
        dasha:                 Dict[str, Any],
        slow_moving_planets:   set,
        rashi_lords_map:       Dict[int, str],
        min_simult_planets:    int   = MIN_SIMULT_PLANETS,
        filter_houses:         set   = MARRIAGE_HOUSES,
        min_duration_days:     int   = 10  # Minimum duration in days
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Return (unique_rows, simult_blocks) for the given dasha slice.

    Parameters:
    -----------
    transit_list: List of transit records
    dasha: Dasha period
    slow_moving_planets: Set of planets to consider
    rashi_lords_map: Mapping of houses to signs
    min_simult_planets: Minimum number of planets required to form a block
    filter_houses: Set of houses that must be touched by at least one planet
    min_duration_days: Minimum duration in days for a block to be included
    """
    dasha_start = _to_dt(dasha["start_date"])
    dasha_end   = _to_dt(dasha["end_date"])

    merged = {}

    for tr in transit_list:
        if tr["planet"] not in slow_moving_planets:
            continue

        tr_start = _to_dt(tr["start_date"])
        tr_end   = _to_dt(tr["end_date"])
        if not date_ranges_overlap(tr_start, tr_end, dasha_start, dasha_end):
            continue
        t = deepcopy(tr)                     # never mutate the master list
        sign = t["sign"]

        #  house number via rashi → house map  -----------------------------
        house_number = next((h for h, s in rashi_lords_map.items()
                             if s == sign), None)
        t["transiting_house"] = house_number
        t["aspecting_houses"] = (
            get_planets_aspecting_houses(t["planet"], house_number)
            if house_number is not None else []
        )

        #  merge duplicates on (planet, sign) ------------------------------
        key = (t["planet"], sign)
        if key in merged:
            m = merged[key]
            m["start_date"]   = min(m["start_date"], t["start_date"])
            m["end_date"]     = max(m["end_date"],   t["end_date"])
            m["aspecting_houses"] = sorted(
                set(m.get("aspecting_houses", [])) |
                set(t.get("aspecting_houses", []))
            )
        else:
            merged[key] = t

    unique_rows = list(merged.values())

    # ---------- 2-B.  carve out simultaneity windows ----------------------
    simult_blocks = build_simultaneous_blocks(
        unique_rows,
        min_planets = min_simult_planets,
        filter_houses = filter_houses,
        min_duration_days = min_duration_days
    )

    # Filter blocks to ensure they're within dasha period
    filtered_blocks = []
    for block in simult_blocks:
        block_start = _to_dt(block["start"])
        block_end = _to_dt(block["end"])

        # Skip blocks that are completely outside the dasha period
        if block_end < dasha_start or block_start > dasha_end:
            continue

        # Trim start date if needed
        if block_start < dasha_start:
            block["start"] = dasha_start.strftime("%Y-%m-%d")

        # Trim end date if needed
        if block_end > dasha_end:
            block["end"] = dasha_end.strftime("%Y-%m-%d")

        # Recalculate duration after trimming
        new_duration = (_to_dt(block["end"]) - _to_dt(block["start"])).days + 1

        # Skip if duration is now below minimum
        if new_duration < min_duration_days:
            continue

        block["duration_days"] = new_duration
        filtered_blocks.append(block)

    return unique_rows, filtered_blocks


# ------------------------------------------------------------------
# 3.  Sweep-line interval compositor
# ------------------------------------------------------------------
def build_simultaneous_blocks(
        rows:           List[Dict[str, Any]],
        *,
        min_planets:    int,
        filter_houses:  set | None = None,
        min_duration_days: int = 10  # Minimum duration in days
) -> List[Dict[str, Any]]:
    """
    Return every maximal stretch in which the set of active transits
    has ≥ min_planets and (optionally) touches `filter_houses`.
    Each block contains per-planet detail.

    Parameters:
    -----------
    rows: List of transit records
    min_planets: Minimum number of planets required to form a block
    filter_houses: Set of houses that must be touched by at least one planet
    min_duration_days: Minimum duration in days for a block to be included
    """
    events: List[Tuple] = []            # (datetime, flag, row_index)
    for idx, r in enumerate(rows):
        start_date = _to_dt(r["start_date"])
        end_date = _to_dt(r["end_date"])
        events.append((start_date, 1, idx))                    # +1  add
        events.append((end_date + timedelta(days=1), -1, idx)) # -1 remove
    events.sort(key=lambda x: x[0])     # sweep by time

    active: set[int] = set()
    blocks  = []
    prev_t  = None

    for t, flag, idx in events:
        # ----- close previous segment if any ------------------------------
        if prev_t is not None and t > prev_t and len(active) >= min_planets:
            duration_days = (t - prev_t).days

            # Skip short periods
            if duration_days < min_duration_days:
                # Update active set and continue to next event
                if flag == 1:
                    active.add(idx)
                else:
                    active.discard(idx)  # Using discard to avoid KeyError if not present
                prev_t = t
                continue

            houses_hit = set()
            for i in active:
                house = rows[i]["transiting_house"]
                if house:  # Ensure house is not None
                    houses_hit.add(house)
                houses_hit.update(rows[i].get("aspecting_houses", []))

            if filter_houses is None or houses_hit & filter_houses:
                # per-planet info
                planet_details = {
                    rows[i]["planet"]: {
                        "sign":              rows[i]["sign"],
                        "transiting_house":  rows[i]["transiting_house"],
                        "aspecting_houses":  rows[i].get("aspecting_houses", [])
                    }
                    for i in active
                }

                # Format dates as ISO strings in the final output
                blocks.append({
                    "start":            prev_t.strftime("%Y-%m-%d"),
                    "end":              (t - timedelta(days=1)).strftime("%Y-%m-%d"),  # inclusive
                    "duration_days":    duration_days,
                    "planets":          sorted(planet_details.keys()),
                    "houses_affected":  sorted(houses_hit),
                    "planet_details":   planet_details
                })

        # ----- update active set ------------------------------------------
        if flag == 1:
            active.add(idx)
        else:
            active.discard(idx)  # Using discard to avoid KeyError if not present
        prev_t = t

    return blocks


# ------------------------------------------------------------------
# 4.  Convenience console printer  (optional)
# ------------------------------------------------------------------
def print_simult_windows(dasha):
    """Quick human-readable dump for debugging."""
    for win in dasha.get("simultaneous_windows", []):
        start_date = _to_dt(win['start'])
        end_date = _to_dt(win['end'])
        print(f"\n▶ {start_date.date()} → {end_date.date()}")
        for planet, info in win["planet_details"].items():
            asp = ", ".join(map(str, info["aspecting_houses"])) or "–"
            print(f"   • {planet:<8} : transiting "
                  f"{ordinal(info['transiting_house'])} house "
                  f"({info['sign']}) | aspecting {asp}")
# ------------------------------------------------------------------
# 5.  End of module
# ------------------------------------------------------------------
