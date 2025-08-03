#!/usr/bin/env python3
"""
physics/physical_constraints.jsb  →  physical_constraints.json decoder
---------------------------------------------------------------------
• Hard-wired to src/clean_simatch/physics/physical_constraints.jsb
• Decodes the TWO embedded copies (obj1, obj2) with the correct integer-tag
  rules: 0x02 → 4-byte little-endian, 0x??2 with bit-7 = 1 → 1-byte int.
• Saves a JSON list **[obj1, obj2]** whose keys are ordered by the fixed
  ORDER list (extras appended alphabetically).
• Provides helpers to
      – compare the two copies inside the JSB           → compare_jsb_copies()
      – verify the JSB against a “desired values” JSON  → verify_physical_constraints()
"""

from __future__ import annotations
from pathlib import Path
import json
import string
import sys

# ───────────────────────── paths ────────────────────────────────
ROOT_DIR         = Path(__file__).resolve().parent.parent
SIMATCH_FOLDER   = ROOT_DIR / "src" / "clean_simatch"
PHYSICS_JSB_PATH = SIMATCH_FOLDER / "physics" / "physical_constraints.jsb"
PHYSICS_JSON_OUT = ROOT_DIR / "physical_constraints.json"          # decoder output
PATCH_VALUES_JSON = ROOT_DIR / "desired_physical_constraints.json" # ← used by verify()

# ───────────────────── indicator helpers ────────────────────────
_ASCII_OK = set(map(ord, string.ascii_letters + string.digits + "_"))

def _find_indicator(jsb: bytes, pos: int) -> int:
    """Return index of first non-ASCII byte at/after *pos* (the indicator)."""
    while pos < len(jsb) and jsb[pos] in _ASCII_OK:
        pos += 1
    return pos

def _int_size(ind: int) -> int | None:
    if ind == 0x02:                              # full 32-bit
        return 4
    if (ind & 0x80) and (ind & 0x0F) == 0x02:    # compressed 8-bit
        return 1
    return None

# ───────────────────── presentation order ───────────────────────
ORDER = [
    #                                              ↓↓↓  (unchanged list)  ↓↓↓
    "very_slow_walk_speed","slow_walk_speed","walk_speed","fast_walk_speed",
    "slow_jog_speed","jog_speed","moderate_jog_speed","fast_jog_speed",
    "run_speed","sprint_speed","base_top_speed","top_speed",
    "speed_scaler","acceleration_scaler","soft_kick_speed",
    "soft_to_medium_kick_speed","medium_kick_speed",
    "medium_to_moderate_kick_speed","moderate_kick_speed",
    "quite_hard_kick_speed","hard_kick_speed","very_hard_kick_speed",
    "basic_header_speed","theoretical_max_acceleration",
    "theoretical_max_deceleration","theoretical_max_diving_acceleration",
    "theoretical_max_diving_speed",
    "theoretical_max_potential_direction_change_jog",
    "theoretical_max_potential_direction_change_run",
    "theoretical_max_potential_direction_change_walk",
    "theoretical_max_running_speed","theoretical_max_turning_rate",
    "theoretical_min_acceleration","theoretical_min_deceleration",
    "theoretical_min_diving_acceleration","theoretical_min_diving_speed",
    "theoretical_min_potential_direction_change_jog",
    "theoretical_min_potential_direction_change_run",
    "theoretical_min_potential_direction_change_walk",
    "min_delay_for_ball_lunge_do","min_delay_for_ball_lunge_receive",
    "min_delay_for_block_tackle_do","min_delay_for_block_tackle_receive",
    "min_delay_for_celebrating_a_goal","min_delay_for_deflect_ball_do",
    "min_delay_for_deflect_ball_receive","min_delay_for_diving_header",
    "min_delay_for_foot_up_in_tackle_do",
    "min_delay_for_foot_up_in_tackle_receive",
    "min_delay_for_force_opponent_to_lose_ball_do",
    "min_delay_for_force_opponent_to_lose_ball_receive",
    "min_delay_for_getting_injured","min_delay_for_normal_header",
    "min_delay_for_obstruct_do","min_delay_for_obstruct_receive",
    "min_delay_for_player_stop_to_avoid_collision",
    "min_delay_for_push_opponen_receive","min_delay_for_push_opponent_do",
    "min_delay_for_shirt_tug_receive","min_delay_for_shoulder_charge_do",
    "min_delay_for_shoulder_charge_receive","min_delay_for_slide_tackle_do",
    "min_delay_for_slide_tackle_receive","min_delay_for_trip_do",
    "min_delay_for_trip_receive","min_delay_for_two_footed_tackle_do",
    "min_delay_for_two_footed_tackle_receive","min_delay_for_violent_act_do",
    "min_delay_for_violent_act_receive",
    "min_delay_keeper_drop_ball_for_distribution",
    "min_delay_keeper_save_dive_and_hold_ball",
    "min_delay_keeper_save_dive_but_not_held",
    "min_delay_keeper_save_intentionally_drop_ball",
    "min_delay_keeper_save_no_dive_hold_ball",
    "min_delay_keeper_save_no_dive_not_held",
    "min_delay_keeper_save_with_outreached_foot",
    "min_extra_delay_for_falling_down_before_injury",
    "version_year",
]

