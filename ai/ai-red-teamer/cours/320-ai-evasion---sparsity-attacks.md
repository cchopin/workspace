# AI Evasion - Sparsity Attacks (module 320)

## En bref

Les **sparsity attacks** cherchent la misclassification en modifiant le **moins de features possible** (pixels), c.-à-d. en minimisant la **pseudo-norme L0** = nombre de coordonnées qui diffèrent entre `x_adv` et `x`, au lieu de minimiser l'amplitude (L2/L∞). Deux familles couvertes :
- **ElasticNet / EAD** (Chen et al. 2018) : attaque de type C&W qui ajoute une régularisation **L1 + L2**. Le terme **L1 induit la sparsité** (met des coordonnées exactement à zéro via soft-thresholding), le **L2 lisse** l'optimisation. Résolue par **FISTA** (proximal + momentum de Nesterov) avec **binary search sur la constante c**. Hyperparams clés : `beta` (poids L1 = sparsité), `c` (attaque vs distorsion), `learning_rate`, `max_iterations`, `binary_search_steps`.
- **JSMA** (Papernot et al. 2016) : construit une **saliency map** à partir du **Jacobian forward** (∂F/∂x pour chaque classe), sélectionne à chaque itération le/les pixel(s) qui **augmentent la classe cible et suppriment les concurrentes**, et les sature. Contrôle L0 **explicite** via `gamma` (budget de features) et `theta` (pas). Variantes : single-pixel et **pairwise** (2 pixels/itération).
- Les trois challenges (EAD, JSMA, Skills Assessment CIFAR-10 ResNet-18) sont **non résolus** (user_answer vides) : chaque flag `HTB{...}` s'obtient en soumettant un adversarial valide à l'API. Méthode détaillée pour chacun ci-dessous.
- Idées-force examen : **L0 = compter les pixels changés** ; **L1 → sparsité** (coins du diamant) ; **saliency = α·|β| sous contraintes de signe** ; **calculer le Jacobian = 1 backward pass par classe** ; **wrt=logits (pas softmax)**.

---

## 1. Introduction aux Sparsity Evasion Attacks

### 1.1 La pseudo-norme L0

La sparsité se mesure par la **pseudo-norme L0** = nombre de coordonnées qui diffèrent :

```
‖x_adv − x‖₀ = |{ i | (x_adv)_i ≠ x_i }|
```

Au lieu de répartir de petits changements sur toutes les features (L∞, L2), les sparsity attacks **concentrent les modifications sur un petit ensemble de features à fort impact**. Elles préservent l'essentiel de l'input inchangé et peuvent **échapper aux détecteurs d'anomalies** réglés sur le bruit global.

### 1.2 De first-order à sparsity

