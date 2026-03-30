2026-03-30

Decisions:
- Created branch `fix/installation-tdd` to fix installation and add TDD flow.
- Unit tests will use synthesizer stubs (no heavy dependencies) so CI runs fast.
- Dockerfile added for reproducible CPU-based runtime; E2E tests are manual because models are large.

Next actions:
- Run CI on branch and iterate on install issues (espnet dependencies).
- Run Docker E2E locally and collect generated WAV artifacts.
- If model download issues appear, consider hosting model artifacts on HF.
