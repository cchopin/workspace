# AI Evasion - First-Order Attacks (module 319)

## En bref

- Module CENTRAL sur les **first-order (gradient-based) evasion attacks** : perturbations adverses calculées à l'inference-time via `∇_x J(θ,x,y)` (gradient de la loss par rapport à l'INPUT, pas aux poids).
- **FGSM** (Goodfellow 2014) : one-step, L∞, `x_adv = x + ε·sign(∇_x J)`. Untargeted = `+`, targeted = `−` avec label cible `y_t`.
- **BIM / I-FGSM** (Kurakin 2016) : itératif, sign step `α`, projection sur la boule L∞ après chaque pas. `x^(t+1) = Π_{B∞(x,ε)}(x^(t) + α·sign(∇J))`.
- **PGD** (Madry 2017) : I-FGSM + `random_start` + restarts multiples ; forme générale des attaques itératives sous contrainte.
- **DeepFool** (Moosavi-Dezfooli 2016) : cherche la perturbation MINIMALE (L2 par défaut) vers la decision boundary la plus proche via linéarisation itérative + overshoot. Sert de mesure de robustesse (`ρ_adv`).
- Cadres de sécurité : **OWASP ML01:2023** (Input Manipulation Attack, risque le plus élevé) et **Google SAIF** (defense in depth, red teaming).
- Rôle central des **norms** (L0/L1/L2/L∞) : elles définissent le "budget" `ε` et la forme géométrique de la contrainte.
- MNIST : `μ=0.1307`, `σ=0.3081` ; espace normalisé `[-0.424, 2.821]` ; conversion `ε_pixel = σ·ε_norm`.
- 4 challenges non résolus : FGSM Challenge (MNIST L∞), DeepFool Challenge (MNIST targeted L2), Skills Assessment 1 (CIFAR-10 I-FGSM targeted dog→cat, ε=8/255), Skills Assessment 2 (CIFAR-10 DeepFool untargeted, L2 normalisé ≤ 3.5).
- White-box (gradients exacts) vs black-box (surrogate + transferability). Les attaques first-order sont hautement **transférables**.

---

## 1. Introduction aux First-Order Evasion Attacks

**Définition.** Une first-order attack utilise le gradient pour fabriquer des adversarial examples. Pendant l'entraînement, le gradient dit comment changer les **poids** pour réduire l'erreur ; pendant l'attaque, il dit comment changer l'**input** pour l'augmenter. On calcule `∇_x J(θ,x,y)` (gradient p/r à l'input, θ frozen).

**Scénarios :**
- **White-box** : accès complet au modèle → gradients exacts.
- **Black-box** : uniquement les sorties par query → estimation numérique du gradient OU crafting sur un surrogate model + **transferability**.

**Contrainte clé :** garder la perturbation aussi petite que possible, mesurée par une **norm**.

**Deux philosophies :**
- **FGSM** : "Étant donné un budget `ε`, où frapper ?" → budget fixe, un pas.
- **DeepFool** : "Quel est le plus petit changement qui trompe le modèle ?" → cherche la boundary la plus proche, budget minimal découvert.

**Pourquoi ça compte :** un modèle à 99% d'accuracy peut échouer catastrophiquement sous adversarial examples. Transférabilité → attaques réalistes sans accès total.

**Frameworks de sécurité (🎯 Exam) :**
- **OWASP Machine Learning Security Top 10** : Input Manipulation = **ML01:2023**, le risque le plus élevé pour le ML traditionnel. Distingue les attaques inference-time (evasion) des attaques training-time (poisoning).
- **Google SAIF** (Secure AI Framework) : defense in depth — adversarial training (dev), robustness evaluation (avant déploiement), input filtering (opération) + red teams.

---

## 2. Understanding Norms

