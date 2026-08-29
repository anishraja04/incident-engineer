# Submitted trajectories

These are the agent and baseline runs for the final evaluation. Every line
is one step: the assistant's instruction, the tool it called, the tool's
response, and any human checkpoint.

How to read a trajectory:

```
{"role": "assistant", "content": "{\"action\": \"read_file\", ...}"}   <- what the agent asked for
{"role": "tool",      "content": "<tool output>", "tool": "read_file"} <- what the tool returned
{"role": "human",     "content": "HUMAN CHECKPOINT: ..."}              <- operator checkpoint
{"role": "triage",    "content": "TRIAGE SUMMARY: ..."}                <- triage agent hypotheses
```

## Final runs

| Folder | What it is | Why it matters |
|---|---|---|
| `agent_final_orchestrated/` | **Final agent** (triage + investigator, all 11 cases) | The submission's headline evidence: 11/11 with full trajectories. |
| `baseline_final_v3/` | **Final baseline** (manual process, all 11 cases) | 0/11 - the honest starting point. |
| `agent_flashlite_2cases/` | Same agent on **Gemini 3.1 flash-lite** (2 sampled cases) | Model-agnostic evidence. |

## Iteration evidence (referenced by the changelog)

| Folder | What it is |
|---|---|
| `control_fullsource_baseline/` | The **removed control experiment**: baseline given the full source in one prompt -> 11/11. Proves the cases are solvable and fair; removed because it left no improvement to measure. |
| `agent_deepseek_v1/` | Agent v1 (basic tool loop, unbounded context) |
| `agent_deepseek_v2_compaction/` | Agent v2 (bounded evidence ledger) |

Summary files (cost, steps, tokens) sit next to each trajectory folder;
aggregate results are in `eval/results/`.