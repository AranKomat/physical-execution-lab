# Physical Execution Lab · Semantic Hierarchy v0.5

**New experiment:** GPT supplies a language subtask; the frozen motor policy keeps its normal action cadence. No task-specific skill scripts and no exploration-memory recipes.

Read **`HANDOFF_V5.md`** for the self-contained design, source references, implementation and experiment sequence. Give **`TAKEOVER_V5.md`** to the external coding agent.

## Existing live project: apply new files only

The archive's legacy `k1lab/` files are the previous v4 CPU baseline, not a current GitHub clone. The current live repository was inspected at `dc2e704064bc8e997f64d7978bb9714e995e65f2`. Use a separate live worktree and the additive installer:

```bash
python scripts/semantic/apply_overlay.py --target /path/to/live-worktree
python scripts/semantic/apply_overlay.py --target /path/to/live-worktree --apply
```

It does not overwrite native fixes or prior experiment evidence. Do not extract the full ZIP over the active GPU checkout.

## Standalone CPU demo

```bash
python -m pip install -e '.[test,multibench]'
python -m pytest -q
python run_semantic.py synthetic --output runs/semantic-demo
```

Open `runs/semantic-demo/report.html`. These are synthetic software fixtures, not robot benchmark gains.

Implemented: language-context contracts, three prompt modes, source-specific policy conditioning, shadow/motor/hierarchy conditions, ACK-preserving prefix execution, semantic planning client, source/config freezes, reporting, tests, and additive deployment.

Not demonstrated here: GPU/tokenizer qualification, native task improvement, live API execution, trained π0.7 capability, or asynchronous physical operation. See `docs/semantic/STATUS.md`.
