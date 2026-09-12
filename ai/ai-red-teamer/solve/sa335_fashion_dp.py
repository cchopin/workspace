#!/usr/bin/env python3
# 335 Skills Assessment: DP-SGD FashionMNISTCNN -> defended_model.safetensors (acc>=70%, MIA reduced >=40%).
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
import torchvision, torchvision.transforms as transforms
from torch.utils.data import DataLoader, Subset
from opacus import PrivacyEngine
from safetensors.torch import save_file
torch.manual_seed(1337); np.random.seed(1337)

tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.2860,),(0.3530,))])
train=torchvision.datasets.FashionMNIST('./data',train=True,download=True,transform=tf)
test=torchvision.datasets.FashionMNIST('./data',train=False,download=True,transform=tf)

class FashionMNISTCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1=nn.Conv2d(1,32,3,padding=1); self.conv2=nn.Conv2d(32,64,3,padding=1); self.conv3=nn.Conv2d(64,64,3,padding=1)
        self.pool=nn.MaxPool2d(2,2); self.relu=nn.ReLU()
        self.fc1=nn.Linear(64*3*3,128); self.fc2=nn.Linear(128,10)
    def forward(self,x):
        x=self.pool(self.relu(self.conv1(x))); x=self.pool(self.relu(self.conv2(x))); x=self.pool(self.relu(self.conv3(x)))
        x=x.view(-1,64*3*3); x=self.relu(self.fc1(x)); return self.fc2(x)

idx=np.random.choice(len(train),30000,replace=False)
tr=Subset(train,idx.tolist())
train_loader=DataLoader(tr,batch_size=256,shuffle=True)
test_loader=DataLoader(test,batch_size=512)
model=FashionMNISTCNN()
opt=torch.optim.SGD(model.parameters(),lr=0.1,momentum=0.9)
pe=PrivacyEngine()
model,opt,train_loader=pe.make_private(module=model,optimizer=opt,data_loader=train_loader,
    noise_multiplier=0.8,max_grad_norm=1.0)

def acc():
    model.eval(); c=t=0
    with torch.no_grad():
        for xb,yb in test_loader:
            c+=(model(xb).argmax(1)==yb).sum().item(); t+=len(yb)
    model.train(); return c/t

for ep in range(10):
    for xb,yb in train_loader:
        opt.zero_grad(); F.cross_entropy(model(xb),yb).backward(); opt.step()
    a=acc(); print(f"epoch {ep+1} acc {a:.4f} eps {pe.get_epsilon(1e-5):.2f}",flush=True)
    if a>=0.80: break
save_file(model._module.state_dict(),"defended_model.safetensors")
print("SAVED defended_model.safetensors final_acc",acc(),flush=True)
