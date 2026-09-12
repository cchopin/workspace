#!/usr/bin/env python3
# Module 320 Skills Assessment: targeted EAD/JSMA on ResNet-18 CIFAR-10, min L2 1.5.
import os, io, base64, json, numpy as np, requests, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
B=os.environ["BASE_URL"]
MEAN=torch.tensor([0.4914,0.4822,0.4465]).view(1,3,1,1)
STD=torch.tensor([0.247,0.2435,0.2616]).view(1,3,1,1)

def x01_from_b64(b64):
    raw=base64.b64decode(b64); img=Image.open(io.BytesIO(raw)).convert("RGB")
    return (np.asarray(img,np.float32)/255.0)  # (32,32,3)
def b64_from_x01(a):  # (3,32,32) tensor-ish np
    x=np.transpose(a,(1,2,0)); x255=np.clip((x*255).round(),0,255).astype(np.uint8)
    buf=io.BytesIO(); Image.fromarray(x255,mode="RGB").save(buf,format="PNG",optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

class BasicBlock(nn.Module):
    expansion=1
    def __init__(self,inp,planes,stride=1):
        super().__init__()
        self.conv1=nn.Conv2d(inp,planes,3,stride=stride,padding=1,bias=False); self.bn1=nn.BatchNorm2d(planes)
        self.conv2=nn.Conv2d(planes,planes,3,padding=1,bias=False); self.bn2=nn.BatchNorm2d(planes)
        self.shortcut=nn.Sequential()
        if stride!=1 or inp!=planes:
            self.shortcut=nn.Sequential(nn.Conv2d(inp,planes,1,stride=stride,bias=False),nn.BatchNorm2d(planes))
    def forward(self,x):
        o=torch.relu(self.bn1(self.conv1(x))); o=self.bn2(self.conv2(o)); o+=self.shortcut(x); return torch.relu(o)
class ResNetCIFAR(nn.Module):
    def __init__(self,nb=(2,2,2,2),nc=10):
        super().__init__(); self.in_planes=64
        self.conv1=nn.Conv2d(3,64,3,1,1,bias=False); self.bn1=nn.BatchNorm2d(64)
        self.layer1=self._ml(64,nb[0],1); self.layer2=self._ml(128,nb[1],2)
        self.layer3=self._ml(256,nb[2],2); self.layer4=self._ml(512,nb[3],2)
        self.avgpool=nn.AdaptiveAvgPool2d(1); self.fc=nn.Linear(512,nc)
    def _ml(self,planes,n,stride):
        layers=[]
        for s in [stride]+[1]*(n-1):
            layers.append(BasicBlock(self.in_planes,planes,s)); self.in_planes=planes
        return nn.Sequential(*layers)
    def forward(self,x):
        o=torch.relu(self.bn1(self.conv1(x)))
        o=self.layer1(o);o=self.layer2(o);o=self.layer3(o);o=self.layer4(o)
        o=self.avgpool(o);o=torch.flatten(o,1);return self.fc(o)

def norm(t): return (t-MEAN)/STD

meta=requests.get(f"{B}/model",timeout=20).json()
open("/tmp/rescifar.pth","wb").write(requests.get(f"{B}{meta['weights_url']}",timeout=60).content)
st=torch.load("/tmp/rescifar.pth",map_location="cpu")
sd=st.get("state_dict_ema") or st.get("state_dict") or st
model=ResNetCIFAR().eval(); model.load_state_dict(sd)

ch=requests.get(f"{B}/challenge",timeout=20).json()
print("items",len(ch["items"]))
def logits(t): return model(norm(t))
def pred(t):
    with torch.no_grad(): return int(logits(t).argmax(1))

def cw_targeted(t,tgt,kappa=0.0):
    z=logits(t)[0]; real=z[tgt]; other=torch.max(torch.cat([z[:tgt],z[tgt+1:]]))
    return torch.clamp(other-real+kappa,min=0)  # want real>other -> minimize

def ead_targeted(x0,tgt,beta=0.01,iters=400,lr=0.02):
    x_adv=x0.clone(); y=x0.clone(); tk=1.0; best=None
    for it in range(iters):
        y=y.clone().detach().requires_grad_(True)
        loss=20*cw_targeted(y,tgt)+((y-x0).reshape(-1).norm(2)**2)
        model.zero_grad(); loss.backward()
        with torch.no_grad():
            newx=y-lr*y.grad
            b=lr*beta
            newx=torch.where(newx-x0>b, torch.clamp(newx-b,max=1.0),
                  torch.where(newx-x0<-b, torch.clamp(newx+b,min=0.0), x0)).clamp(0,1)
            tk1=(1+np.sqrt(1+4*tk*tk))/2; y=newx+((tk-1)/tk1)*(newx-x_adv); x_adv=newx; tk=tk1
        if pred(x_adv)==tgt: best=x_adv.clone()
    return best if best is not None else x_adv

def jsma_targeted(x0,tgt,max_pixels=200):
    adv=x0.clone().reshape(-1); D=adv.numel()
    for step in range(max_pixels):
        if pred(adv.view(1,3,32,32))==tgt and float((adv-x0.reshape(-1)).norm(2))>=1.55: break
        t=adv.view(1,3,32,32).clone().detach().requires_grad_(True)
        z=logits(t)[0]
        gt=torch.autograd.grad(z[tgt],t,retain_graph=True)[0].reshape(-1).detach()
        gsum=torch.zeros(D)
        for k in range(10):
            if k==tgt: continue
            gsum=gsum+torch.autograd.grad(z[k],t,retain_graph=(k<9))[0].reshape(-1).detach()
        flat=adv
        alpha=gt; beta=gsum
        sal_inc=torch.where((flat<1.0)&(alpha>0)&(beta<0), alpha*(-beta), torch.zeros(D))
        sal_dec=torch.where((flat>0.0)&(alpha<0)&(beta>0), (-alpha)*beta, torch.zeros(D))
        bi=int(sal_inc.argmax()); bd=int(sal_dec.argmax())
        if sal_inc[bi]>=sal_dec[bd] and sal_inc[bi]>0: flat[bi]=1.0
        elif sal_dec[bd]>0: flat[bd]=0.0
        else: flat[int(alpha.argmax())]=1.0
        adv=flat
    return adv.view(1,3,32,32)

def ensure_l2(adv,x0,method):
    # scale perturbation up if below 1.5 (keep direction)
    d=adv-x0; l2=float(d.reshape(-1).norm(2))
    if l2>=1.55: return adv
    if l2<1e-6: return adv
    adv2=(x0+d*(1.6/l2)).clamp(0,1)
    return adv2

results=[]
for it in ch["items"]:
    sid=it["sample_id"]; tgt=int(it["target"]); method=it["required_method"]
    x=x01_from_b64(it["image_b64"]); x0=torch.from_numpy(np.transpose(x,(2,0,1))[None,...]).float()
    if method=="jsma":
        adv=jsma_targeted(x0,tgt)
    else:
        adv=ead_targeted(x0,tgt)
    adv=ensure_l2(adv,x0,method)
    arr=adv.squeeze(0).numpy(); b64=b64_from_x01(arr)
    xr=x01_from_b64(b64); xrt=torch.from_numpy(np.transpose(xr,(2,0,1))[None,...]).float()
    p=pred(xrt); l2=float((xrt-x0).reshape(-1).norm(2)); l0=int((np.abs(xr-x)>1e-6).sum())
    print(f"item {sid} method {method} target {tgt} -> pred {p} l2 {l2:.3f} l0 {l0}")
    results.append({"sample_id":sid,"method":method,"image_b64":b64})
r=requests.post(f"{B}/submit_images",json={"items":results},timeout=60)
print("SUBMIT",r.status_code,r.text[:500])
