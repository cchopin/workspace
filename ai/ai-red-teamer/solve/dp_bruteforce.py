#!/usr/bin/env python3
# Brute-force: train official recipe (eps=6) over many seeds on MPS, save each model + local MIA.
import torch, torch.nn as nn, torch.nn.functional as F, torch.optim as optim, numpy as np, time, json
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator
from safetensors.torch import save_file
BATCH_SIZE=256; DP_EPOCHS=20; DP_LR=0.1; MAX_GRAD_NORM=1.0; DELTA=1e-5; TARGET_EPSILON=6.0
dev=torch.device("mps")
MEAN=(0.4377,0.4438,0.4728); STD=(0.1980,0.2010,0.1970)
tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
train=datasets.SVHN("data",split='train',download=False,transform=tf)
test=datasets.SVHN("data",split='test',download=False,transform=tf)
test_loader=DataLoader(test,batch_size=512)
class SVHNCNN(nn.Module):
    def __init__(s):
        super().__init__()
        s.conv1=nn.Conv2d(3,32,3,padding=1); s.conv2=nn.Conv2d(32,64,3,padding=1); s.conv3=nn.Conv2d(64,64,3,padding=1)
        s.pool=nn.MaxPool2d(2,2); s.fc1=nn.Linear(64*4*4,64); s.fc2=nn.Linear(64,10)
    def forward(s,x):
        x=s.pool(F.relu(s.conv1(x))); x=s.pool(F.relu(s.conv2(x))); x=s.pool(F.relu(s.conv3(x)))
        return s.fc2(F.relu(s.fc1(x.view(-1,64*4*4))))
def conf(m,ds,n=2000):
    m.eval(); out=[]
    with torch.no_grad():
        for xb,_ in DataLoader(Subset(ds,list(range(n))),batch_size=512):
            out.append(F.softmax(m(xb.to(dev)),1).max(1).values.cpu().numpy())
    m.train(); return np.concatenate(out)
def mia(m):
    mem=conf(m,train); non=conf(m,test); n=min(len(mem),len(non)); mem=mem[:n]; non=non[:n]
    allc=np.concatenate([mem,non]); lab=np.concatenate([np.ones(n),np.zeros(n)]); best=0
    for t in np.percentile(allc,np.linspace(0,100,500)): best=max(best,np.mean((allc>=t).astype(int)==lab))
    return best-0.5
def acc(m):
    m.eval(); c=t=0
    with torch.no_grad():
        for xb,yb in test_loader: c+=(m(xb.to(dev)).argmax(1).cpu()==yb).sum().item(); t+=len(yb)
    m.train(); return c/t
results=[]
for sd in [1,2,3,5,8,11,13,21,34,55,89,144]:
    torch.manual_seed(sd); np.random.seed(sd)
    tl=DataLoader(train,batch_size=BATCH_SIZE,shuffle=True)
    m=ModuleValidator.fix(SVHNCNN()).to(dev); opt=optim.SGD(m.parameters(),lr=DP_LR,momentum=0.9)
    pe=PrivacyEngine(accountant="rdp")
    m,opt,tl=pe.make_private_with_epsilon(module=m,optimizer=opt,data_loader=tl,
        target_epsilon=TARGET_EPSILON,target_delta=DELTA,epochs=DP_EPOCHS,max_grad_norm=MAX_GRAD_NORM)
    crit=nn.CrossEntropyLoss(); t0=time.time()
    for ep in range(DP_EPOCHS):
        for xb,yb in tl:
            xb,yb=xb.to(dev),yb.to(dev); opt.zero_grad(); crit(m(xb),yb).backward(); opt.step()
    a=acc(m); mv=mia(m)
    fn=f"models_hunt/seed{sd}_mia{mv:.4f}_acc{a:.3f}.safetensors"
    save_file({k:v.cpu() for k,v in m._module.state_dict().items()},fn)
    results.append((mv,a,sd,fn)); results.sort()
    print(f"seed {sd}: acc {a:.4f} local_mia {mv:.4f} ({time.time()-t0:.0f}s) -> {fn}",flush=True)
    print("  TOP3 so far: "+", ".join(f"{r[0]:.4f}(s{r[2]})" for r in results[:3]),flush=True)
print("DONE. sorted by local_mia:",flush=True)
for mv,a,sd,fn in results: print(f"  {mv:.4f} acc {a:.3f} seed {sd} {fn}",flush=True)
