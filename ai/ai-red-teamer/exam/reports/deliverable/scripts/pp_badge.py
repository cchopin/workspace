#!/usr/bin/env python3
"""Task 1 (PassPort) - craft an adversarial badge classified as 'admin'.

Pipeline replicated from /passport/docs:
  seal-mask -> grayscale(BT.601) -> resize 256x384 -> 64x96 (nearest) -> normalize(0.5,0.25)
Constraints: HoloSeal region [209,318,238,339] must stay identical to the reference
(HMAC), and L-inf per-channel deviation <= 18 (uint8) everywhere else.
"""
import json, sys
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image

EXAM = "exam"
A = f"{EXAM}/loot/passport"
dev = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")

NUM_CLASSES = 3
class BadgeClassifier(nn.Module):
    def __init__(self, num_classes=NUM_CLASSES):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3,16,3,padding=1), nn.ReLU(inplace=True), nn.MaxPool2d(2),
            nn.Conv2d(16,32,3,padding=1), nn.ReLU(inplace=True), nn.MaxPool2d(2),
            nn.Conv2d(32,64,3,padding=1), nn.ReLU(inplace=True), nn.AdaptiveAvgPool2d((1,1)),
        )
        self.classifier = nn.Linear(64, num_classes)
    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)

cfg = json.load(open(f"{A}/auth_config.json"))
X1,Y1,X2,Y2 = cfg["auth_bbox"]          # [209,318,238,339] (x1,y1,x2,y2)
EPS = float(cfg["eps_uint8"])           # 18
TARGET = int(cfg["target_class"])       # 2 = admin

model = BadgeClassifier().to(dev)
sd = torch.load(f"{A}/passport_model.pth", map_location="cpu", weights_only=True)
if isinstance(sd, dict) and "state_dict" in sd: sd = sd["state_dict"]
model.load_state_dict(sd); model.eval()

MU, SIG = 0.5, 0.25
GW = torch.tensor([0.2989,0.5870,0.1140], device=dev).view(1,3,1,1)

def preprocess(img_chw01):
    """img_chw01: (1,3,384,256) float in [0,1]. Returns normalized (1,3,96,64)."""
    x = img_chw01.clone()
    # seal -> white (1.0)
    x[:,:,Y1:Y2,X1:X2] = 1.0
    # grayscale BT.601, replicate to 3ch
    y = (x*GW).sum(1, keepdim=True)
    y = y.repeat(1,3,1,1)
    # resize to 64x96 (H=96,W=64) nearest
    y = F.interpolate(y, size=(96,64), mode="nearest")
    # normalize
    return (y-MU)/SIG

ref = np.asarray(Image.open(f"{A}/visitor_badge.png").convert("RGB"), dtype=np.float32)  # (384,256,3)
ref_t = torch.from_numpy(ref).permute(2,0,1).unsqueeze(0).to(dev)  # (1,3,384,256) 0..255

def predict(u8_chw):
    with torch.no_grad():
        logits = model(preprocess(u8_chw/255.0))
    return logits

print("device", dev, "| ref logits:", predict(ref_t).cpu().numpy().round(3),
      "-> class", int(predict(ref_t).argmax()))

# ---- PGD in the 64x96 reduced space, replicated to 4x4 blocks (robust to nearest offset)
# delta_small: (1,3,96,64), applied uniformly to each 4x4 full-res block.
delta_small = torch.zeros(1,3,96,64, device=dev, requires_grad=True)
lr = 1.0
ce = nn.CrossEntropyLoss()
tgt = torch.tensor([TARGET], device=dev)

# seal blocks: any 4x4 block overlapping seal -> forbid perturbation there
seal_block = torch.zeros(1,1,96,64, device=dev)
seal_block[:,:, Y1//4:(Y2+3)//4, X1//4:(X2+3)//4] = 1.0

for it in range(400):
    delta_full = F.interpolate(delta_small, scale_factor=4, mode="nearest")  # (1,3,384,256)
    adv = torch.clamp(ref_t + delta_full, 0, 255)
    adv[:,:,Y1:Y2,X1:X2] = ref_t[:,:,Y1:Y2,X1:X2]  # keep seal exact
    logits = model(preprocess(adv/255.0))
    loss = ce(logits, tgt)
    model.zero_grad()
    if delta_small.grad is not None: delta_small.grad.zero_()
    loss.backward()
    with torch.no_grad():
        delta_small -= lr * delta_small.grad.sign()
        delta_small.clamp_(-EPS, EPS)
        delta_small.mul_(1 - seal_block)  # no perturbation on seal blocks
    if it % 50 == 0 or it == 399:
        cls = int(logits.argmax()); marg = (logits[0,TARGET]-logits.max()).item()
        print(f"it{it:3d} loss{loss.item():.4f} cls{cls} logits{logits.detach().cpu().numpy().round(2)}")

# ---- build final uint8 badge, enforce integer L-inf<=18 and exact seal
with torch.no_grad():
    delta_full = F.interpolate(delta_small, scale_factor=4, mode="nearest")
    adv = torch.clamp(ref_t + delta_full, 0, 255)
    adv_u8 = adv.round()
    # enforce |adv-ref|<=18 in integer space
    adv_u8 = torch.min(torch.max(adv_u8, ref_t-EPS), ref_t+EPS)
    adv_u8 = torch.clamp(adv_u8, 0, 255)
    adv_u8[:,:,Y1:Y2,X1:X2] = ref_t[:,:,Y1:Y2,X1:X2]  # exact seal
    arr = adv_u8[0].permute(1,2,0).byte().cpu().numpy()

out = f"{A}/admin_badge.png"
Image.fromarray(arr, "RGB").save(out)

# verify constraints + prediction after PNG round-trip
rt = np.asarray(Image.open(out).convert("RGB"), dtype=np.int32)
diff = np.abs(rt - ref.astype(np.int32))
seal_ok = (diff[Y1:Y2, X1:X2] == 0).all()
outside = diff.copy(); outside[Y1:Y2, X1:X2] = 0
rt_t = torch.from_numpy(rt.astype(np.float32)).permute(2,0,1).unsqueeze(0).to(dev)
final_logits = predict(rt_t); final_cls = int(final_logits.argmax())
print(f"\nSaved {out}")
print(f"seal unchanged: {seal_ok} | max L-inf outside seal: {outside.max()} (budget {int(EPS)})")
print(f"final logits {final_logits.cpu().numpy().round(3)} -> class {final_cls} ({['visitor','employee','admin'][final_cls]})")
print("SUCCESS" if (seal_ok and outside.max()<=EPS and final_cls==TARGET) else "FAILED constraints")
