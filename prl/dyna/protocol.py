"""Numerical protocol transcribed from the attached PDF; gaps are explicit."""
from dataclasses import dataclass, asdict
from ..errors import ValidationError
from ..util import finite, integer, digest

PAPER_SUITES = ('libero_goal_task', 'libero_goal_swap', 'libero_10_task', 'libero_10_swap')
SUITE_STEPS = {'libero_spatial': 220, 'libero_object': 280, 'libero_goal': 300, 'libero_10': 520}
ARMS = ('bare', 'A2static', 'A2seq', 'A2ctrl', 'no_contact', 'no_recovery', 'no_groups', 'no_vla', 'unlatched')


def suite_budget(suite):
    for name, value in SUITE_STEPS.items():
        if suite == name or suite.startswith(name + '_'):
            return value
    raise ValidationError(f'unknown_paper_suite:{suite}')


@dataclass(frozen=True)
class PaperSettings:
    # Explicit in Sec 3 / Appendix D.1.
    control_hz: int = 20
    governor_hz: int = 2
    safety_hz: int = 50
    joint_velocity_rad_s: float = 2.0
    max_ticks: int = 600
    planner_temperature: float = 0.1
    planner_max_tokens: int = 2048
    planner_timeout_s: float = 90.0
    plan_validity_s: float = 180.0
    serialization_repairs: int = 1
    blocked_ticks: int = 12
    policy_chunk_actions: int = 10
    policy_command_actions: int = 20
    # Exact command lease and monitor thresholds are NOT enumerated in the PDF.
    # These are reconstruction defaults, not attributed paper constants.
    command_lease_s: float = 90.0
    episode_wall_s: float = 1800.0
    progress_delta_m: float = 0.001
    stall_ticks: int = 4
    movement_tolerance_m: float = 0.008
    rotation_tolerance_rad: float = 0.06
    grasp_translation_m: float = 0.018
    release_tolerance_m: float = 0.020
    jaw_span_m: float = 0.080
    minimum_clearance_m: float = 0.030
    wrist_ramp_steps: int = 4
    drawer_handle_shift_m: float = 0.020  # Appendix D.4
    drawer_reseat_enabled: bool = True
    max_geometry_age_steps: int = 10
    max_planner_calls: int = 80  # independent infrastructure ceiling
    policy_enabled: bool = True
    # Counts approximate observed stage costs, NOT fitted controller gains.
    pick_place_budget_floor: int = 230  # approximate whole-command cost, Table 4
    approach_steps: int = 30
    descend_steps: int = 30
    close_steps: int = 10
    lift_steps: int = 23
    carry_steps: int = 70
    lower_steps: int = 15
    release_steps: int = 10
    retreat_steps: int = 23

    def __post_init__(self):
        for name in ('control_hz','governor_hz','safety_hz','max_ticks','blocked_ticks',
                     'policy_chunk_actions','policy_command_actions','max_planner_calls',
                     'approach_steps','descend_steps','close_steps','lift_steps','carry_steps',
                     'lower_steps','release_steps','retreat_steps','stall_ticks','wrist_ramp_steps'):
            integer(getattr(self, name), name, 1)
        if self.control_hz % self.governor_hz:
            raise ValidationError('governor_must_divide_control_rate')
        for name in ('command_lease_s','episode_wall_s','plan_validity_s','joint_velocity_rad_s',
                     'progress_delta_m','movement_tolerance_m','rotation_tolerance_rad',
                     'jaw_span_m','minimum_clearance_m'):
            finite(getattr(self, name), name, 1e-9)
        integer(self.max_geometry_age_steps, 'max_geometry_age_steps', 0)
        integer(self.serialization_repairs, 'serialization_repairs', 0, 1)

    @property
    def decision_stride(self):
        return self.control_hz // self.governor_hz

    @property
    def pick_place_cost(self):
        return sum(getattr(self,n+'_steps') for n in
                   ('approach','descend','close','lift','carry','lower','release','retreat'))

    @property
    def fingerprint(self):
        return digest(asdict(self))


# These are PAPER RESULTS for comparison, never emitted as a local run.
REFERENCE_RESULTS = {
    'development': {'episodes':800, 'state_indices': list(range(21,41)),
                    'final_archived':594, 'A2ctrl':592, 'A2static':511, 'A2seq':510,
                    'no_contact':133, 'no_recovery':585, 'no_groups':126, 'bare':130},
    'new_states_C': {'episodes':800, 'champion':602, 'bare':140,
                     'comparison':'post-selection initial-state transfer, not new task families'},
    'early_no_evolution': {'episodes':800, 'state_indices':list(range(1,21)),
                           'harness_percent':13.9, 'bare_percent':17.1},
    'paper_checkpoint':'public pi0.5 LIBERO; NOT RLinf/pi05_libero130_fullshot',
    'slow_model':'Qwen3-VL-4B-Instruct; Appendix G describes a local 4-bit build',
}
