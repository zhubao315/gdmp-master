#!/usr/bin/env python3
import os,re,sys,yaml
root=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
errs=[]
for p in ['SKILL.md','manifest.yaml','VERSION','CHANGELOG.md','README.md','deploy/install.sh','deploy/uninstall.sh','deploy/verify-install.sh']:
    if not os.path.exists(os.path.join(root,p)): errs.append('missing '+p)
s=open(os.path.join(root,'SKILL.md'),encoding='utf-8').read()
m=re.match(r'^---\n(.*?)\n---\n',s,re.S)
if not m: errs.append('no frontmatter')
else:
    fm=yaml.safe_load(m.group(1))
    if fm.get('name')!='gdmp-master': errs.append('bad name')
    if not fm.get('description'): errs.append('no description')
man=yaml.safe_load(open(os.path.join(root,'manifest.yaml'),encoding='utf-8'))
if man['runtime']['native_skill_runtime'] is not False: errs.append('must declare native_skill_runtime:false')
if man['runtime']['ai_execution']!='not_enabled': errs.append('must declare ai_execution:not_enabled')
print('validate-skill(gdmp):', 'OK' if not errs else 'FAIL '+str(errs))
sys.exit(1 if errs else 0)
