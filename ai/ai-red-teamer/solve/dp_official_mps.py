#!/usr/bin/env python3
import torch, torch.nn as nn, torch.nn.functional as F, torch.optim as optim, numpy as np, time
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator
from safetensors.torch import save_file
RANDOM_SEED=1337; BATCH_SIZE=256; DP_EPOCHS=20; DP_LR=0.1; MAX_GRAD_NORM=1.0; DELTA=1e-5; TARGET_EPSILON=6.0
torch.manual_seed(RANDOM_SEED); np.random.seed(RANDOM_SEED)
dev=torch.device("mps")
SVHN_MEAN=(0.4377,0.4438,0.4728); SVHN_STD=(0.1980,0.2010,0.1970)
tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize(SVHN_MEAN,SVHN_STD)])
train=datasets.SVHN("data",split='train',download=False,transform=tf)
test=datasets.SVHN("data",split='test',download=False,transform=tf)
train_loader=DataLoader(train,batch_size=BATCH_SIZE,shuffle=True)
test_loader=DataLoader(test,batch_size=512)
class SVHNCNN(nn.Module):
    def __init__(s):
        super().__init__()
        s.conv1=nn.Conv2d(3,32,3,padding=1); s.conv2=nn.Conv2d(32,64,3,padding=1); s.conv3=nn.Conv2d(64,64,3,padding=1)
        s.pool=nn.MaxPool2d(2,2); s.fc1=nn.Linear(64*4*4,64); s.fc2=nn.Linear(64,10)
    def forward(s,x):
        x=s.pool(F.relu(s.conv1(x))); x=s.pool(F.relu(s.conv2(x))); x=s.pool(F.relu(s.conv3(x)))
        return s.fc2(F.relu(s.fc1(x.view(-1,64*4*4))))
dp_model=ModuleValidator.fix(SVHNCNN()).to(dev)
optimizer=optim.SGD(dp_model.parameters(),lr=DP_LR,momentum=0.9)
pe=PrivacyEngine(accountant="rdp")
dp_model,optimizer,train_loader=pe.make_private_with_epsilon(module=dp_model,optimizer=optimizer,data_loader=train_loader,
    target_epsilon=TARGET_EPSILON,target_delta=DELTA,epochs=DP_EPOCHS,max_grad_norm=MAX_GRAD_NORM)
def acc():
    dp_model.eval(); c=t=0
    with torch.no_grad():
        for xb,yb in test_loader:
            xb=xb.to(dev); c+=(dp_model(xb).argmax(1).cpu()==yb).sum().item(); t+=len(yb)
    dp_model.train(); return c/t
crit=nn.CrossEntropyLoss()
for ep in range(DP_EPOCHS):
    dp_model.train(); t0=time.time()
    for xb,yb in train_loader:
        xb,yb=xb.to(dev),yb.to(dev); optimizer.zero_grad(); crit(dp_model(xb),yb).backward(); optimizer.step()
    print(f"epoch {ep+1}/{DP_EPOCHS} acc {acc():.4f} eps {pe.get_epsilon(DELTA):.2f} ({time.time()-t0:.0f}s)",flush=True)
save_file({k:v.cpu() for k,v in dp_model._module.state_dict().items()},"dp_model.safetensors")
print("SAVED final acc",round(acc(),4),"eps",round(pe.get_epsilon(DELTA),2),flush=True)