# ───── full offset table ────────────────────────────────────────

physical_constraints_offsets: dict[str, dict[str, int]] = {
    "acceleration_scaler": {
        "loc": 0x00000016,
        "loc2": 0x00000B1D,
    },
    "base_top_speed": {
        "loc": 0x0000002F,
        "loc2": 0x00000B36,
    },
    "basic_header_speed": {
        "loc": 0x00000043,
        "loc2": 0x00000B4A,
    },
    "fast_jog_speed": {
        "loc": 0x0000005B,
        "loc2": 0x00000B62,
    },
    "fast_walk_speed": {
        "loc": 0x0000006F,
        "loc2": 0x00000B76,
    },
    "hard_kick_speed": {
        "loc": 0x00000084,
        "loc2": 0x00000B8B,
    },
    "jog_speed": {
        "loc": 0x00000099,
        "loc2": 0x00000BA0,
    },
    "medium_kick_speed": {
        "loc": 0x000000A8,
        "loc2": 0x00000BAF,
    },
    "medium_to_moderate_kick_speed": {
        "loc": 0x000000BF,
        "loc2": 0x00000BC6,
    },
    "min_delay_for_ball_lunge_do": {
        "loc": 0x000000E2,
        "loc2": 0x00000BE9,
    },
    "min_delay_for_ball_lunge_receive": {
        "loc": 0x00000103,
        "loc2": 0x00000C0A,
    },
    "min_delay_for_block_tackle_do": {
        "loc": 0x00000129,
        "loc2": 0x00000C30,
    },
    "min_delay_for_block_tackle_receive": {
        "loc": 0x0000014C,
        "loc2": 0x00000C53,
    },
    "min_delay_for_celebrating_a_goal": {
        "loc": 0x00000174,
        "loc2": 0x00000C7B,
    },
    "min_delay_for_deflect_ball_do": {
        "loc": 0x0000019A,
        "loc2": 0x00000CA1,
    },
    "min_delay_for_deflect_ball_receive": {
        "loc": 0x000001BD,
        "loc2": 0x00000CC4,
    },
    "min_delay_for_diving_header": {
        "loc": 0x000001E5,
        "loc2": 0x00000CEC,
    },
    "min_delay_for_foot_up_in_tackle_do": {
        "loc": 0x00000206,
        "loc2": 0x00000D0D,
    },
    "min_delay_for_foot_up_in_tackle_receive": {
        "loc": 0x0000022E,
        "loc2": 0x00000D35,
    },
    "min_delay_for_force_opponent_to_lose_ball_do": {
        "loc": 0x0000025B,
        "loc2": 0x00000D62,
    },
    "min_delay_for_force_opponent_to_lose_ball_receive": {
        "loc": 0x0000028D,
        "loc2": 0x00000D94,
    },
    "min_delay_for_getting_injured": {
        "loc": 0x000002C4,
        "loc2": 0x00000DCB,
    },
    "min_delay_for_normal_header": {
        "loc": 0x000002E7,
        "loc2": 0x00000DEE,
    },
    "min_delay_for_obstruct_do": {
        "loc": 0x00000308,
        "loc2": 0x00000E0F,
    },
    "min_delay_for_obstruct_receive": {
        "loc": 0x00000327,
        "loc2": 0x00000E2E,
    },
    "min_delay_for_player_stop_to_avoid_collision": {
        "loc": 0x0000034B,
        "loc2": 0x00000E52,
    },
    "min_delay_for_push_opponen_receive": {
        "loc": 0x0000037D,
        "loc2": 0x00000E84,
    },
    "min_delay_for_push_opponent_do": {
        "loc": 0x000003A5,
        "loc2": 0x00000EAC,
    },
    "min_delay_for_shirt_tug_do": {
        "loc": 0x000003C9,
        "loc2": 0x00000ED0,
    },
    "min_delay_for_shirt_tug_receive": {
        "loc": 0x000003E5,
        "loc2": 0x00000EEC,
    },
    "min_delay_for_shoulder_charge_do": {
        "loc": 0x0000040A,
        "loc2": 0x00000F11,
    },
    "min_delay_for_shoulder_charge_receive": {
        "loc": 0x00000430,
        "loc2": 0x00000F37,
    },
    "min_delay_for_slide_tackle_do": {
        "loc": 0x0000045B,
        "loc2": 0x00000F62,
    },
    "min_delay_for_slide_tackle_receive": {
        "loc": 0x0000047E,
        "loc2": 0x00000F85,
    },
    "min_delay_for_trip_do": {
        "loc": 0x000004A6,
        "loc2": 0x00000FAD,
    },
    "min_delay_for_trip_receive": {
        "loc": 0x000004C1,
        "loc2": 0x00000FC8,
    },
    "min_delay_for_two_footed_tackle_do": {
        "loc": 0x000004E1,
        "loc2": 0x00000FE8,
    },
    "min_delay_for_two_footed_tackle_receive": {
        "loc": 0x00000509,
        "loc2": 0x00001010,
    },
    "min_delay_for_violent_act_do": {
        "loc": 0x00000536,
        "loc2": 0x0000103D,
    },
    "min_delay_for_violent_act_receive": {
        "loc": 0x00000558,
        "loc2": 0x0000105F,
    },
    "min_delay_keeper_drop_ball_for_distribution": {
        "loc": 0x0000057F,
        "loc2": 0x00001086,
    },
    "min_delay_keeper_save_dive_and_hold_ball": {
        "loc": 0x000005B0,
        "loc2": 0x000010B7,
    },
    "min_delay_keeper_save_dive_but_not_held": {
        "loc": 0x000005DE,
        "loc2": 0x000010E5,
    },
    "min_delay_keeper_save_intentionally_drop_ball": {
        "loc": 0x0000060B,
        "loc2": 0x00001112,
    },
    "min_delay_keeper_save_no_dive_hold_ball": {
        "loc": 0x0000063E,
        "loc2": 0x00001145,
    },
    "min_delay_keeper_save_no_dive_not_held": {
        "loc": 0x0000066B,
        "loc2": 0x00001172,
    },
    "min_delay_keeper_save_with_outreached_foot": {
        "loc": 0x00000697,
        "loc2": 0x0000119E,
    },
    "min_extra_delay_for_falling_down_before_injury": {
        "loc": 0x000006C7,
        "loc2": 0x000011CE,
    },
    "version_major": {
        "loc": 0x0000070B,
        "loc2": 0x00001212,
    },
    "version_minor": {
        "loc": 0x0000071A,
        "loc2": 0x00001221,
    },
    "version_release": {
        "loc": 0x00000729,
        "loc2": 0x00001230,
    },
    "version_year": {
        "loc": 0x0000073A,
        "loc2": 0x00001241,
    },
    "moderate_jog_speed": {
        "loc": 0x0000074C,
        "loc2": 0x0000124F,
    },
    "moderate_kick_speed": {
        "loc": 0x00000764,
        "loc2": 0x00001267,
    },
    "quite_hard_kick_speed": {
        "loc": 0x0000077D,
        "loc2": 0x00001280,
    },
    "run_speed": {
        "loc": 0x00000798,
        "loc2": 0x0000129B,
    },
    "slow_jog_speed": {
        "loc": 0x000007A7,
        "loc2": 0x000012AA,
    },
    "slow_walk_speed": {
        "loc": 0x000007BB,
        "loc2": 0x000012BE,
    },
    "soft_kick_speed": {
        "loc": 0x000007D0,
        "loc2": 0x000012D3,
    },
    "soft_to_medium_kick_speed": {
        "loc": 0x000007E5,
        "loc2": 0x000012E8,
    },
    "speed_scaler": {
        "loc": 0x00000804,
        "loc2": 0x00001307,
    },
    "sprint_speed": {
        "loc": 0x00000816,
        "loc2": 0x00001319,
    },
    "theoretical_max_acceleration": {
        "loc": 0x00000828,
        "loc2": 0x0000132B,
    },
    "theoretical_max_deceleration": {
        "loc": 0x0000084A,
        "loc2": 0x0000134D,
    },
    "theoretical_max_diving_acceleration": {
        "loc": 0x0000086C,
        "loc2": 0x0000136F,
    },
    "theoretical_max_diving_speed": {
        "loc": 0x00000895,
        "loc2": 0x00001398,
    },
    "theoretical_max_potential_direction_change_jog": {
        "loc": 0x000008B7,
        "loc2": 0x000013BA,
    },
    "theoretical_max_potential_direction_change_run": {
        "loc": 0x000008EB,
        "loc2": 0x000013EE,
    },
    "theoretical_max_potential_direction_change_walk": {
        "loc": 0x0000091F,
        "loc2": 0x00001422,
    },
    "theoretical_max_running_speed": {
        "loc": 0x00000954,
        "loc2": 0x00001457,
    },
    "theoretical_max_turning_rate": {
        "loc": 0x00000977,
        "loc2": 0x0000147A,
    },
    "theoretical_min_acceleration": {
        "loc": 0x00000999,
        "loc2": 0x0000149C,
    },
    "theoretical_min_deceleration": {
        "loc": 0x000009BB,
        "loc2": 0x000014BE,
    },
    "theoretical_min_diving_acceleration": {
        "loc": 0x000009DD,
        "loc2": 0x000014E0,
    },
    "theoretical_min_diving_speed": {
        "loc": 0x00000A06,
        "loc2": 0x00001509,
    },
    "theoretical_min_potential_direction_change_jog": {
        "loc": 0x00000A28,
        "loc2": 0x0000152B,
    },
    "theoretical_min_potential_direction_change_run": {
        "loc": 0x00000A5C,
        "loc2": 0x0000155F,
    },
    "theoretical_min_potential_direction_change_walk": {
        "loc": 0x00000A90,
        "loc2": 0x00001593,
    },
    "top_speed": {
        "loc": 0x00000AC5,
        "loc2": 0x000015C8,
    },
    "very_hard_kick_speed": {
        "loc": 0x00000AD4,
        "loc2": 0x000015D7,
    },
    "very_slow_walk_speed": {
        "loc": 0x00000AEE,
        "loc2": 0x000015F1,
    },
    "walk_speed": {
        "loc": 0x00000B08,
        "loc2": 0x0000160B,
    },
}


