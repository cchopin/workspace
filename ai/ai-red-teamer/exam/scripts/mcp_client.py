#!/usr/bin/env python3
import sys, json, requests
IP="154.57.164.73"; PORT="31374"
BASE=f"http://mcp.phantomkernel.htb:{PORT}/mcp"
AUTH=("staging","c7af8ebf8d718d95156c56697cfb1551")
HDR={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
S=requests.Session(); S.auth=AUTH
# resolve host header to IP
from requests.adapters import HTTPAdapter
import urllib3; urllib3.disable_warnings()
def _post(payload, sid=None):
    h=dict(HDR)
    if sid: h["Mcp-Session-Id"]=sid
    # send to IP with Host header, allow redirects manually to /mcp
    url=f"http://{IP}:{PORT}/mcp"
    h["Host"]="mcp.phantomkernel.htb"
    r=S.post(url, headers=h, data=json.dumps(payload), allow_redirects=True, stream=True, timeout=60)
    sid2=r.headers.get("mcp-session-id", sid)
    body=r.text
    # parse SSE
    out=[]
    for line in body.splitlines():
        if line.startswith("data:"):
            try: out.append(json.loads(line[5:].strip()))
            except: out.append(line[5:].strip())
    return r.status_code, sid2, out, body

def init():
    p={"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rt","version":"1"}}}
    c,sid,out,body=_post(p)
    # initialized notification
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, sid)
    return sid

def rpc(method, params=None, sid=None, id=2):
    p={"jsonrpc":"2.0","id":id,"method":method}
    if params is not None: p["params"]=params
    return _post(p, sid)

if __name__=="__main__":
    sid=init()
    cmd=sys.argv[1] if len(sys.argv)>1 else "tools/list"
    if cmd=="tools/list":
        c,sid,out,body=rpc("tools/list",{}, sid); print(json.dumps(out,indent=2))
    elif cmd=="prompts/list":
        c,sid,out,body=rpc("prompts/list",{}, sid); print(json.dumps(out,indent=2))
    elif cmd=="resources/list":
        c,sid,out,body=rpc("resources/list",{}, sid); print(json.dumps(out,indent=2))
    elif cmd=="call":
        name=sys.argv[2]; args=json.loads(sys.argv[3]) if len(sys.argv)>3 else {}
        c,sid,out,body=rpc("tools/call",{"name":name,"arguments":args}, sid)
        print(json.dumps(out,indent=2))
