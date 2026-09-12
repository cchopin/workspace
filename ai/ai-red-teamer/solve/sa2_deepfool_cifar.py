#!/usr/bin/env python3
# Multiclass DeepFool (closest boundary) + magnitude scaling to survive PNG quantization.
import os, sys, numpy as np, requests, torch, torch.nn as nn
sys.path.insert(0,os.path.dirname(__file__))
from cifar_common import *
B=os.environ["BASE_URL"]
ch=requests.get(f"{B}/challenge",timeout=20).json()
x01=img01_from_b64(ch["image"]); lab=int(ch["original_class"]); thr=float(ch["l2_threshold"])
overshoot=float(ch.get("overshoot_hint",0.02)); maxit=int(ch.get("max_iterations_hint",50))
open("/tmp/cifar.pth","wb").write(requests.get(f"{B}/model/weights",timeout=30).content)
m=load_model("/tmp/cifar.pth")
x=to_tensor01(x01); z0=normalize(x).detach(); num=10

def grads_all(z):
    z=z.clone().detach().requires_grad_(True); out=m(z)[0]; gs=[]
    for k in range(num):
        gs.append(torch.autograd.grad(out[k],z,retain_graph=(k<num-1))[0].detach().reshape(-1))
    return out.detach(), torch.stack(gs)

z=z0.clone().detach(); r_tot=torch.zeros_like(z0.reshape(-1))
for i in range(max(maxit,60)):
    if int(m(z).argmax(1))!=lab: break
    f,gr=grads_all(z); w_lab=gr[lab]
    bd=1e18;bw=None;bf=None
    for k in range(num):
        if k==lab: continue
        w=gr[k]-w_lab; fk=f[k]-f[lab]; d=abs(fk.item())/(w.norm(2).item()+1e-12)
        if d<bd: bd=d;bw=w;bf=fk
    r_tot=r_tot+(abs(bf.item())/(bw.norm(2).item()**2+1e-12))*bw
    z=(z0.reshape(-1)+(1+overshoot)*r_tot).reshape_as(z0).detach()

delta=(z-z0)  # DeepFool direction
base_l2=float(delta.reshape(-1).norm(2))
def png_pred(zt):
    a=to_img01(denormalize(zt)).clip(0,1); b=b64_from_img01(a)
    zr=normalize(to_tensor01(img01_from_b64(b)))
    return int(m(zr).argmax(1)), float((zr-z0).reshape(-1).norm(2)), b
# grow magnitude along same direction until PNG-quantized pred flips, staying <= thr
chosen=None
for fac in np.linspace(1.0, max(1.0, thr/max(base_l2,1e-6))*0.98, 40):
    zt=z0+delta*float(fac)
    p,l2r,b=png_pred(zt)
    if p!=lab and l2r<=thr:
        chosen=(zt,p,l2r,b); break
if chosen is None:
    zt=z0+delta*(thr/max(base_l2,1e-6))*0.97; p,l2r,b=png_pred(zt); chosen=(zt,p,l2r,b)
zt,p,l2r,b64=chosen
print("base_l2",round(base_l2,3),"final l2 after png",round(l2r,3),"local pred",p)
print("server pred", requests.post(f"{B}/predict",json={"image":b64},timeout=20).json().get("predicted_class_name"))
r=requests.post(f"{B}/submit",json={"image":b64},timeout=20); print("SUBMIT",r.status_code,r.text[:400])
