"""Reproducible experiment configurations, not unverified policy speed rankings."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from k1lab.util import atomic_json

MODEL={'transport':'responses','base_url':'https://api.openai.com/v1',
       'api_key_env':'OPENAI_API_KEY','model':'gpt-6.1-sol','reasoning_effort':'medium',
       'service_tier':'default','timeout_s':300,'max_requests':180,'max_output_tokens':2048,
       'max_total_output_tokens':368640,'history_rounds':4,'image_max_edge':480}

POLICIES={
 'pi05':{'backend':'pi05','policy':'pi05','gpt_as_policy_root':'external/GPT-as-Policy',
         'checkpoint_path':'/ABSOLUTE/PATH/RoboDojo-sim-arx_x5-joint-0/59999','port':19114,
         'artifact_dir':'/ABSOLUTE/PATH/NEW_POLICY_ARTIFACTS','native_checkpoint_sha256':None,
         'identity':{'name':'pi05_robodojo','checkpoint_sha256':None,
         'revision':'8f3d362b077d8efb77e2a7274d5b2c20e2243846','action_space':'x5_joint14',
         'benchmark_training':'RoboDojo task/embodiment post-trained','native_hz':25.,
         'execute_steps':15,'prediction_horizon':50,'stateful':False,'preprocessing_id':'gpt_as_policy_openpi_jax_cam3_joint14'}},
 'xiaomi_r1':{'backend':'xpolicylab','policy':'xiaomi_r1','xpolicylab_root':'external/XPolicyLab',
         'gripper_clip':False,'model_config':{'bench_name':'RoboDojo','env_cfg_type':'arx_x5','action_type':'ee',
            'model_dir':'/ABSOLUTE/PATH/Xiaomi_Robotics_1','action_length':30,
            'image_factor':32,'image_max_pixels':160000,'vlm_processor_path':'Qwen/Qwen3-VL-4B-Instruct'},
         'identity':{'name':'xiaomi_r1_robodojo','checkpoint_sha256':None,
         'revision':'408b99d959a7b2207f5f785528fefcc019d7b131','action_space':'x5_eef16_wxyz',
         'benchmark_training':'RoboDojo task/embodiment post-trained','native_hz':25.,
         'execute_steps':30,'prediction_horizon':None,'stateful':False,'preprocessing_id':'xpl_xr1_mibot_to_env_absolute_ee'}},
 'g05':{'backend':'xpolicylab','policy':'g05','xpolicylab_root':'external/XPolicyLab',
         'gripper_clip':False,'model_config':{'bench_name':'RoboDojo','env_cfg_type':'arx_x5','action_type':'joint',
            'eval_embodiment':'robodojo','ckpt_path':'/ABSOLUTE/PATH/checkpoint','action_source':'fm',
            'action_steps':16,'frequency':30},
         'identity':{'name':'g05_robodojo_fm','checkpoint_sha256':None,
         'revision':'408b99d959a7b2207f5f785528fefcc019d7b131','action_space':'x5_joint14',
         'benchmark_training':'RoboDojo task/embodiment post-trained','native_hz':25.,
         'execute_steps':16,'prediction_horizon':None,'stateful':True,'preprocessing_id':'xpl_g05_fm_source_frequency30_native25_to_qualify'}},
 'internw0_delta':{'backend':'xpolicylab','policy':'internw0_delta','xpolicylab_root':'external/XPolicyLab',
         'gripper_clip':False,'model_config':{'env_cfg_type':'arx_x5','action_type':'joint','device':'cuda',
            'checkpoint_path':'/ABSOLUTE/PATH/robodojo.pt','mixed_precision':'bf16',
            'action_horizon':32,'replan_steps':10,'num_inference_steps':10,'action_hz':25.,
            'text_cfg_scale':1.,'negative_prompt':'','rand_device':'cpu','tiled':False,
            'allow_dummy_policy':False,'timing_enabled':True},
         'identity':{'name':'internw0_delta_robodojo','checkpoint_sha256':None,
         'revision':'408b99d959a7b2207f5f785528fefcc019d7b131','action_space':'x5_joint14',
         'benchmark_training':'RoboDojo task/embodiment post-trained','native_hz':25.,
         'execute_steps':10,'prediction_horizon':32,'stateful':True,'preprocessing_id':'xpl_wam_three_view_canvas_actual_ack'}},
 'xiaomi_robocasa365':{'backend':'xiaomi_robocasa','policy':'xiaomi_robocasa365',
         'xiaomi_root':'external/Xiaomi-Robotics-1','checkpoint_path':'/ABSOLUTE/PATH/Xiaomi-Robotics-1-RoboCasa365',
         'host':'127.0.0.1','port':10086,'obs_history':4,'obs_interval':2,'crop_ratio':.95,
         'identity':{'name':'xiaomi_r1_robocasa365','checkpoint_sha256':None,
         'revision':'0dd7aef8dc87296246aae812a1f59ccb708e5546','action_space':'robocasa12',
         'benchmark_training':'Human300 benchmark-trained; held-out composite tasks evaluated separately',
         'native_hz':20.,'execute_steps':16,'prediction_horizon':None,'stateful':True,
         'preprocessing_id':'xr1_rc365_ee14_state60_history4_interval2_crop095'}}}


def configs():
    rows=[]
    for name in ('pi05','xiaomi_r1','g05','internw0_delta'):
        for mode in ('motor_only','review_every_chunk','sparse'):
            identity=deepcopy(POLICIES[name]['identity'])
            rows.append({'name':f'robodojo_{name}_{mode}','benchmark':'robodojo','mode':mode,
                'max_decision_steps':identity['execute_steps'],'max_correction_steps':5,'max_reviews':180,
                'wall_limit_s':3600,'model':deepcopy(MODEL),'no_task_memory':True,'no_task_demonstrations':True,
                'monitor':{'max_unreviewed_steps':50,'max_unreviewed_chunks':4},
                'robot_preview':True,
                'environment':{'backend':'robodojo_rpc','gpt_as_policy_root':'external/GPT-as-Policy',
                   'sim_port':19113,'native_outcome_path':'/ABSOLUTE/PATH/SIM_OUTPUT/evaluation_outcome.json',
                   'allow_xiaomi_eef_via_dls':name=='xiaomi_r1'},
                'policy':{'backend':'remote','endpoint':'http://127.0.0.1:19600','identity':identity,
                   'artifact_manifest':'/ABSOLUTE/PATH/policy-artifacts.json'},
                'classification':'benchmark_trained_policy_plus_runtime',
                'controller_qualification_required':True})
    for mode,steps in (('direct_dense',5),('direct_sparse',40)):
        rows.append({'name':f'robodojo_{mode}','benchmark':'robodojo','mode':mode,
            'model':deepcopy(MODEL),'policy':None,'max_decision_steps':steps,'max_correction_steps':steps,
            'max_reviews':180,'wall_limit_s':3600,'translation_limit_m':.05,'robot_preview':False,
            'environment':{'backend':'robodojo_rpc','gpt_as_policy_root':'external/GPT-as-Policy','sim_port':19113},
            'no_task_memory':True,'no_task_demonstrations':True,
            'classification':'no_robot_policy_training', 'controller_qualification_required':True})
    for mode in ('motor_only','review_every_chunk','sparse'):
        rows.append({'name':f'robocasa365_xiaomi_{mode}','benchmark':'robocasa365','mode':mode,
           'model':deepcopy(MODEL),'max_decision_steps':16,'max_correction_steps':5,'max_reviews':180,'wall_limit_s':3600,
           'environment':{'backend':'robocasa','xiaomi_root':'external/Xiaomi-Robotics-1',
             'robocasa_root':'external/RoboCasa','control_hz':20},
           'policy':deepcopy(POLICIES['xiaomi_robocasa365'])|{'artifact_manifest':'/ABSOLUTE/PATH/policy-artifacts.json'},
           'monitor':{'max_unreviewed_steps':50,'max_unreviewed_chunks':4},'robot_preview':True,
           'no_task_memory':True,'no_task_demonstrations':True,
           'classification':'benchmark_trained_policy_plus_runtime','controller_qualification_required':True})
    return rows


def write_configs(root):
    root=Path(root)
    for cfg in configs():atomic_json(root/(cfg['name']+'.json'),cfg)
    for name,policy in POLICIES.items():
        atomic_json(root/'policies'/(name+'.json'),policy|{'artifact_manifest':'/ABSOLUTE/PATH/policy-artifacts.json'})
    flex=deepcopy(MODEL);flex['service_tier']='flex';flex['timeout_s']=900
    atomic_json(root/'model_standard.json',MODEL);atomic_json(root/'model_flex.json',flex)