Une **norm** = une "règle" mathématique qui assigne une taille/longueur à une perturbation. Métaphore : distance Times Square → Central Park mesurée différemment (intersections traversées, marche dans la grille, vol d'oiseau, plus longue étape).

**Les 3 règles d'une norme :**
1. **Zero means zero** : seule la valeur nulle a une taille nulle.
2. **Doubling means doubling** : échelle (homogénéité). `‖α·x‖ = |α|·‖x‖`.
3. **Triangle inequality** : `‖a+b‖ ≤ ‖a‖ + ‖b‖` (pas de raccourci).

**Formule de la famille p-norm :**

```
‖x‖_p = ( Σ_i |x_i|^p )^(1/p)
```

| Norm | Formule | Forme de contrainte | Effet perturbation |
|------|---------|---------------------|--------------------|
| **L0** | `‖x‖_0 = Σ_i 𝟙[x_i ≠ 0]` (compte les non-zéros) | points épars (union de sous-espaces) | change PEU de pixels, magnitude libre |
| **L1** | `‖δ‖_1 = Σ_i |δ_i|` | diamant (diamond) | sparse, "salt & pepper" |
| **L2** | `‖δ‖_2 = √(Σ_i δ_i²)` (euclidienne) | cercle (circle) | lisse, réparti, "haze/fog" |
| **L∞** | `‖δ‖_∞ = max_i |δ_i|` | carré (square/box) | changement max par pixel borné, uniforme |

**⚠️ L0 n'est PAS une vraie norme** : viole la règle 2 (doubler les changements ne double pas le compte). Pas obtenue en posant p=0 dans la formule p-norm. Non-lisse, non-convexe → "expert mode" (greedy/combinatoire).

**Relations entre normes (🎯 Exam) :**

```
‖x‖_∞ ≤ ‖x‖_2 ≤ ‖x‖_1 ≤ √n·‖x‖_2 ≤ n·‖x‖_∞
```

Pour L0 : `‖x‖_0 ≤ n` et `‖x‖_2 ≤ √(‖x‖_0)·‖x‖_∞`. Un bound L0 seul ne borne PAS les magnitudes ; il faut y ajouter un bound per-coordinate (L∞ ou range de pixels valides).

**Propriétés de calcul :**
- L0 : discontinue, non-convexe → greedy/combinatoire.
- L1 : "kink" à zéro → soft-thresholding / proximal gradient.
- L2 : lisse, différentiable partout → optimisation facile (le "vanilla ice cream"). En pratique on utilise souvent le **squared L2** (différentiable partout).
- L∞ : efficace mais gradients sparse (seul le max a un gradient non nul) → projected gradient descent.

**Dual norms :** exposants conjugués `1/p + 1/q = 1`. Paires : **L∞ ↔ L1**, **L2 ↔ L2** (auto-duale). Utilisé dans la preuve d'optimalité de FGSM.

---

## 3. FGSM (Fast Gradient Sign Method)

**Origine :** Goodfellow et al. 2014, "Explaining and Harnessing Adversarial Examples" (arxiv 1412.6572).

### 3.1 Formule core (🎯 Exam — à connaître par cœur)

```
x_adv = x + ε · sign( ∇_x J(θ, x, y) )     [UNTARGETED, L∞]
```

- `sign()` : extrait seulement la **direction** de chaque composante du gradient, jette la magnitude → chaque pixel change d'exactement `ε` en valeur absolue → colle parfaitement à la contrainte **L∞**.
- `ε` = perturbation budget (trade-off imperceptibilité ↔ force).
- One-step : un forward, un backward, terminé.

**Targeted (devenu standard) :**

```
x_adv_target = x − ε · sign( ∇_x J(θ, x, y_t) )     [descend la loss vers y_t]
```

Différences vs untargeted : (1) le gradient utilise le label cible `y_t`, (2) le signe du pas est inversé (`−`). Budget L∞ et clipping inchangés. Targeted requiert souvent un `ε` plus grand.

### 3.2 Pourquoi FGSM fonctionne

Deux raisons : **local linearity** + **high dimensionality**. Près d'une image propre, les deep nets sont quasi-linéaires ; un pas gradient pousse la loss dans la direction la plus raide. Comme les images ont beaucoup de pixels, de petites modifs alignées s'accumulent.

Pour un modèle linéaire `f(x) = wᵀx`, avec `‖δ‖_∞ ≤ ε` :

```
|f(x+δ) − f(x)| = |wᵀδ| ≤ ε·‖w‖_1
```

Exemple : 784 pixels (MNIST 28×28), chaque poids ≈ 0.01 → `‖w‖_1 = 7.84`. Avec `ε=0.1` → changement max du logit = `0.784` (suffit à flipper une décision).

### 3.3 Constrained linearization (preuve d'optimalité — 🎯 Exam)

Problème adverse (inner maximization) :

```
max_δ  J(θ, x+δ, y)   s.t.   ‖δ‖_∞ ≤ ε
```

Taylor 1er ordre : `J(θ,x+δ,y) ≈ J(θ,x,y) + gᵀδ` avec `g = ∇_x J`. Le terme constant ne change pas l'argmax :

```
max_{‖δ‖_∞ ≤ ε}  gᵀδ
```

**Hölder's inequality** : `|uᵀv| ≤ ‖u‖_p·‖v‖_q` avec `1/p + 1/q = 1`. Ici L∞↔L1 (car `1/∞ + 1/1 = 1`) donne `gᵀδ ≤ ε·‖g‖_1`, égalité atteinte quand `δ` est aligné composante par composante avec `sign(g)`. Solution optimale :

```
δ* = ε · sign(g)      max value = ε·‖g‖_1
```

Substituant `g = ∇_x J` → l'update FGSM. Interprétation : maximiser un plan plat sur une box L∞ pousse chaque coordonnée sur sa borne avec le signe du gradient.

### 3.4 Budgets alternatifs (dual norm)

- **L2-bounded** (rayon ε) : `δ*_2 = ε · g/‖g‖_2` (direction du gradient normalisée L2).
- **L1-bounded** : concentre le budget sur les coordonnées de plus grand |gradient| ; en pratique `±ε` sur les top coordinates.

### 3.5 Backpropagation to inputs

Pour cross-entropy `J = −log p_y(x)` avec `p_i = softmax(z(x))_i` :

```
∇_x J(θ,x,y) = Σ_i ( p_i(x) − 𝟙[i=y] ) · ∇_x z_i(x)
```

Coefficient pour la vraie classe : `p_y − 1 = −(1−p_y)`. Si `p_y=0.95` → coeff `−0.05` (petit gradient) ; si `p_y=0.20` → coeff `−0.80` (gros gradient, attaque plus forte). En pratique : `x.requires_grad_(True)` → forward → `loss.backward()` → lire `x.grad`.

---

## 4. FGSM Setup (environnement)

### 4.1 Installation & reproductibilité

```bash
# Install the AI Library (or update it)
pip install --upgrade git+https://github.com/PandaSt0rm/htb-ai-library
```

```python
import os
import random
import numpy as np
import torch
from torch import nn, Tensor
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Import common utilities from HTB Evasion Library
from htb_ai_library import (
    set_reproducibility,
    SimpleCNN,
    get_mnist_loaders,
    mnist_denormalize,
    train_model,
    evaluate_accuracy
)

# Configure reproducibility
set_reproducibility(1337)
```

`set_reproducibility(1337)` verrouille 3 sources d'aléa : `PYTHONHASHSEED`, `random`+NumPy (seed 1337), et cuDNN deterministic mode.

### 4.2 Device, data, model, training

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

train_loader, test_loader = get_mnist_loaders(batch_size=128, normalize=True)

model = SimpleCNN().to(device)

trained_model = train_model(model, train_loader, test_loader, epochs=1, device=device)
baseline_acc = evaluate_accuracy(trained_model, test_loader, device)
print(f"Baseline test accuracy: {baseline_acc:.2f}%")
```

**SimpleCNN** : conv1 (1→32, 3×3, padding=1) + ReLU, conv2 (32→64, 3×3) + ReLU, 2× maxpool stride 2 (28→14→7), feature map 64×7×7 = 3136, 2 FC → 10 logits. Adam lr=0.001. `get_mnist_loaders` : ToTensor ([0,255]→[0,1]), normalize MNIST, shuffle seed 1337, num_workers=0.

Output attendu : `Epoch 1/1: Avg Loss = 0.1566, Test Accuracy = 98.41%`.

---

## 5. Normalization (crucial pour FGSM — 🎯 Exam)

**Opération :** `x_norm = (x − μ) / σ`. Pour MNIST : `μ=0.1307`, `σ=0.3081` (calculés sur 60 000 images).

**Pourquoi normaliser ?** Pas pour l'œil (images identiques) mais pour la **gradient mathematics**. Inputs zero-mean/unit-variance → gradients positifs ET négatifs → exploration efficace de l'espace, single learning rate, gradients stables même en profondeur. Sans normalisation : convergence lente (85% à epoch 20 vs 98% à epoch 1), gradients corrélés.

**Paradoxe robustesse/accuracy :** un modèle bien entraîné (boundaries nettes) est simultanément plus précis ET plus vulnérable aux gradient attacks.

**Bornes valides normalisées (constantes clés) :**

```
MNIST_NORM_MIN = (0.0 - 0.1307) / 0.3081 ≈ -0.424
MNIST_NORM_MAX = (1.0 - 0.1307) / 0.3081 ≈  2.821
```

**Conversion des budgets ε (🎯 Exam) :**

```
ε_pixel = σ · ε_norm          ε_norm = ε_pixel / σ
```

Exemples MNIST : `ε_norm=0.8` → `ε_pixel = 0.8×0.3081 ≈ 0.25` ≈ 64 niveaux d'intensité 8-bit. Inversement `ε_pixel=0.3` → `ε_norm = 0.3/0.3081 ≈ 0.97`. `ε_pixel = 8/255 ≈ 0.031`.

---

## 6. Core FGSM Implementation (code reproductible)

### 6.1 Loss sans effets de bord

```python
def _forward_and_loss(model: nn.Module, x: Tensor, y: Tensor) -> tuple[Tensor, Tensor]:
    """Forward pass and cross-entropy loss without side effects."""
    if getattr(model, "training", False):
        raise RuntimeError("Expected model.eval() for attack computations to avoid BN/Dropout state updates")
    logits = model(x)
    loss = F.cross_entropy(logits, y)
    return logits, loss
```

### 6.2 Input gradient

```python
def _input_gradient(model: nn.Module, x: Tensor, y: Tensor) -> Tensor:
    """Return gradient of loss with respect to input tensor x."""
    x_req = x.clone().detach().requires_grad_(True)
    _, loss = _forward_and_loss(model, x_req, y)
    model.zero_grad(set_to_none=True)
    loss.backward()
    return x_req.grad.detach()
```

### 6.3 FGSM attack (LE code central — 🎯 Exam)

```python
def fgsm_attack(model: nn.Module,
                images: Tensor,
                labels: Tensor,
                epsilon: float,
                targeted: bool = False) -> Tensor:

    # Valid normalized range for MNIST
    MNIST_NORM_MIN = (0.0 - 0.1307) / 0.3081
    MNIST_NORM_MAX = (1.0 - 0.1307) / 0.3081

    if epsilon < 0:
        raise ValueError("epsilon must be non-negative")
    if not images.is_floating_point():
        raise ValueError("images must be floating point tensors")

    grad = _input_gradient(model, images, labels)
    step_dir = -1.0 if targeted else 1.0
    x_adv = images + step_dir * epsilon * grad.sign()
    x_adv = torch.clamp(x_adv, MNIST_NORM_MIN, MNIST_NORM_MAX)
    return x_adv.detach()
```

`step_dir=+1.0` untargeted (monte la loss de `y`), `step_dir=-1.0` targeted (descend la loss vers `labels`=cible). `torch.clamp` garde l'image dans le range normalisé valide.

### 6.4 Test

```python
images, labels = next(iter(test_loader))
images, labels = images.to(device), labels.to(device)

model.eval()
# Epsilon in normalized space (≈0.25 in pixel space)
epsilon = 0.8
with torch.no_grad():
    clean_pred = model(images).argmax(dim=1)

x_adv = fgsm_attack(model, images, labels, epsilon)
with torch.no_grad():
    adv_pred = model(x_adv).argmax(dim=1)

originally_correct = (clean_pred == labels)
flipped = (adv_pred != labels) & originally_correct
success = flipped.sum().item() / max(int(originally_correct.sum().item()), 1)
print(f"FGSM flips (first batch): {success:.2%}")
```

Output : `FGSM flips (first batch): 71.09%` (91/128 flips à ε=0.8 normalisé).

### 6.5 Pixel-space FGSM variant (inputs en [0,1] attaquant un modèle normalisé)

Idée clé : gradients calculés en espace normalisé → les diviser par `σ` (chain rule `∇_x J = ∇_{x_norm} J / σ`) pour que `ε` ait un sens pixel-space.

```python
def _norm_params(images: Tensor, mean: list, std: list) -> tuple[Tensor, Tensor]:
    """Convert normalization parameters to broadcastable tensors (1, C, 1, 1)."""
    device, dtype, C = images.device, images.dtype, images.shape[1]
    mean_t = torch.tensor(mean, device=device, dtype=dtype).view(1, -1, 1, 1)
    std_t = torch.tensor(std, device=device, dtype=dtype).view(1, -1, 1, 1)
    if mean_t.shape[1] != C or std_t.shape[1] != C:
        raise ValueError("mean/std channels must match images")
    return mean_t, std_t


def fgsm_pixel_space(model: nn.Module,
                     images: Tensor,
                     labels: Tensor,
                     epsilon: float,
                     mean: list,
                     std: list,
                     targeted: bool = False) -> Tensor:
    """FGSM for pixel-space inputs [0,1] attacking normalized models."""
    mean_t, std_t = _norm_params(images, mean, std)
    x = images.clone().detach()
    x_norm = (x - mean_t) / std_t
    x_norm.requires_grad_(True)

    _, loss = _forward_and_loss(model, x_norm, labels)
    model.zero_grad(set_to_none=True)
    loss.backward()

    # Convert gradient from normalized space to image space
    grad_img = x_norm.grad / std_t
    step_dir = -1.0 if targeted else 1.0
    x_adv = torch.clamp(x + step_dir * epsilon * grad_img.sign(), 0.0, 1.0)
    return x_adv.detach()
```

Usage : `ε=8/255≈0.031` en unités pixel. Si data déjà normalisée → utiliser `fgsm_attack` directement.

---

## 7. Evaluation Metrics

```python
from typing import Dict

def evaluate_attack(model: nn.Module,
                   clean_images: Tensor,
                   adversarial_images: Tensor,
                   true_labels: Tensor) -> Dict[str, float]:
    """Compute accuracy, success rate, confidence shift, and norms."""
    model.eval()
    with torch.no_grad():
        clean_logits = model(clean_images)
        adv_logits = model(adversarial_images)

        clean_probs = F.softmax(clean_logits, dim=1)
        adv_probs = F.softmax(adv_logits, dim=1)

        clean_pred = clean_logits.argmax(dim=1)
        adv_pred = adv_logits.argmax(dim=1)

        clean_correct = (clean_pred == true_labels)
        adv_correct = (adv_pred == true_labels)

        originally_correct = clean_correct
        flipped = (~adv_correct) & originally_correct

        conf_clean = clean_probs.gather(1, true_labels.view(-1, 1)).squeeze(1)
        conf_adv = adv_probs.gather(1, true_labels.view(-1, 1)).squeeze(1)

        l2 = (adversarial_images - clean_images).view(clean_images.size(0), -1).norm(p=2, dim=1)
        linf = (adversarial_images - clean_images).abs().amax()

        return {
            "clean_accuracy": clean_correct.float().mean().item(),
            "adversarial_accuracy": adv_correct.float().mean().item(),
            "attack_success_rate": (
                flipped.float().sum() / originally_correct.float().sum().clamp_min(1.0)
            ).item(),
            "avg_clean_confidence": conf_clean.mean().item(),
            "avg_adv_confidence": conf_adv.mean().item(),
            "avg_confidence_drop": (conf_clean - conf_adv).mean().item(),
            "avg_l2_perturbation": l2.mean().item(),
            "max_linf_perturbation": linf.item(),
        }
```

- **attack_success_rate** = fraction des originally-correct qui ont flippé (isole l'efficacité de l'attaque de la qualité du modèle).
- Output FGSM ε=0.8 : clean_acc 0.9766, adv_acc 0.3203, ASR 0.6797, conf 0.9824→0.3891 (drop 0.5933), L2≈10.85, max_linf=0.8000 (respecte le budget).

---

## 8. Targeted FGSM

Change l'objectif : au lieu de réduire la confiance dans la vraie classe, augmenter la confiance dans une classe cible. Untargeted monte `J(θ,x,y)` ; targeted descend `J(θ,x,y_t)` (= monte `−J(θ,x,y_t)`). Deux différences : label cible `y_t` dans le gradient + signe inversé. Budget/clip inchangés. Souvent besoin d'un `ε` plus grand + early stopping.

Exemple 1→7 : recherche du `ε` minimal parmi `[0.5, 0.8, 1.0]`.

```python
target_label = torch.tensor([7], device=device)

for eps_try in eps_candidates:   # [0.5, 0.8, 1.0]
    x_adv = fgsm_attack(model, candidate.unsqueeze(0), target_label,
                        epsilon=eps_try, targeted=True)
    with torch.no_grad():
        pred = model(x_adv).argmax(dim=1).item()
    print(f"epsilon={eps_try:.2f} -> predicted {pred}")
    if pred == 7:
        success_image, success_label, success_eps = candidate, candidate_label, eps_try
        break
```

Output : `epsilon=0.50 -> predicted 1` puis `epsilon=0.80 -> predicted 7`. (`candidate.unsqueeze(0)` : `[1,28,28]`→`[1,1,28,28]`.)

---

## 9. I-FGSM / BIM (Basic Iterative Method)

**Origine :** Kurakin et al. 2016, "Adversarial Examples in the Physical World" (arxiv 1607.02533). Aussi appelé **BIM**. Plusieurs petits pas au lieu d'un grand.

### 9.1 Update et projection (🎯 Exam)

```
x^(0) = x
x^(t+1) = Π_{B∞(x,ε)} ( x^(t) + α · sign( ∇_{x^(t)} J(θ, x^(t), y) ) )
```

- `α` = step size, typiquement `α = ε/T` (T = nb itérations).
- `Π_{B∞(x,ε)}` = projection sur la boule L∞ de rayon `ε` autour de `x`, puis clip au domaine valide. En coordonnées :

```
Π_{B∞(x,ε)}(x') = x + clip(x' − x, −ε, ε)   puis   x' ← clip(x', x_min, x_max)
```

**⚠️ Projection relative à l'image ORIGINALE `x`, pas au précédent itéré** → le budget signifie "ε loin du point de départ", pas "ε par pas".

**Targeted :** label `y_t` + signe `−` :

```
x^(t+1) = Π_{B∞(x,ε)} ( x^(t) − α · sign( ∇_{x^(t)} J(θ, x^(t), y_t) ) )
```

### 9.2 Implémentation (code central — 🎯 Exam)

```python
def iterative_fgsm(model: nn.Module,
                   images: Tensor,
                   labels: Tensor,
                   epsilon: float,
                   num_iter: int,
                   alpha: float | None = None,
                   targeted: bool = False,
                   random_start: bool = False) -> Tensor:
    """Iterative FGSM (Basic Iterative Method) with projection."""
    # Valid normalized range for MNIST
    MNIST_NORM_MIN = (0.0 - 0.1307) / 0.3081
    MNIST_NORM_MAX = (1.0 - 0.1307) / 0.3081

    if alpha is None:
        alpha = epsilon / max(num_iter, 1)
    if random_start:
        torch.manual_seed(1337)
        delta = torch.empty_like(images).uniform_(-epsilon, epsilon)
        x_adv = torch.clamp(images + delta, MNIST_NORM_MIN, MNIST_NORM_MAX)
    else:
        x_adv = images.clone()

    for _ in range(num_iter):
        x_adv = x_adv.detach().requires_grad_(True)
        logits = model(x_adv)
        loss = F.cross_entropy(logits, labels)
        model.zero_grad(set_to_none=True)
        loss.backward()
        step_dir = -1.0 if targeted else 1.0
        x_adv = x_adv + step_dir * alpha * x_adv.grad.sign()
        x_adv = torch.clamp(images + (x_adv - images).clamp(-epsilon, epsilon), MNIST_NORM_MIN, MNIST_NORM_MAX)

    return x_adv.detach()
