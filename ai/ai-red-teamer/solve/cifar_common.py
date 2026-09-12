import io, base64, numpy as np, torch, torch.nn as nn
from PIL import Image
MEAN = torch.tensor([0.4914,0.4822,0.4465]).view(1,3,1,1)
STD  = torch.tensor([0.247,0.2435,0.2616]).view(1,3,1,1)

class CIFAR10CNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.conv1=nn.Conv2d(3,32,3,padding=1); self.bn1=nn.BatchNorm2d(32); self.relu1=nn.ReLU(); self.pool1=nn.MaxPool2d(2,2)
        self.conv2=nn.Conv2d(32,64,3,padding=1); self.bn2=nn.BatchNorm2d(64); self.relu2=nn.ReLU(); self.pool2=nn.MaxPool2d(2,2)
        self.fc1=nn.Linear(64*8*8,128); self.relu3=nn.ReLU(); self.dropout=nn.Dropout(0.5); self.fc2=nn.Linear(128,num_classes)
    def forward(self,x):
        x=self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x=self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x=x.reshape(x.size(0),-1)
        x=self.dropout(self.relu3(self.fc1(x)))
        return self.fc2(x)

def load_model(path):
    ck=torch.load(path,map_location="cpu")
    m=CIFAR10CNN()
    sd=ck["model_state_dict"] if isinstance(ck,dict) and "model_state_dict" in ck else ck
    m.load_state_dict(sd); m.eval(); return m

def img01_from_b64(b64):
    raw=base64.b64decode(b64); im=Image.open(io.BytesIO(raw)).convert("RGB")
    return np.asarray(im,np.float32)/255.0            # (32,32,3)
def b64_from_img01(a):
    a=np.clip((a*255.0).round(),0,255).astype(np.uint8)
    buf=io.BytesIO(); Image.fromarray(a,mode="RGB").save(buf,format="PNG");
    return base64.b64encode(buf.getvalue()).decode()
def to_tensor01(a):  # (32,32,3)->(1,3,32,32)
    return torch.from_numpy(a.transpose(2,0,1)[None,...]).float()
def to_img01(t):     # (1,3,32,32)->(32,32,3)
    return t.detach().squeeze(0).permute(1,2,0).numpy()
def normalize(t): return (t-MEAN)/STD
def denormalize(z): return z*STD+MEAN
