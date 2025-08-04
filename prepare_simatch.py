#!/usr/bin/env python3
"""
FM-mod helper – **three fully-self-contained steps**

1. **build_simatch()**
   ▸ copies a pristine tree from src/clean_simatch/ → simatch/
   ▸ swaps weights.jsb → weights.json
   ▸ swaps player_ratings_data.jsb → player_ratings_data.json (clean copy)

2. **patch_physical_constraints()**
   ▸ binary-patches simatch/physics/physical_constraints.jsb
     with the values from physics/physical_constraints.json

3. **apply_ratings_edits()**
   ▸ pushes the numbers you edited in data/player_ratings_data.xlsx
     into simatch/player_ratings_data.json

Edit the *config block* below if your paths differ.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import shutil
import sys
import importlib.util
import importlib
import subprocess

def ensure(pkg: str, symbol: str | None = None) -> Any:
    """
    Import *pkg*. If it's missing, ask whether to install it.
    Returns the module (or getattr(module, symbol) if *symbol* is given).
    """

    # Fast path – nothing interactive, no process exit.
    if importlib.util.find_spec(pkg):
        module = importlib.import_module(pkg)
        globals()[pkg] = module
        return getattr(module, symbol) if symbol else module

    # ------- user interaction ----------------------------------------------
    choice = input(
        f"The script needs '{pkg}'.\n"
        "Press 1 to install and continue, press 2 to abort: "
    ).strip()

    if choice != "1":
        print("Aborted by user.")
        sys.exit(0)

    # ------- make sure pip exists (now safe to exit on fatal errors) --------
    try:
        import pip  # noqa: F401, imported to ensure pip is available
    except ModuleNotFoundError:
        try:
            import ensurepip

            ensurepip.bootstrap(upgrade=True)
        except Exception:
            try:
                subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            except subprocess.CalledProcessError as err:
                print(f"Cannot bootstrap pip: {err}\nExiting.")
                sys.exit(1)

    # ------- install the requested package ---------------------------------
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", pkg]
        )
    except subprocess.CalledProcessError as err:
        print(f"'pip install {pkg}' failed: {err}. Exiting.")
        sys.exit(1)

    # ------- import & return ------------------------------------------------
    try:
        module = importlib.import_module(pkg)
        globals()[pkg] = module
        return getattr(module, symbol) if symbol else module
    except AttributeError:
        print(f"'{pkg}' has no attribute '{symbol}'. Exiting.")
        sys.exit(1)
    except Exception as err:
        print(f"Installed '{pkg}' but could not import it: {err}")
        sys.exit(1)


load_workbook = ensure("openpyxl", "load_workbook")

# ── config – edit here if paths differ ────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
PHYSICS_JSON = ROOT_DIR / "physical_constraints.json"
WEIGHTS_JSON = ROOT_DIR / "weights.json"  # source
RATINGS_JSON = ROOT_DIR / "src" / "player_ratings_data.json"
RATINGS_XLSX = ROOT_DIR / "player_ratings_data.xlsx"
CLEAN_FOLDER = ROOT_DIR / "src" / "clean_simatch"  # pristine tree
SIMATCH_FOLDER = ROOT_DIR / "simatch"

# ── helpers ────────────────────────────────────────────

GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def _pause(input_msg: str = "Press Enter to continue…"):
    # Skip pause if in interactive mode or IPython/Jupyter
    if getattr(sys.flags, "interactive", 0):
        return
    if "ipykernel" in sys.modules or "IPython" in sys.modules:
        return
    try:
        input(input_msg)
    except EOFError:
        pass


def apply_ratings_edits() -> None:
    """Inject numbers from RATINGS_XLSX into simatch/player_ratings_data.json."""

    target_json = SIMATCH_FOLDER / "player_ratings_data.json"

    def excel_to_json(json_path: Path, xlsx_path: Path) -> None:
        data: dict[str, Any] = json.loads(json_path.read_text("utf-8"))
        role_data = data["values"][0]["role_data"]
        maps = [{c["name"]: c for c in block["coefficients"]} for block in role_data]

        ws = load_workbook(xlsx_path, data_only=True).active
        max_r, max_c = ws.max_row or 0, ws.max_column or 0

        for col in range(2, max_c + 1):  # B… = block index
            try:
                b_idx = int(ws.cell(row=1, column=col).value)
            except (TypeError, ValueError):
                continue
            if not (0 <= b_idx < len(role_data)):
                continue
            lookup = maps[b_idx]

            for row in range(4, max_r + 1):
                coeff = ws.cell(row=row, column=1).value
                if not coeff:
                    continue
                val = ws.cell(row=row, column=col).value
                if val in (None, ""):
                    continue
                try:
                    val = int(round(float(val)))
                except (ValueError, TypeError):
                    continue
                entry = lookup.get(coeff)
                if entry:
                    entry["value"] = val

        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")

    try:
        excel_to_json(target_json, RATINGS_XLSX)
    except Exception:
        print(f"Failed to apply edits from {RATINGS_XLSX} to {target_json}.")
        print("Make sure the file exists and is formatted correctly.")
        print("Simatch will use the original values from player_ratings_data.json.")
        _pause("Press Enter to exit…")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────
# 1. Build simatch and swap files
# ──────────────────────────────────────────────────────────────────
def build_simatch() -> None:
    """Clone CLEAN_FOLDER → SIMATCH_FOLDER and replace weights/ratings files."""
    if SIMATCH_FOLDER.exists():
        if input("simatch exists – delete it? [y/N]: ").strip().lower() == "y":
            shutil.rmtree(SIMATCH_FOLDER)
            print("\n")
        else:
            print("Aborted.")
            _pause()
            sys.exit(0)

    shutil.copytree(CLEAN_FOLDER, SIMATCH_FOLDER)
    print(f"Copied new simatch tree for preparation: {SIMATCH_FOLDER} \n")

    # ---- weights -------------------------------------------------
    jsb_weights = SIMATCH_FOLDER / "weights.jsb"
    try:
        if WEIGHTS_JSON.exists():
            jsb_weights.unlink()
            shutil.copy2(WEIGHTS_JSON, SIMATCH_FOLDER / "weights.json")
            print(
                "Replaced weights.jsb with weights.json. \n       If this is not needed, rename/delete weights.json and rerun this script. \n"
            )
        else:
            print("No weights.json found, using original values from weights.jsb")
    except Exception as e:
        print(f"Failed to copy weights.json to simatch/weights.jsb. Unknown error {e}.")
        _pause("Press Enter to exit…")
        sys.exit(1)

    # ---- player_ratings_data ------------------------------------
    try:
        jsb_ratings = SIMATCH_FOLDER / "player_ratings_data.jsb"
        if RATINGS_XLSX.exists():
            jsb_ratings.unlink()
            shutil.copy2(RATINGS_JSON, SIMATCH_FOLDER / "player_ratings_data.json")
            apply_ratings_edits()
            print(
                "Replaced player_ratings_data.jsb with excel values from ratings.xlsx. \n     If this is not needed, rename/delete ratings.xlsx and rerun this script. \n"
            )
        else:
            print(
                "No player_ratings_data.xlsx found, using original values from player_ratings_data.jsb"
            )
    except Exception as e:
        print(
            f"Failed to copy player_ratings_data.json to simatch/player_ratings_data.jsb. Unknown error {e}."
        )
        _pause("Press Enter to exit…")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────
# 2. Patch physical_constraints.jsb inside the new simatch tree
# ──────────────────────────────────────────────────────────────────

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


def patch_physical_constraints() -> None:
    """Binary-patch simatch/physics/physical_constraints.jsb from PHYSICS_JSON.

    The offsets now mark the *first* byte of each key string; the indicator byte
    (`0x02`) is therefore at `loc + len(key)`, and the 32-bit little-endian
    value starts one byte after that.
    """
    ignored_keys = {
        "version_year",
        "version_major",
        "version_minor",
        "version_release",
        "version_year",
    }

    try:
        jsb_path = SIMATCH_FOLDER / "physics" / "physical_constraints.jsb"
        jsb_data = bytearray(jsb_path.read_bytes())

        if not PHYSICS_JSON.exists():
            print("No physical_constraints.json file found, skipping…")
            return

        updates: dict[str, int] = json.loads(PHYSICS_JSON.read_text("utf-8"))

        for key, val in updates.items():
            if key in ignored_keys:
                continue
            if key not in physical_constraints_offsets:
                print(f"Warning: Key '{key}' not found in offsets table, skipping.")
                continue

            for loc_key in ("loc", "loc2"):
                if loc_key not in physical_constraints_offsets[key]:
                    continue
                offset = physical_constraints_offsets[key][loc_key]

                indicator_pos = offset + len(key)
                if jsb_data[indicator_pos] != 0x02:
                    print(
                        f"Warning: Indicator byte for key '{key}' is {jsb_data[indicator_pos]:#x}, this limits editing. Skipping..."
                    )
                    continue
                data_pos = indicator_pos + 1  # first value byte

                value_bytes = val.to_bytes(4, "little", signed=False)
                jsb_data[data_pos : data_pos + 4] = value_bytes

        jsb_path.write_bytes(jsb_data)

    except Exception as e:
        print(f"Failed to patch physical_constraints.jsb: {e}")
        input("Press Enter to exit…")
        sys.exit(1)

    print("Patched physical_constraints.jsb with values from physical_constraints.json")
    print("If this is not needed, delete/rename the JSON file and rerun.\n")

# ──────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────
def main() -> None:
    build_simatch()
    patch_physical_constraints()

    print(
        f"\n{GREEN}✓ Finished - created simatch folder{RESET}"
        f"\n{YELLOW}You now need to use the 'Football Manager 2024 Resource Archiver'"
        f"\nand create simatch.fmf{RESET}"
    )
    _pause()


if __name__ == "__main__":
    main()