```

`random_start` ajoute du bruit uniforme `[-ε, ε]` avant d'itérer (échappe aux voisinages où le gradient est inutile).

### 9.3 Résultats & hyperparamètres

- Test ε=0.8, T=10, α=0.08, random_start=True → **I-FGSM flips: 100.00%** (vs FGSM 71.09% au même ε). adv_acc 0.0, conf drop 0.9739, max_linf 0.8000, L2≈14.05.
- Comparaison ε=0.7 : **FGSM 57.8% vs I-FGSM 95.3%** (amélioration relative +64.9%).
- **Trade-offs α/T :** large α + peu d'itérations (α=0.1, T=2) → overshoot ; petit α + beaucoup d'itérations (α=0.01, T=20) → suit mieux la surface courbée, adversaires plus forts. `α=ε/T` garde le worst-case per-pixel dans le budget.
- **Random starts** : peuvent faire passer le success rate de 85% à 92% au même budget.

### 9.4 Relation à PGD (Madry 2017 — 🎯 Exam)

**PGD** (Projected Gradient Descent, arxiv 1706.06083) = forme générale des attaques itératives sous contrainte. Avec sign step + `α=ε/T` + random restarts optionnels, l'implémentation ci-dessus coïncide avec BIM/PGD pour le threat model L∞.

- **BIM** = I-FGSM **sans** initialisation aléatoire.
- **PGD** = I-FGSM **+ random_start** + (optionnel) **multiple random restarts** en gardant le plus fort adversaire trouvé.
- Même update : `x^(t+1) = Π_{B∞}(x^(t) + α·sign(∇L))`.

---

## 10. FGSM Challenge (interactif, non résolu)

**Objectif :** crafter un adversarial example qui trompe un classifieur MNIST via FGSM. Contrainte : `‖x_adv − x‖_∞ ≤ ε` ET classe prédite ≠ label baseline. Toutes les API attendent des images en **[0,1] pixel space**, base64 PNG 28×28 single-channel.

**API :**
- `GET /health` → `{"status":"ok","epsilon":0.25,"index":2}`
- `GET /challenge` → `{"sample_index","label","epsilon","image_b64"}`
- `POST /predict` (body `{"image_b64":...}`) → `{"pred","confidence"}` (ne donne PAS le flag).
- `GET /weights` → state_dict PyTorch (architecture `SimpleClassifier`), `torch.load(path, map_location='cpu')`.
- `POST /submit` → valide 28×28 [0,1], `L∞ ≤ ε`, misclassification → renvoie le flag. Échec = HTTP 400 (`"L_inf too large: 0.26 > 0.25"` ou `"Not misclassified; try a stronger perturbation"`).

**Architecture serveur `SimpleClassifier` (normalisation INTERNE, log_softmax en sortie) :**

```python
class SimpleClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x01: torch.Tensor) -> torch.Tensor:
        x = (x01 - MNIST_MEAN) / MNIST_STD      # MNIST_MEAN,MNIST_STD = 0.1307, 0.3081
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.dropout2(x)
        x = self.fc2(x)
        return torch.log_softmax(x, dim=1)
