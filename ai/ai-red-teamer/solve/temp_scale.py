import sys, torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from safetensors.torch import load_file, save_file
T=float(sys.argv[1]) if len(sys.argv)>1 else 30.0
MEAN=(0.4377,0.4438,0.4728); STD=(0.1980,0.2010,0.1970)
tf=transforms.Compose([transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
test=datasets.SVHN("data",split='test',download=True,transform=tf)
class SVHNCNN(nn.Module):
    def __init__(s):
        super().__init__(); s.conv1=nn.Conv2d(3,32,3,padding=1); s.conv2=nn.Conv2d(32,64,3,padding=1); s.conv3=nn.Conv2d(64,64,3,padding=1)
        s.pool=nn.MaxPool2d(2,2); s.fc1=nn.Linear(64*4*4,64); s.fc2=nn.Linear(64,10)
    def forward(s,x):
        x=s.pool(F.relu(s.conv1(x))); x=s.pool(F.relu(s.conv2(x))); x=s.pool(F.relu(s.conv3(x)))
        return s.fc2(F.relu(s.fc1(x.view(-1,64*4*4))))
sd=load_file("dp_model.safetensors")
m=SVHNCNN(); m.load_state_dict(sd); m.eval()
te=DataLoader(test,batch_size=512)
def acc_conf():
    c=t=0; confs=[]
    with torch.no_grad():
        for xb,yb in te:
            out=m(xb); c+=(out.argmax(1)==yb).sum().item(); t+=len(yb)
            confs+=F.softmax(out,1).max(1).values.tolist()
    return c/t, float(np.mean(confs)), float(np.std(confs))
a0,mc0,sc0=acc_conf(); print(f"before: acc {a0:.4f} conf mean {mc0:.3f} std {sc0:.3f}")
# temperature scale: divide final layer by T -> flatter softmax
with torch.no_grad():
    m.fc2.weight.div_(T); m.fc2.bias.div_(T)
a1,mc1,sc1=acc_conf(); print(f"after T={T}: acc {a1:.4f} conf mean {mc1:.3f} std {sc1:.3f}")
save_file(m.state_dict(),"dp_model.safetensors"); print("SAVED temperature-scaled model")
