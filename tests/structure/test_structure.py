#!/usr/bin/env python3
import os,re,sys,yaml
root=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
errs=[]
req=['SKILL.md','manifest.yaml','VERSION','CHANGELOG.md','README.md','deploy/install.sh','deploy/uninstall.sh','deploy/verify-install.sh']
req+=[f'references/{n}.md' for n in ['platform-architecture','module-inventory','services-and-dependencies','resource-assessment','deployment-architecture','designer-operations','component-management','workflow-management','application-lifecycle','datasource-management','database-operations','permission-management','performance-optimization','troubleshooting','upgrade-guide','migration-guide','backup-restore','security-guide']]
req+=[f'runbooks/{n}.md' for n in ['install','deploy','restart','health-check','application-publish','workflow-diagnosis','datasource-diagnosis','database-maintenance','performance-tuning','upgrade','rollback']]
for p in req:
    if not os.path.exists(os.path.join(root,p)): errs.append('missing '+p)
s=open(os.path.join(root,'SKILL.md'),encoding='utf-8').read()
m=re.match(r'^---\n(.*?)\n---\n',s,re.S)
if not m: errs.append('no frontmatter')
else:
    fm=yaml.safe_load(m.group(1))
    if fm.get('name')!='gdmp-master': errs.append('bad name')
man=yaml.safe_load(open(os.path.join(root,'manifest.yaml'),encoding='utf-8'))
if man['runtime']['ai_execution']!='not_enabled': errs.append('ai_execution must be not_enabled')
print('structure(gdmp):','PASS' if not errs else 'FAIL '+str(errs))
sys.exit(1 if errs else 0)