```

**Helpers fournis :** `x01_from_b64_png` (base64 PNG → np [0,1] 28×28), `b64_png_from_x01` (np [0,1] → base64 PNG), `linf(a,b)=max|a−b|`.

**### Questions (section)** — user_answer VIDE (non résolu) :
- id 3331 : "After successfully completing the challenge, what is the flag you receive?" → **flag `HTB{...}`** (5 cubes, 60 XP).

**Méthode de résolution attendue (🎯 Exam) :**
1. `GET /challenge`, décoder `image_b64` → `x` en [0,1], noter `label` et `eps`.
2. `GET /weights`, charger dans `SimpleClassifier().eval()`.
3. Le modèle normalise en interne → travailler en **pixel space** : `x_t = torch.from_numpy(x[None,None,...]).float()`, `x_t.requires_grad_(True)`.
4. Forward (le forward renvoie déjà log_softmax) → loss = `F.nll_loss(out, torch.tensor([label]))` (ou cross_entropy sur les logits) → backward → `grad = x_t.grad`.
5. `x_adv = clamp(x_t + eps * grad.sign(), 0, 1)` (untargeted, budget = eps EXACTEMENT en pixel space).
6. Vérifier localement `argmax != label` et `linf(x_adv, x) ≤ eps` ; sinon itérer (I-FGSM) tout en respectant la projection L∞.
7. Encoder → `POST /submit` → récupérer le flag. Attention à la ronde de quantification PNG (uint8) qui peut faire dépasser légèrement le budget ou changer la prédiction : garder une marge (`eps` légèrement réduit) et re-vérifier après ré-encodage.

---

## 11. DeepFool — Théorie (quête de minimalité)

**Origine :** Moosavi-Dezfooli, Fawzi, Frossard, CVPR 2016. Question : "Quelle est la plus petite perturbation qui trompe le réseau ?" → problème **géométrique** : plus court chemin d'un point vers la decision boundary la plus proche. Élimine le choix arbitraire de `ε` → la magnitude devient une **mesure de robustesse** de l'input.

### 11.1 Classifieur linéaire binaire (base)

Pour `f(x) = wᵀx + b`, boundary = hyperplan `f(x)=0`. Distance d'un point `x_0` :

```
d = |f(x_0)| / ‖w‖_2
```

Perturbation minimale (projection orthogonale) :

```
r* = − ( f(x_0) / ‖w‖_2² ) · w
```

Contrairement au `sign()` de FGSM, DeepFool **préserve les magnitudes relatives** du gradient → les pixels influents changent plus. Projection orthogonale = optimale en L2 (plus court chemin point→hyperplan est perpendiculaire).

### 11.2 Formulation multi-classes (🎯 Exam — cœur de DeepFool)

Input `x` classé `k̂(x) = argmax_k f_k(x)`. À chaque itération, pour chaque classe alternative `k ≠ k̂(x_i)` :

```
w_k = ∇f_k(x_i) − ∇f_{k̂}(x_i)          (gradient difference)
f'_k = f_k(x_i) − f_{k̂}(x_i)            (score gap, négatif)
```

Boundary la plus proche :

```
l = argmin_{k ≠ k̂}  |f'_k| / ‖w_k‖_2
```

Pas minimal (projection orthogonale sur la boundary linéarisée la plus proche) :

```
r_i = ( |f'_l| / ‖w_l‖_2² ) · w_l
x_{i+1} = x_i + r_i
```

On re-linéarise et répète tant que la classification n'a pas changé. Multi-classes = binaire + un step de sélection de la boundary la plus proche.

### 11.3 Overshoot parameter

`overshoot` (typiquement **0.02**) : le pas réel est `(1 + overshoot) × r_i`. Deux buts : (1) garantir de vraiment traverser la boundary non-linéaire (pas juste la toucher), (2) accélérer la convergence. Trade-off : perturbation finale marginalement plus grande (négligeable à 2%).

### 11.4 DeepFool vs I-FGSM

| | I-FGSM | DeepFool |
|---|--------|----------|
| Direction | `sign(gradient)` (jette la magnitude) | préserve la magnitude du gradient |
| Pas | uniforme `α`, projeté sur contrainte | pas géométrique exact vers boundary |
| Cible | budget fixe, n'importe quel flip | boundary la plus proche, budget minimal |
| Norme | L∞ (défaut) | L2 (défaut) |

### 11.5 Mesure de robustesse ρ_adv

```
ρ_adv = (1/|D|) · Σ_{x∈D}  ‖r(x)‖_2 / ‖x‖_2
```

Perturbation relative moyenne. `ρ_adv=0.02` → 2% de perturbation moyenne suffit ; `ρ_adv=0.10` → modèle 5× plus robuste. Networks avec `ρ_adv` plus grand = plus robustes.

### 11.6 Variante L∞ de DeepFool

Le dénominateur passe de L2 à L1, et la direction utilise `sign()` :

```
l̂ = argmin_{k ≠ k̂}  |f'_k| / ‖w_k‖_1
r_i = ( |f'_l̂| / ‖w_l̂‖_1 ) · sign(w_l̂)
```

Distribue la perturbation uniformément sur les pixels sous contrainte L∞.

**Universal adversarial perturbations :** une seule perturbation qui trompe la plupart des inputs, construite en accumulant des DeepFool sur différents exemples.

---

## 12. DeepFool — Implémentation (code central — 🎯 Exam)

Architecture cible : `MNISTClassifierWithDropout` (dropout crée des boundaries plus réalistes). Conv1 1→32 3×3 ReLU pool 25% dropout ; Conv2 32→64 3×3 ReLU pool 25% dropout ; FC1 3136→128 ReLU 50% dropout ; FC2 128→10. **`model.eval()` OBLIGATOIRE** (dropout off → gradients stables).

```python
def deepfool(image: torch.Tensor,
             net: nn.Module,
             num_classes: int = 10,
             overshoot: float = 0.02,
             max_iter: int = 50,
             device: str = 'cuda') -> Tuple[torch.Tensor, int, int, int, torch.Tensor]:
    """Generate minimal adversarial perturbation using DeepFool algorithm.
    Returns: (r_tot, loop_i, label, k_i, pert_image)"""
    image = image.to(device)
    net = net.to(device)

    # Original prediction and class ordering (descending score)
    f_image = net(image).data.cpu().numpy().flatten()
    I = f_image.argsort()[::-1]
    label = I[0]

    # Working tensors and accumulators
    input_shape = image.shape
    pert_image = image.clone()
    r_tot = torch.zeros(input_shape).to(device)
    loop_i = 0

    while loop_i < max_iter:
        x = pert_image.clone().requires_grad_(True)
        fs = net(x)
        k_i = fs.data.cpu().numpy().flatten().argsort()[::-1][0]

        if k_i != label:              # prediction changed -> success
            break

        pert = float('inf')
        w = None

        for k in range(1, num_classes):
            if I[k] == label:
                continue

            # Gradient for candidate class
            if x.grad is not None:
                x.grad.zero_()
            fs[0, I[k]].backward(retain_graph=True)
            grad_k = x.grad.data.clone()

            # Gradient for original class
            if x.grad is not None:
                x.grad.zero_()
            fs[0, label].backward(retain_graph=True)
            grad_label = x.grad.data.clone()

            # Direction and distance under linearization
            w_k = grad_k - grad_label
            f_k = (fs[0, I[k]] - fs[0, label]).data.cpu().numpy()
            pert_k = abs(f_k) / (torch.norm(w_k.flatten()) + 1e-10)

            if pert_k < pert:
                pert = pert_k
                w = w_k

        # Minimal step for the selected direction
        r_i = (pert + 1e-4) * w / (torch.norm(w.flatten()) + 1e-10)
        r_tot = r_tot + r_i

        # Apply with overshoot to ensure crossing
        pert_image = image + (1 + overshoot) * r_tot
        loop_i += 1

    return r_tot, loop_i, label, k_i, pert_image
```

**Détails clés :**
- `I = f_image.argsort()[::-1]` : indices triés par score décroissant, `label = I[0]`.
- Boucle candidats `range(1, num_classes)` (saute `I[0]` = classe courante).
- `retain_graph=True` requis pour 2 backward sur le même graphe ; `.clone()` pour ne pas écraser.
- `w_k = grad_k − grad_label` (tug-of-war), `pert_k = |f_k| / ‖w_k‖_2`.
- `r_i = (pert + 1e-4)·w / ‖w‖_2` (normalise w à unité, scale par distance ; `1e-4` évite les soucis numériques, `1e-10` évite div/0).
- Overshoot appliqué sur `r_tot` accumulé : `pert_image = image + (1+overshoot)·r_tot`.
- `num_classes` : MNIST=10 (toutes) ; ImageNet → top 10 suffit (−99% de gradients).

**Résultats démonstration :**
- Single 7→2 : L2=7.72, L∞=1.58, relative 32.48%, conf 1.000→0.404. (Uniforme donnerait L∞≈7.72/√784≈0.276 ; observé 1.58 ≈ 6× → concentration sur pixels discriminants.)
- Batch 20 samples : **100% success**, L2 moyen 4.87, **3.0 itérations** moyennes. Range L2 : 0.60 (3→5 similaires) à 7.72 (7→2). MNIST converge en 1-3 itérations.

---

## 13. DeepFool Challenge (interactif, non résolu)

**Objectif :** adversarial **TARGETED** via attaque itérative DeepFool-style. Contrainte : `‖x_adv − x‖_2 ≤ threshold` ET classe prédite = **target** (pas juste n'importe quel flip). API en [0,1] pixel space, PNG 28×28.

**API :**
- `GET /health` → `{"status":"ok","l2_threshold":0.75,"index":95,"target":6}`
- `GET /challenge` → `{"sample_index","label","target","l2_threshold","image_b64"}`
- `POST /predict` → `{"pred","confidence"}`
- `GET /weights` → state_dict (même `SimpleClassifier` que FGSM Challenge, normalisation interne, log_softmax).
- `POST /submit` → valide L2 ≤ threshold ET `pred == target` → flag. Échec 400 (`"L2 too large: 0.82 > 0.75"` ou `"Wrong target: predicted 8, need 6"`).

Helper spécifique : `l2(a,b) = np.linalg.norm((a-b).ravel(), ord=2)`.

**### Questions (section)** — user_answer VIDE (non résolu) :
- id 3346 : "After successfully completing the challenge, what is the flag you receive?" → **flag `HTB{...}`** (5 cubes, 60 XP).

**Méthode de résolution attendue (🎯 Exam) :**
1. `GET /challenge` → `x`, `label`, `target`, `thr` ; `GET /weights` → `SimpleClassifier().eval()`.
2. Comme c'est **targeted L2**, adapter DeepFool ou faire une **targeted PGD-L2** : minimiser la loss vers `target` par pas L2 normalisés, projeter sur la boule L2 de rayon `thr`.
   - Alternative DeepFool targeted : au lieu de la boundary la plus proche, viser spécifiquement la boundary entre `label` et `target` : `w = ∇f_target − ∇f_label`, `f' = f_target − f_label`, `r_i = (|f'|/‖w‖_2²)·w` + overshoot ; itérer jusqu'à `argmax == target`.
3. Après convergence, si `‖x_adv − x‖_2 > thr`, **rescale** la perturbation : `r ← r · (thr/‖r‖_2)` (attention : peut faire perdre le target → compromis).
4. Clamp [0,1], encoder PNG, vérifier localement `pred==target` ET `l2 ≤ thr` (re-vérifier après quantization PNG uint8).
5. `POST /submit` → flag.

---

## 14. Skills Assessment 1 (interactif, non résolu) — CIFAR-10 I-FGSM Targeted

**Objectif :** transformer une image de **chien (dog, classe 5)** en **chat (cat, classe 3)** via I-FGSM targeted. Contrainte : `‖x_adv − x‖_∞ ≤ ε` avec **`ε = 8/255 ≈ 0.031373`** en pixel space, `pred == cat (3)`, pixels dans `[0,1]^{32×32×3}`.

**API (images base64 PNG 32×32×3 RGB en [0,1]) :**
- `GET /challenge` → inclut `original_class:5 (dog)`, `target_class:3 (cat)`, `epsilon:0.03137...`, `max_iterations_hint:100`, `normalization:{mean:[0.4914,0.4822,0.4465], std:[0.247,0.2435,0.2616]}`, `image`.
- `GET /model/weights` → `cifar10_model_best.pth` (~6.3MB).
- `POST /predict` (body `{"image":...}`) → `{"predicted_class","predicted_class_name","confidence","all_probabilities"}`.
- `POST /submit` → valide 32×32×3 [0,1], L∞ ≤ ε, `pred == target` → flag. Échec : `success:false, "Target not achieved"`.

**Architecture `CIFAR10CNN` (⚠️ normalisation EXTERNE — appliquer `(x-mean)/std` AVANT le forward) :**

```python
import torch
import torch.nn as nn

class CIFAR10CNN(nn.Module):
    def __init__(self, num_classes: int = 10):
        super(CIFAR10CNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.relu3 = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu3(self.fc1(x)))
        x = self.fc2(x)
        return x        # logits bruts (pas de softmax)

def load_model(model_path, device="cuda"):
    model = CIFAR10CNN(num_classes=10)
    checkpoint = torch.load(model_path, map_location=device)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)
    return model.to(device).eval()

