#!/usr/bin/env python3
import os, io, base64, numpy as np, requests, torch, torch.nn as nn
from PIL import Image
BASE_URL = os.environ["BASE_URL"]
MNIST_MEAN, MNIST_STD = 0.1307, 0.3081

def x01_from_b64(b64):
    raw = base64.b64decode(b64); img = Image.open(io.BytesIO(raw)).convert("L")
    return np.clip(np.asarray(img, np.float32)/255.0, 0, 1)
def b64_from_x01(x2d):
    x255 = np.clip((x2d*255.0).round(),0,255).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(x255, mode="L").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()
def linf(a,b): return float(np.max(np.abs(a-b)))

class SimpleClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1=nn.Conv2d(1,32,3,1); self.conv2=nn.Conv2d(32,64,3,1)
        self.dropout1=nn.Dropout(0.25); self.dropout2=nn.Dropout(0.5)
        self.fc1=nn.Linear(9216,128); self.fc2=nn.Linear(128,10)
    def forward(self,x01):
        x=(x01-MNIST_MEAN)/MNIST_STD
        x=torch.relu(self.conv1(x)); x=torch.relu(self.conv2(x))
        x=torch.max_pool2d(x,2); x=self.dropout1(x); x=torch.flatten(x,1)
        x=torch.relu(self.fc1(x)); x=self.dropout2(x); x=self.fc2(x)
        return torch.log_softmax(x,dim=1)

ch = requests.get(f"{BASE_URL}/challenge",timeout=15).json()
x = x01_from_b64(ch["image_b64"]); lab=int(ch["label"]); eps=float(ch["epsilon"])
print("label",lab,"eps",eps)
wt = requests.get(f"{BASE_URL}/weights",timeout=15).content
open("/tmp/fgsm_w.pth","wb").write(wt)
model = SimpleClassifier().eval()
model.load_state_dict(torch.load("/tmp/fgsm_w.pth",map_location="cpu"))

xt = torch.from_numpy(x[None,None,...]).float()
print("local pred clean", int(model(xt).argmax(1)))

alpha = eps/4 if eps>0.05 else eps
x_adv = xt.clone().detach()
for i in range(50):
    x_adv.requires_grad_(True)
    out = model(x_adv)
    loss = nn.functional.nll_loss(out, torch.tensor([lab]))
    model.zero_grad(); loss.backward()
    with torch.no_grad():
        x_adv = x_adv + alpha*x_adv.grad.sign()
        x_adv = torch.max(torch.min(x_adv, xt+eps), xt-eps).clamp(0,1)
    x_adv = x_adv.detach()
    pred = int(model(x_adv).argmax(1))
    if pred != lab:
        print("misclassified at iter",i,"->",pred); break

xadv_np = x_adv.squeeze().numpy()
b64 = b64_from_x01(xadv_np)
xrt = x01_from_b64(b64)
print("linf after PNG roundtrip", linf(x, xrt), "budget", eps)
sp = requests.post(f"{BASE_URL}/predict",json={"image_b64":b64},timeout=15).json()
print("server pred", sp)
r = requests.post(f"{BASE_URL}/submit",json={"image_b64":b64},timeout=15)
print("SUBMIT", r.status_code, r.text)
