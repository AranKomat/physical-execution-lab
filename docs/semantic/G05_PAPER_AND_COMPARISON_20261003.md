# G0.5 Paper Review And Next Comparison

## Decision

The owner requested G0.5 alone versus G0.5 with sparse GPT-6 subtasks, rather
than using more GPT calls to compensate for a poorly steerable motor model.
GPT keeps the original task; the candidate motor prompt is the current subtask
alone, falling back to the original instruction until one is issued. Semantic
recovery remains enabled under the existing failed-only gate, now explained
explicitly in the planner prompt/schema. Uncertain replanning may use ordinary
set_subtask subject to minimum dwell; uncertainty is never converted to failure.

These are opened ten-task screens, not untouched-task phase E qualification or
official per-task success-rate estimates. Both conditions are frozen before
their outcomes. Native source predicts H32, exposes/executes 16 actions at
25 Hz; model configuration frequency30 remains disclosed. Semantic review
target100 is checked at the next drained H16 boundary (normally step112).
No numeric intervention, source-history reset, task recipe, training, added
camera, target crop or bounding-box conditioning is introduced.

## What The Paper Actually Supports

Source: [G0.5 paper, arXiv:2608.11739](https://arxiv.org/pdf/2608.11739),
especially sections 3.2, 4, 5.5 and 5.6, Table5 and Figure11. Its foundation
model starts from Qwen3.5-2B. A smaller backbone does not by itself establish
weak robotics instruction following: data, objective, embodiment adaptation and
action-conditioning interface matter.

G0.5 natively trains intermediate subtask text, object boxes, traces and action
hints in an autoregressive stream. This is distinct from simply putting an
external planner's text in a flow-matching policy's task field. Section5.6
also supplies per-stage natural-language instructions at runtime; native
reasoning is not a replacement for all high-level stage management.

Under one pretrained R1-Lite checkpoint, AR+reasoning improves five-stage
progress: Air Fryer2.4 to3.8; Cook Bacon1.5 to3.4. FM gains are smaller:
2.1 to2.7 and1.2 to2.0. The long-horizon probe uses five rollouts per cell,
not RoboDojo or the downloaded FM-only specialist checkpoint. The authors
hypothesize stronger coupling between native reasoning and AR actions; that
mechanism is not proved by the reported observations.

Table5, the R1-Lite pick/place referring-context ablation:

| Context | Language Following | Task Success |
|---|---:|---:|
| Name only | 84.4% | 75.0% |
| Added box-coordinate text | 85.9% | 76.6% |
| Added target visual crops | 98.4% | 84.4% |

The adjacent prose says coordinate text does not improve over name-only,
whereas the table shows small positive differences. Preserve that discrepancy;
do not describe coordinates as a demonstrated large gain or degradation.
The large reported gain is from appended visual target context, not numeric
boxes alone. These gains do not transfer automatically to our checkpoint.

The deployed RoboDojo provider is FM-only (`action_source=fm`, discrete-action
generation disabled). Native subtask/box generation and an AR action head have
not been qualified here. A failure in this external-language screen therefore
cannot refute the paper's AR-plus-native-reasoning result.

## Bounding Boxes And GPT Frequency

Sparse GPT-6 target identification could become a useful separate grounding
factor, particularly when errors are about which object rather than mechanics.
Do not pass a box as an arbitrary task-field annotation and assume the policy
uses it. First establish the released checkpoint's supported target-context
interface. If target crops are supported, derive them only from legal camera
pixels, preserve camera/coordinate identity, and compare as a new sensing/
conditioning condition. Never replace a wrist camera with a target crop.

GPT choosing meaningful stages while a capable local policy grounds objects
and executes continuously remains the intended division of labor. More
frequent GPT decisions are not the default remedy for ineffective conditioning.
Explicit-context post-training is a plausible later remedy, not something
this single-screen comparison can prove necessary.

## Checklist

- [x] Read the paper's relevant methods and ablations, including the rendered
  Table5 page; distinguish foundation/R1-Lite results from the FM-only deployment.
- [x] Restore the isolated GPU-host G05 environment from retained package versions;
  Python3.10.18 is a disclosed difference from the earlier3.10.19 environment.
  No model weights were downloaded to the Mac or system packages changed.
- [x] Implement shared source-fused B10 inference with unique cohort/task IDs,
  actual model-token-boundary retention checks and native H16 ACK routing.
- [x] Clarify recover/failed versus ordinary uncertain replanning; keep gates intact.
- [x] Freeze original-only and subtask-only/recovery conditions before outcomes.
- [x] Complete/audit original-only across ten distinct tasks concurrently.
- [ ] Independently verify the complete local original-only backup.
- [ ] Complete/audit/back up the separate semantic candidate under existing budgets.
- [ ] Review actual goal epochs and physical behavior; report scores with coverage,
  censoring, latency, GPT calls/cost and all negative outcomes.
- [ ] Decide whether a target-grounding or native-reasoning condition is justified
  by failures and the actual released interface, rather than a prompt sweep.

Fused sampling uses one source seed0 RNG stream, not independent per-environment
streams or demonstrated singleton numerical parity. Inference-only padding
keeps B10 as tasks retire; padded rows never execute or count as task actions.
Source observation history is explicitly restricted to one frame; arbitrary
recurrent motor models are not qualified by this extension.

First baseline001 stopped during setup before any policy prediction/action:
the copied provider's external/env_cfg alias was absent on the new host, not
changed model weights. Restoring the alias to retained RoboDojo files verified
all three original ancillary hashes exactly; no source config was rewritten.
The separately named baseline002 uses the same frozen motor condition and the
previously successful simulator-only libstdc++6.0.36 preload. Keep baseline001
as infrastructure evidence, not ten physical failures or a scored retry.

## Original-Only Result And Active Candidate

Baseline002 reached all ten native terminal states: five successes, five
failures, mean native score0.62, 8,182 actions and516 motor predictions in
790.30 seconds including startup. Its82 fused batches included real B10;
warm full-B10 median was2.086 seconds. Prompt routing, source predictions and
native ACK audit passed, with no controller errors or unstable environments.
Successes: tower, folding, Kong, classification and bottles. Failures: number
arrangement0.15, language classification0, imitation0.05, table0.75, packing0.25.
These are one attempt/layout per opened task, not official RoboDojo SR.

Subtask-only/recovery001 is running with GPT-6.1 Sol/medium, Flex preferred
and the approved same-model Standard capacity fallback; $3 local/$95 shared
reservation caps remain. The original pre-outcome freeze is retained. Adding
only the offline semantic audit/renderer required a fresh source snapshot
`7c4f42c2344fca33f8ed5be4166e5c570b972a6dd909d2803b2f173f08d3f468`;
the frozen comparison conditions and baseline-admission core are unchanged.
Do not report candidate performance until it reaches an authoritative outcome.
