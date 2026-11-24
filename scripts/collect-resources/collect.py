#!/usr/bin/env python3
"""机械采集本机资源基线（只读，无敏感信息）。注意：本机可能不运行 GDMP。"""
import json,subprocess,datetime
def run(c):
    try: return subprocess.check_output(c,shell=True,stderr=subprocess.STDOUT,text=True,timeout=30).strip()
    except Exception as e: return f"unavailable: {e}"
print(json.dumps({"collected_at":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
 "kernel":run("uname -sr"),"cpu_cores":run("nproc"),"memory":run("free -h | head -2"),
 "disk":run("df -h / /data 2>/dev/null"),"note":"OpenCode host may not host GDMP; do NOT use as GDMP baseline"},ensure_ascii=False,indent=2))
