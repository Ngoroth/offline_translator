"""Aggregate structured performance events from a Loguru JSON log."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import cast


REQUIRED_PHASES = {
    "trial_end",
    "resource_start",
    "resource_end",
    "ptt_release",
    "stt_start",
    "stt_end",
    "llm_start",
    "llm_end",
    "tts_start",
    "tts_first_chunk",
    "tts_end",
}
PLAYBACK_PHASES = ("playback_submit", "playback_first_write")
RESOURCE_FIELDS = {
    "mem_available_kb",
    "process_vmrss_kb",
    "swap_free_kb",
    "pswpin",
    "pswpout",
    "cpu_freq_khz",
    "cpu_governor",
    "temperature_c",
    "vcgencmd_throttled",
}
ORDER_CONSTRAINTS = (
    ("trial_start", "resource_start"),
    ("resource_start", "ptt_release"),
    ("ptt_release", "stt_start"),
    ("stt_start", "stt_end"),
    ("stt_end", "llm_start"),
    ("llm_start", "llm_end"),
    ("llm_end", "tts_start"),
    ("tts_start", "tts_first_chunk"),
    ("tts_start", "tts_end"),
    ("tts_first_chunk", "playback_submit"),
    ("playback_submit", "resource_end"),
    ("tts_end", "resource_end"),
    ("resource_end", "trial_end"),
)


def _as_dict(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None


def load_events(path: Path) -> list[dict[str, object]]:
    """Read only performance events from serialized Loguru records."""

    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = _as_dict(cast(object, json.loads(line)))
        except json.JSONDecodeError:
            continue
        if record is None:
            continue
        log_record = _as_dict(record.get("record"))
        extra = _as_dict(log_record.get("extra")) if log_record else None
        event = _as_dict(extra.get("performance_event")) if extra else None
        if event is not None:
            events.append(event)
    return events


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _phase_time(events: list[dict[str, object]], phase: str) -> int | None:
    values = [
        int(value)
        for event in events
        if event.get("phase") == phase
        for value in [_number(event.get("monotonic_ns"))]
        if value is not None
    ]
    return values[0] if len(values) == 1 else None


def _phase_time_any(events: list[dict[str, object]], phases: tuple[str, ...]) -> int | None:
    values = [
        int(value)
        for event in events
        if event.get("phase") in phases
        for value in [_number(event.get("monotonic_ns"))]
        if value is not None
    ]
    return values[0] if len(values) == 1 else None


def _duration_ms(events: list[dict[str, object]], start: str, end: str) -> float | None:
    start_ns = _phase_time(events, start)
    end_ns = _phase_time(events, end)
    if start_ns is None or end_ns is None or end_ns < start_ns:
        return None
    return (end_ns - start_ns) / 1_000_000


def _duration_to_playback(events: list[dict[str, object]]) -> float | None:
    start_ns = _phase_time(events, "ptt_release")
    end_ns = _phase_time_any(events, PLAYBACK_PHASES)
    if start_ns is None or end_ns is None or end_ns < start_ns:
        return None
    return (end_ns - start_ns) / 1_000_000


def _throttle_active(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip().lower()
    if "=" in normalized:
        normalized = normalized.rsplit("=", maxsplit=1)[1].strip()
    return normalized not in {"0", "0x0", "0x00000", "0x00000000"}


def _resource_pressure(events: list[dict[str, object]]) -> list[str]:
    starts: dict[str, object] = {}
    ends: dict[str, object] = {}
    for event in events:
        phase = event.get("phase")
        resource = _as_dict(event.get("resource"))
        if phase == "resource_start" and resource is not None:
            starts = resource
        elif phase == "resource_end" and resource is not None:
            ends = resource

    reasons: list[str] = []
    for key in ("pswpin", "pswpout"):
        before = _number(starts.get(key))
        after = _number(ends.get(key))
        if before is not None and after is not None and after > before:
            reasons.append(f"{key}_delta={int(after - before)}")

    for boundary, resources in (("start", starts), ("end", ends)):
        throttle = resources.get("vcgencmd_throttled")
        if _throttle_active(throttle):
            reasons.append(f"throttle_{boundary}={throttle}")
    return reasons


def _resource_snapshot_complete(events: list[dict[str, object]], phase: str) -> bool:
    snapshots = [
        _as_dict(event.get("resource"))
        for event in events
        if event.get("phase") == phase
    ]
    if len(snapshots) != 1 or snapshots[0] is None:
        return False
    snapshot = snapshots[0]
    return RESOURCE_FIELDS <= snapshot.keys() and all(
        snapshot[field] is not None for field in RESOURCE_FIELDS
    )


def _phase_positions(events: list[dict[str, object]]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, event in enumerate(events):
        phase = event.get("phase")
        if isinstance(phase, str) and phase not in positions:
            positions[phase] = index
    if "playback_submit" not in positions and "playback_first_write" in positions:
        positions["playback_submit"] = positions["playback_first_write"]
    return positions


def _trial_shape_reasons(events: list[dict[str, object]]) -> list[str]:
    counts: dict[str, int] = {}
    for event in events:
        phase = event.get("phase")
        if isinstance(phase, str):
            counts[phase] = counts.get(phase, 0) + 1

    reasons: list[str] = []
    for phase in sorted(REQUIRED_PHASES):
        if counts.get(phase, 0) == 0:
            reasons.append(f"missing_phase={phase}")
        elif counts[phase] > 1:
            reasons.append(f"duplicate_phase={phase}")
    playback_count = sum(counts.get(phase, 0) for phase in PLAYBACK_PHASES)
    if playback_count == 0:
        reasons.append("missing_phase=playback_submit")
    elif playback_count > 1:
        reasons.append("duplicate_phase=playback_submit")

    positions = _phase_positions(events)
    for before, after in ORDER_CONSTRAINTS:
        if before in positions and after in positions and positions[before] >= positions[after]:
            reasons.append(f"out_of_order={before}>{after}")

    if not _resource_snapshot_complete(events, "resource_start") or not _resource_snapshot_complete(
        events, "resource_end"
    ):
        reasons.append("missing_or_incomplete_resource_snapshot")
    return reasons


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _metric_summary(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "p50_ms": _percentile(values, 50),
        "p95_ms": _percentile(values, 95),
    }


def aggregate_events(events: Iterable[dict[str, object]]) -> dict[str, object]:
    """Return p50/p95 for valid warm trials and explicit invalid-trial reasons."""

    grouped: dict[str, list[dict[str, object]]] = {}
    for event in events:
        trial_id = event.get("trial_id")
        if isinstance(trial_id, str) and trial_id:
            grouped.setdefault(trial_id, []).append(event)

    valid_warm = 0
    invalid_warm: list[dict[str, object]] = []
    metric_values: dict[str, list[float]] = {
        "release_to_first_audio": [],
        "stt": [],
        "llm": [],
        "tts": [],
        "tts_to_first_chunk": [],
    }

    for trial_id, trial_events in grouped.items():
        kind = next(
            (
                event.get("trial_kind")
                for event in trial_events
                if isinstance(event.get("trial_kind"), str)
            ),
            None,
        )
        if kind != "warm":
            if kind != "cold":
                invalid_warm.append(
                    {"trial_id": trial_id, "reasons": ["missing_or_invalid_trial_kind"]}
                )
            continue

        has_fingerprint = any(
            isinstance(event.get("profile_fingerprint"), dict) for event in trial_events
        )
        pressure = _resource_pressure(trial_events)
        reasons = _trial_shape_reasons(trial_events)
        if not has_fingerprint:
            reasons.append("missing_profile_fingerprint")
        reasons.extend(f"resource_pressure:{reason}" for reason in pressure)
        if reasons:
            invalid_warm.append({"trial_id": trial_id, "reasons": reasons})
            continue

        durations = {
            "release_to_first_audio": _duration_to_playback(trial_events),
            "stt": _duration_ms(trial_events, "stt_start", "stt_end"),
            "llm": _duration_ms(trial_events, "llm_start", "llm_end"),
            "tts": _duration_ms(trial_events, "tts_start", "tts_end"),
            "tts_to_first_chunk": _duration_ms(
                trial_events, "tts_start", "tts_first_chunk"
            ),
        }
        if any(value is None for value in durations.values()):
            invalid_warm.append({"trial_id": trial_id, "reasons": ["invalid_timestamps"]})
            continue
        valid_warm += 1
        for metric, value in durations.items():
            metric_values[metric].append(cast(float, value))

    return {
        "warm_trials": {
            "valid": valid_warm,
            "invalid": len(invalid_warm),
            "invalid_details": invalid_warm,
        },
        "metrics_ms": {
            metric: _metric_summary(values) for metric, values in metric_values.items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("log", type=Path, help="serialized Loguru JSON log")
    args = parser.parse_args()
    log_path = cast(Path, args.log)
    report = aggregate_events(load_events(log_path))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
