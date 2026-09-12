#!/usr/bin/env python3
"""Task 3 OmniDigit: craft minimal-L0 (<=16 px) adversarial tiles so the transferable
MNIST surrogate reads the escalation code, staying bank-consistent. Compose + submit."""
import glob, io, sys, numpy as np, requests, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image

IP="154.57.164.73"; PORT="31374"; H="staging.phantomkernel.htb"
URL=f"http://{IP}:{PORT}/omnidigit/api/verify"; HEAD={"Host":H}
BANK="/Users/cchopin/Workspace/ai/ai-red-teamer/exam/loot/omnidigit/bank"
dev=torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
L0MAX=16
MEAN,STD=0.1307,0.3081

class Net(nn.Module):
    def __init__(s):
        super().__init__(); s.c1=nn.Conv2d(1,32,3,padding=1); s.c2=nn.Conv2d(32,64,3,padding=1)
        s.fc1=nn.Linear(64*7*7,128); s.fc2=nn.Linear(128,10)
    def forward(s,x):
        x=F.max_pool2d(F.relu(s.c1(x)),2); x=F.max_pool2d(F.relu(s.c2(x)),2)
        return s.fc2(F.relu(s.fc1(torch.flatten(x,1))))
net=Net().to(dev); net.load_state_dict(torch.load("/Users/cchopin/Workspace/ai/ai-red-teamer/solve/.mnist_cnn.pt",map_location=dev)); net.eval()

def logits_of(x01):  # x01 tensor (28,28) in [0,1]
    t=((x01-MEAN)/STD).view(1,1,28,28)
    return net(t)[0]
def conf(x01,cls):
    with torch.no_grad(): return float(F.softmax(logits_of(x01),0)[cls])
def pred(x01):
    with torch.no_grad():
        p=F.softmax(logits_of(x01),0); return int(p.argmax()),float(p.max())

def load(tid): return np.asarray(Image.open(f"{BANK}/tile_{tid}.png").convert("L"),dtype=np.float32)/255.0
tiles={int(f.split('_')[-1].split('.')[0]):load(int(f.split('_')[-1].split('.')[0]))
       for f in glob.glob(f"{BANK}/tile_*.png")}

def greedy_l0(src01, target, budget=L0MAX):
    """Greedily flip up to `budget` pixels to {0 or 1} to maximize target logit."""
    orig=torch.tensor(src01,device=dev)
    x=orig.clone()
    changed=set()
    for step in range(budget):
        xr=x.clone().requires_grad_(True)
        lg=logits_of(xr)
        loss=lg[target]-lg[torch.arange(10,device=dev)!=target].max()
        net.zero_grad(); loss.backward()
        g=xr.grad.detach()  # d(target-margin)/dx
        # candidate change per pixel: push to 1 if g>0 else to 0; gain ~ |g|*(delta)
        push_up = (1.0-x)*torch.clamp(g,min=0)     # gain if set to 1
        push_dn = (x-0.0)*torch.clamp(-g,min=0)    # gain if set to 0
        gain=torch.maximum(push_up,push_dn).clone()
        # forbid already-changed pixels from re-selection (allow but skip if no gain)
        flat=gain.view(-1)
        for idx in changed: flat[idx]=-1
        best=int(torch.argmax(flat))
        if flat[best]<=0: break
        r,c=divmod(best,28)
        x[r,c]=1.0 if g[r,c]>0 else 0.0
        changed.add(best)
        p,pc=pred(x)
        if p==target and pc>0.90 and len(changed)>=3:
            break
    l0=int((x!=orig).sum().item())
    return x.detach().cpu().numpy(), l0

def best_tile_for(target):
    # rank source tiles by achievable target confidence within budget
    results=[]
    for tid,arr in tiles.items():
        adv,l0=greedy_l0(arr,target)
        c=conf(torch.tensor(adv,device=dev),target)
        p,pc=pred(torch.tensor(adv,device=dev))
        results.append((c,l0,tid,adv,p))
    results.sort(key=lambda r:(-(r[0]), r[1]))
    return results

CODE=[int(c) for c in (sys.argv[1] if len(sys.argv)>1 else "133717")]
print("target code:",CODE,"| L0 budget",L0MAX)
chosen=[]
for pos,d in enumerate(CODE):
    res=best_tile_for(d)
    c,l0,tid,adv,p=res[0]
    print(f"pos{pos} digit{d}: best src tile_{tid} -> pred{p} conf{c:.3f} L0={l0}")
    chosen.append(adv)

# compose + submit
canvas=np.zeros((28,168),np.float32)
for i,a in enumerate(chosen): canvas[:,i*28:(i+1)*28]=a
u8=(canvas*255).round().clip(0,255).astype(np.uint8)
Image.fromarray(u8,"L").save("/Users/cchopin/Workspace/ai/ai-red-teamer/exam/loot/omnidigit/attack.png")
b=io.BytesIO(); Image.fromarray(u8,"L").save(b,"PNG"); b.seek(0)
r=requests.post(URL,headers=HEAD,files={"file":("captcha.png",b,"image/png")},timeout=40)
print("\nSERVER:",r.status_code,r.text.strip())