# ═════════════════════════ DECODER ══════════════════════════════
def decode_physical_constraints(
    which: str | None = None,
):
    """
    Returns
    -------
    • which is None  → [obj1, obj2]  (default)
    • which = 'obj1' → obj1
    • which = 'obj2' → obj2
    """
    jsb = PHYSICS_JSB_PATH.read_bytes()

    ignored_keys = {
        "version_year",
        "version_major",
        "version_minor",
        "version_release",
        "version_year",
    }

    def _grab(key: str, loc: int | None) -> int | None:
        if loc is None:
            return None
        ind_pos = _find_indicator(jsb, loc)
        size    = _int_size(jsb[ind_pos])
        if size is None:
            return None
        blob = jsb[ind_pos + 1 : ind_pos + 1 + size]
        if len(blob) != size:
            return None
        return int.from_bytes(blob, "little")

    obj1, obj2 = {}, {}
    for key, offs in physical_constraints_offsets.items():
        if key in ignored_keys:
            continue
        obj1_val = _grab(key, offs.get("loc"))
        obj2_val = _grab(key, offs.get("loc2"))
        if obj1_val is not None:
            obj1[key] = obj1_val
        if obj2_val is not None:
            obj2[key] = obj2_val

    if which == "obj1":
        return obj1
    if which == "obj2":
        return obj2
    return [obj1, obj2]

