# Submitted agent trajectories

These are the representative trajectories for the final evaluation. Every
line is one step of the run: the assistant's instruction, the tool it
called, the tool's response, and any human checkpoint.

How to read a trajectory:

```
{"role": "assistant", "content": "{\"action\": \"read_file\", ...}"}   <- what the agent asked for
{"role": "tool",      "content": "<tool output>", "tool": "read_file"} <- what the tool returned
{"role": "human",     "content": "HUMAN CHECKPOINT: ..."}              <- operator checkpoint
```

| File | Case | Why it is representative |
|---|---|---|
| `agent_final_orchestrated/case_009_hour_shift_bucketing.jsonl` | Challenging: cross-module hour shift | Full pipeline: triage → logs → 3 modules traced → legacy `+1h` adjustment found in `bucket.py` → fixed → verified. Includes the human checkpoint. |
| `agent_final_orchestrated/case_001_timezone_payments.jsonl` | Naive/aware datetime crash | Shows a failed first fix attempt caught by the verification loop, then a correct second attempt. |
| `agent_final_orchestrated/case_006_encoding_latin1.jsonl` | Encoding crash | Investigate-by-tools: agent inspects the data file bytes and the loader before fixing. |
| `agent_final_orchestrated/case_007_float_precision_tax.jsonl` | Half-cent rounding | Multiple hypotheses examined, rejected ones visible in the ledger, fix verified on all 12 tests. |
| `baseline_deepseek_v2/case_001_timezone_payments.jsonl` | Baseline (manual process) | Correct diagnosis, un-applicable patch — the bottleneck the solution removes. |

All runs (including the cross-model Gemini run and the mock infra test)
remain under `trajectories/runs/` for completeness.
