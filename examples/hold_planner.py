"""Trusted JSON responder for native RESET/RENDER/HOLD smoke, NOT benchmark policy."""
import json,sys
c=json.load(sys.stdin)
if c['recent_receipts']:
    out={'capability':'finish','arguments':{},'max_steps':0,'decision_summary':'End smoke; no competence claim.'}
else:
    out={'capability':'set_gripper','arguments':{'gripper':-1,'steps':1},'max_steps':1,
         'decision_summary':'One zero-translation open-gripper action for native integration smoke.'}
json.dump(out,sys.stdout)
