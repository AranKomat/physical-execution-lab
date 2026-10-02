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
