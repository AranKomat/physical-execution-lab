# Source audit — v0.4

Source inspected on 2026-10-01 through the GitHub connector and official OpenAI
documentation. These are interface findings, not results from running upstream
simulators/models. Direct Git network access was unavailable on the build host.

## Native environment and controller

[GPT-as-Policy @ 8f3d362b077d8efb77e2a7274d5b2c20e2243846](https://github.com/anonymous-report-421/GPT-as-Policy/tree/8f3d362b077d8efb77e2a7274d5b2c20e2243846)

Read `hybrid_rollout/robodojo/robodojo_server/{server,session,rpc,kinematics,client}.py`,
`pi05_server/client.py`, and `evaluation.py`. Earlier context also supplied the
source action contract, gate, checkpoint identity and public case metadata.

- Reset only once per source server; eval_seed is the layout group, not reset ID.
- Source registers native reward/completion conditions before acting. Empty lists
  cannot count as success.
- RGB3 plus measured arm joint/EEF state. Gripper opening is a controller command.
- Mutating calls bind episode and current native step. No automatic replay.
- Joint actions14; EEF targets link6, environment-origin metres, wxyz.
- DLS target must contain boolean `gripper_closed`; optional continuous opening is
  separately preserved. Near-unit quaternions are normalized at our boundary.
- FK preview strictly requires H50; our pure-FK compatibility shim is documented
  and drops padded outputs without stepping physics.
- Partial score is read only from final evaluator output, never actor context.
- π0.5 server has H50/dim14/OpenPI-JAX identity and monotonic inference numbering.

## Motor adapters

[XPolicyLab @ 408b99d959a7b2207f5f785528fefcc019d7b131](https://github.com/XPolicyLab/XPolicyLab/tree/408b99d959a7b2207f5f785528fefcc019d7b131)

Read `model_template.py`, G05 model initialization/interface, Xiaomi model state
and action conversion/inference interface, and Intern model plus `_adapter_base.py`.

| Source | Kept | Not inferred |
|---|---|---|
| G05 | Model update_obs/get_action/reset, FM source,16-step configuration, source frequency30 | No ms/inference or faster-than-Intern claim |
| Xiaomi | Source relative→absolute dual-EEF decoding, joint-state input,30-prefix configuration | EEF cannot be treated as joint14; DLS is our explicit controller variant |
| Intern | Stateful pending ACK accounting,32/10 model/replan horizons,10denoise,25Hz | No fake ACKs, no steady-state timing inferred from cold/reset replay |

Benchmark weights/ancillary encoders are not included. Their licenses/access
conditions must be checked independently. All providers require concrete local
artifact hashes before normal native evaluation.

## RoboCasa365

[Xiaomi @ 0dd7aef8dc87296246aae812a1f59ccb708e5546](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1/tree/0dd7aef8dc87296246aae812a1f59ccb708e5546)

Read `eval_robocasa365/README.md` and `entry.py`.

- Official client/server and preprocessing imported rather than rewritten.
- EE-first14 state→official60 padding; three camera histories4/interval2.
- Crop.95; native controller action12;16 actions/query.
- Task registry order and global seed formula preserved.
- Reference source uses **pretrain kitchen split**, target50 task set,50trials/task,
  seed7. Published code-run1432/2500 is not relabeled as57.4%.

[RoboCasa @ 456174f62b89b8fca99eaaf33949c29fec9cfc2a](https://github.com/robocasa/robocasa/tree/456174f62b89b8fca99eaaf33949c29fec9cfc2a)

Read `robocasa/utils/env_utils.py` and `robocasa/wrappers/gym_wrapper.py`.
Controller values are not world metre poses. Robot base-relative observations
must not be combined with K1 world coordinates without a qualified transform.
Our teacher corrections are bounded arm-only normalized commands; mobile-base
correction and depth-tool porting are not claimed.

## Model API

[GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
requires Responses for tool calls; none/minimal reasoning are unsupported.
[Flex](https://developers.openai.com/api/docs/guides/flex-processing) is an
explicit service tier with latency/capacity trade-offs. Standard (`default`) and
Flex are not different model architectures. Actual served-model/tier fields are
archived. No silent fallback or automatic retry is implemented.

## Novel vs reused

Native local DLS/OSC, RGB/proprio sensors, FK, source model inference,
within-episode progress and outcome/intent checks are not newly invented here.
The proposed comparison adds a common multi-policy execution boundary, scheduled
plus event-triggered supervision, bounded direct execution and matched reporting.
It has not established that those changes improve physical performance.

No task-specific analytic library, privileged simulator grounding or DynaHarness
headline replication is part of this v0.4 experiment. K1's source and prior
RGB-D/local-execution integration remain in the legacy lane.
