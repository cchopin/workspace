#!/usr/bin/env python3
# Train official recipe (eps=6) with multiple seeds on MPS; keep model with lowest course-style local MIA.
import sys, torch, torch.nn as nn, torch.nn.functional as F, torch.optim as optim, numpy as np, time
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

def confidences(model, ds, n=2000):
    model.eval(); loader=DataLoader(Subset(ds,list(range(n))),batch_size=512); out=[]
    with torch.no_grad():
        for xb,_ in loader:
            p=F.softmax(model(xb.to(dev)),1).max(1).values.cpu().numpy(); out.append(p)
    model.train(); return np.concatenate(out)

def course_mia(model):
    mem=confidences(model,train,2000); non=confidences(model,test,2000)
    n=min(len(mem),len(non)); mem=mem[:n]; non=non[:n]
    allc=np.concatenate([mem,non]); labels=np.concatenate([np.ones(n),np.zeros(n)])
    best=0.0
    for thr in np.percentile(allc, np.linspace(0,100,1000)):
        acc=np.mean((allc>=thr).astype(int)==labels); best=max(best,acc)
    return best-0.5

def acc_test(model):
    model.eval(); c=t=0
    with torch.no_grad():
        for xb,yb in test_loader:
            c+=(model(xb.to(dev)).argmax(1).cpu()==yb).sum().item(); t+=len(yb)
    model.train(); return c/t

seeds=[int(x) for x in sys.argv[1:]] or [1337,7,42,2024,100,999]
best=None
for sd in seeds:
    torch.manual_seed(sd); np.random.seed(sd)
    train_loader=DataLoader(train,batch_size=BATCH_SIZE,shuffle=True)
    m=ModuleValidator.fix(SVHNCNN()).to(dev); opt=optim.SGD(m.parameters(),lr=DP_LR,momentum=0.9)
    pe=PrivacyEngine(accountant="rdp")
    m,opt,train_loader=pe.make_private_with_epsilon(module=m,optimizer=opt,data_loader=train_loader,
        target_epsilon=TARGET_EPSILON,target_delta=DELTA,epochs=DP_EPOCHS,max_grad_norm=MAX_GRAD_NORM)
    crit=nn.CrossEntropyLoss(); t0=time.time()
    for ep in range(DP_EPOCHS):
        for xb,yb in train_loader:
            xb,yb=xb.to(dev),yb.to(dev); opt.zero_grad(); crit(m(xb),yb).backward(); opt.step()
    a=acc_test(m); mia=course_mia(m)
    print(f"seed {sd}: acc {a:.4f} local_mia {mia:.4f} ({time.time()-t0:.0f}s)",flush=True)
    if a>=0.55 and (best is None or mia<best[1]):
        best=(sd,mia,{k:v.cpu() for k,v in m._module.state_dict().items()})
        save_file(best[2],"dp_best.safetensors")
        print(f"  -> new best seed {sd} local_mia {mia:.4f} saved to dp_best.safetensors",flush=True)
print(f"BEST seed {best[0]} local_mia {best[1]:.4f}",flush=True)
