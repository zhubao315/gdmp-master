#!/usr/bin/env python3
import yaml,json,sys
root=__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
m=yaml.safe_load(open(root+'/manifest.yaml'))
print('declared commit:',m['target']['observed_commit'])
print('ai_execution:',m['runtime']['ai_execution'],'| native runtime:',m['runtime']['native_skill_runtime'])
print('compatibility check: INFO only; no runtime version available without credentials')
sys.exit(0)
