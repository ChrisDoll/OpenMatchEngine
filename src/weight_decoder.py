#!/usr/bin/env python3
"""
weights_decoder.py — Hard-wired decoder for Football-Manager 24
weights.jsb → weights.json
"""

from __future__ import annotations

import json
import re
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# ───────── 1. Low-level structures ─────────
@dataclass
class MEVersion:
    """Metadata for one match-engine pack (year never None after normalisation)."""
    ME_PACK_VERSION_MAJOR: int
    ME_PACK_VERSION_MINOR: int
    ME_PACK_VERSION_RELEASE: int
    ME_PACK_VERSION_YEAR: int  # 24, 0, …


@dataclass
class TeamPickingWeights:
    """Numeric weights that drive one team-picking style."""
    TSF_POSITION_ABILITY: int
    TSF_POSITION_ABILITY_IN_ROLE: int
    TSF_POSITION_TACTICAL_FAMILARITY: int
    TSF_LOAN_TERMS: int
    TSF_MATCH_RATING_TIME_ON: int
    TSF_CONDITION: int
    TSF_ALLOWED_MINS: int
    TSF_CA: int
    TSF_PA: int
    TSF_REPUTATION: int
    TSF_YOUNG_PLAYERS: int
    TSF_MORALE: int
    TSF_TESTIMONIAL: int
    TSF_FOOTBALL_PROMISES: int
    TSF_BOOST_LOW_MATCH_FITNESS: int
    TSF_CUP_KEEPER: int
    TSF_PPMS: int
    TSF_HUMAN_SELECTION: int
    TSF_TRIALIST_B_TEAM_PLAYERS: int
    TSF_DECLARED_FOR_RESERVES: int
    TSF_CAPTAINCY: int
    TSF_UNHAPPINESS: int
    TSF_INTERNATIONAL_CAPS: int
    TSF_CLUB_NATION_CHOICE_FACTORS: int
    TSF_FORM: int
    TSF_AGREED_PLAYING_TIME: int
    TSF_PLAYING_SIDE_PREFERENCE: int
    TSF_MATCH_FITNESS: int
    TSF_BOOST_SUBSTITUTE: int
    TSF_STAR_PLAYER: int
    TSF_OLYMPIC_U23: int
    TSF_REST_PROMISES: int
    TSF_UPCOMING_SUSPENSION: int
    TSF_NEED_MATCH_XP: int
    TSF_DISLIKE_BY_NON_PLAYER: int
    TSF_INTEGRATION: int
    TSF_LAST_RATINGS: int
    TSF_VIRTUAL: int
    TSF_EXTRA_ADJ: int


# ───────── 2. Season block ─────────
@dataclass(slots=True)
class SeasonWeights:
    """Weights for one match-engine season/pack."""
    ME_VERSION: MEVersion
    TPS_FIRST_TEAM_PICKING: TeamPickingWeights
    TPS_SEMI_RESERVE_PICKING: TeamPickingWeights
    TPS_SLIGHTLY_RESERVE_PICKING: TeamPickingWeights
    TPS_TOTAL_RESERVE_PICKING: TeamPickingWeights


# ───────── 3. Top-level document ─────────
@dataclass(slots=True)
class WeightsDoc:
    WEIGHTS: list[SeasonWeights]


# ───────── regex helpers ─────────
_PFX = b"(?:TEAM_PICKING_STYLE::|simatchshared::TSF_|ME_PACK_VERSION_)"
_NEXT_KEY = b"[\x82\x5A\x6A\x00]"
_PATTERN = (
    rb"(" + _PFX + rb"[A-Z0-9_:]{1,96})"
    rb"(?:\x02(.{4})"        # int32 value
    rb"|\x0A.{5}"            # nested object header (skip)
    rb"|(?=" + _NEXT_KEY + rb"))"
)
_KEY_RE = re.compile(_PATTERN, re.DOTALL)

def _le_i32(b: bytes) -> int:
    return struct.unpack("<i", b)[0]


# ───────── helper: build TeamPickingWeights from raw dict ─────────
def _make_tpw(raw: dict[str, int]) -> TeamPickingWeights:
    """Strip the 'simatchshared::' prefix and fill missing fields with 0."""
    base: dict[str, int] = {
        fld: raw.get(f"simatchshared::{fld}", 0)
        for fld in TeamPickingWeights.__annotations__
    }
    return TeamPickingWeights(**base)  # type: ignore[arg-type]