# ─────────────────────── ordering helper ────────────────────────
def _ordered(d: dict[str, int]) -> dict[str, int]:
    out: dict[str, int] = {}
    for k in ORDER:
        if k in d:
            out[k] = d.pop(k)
    for k in sorted(d):                # append leftovers alphabetically
        out[k] = d[k]
    return out

# ═══════════  COMPARISON & VERIFICATION UTILITIES  ══════════════
def compare_jsb_copies(ignored: set[str] | None = None) -> bool:
    """
    Print differences between the two embedded objects.  Returns True if
    identical (aside from *ignored* keys).
    """
    if ignored is None:
        ignored = {"version_major", "version_minor", "version_release",
                   "version_year"}

    obj1: dict[str, int]
    obj2: dict[str, int]
    obj1, obj2 = decode_physical_constraints()   # list unpack
    ok = True
    for k in sorted(set(obj1) | set(obj2)):
        if k in ignored:
            continue
        if obj1.get(k) != obj2.get(k):
            print(f"[DIFF] {k}: obj1={obj1.get(k)}  obj2={obj2.get(k)}")
            ok = False
    print("✔  Objects identical" if ok else "✘  Objects differ")
    return ok

def verify_physical_constraints() -> bool:
    """
    Compare JSB values against PATCH_VALUES_JSON (dict of desired values).
    A key passes if AT LEAST one of the two copies matches the expected value.
    """
    if not PATCH_VALUES_JSON.exists():
        print("Desired-values JSON not found – nothing to verify.")
        return False

    desired: dict[str, int] = json.loads(PATCH_VALUES_JSON.read_text("utf-8"))
    obj1, obj2 = decode_physical_constraints()

    ok = True
    for key, exp in desired.items():
        v1, v2 = obj1.get(key), obj2.get(key)
        if v1 == exp or v2 == exp:
            if v1 != v2:
                print(f"[WARN] {key}: obj1={v1}, obj2={v2}, expected={exp}")
        else:
            print(f"[FAIL] {key}: obj1={v1}, obj2={v2}, expected={exp}")
            ok = False

    print("✔  Verification succeeded" if ok else "✘  Verification failed")
    return ok

