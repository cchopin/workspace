#!/usr/bin/env python3
"""Task 3 (OmniDigit) - train an MNIST surrogate OCR and label the 30 public bank tiles.
The debug console states decision boundaries are consistent with independently trained
instances on the same distribution, so a canonical MNIST CNN transfers.
"""
import glob, os, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
import torchvision, torchvision.transforms as T

dev = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
BANK = "exam/loot/omnidigit/bank"
DATA = "solve/.mnist"

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1=nn.Conv2d(1,32,3,padding=1); self.c2=nn.Conv2d(32,64,3,padding=1)
        self.fc1=nn.Linear(64*7*7,128); self.fc2=nn.Linear(128,10)
    def forward(self,x):
        x=F.max_pool2d(F.relu(self.c1(x)),2)
        x=F.max_pool2d(F.relu(self.c2(x)),2)
        x=torch.flatten(x,1)
        return self.fc2(F.relu(self.fc1(x)))

def train():
    tf=T.Compose([T.ToTensor(), T.Normalize((0.1307,),(0.3081,))])
    tr=torchvision.datasets.MNIST(DATA,train=True,download=True,transform=tf)
    dl=torch.utils.data.DataLoader(tr,batch_size=256,shuffle=True)
    net=Net().to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
    net.train()
    for ep in range(3):
        for xb,yb in dl:
            xb,yb=xb.to(dev),yb.to(dev)
            opt.zero_grad(); loss=F.cross_entropy(net(xb),yb); loss.backward(); opt.step()
        print("epoch",ep,"loss",float(loss))
    torch.save(net.state_dict(), "solve/.mnist_cnn.pt")
    return net

mp="solve/.mnist_cnn.pt"
net=Net().to(dev)
if os.path.exists(mp):
    net.load_state_dict(torch.load(mp,map_location=dev)); print("loaded surrogate")
else:
    net=train()
net.eval()

MEAN,STD=0.1307,0.3081
def classify(arr):  # arr 28x28 float 0..1, MNIST style (white on black)
    t=torch.from_numpy(((arr-MEAN)/STD).astype(np.float32)).view(1,1,28,28).to(dev)
    with torch.no_grad(): p=F.softmax(net(t),1)[0].cpu().numpy()
    return int(p.argmax()), float(p.max()), p

# figure polarity: MNIST is bright digit on dark bg. Check bank tile mean.
files=sorted(glob.glob(f"{BANK}/tile_*.png"), key=lambda f:int(f.split('_')[-1].split('.')[0]))
sample=np.asarray(Image.open(files[0]).convert("L"),dtype=np.float32)/255.0
print("sample mean",sample.mean(),"-> ", "likely dark-on-light (invert)" if sample.mean()>0.5 else "likely light-on-dark")

rows=[]
for f in files:
    tid=int(f.split('_')[-1].split('.')[0])
    a=np.asarray(Image.open(f).convert("L"),dtype=np.float32)/255.0
    # try both polarities, keep most confident
    d1,c1,_=classify(a)
    d2,c2,_=classify(1.0-a)
    if c2>c1: digit,conf,inv=d2,c2,True
    else: digit,conf,inv=d1,c1,False
    rows.append((tid,digit,conf,inv))

rows.sort(key=lambda r:-r[2])
print("\ntile_id  digit  conf  inverted")
for tid,d,c,inv in sorted(rows,key=lambda r:r[0]):
    print(f"  {tid:>3}     {d}    {c:.3f}   {inv}")

# summarize which tiles read as each digit (conf>0.8)
from collections import defaultdict
by=defaultdict(list)
for tid,d,c,inv in rows:
    if c>0.8: by[d].append((tid,round(c,3)))
print("\nconfident tiles by digit:")
for d in range(10):
    print(f"  {d}: {by[d]}")
