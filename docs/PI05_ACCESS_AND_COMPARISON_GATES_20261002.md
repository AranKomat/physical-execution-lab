# Exact Pi0.5 Access And Comparison Gates

This is the provisioning snapshot. The runtime and first complete native episode
now pass; see [the pi0.5 native pilot](PI05_NATIVE_PILOT_20261002.md). Remaining
screen/timing work and the paid-lane limitations are not closed by provisioning.

## Checkpoint Provisioned

The exact RoboDojo pi0.5 access blocker is resolved. The public dataset
`RoboDojo-Benchmark/RoboDojo`, pinned revision
`35efbc7dedfdbeeb6e95fb749bd885d73d483e41`, contains
`ckpt/RoboDojo/Pi_05/RoboDojo-sim-arx_x5-joint-0/59999`.
Only 18 inference files were downloaded: params, the `arx_x5_sim` normalizer,
and checkpoint metadata. Total size is 12,440,992,402 bytes. Every file's size
and SHA-256 matches the publisher metadata; no optimizer state, other seed,
generic checkpoint or task demonstration was downloaded.

The donor's checkpoint identity algorithm over params/assets yields
`d15fb8bd1d29cb30b69f01b71c66596cb0293c1a8a94111b343c1580dd3e3e5b`,
exactly its `SOURCE.json` recorded previous-load identity. This is distinct from
the harness's artifact-manifest identity, which has a different scope.
Public metadata: `docs/evidence/pi05-provision-001.json`.
Large weights remain on the GPU host, not in Git or on the Mac.

The reproducible downloader is `scripts/multibench/provision_exact_pi05.py`.
An initial base-environment invocation lacked huggingface_hub and downloaded
nothing. The existing G0.5 FLA environment completed downloading; verification
then exposed Python 3.10's lack of hashlib.file_digest. Streaming SHA-256 fixed
that compatibility issue, and the next invocation verified the existing files.
No native robot action or paid API call occurred during provisioning.

## Native Runtime Is Still Missing

Current host import checks found no OpenPI/JAX in the six harness/model
environments or the RoboDojo conda environment. The older bring-up statement
that an OpenPI/JAX runtime was installed does not describe the current host.
The vendored XPolicyLab Pi_05 source contains the exact named training config;
use its pinned installation/runtime contract, not the unrelated K1 RLinf OpenPI
pin. Provision an isolated runtime, verify checkpoint load and real inference,
then run one complete native development episode. Artifact access alone does
not close Stage A or the pi0.5 part of Stage B.

## Paid Lane And Direct Budget

Read-only ledger recheck: 4537 reservations, $75.934460744300 spent plus holds,
$9.065539255700 remaining under $85. The unresolved Sol reservations are
`g05-sparse-sol-flex-dev-001-0`, `g05-sparse-sol-flex-dev-002-0`, and
`xr1-supervision-kettle-001-1`. The ledger blocks new reservations without
explicit acknowledgement; all cost holds remain charged. No retry or tier
fallback was performed. A user preference question about remaining Flex-only
versus a separately labeled Standard comparison is pending.

The direct-dense template permits 180 decisions of at most five actions:
at most 900 native actions. Tower's 1050-step limit requires at least 210 such
decisions; sorting's 1100 requires 220. Early success remains possible, but
equal call budgets are not equal attainable action horizons. The planner now
records this bound per direct job, without silently changing budgets. Wall,
cost, token limits and early target-arrival checks can further reduce execution.
Before interpreting the dense/sparse result, explicitly select resource-limited
or full-horizon evaluation and budget the actual comparison accordingly.

Planner/downloader source changes invalidate the older code fingerprint in
the XR1 motor-only freeze. Native controller qualification itself is unchanged;
regenerate and verify the freeze before any scored run. No held-out case was
opened during this update.
