#!/usr/bin/env python3
"""机械探测已知 GDMP 端点（只读，不含凭据）。"""
import json,subprocess,datetime
def http(u):
    try:
        return subprocess.check_output(f"curl -k -s -o /dev/null -w '%{{http_code}}' --max-time 8 {u}",shell=True,text=True,timeout=15).strip()
    except Exception: return "unavailable"
print(json.dumps({"collected_at":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
 "endpoints":{"docs_9191":http("https://219.142.87.233:9191/"),
              "product_192_168_1_32":http("http://192.168.1.32:8080/"),
              "product_external_3280":http("http://219.142.87.231:3280/")},
 "note":"HTTP 200 only proves reachability, not platform health"},ensure_ascii=False,indent=2))
