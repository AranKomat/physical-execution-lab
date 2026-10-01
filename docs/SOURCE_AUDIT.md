# Source audit — PDF revision

Primary source is the uploaded complete37-page **2609.40306v1.pdf**. The previous
project-page-only audit is archived in `docs/legacy/`. `docs/PAPER_FIDELITY.md` is
the authoritative current source-to-code map.

Additional live source inspections used for implementation, not to replace the paper:

| Repository / source | Pinned revision / path | Relevant finding |
|---|---|---|
| RLinf/RPent | `d2595ff270c7d66dbb2effb803f5e6d4d8e08f82`, `rpent/robots/components/pi05_vla_server.py` | LIBERO preset defaults to5-action chunks; explicit10-action override needed. |
| RLinf/RPent | same, `pi05_vla_client.py` | Encoder expects unbatched image/state input and returns `[chunk,7]`. |
| RLinf/RLinf | `88f9867ff5b3004b482d6788a871081a43098620`, `rlinf/envs/sim/libero/libero_env.py` | PRO package aliases, environment setup and processed observation context. |
| RLinf/RLinf | same, `utils.py` | Policy RGB rotates180°; preserve this separately from calibrated/display frames. |
| RLinf/LIBERO-PRO | `d1e11fb181b8544487d27742c0caa3a4d46452ad`, `liberopro/liberopro/envs/env_wrapper.py` | Direct native reset/state/success interfaces; robosuite1.5 composite controller. |
| RLinf/LIBERO-PRO | same, `bddl_base_domain.py` | Object/fixture/site dictionaries available; geometry need not read task goal clauses. |
| DynaHarness | `https://github.com/Denghaoyuan123/DynaHarness` | Public contents returned404; no implementation downloaded. |

The build container cannot resolve direct GitHub DNS and has no MuJoCo/RPent
installation. Source text was inspected through the GitHub connector. A failed
network clone is not represented as a successful vendoring or native execution.

No third-party source is copied wholesale into this revision. The existing lockfile
preserves inspected commits; native dependency solving and execution remain work
for the external GPU agent. The attached paper is included solely as user-provided
research context, not relicensed under this repository's software license.
