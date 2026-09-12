#!/usr/bin/env python3
# PATE on EMNIST Letters: teachers on disjoint partitions -> noisy aggregated labels -> student MLP.
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets
from sklearn.preprocessing import StandardScaler
from safetensors.torch import save_file
torch.manual_seed(1337); np.random.seed(1337)

train=datasets.EMNIST("data",split='letters',train=True,download=True)
test=datasets.EMNIST("data",split='letters',train=False,download=True)
Xtr=train.data.numpy().reshape(-1,784).astype(np.float32)/255.0
Xte=test.data.numpy().reshape(-1,784).astype(np.float32)/255.0
ytr=train.targets.numpy()-1; yte=test.targets.numpy()-1
scaler=StandardScaler().fit(Xtr)
Xtr=scaler.transform(Xtr).astype(np.float32); Xte=scaler.transform(Xte).astype(np.float32)

class MLP(nn.Module):
    def __init__(self,input_size=784,hidden_layers=(256,128),num_classes=26,dropout=0.2):
        super().__init__(); self.layers=nn.ModuleList(); self.dropouts=nn.ModuleList()
        prev=input_size
        for h in hidden_layers:
            self.layers.append(nn.Linear(prev,h)); self.dropouts.append(nn.Dropout(dropout)); prev=h
        self.output=nn.Linear(prev,num_classes)
    def forward(self,x):
        for l,d in zip(self.layers,self.dropouts):
            x=d(F.relu(l(x)))
        return self.output(x)

def train_model(Xt,yt,epochs=12,bs=256,lr=1e-3,dropout=0.2):
    m=MLP(dropout=dropout); opt=torch.optim.Adam(m.parameters(),lr=lr)
    Xt=torch.tensor(Xt); yt=torch.tensor(yt).long(); n=len(Xt)
    for ep in range(epochs):
        perm=torch.randperm(n)
        m.train()
        for i in range(0,n,bs):
            idx=perm[i:i+bs]; opt.zero_grad()
            loss=F.cross_entropy(m(Xt[idx]),yt[idx]); loss.backward(); opt.step()
    return m

def acc(m,X,y):
    m.eval()
    with torch.no_grad():
        p=m(torch.tensor(X)).argmax(1).numpy()
    return (p==y).mean()

# Split: private (teachers) vs public (student queries)
N=len(Xtr); idx=np.random.permutation(N)
priv=idx[:100000]; pub=idx[100000:]           # ~24800 public
NUM_T=25
parts=np.array_split(priv,NUM_T)
print("teachers",NUM_T,"public",len(pub),flush=True)
# teacher votes on public
votes=np.zeros((len(pub),26),dtype=np.float64)
for ti,part in enumerate(parts):
    t=train_model(Xtr[part],ytr[part],epochs=14,dropout=0.1)
    with torch.no_grad():
        pv=t(torch.tensor(Xtr[pub])).argmax(1).numpy()
    for j,c in enumerate(pv): votes[j,c]+=1
    print("teacher",ti+1,"done teacher_acc",round(float(acc(t,Xte,yte)),3),flush=True)
# noisy aggregation (Laplace scale tuned for 25 teachers; large scale destroys signal)
noise=np.random.laplace(0.0,0.3,size=votes.shape)
noisy=votes+noise
labels=noisy.argmax(1)
print("label agreement with true:",round(float((labels==ytr[pub]).mean()),3),flush=True)
# train student on public + noisy labels
student=train_model(Xtr[pub],labels,epochs=90,dropout=0.15)
print("STUDENT test acc",round(float(acc(student,Xte,yte)),4),flush=True)
save_file(student.state_dict(),"pate_student.safetensors")
print("SAVED pate_student.safetensors",flush=True)
