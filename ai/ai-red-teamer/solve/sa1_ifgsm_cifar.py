#!/usr/bin/env python3
import os, sys, numpy as np, requests, torch, torch.nn as nn
sys.path.insert(0,os.path.dirname(__file__))
from cifar_common import *
B=os.environ["BASE_URL"]
ch=requests.get(f"{B}/challenge",timeout=20).json()
x01=img01_from_b64(ch["image"]); lab=int(ch["original_class"]); tgt=int(ch["target_class"]); eps=float(ch["epsilon"])
print("orig",lab,"target",tgt,"eps",eps)
open("/tmp/cifar.pth","wb").write(requests.get(f"{B}/model/weights",timeout=30).content)
m=load_model("/tmp/cifar.pth")
x=to_tensor01(x01)
print("clean pred", int(m(normalize(x)).argmax(1)))
alpha=eps/10
x_adv=x.clone()
for i in range(200):
    x_adv.requires_grad_(True)
    logits=m(normalize(x_adv))
    loss=nn.functional.cross_entropy(logits,torch.tensor([tgt]))
    m.zero_grad(); loss.backward()
    with torch.no_grad():
        x_adv=x_adv-alpha*x_adv.grad.sign()
        x_adv=torch.max(torch.min(x_adv,x+eps),x-eps).clamp(0,1)
    x_adv=x_adv.detach()
    p=int(m(normalize(x_adv)).argmax(1))
    if p==tgt: print("target reached iter",i); break
b64=b64_from_img01(to_img01(x_adv))
# verify linf after png roundtrip
xr=img01_from_b64(b64); print("linf", float(np.max(np.abs(x01-xr))), "eps", eps)
print("server pred", requests.post(f"{B}/predict",json={"image":b64},timeout=20).json().get("predicted_class_name"))
r=requests.post(f"{B}/submit",json={"image":b64},timeout=20); print("SUBMIT",r.status_code,r.text[:300])
