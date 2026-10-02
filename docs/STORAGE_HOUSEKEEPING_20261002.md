# GPU Host Storage Housekeeping

Host: current two-4090 instance. Filesystem capacity: 372 GiB as reported by df.
Free space before housekeeping: approximately 3.7 GiB; afterward approximately
20 GiB, while the current sorting experiment produced new evidence.

## Removed

- Pip package-download HTTP and wheel caches. The old project pip recognized
  only its legacy cache (48 files); the newer Miniconda pip then removed 2590
  files/7320.7 MB from the newer cache format.
- Unused uv cache entries via the official `uv cache prune` command: 95735
  files/23.3 GiB logical removal. Actual filesystem reclamation is smaller
  because cache files shared hard links with installed environments.

No package installation was running at the inspection. No install, upgrade,
driver change, reboot or rental change occurred. The installed environments,
model artifacts, benchmark assets and retained experiment evidence were not
deleted. The live sorting rollout continued and terminated by semantic
abstention, not a storage or controller fault.

## Retained Large Consumers

| Location | Approximate Allocated Size At Inspection |
|---|---:|
| external/XPolicyLab | 127 GiB |
| external/RoboDojo | 66 GiB |
| external/RoboCasa | 23 GiB |
| model-artifacts | 33 GiB |
| runs | 29 GiB |

RoboDojo's `.cache/robodojo_assets_repo` is its actual asset store, not a
disposable download cache. XPolicyLab's G05 checkpoints account for about
88 GiB and InternW0-Delta for about 29 GiB. These were left intact. Their
training/inference assets may offer future deduplication opportunities, but
only after checking bindings, exact byte identity and model dependency paths.

Keep the existing per-episode free-disk preflight and SHA-verified local backup
before retiring redundant remote observations. Do not automatically purge
benchmark or Hugging Face model caches by directory name.

## Local Duplicate Retirement

The incomplete local sorting1 GPU1 candidate directory contained 611 NPZ
files also present in its complete compressed backup. The archive digest and
all 1,658 original file hashes were reverified, then only individually
checksum-matching duplicates were retired, freeing 964,896,121 bytes.
Archive SHA256: `7e683059561226a2f1f95ad51ee123048a982c01694eaf85ab5dba68b584ca22`.
The verified archive, metadata and remote source were retained. The local
per-file directory is intentionally incomplete; use the verified archive
when retrieving full evidence. No unique historical payload was deleted.

The sorting2 subtask-only full archive was also verified locally: all 1,853
files and archive digest `2ed3205a2d6c326dd3fcf11ded7fbd1422ce9698b9f706d8d2af51f7c0ed7e5b`.
Only 841 checksum-matching remote native sensor NPZ duplicates were then
retired, reclaiming 1,323,182,609 bytes. Remote controller captures, action
journals, model proposals, results and bindings remain. The exact retirement
manifest is published with that episode's evidence; full historical sensors
are recoverable from the local archive, not the retired remote directory.