# ───────── flatten → dataclasses ─────────
def _restructure(pairs: list[tuple[str, int | None]]) -> WeightsDoc:
    blocks: list[dict[str, Any]] = []
    me_buf: dict[str, int | None] = {}
    cur_block: dict[str, Any] | None = None
    cur_tps: str | None = None

    for k, v in pairs:
        # ME_VERSION keys
        if k.startswith("ME_PACK_VERSION_"):
            me_buf[k] = v
            if k == "ME_PACK_VERSION_YEAR":  # complete ME_VERSION → new block
                cur_block = {"ME_VERSION": dict(me_buf)}
                blocks.append(cur_block)
                me_buf.clear()
                cur_tps = None
            continue

        # TPS header
        if k.startswith("TEAM_PICKING_STYLE::"):
            if cur_block is None:
                cur_block = {"ME_VERSION": dict(me_buf)}
                blocks.append(cur_block)
                me_buf.clear()
            cur_tps = k
            cur_block[cur_tps] = {}
            continue

        # ordinary weight
        if cur_block is None:
            cur_block = {"ME_VERSION": dict(me_buf)}
            blocks.append(cur_block)
            me_buf.clear()
        if cur_tps is None:          # stray weight
            cur_tps = "MISC"
            cur_block[cur_tps] = {}
        if v is not None:
            cur_block[cur_tps][k] = v

    # post-process: null→0 and drop ME_YEAR 23
    cleaned: list[dict[str, Any]] = []
    for blk in blocks:
        year = blk["ME_VERSION"].get("ME_PACK_VERSION_YEAR")
        if year is None:
            blk["ME_VERSION"]["ME_PACK_VERSION_YEAR"] = 0
            year = 0
        if year == 23:           # discard FM23 pack
            continue
        cleaned.append(blk)

    # dicts → dataclasses
    seasons: list[SeasonWeights] = []
    for blk in cleaned:
        me = MEVersion(**blk["ME_VERSION"])  # type: ignore[arg-type]

        def pick(name: str) -> TeamPickingWeights:
            return _make_tpw(blk.get(f"TEAM_PICKING_STYLE::{name}", {}))

        seasons.append(
            SeasonWeights(
                ME_VERSION=me,
                TPS_FIRST_TEAM_PICKING=pick("TPS_FIRST_TEAM_PICKING"),
                TPS_SEMI_RESERVE_PICKING=pick("TPS_SEMI_RESERVE_PICKING"),
                TPS_SLIGHTLY_RESERVE_PICKING=pick("TPS_SLIGHTLY_RESERVE_PICKING"),
                TPS_TOTAL_RESERVE_PICKING=pick("TPS_TOTAL_RESERVE_PICKING"),
            )
        )

    return WeightsDoc(WEIGHTS=seasons)


# ───────── decode one weights.jsb file ─────────
def decode(jsb: Path) -> WeightsDoc:
    data = jsb.read_bytes()
    pairs: list[tuple[str, int | None]] = []

    for m in _KEY_RE.finditer(data):
        key = m.group(1).decode("ascii")
        vbytes = m.group(2)
        if vbytes is not None:
            val: int | None = _le_i32(vbytes)
        else:
            # ME_* defaults to 0 except YEAR (None for now)
            val = 0 if key.startswith("ME_PACK_VERSION_") and key != "ME_PACK_VERSION_YEAR" else None
        pairs.append((key, val))

    return _restructure(pairs)


# ───────── misc util ─────────
def _pause(msg: str = "Press Enter to continue…") -> None:
    if getattr(sys.flags, "interactive", 0):
        return
    if "ipykernel" in sys.modules or "IPython" in sys.modules:
        return
    try:
        input(msg)
    except EOFError:
        pass


# ───────── main ─────────
def main() -> None:

    # ───────── Hard-coded paths ─────────
    ROOT: Path = Path(__file__).resolve().parent.parent
    JSB_PATH: Path = ROOT / "src" / "clean_simatch" / "weights.jsb"
    JSON_PATH: Path = ROOT / "weights.json"

    if not JSB_PATH.exists():
        _pause(f"weights.jsb not found at {JSB_PATH}")
        return

    print(f"→ decoding {JSB_PATH}")
    try:
        doc = decode(JSB_PATH)
        JSON_PATH.write_text(json.dumps(asdict(doc), indent=2, ensure_ascii=False), "utf-8")
        print(f"✓ {JSON_PATH.name}")
        _pause()
    except Exception as exc:  # pragma: no-cover
        _pause(f"Failed: {exc}")


if __name__ == "__main__":
    main()