CIFAR10_CLASSES = ["airplane","automobile","bird","cat","deer","dog","frog","horse","ship","truck"]
NORMALIZATION_MEAN = [0.4914, 0.4822, 0.4465]
NORMALIZATION_STD  = [0.247, 0.2435, 0.2616]
```

Helpers : `tensor_from_b64_png` (→ (3,32,32) [0,1] via `transforms.ToTensor()`), `b64_png_from_tensor` (permute (1,2,0)*255 uint8), `linf`.

**### Questions (section)** — user_answer VIDE (non résolu) :
- id 3347 : "After successfully completing the assessment task, what is the flag you receive?" → **flag `HTB{...}`** (5 cubes, 60 XP).

**Méthode de résolution attendue (🎯 Exam) :**
1. Fetch challenge, load model. Normalisation EXTERNE : `mean,std` en `view(3,1,1)`, `x_norm = (x - mean)/std`.
2. I-FGSM **targeted** en pixel space avec conversion gradient : soit attaquer directement `x` en normalisant à l'intérieur de la boucle et diviser le gradient par `std` (comme `fgsm_pixel_space`), soit intégrer la normalisation dans le forward.
3. Boucle (jusqu'à ~100 itérations) : `x_adv_norm = (x_adv - mean)/std`, forward → logits, `loss = F.cross_entropy(logits, target=3)`, backward, `grad_pixel = x_adv.grad / std`, `x_adv = x_adv - α·grad_pixel.sign()` (signe `−` = targeted), projeter L∞ : `x_adv = x + clamp(x_adv - x, -ε, ε)`, clamp [0,1]. `α ≈ ε/10` ou plus petit.
4. Early stop dès que `predict == cat(3)`. Vérifier `linf ≤ 8/255`. Encoder → submit.

---

## 15. Skills Assessment 2 (interactif, non résolu) — CIFAR-10 DeepFool Untargeted

**Objectif :** implémenter DeepFool pour trouver la perturbation L2 minimale causant une misclassification (untargeted, n'importe quelle classe ≠ **horse (7)**). Contrainte particulière : **`‖(x_adv − x)/σ‖_2 ≤ threshold`** — L2 mesuré en **espace NORMALISÉ** — avec **threshold = 3.5**, pixels dans `[0,1]^{32×32×3}`.

**API :**
- `GET /challenge` → `original_class:7 (horse)`, `l2_threshold:3.5`, `num_classes_hint:10`, `overshoot_hint:0.02`, `max_iterations_hint:50`, `normalization:{mean:[0.4914,0.4822,0.4465], std:[0.247,0.2435,0.2616]}`, `image`.
- `GET /model/weights` → `cifar10_model_best.pth`. Même `CIFAR10CNN` que SA1.
- `POST /predict` → `{"predicted_class","predicted_class_name","confidence","all_probabilities"}`.
- `POST /submit` → valide 32×32×3 [0,1], **L2 en espace normalisé ≤ 3.5**, misclassification → flag. Échec : `success:false, "Misclassification not achieved"`. Succès contient `validation:{l2_norm, l2_threshold, l2_satisfied, valid_range, original_class, adversarial_class, misclassification}`.

**### Questions (section)** — user_answer VIDE (non résolu) :
- id 3348 : "After successfully completing the assessment task, what is the flag you receive?" → **flag `HTB{...}`** (5 cubes, 60 XP).

**Méthode de résolution attendue (🎯 Exam) :**
1. Fetch, load model. `mean_t, std_t = view(3,1,1)`.
2. Appliquer l'algorithme `deepfool` (section 12) sur `x_norm = (x - mean)/std` avec `num_classes=10, overshoot=0.02, max_iter=50`. DeepFool opère naturellement en L2 → le threshold est mesuré en espace normalisé, donc **attaquer dans l'espace normalisé** est le plus direct.
3. Récupérer `pert_image` (normalisé), le dé-normaliser : `x_adv = pert_image * std + mean`, clamp [0,1].
4. Vérifier `‖(x_adv - x)/σ‖_2 ≤ 3.5` et `predict != horse(7)`. DeepFool trouvant le minimal, la contrainte 3.5 est généreuse (L2 typique CIFAR ≈ 0.96 en normalisé → largement sous 3.5).
5. Encoder PNG (attention quantization uint8 : re-vérifier après ré-encodage), submit → flag.

---

## 🎯 Questions d'examen probables

1. **Q : Formule exacte de FGSM untargeted ?**
   R : `x_adv = x + ε · sign(∇_x J(θ,x,y))`. One-step, norme L∞.

2. **Q : Comment obtenir la variante targeted de FGSM ?**
   R : Utiliser le label cible `y_t` dans le gradient ET inverser le signe : `x_adv = x − ε · sign(∇_x J(θ,x,y_t))`. Descend la loss vers `y_t`.

3. **Q : Pourquoi FGSM utilise `sign()` et pas le gradient brut ?**
   R : Parce que la contrainte est L∞. Par Hölder (dual L∞↔L1), le maximiseur de `gᵀδ` sous `‖δ‖_∞ ≤ ε` est `δ* = ε·sign(g)` : chaque pixel change d'exactement ε, sur la borne de la box L∞.

4. **Q : Quelle norme FGSM contraint, et quelle est sa duale ?**
   R : L∞ (max per-pixel). Duale = L1 (car `1/∞ + 1/1 = 1`).

5. **Q : Formule I-FGSM et rôle de la projection ?**
   R : `x^(t+1) = Π_{B∞(x,ε)}(x^(t) + α·sign(∇J))`. La projection `Π = x + clip(x'−x, −ε, ε)` (relative à l'image ORIGINALE) enforce le budget L∞ ε après chaque pas ; `α = ε/T` typiquement.

