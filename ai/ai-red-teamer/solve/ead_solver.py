#!/usr/bin/env python3
# ElasticNet (EAD) attack via FISTA + binary search on MNIST SimpleClassifier. Untargeted.
import os, io, base64, numpy as np, requests, torch, torch.nn as nn
from PIL import Image
B=os.environ["BASE_URL"]
MNIST_MEAN, MNIST_STD = 0.1307, 0.3081

def x01_from_b64(b64):
    raw=base64.b64decode(b64); img=Image.open(io.BytesIO(raw)).convert("L")
    return np.clip(np.asarray(img,np.float32)/255.0,0,1)
def b64_from_x01(x2d):
    x255=np.clip((x2d*255.0).round(),0,255).astype(np.uint8)
    buf=io.BytesIO(); Image.fromarray(x255,mode="L").save(buf,format="PNG",optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

class SimpleClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1=nn.Conv2d(1,32,3,1); self.conv2=nn.Conv2d(32,64,3,1)
        self.dropout1=nn.Dropout(0.25); self.dropout2=nn.Dropout(0.5)
        self.fc1=nn.Linear(9216,128); self.fc2=nn.Linear(128,10)
    def forward(self,x01):
        x=(x01-MNIST_MEAN)/MNIST_STD
        x=torch.relu(self.conv1(x)); x=torch.relu(self.conv2(x))
        x=torch.max_pool2d(x,2); x=self.dropout1(x); x=torch.flatten(x,1)
        x=torch.relu(self.fc1(x)); x=self.dropout2(x); x=self.fc2(x)
        return x  # logits (no log_softmax; we need raw Z for CW loss)

ch=requests.get(f"{B}/challenge",timeout=20).json()
x=x01_from_b64(ch["image_b64"]); lab=int(ch["label"]); beta=float(ch["beta"])
elastic_max=float(ch["elastic_max"]); l2_max=float(ch["l2_max"]); l1_max=float(ch["l1_max"])
print("lab",lab,"beta",beta,"elastic_max",elastic_max,"l2_max",l2_max,"l1_max",l1_max)
open("/tmp/ead.pth","wb").write(requests.get(f"{B}/weights",timeout=20).content)
model=SimpleClassifier().eval(); model.load_state_dict(torch.load("/tmp/ead.pth",map_location="cpu"))
x0=torch.from_numpy(x[None,None,...]).float()

def cw_loss(img, kappa=0.0):
    z=model(img)[0]
    real=z[lab]; other=torch.max(torch.cat([z[:lab],z[lab+1:]]))
    return torch.clamp(real-other+kappa, min=0)  # untargeted: want other>real

def shrink(z, x0, beta):  # EAD elastic-net proximal + [0,1] box
    upper=torch.clamp(z-beta,max=1.0)
    lower=torch.clamp(z+beta,min=0.0)
    out=torch.where(z-x0>beta, upper, torch.where(z-x0<-beta, lower, x0))
    return out.clamp(0,1)

def dists(adv):
    d=(adv-x0).reshape(-1)
    l1=float(d.abs().sum()); l2=float(d.norm(2)); linf=float(d.abs().max())
    return l1,l2,l1*beta+l2

def ead(c, iters=1000, lr=0.01, kappa=0.0):
    x_adv=x0.clone(); y=x0.clone(); tk=1.0
    best=None; bestdist=1e18
    for it in range(iters):
        y=y.clone().detach().requires_grad_(True)
        loss=c*cw_loss(y,kappa)+((y-x0).reshape(-1).norm(2)**2)
        model.zero_grad(); loss.backward()
        with torch.no_grad():
            newx=y-lr*y.grad
            newx=shrink(newx,x0,lr*beta)
            tk1=(1+np.sqrt(1+4*tk*tk))/2
            y=newx+((tk-1)/tk1)*(newx-x_adv)
            x_adv=newx; tk=tk1
        pred=int(model(x_adv).argmax(1))
        if pred!=lab:
            l1,l2,el=dists(x_adv)
            if el<bestdist:
                bestdist=el; best=x_adv.clone()
    return best,bestdist

chosen=None
for c in [1,5,10,20,40,80,160]:
    best,bd=ead(c)
    if best is not None:
        # check via PNG roundtrip
        arr=best.squeeze().numpy(); b64=b64_from_x01(arr); xr=x01_from_b64(b64)
        d=(xr-x); l1=float(np.abs(d).sum()); l2=float(np.sqrt((d**2).sum())); el=l2+beta*l1
        pr=requests.post(f"{B}/predict",json={"image_b64":b64},timeout=15).json()
        okc=(el<=elastic_max and l2<=l2_max and l1<=l1_max and pr["pred"]!=lab)
        print(f"c={c} el={el:.3f}/{elastic_max} l2={l2:.3f}/{l2_max} l1={l1:.3f}/{l1_max} pred={pr['pred']} ok={okc}")
        if okc:
            chosen=b64; break
if chosen is None:
    print("no candidate satisfied all caps"); raise SystemExit
r=requests.post(f"{B}/submit",json={"image_b64":chosen},timeout=20)
print("SUBMIT",r.status_code,r.text[:300])
