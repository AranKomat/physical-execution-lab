#!/usr/bin/env python3
"""An interface-test actor, NOT a robotics planner. It requests done only."""
import json,sys
request=json.load(sys.stdin)
print(json.dumps({'request_sha256':request['request_sha256'],'tool':'done',
                  'arguments':{'summary':'transport test; not claiming task success','decision_note':'Interface test only.'}}))