6. **Q : Différence BIM vs I-FGSM vs PGD ?**
   R : I-FGSM = BIM (sans random init). PGD = I-FGSM + random_start dans la boule ε + (optionnel) multiple restarts en gardant le plus fort. Même update.

7. **Q : Valeur typique de α dans I-FGSM ?**
   R : `α = ε/T` (budget divisé sur T itérations). Ex : ε=0.8, T=10 → α=0.08.

8. **Q : DeepFool — quelle norme, targeted ou untargeted par défaut ?**
   R : L2 par défaut, untargeted (vise la boundary la plus proche parmi toutes les classes).

9. **Q : Formule du pas DeepFool multi-classe ?**
   R : `w_k = ∇f_k − ∇f_{k̂}`, `f'_k = f_k − f_{k̂}`, boundary `l = argmin_{k≠k̂} |f'_k|/‖w_k‖_2`, pas `r_i = (|f'_l|/‖w_l‖_2²)·w_l`. Update `x_{i+1} = x_i + r_i`.

10. **Q : Rôle et valeur typique de l'overshoot dans DeepFool ?**
    R : `overshoot ≈ 0.02`. Pas réel = `(1+overshoot)·r_i`. Garantit de traverser la boundary non-linéaire (pas juste toucher la linéarisée) et accélère la convergence.

