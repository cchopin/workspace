#!/usr/bin/env python3
# JSMA targeted L0 attack on MNIST LeNet-5 (MNISTClassifier).
import os, io, base64, numpy as np, requests, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
B=os.environ["BASE_URL"]
MEAN,STD=0.1307,0.3081
def x01_from_b64(b64):
    raw=base64.b64decode(b64); img=Image.open(io.BytesIO(raw)).convert("L")
    return np.clip(np.asarray(img,np.float32)/255.0,0,1)
def b64_from_x01(x2d):
    x255=np.clip((x2d*255.0).round(),0,255).astype(np.uint8)
    buf=io.BytesIO(); Image.fromarray(x255,mode="L").save(buf,format="PNG",optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

class MNISTClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1=nn.Conv2d(1,6,5,1,0); self.conv2=nn.Conv2d(6,16,5,1,0)
        self.pool=nn.AvgPool2d(2,2); self.fc1=nn.Linear(16*4*4,120)
        self.fc2=nn.Linear(120,84); self.fc3=nn.Linear(84,10); self.act=nn.Tanh()
    def logits(self,x):
        x=self.act(self.conv1(x)); x=self.pool(x); x=self.act(self.conv2(x)); x=self.pool(x)
        x=torch.flatten(x,1); x=self.act(self.fc1(x)); x=self.act(self.fc2(x)); return self.fc3(x)
    def forward(self,x): return F.log_softmax(self.logits(x),dim=1)

def norm(x): return (x-MEAN)/STD

ch=requests.get(f"{B}/challenge",timeout=20).json()
x=x01_from_b64(ch["image_b64"]); lab=int(ch["original_label"]); tgt=int(ch["target_class"])
budget=int(ch["l0_budget"]); max_l2=float(ch["max_l2"])
print("lab",lab,"target",tgt,"L0 budget",budget,"max_l2",max_l2)
open("/tmp/jsma.pth","wb").write(requests.get(f"{B}/weights",timeout=20).content)
m=MNISTClassifier().eval(); m.load_state_dict(torch.load("/tmp/jsma.pth",map_location="cpu"))
x0=torch.from_numpy(x.copy())
adv=x0.clone()
modified=set()
theta=1.0

def pred_of(t):
    with torch.no_grad():
        return int(m(norm(t.view(1,1,28,28))).argmax(1))

def jac(t):
    t=t.view(1,1,28,28).clone().detach().requires_grad_(True)
    z=m.logits(norm(t))[0]  # (10,)
    J=[]
    for k in range(10):
        g=torch.autograd.grad(z[k],t,retain_graph=(k<9))[0].reshape(-1).detach()
        J.append(g)
    return torch.stack(J)  # (10,784)

for step in range(budget):
    if pred_of(adv)==tgt: break
    J=jac(adv)
    flat=adv.reshape(-1)
    alpha=J[tgt]                       # d logit_target / d pixel
    beta=J.sum(0)-J[tgt]               # sum of others
    sal=torch.zeros(784)
    # increasing pixels: need room to increase (pixel<1)
    can_inc=(flat<1.0)
    mask_inc=can_inc & (alpha>0) & (beta<0)
    sal_inc=torch.where(mask_inc, alpha*(-beta), torch.zeros(784))
    # decreasing pixels: pixel>0, alpha<0 & beta>0
    can_dec=(flat>0.0)
    mask_dec=can_dec & (alpha<0) & (beta>0)
    sal_dec=torch.where(mask_dec, (-alpha)*(beta), torch.zeros(784))
    # forbid re-picking already-modified pixels beyond count; but allow saturating
    best_inc=int(sal_inc.argmax()); best_dec=int(sal_dec.argmax())
    v_inc=float(sal_inc[best_inc]); v_dec=float(sal_dec[best_dec])
    if v_inc<=0 and v_dec<=0:
        # fallback: push pixel most aligned with increasing target
        idx=int(alpha.argmax()); flat[idx]=min(1.0,flat[idx].item()+theta); modified.add(idx)
    elif v_inc>=v_dec:
        flat[best_inc]=1.0; modified.add(best_inc)
    else:
        flat[best_dec]=0.0; modified.add(best_dec)
    adv=flat.view(28,28)

arr=adv.numpy()
b64=b64_from_x01(arr); xr=x01_from_b64(b64)
diff=np.abs(xr-x); l0=int((diff>1e-6).sum()); l2=float(np.sqrt((diff**2).sum()))
pr=requests.post(f"{B}/predict",json={"image_b64":b64},timeout=15).json()
print("L0",l0,"budget",budget,"l2",round(l2,3),"max_l2",max_l2,"pred",pr.get("predicted_class"))
r=requests.post(f"{B}/submit",json={"image_b64":b64},timeout=20)
print("SUBMIT",r.status_code,r.text[:300])
