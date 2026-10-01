# Third-party sources and attribution

This distribution contains original extension code and documentation. It does not bundle K1, RPent, LIBERO assets, datasets, model weights, closed-source agent implementations or provider credentials.

- **Robo-Harness K1** — https://github.com/Robo-Harness/k1, expected revision `ee46363101fcf3ef87182fb2dbad99a92ce77fc0`. Upstream MIT license. Our extension calls its registry, sensor tools, native adapters and `run_agent` entry point. We inspected public source to align the interface; these are not our inventions.
- **LIBERO-PRO / Zxy-MLlab** — https://github.com/Zxy-MLlab/LIBERO-PRO, revision `eafdb809426b13153aa1e4c42d6601844217dfec`. Source, simulator, data and asset rights remain upstream. Read the exact release licenses before use/distribution.
- **RPent / RLinf / openpi** — https://github.com/RLinf/RPent, https://github.com/RLinf/RLinf, https://github.com/RLinf/openpi. The inspected RPent client/server source is Apache-2.0. Related model, simulator, dependency and checkpoint terms remain separate. No task-memory corpus is downloaded.
- **FLUX 3 Action** — https://github.com/black-forest-labs/flux-action. Only a documented recorded-observation CLI invocation is provided. No FLUX source/weights or implicit license grant is included; check each checkpoint's terms.
- **SAM3, TAPNext++, GraspGen, RATs/CaP-X** — optional or future upstream dependencies used by K1. They are not installed or redistributed by this package.
- **DynaHarness, Harness VLA and Robo-Harness K1 papers** — methodological references in the handoff. Our code does not claim to be their official implementation or to reproduce their published numbers.

Model/API services are user-selected and subject to their own terms. GitHub links and model names are attribution, not affiliation or endorsement.


## v0.4 source-interface additions

This package adds independent wrappers against pinned GPT-as-Policy, XPolicyLab,
Xiaomi-Robotics-1 and RoboCasa interfaces. Their source repositories, models and
assets are not bundled. Source contract findings and exact revisions are listed
in `docs/multibench/SOURCES.md`. Upstream code retains its own license; model
weights and benchmark assets require separate access/license review.

No fonts or paid credentials are included. Synthetic fixture data and our new
wrappers are not official benchmark datasets or author model outputs.