11. **Q : Formule de robustesse ρ_adv ?**
    R : `ρ_adv = (1/|D|)·Σ ‖r(x)‖_2/‖x‖_2`. ρ_adv plus grand = modèle plus robuste.

12. **Q : DeepFool vs I-FGSM — différence fondamentale ?**
    R : I-FGSM jette la magnitude (`sign`), pas uniforme sous budget fixe. DeepFool préserve la magnitude, pas géométrique exact vers la boundary la plus proche, budget minimal découvert.

13. **Q : Paramètres de normalisation MNIST et bornes normalisées ?**
    R : `μ=0.1307`, `σ=0.3081`. Range normalisé `[-0.424, 2.821]` (MNIST_NORM_MIN/MAX).

14. **Q : Conversion ε entre espaces ?**
    R : `ε_pixel = σ·ε_norm`. MNIST : ε_norm=0.8 → ε_pixel≈0.25. ε_pixel=8/255≈0.031.

15. **Q : Pourquoi `model.eval()` est obligatoire pendant une attaque ?**
    R : Désactive dropout + fige BatchNorm → gradients stables et reproductibles. Le dropout aléatoire crée des gradients bruités qui violent l'hypothèse de linéarité locale.

16. **Q : OWASP ML — quel identifiant pour l'evasion / input manipulation ?**
    R : **ML01:2023** (Input Manipulation Attack), le risque le plus élevé.

