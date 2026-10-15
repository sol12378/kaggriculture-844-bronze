# Kaggriculture submission candidate — ORTHO V4 mask32

`submission.tar.gz` is a self-contained Kaggle agent archive. It has `main.py`, `LICENSE`, and `NOTICE` at the archive root. The policy retains the Apache-licensed Aurax V7 parent and adds a bounded production action: a ready animal product may be harvested in place of one PASS. The parent market action is preserved.

## Identity

- Archive SHA-256: `b5f82d69f5a5d8a4c377193b9560c31838bee16bebc63a6891e226e6a7797f2e`
- `main.py` SHA-256: `3d6d319ff918fc2da62447a61186094a02eef1b0be075bcd7d928f67247b8e6b`
- Original frozen archive: `../kg_ortho_program_20260922/artifacts/V4_MASK32_submission.tar.gz`
- Source and attribution: `LICENSE`, `NOTICE`

## Evidence and limits

- A fresh 320-game fast validation in `../kg_ortho_program_20260922/validation/V4CP001_SCORE.json` found paired terminal half-win delta `+0.04375` over the parent. The gain came from one of five public opponent families.
- A separate 320-game run with the pinned official engine in `../kg_ortho_program_20260922/official/V4OFF001_SCORE.json` passed the package-equivalence, market-firewall, and local official-champion checks. Its paired terminal half-win delta was `+0.0125`, again concentrated in one family. The independent audit and completed job are in the same `official` directory.
- On 2026-09-30, the copied archive was checked for root files, exact agreement with the copied source files, an `agent` function, Python syntax, and matching hashes. No new match was run for this copy.
- This is a runnable submission candidate, **not** a proven gold or full release-gate winner.

## Kaggle submissions on 2026-09-30

Both archives in this directory were submitted using the Kaggle CLI. At the 00:48 UTC readback, they were the latest two entries and both were `COMPLETE` with an initial public score of `600.0`:

- `submission.tar.gz` (ORTHO V4 mask32): submission `56692403`
- `aurax_v7_submission.tar.gz` (exact public Aurax V7 fallback): submission `56692389`

The official deadline is 2026-09-30 23:59 UTC (2026-10-01 08:59 JST). `COMPLETE` confirms hosted validation; the initial `600.0` is not a settled skill estimate.
