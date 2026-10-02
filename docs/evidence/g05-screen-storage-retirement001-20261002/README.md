# Verified Duplicate Sensor Retirement

The idle GPU host had3.8 GiB free. Full native NPZ copies for four historical
G0.5 screen episodes were already retained locally. The included operator
rehashed all local files into the included manifest, checked native-completed
results, then preflighted every corresponding remote file and byte count before
deleting anything. Remote result hashes had to match the local result hashes.
Only `native/<episode>/observations/<step>.npz` was eligible. All other files,
models, assets, environments and unrelated CPU workload were left untouched.

| Episode | Retired Duplicate Files | Bytes Freed |
|---|---:|---:|
| g05-screen-sort-l1 | 1101 | 1745998076 |
| g05-screen-sort-l2 | 1101 | 1729413021 |
| g05-screen-tower-l0 | 719 | 1212612458 |
| g05-screen-tower-l1 | 730 | 1231777244 |
| Total | 3651 | 5919800799 |

Both dry-run and applied operator output confirmed the same3651 files and
5919800799 bytes. Manifest SHA256:
`a99c661c073236f553525f2aa9961082d63e87228db9529b8143ec9c0fe86dd3`.
Per-run remote records remain in `verified-duplicate-retirement001.json`.
Full sensors remain under local `runs/native-evidence/<episode>/native/`;
do not delete those local copies. Remote controller captures, actions, videos,
scores and bindings remain. No data or model weights were downloaded for this
operation. Newer unique vector/reference sensors were not retired.
