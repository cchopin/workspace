# HTB Support — AI Privacy module, "DP-SGD Challenge" grader rejects the official walkthrough solution

**Module:** AI Privacy (Job Role Path: AI Red Teamer / COAE)
**Section:** DP-SGD Challenge (interactive, section id 4086)

## Summary
The `/validate` grader on this challenge's spawned target rejects a model that follows the module's **own official walkthrough recipe exactly**, and appears to be running a different, much heavier evaluation than the one documented in the walkthrough. As a result the section cannot be completed, which blocks reaching 100% path progress.

## What the official walkthrough shows
The "Show Solution" walkthrough for this section trains with:
- `SVHNCNN` (exact required architecture), full SVHN `train` split, `ModuleValidator.fix(model)`
- `optim.SGD(lr=0.1, momentum=0.9)`, `PrivacyEngine(accountant="rdp")`
- `make_private_with_epsilon(target_epsilon=6.0, target_delta=1e-5, epochs=20, max_grad_norm=1.0)`
- `RANDOM_SEED=1337`, `BATCH_SIZE=256`, `DP_EPOCHS=20`

and shows this SUCCESS response:
```json
{"accuracy":0.78, "evaluation_time":6.12, "flag":"{hidden}", "mia_advantage":0.0115, "passed":true}
```

## What the deployed grader actually returns
Reproducing the walkthrough recipe verbatim (verified on both CPU and Apple MPS, seed 1337), the trained model reaches accuracy ~0.785 and ε≈5.99. Submitting it to `/validate` returns, repeatably and on a freshly reset instance:
```json
{"accuracy":0.7766, "evaluation_time":129.68, "mia_advantage":0.0295, "passed":false}
{"accuracy":0.7766, "evaluation_time":280.90, "mia_advantage":0.0295, "passed":false}
```
- Documented pass criteria are accuracy ≥ 55% and mia_advantage ≤ 5%. This model satisfies BOTH (0.7766 ≥ 0.55 and 0.0295 ≤ 0.05) yet `passed` is `false`.
- `evaluation_time` is 130–280 s versus 6.12 s in the walkthrough — the deployed evaluation is ~45× heavier/slower.
- The submitted model has **identical mean confidence on members and non-members (0.945 / 0.945), i.e. no measurable membership leakage**, yet the grader still reports ~0.0285–0.0295. This is consistent with an optimistic threshold-selection bias floor (best-of-N threshold picked and scored on the same finite 2000-sample set), which sits above the effective pass threshold.

## Evidence that it is not a model-quality issue
Eight independently trained models (varying noise/epsilon, an intentionally overfit model, a model trained on the disjoint SVHN `extra` split, and a temperature-scaled model) all returned mia_advantage in the range 0.0238–0.034 and all failed, regardless of actual privacy. The best draw (0.0238) still failed, so the effective threshold is below the grader's own noise floor.

## Request
Please check the DP-SGD Challenge `/validate` grader on the AI Privacy module. It appears to have been updated to a slower evaluation whose mia_advantage floor (~0.028) exceeds the effective pass threshold, so even the module's official solution now fails. Kindly fix the grader or credit the section so the path can reach 100%.

## Environment
- Python 3.11, torch 2.14.0, opacus (RDP accountant), safetensors
- Reproduced on macOS (Apple Silicon, CPU and MPS)
