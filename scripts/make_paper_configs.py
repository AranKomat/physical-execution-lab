#!/usr/bin/env python3
"""Generate PDF-track configs without replacing legacy K1/sensor configs."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import atomic_json,file_digest
from prl.dyna.protocol import ARMS,REFERENCE_RESULTS


def main():
    folder=ROOT/'configs/dyna';folder.mkdir(parents=True,exist_ok=True)
    for arm in ARMS:
        d={'track':'pdf_reproduction','backend':'direct_libero','arm':arm,
           'information_profile':'privileged_sim','rpent_root':'external/RPent',
           'cuda_device':0,'mujoco_gl':'egl','settle_steps':10,'record_video':False,
           'geometry_overrides':{},'max_infrastructure_errors':1,
           'checkpoint_id':'REPLACE_public_Physical_Intelligence_pi05_libero_revision',
           'checkpoint_sha256':'REPLACE_WITH_CHECKPOINT_MANIFEST_HASH',
           'policy_attestation':'runs/policy-attestation.json','vla_endpoint':'http://127.0.0.1:8911',
           'settings':{},
           'planner':{'kind':'api','model':'Qwen3-VL-4B-Instruct',
                      'base_url':'http://127.0.0.1:8000/v1','api_key_env':'PRL_API_KEY',
                      'input_token_reservation':30000},
           'call_budget':{'max_calls':150,'max_reserved_tokens':5000000}}
        atomic_json(folder/f'{arm}.template.json',d)
    for arm in ('bare','A2static','A2seq','A2ctrl','unlatched'):
        atomic_json(folder/f'fixture_{arm}.json',{'track':'pdf_reproduction','backend':'synthetic','arm':arm,
            'information_profile':'synthetic','fixture_steps':300,'max_infrastructure_errors':1,
            'settings':{},'planner':{'kind':'fixture'},
            'call_budget':{'max_calls':1,'max_reserved_tokens':1000}})
    atomic_json(folder/'paper_reference_results.json',{'origin':'SOURCE PAPER ONLY — NOT LOCAL MEASUREMENTS',**REFERENCE_RESULTS})
    atomic_json(folder/'paper_spec.json',{
      'source':{'file':'references/2609.40306v1.pdf','sha256':file_digest(ROOT/'references/2609.40306v1.pdf'),
                'pages':37,'title':'DynaHarness: A Dynamic Physical Harness for Self-Evolving Robot Agents',
                'date':'2026-09-30','review':'Full uploaded PDF, main text and Appendices A–I',
                'code_access':'Implementation GitHub URL returned 404 in this revision; not bundled'},
      'facts':{
        'geometry':{'value':'simulator-state geometry in LIBERO; camera-derived scene information on hardware','page':14},
        'planner':{'value':'Qwen3-VL-4B-Instruct, local 4-bit build; symbolic arguments, not poses','pages':[4,5,34]},
        'policy':{'value':'public frozen pi0.5 LIBERO, not piRLinf/fullshot','pages':[5,17]},
        'rates':{'control_hz':20,'governor_hz':2,'safety_hz':50,'joint_velocity_rad_s':2,'pages':[4,14,27]},
        'planner_settings':{'temperature':0.1,'output_tokens':2048,'timeout_s':90,'plan_validity_s':180,
                            'serialization_repair':1,'page':25},
        'budgets':{'spatial':220,'object':280,'goal':300,'long':520,'ticks':600,'pages':[16,25]},
        'ablation':{'A2static':'replan only after nominal success; fixed retries on failures',
                    'A2seq':'initial complete sequence, retry once plus replay/retry; 12 blocked ticks',
                    'pages':[24,25,26]},
        'evolution':{'value':'Eq5 cell-level paired gate plus broader regression; attribution diagnostic, not causal proof','pages':[5,15,32,37]},
        'performance_cause':{'value':'analytic skills supply main competence; initial no-evolution harness underperforms policy','pages':[8,9]},
      },
      'implemented':[
        'separate explicit privileged-simulation reproduction profile',
        'symbolic no-pose planner with 1-step and complete-sequence schemas',
        'matched A2static/A2seq/A2ctrl executor semantics and bounded retries',
        'geometry-aware analytic capability families, slots, corridor, object-to-TCP transport',
        'drawer handle shift, reseat hook, and bounded articulation trajectories',
        'per-suite step limits, affordability, leases, independent completion latch',
        'source-inspected direct LIBERO seam and physics-substep watchdog hook',
        'RPent policy server with 10-action chunk override and live attestation',
        'cell-count Eq5 gate and mandatory broader validation',
        'full-denominator reporting, paired exact test and task-cell bootstrap',
      ],
      'remaining_qualification':[
        'No native LIBERO episode or learned-policy inference has run in this environment.',
        'Exact paper skill source, seven removal IDs and six recovery IDs are not enumerated in the PDF.',
        'Exact grasp/site/joint mappings, motion gains, sensor resolution and completion tolerances need native qualification.',
        'Exact original checkpoint hash, normalization, diffusion sampler, quantization, prompt and seed control remain unverified.',
        'Official reset indices 21–40 are specified; author block C generation/state files are unavailable.',
        'Reset settling, governor stall thresholds, command lease duration and local verification are reconstruction settings.',
        '50 Hz substep hook is implemented but not natively tested; no hardware safety claim.',
        'Exact ordered 13 diagnostic checks are not supplied. Local taxonomy is explicitly reconstructed.',
        'Probe archive contains physics only, not full controller/RNG/governor checkpoint; exact branch replay is not qualified.',
        'A2static fixed retry count is reconstructed from explicit A2seq description plus A2static prose; exact A2static source still needed.',
      ],
      'paper_results_reproduced':False})
if __name__=='__main__':main()
