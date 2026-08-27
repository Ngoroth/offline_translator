from collections.abc import Mapping
from typing import cast

from scripts.aggregate_performance import aggregate_events, load_events


def _event(
    trial_id: str,
    phase: str,
    monotonic_ns: int,
    *,
    trial_kind: str = "warm",
    resource: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "run_id": "run-1",
        "trial_id": trial_id,
        "session_id": f"session-{trial_id}",
        "phase": phase,
        "monotonic_ns": monotonic_ns,
        "audio_ms": None,
        "input_chars": None,
        "output_chars": None,
        "trial_kind": trial_kind,
        "profile_fingerprint": {"profile": "test", "revision": "test-rev"},
        **({"resource": resource} if resource is not None else {}),
    }


def _complete_trial(
    trial_id: str,
    offset_ns: int,
    *,
    trial_kind: str = "warm",
    swap_end: int = 100,
) -> list[dict[str, object]]:
    resource_start = {
        "mem_available_kb": 1000,
        "process_vmrss_kb": 500,
        "swap_free_kb": 2000,
        "pswpin": 100,
        "pswpout": 200,
        "cpu_freq_khz": 1800000,
        "cpu_governor": "performance",
        "temperature_c": 50.0,
        "vcgencmd_throttled": "throttled=0x0",
    }
    resource_end = {
        "mem_available_kb": 900,
        "process_vmrss_kb": 550,
        "swap_free_kb": 2000,
        "pswpin": swap_end,
        "pswpout": 200,
        "cpu_freq_khz": 1800000,
        "cpu_governor": "performance",
        "temperature_c": 52.0,
        "vcgencmd_throttled": "throttled=0x0",
    }
    points = {
        "trial_start": 0,
        "resource_start": 1,
        "ptt_release": 2,
        "stt_start": 3,
        "stt_end": 4,
        "llm_start": 5,
        "llm_end": 7,
        "tts_start": 8,
        "tts_first_chunk": 9,
        "tts_end": 10,
        "playback_first_write": 12,
        "resource_end": 13,
        "trial_end": 14,
    }
    result: list[dict[str, object]] = []
    for phase, offset in points.items():
        resource = resource_start if phase == "resource_start" else None
        if phase == "resource_end":
            resource = resource_end
        result.append(
            _event(
                trial_id,
                phase,
                offset_ns + offset * 1_000_000,
                trial_kind=trial_kind,
                resource=resource,
            )
        )
    return result


def test_aggregator_uses_valid_warm_trials_and_reports_p50_p95() -> None:
    events = _complete_trial("warm-1", 0) + _complete_trial("warm-2", 100_000_000)
    events += _complete_trial("cold-1", 200_000_000, trial_kind="cold")
    events += _complete_trial("swap-1", 300_000_000, swap_end=101)

    report = aggregate_events(events)

    warm_trials = cast(dict[str, object], report["warm_trials"])
    assert warm_trials == {
        "valid": 2,
        "invalid": 1,
        "invalid_details": [
            {
                "trial_id": "swap-1",
                "reasons": ["resource_pressure:pswpin_delta=1"],
            }
        ],
    }
    metrics = cast(dict[str, dict[str, float | int | None]], report["metrics_ms"])
    assert metrics["release_to_first_audio"] == {
        "count": 2,
        "p50_ms": 10.0,
        "p95_ms": 10.0,
    }
    assert metrics["stt"] == {"count": 2, "p50_ms": 1.0, "p95_ms": 1.0}
    assert metrics["llm"] == {"count": 2, "p50_ms": 2.0, "p95_ms": 2.0}


def test_aggregator_invalidates_nonzero_throttle() -> None:
    events = _complete_trial("throttled-1", 0)
    for event in events:
        if event["phase"] == "resource_end":
            resource = event["resource"]
            assert isinstance(resource, dict)
            resource["vcgencmd_throttled"] = "throttled=0x50005"

    report = aggregate_events(events)

    warm_trials = cast(dict[str, object], report["warm_trials"])
    assert warm_trials["valid"] == 0
    assert warm_trials["invalid_details"] == [
        {
            "trial_id": "throttled-1",
            "reasons": ["resource_pressure:throttle_end=throttled=0x50005"],
        }
    ]


def test_load_events_extracts_performance_event_from_loguru_json(tmp_path) -> None:
    log_path = tmp_path / "app.log"
    log_path.write_text(
        '{"record": {"extra": {"performance_event": '
        + '{"trial_id": "trial-1", "phase": "trial_end"}}}}\n',
        encoding="utf-8",
    )

    events = load_events(log_path)

    assert events == [{"trial_id": "trial-1", "phase": "trial_end"}]


def test_aggregator_rejects_trial_without_explicit_kind() -> None:
    report = aggregate_events(_complete_trial("unlabelled-1", 0, trial_kind=""))

    warm_trials = cast(dict[str, object], report["warm_trials"])
    assert warm_trials["valid"] == 0
    assert warm_trials["invalid_details"] == [
        {
            "trial_id": "unlabelled-1",
            "reasons": ["missing_or_invalid_trial_kind"],
        }
    ]


def test_aggregator_rejects_duplicate_phase_events() -> None:
    events = _complete_trial("duplicate-1", 0)
    duplicate = next(event for event in events if event["phase"] == "llm_start")
    events.append(dict(duplicate))

    report = aggregate_events(events)

    warm_trials = cast(dict[str, object], report["warm_trials"])
    assert warm_trials["valid"] == 0
    invalid_details = cast(list[dict[str, object]], warm_trials["invalid_details"])
    assert invalid_details[0]["trial_id"] == "duplicate-1"


def test_aggregator_rejects_reordered_phase_events() -> None:
    events = _complete_trial("reordered-1", 0)
    events[3], events[4] = events[4], events[3]

    report = aggregate_events(events)

    warm_trials = cast(dict[str, object], report["warm_trials"])
    assert warm_trials["valid"] == 0
    invalid_details = cast(list[dict[str, object]], warm_trials["invalid_details"])
    assert invalid_details[0]["trial_id"] == "reordered-1"


def test_aggregator_rejects_incomplete_resource_snapshots() -> None:
    events = _complete_trial("incomplete-resource-1", 0)
    for event in events:
        if event["phase"] == "resource_start":
            resource = event["resource"]
            assert isinstance(resource, dict)
            del resource["pswpout"]

    report = aggregate_events(events)

    warm_trials = cast(dict[str, object], report["warm_trials"])
    assert warm_trials["valid"] == 0
    invalid_details = cast(list[dict[str, object]], warm_trials["invalid_details"])
    assert invalid_details[0]["trial_id"] == "incomplete-resource-1"
    reasons = cast(list[str], invalid_details[0]["reasons"])
    assert "missing_or_incomplete_resource_snapshot" in reasons
