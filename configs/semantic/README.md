# Semantic configurations

Do not duplicate old provider paths or invent checkpoint hashes here. Generate four fresh named conditions from one already-working bound motor-only configuration:

```bash
python run_semantic.py prepare --from-config /absolute/working-motor.json \
    --output configs/local/semantic-pi05 --max-calls 32
```

Generated conditions: motor original-only, GPT shadow original-only, task-plus-subtask hierarchy, subtask-only hierarchy. All share the same policy configuration. The new server must use `run_semantic.py serve-policy`; an old provider cannot silently receive the added context.

Optional later variants are ordinary **new config files**: enable `semantic_schedule.allow_semantic_recovery`, or change `review_interval_steps` to compare semantic review frequency while keeping native policy prefixes unchanged. Freeze them separately.

No generated config is approved for native use by its presence. Preserve the user's authorized Flex-only route and external account budget ledger. Missing source assets, native qualifications and tokenizer checks remain explicit gates.
