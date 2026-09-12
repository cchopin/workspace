#!/usr/bin/env python3
# Train SVHNCNN with strong DP-SGD -> dp_model.safetensors. Reports local MIA estimate.
import sys, torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
from opacus import PrivacyEngine
from safetensors.torch import save_file
import numpy as np
torch.manual_seed(1337); np.random.seed(1337)

NOISE=float(sys.argv[1]) if len(sys.argv)>1 else 2.0
ACC_STOP=float(sys.argv[2]) if len(sys.argv)>2 else 0.63
SVHN_MEAN=(0.4377,0.4438,0.4728); SVHN_STD=(0.1980,0.2010,0.1970)
tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize(SVHN_MEAN,SVHN_STD)])
train=datasets.SVHN("data",split='train',download=True,transform=tf)
test=datasets.SVHN("data",split='test',download=True,transform=tf)

class SVHNCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1=nn.Conv2d(3,32,3,padding=1); self.conv2=nn.Conv2d(32,64,3,padding=1)
        self.conv3=nn.Conv2d(64,64,3,padding=1); self.pool=nn.MaxPool2d(2,2)
        self.fc1=nn.Linear(64*4*4,64); self.fc2=nn.Linear(64,10)
    def forward(self,x):
        x=self.pool(F.relu(self.conv1(x))); x=self.pool(F.relu(self.conv2(x))); x=self.pool(F.relu(self.conv3(x)))
        x=x.view(-1,64*4*4); x=F.relu(self.fc1(x)); return self.fc2(x)

idx=np.random.choice(len(train),30000,replace=False)
member_idx=idx.tolist()
tr=Subset(train,member_idx)
train_loader=DataLoader(tr,batch_size=256,shuffle=True)
test_loader=DataLoader(test,batch_size=512)
model=SVHNCNN()
opt=torch.optim.SGD(model.parameters(),lr=0.1,momentum=0.9)
pe=PrivacyEngine()
model,opt,train_loader=pe.make_private(module=model,optimizer=opt,data_loader=train_loader,
    noise_multiplier=NOISE,max_grad_norm=1.0)

def acc():
    model.eval(); c=t=0
    with torch.no_grad():
        for xb,yb in test_loader:
            c+=(model(xb).argmax(1)==yb).sum().item(); t+=len(yb)
    model.train(); return c/t

def losses_for(dataset, indices, n=2000):
    model.eval(); ls=[]
    sel=indices[:n]
    with torch.no_grad():
        for i in range(0,len(sel),512):
            batch=[dataset[j] for j in sel[i:i+512]]
            xb=torch.stack([b[0] for b in batch]); yb=torch.tensor([b[1] for b in batch])
            l=F.cross_entropy(model(xb),yb,reduction='none')
            ls.extend(l.tolist())
    model.train(); return np.array(ls)

def local_mia():
    # members: training subset; non-members: test set
    mem=losses_for(train, member_idx, 2000)
    non=losses_for(test, list(range(len(test))), 2000)
    # threshold attack: predict member if loss < thr; advantage = max balanced-acc - 0.5
    allv=np.concatenate([mem,non]); best=0
    for thr in np.quantile(allv, np.linspace(0.01,0.99,99)):
        tpr=(mem<thr).mean(); fpr=(non<thr).mean()
        acc_bal=0.5*(tpr+(1-fpr))
        best=max(best,acc_bal)
    return best-0.5

for ep in range(20):
    for xb,yb in train_loader:
        opt.zero_grad(); F.cross_entropy(model(xb),yb).backward(); opt.step()
    a=acc(); mia=local_mia()
    print(f"epoch {ep+1} acc {a:.4f} eps {pe.get_epsilon(1e-5):.2f} local_mia {mia:.4f}",flush=True)
    if a>=ACC_STOP: break

save_file(model._module.state_dict(),"dp_model.safetensors")
print("SAVED final_acc",round(acc(),4),"local_mia",round(local_mia(),4),flush=True)
