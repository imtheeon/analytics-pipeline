import runpy

import pytest

from industries.insurance.run_pipeline import run_pipeline


def test_runs_steps_in_order_and_stops_on_failure(monkeypatch):
    ran = []

    def fake_run(module, run_name):
        ran.append(module.rsplit(".", 1)[1])
        if module.endswith("validate"):
            raise ValueError("Validation failed")

    monkeypatch.setattr(runpy, "run_module", fake_run)
    with pytest.raises(ValueError):
        run_pipeline()
    assert ran == ["clean", "validate"]