17. **Q : Pourquoi diviser le gradient par σ dans FGSM pixel-space ?**
    R : Chain rule : gradients calculés en espace normalisé (`x_norm=(x−μ)/σ`) → `∇_x J = ∇_{x_norm} J / σ`. Sans cela, un ε pixel-space appliqué à des gradients normalisés donne des magnitudes fausses.

18. **Q : Skills Assessment 1 — quelle attaque, quel ε, quelle transformation ?**
    R : I-FGSM targeted, ε=8/255≈0.0314 (L∞ pixel space), dog(5)→cat(3), CIFAR-10, normalisation externe mean/std.

---

## 🧪 Code réutilisable (prêt à adapter)

### FGSM (untargeted + targeted, générique)

```python
import torch, torch.nn.functional as F

def fgsm(model, x, y, epsilon, targeted=False, clip_min=0.0, clip_max=1.0):
    """FGSM one-step, L_inf. targeted=True -> y est la classe cible.
    Suppose model.eval(). x en [clip_min, clip_max]."""
    x = x.clone().detach().requires_grad_(True)
    logits = model(x)
    loss = F.cross_entropy(logits, y)
    model.zero_grad(set_to_none=True)
    loss.backward()
    step = -1.0 if targeted else 1.0
    x_adv = x + step * epsilon * x.grad.sign()
    return torch.clamp(x_adv, clip_min, clip_max).detach()
```

### PGD / I-FGSM (L∞, avec random_start et projection)

```python
def pgd_linf(model, x, y, epsilon, alpha=None, num_iter=10,
             targeted=False, random_start=True, clip_min=0.0, clip_max=1.0):
    """I-FGSM/PGD L_inf. alpha défaut = epsilon/num_iter. Projection sur boule L_inf autour de x."""
    if alpha is None:
        alpha = epsilon / max(num_iter, 1)
    x_orig = x.clone().detach()
    if random_start:
        x_adv = x_orig + torch.empty_like(x_orig).uniform_(-epsilon, epsilon)
        x_adv = torch.clamp(x_adv, clip_min, clip_max)
    else:
        x_adv = x_orig.clone()
    for _ in range(num_iter):
        x_adv = x_adv.detach().requires_grad_(True)
        loss = F.cross_entropy(model(x_adv), y)
        model.zero_grad(set_to_none=True)
        loss.backward()
        step = -1.0 if targeted else 1.0
        x_adv = x_adv + step * alpha * x_adv.grad.sign()
        # projection L_inf relative à l'original + clip domaine
        x_adv = torch.clamp(x_orig + (x_adv - x_orig).clamp(-epsilon, epsilon), clip_min, clip_max)
    return x_adv.detach()
```

### PGD-L2 (pour contraintes L2, ex. DeepFool Challenge targeted)

```python
def pgd_l2(model, x, y, epsilon, alpha, num_iter=50, targeted=False,
           clip_min=0.0, clip_max=1.0):
    """PGD sous contrainte L2 (projection sur la boule L2 de rayon epsilon)."""
    x_orig = x.clone().detach()
    x_adv = x_orig.clone()
    for _ in range(num_iter):
        x_adv = x_adv.detach().requires_grad_(True)
        loss = F.cross_entropy(model(x_adv), y)
        model.zero_grad(set_to_none=True)
        loss.backward()
        g = x_adv.grad
        g_norm = g.view(g.size(0), -1).norm(p=2, dim=1).clamp_min(1e-12).view(-1,1,1,1)
        step = -1.0 if targeted else 1.0
        x_adv = x_adv + step * alpha * g / g_norm         # pas normalisé L2
        delta = x_adv - x_orig
        d_norm = delta.view(delta.size(0), -1).norm(p=2, dim=1).view(-1,1,1,1)
        factor = (epsilon / d_norm.clamp_min(1e-12)).clamp(max=1.0)
        x_adv = torch.clamp(x_orig + delta * factor, clip_min, clip_max)
    return x_adv.detach()
```

### DeepFool (untargeted, L2, multi-classe)

```python
from typing import Tuple

def deepfool(image, net, num_classes=10, overshoot=0.02, max_iter=50, device='cpu'):
    """DeepFool L2 untargeted. image: (1,C,H,W). net.eval() requis.
    Returns (r_tot, loop_i, label, k_i, pert_image)."""
    image = image.to(device); net = net.to(device)
    f_image = net(image).data.cpu().numpy().flatten()
    I = f_image.argsort()[::-1]
    label = I[0]
    pert_image = image.clone()
    r_tot = torch.zeros(image.shape).to(device)
    loop_i = 0
    while loop_i < max_iter:
        x = pert_image.clone().requires_grad_(True)
        fs = net(x)
        k_i = fs.data.cpu().numpy().flatten().argsort()[::-1][0]
        if k_i != label:
            break
        pert = float('inf'); w = None
        for k in range(1, num_classes):
            if I[k] == label:
                continue
            if x.grad is not None: x.grad.zero_()
            fs[0, I[k]].backward(retain_graph=True)
            grad_k = x.grad.data.clone()
            if x.grad is not None: x.grad.zero_()
            fs[0, label].backward(retain_graph=True)
            grad_label = x.grad.data.clone()
            w_k = grad_k - grad_label
            f_k = (fs[0, I[k]] - fs[0, label]).data.cpu().numpy()
            pert_k = abs(f_k) / (torch.norm(w_k.flatten()) + 1e-10)
            if pert_k < pert:
                pert = pert_k; w = w_k
        r_i = (pert + 1e-4) * w / (torch.norm(w.flatten()) + 1e-10)
        r_tot = r_tot + r_i
        pert_image = image + (1 + overshoot) * r_tot
        loop_i += 1
    return r_tot, loop_i, label, k_i, pert_image
```

### Helpers API challenges (base64 PNG ↔ tensor)

```python
import io, base64, numpy as np
from PIL import Image

def x01_from_b64_png(b64):          # MNIST 28x28 grayscale
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("L")
    x = np.asarray(img, dtype=np.float32) / 255.0
    return np.clip(x, 0.0, 1.0)

def b64_png_from_x01(x2d):
    x255 = np.clip((x2d * 255.0).round(), 0, 255).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(x255, mode="L").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def linf(a, b): return float(np.max(np.abs(a - b)))
def l2(a, b):   return float(np.linalg.norm((a - b).ravel(), ord=2))
```

**Rappels pièges (🎯 Exam) :**
- Toujours `model.eval()` avant d'attaquer.
- Vérifier si la normalisation est **interne** (MNIST `SimpleClassifier`, forward renvoie log_softmax) ou **externe** (CIFAR `CIFAR10CNN`, appliquer `(x-mean)/std` avant forward, logits bruts).
- Après ré-encodage PNG (quantization uint8), re-vérifier `pred` ET la norme (garder une marge sur ε).
- I-FGSM/PGD : projection relative à l'image ORIGINALE, pas au précédent itéré.
- DeepFool L2 → attaque minimale ; pour un budget L2 imposé, DeepFool suffit si le threshold est généreux.