Le module précédent (first-order : FGSM en L∞, DeepFool en L2) pénalisait la **taille** de la perturbation mais laissait toutes les features bouger. Ici la contrainte pertinente est **combien** de features peuvent changer (attaque discrète/partiellement discrète : bits d'un binaire, pixels qui saturent aux bornes, tokens un par un).

### 1.3 Threat model et budgets

- Attaquant **inference-time** qui peut calculer ou approximer des gradients.
- **White-box** : dérive à travers le modèle pour sélectionner les features. **Black-box** : estime les importances par requêtes ou transfère depuis un surrogate.
- Budget principal = **L0**, parfois avec limites auxiliaires L2 ou L∞.
- Les inputs restent dans `[0,1]` (images) après chaque update. Si normalisation `x̂ = (x − μ)/σ`, les gradients se propagent par chain rule → raisonner en pixel space reste correct en respectant les box constraints.

### 1.4 Deux chemins vers la sparsité (🎯 Exam)

| Méthode | Principe | Contrôle de la sparsité |
|---|---|---|
| **ElasticNet (EAD)** | ajoute une pénalité **L1** à l'objectif ; L1 pousse de nombreuses coordonnées à **exactement zéro** tout en restant continu (approxime L0) | paramètre `β` (poids du terme L1) |
| **JSMA** | budget **L0 explicite** : modifie 1 ou 2 features/itération via une **saliency map** issue du Jacobian | paramètre `γ` (fraction de features) |

Objectif EAD générique :
```
min_{x'}  c·f(x') + ‖x'−x‖₂² + β·‖x'−x‖₁    s.t.  x' ∈ [0,1]
```
où `f(x')` est une loss de misclassification (souvent targeted), `c` équilibre succès vs compacité, `β` contrôle la sparsité via L1.

---

## 2. ElasticNet (EAD)

### 2.1 Motivation : limites du single-norm

- **FGSM (L∞)** : perturbe uniformément tous les pixels jusqu'à ε → exemples visuellement bruités.
- **DeepFool (L2)** : perturbation lisse mais **dense** (chaque pixel contribue un peu).
- **L1** : offre la **sparsité**. Sa boule (diamant) a des **coins pointus le long des axes de coordonnées** → l'optimisation met naturellement beaucoup de coordonnées à zéro exactement. En minimisant `‖x‖₁ = Σ_i |x_i|`, le gradient pousse vers des solutions où la plupart des `x_i = 0`.

**Trade-off sparsity-smoothness** : L2 est optimization-friendly (gradients bien définis partout) mais dense ; L1 est sparse mais non-différentiable aux coins. **EAD combine les deux** : L2 fournit des gradients lisses (stabilité), L1 induit la sparsité (zeroing des pixels peu importants). Le paramètre **β** règle l'équilibre.

**Exemple numérique (🎯 Exam — pourquoi L1 sépare des cas que L2 confond)** : image 28×28.
- Cas A : 100 pixels changés de 0.10 → L2² = 100×0.10² = **1.00**, L1 = 100×0.10 = **10.0**.
- Cas B : 10 pixels changés de 0.316 → L2² ≈ 10×0.316² ≈ **1.00**, L1 ≈ 10×0.316 = **3.16**.
- Même L2² → le terme smoothness les traite pareil. **Le terme L1 les sépare**, favorisant B (moins de pixels). **β grand → tend vers B (sparse)** ; **β petit → tend vers L2 pur (dense, faible amplitude)**.

Origine : Chen, Zhang, Sharma, Yi, Hsieh 2018, *"EAD: Elastic-Net Attacks to Deep Neural Networks via Adversarial Examples"* (arxiv.org/abs/1709.04114). S'appuie sur le framework **Carlini & Wagner (C&W)**.

### 2.2 Métriques de distance

Pour une image 28×28 (784 pixels) :
- **L1** = `Σ |x'_i − x_i|` : magnitude totale du changement. 100 px × 0.15 = 15.0 ; 50 px × 0.30 = 15.0 (identiques). L1 pondère chaque pixel par son amplitude.
- **L2** (au carré) = `Σ (x'_i − x_i)²` : distance euclidienne² ; pénalise fortement les gros changements individuels. 100 px × 0.15² = **2.25** ; 50 px × 0.30² = **4.50** (le second a 2× le L2 malgré même L1).
- **Elastic-net** : `‖δ‖₂² + β·‖δ‖₁`. β=0 → L2 pur ; β↑ → biais vers plus sparse.

```python
def compute_distances(adv_images, original_images, beta):
    """Compute L1, L2, and elastic-net distances. Returns (batch_size,) each."""
    l1_dist = torch.sum(torch.abs(adv_images - original_images), dim=(1, 2, 3))
    l2_dist = torch.sum((adv_images - original_images) ** 2, dim=(1, 2, 3))
    elastic_dist = l2_dist + beta * l1_dist
    return l1_dist, l2_dist, elastic_dist
```
Note : `l2_dist` est ici le **L2 au carré** (pas de sqrt), sommé par exemple.

### 2.3 Adversarial loss (Carlini & Wagner)

Loss **margin-based** comparant les **logits** (Z). Untargeted (s'éloigner de la vraie classe `y`) :
```
f(x', y) = max( Z_y(x') − max_{j≠y} Z_j(x') + κ , 0 )
```
- Ex : vraie classe 7, Z₇=2.8, meilleur concurrent Z₄=1.2, κ=0 → margin = 2.8−1.2+0 = **1.6** > 0 → loss 1.6, le gradient réduit Z₇ et augmente Z₄.
- Après flip : Z₇=1.0, concurrent Z₂=1.5 → 1.0−1.5+0 = −0.5 → hinge clamp `max(−0.5,0)=0` → **misclassification confirmée**, l'optim se concentre sur la distorsion.
- **κ (confidence)** : marge exigée. κ=0 → succès dès qu'un concurrent dépasse d'un iota. κ>0 → concurrent doit dépasser d'au moins κ → adversarials plus robustes mais plus grosse perturbation.

Targeted (le target doit dépasser) : `f = max(other − real + κ, 0)`. Ex target=2.0, concurrent=2.6, κ=0 → `max(2.6−2.0,0)=0.6` (pas encore) ; target=2.7 vs 2.6 → `max(−0.1,0)=0`.

```python
def compute_adversarial_loss(logits, labels_onehot, confidence, targeted=False):
    """C&W margin loss per example (batch_size,). Zero once margin achieved."""
    # Extract scores
    real = torch.sum(labels_onehot * logits, dim=1)
    other = torch.max((1 - labels_onehot) * logits - labels_onehot * 10000, dim=1)[0]
    # Compute margin loss
    if targeted:
        loss = torch.clamp(other - real + confidence, min=0)
    else:
        loss = torch.clamp(real - other + confidence, min=0)
    return loss
```
Astuce d'implémentation : `real` extrait le logit vrai via le masque one-hot (produit + somme). `other` : `(1−onehot)*logits` annule la vraie classe, `− onehot*10000` la rend impossible à sélectionner comme max, puis `torch.max`.

### 2.4 Objectif total (partie lisse)

```
L_total = c·f(x', y) + ‖x' − x‖₂²
```
Le **terme L1 n'apparaît PAS ici** : il est géré par le **proximal operator** de FISTA (pas par le gradient). Ex : f=0.6, L2²=2.25, c=0.1 → L_total = 0.1×0.6+2.25 = **2.31** ; c=1.0 → **2.85**. c↑ = plus de pression de misclassification.

```python
def compute_total_loss(adv_images, original_images, labels_onehot, const,
                       model, beta, confidence, targeted=False):
    """Smooth part: c * adversarial + squared L2 (L1 via proximal operator)."""
    logits = model(adv_images)
    adversarial_loss = compute_adversarial_loss(logits, labels_onehot, confidence, targeted)
    l1_dist, l2_dist, elastic_dist = compute_distances(adv_images, original_images, beta)
    # L1 is handled by FISTA's proximal operator, not in this gradient
    total_loss = const * adversarial_loss + l2_dist
    return total_loss, adversarial_loss, (l1_dist, l2_dist, elastic_dist)
```

### 2.5 Proximal operators & FISTA

**Pourquoi L1 est dur** : `|x|` a un **coin non-différentiable en 0**. La descente de gradient naïve donne de la **pseudo-sparsité** (valeurs proches de zéro mais jamais exactement zéro), pas de la vraie sparsité (zéros exacts).

**Proximal operator** — généralise la projection aux pénalités non-lisses :
```
prox_{λh}(z) = argmin_x { ½‖x − z‖₂² + λ·h(x) }
```

**Soft-thresholding = prox de la norme L1** (opère élément par élément) :
```
                 ⎧ z_i − λ   si z_i > λ
S_λ(z)_i =       ⎨ 0         si |z_i| ≤ λ      (dead zone → sparsité)
                 ⎩ z_i + λ   si z_i < −λ
```
Dérivation : minimiser `½(x_i−z_i)² + λ|x_i|`. Pour z_i>λ, minimum en x_i>0 → `x_i−z_i+λ=0` → `x_i=z_i−λ`. Pour la boule L2 (comparaison) : `prox_{λ‖·‖₂}(z) = max(0, 1−λ/‖z‖₂)·z`.

**ISTA** (proximal gradient) : `x^(k+1) = prox_{ηh}( x^(k) − η∇f(x^(k)) )`.

**FISTA** (accéléré, Nesterov) :
```
x^(k+1) = prox_{ηh}( y^(k) − η∇f(y^(k)) )
t_{k+1} = (1 + √(1 + 4·t_k²)) / 2
y^(k+1) = x^(k+1) + ((t_k − 1)/t_{k+1})·(x^(k+1) − x^(k))
```
FISTA atteint le taux optimal **O(1/k²)** pour les problèmes convexes lisses. Dans le code, le coefficient de momentum est simplifié en `k/(k+3)` (approxime `(k−1)/(k+2)`, légèrement plus conservateur, borné < 1). Ex progression : k=1→0.25, 5→0.625, 10→0.769, 50→0.943, 100→0.971, 1000→0.997.

**Application de FISTA à EAD** :
- lisse : `f(x') = c·max(Z_y − max_{j≠y} Z_j + κ, 0) + ‖x'−x‖₂²`, gradient `∇_{x'}‖x'−x‖₂² = 2(x'−x)`
- non-lisse : `h(x') = β·‖x'−x‖₁`, prox : `prox_{ηβ‖·‖₁}(z) = x + S_{ηβ}(z − x)` (soft-threshold appliqué à la **différence** avec l'original)

```python
def compute_fista_momentum(iteration):
    """Nesterov acceleration: k/(k+3). In [0,1)."""
    return iteration / (iteration + 3.0)

def apply_shrinkage_thresholding(y, original_images, threshold, clip_min=0.0, clip_max=1.0):
    """Soft thresholding → sparse perturbations. threshold = learning_rate * beta."""
    diff = y - original_images
    shrink_positive = torch.clamp(y - threshold, min=clip_min, max=clip_max)
    shrink_negative = torch.clamp(y + threshold, min=clip_min, max=clip_max)
    cond_positive = (diff > threshold).float()
    cond_zero = (torch.abs(diff) <= threshold).float()
    cond_negative = (diff < -threshold).float()
    result = (cond_positive * shrink_positive
              + cond_zero * original_images      # dead zone → revient à l'original (zéro exact)
              + cond_negative * shrink_negative)
    return result
```
Effet du threshold : sur une perturbation 5×5, β=0.1 zéroe 13/25 éléments (64% sparse) ; β=0.2 → 80% sparse ; β=0.05 → 44% sparse. Les éléments éliminés deviennent des **zéros exacts** (pas 0.001).

**Une itération FISTA complète** :
```python
def fista_step(adv_images, y_momentum, original_images, labels_onehot, const, model,
               beta, learning_rate, confidence, iteration, targeted=False,
               clip_min=0.0, clip_max=1.0):
    """One FISTA iteration: gradient + shrinkage + momentum."""
    y_momentum = y_momentum.detach().requires_grad_(True)
    total_loss, adversarial_loss, distances = compute_total_loss(
        y_momentum, original_images, labels_onehot, const, model, beta, confidence, targeted)
    total_loss_summed = total_loss.sum()
    total_loss_summed.backward()
    grad = y_momentum.grad
    # Gradient step (smooth part)
    y_new = y_momentum - learning_rate * grad
    # Proximal operator for L1 (shrinkage), threshold = learning_rate * beta
    adv_new = apply_shrinkage_thresholding(y_new, original_images, learning_rate * beta, clip_min, clip_max)
    # Nesterov momentum update
    momentum_coef = compute_fista_momentum(iteration)
    y_new_momentum = adv_new + momentum_coef * (adv_new - adv_images)
    return adv_new, y_new_momentum, total_loss_summed.item(), distances
```

**Critère d'arrêt** : `|f^(k+1) + h^(k+1) − f^(k) − h^(k)| < ε`.

### 2.6 Binary search sur la constante c (🎯 Exam)

`c` équilibre misclassification vs distorsion. **c grand** = priorité au fooling (grosses perturbations) ; **c petit** = priorité à l'imperceptibilité (risque d'échec). Le binary search trouve automatiquement le **c minimal suffisant** par exemple :
- Attaque **réussie** → on **baisse l'upper bound** (on peut essayer plus petit).
- Attaque **échouée** → on **monte le lower bound** (il faut plus grand) ; si aucune borne haute encore, `c *= 10` (croissance exponentielle).

```python
def check_attack_success(adv_images, labels, model, targeted=False):
    """Boolean mask (batch_size,) of successful attacks."""
    with torch.no_grad():
        outputs = model(adv_images)
        predictions = outputs.argmax(dim=1)
        if targeted:
            success = predictions.eq(labels)      # prédiction == target
        else:
            success = predictions.ne(labels)      # prédiction != vraie classe
    return success

def update_binary_search_bounds(lower_bound, upper_bound, const, success_mask):
    for i in range(len(success_mask)):
        if success_mask[i]:
            upper_bound[i] = min(upper_bound[i], const[i])
            if upper_bound[i] < 1e10:
                const[i] = (lower_bound[i] + upper_bound[i]) / 2
        else:
            lower_bound[i] = max(lower_bound[i], const[i])
            if upper_bound[i] < 1e10:
                const[i] = (lower_bound[i] + upper_bound[i]) / 2
            else:
                const[i] *= 10  # Exponential increase for persistent failures
    return lower_bound, upper_bound, const
```

### 2.7 Hyperparamètres & exécution EAD

```python
config = {
    "beta": 0.01,             # L1 vs L2 trade-off (plus haut = plus sparse ; 0.05-0.1 très sparse, 0.001 quasi dense)
    "confidence": 0,          # marge kappa de misclassification
    "learning_rate": 0.01,    # pas FISTA (>0.05 diverge, <0.001 très lent)
    "max_iterations": 1000,   # itérations FISTA par binary search step
    "binary_search_steps": 5, # nb d'étapes de binary search (3-5 = rapide, 7-9 = précis)
    "initial_const": 0.001,   # c initial
    "clip_min": 0.0, "clip_max": 1.0,
}
```

Boucle imbriquée (binary search externe, FISTA interne) :
```python
# Initialisation
batch_size = len(attack_data)
original_images = attack_data.clone()
labels_onehot = torch.zeros(batch_size, 10).to(device)
labels_onehot.scatter_(1, attack_targets.unsqueeze(1), 1)
lower_bound = torch.zeros(batch_size).to(device)
upper_bound = torch.ones(batch_size).to(device) * 1e10
const = torch.ones(batch_size).to(device) * config["initial_const"]
best_adv = original_images.clone()
best_l2  = torch.ones(batch_size).to(device) * 1e10

for binary_step in range(config["binary_search_steps"]):
    # Réinit FISTA depuis les images originales (évite la contamination entre valeurs de c)
    adv_images = original_images.clone().detach()
    y_momentum = adv_images.clone()
    for iteration in range(config["max_iterations"]):
        adv_images, y_momentum, loss, distances = fista_step(
            adv_images, y_momentum, original_images, labels_onehot, const, model,
            config["beta"], config["learning_rate"], config["confidence"], iteration,
            targeted=False, clip_min=config["clip_min"], clip_max=config["clip_max"])
    success_mask = check_attack_success(adv_images, attack_targets, model, targeted=False)
    l1_dist, l2_dist, elastic_dist = compute_distances(adv_images, original_images, config["beta"])
    for i in range(batch_size):
        if success_mask[i] and l2_dist[i] < best_l2[i]:   # garde le meilleur (plus petit L2) qui réussit
            best_adv[i] = adv_images[i]
            best_l2[i]  = l2_dist[i]
    lower_bound, upper_bound, const = update_binary_search_bounds(
        lower_bound, upper_bound, const, success_mask)
```

**Coût** : 20 exemples × 5 steps × 1000 itérations ≈ 5 000 forward + 5 000 backward (batch). GPU moderne : 2-3 min ; CPU : 30-60 min. Model cible d'entraînement : `MNISTClassifierWithDropout` (2 conv dropout 0.25, 2 FC dropout 0.5), 5 epochs, ~98.89% test accuracy. Reproductibilité : `set_reproducibility(1337)`.

**Distinction vs FGSM** : plutôt qu'un ε universel, EAD **découvre le seuil de vulnérabilité de chaque exemple** via binary search (exemples près de la frontière → petit c ; loin → grand c).

---

## 3. ElasticNet Attack Challenge (interactif, docker)

**Objectif** : fabriquer un adversarial qui fait misclassifier un classifieur MNIST via EAD, en respectant **simultanément 3 bornes de distance** :
```
elastic-net : ‖x_adv − x‖₂ + β·‖x_adv − x‖₁ ≤ elastic_max
L2 (aux)    : ‖x_adv − x‖₂ ≤ l2_max
L1 (aux)    : ‖x_adv − x‖₁ ≤ l1_max
```
+ classe prédite ≠ label baseline, + pixels dans `[0,1]`. (Ici les bornes L2/L1 utilisent le **L2 non au carré** = sqrt.)

**API** (images = PNG base64 28×28 mono, `[0,1]` après décodage) :
- `GET /health` → `{"status":"ok"}`
- `GET /challenge` → `{sample_index, label, beta, elastic_max, l2_max, l1_max, image_b64}`
- `POST /predict` `{"image_b64": "..."}` → `{pred, confidence}` (ne donne pas le flag ; sert à valider l'encodage)
- `GET /weights` → state_dict binaire (charger sur CPU, archi `SimpleClassifier`)
- `POST /submit` `{"image_b64": "..."}` → `{ok, flag: "HTB{...}", pred, metrics:{l1,l2,linf,elastic}}` ; échec = HTTP 400 avec message (ex `"Elastic too large: 1.85 > 1.80"`, `"L2 too large: 1.42 > 1.40"`, `"Not misclassified; try stronger within bounds"`).

**Archi du modèle serveur** (à répliquer localement — le forward **ne normalise PAS**, il faut appeler `mnist_normalize` avant) :
```python
class SimpleClassifier(nn.Module):
    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, num_classes)
    def forward(self, x):
        x = torch.relu(self.conv1(x)); x = torch.relu(self.conv2(x))
        x = torch.max_pool2d(x, 2); x = self.dropout1(x)
        x = torch.flatten(x, 1); x = torch.relu(self.fc1(x))
        x = self.dropout2(x); x = self.fc2(x)
        return x

MNIST_MEAN, MNIST_STD = 0.1307, 0.3081
def mnist_normalize(x01):   # (N,1,28,28) dans [0,1]
    return (x01 - MNIST_MEAN) / MNIST_STD
```

**Méthode de résolution (challenge NON résolu, user_answer vide)** :
1. `GET /challenge`, décoder `image_b64` en array `[0,1]` (helper `x01_from_b64_png`), lire `beta, elastic_max, l2_max, l1_max, label`.
2. `GET /weights`, charger dans `SimpleClassifier().eval()`. Vérifier que `model(mnist_normalize(x))` prédit bien `label` (parité avec le serveur via `/predict`).
3. Lancer **EAD untargeted** (FISTA + binary search, code section 2) avec le `beta` du challenge, en propageant le gradient **à travers `mnist_normalize`** (raisonner en pixel space `[0,1]`). Utiliser un `learning_rate` ~0.01, plusieurs binary_search_steps.
4. Contrainte importante : respecter les **3 bornes**. Baisser `c` / augmenter `beta` si `elastic`/`L2`/`L1` dépassent ; augmenter `c` si `"Not misclassified"`. Chercher le plus petit perturbation qui fool tout en restant sous les 3 caps.
5. **PNG round-trip** avant soumission (encoder puis re-décoder pour que la perturbation survive à la quantification 8-bit), recalculer localement les distances pour vérifier.
6. `POST /submit` → récupérer `flag`.

**### Questions (section)** — id 3365 (cubes 5, XP 60) : *"After successfully completing the task, what is the flag you receive?"* → **user_answer VIDE (non résolu)**. Réponse = le flag `HTB{...}` renvoyé par `POST /submit`.

---

## 4. JSMA — Jacobian-based Saliency Map Attack

### 4.1 Fondamentaux

JSMA (Papernot, McDaniel, Jha, Fredrikson, Celik, Swami 2016, *"The Limitations of Deep Learning in Adversarial Settings"*, arxiv.org/abs/1511.07528) **minimise L0** (nombre de features) et non l'amplitude. Il identifie les pixels les plus influents via une saliency map et modifie **uniquement ceux-là**, souvent **20-40 pixels sur 784** en MNIST. Les pixels peuvent sauter fort (0.0→1.0) : on échange la stealth contre l'**extrême sparsité** (points/traits visibles plutôt que bruit imperceptible).

**Coût** : linéaire en nb de classes → **1 backward pass par classe** pour le Jacobian complet. MNIST (10 classes) = 10 backward/itération (gérable) ; ImageNet (1000 classes) = 1000 backward/itération (prohibitif).

### 4.2 wrt=logits, pas softmax (🎯 Exam)

Calculer les gradients par rapport aux **logits** (pré-softmax), pas aux probabilités. Post-softmax, comme les probas somment à 1, la différentiation **force β = −α par construction**, ce qui collapse la saliency en un carré de la pente cible et **élimine le terme de suppression des concurrents**. On perd le comportement JSMA voulu. Modèle typique : **LeNet-like MNIST** (les pixels y sont très influents ; les ResNet modernes diluent l'influence → JSMA moins efficace, d'où SparseFool/EAD).

### 4.3 Jacobian & extraction de gradients

Jacobian = matrice `(num_classes, num_features)` où la ligne `i` = `∂F_i/∂x_j` pour tous les pixels. Pour MNIST : `(10, 784)` = 7 840 valeurs (~31 KB fp32).

```python
def compute_class_gradient(x, model, class_idx, wrt='logits'):
    x_grad = x.detach().requires_grad_(True)
    logits = model(x_grad)
    if wrt == 'logits':
        scalar = logits[0, class_idx]
    else:
        probs = F.softmax(logits, dim=1)
        scalar = probs[0, class_idx]
    scalar.backward()                                       # backward doit partir d'un SCALAIRE
    grad = x_grad.grad.detach().cpu().numpy().flatten().copy()  # aplati C-H-W, .copy() détache du graphe
    return grad

def compute_jacobian_matrix(x, model, num_classes=10, wrt='logits'):
    if x.shape[0] != 1:
        raise ValueError("compute_jacobian_matrix expects batch size 1")  # sinon gradients moyennés → faux
    jacobian = []
    for class_idx in range(num_classes):
        grad = compute_class_gradient(x, model, class_idx, wrt)
        jacobian.append(grad)
    return np.asarray(jacobian)     # (num_classes, num_features)
```

**Séparation cible / concurrents** (α = gradient de la cible, β = somme des autres) :
```python
def extract_target_gradient(jacobian, target_class):
    return jacobian[target_class].copy()          # .copy() → évite de corrompre le Jacobian

def extract_other_gradients(jacobian, target_class):
    target_grad = jacobian[target_class]
    total_grad = jacobian.sum(axis=0)             # somme de toutes les lignes
    other_grad = total_grad - target_grad         # β = tout − cible
    return other_grad
```
Ex 3 classes, target=2, J = [[0.2,0.5,-0.1,0.3],[-0.1,0.2,0.4,-0.2],[0.6,-0.3,0.1,0.5]] → α (classe 2) = [0.6,-0.3,0.1,0.5], β = total−α = [0.7,0.4,0.4,0.6]−[0.6,-0.3,0.1,0.5] = **[0.1,0.7,0.3,0.1]**.

**Masquage du search space** (multiplication élément par élément, préserve les indices) :
```python
def apply_search_mask(gradient, search_space):
    return gradient * search_space   # True→1.0, False→0.0 ; pixel 352 reste à l'indice 352
```

### 4.4 Saliency scoring & contraintes de signe (🎯 Exam)

**Score = |α_j| × |β_j|** UNIQUEMENT quand les contraintes de signe sont respectées, sinon 0. Deux directions :
- **Increase** (augmenter le pixel aide) : `∂F_t/∂x_j > 0` (α>0, booste la cible) ET `Σ_{i≠t} ∂F_i/∂x_j < 0` (β<0, supprime les concurrents). Score = `α_j × |β_j|`.
- **Decrease** (diminuer le pixel aide) : `α_j < 0` ET `β_j > 0`. Score = `|α_j| × β_j`.

```python
def score_increase_saliency(target_grad, other_grad):
    increase_mask = (target_grad > 0) & (other_grad < 0)
    scores = target_grad * np.abs(other_grad) * increase_mask
    return scores

def score_decrease_saliency(target_grad, other_grad):
    decrease_mask = (target_grad < 0) & (other_grad > 0)
    scores = np.abs(target_grad) * other_grad * decrease_mask
    return scores

def select_best_direction(inc_scores, dec_scores):
    max_inc_idx = int(np.argmax(inc_scores)); max_dec_idx = int(np.argmax(dec_scores))
    max_inc_score = float(inc_scores[max_inc_idx]); max_dec_score = float(dec_scores[max_dec_idx])
    if max_inc_score > max_dec_score:
        return max_inc_idx, max_inc_score, True    # (pixel_idx, score, increase=True)
    else:
        return max_dec_idx, max_dec_score, False   # increase=False → decrease
```
Ex α=[0.6,-0.3,0.4,0.1,-0.5,0.2], β=[-0.2,0.4,-0.5,0.3,0.6,-0.1] : feature 2 → inc score 0.4×0.5=**0.200** ; feature 4 → dec score 0.5×0.6=**0.300** (gagnant, decrease). Feature 3 (α>0,β>0) invalide dans les deux directions → 0.

**Intuition toy** (target=classe 2, scores initiaux 0.6/0.5/0.3) : feature 1 avec `∂F₂/∂x₁=0.6` et `Σ_{j≠2}=−0.4` → saliency 0.6×0.4=**0.24** (idéal). Feature 2 avec `∂F₂/∂x₂=0.3` mais `Σ=+0.5` → viole la contrainte de signe → saliency **0** (aide plus les concurrents).

### 4.5 Gestion du search space (saturation)

```python
def initialize_search_space(shape):
    num_features = int(np.prod(shape[1:]))     # ignore la dim batch ; MNIST → 784
    return np.ones(num_features, dtype=bool)   # tous disponibles

def remove_saturated_pixels(search_space, x, clip_min=0.0, clip_max=1.0, epsilon=1e-6):
    x_flat = x.detach().cpu().numpy().flatten()
    saturated_min = (x_flat <= clip_min + epsilon)
    saturated_max = (x_flat >= clip_max - epsilon)
    saturated = saturated_min | saturated_max
    updated_mask = search_space & ~saturated    # garde dispo ET non saturé
    return updated_mask
```
Un pixel saturé (à 0.0 ou 1.0) ne peut plus bouger dans cette direction → on le retire (avec tolérance epsilon pour les erreurs d'arrondi).

### 4.6 Utilitaires single-pixel

```python
def apply_single_pixel_perturbation(x, pixel_idx, theta, increase, clip_min=0.0, clip_max=1.0):
    original_shape = x.shape
    x_flat = x.view(-1).clone()                 # clone → évite l'aliasing mémoire
    perturbation = theta if increase else -theta
    x_flat[pixel_idx] = torch.clamp(x_flat[pixel_idx] + perturbation, clip_min, clip_max)
    return x_flat.view(original_shape)          # restaure structure 4D (même ordre C-H-W)

def check_target_reached(x, target_class, model):
    with torch.no_grad():
        logits = model(x)
        prediction = int(logits.argmax(dim=1).item())
    return prediction == target_class

def compute_confidence(x, target_class, model):
    with torch.no_grad():
        logits = model(x)
        probs = F.softmax(logits, dim=1)
        confidence = float(probs[0, target_class].item())
    return confidence
```
Modification **irréversible** : JSMA n'annule jamais un changement, chaque itération est un progrès permanent. Cohérence d'ordre d'aplatissement C-H-W critique (mélanger flatten/reshape → bug catastrophique silencieux, 0% de succès).

### 4.7 Algorithme single-pixel : étape par étape

Cycle itératif : (1) calculer le Jacobian → (2) construire la saliency map → (3) sélectionner le meilleur pixel+direction → (4) appliquer/saturer → (5) mettre à jour le search space. Répéter jusqu'à misclassification ou épuisement du budget L0.

Deux paramètres (🎯 Exam) :
- **θ (theta)** = amplitude par itération. θ grand → attaque rapide mais perturbations plus visibles ; θ petit → plus d'itérations, plus subtil.
- **γ (gamma)** = budget de sparsité (fraction de features). Max pixels = `γ × num_features`. MNIST : `0.15 × 784 = 117`.

```python
config = {'theta': 0.25, 'gamma': 0.15, 'max_iter': 100,
          'wrt': 'logits', 'clip_min': 0.0, 'clip_max': 1.0}

x_adv = x.clone().detach()
search_space = initialize_search_space(x.shape)
num_features = int(np.prod(x.shape[1:]))
max_pixels = int(config['gamma'] * num_features)   # 117
pixels_modified = 0

for iteration in range(config['max_iter']):
    if check_target_reached(x_adv, target_class, model):    # succès
        break
    if pixels_modified >= max_pixels:                        # budget épuisé
        break
    # 1) Jacobian + extraction
    jacobian = compute_jacobian_matrix(x_adv, model, num_classes=10, wrt=config['wrt'])
    alpha = extract_target_gradient(jacobian, target_class)
    beta  = extract_other_gradients(jacobian, target_class)
    alpha_masked = apply_search_mask(alpha, search_space)
    beta_masked  = apply_search_mask(beta, search_space)
    # 2-3) saliency + sélection
    inc_scores = score_increase_saliency(alpha_masked, beta_masked)
    dec_scores = score_decrease_saliency(alpha_masked, beta_masked)
    pixel_idx, saliency, increase = select_best_direction(inc_scores, dec_scores)
    if saliency <= 0:                                        # search space épuisé
        break
    # 4) perturbation
    x_adv = apply_single_pixel_perturbation(x_adv, pixel_idx, config['theta'], increase,
                                            config['clip_min'], config['clip_max'])
    # 5) update search space (retire le pixel choisi + les saturés)
    search_space[pixel_idx] = False
    search_space = remove_saturated_pixels(search_space, x_adv, clip_min, clip_max)
    pixels_modified += 1
```
Perf single-pixel (démo 10 échantillons) : **70% succès**, ~**73.6 pixels** modifiés en moyenne (9.39% de l'image), les échecs épuisent les 100 itérations. Effet de θ : testé sur 0.10→1.00 (subtil → agressif).

### 4.8 Variante pairwise (2 pixels/itération)

Modifie **2 pixels simultanément** pour exploiter des **synergies** : `α_pq = α_p + α_q`, `β_pq = β_p + β_q`, contraintes de signe **sur les sommes** (pas sur chaque pixel), score `S⁺[p,q] = α_pq × |β_pq|`. Cela découvre des paires synergiques où aucun pixel seul ne passerait le filtre single-pixel.

**Complexité** : O(n²) — `C(n,2) = n(n−1)/2` paires. Sans pruning, 784 pixels → `C(784,2)` ≈ 306 936 paires ; avec **top_k=128** → `C(128,2) = 8 128` (−97%). Le pruning garde les top-k par `|α_j|×|β_j|`.

```python
def prune_candidates(alpha, beta, search_space, top_k):
    alpha_masked = alpha * search_space; beta_masked = beta * search_space
    valid = np.where(search_space)[0]
    if valid.size < 2 or top_k is None or valid.size <= top_k:
        return valid
    prelim_scores = np.abs(alpha_masked[valid]) * np.abs(beta_masked[valid])
    idx = np.argsort(-prelim_scores)[:top_k]
    return valid[idx]

def evaluate_pairs(alpha, beta, valid, direction):
    best_p, best_q, best_score = -1, -1, 0.0
    for i in range(valid.size):
        p = valid[i]
        for j in range(i + 1, valid.size):
            q = valid[j]
            a_pq = alpha[p] + alpha[q]; b_pq = beta[p] + beta[q]
            if direction == 'increase':
                if a_pq <= 0 or b_pq >= 0: continue     # signe sur la SOMME
                score = a_pq * abs(b_pq)
            else:
                if a_pq >= 0 or b_pq <= 0: continue
                score = abs(a_pq) * b_pq
            if score > best_score:
                best_score = float(score); best_p, best_q = int(p), int(q)
    return best_p, best_q, best_score

def compute_pairwise_saliency(alpha, beta, search_space, direction='increase', top_k=None):
    valid = prune_candidates(alpha, beta, search_space, top_k)
    if valid.size < 2: return -1, -1, 0.0
    best_p, best_q, best_score = evaluate_pairs(alpha, beta, valid, direction)
    if best_p == -1: return -1, -1, 0.0
    return best_p, best_q, best_score

def apply_pair_perturbation(x, p, q, theta, increase, clip_min=0.0, clip_max=1.0):
    original_shape = x.shape
    x_flat = x.view(-1).clone()
    step = theta if increase else -theta
    x_flat[p] = torch.clamp(x_flat[p] + step, clip_min, clip_max)
    x_flat[q] = torch.clamp(x_flat[q] + step, clip_min, clip_max)
    return x_flat.view(original_shape)
```

Config pairwise : `theta=1.0` (saturation agressive en un pas), `gamma=0.15`, `max_iter=90`, `top_k=128`. Budget 117 px, pairwise modifie 2 px/itér → `⌊117/2⌋ = 58` itérations max. `pixels_modified += 2` par itération. Sélection : tournament entre increase/decrease (increase gagne les égalités `>=`), sentinelles `p=-1/q=-1` = pas de paire valide.

**Comparaison single vs pairwise (🎯 Exam)** :

| Métrique | Single-pixel | Pairwise |
|---|---|---|
| Succès | 70% | **90%** |
| Pixels moyens | 73.6 | **42.8** |
| Itérations moyennes | 74.3 | **22.4** (−69.9%) |
| Coût/itération | ~15.0 ms | ~17.1 ms (+14%) |
| Saliency compute | <0.01 ms | 2.13 ms |

Le **Jacobian domine le coût** (~15 ms = 10 backward passes), donc le surcoût pairwise est négligeable vs les gains (moins d'itérations, meilleur succès). **Synergie** = `impact_pq − (impact_p + impact_q)` : positive = interaction non-linéaire, négative = interférence, zéro = additif. Souvent non mesurable en isolation car l'attaque réussit par accumulation séquentielle.

---

## 5. JSMA Attack Challenge (interactif, docker)

**Objectif** : adversarial **targeted** contre un classifieur MNIST via JSMA, en modifiant **au plus `l0_budget` pixels** :
```
‖x_adv − x‖₀ ≤ budget    (différences > 1e-6)
```
+ classe prédite == `target_class`, + L2 < `max_l2` (garde-fou anti « copie d'une image cible »), + pixels dans `[0,1]`.

**API** :
- `GET /health` → `{"status":"healthy"}`
- `GET /challenge` → `{sample_index, target_class, l0_budget, original_label, max_l2, image_b64}` (ex : sample_index=2, target_class=7, l0_budget=50, original_label=1, max_l2=8.0)
- `POST /predict` → `{predicted_class, confidence, all_probabilities[10]}`
- `GET /weights` → state_dict, archi **`MNISTClassifier` LeNet-5** (Tanh + AvgPool)
- `POST /submit` → `{success, flag:"HTB{...}", pixels_modified, predicted_class, target_class}` ; échec 400 (ex `"L0 constraint violated: 55 pixels modified (max: 50)"`, `"Target misclassification failed: predicted 3, expected 7"`, `"Submission rejected: please derive the adversarial example from the provided baseline image"`).

**Archi serveur (à répliquer)** — forward retourne **log_softmax** (attention : le "wrt=logits" doit alors viser la sortie avant log_softmax, ou traiter les log-probas ; le forward ne normalise pas → appeler `mnist_normalize` avant) :
```python
class MNISTClassifier(nn.Module):   # LeNet-5 : Conv1 1->6 5x5 Tanh AvgPool2, Conv2 6->16 5x5 Tanh AvgPool2, FC 256->120->84->10
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5, stride=1, padding=0)
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5, stride=1, padding=0)
        self.pool  = nn.AvgPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(16 * 4 * 4, 120); self.fc2 = nn.Linear(120, 84); self.fc3 = nn.Linear(84, 10)
        self.act = nn.Tanh()
    def forward(self, x):
        x = self.act(self.conv1(x)); x = self.pool(x)      # (B,6,12,12)
        x = self.act(self.conv2(x)); x = self.pool(x)      # (B,16,4,4)
        x = torch.flatten(x, 1)                            # (B,256)
        x = self.act(self.fc1(x)); x = self.act(self.fc2(x)); x = self.fc3(x)
        return F.log_softmax(x, dim=1)
```

**Méthode de résolution (NON résolu, user_answer vide)** :
1. `GET /challenge`, décoder l'image, lire `target_class`, `l0_budget`, `max_l2`, `original_label`.
2. `GET /weights`, charger `MNISTClassifier().eval()`. Vérifier parité avec `/predict`.
3. Lancer **JSMA targeted** (section 4.7 ou 4.8 pairwise), en calculant le Jacobian à travers `mnist_normalize`, `wrt` sur la sortie du réseau. Utiliser `gamma` tel que `γ×784 ≤ l0_budget` (ou plafonner `max_pixels = l0_budget`).
4. Le pairwise est recommandé (moins de pixels, meilleur succès) pour rester sous le budget L0. Vérifier localement `count_modified_pixels ≤ budget` et `L2 < max_l2`.
5. PNG round-trip, puis `POST /submit` → `flag`.

**### Questions (section)** — id 3366 (cubes 5, XP 60) : *"After successfully completing the task, what is the flag you receive?"* → **user_answer VIDE (non résolu)**. Réponse = flag de `POST /submit`.

---

## 6. Skills Assessment (interactif, docker)

**Objectif** : adversarial **targeted** contre un **ResNet-18 CIFAR-10**, soumettre un PNG base64 **32×32×3**, en utilisant **EAD ou JSMA**. L'évaluateur valide la signature de méthode et impose un **seuil minimal de perturbation L2 = 1.5** (anti-triche : empêche de soumettre l'image clean).

**API** :
- `GET /health` → `{status, model, items}`
- `GET /challenge` → `{items:[{sample_id, label, target, required_method, image_b64}]}`
- `GET /model` → `{arch:"ResNetCIFAR", weights_sha256, weights_size, normalize:{mean,std}, weights_url:"/model/weights"}`
- `GET /model/weights` → poids ; `POST /predict` (valider l'encodage)
- `POST /submit_images` `{"items":[{"sample_id":0,"method":"ead","image_b64":"..."}]}` → flag si (misclassification targeted + signature méthode + L2 ≥ 1.5).

**Archi** : `ResNetCIFAR` (BasicBlock ×(2,2,2,2), conv1 3→64 3x3, layers 64/128/256/512, AdaptiveAvgPool, fc 512→10). Normalisation CIFAR : mean `(0.4914,0.4822,0.4465)`, std `(0.2470,0.2435,0.2616)`. Chargement des poids : `state.get("state_dict_ema") or state.get("state_dict") or state`. Images RGB : transposer `(C,H,W) ↔ (H,W,C)`.

**Méthode de résolution (NON résolu, user_answer vide)** :
1. `GET /challenge` + `GET /model`, télécharger les poids, charger `ResNetCIFAR`.
2. Pour chaque item : selon `required_method` (`"ead"` ou `"jsma"`), lancer l'attaque **targeted** vers `target`, à travers `cifar_normalize` (3 canaux). ResNet dilue l'influence pixel → JSMA plus dur ; EAD généralement plus fiable.
3. **PNG round-trip** obligatoire (mirror du decode serveur). S'assurer que **L2 ≥ 1.5** (sinon rejet anti-triche) tout en atteignant la classe cible.
4. `POST /submit_images` avec le bon `sample_id` + `method` → flag.

**### Questions (section)** — id 3364 (cubes 10, XP 60) : *"After successfully completing the task, what is the flag you receive?"* → **user_answer VIDE (non résolu)**. Réponse = flag de `POST /submit_images`.

---

## 7. Récapitulatif comparatif (🎯 Exam)

| Attaque | Norme visée | Mécanisme sparsité | Optim | Hyperparams clés | Distinctif |
|---|---|---|---|---|---|
| FGSM | L∞ | aucune (dense) | 1 pas, sign | ε | rapide, dense |
| DeepFool | L2 | aucune (dense) | linéarisations | — | minimal L2 |
| **EAD** | **L1+L2 (≈L0)** | pénalité **L1** → soft-threshold (zéros exacts) | **FISTA** + binary search c | **β**, c, lr, iters, bs_steps | sparse **et** lisse |
| **JSMA** | **L0 explicite** | saliency map, sélection 1-2 px/itér | itératif greedy | **θ, γ** (, top_k) | L0 contrôlé, pixels saturés |

Points clés transversaux :
- **EAD** : L1 dans le proximal (pas dans le gradient), L2 dans le gradient. Soft-thresholding = prox de L1. Binary search auto-tune c par exemple.
- **JSMA** : Jacobian = 1 backward/classe ; wrt=logits ; saliency = α·|β| sous contraintes de signe ; θ = pas, γ = budget L0.

---

## 🎯 Questions d'examen probables

**Q1. Quelle norme les sparsity attacks minimisent-elles, et comment se définit-elle ?**
La **pseudo-norme L0** = `‖x_adv − x‖₀ = |{i | (x_adv)_i ≠ x_i}|`, le **nombre de features modifiées** (pas leur amplitude).

**Q2. Pourquoi le terme L1 induit-il la sparsité, contrairement à L2 ?**
La boule L1 (diamant) a des **coins pointus sur les axes de coordonnées** ; l'optimisation y met de nombreuses coordonnées à **exactement zéro**. L2 (boule ronde, lisse) répartit de petits changements sur toutes les dimensions (dense), sans garantie de zéros.

**Q3. Dans EAD, où est traité le terme L1 dans FISTA ?**
Pas dans le gradient : par le **proximal operator** (soft-thresholding `S_{ηβ}`). Le gradient ne porte que sur la partie lisse `c·f(x') + ‖x'−x‖₂²`.

**Q4. Écrire l'opérateur de soft-thresholding S_λ(z).**
`z−λ si z>λ ; 0 si |z|≤λ (dead zone) ; z+λ si z<−λ`. C'est le prox de la norme L1.

**Q5. Pourquoi FISTA plutôt qu'une descente de gradient naïve pour EAD ?**
`|x|` est **non-différentiable en 0** → la descente naïve donne de la pseudo-sparsité (valeurs ~0 jamais exactement 0). FISTA décompose lisse/non-lisse, remplace le gradient de L1 par le prox (zéros exacts) et accélère via momentum de Nesterov (O(1/k²)).

**Q6. Donner l'update de momentum FISTA utilisé dans le code et sa progression.**
`compute_fista_momentum(k) = k/(k+3)` (approx de la forme Nesterov `t_{k+1}=(1+√(1+4t_k²))/2`). Croît de 0.25 (k=1) vers ~1 : conservateur tôt, agressif tard, borné < 1.

**Q7. Rôle de la constante c et du binary search dans EAD ?**
`c` équilibre misclassification (grand c) vs distorsion (petit c). Le binary search trouve le **c minimal suffisant par exemple** : succès → baisse upper_bound ; échec → monte lower_bound (ou `c*=10` si pas encore de borne haute).

**Q8. Formule de la C&W adversarial loss (untargeted) et effet de κ.**
`f = max(Z_y − max_{j≠y} Z_j + κ, 0)`. κ=0 : succès dès qu'un concurrent dépasse ; κ>0 : marge exigée → adversarials plus robustes, plus grosse perturbation. Loss = 0 une fois la marge atteinte.

**Q9. Pourquoi calculer le Jacobian JSMA wrt=logits et non wrt=probabilities ?**
Post-softmax, les probas somment à 1 → **β = −α par construction**, ce qui collapse la saliency en carré de la pente cible et **supprime le terme de suppression des concurrents**. On perd le comportement JSMA.

**Q10. Combien de backward passes pour un Jacobian JSMA, et implication ?**
**1 backward par classe** (10 pour MNIST). Coût linéaire en nb de classes → prohibitif sur ImageNet (1000 classes = 1000 backward/itération).

**Q11. Formule de saliency JSMA et contraintes de signe (direction increase).**
Score = `α_j × |β_j|` **si** `α_j > 0` (booste la cible) ET `β_j < 0` (supprime les concurrents), sinon 0. Direction decrease : `α_j<0` ET `β_j>0`, score `|α_j|×β_j`.

**Q12. Que contrôlent θ et γ dans JSMA ?**
**θ** = pas (amplitude par pixel/itération ; grand = rapide/visible, petit = subtil/lent). **γ** = budget de sparsité : `max_pixels = γ × num_features` (MNIST : 0.15×784 = 117).

**Q13. Pourquoi retirer les pixels saturés du search space ?**
Un pixel à 0.0 ou 1.0 (avec tolérance epsilon) ne peut plus bouger dans la direction utile ; le garder gaspille des itérations. `remove_saturated_pixels` fait `search_space & ~saturated`.

**Q14. Pairwise JSMA : principe et gain, complexité ?**
Modifie 2 pixels/itération avec contraintes de signe **sur les sommes** `α_pq=α_p+α_q`, `β_pq=β_p+β_q`, score `α_pq×|β_pq|`. Découvre des synergies. Complexité **O(n²)** = `C(n,2)` paires, réduite par `top_k` (128 → 8 128 paires). Gain : 70%→90% succès, 73.6→42.8 pixels, 74.3→22.4 itérations.

**Q15. Quelle est la contrainte à respecter dans le challenge EAD, en plus de la misclassification ?**
**3 bornes simultanées** : elastic (`‖δ‖₂+β‖δ‖₁ ≤ elastic_max`), L2 (`≤ l2_max`), L1 (`≤ l1_max`), pixels dans `[0,1]`.

**Q16. Piège d'implémentation des modèles de challenge concernant la normalisation ?**
Le `forward` des modèles serveur **ne normalise PAS** : il faut appliquer `mnist_normalize`/`cifar_normalize` avant, et propager le gradient à travers (raisonner en pixel space `[0,1]`).

**Q17. Différence de mesure L2 entre `compute_distances` d'entraînement et les bornes du challenge EAD ?**
Le code d'attaque utilise le **L2 au carré** (`Σδ²`, sans sqrt) ; les bornes challenge (`l2_max`, elastic) utilisent le **L2 = sqrt(Σδ²)**.

**Q18. Pourquoi l'assessment Skills impose L2 ≥ 1.5 ?**
Mesure **anti-triche** : empêche de soumettre l'image clean (ou une copie de la cible) sans perturbation réelle ; force un vrai adversarial.

---

## 🧪 Code réutilisable

### 🧪 A. EAD / ElasticNet (FISTA + binary search) — complet

```python
import torch, torch.nn as nn, torch.nn.functional as F

# --- Distances ---
def compute_distances(adv, orig, beta):
    l1 = torch.sum(torch.abs(adv - orig), dim=(1,2,3))
    l2 = torch.sum((adv - orig)**2, dim=(1,2,3))      # L2 AU CARRÉ
    elastic = l2 + beta * l1
    return l1, l2, elastic

# --- C&W adversarial loss (margin) ---
def compute_adversarial_loss(logits, labels_onehot, confidence, targeted=False):
    real  = torch.sum(labels_onehot * logits, dim=1)
    other = torch.max((1 - labels_onehot) * logits - labels_onehot * 10000, dim=1)[0]
    if targeted:
        return torch.clamp(other - real + confidence, min=0)
    return torch.clamp(real - other + confidence, min=0)

# --- Objectif lisse (L1 exclu → géré par le prox) ---
def compute_total_loss(adv, orig, labels_onehot, const, model, beta, confidence, targeted=False):
    logits = model(adv)
    adv_loss = compute_adversarial_loss(logits, labels_onehot, confidence, targeted)
    l1, l2, elastic = compute_distances(adv, orig, beta)
    total = const * adv_loss + l2
    return total, adv_loss, (l1, l2, elastic)

# --- FISTA building blocks ---
def compute_fista_momentum(iteration):
    return iteration / (iteration + 3.0)

def apply_shrinkage_thresholding(y, orig, threshold, clip_min=0.0, clip_max=1.0):
    diff = y - orig
    sp = torch.clamp(y - threshold, min=clip_min, max=clip_max)
    sn = torch.clamp(y + threshold, min=clip_min, max=clip_max)
    cp = (diff >  threshold).float()
    cz = (torch.abs(diff) <= threshold).float()
    cn = (diff < -threshold).float()
    return cp*sp + cz*orig + cn*sn

def fista_step(adv, y_mom, orig, labels_onehot, const, model, beta, lr, confidence,
               iteration, targeted=False, clip_min=0.0, clip_max=1.0):
    y_mom = y_mom.detach().requires_grad_(True)
    total, _, distances = compute_total_loss(y_mom, orig, labels_onehot, const, model, beta, confidence, targeted)
    total.sum().backward()
    y_new = y_mom - lr * y_mom.grad
    adv_new = apply_shrinkage_thresholding(y_new, orig, lr*beta, clip_min, clip_max)  # prox L1
    m = compute_fista_momentum(iteration)
    y_new_mom = adv_new + m * (adv_new - adv)
    return adv_new, y_new_mom, total.sum().item(), distances

# --- Success & binary search ---
def check_attack_success(adv, labels, model, targeted=False):
    with torch.no_grad():
        pred = model(adv).argmax(dim=1)
        return pred.eq(labels) if targeted else pred.ne(labels)

def update_binary_search_bounds(lb, ub, const, success):
    for i in range(len(success)):
        if success[i]:
            ub[i] = min(ub[i], const[i])
            if ub[i] < 1e10: const[i] = (lb[i]+ub[i])/2
        else:
            lb[i] = max(lb[i], const[i])
            const[i] = (lb[i]+ub[i])/2 if ub[i] < 1e10 else const[i]*10
    return lb, ub, const

# --- Driver ---
def ead_attack(model, original_images, attack_targets, num_classes=10, targeted=False,
               beta=0.01, confidence=0, lr=0.01, max_iterations=1000, binary_search_steps=5,
               initial_const=0.001, clip_min=0.0, clip_max=1.0, device="cpu"):
    B = len(original_images); original_images = original_images.clone()
    labels_onehot = torch.zeros(B, num_classes, device=device)
    labels_onehot.scatter_(1, attack_targets.unsqueeze(1), 1)
    lb = torch.zeros(B, device=device); ub = torch.ones(B, device=device)*1e10
    const = torch.ones(B, device=device)*initial_const
    best_adv = original_images.clone(); best_l2 = torch.ones(B, device=device)*1e10
    for _ in range(binary_search_steps):
        adv = original_images.clone().detach(); y_mom = adv.clone()
        for it in range(max_iterations):
            adv, y_mom, _, _ = fista_step(adv, y_mom, original_images, labels_onehot, const,
                                          model, beta, lr, confidence, it, targeted, clip_min, clip_max)
        succ = check_attack_success(adv, attack_targets, model, targeted)
        _, l2, _ = compute_distances(adv, original_images, beta)
        for i in range(B):
            if succ[i] and l2[i] < best_l2[i]:
                best_adv[i] = adv[i]; best_l2[i] = l2[i]
        lb, ub, const = update_binary_search_bounds(lb, ub, const, succ)
    return best_adv
# NB challenge : passer model = lambda x: server_model(mnist_normalize(x)) pour rester en pixel space [0,1].
```

### 🧪 B. JSMA (single-pixel + pairwise) — complet

```python
import numpy as np, torch, torch.nn.functional as F

# --- Jacobian ---
def compute_class_gradient(x, model, class_idx, wrt='logits'):
    xg = x.detach().requires_grad_(True)
    logits = model(xg)
    scalar = logits[0, class_idx] if wrt == 'logits' else F.softmax(logits, dim=1)[0, class_idx]
    scalar.backward()
    return xg.grad.detach().cpu().numpy().flatten().copy()

def compute_jacobian_matrix(x, model, num_classes=10, wrt='logits'):
    if x.shape[0] != 1: raise ValueError("batch size 1 requis")
    return np.asarray([compute_class_gradient(x, model, c, wrt) for c in range(num_classes)])

def extract_target_gradient(J, t): return J[t].copy()
def extract_other_gradients(J, t): return J.sum(axis=0) - J[t]
def apply_search_mask(g, ss): return g * ss

# --- Saliency ---
def score_increase_saliency(a, b): return a * np.abs(b) * ((a > 0) & (b < 0))
def score_decrease_saliency(a, b): return np.abs(a) * b * ((a < 0) & (b > 0))
def select_best_direction(inc, dec):
    ii, di = int(np.argmax(inc)), int(np.argmax(dec))
    si, sd = float(inc[ii]), float(dec[di])
    return (ii, si, True) if si > sd else (di, sd, False)

# --- Search space ---
def initialize_search_space(shape): return np.ones(int(np.prod(shape[1:])), dtype=bool)
def remove_saturated_pixels(ss, x, clip_min=0.0, clip_max=1.0, eps=1e-6):
    xf = x.detach().cpu().numpy().flatten()
    sat = (xf <= clip_min+eps) | (xf >= clip_max-eps)
    return ss & ~sat

# --- Perturbation & checks ---
def apply_single_pixel_perturbation(x, idx, theta, increase, clip_min=0.0, clip_max=1.0):
    sh = x.shape; xf = x.view(-1).clone()
    xf[idx] = torch.clamp(xf[idx] + (theta if increase else -theta), clip_min, clip_max)
    return xf.view(sh)
def check_target_reached(x, t, model):
    with torch.no_grad(): return int(model(x).argmax(dim=1).item()) == t
def compute_confidence(x, t, model):
    with torch.no_grad(): return float(F.softmax(model(x), dim=1)[0, t].item())

# --- Single-pixel driver ---
def jsma_single(model, x, target_class, num_classes=10, theta=0.25, gamma=0.15,
                max_iter=100, wrt='logits', clip_min=0.0, clip_max=1.0):
    x_adv = x.clone().detach(); ss = initialize_search_space(x.shape)
    max_pixels = int(gamma * int(np.prod(x.shape[1:]))); n = 0
    for _ in range(max_iter):
        if check_target_reached(x_adv, target_class, model): break
        if n >= max_pixels: break
        J = compute_jacobian_matrix(x_adv, model, num_classes, wrt)
        a = apply_search_mask(extract_target_gradient(J, target_class), ss)
        b = apply_search_mask(extract_other_gradients(J, target_class), ss)
        idx, sal, inc = select_best_direction(score_increase_saliency(a, b),
                                              score_decrease_saliency(a, b))
        if sal <= 0: break
        x_adv = apply_single_pixel_perturbation(x_adv, idx, theta, inc, clip_min, clip_max)
        ss[idx] = False; ss = remove_saturated_pixels(ss, x_adv, clip_min, clip_max); n += 1
    return x_adv, n

# --- Pairwise ---
def prune_candidates(a, b, ss, top_k):
    am, bm = a*ss, b*ss; valid = np.where(ss)[0]
    if valid.size < 2 or top_k is None or valid.size <= top_k: return valid
    pre = np.abs(am[valid]) * np.abs(bm[valid])
    return valid[np.argsort(-pre)[:top_k]]

def evaluate_pairs(a, b, valid, direction):
    bp, bq, bs = -1, -1, 0.0
    for i in range(valid.size):
        p = valid[i]
        for j in range(i+1, valid.size):
            q = valid[j]; apq = a[p]+a[q]; bpq = b[p]+b[q]
            if direction == 'increase':
                if apq <= 0 or bpq >= 0: continue
                s = apq * abs(bpq)
            else:
                if apq >= 0 or bpq <= 0: continue
                s = abs(apq) * bpq
            if s > bs: bs, bp, bq = float(s), int(p), int(q)
    return bp, bq, bs

def compute_pairwise_saliency(a, b, ss, direction='increase', top_k=None):
    valid = prune_candidates(a, b, ss, top_k)
    if valid.size < 2: return -1, -1, 0.0
    bp, bq, bs = evaluate_pairs(a, b, valid, direction)
    return (-1, -1, 0.0) if bp == -1 else (bp, bq, bs)

def apply_pair_perturbation(x, p, q, theta, increase, clip_min=0.0, clip_max=1.0):
    sh = x.shape; xf = x.view(-1).clone(); step = theta if increase else -theta
    xf[p] = torch.clamp(xf[p]+step, clip_min, clip_max)
    xf[q] = torch.clamp(xf[q]+step, clip_min, clip_max)
    return xf.view(sh)

def jsma_pairwise(model, x, target_class, num_classes=10, theta=1.0, gamma=0.15,
                  max_iter=90, top_k=128, wrt='logits', clip_min=0.0, clip_max=1.0):
    x_adv = x.clone().detach(); ss = initialize_search_space(x.shape)
    max_pixels = int(gamma * int(np.prod(x.shape[1:]))); n = 0
    for _ in range(max_iter):
        if check_target_reached(x_adv, target_class, model): break
        if n >= max_pixels: break
        J = compute_jacobian_matrix(x_adv, model, num_classes, wrt)
        a = extract_target_gradient(J, target_class); b = extract_other_gradients(J, target_class)
        pi, qi, si = compute_pairwise_saliency(a, b, ss, 'increase', top_k)
        pd, qd, sd = compute_pairwise_saliency(a, b, ss, 'decrease', top_k)
        if max(si, sd) <= 0: break
        if si >= sd: p, q, inc = pi, qi, True
        else:        p, q, inc = pd, qd, False
        if p == -1 or q == -1: break
        x_adv = apply_pair_perturbation(x_adv, p, q, theta, inc, clip_min, clip_max)
        ss[p] = False; ss[q] = False
        ss = remove_saturated_pixels(ss, x_adv, clip_min, clip_max); n += 2
    return x_adv, n
# NB challenge : model = lambda x: server_model(mnist_normalize(x)) ; wrt sur la sortie réseau.
```

### 🧪 C. Helpers API challenges (I/O images)

```python
import io, base64, numpy as np
from PIL import Image

def x01_from_b64_png(b64):                     # MNIST 28x28 mono
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("L")
    if img.size != (28, 28): raise ValueError("Expected 28x28 PNG")
    return np.clip(np.asarray(img, dtype=np.float32)/255.0, 0.0, 1.0)

def b64_png_from_x01(x2d):                      # round-trip 8-bit
    x255 = np.clip((x2d*255.0).round(), 0, 255).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(x255, mode="L").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def count_modified_pixels(a, b, threshold=1e-6):    # L0 (JSMA)
    return int(np.sum(np.abs(a - b) > threshold))

MNIST_MEAN, MNIST_STD = 0.1307, 0.3081
def mnist_normalize(x01): return (x01 - MNIST_MEAN) / MNIST_STD
# CIFAR (Skills Assessment) : mean (0.4914,0.4822,0.4465), std (0.2470,0.2435,0.2616)
```
