#!/usr/bin/env python3
# Targeted L2 adversarial attack (DeepFool-style / PGD-L2) on MNIST SimpleClassifier.
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
def l2(a,b): return float(np.sqrt(np.sum((a-b)**2)))

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
x = x01_from_b64(ch["image_b64"]); lab=int(ch["label"]); tgt=int(ch["target"]); thr=float(ch["l2_threshold"])
print("label",lab,"target",tgt,"l2_threshold",thr)
open("/tmp/df_w.pth","wb").write(requests.get(f"{BASE_URL}/weights",timeout=15).content)
model = SimpleClassifier().eval()
model.load_state_dict(torch.load("/tmp/df_w.pth",map_location="cpu"))
xt = torch.from_numpy(x[None,None,...]).float()
print("local clean pred", int(model(xt).argmax(1)))

def project_l2(delta, radius):
    n = delta.view(-1).norm(2).item()
    if n > radius:
        delta = delta * (radius / (n + 1e-12))
    return delta

# margin below threshold to survive PNG quantization
budget = thr * 0.9
x_adv = xt.clone().detach()
best = None
for i in range(300):
    x_adv.requires_grad_(True)
    out = model(x_adv)
    loss = nn.functional.nll_loss(out, torch.tensor([tgt]))  # minimize -> push toward target
    model.zero_grad(); loss.backward()
    g = x_adv.grad.detach()
    gn = g.view(-1).norm(2) + 1e-12
    with torch.no_grad():
        step = 0.1  # L2 step size
        x_adv = x_adv - step * g / gn
        delta = project_l2(x_adv - xt, budget)
        x_adv = (xt + delta).clamp(0,1)
    x_adv = x_adv.detach()
    pred = int(model(x_adv).argmax(1))
    cur_l2 = l2(x, x_adv.squeeze().numpy())
    if pred == tgt and cur_l2 <= thr:
        best = x_adv.clone();
        # try to shrink further
        budget = min(budget, cur_l2*0.98)
    if i % 50 == 0:
        print(f"iter {i} pred {pred} l2 {cur_l2:.3f}")

use = best if best is not None else x_adv
xadv_np = use.squeeze().numpy()
b64 = b64_from_x01(xadv_np)
xrt = x01_from_b64(b64)
print("final l2 after PNG", l2(x, xrt), "thr", thr, "pred", requests.post(f"{BASE_URL}/predict",json={'image_b64':b64},timeout=15).json())
r = requests.post(f"{BASE_URL}/submit",json={"image_b64":b64},timeout=15)
print("SUBMIT", r.status_code, r.text)
