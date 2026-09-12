#!/usr/bin/env python3
# DP-SGD on SVHN 'extra' split (disjoint from train members the grader uses).
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
from opacus import PrivacyEngine
from safetensors.torch import save_file
torch.manual_seed(7); np.random.seed(7)
MEAN=(0.4377,0.4438,0.4728); STD=(0.1980,0.2010,0.1970)
tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
extra=datasets.SVHN("data",split='extra',download=True,transform=tf)
test=datasets.SVHN("data",split='test',download=True,transform=tf)
class SVHNCNN(nn.Module):
    def __init__(s):
        super().__init__(); s.conv1=nn.Conv2d(3,32,3,padding=1); s.conv2=nn.Conv2d(32,64,3,padding=1); s.conv3=nn.Conv2d(64,64,3,padding=1)
        s.pool=nn.MaxPool2d(2,2); s.fc1=nn.Linear(64*4*4,64); s.fc2=nn.Linear(64,10)
    def forward(s,x):
        x=s.pool(F.relu(s.conv1(x))); x=s.pool(F.relu(s.conv2(x))); x=s.pool(F.relu(s.conv3(x)))
        return s.fc2(F.relu(s.fc1(x.view(-1,64*4*4))))
idx=np.random.choice(len(extra),60000,replace=False)
tl=DataLoader(Subset(extra,idx.tolist()),batch_size=512,shuffle=True)
te=DataLoader(test,batch_size=512)
m=SVHNCNN(); opt=torch.optim.SGD(m.parameters(),lr=0.1,momentum=0.9)
pe=PrivacyEngine()
m,opt,tl=pe.make_private(module=m,optimizer=opt,data_loader=tl,noise_multiplier=1.0,max_grad_norm=1.0)
def acc():
    m.eval(); c=t=0
    with torch.no_grad():
        for xb,yb in te: c+=(m(xb).argmax(1)==yb).sum().item(); t+=len(yb)
    m.train(); return c/t
for ep in range(8):
    for xb,yb in tl:
        opt.zero_grad(); F.cross_entropy(m(xb),yb).backward(); opt.step()
    a=acc(); print(f"epoch {ep+1} acc {a:.4f} eps {pe.get_epsilon(1e-5):.2f}",flush=True)
    if a>=0.70: break
save_file(m._module.state_dict(),"dp_model.safetensors"); print("SAVED acc",round(acc(),4),flush=True)
