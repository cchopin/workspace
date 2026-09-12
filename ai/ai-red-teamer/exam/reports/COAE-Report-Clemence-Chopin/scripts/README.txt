PhantomKernel Offensive AI Assessment - reusable exploitation scripts
Run from the repo root with the project venv (.venv/bin/python). Targets in scope only.

  Finding 1  mcp_exfil.py         MCP command-injection blind time-based oracle (--selftest / --cat PATH)
  Finding 2  www_task5_admin.py   NeuraCore SQL-injection guardrail bypass -> website admin takeover
  Finding 3  tf_poison.py         IdentityGate analyst-override label-flipping data poisoning
  Finding 4  www_task6_secret.py  SysMind indirect prompt injection -> /secret_data.txt disclosure
  Finding 5  www_task4_support.py KernelGate prompt-injection API-key leak -> support takeover
  Finding 6  pp_badge.py          PassPort adversarial badge crafting (PGD); then POST to /passport/api/scan
  Finding 7  od_ensemble.py       OmniDigit ensemble adversarial OCR tile crafting (od_label.py = surrogate labeler)

LLM-driven steps (Findings 3,4,5, and the SQLi in 2) are non-deterministic - re-run if a step does not succeed first time.
