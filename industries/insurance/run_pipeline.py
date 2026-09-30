"""Run the whole insurance pipeline in order; stops at the first step that fails."""

import runpy

STEPS = ["clean", "validate", "store", "analyze", "report", "export"]


def run_pipeline(steps: list[str] = STEPS) -> None:
    """Run each step's script exactly as `python -m industries.insurance.<step>` would."""
    for step in steps:
        print(f"\n=== {step} ===")
        runpy.run_module(f"industries.insurance.{step}", run_name="__main__")


if __name__ == "__main__":
    run_pipeline()
