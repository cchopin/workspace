import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
from safetensors.torch import save_file
torch.manual_seed(1); np.random.seed(1)
tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.4377,0.4438,0.4728),(0.1980,0.2010,0.1970))])
train=datasets.SVHN("data",split='train',download=True,transform=tf); test=datasets.SVHN("data",split='test',download=True,transform=tf)
class SVHNCNN(nn.Module):
    def __init__(s):
        super().__init__(); s.conv1=nn.Conv2d(3,32,3,padding=1); s.conv2=nn.Conv2d(32,64,3,padding=1); s.conv3=nn.Conv2d(64,64,3,padding=1)
        s.pool=nn.MaxPool2d(2,2); s.fc1=nn.Linear(64*4*4,64); s.fc2=nn.Linear(64,10)
    def forward(s,x):
        x=s.pool(F.relu(s.conv1(x))); x=s.pool(F.relu(s.conv2(x))); x=s.pool(F.relu(s.conv3(x)))
        return s.fc2(F.relu(s.fc1(x.view(-1,64*4*4))))
# train on a SMALL subset to force overfitting (high MIA)
idx=np.random.choice(len(train),5000,replace=False)
tl=DataLoader(Subset(train,idx.tolist()),batch_size=128,shuffle=True)
te=DataLoader(test,batch_size=512)
m=SVHNCNN(); opt=torch.optim.Adam(m.parameters(),1e-3)
for ep in range(30):
    m.train()
    for xb,yb in tl:
        opt.zero_grad(); F.cross_entropy(m(xb),yb).backward(); opt.step()
m.eval(); c=t=0
with torch.no_grad():
    for xb,yb in te: c+=(m(xb).argmax(1)==yb).sum().item(); t+=len(yb)
print("test acc",c/t)
save_file(m.state_dict(),"nondp_model.safetensors"); print("SAVED")