# ═════════════════════════ main() ═══════════════════════════════

def ask_num_objects() -> str:
    """Ask user for which object to decode."""
    while True:
        choice = input("""
            Which object to decode? (obj1, obj2, both): 
            In most cases, you should want obj1, when patching, both a sole object is needed.
            1: obj1
            2: obj2
            3: both           
                       
            """).strip().lower()
        
        if choice in ("obj1", "1"):
            return "obj1"
        elif choice in ("obj2", "2"):
            return "obj2"
        elif choice in ("both", "3"):
            return "both"
        print("Invalid choice. Please enter 'obj1', 'obj2', or 'both'.")


def main(choice) -> None:

    if not PHYSICS_JSB_PATH.exists():
        sys.exit(f"JSB not found: {PHYSICS_JSB_PATH}")

    obj1, obj2 = decode_physical_constraints()

    if choice == "obj1":
        obj1 = _ordered(obj1)
        print(f"✓ Decoded {PHYSICS_JSB_PATH.relative_to(ROOT_DIR)} "
              f"({len(obj1)} keys)")
        PHYSICS_JSON_OUT.write_text(json.dumps(obj1, indent=2))
        return
    if choice == "obj2":
        obj2 = _ordered(obj2)
        print(f"✓ Decoded {PHYSICS_JSB_PATH.relative_to(ROOT_DIR)} "
              f"({len(obj2)} keys)")
        PHYSICS_JSON_OUT.write_text(json.dumps(obj2, indent=2))
        return
    if choice == "both":
        obj1 = _ordered(obj1)
        obj2 = _ordered(obj2)
        print(f"✓ Decoded {PHYSICS_JSB_PATH.relative_to(ROOT_DIR)} "
              f"({len(obj1)} keys for obj1, {len(obj2)} keys for obj2)")
        PHYSICS_JSON_OUT.write_text(json.dumps([obj1, obj2], indent=2))
        return

        
if __name__ == "__main__":
    choice = ask_num_objects()
    main(choice)