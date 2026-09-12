# AI Privacy (module 335) — Fiche de révision

Module **DÉFENSIF** : attaques privacy sur ML (rappels) + défenses par **Differential Privacy** (DP-SGD, PATE).

---

## En bref

- La **privacy leakage** en ML vient de l'**overfitting/mémorisation** : un modèle est plus confiant sur ses données d'entraînement (members) que sur des données jamais vues (non-members).
- Famille d'attaques : **Membership Inference (MIA)**, **Model Inversion**, **Attribute Inference**, **Training Data Extraction**, **Model Extraction**. MIA = brique de base (moins d'infos requises, sert d'audit de privacy).
- **Shadow Model Attack** (Shokri et al. 2017) : entraîner des shadow models dont on connaît la membership, collecter leurs prédictions, entraîner un **attack model** binaire, l'appliquer au target (black-box).
- **Differential Privacy (DP)** : garantie formelle worst-case. (ε,δ)-DP borne combien un seul enregistrement peut changer la distribution des sorties. ε petit = privacy forte ; δ = proba d'échec (< 1/n).
- **Mécanisme Gaussien** : σ = Δf·√(2·ln(1.25/δ))/ε. **Mécanisme Laplacien** : Lap(scale=Δf/ε).
- **DP-SGD** : (1) **per-sample gradient clipping** à la norme L2 = C (`max_grad_norm`), (2) ajout de bruit **Gaussien** σ = C × noise_multiplier, (3) **privacy accounting** (RDP/moments accountant via Opacus).
- Opacus : `PrivacyEngine.make_private_with_epsilon()` calcule le noise_multiplier pour un ε cible. Incompatible avec **BatchNorm** (remplacer par **GroupNorm/LayerNorm/InstanceNorm**).
- **PATE** : n **teachers** sur partitions **disjointes** de données privées → votent sur données **publiques** → agrégation bruitée (**noisy argmax** + Laplace) → **student** entraîné sur pseudo-labels. Sensibilité du vote = 2, donc ε₀ = 2/noise_scale.
- Tradeoff **privacy-utility** : ε plus petit = plus de bruit = moins de MIA advantage mais accuracy plus basse. DP-SGD borne l'influence individuelle, pas les patterns agrégés.
- Métrique d'attaque clé : **MIA advantage = attack_accuracy − 0.5** (0 = aléatoire, >0.15 = forte vulnérabilité).
- 3 challenges : **DP-SGD** (SVHN), **PATE** (EMNIST Letters), **Skills Assessment** (Fashion-MNIST). Tous soumettent un `.safetensors`.

---

## 1. Rappels — Attaques Privacy sur ML

### 1.1 Membership Inference Attack (MIA)

**Question** : est-ce qu'un échantillon donné a été utilisé pour entraîner le modèle ? Réponse binaire (member / non-member).

**Pourquoi ça marche** : distinction **memorization vs generalization**. L'overfitting crée des différences comportementales détectables. Deux signaux exploités :
- **prediction confidence** : members reçoivent des prédictions plus confiantes (ex. member `[0.05, 0.95]` vs non-member `[0.20, 0.80]`).
- **prediction correctness** : le modèle est plus précis sur ses données d'entraînement.

**Objectif attaquant** : classifieur binaire avec accuracy > 50% (random).

**Facteurs de vulnérabilité** :
| Facteur | Effet |
|---|---|
| Complexité/capacité du modèle | + de paramètres = + de mémorisation = + vulnérable |
| Taille du dataset d'entraînement | Petit dataset = + vulnérable (chaque exemple a + d'influence) |
| Durée d'entraînement / régularisation | + d'epochs sans régularisation = + d'overfitting. Dropout(0.5), weight decay, early stopping réduisent |
| Nombre de classes de sortie | + de classes = signal de membership + riche (ImageNet 1000 classes > binaire) |
| Hétérogénéité des données | Outliers/samples près des frontières + mémorisés (80% sur outliers vs 55% sur typiques) |

**🎯 Exam** : Le paramètre qui maximise l'overfitting gap dans la config target du module = **dropout à 0.0** + entraînement fixe **100 epochs sans early stopping**.

### 1.2 Autres attaques (à connaître)

- **Model Inversion** : reconstruire des features de données d'entraînement à partir des sorties du modèle.
- **Attribute Inference** : déduire des attributs sensibles non directement prédits (ex. modèle prédit revenu → révèle niveau d'éducation).
- **Training Data Extraction** : récupérer des exemples verbatim (LLM qui mémorisent des séquences).
- **Model Extraction / Model theft** : entraîner un modèle surrogate depuis les requêtes API (non couvert par DP-SGD).

### 1.3 Frameworks industriels

- **OWASP ML Security Top 10** (draft v0.3) : MIA = **ML04:2023** ; Model Inversion = **ML03:2023** ; Model theft = **ML05:2023**. MIA : exploitability 4/5, impact 4/5. Défenses : DP + régularisation.
- **OWASP Top 10 for LLM Applications** (2025) : **LLM02: Sensitive Information Disclosure** (fuite de données d'entraînement) ; **LLM04: Data and Model Poisoning**.
- **Google SAIF** : MIA sous **Sensitive Data Disclosure** et **Inferred Sensitive Data**. Responsabilité partagée creators (privacy-preserving training) / consumers (filtrer sorties, monitorer requêtes).

**🎯 Exam** : MIA dans OWASP ML Top 10 = **ML04:2023**. Model inversion = ML03, Model theft = ML05.

### 1.4 Shadow Model Attack (Shokri et al. 2017)

**Principe** : on ne connaît pas le training set du target → on entraîne des **shadow models** dont on contrôle la membership pour générer des données labellisées pour l'**attack model**.

**Threat model** : **black-box** (soumettre inputs, observer softmax outputs, pas d'accès aux paramètres). L'attaquant connaît la distribution des données d'entraînement. Requêtes indétectables (identiques à des requêtes légitimes).

**Similarity assumption** (3 aspects à approximer) : architecture, procédure d'entraînement, distribution des données.

**Attack model input** : probabilités softmax concaténées avec **one-hot true label** → format `[prob_class_0, prob_class_1, label_0, label_1]` (4D pour binaire). Permet d'apprendre des patterns class-specific.

**Alternatives (moins complexes)** :
- **Metric-based** : seuil sur la confidence (ex. >0.9 → member). Aucun entraînement.
- **Loss-based** : seuil sur la cross-entropy loss (members = loss plus basse). Nécessite le true label.
- **Likelihood ratio** : approche bayésienne, ratio de probabilités entre distributions train/reference. Efficacité statistique optimale.

**Configuration du module (Adult Census)** :

```python
TARGET_MODEL_CONFIG = {
    "hidden_layers": [256, 128],
    "dropout": 0.0,  # No dropout to maximize overfitting
    "epochs": 100,
    "batch_size": 32,
    "learning_rate": 0.001,
}
SHADOW_MODEL_CONFIG = {
    "num_shadow_models": 5,
    "hidden_layers": [128, 64],
    "dropout": 0.3,
    "epochs": 100,
    "batch_size": 64,
    "learning_rate": 0.001,
    "early_stopping_patience": 10,
    "shadow_data_size": 0.5,
}
ATTACK_MODEL_CONFIG = {
    "hidden_layers": [64, 32],
    "dropout": 0.2,
    "epochs": 100,
    "batch_size": 128,
    "learning_rate": 0.001,
    "early_stopping_patience": 15,
}
```

**Data split** (`load_adult_census`, 48 842 samples) : Target Training 24 421 (members) | Holdout 24 421 = Shadow Training 12 210 + Attack Eval 12 210 (non-members).

**Résultats typiques** : Target overfitting gap ~11% (train 93.6% / test 82.5%). Attack accuracy ~69% (advantage ~0.19), precision 68.99%, recall 97.58%, F1 0.808, **AUC 0.5675**. Confidence gap members/non-members ~0.0075.

- **Attack advantage** = attack_accuracy − 0.5. Guides : >0.15 forte vulnérabilité ; 0.05–0.15 modérée ; <0.05 ≈ aléatoire.
- AUC (0.57) << accuracy (69%) car AUC mesure sur tous les seuils, accuracy sur seuil fixe 0.5 (favorable au dataset déséquilibré 2:1).

**Note** : sur les shadow models (régularisés), l'attack accuracy ≈ 50-51% (signal faible) ; sur le target (overfit), elle grimpe à 65-66%. L'éval shadow **sous-estime** la perf sur le target.

---

## 2. Differential Privacy — Fondamentaux

### 2.1 Définition formelle

Un algorithme randomisé **M** satisfait la **(ε, δ)-differential privacy** si pour deux datasets **D** et **D′** qui diffèrent d'exactement **un enregistrement**, et pour tout sous-ensemble de sorties **S** :

```
P[M(D) ∈ S] ≤ e^ε · P[M(D′) ∈ S] + δ
```

- **e^ε** : borne multiplicative. Si ε=1, les sorties peuvent être au plus e≈2.7 fois plus probables avec vos données que sans.
- **δ** : proba d'échec complet de la garantie. Pour CIFAR-10 (50 000 samples), δ=10⁻⁵ → garantie tenue avec proba 0.99999.
- **ε-DP pur** = cas où δ=0.

**Interprétation de ε** (plus petit = plus fort) :
- ε=1 : très forte (quasi-indifférence à une personne).
- ε=3 : forte (influence individuelle fortement supprimée).
- ε=10 : modeste (le modèle peut révéler des patterns agrégés). Range pratique 1–10. Apple utilise ε≈2–8. Benchmarks recherche ε=8 ou 10 comme "reasonable privacy".

**Contrainte sur δ** : doit satisfaire **δ < 1/n** (n = taille du training set). CIFAR-10 : δ=10⁻⁵ = 1/100000 < 1/50000. ✓

**🎯 Exam** : Formule (ε,δ)-DP = `P[M(D)∈S] ≤ e^ε · P[M(D')∈S] + δ`. δ doit être < 1/n.

### 2.2 Sensitivity

**Sensitivity Δf** = changement maximal de la sortie de f quand on ajoute/retire un enregistrement.

- En SGD standard, sensitivity ≈ **infinie** (un outlier peut produire un gradient énorme).
- DP-SGD borne la sensitivity par **clipping** : chaque per-sample gradient est scalé pour que sa **norme L2** ≤ `max_grad_norm` (C). Ex. gradient de norme 5.2, C=1.0 → scalé d'un facteur 5.2, norme finale = 1.0.
- Après clipping, la sensitivity de la somme des gradients = **exactement max_grad_norm** (C).

### 2.3 Mécanisme Gaussien

Pour une fonction f de sensitivity L2 = Δf, ajouter du bruit Gaussien d'écart-type :

```
σ = Δf · √(2·ln(1.25/δ)) / ε
```

atteint la (ε, δ)-DP.

En DP-SGD, on ajoute du bruit Gaussien zero-mean à la somme des gradients clippés avant moyennage. L'écart-type utilisé en pratique :

```
σ = max_grad_norm × noise_multiplier
```

où le **noise_multiplier** dépend de ε cible, δ, et du nombre de steps (calculé par le privacy accountant, pas seulement la forme close du mécanisme Gaussien).

### 2.4 Mécanisme Laplacien

Distribution Laplacienne centrée en 0, scale b, PDF :

```
f(x | b) = (1/2b) · exp(−|x|/b)
```

Un tirage Lap(b) a un écart-type **b·√2** (ex. Lap(20) → σ = 20√2 ≈ 28.3).

**ε-DP pur** : Lap(scale = Δf/ε). Utilisé dans **PATE** (voir §4).

### 2.5 Composition de la privacy

Chaque étape/requête consomme du budget. La privacy **se compose** :
- **Naive composition** : ε total = k · ε₀ (linéaire, pessimiste). Ex. 5000 queries × 0.10 = ε=500.
- **Advanced composition theorem** : borne ∝ √k · ε₀ (sous-linéaire).
- **Rényi Differential Privacy (RDP)** / **Moments Accountant** : suivi encore plus serré (utilisé par Opacus). Suit le log de la fonction génératrice des moments de la variable de privacy loss.

**Théorique vs empirique** :
- La garantie DP est un **worst-case upper bound** (tout attaquant, y compris futur, sample worst-case, adversaire optimal).
- Le MIA empirique est un **average-case lower bound** (attaque spécifique). D'où MIA empirique << borne théorique.

---

## 3. DP-SGD (défense principale)

### 3.1 Mécanisme (3 étapes)

DP-SGD corrompt le SGD standard ("controlled amnesia") :
1. **Gradient clipping** : borne l'influence de chaque sample (per-sample gradient, norme L2 ≤ C).
2. **Noise addition** : bruit Gaussien σ = C × noise_multiplier sur la somme des gradients clippés.
3. **Privacy composition** : suivi du budget cumulé (RDP/moments accountant).

**Ordre exact** : per-sample gradients → clip chacun à C → somme → ajout bruit Gaussien → moyenne → step.

### 3.2 Per-sample gradients & contraintes d'architecture

- SGD standard = 1 gradient moyen par batch. DP-SGD = **256 gradient tensors** par paramètre pour un batch de 256, chacun clippé séparément. Coûteux (2-5x plus lent, mémoire ∝ batch size).
- Opacus calcule les per-sample gradients via des **gradient hooks**.
- **BatchNorm INCOMPATIBLE** : calcule des stats sur la dimension batch, couplant les gradients entre samples → viole l'indépendance.
- **Compatibles** : **GroupNorm**, **LayerNorm** (normalisent dans chaque sample), **InstanceNorm**. Remplacer BatchNorm par GroupNorm (groups = nb de channels).
- `ModuleValidator.fix()` corrige automatiquement les incompatibilités courantes (substitue GroupNorm à BatchNorm).

**🎯 Exam** : Layer incompatible avec DP-SGD/Opacus = **BatchNorm**. Alternatives = GroupNorm, LayerNorm, InstanceNorm.

### 3.3 Privacy Amplification by Subsampling

- Opacus utilise le **Poisson subsampling** : chaque sample inclus indépendamment avec proba **q = batch_size / dataset_size**.
- Ex. CIFAR-10 : q = 256/50000 = **0.00512**. Ce faible taux amplifie fortement la privacy (l'attaquant ne sait pas quels samples étaient dans un batch).
- Batches de taille variable (moyenne 256, parfois 240/270), un même sample peut apparaître plusieurs fois ou zéro dans un epoch.
- Batches plus gros = q plus haut = moins d'amplification, mais moins de steps par epoch. Batch modéré (128-512) marche bien.

### 3.4 Hyperparamètres (tuning)

| Hyperparamètre | Rôle / guidance |
|---|---|
| `max_grad_norm` (C) | Clipping. Trop petit (0.1) = starve le signal ; trop grand (10) = gâche du budget. Calibrer : 75e percentile des gradient norms sur quelques epochs sans privacy. CNN CIFAR-10 : norms 0.5–5.0 → **C=1.0** raisonnable. |
| `noise_multiplier` | Calculé par l'accountant pour atteindre ε cible. Plus ε petit = plus grand. **ε=10 → ~1.2 ; ε=3 → ~3.8** (≈3x plus de bruit). |
| batch size | Affecte l'amplification. Petit = + d'amplification mais + de steps. <64 nuit à la convergence. |
| learning rate | Match ou légèrement < baseline. DP-LR=0.1 dans le module. |
| epochs | + d'epochs = + de budget consommé = + de bruit/step. |
| `DELTA` (δ) | < 1/n. CIFAR-10 : **1e-5**. |

### 3.5 Config & code de référence (CIFAR-10)

```python
RANDOM_SEED = 1337
BATCH_SIZE = 256
BASELINE_EPOCHS = 20
BASELINE_LR = 0.1
DP_EPOCHS = 20
DP_LR = 0.1
MAX_GRAD_NORM = 1.0
DELTA = 1e-5
```

Imports Opacus :

```python
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator
```

Entraînement DP-SGD (ε=10) :

```python
TARGET_EPSILON_10 = 10.0
_, _, train_loader_dp, test_loader_dp = get_cifar10_loaders(batch_size=BATCH_SIZE, download=False)

dp_model_10 = CIFAR10CNN().to(device)
dp_model_10 = ModuleValidator.fix(dp_model_10)          # corrige les layers incompatibles
optimizer_dp = optim.SGD(dp_model_10.parameters(), lr=DP_LR, momentum=0.9)

privacy_engine = PrivacyEngine(accountant="rdp")
dp_model_10, optimizer_dp, train_loader_dp = privacy_engine.make_private_with_epsilon(
    module=dp_model_10,
    optimizer=optimizer_dp,
    data_loader=train_loader_dp,
    target_epsilon=TARGET_EPSILON_10,
    target_delta=DELTA,
    epochs=DP_EPOCHS,
    max_grad_norm=MAX_GRAD_NORM,
)

dp_model_10, final_epsilon_10 = train_dp_sgd(
    dp_model_10, train_loader_dp, privacy_engine, optimizer_dp, device
)
```

Sauvegarde (⚠️ accès `._module` car Opacus wrappe le modèle) :

```python
torch.save(dp_model_10._module.state_dict(), "output/dp_model_eps10.pth")
from safetensors.torch import save_file
save_file(dp_model_10._module.state_dict(), "models/dp_model.safetensors")
```

**Note** : chaque modèle DP a besoin de son **propre loader** (Opacus wrappe le loader pour tracker les accès). Ne pas partager les loaders → corromprait le comptage.

### 3.6 Résultats & interprétation

| Model | Test Accuracy | MIA Advantage | Overfitting Gap | noise_mult |
|-------|--------------|--------------|----------------|-----------|
| Baseline | 67% | 0.019 | 10% | — (ε=∞) |
| DP ε=10 | 58% | 0.008 | 3% | ~1.2 |
| DP ε=3 | 53% | 0.004 | 1% | ~3.8 |

- Baseline→ε=10 : −9 pts accuracy, MIA advantage −57%. ε=10→ε=3 : −5 pts accuracy, advantage divisé encore par ~2.
- Le bruit empêche de fitter les exemples individuels → overfitting gap chute (10%→1%).
- **Diminishing returns** : coût marginal de privacy ~constant, bénéfice marginal décroissant.
- Pendant l'entraînement ε=10, ~60-70% des per-sample gradients dépassent C et sont clippés.

**Limites de DP-SGD** :
- Overhead computationnel 2-5x.
- Utility loss à ε<1 peut dépasser 20-30 pts.
- **Protège** : influence individuelle des samples → contre MIA. **Ne protège PAS** : patterns agrégés (âge moyen, features communes), model extraction, adversarial examples.
- Alternatives : **PATE**, **Local DP** (bruit à la collecte), **Federated Learning** (données restent sur device).

---

## 4. PATE (Private Aggregation of Teacher Ensembles)

### 4.1 Principe

Privacy par **séparation architecturale** (pas de perturbation training-time). Le modèle déployé (**student**) n'accède **jamais** aux données sensibles.

**2 phases** :
1. Partitionner données privées en **n subsets DISJOINTS** → entraîner 1 **teacher** par partition.
2. Les teachers **votent** sur des données **publiques non labellisées** → agrégation bruitée → **pseudo-labels** → entraîner le **student** dessus.

**Formule d'agrégation (noisy argmax)** :

```
ŷ = arg max_j ( n_j(x) + Lap(1/ε) )          # forme per-query
ŷ = arg max_j ( n_j(x) + Lap(scale) )        # forme générale
```

- `n_j(x)` = nombre de teachers votant pour la classe j sur l'input x.
- Bruit Laplacien indépendant ajouté à chaque compte de votes avant argmax.

**Pourquoi c'est privé** : pour deux datasets voisins (1 sample de différence), seul **1 teacher** change son vote (les 249 autres inchangés). Changer 1 vote modifie l'histogramme d'au plus **+1 pour une classe, −1 pour une autre** → **sensitivity = 2**.

Garantie 1 requête :
```
ε₀ = 2 / noise_scale
```

Avec noise_scale=20 → **ε₀ = 0.10**.

**🎯 Exam** : Sensitivity du vote PATE = **2** (un vote passe d'une classe à une autre). Donc ε₀ = 2/noise_scale.

### 4.2 Information Bottleneck

Le student ne reçoit que des labels de classe bruités (quelques bits/query). Exemple MNIST : 48 000 images privées × 784 features (float32) ≈ **150 MB** → via 5 000 queries, le student reçoit 5 000 labels (int 0-9, ~4 bits chacun) ≈ **2.5 KB**. **Compression ratio > 60 000:1**. Recovery impossible (limite information-théorique).

### 4.3 Composition du budget

- Naive : 5000 × 0.10 = ε=500 (négligeable).
- Advanced composition (∝ √k) → **ε ≈ 8.81** pour 5000 queries à noise_scale=20.
- **Moments accountant** : bornes encore plus serrées.
- Le student satisfait (ε,δ)-DP par rapport aux données sensibles. **Inférence illimitée sans coût privacy** additionnel après entraînement.

### 4.4 Configuration & code de référence (MNIST)

```python
RANDOM_SEED = 1337
DATASET_CONFIG = {"name": "mnist", "num_classes": 10, "num_features": 784}

TEACHER_CONFIG = {
    "num_teachers": 250,       # config du papier original
    "hidden_layers": [128, 64],
    "dropout": 0.2,
    "epochs": 30,
    "batch_size": 64,
    "learning_rate": 0.001,
}
AGGREGATION_CONFIG = {
    "noise_scale": 20.0,       # ε₀ = 2/20 = 0.10
    "num_student_queries": 5000,
}
STUDENT_CONFIG = {
    "hidden_layers": [128, 64],
    "dropout": 0.2,
    "epochs": 30,
    "batch_size": 64,
    "learning_rate": 0.001,
}
```

- 250 teachers, 48 000 samples privés → **~192 samples/teacher**. Teacher accuracy individuelle 74-82%. Clean ensemble ~88%, noisy labels ~87% (gap < 1 pt).
- ε₀ = 2/20 = 0.10 ; total ε ≈ 8.81.

**Data split** (60 000 train MNIST) : Private 80% (~48 000, teachers) | Public 20% (~12 000, student queries) | Holdout = test set standard (10 000, éval). `stratify=y_train`. StandardScaler fit sur **private uniquement**.

**Partitions disjointes** :

```python
np.random.seed(RANDOM_SEED)
indices = np.random.permutation(len(X_private_norm))
partition_size = len(X_private_norm) // num_teachers
teacher_partitions = []
for i in range(num_teachers):
    start_idx = i * partition_size
    if i == num_teachers - 1:
        partition_indices = indices[start_idx:]           # dernier absorbe le reste
    else:
        partition_indices = indices[start_idx:start_idx + partition_size]
    teacher_partitions.append(partition_indices)
```

Shuffle avant partition = évite le clustering. Disjoint = chaque sample n'influence qu'**un** teacher (borne la privacy).

**Voting** :

```python
def get_teacher_votes(teachers, X, device):
    num_samples = X.shape[0]
    num_classes = DATASET_CONFIG['num_classes']
    votes = np.zeros((num_samples, num_classes), dtype=np.int32)
    for teacher in teachers:
        preds = get_model_predictions(teacher, X, device)
        predictions = np.argmax(preds, axis=1)
        for i, pred in enumerate(predictions):
            votes[i, pred] += 1
    return votes
```

**Noisy aggregation** :

```python
def noisy_argmax(votes, noise_scale):
    """Add Laplacian noise to votes and return the winning class."""
    noise = np.random.laplace(loc=0.0, scale=noise_scale, size=votes.shape)
    noisy_votes = votes.astype(np.float64) + noise
    return np.argmax(noisy_votes, axis=1)
```

**Budget (advanced composition)** :

```python
def compute_privacy_budget(num_queries, noise_scale, delta=1e-5):
    per_query_eps = 2.0 / noise_scale
    epsilon_sq_sum = num_queries * (per_query_eps ** 2)
    total_epsilon = np.sqrt(2 * epsilon_sq_sum * np.log(1 / delta))
    total_epsilon += num_queries * per_query_eps * (np.exp(per_query_eps) - 1)
    return total_epsilon, per_query_eps
```
- 1er terme `√(2·k·ε₀²·ln(1/δ))` = scaling dominant √k. 2e terme = correction ε₀ fini.

**Student training** : MLP `[128, 64]` sur `(X_query, student_labels)`, cross-entropy standard, hard pseudo-labels (pas de soft probabilities, qui fuiteraient + d'info). Student ~88% accuracy. Sauvegarde : `save_file(student_model.state_dict(), "models/pate_student.safetensors")`.

### 4.5 Consensus & Confident Aggregation

Catégories (250 teachers) :
- **High consensus** : ≥200 votes (80%) → ~98% accuracy, flip rate ≈ 0.
- **Medium** : 150-199 votes (60-80%) → ~85% accuracy.
- **Low** : <150 votes → ~65% accuracy (digits ambigus 3vs8, 4vs9).

**Confident aggregation** : ne labelliser QUE les samples ≥ threshold (sentinel −1 pour rejets, filtrés avant training student). Les queries rejetées **ne consomment aucun budget** (aucune info libérée).

```python
def confident_aggregation(votes, noise_scale, threshold):
    max_votes = votes.max(axis=1)
    confident_mask = max_votes >= threshold
    labels = np.full(len(votes), -1, dtype=np.int64)
    if confident_mask.sum() > 0:
        confident_votes = votes[confident_mask]
        noise = np.random.laplace(loc=0.0, scale=noise_scale, size=confident_votes.shape)
        labels[confident_mask] = np.argmax(confident_votes.astype(np.float64) + noise, axis=1)
    return labels, confident_mask
```

Budget avec rejets :

```python
def compute_confident_privacy_budget(num_queries, noise_scale, acceptance_rate, delta=1e-5):
    per_query_eps = 2.0 / noise_scale
    effective_queries = int(num_queries * acceptance_rate)
    epsilon_sq_sum = effective_queries * (per_query_eps ** 2)
    total_epsilon = np.sqrt(2 * epsilon_sq_sum * np.log(1 / delta))
    total_epsilon += effective_queries * per_query_eps * (np.exp(per_query_eps) - 1)
    return total_epsilon, per_query_eps, effective_queries
```

Threshold=200 accepte ~85% de 5000 → 4250 labels effectifs, ε diminue proportionnellement.

### 4.6 Sweep noise_scale (privacy-utility)

| noise_scale | per-ε (2/ns) | label accuracy |
|---|---|---|
| 5 | 0.40 | ~95% |
| 10 | 0.20 | ~92% |
| 20 (défaut) | 0.10 | ~87% (total ε≈8.81) |
| 40 | 0.05 | ~78% |
| 80 | 0.025 | ~65% |

Range pratique 10-40 ; scale=20 au "coude" de la courbe. Query budget : 1000→ε≈3.9 ; 2500→ε≈6.2 ; 5000→ε≈8.81 ; 10000→ε≈12.5 (sous-linéaire : doubler les queries ≈ +40% d'ε).

### 4.7 PATE vs DP-SGD

| | PATE | DP-SGD |
|---|---|---|
| Mécanisme | Séparation architecturale (noisy voting) | Bruit training-time (noisy gradients) |
| Données publiques | **Requises** (proxy de la distribution privée) | Non requises |
| Inférence post-déploiement | Illimitée, gratuite | Modèle direct, pas de coût par query |
| Coût | Entraîner n teachers | Per-sample gradient clipping, tuning |
| Meilleur si | Public data dispo + inférence haut volume | Pas de proxy public / modèles complexes sur données privées |

**Limites PATE** : besoin de public data même distribution (médical/financier rare) ; class imbalance → consensus disparate → student sous-performe sur classes minoritaires ; **partitions disjointes** requièrent déduplication (un individu = 1 seul teacher).

### 4.8 Évaluation privacy PATE (MIA)

Attack = **confidence threshold** (max softmax), recherche du meilleur seuil sur percentiles, datasets équilibrés :

```python
def compute_mia_advantage(model, X_members, y_members, X_nonmembers, y_nonmembers, device):
    member_probs = get_model_predictions(model, X_members, device)
    member_confidence = np.max(member_probs, axis=1)
    nonmember_probs = get_model_predictions(model, X_nonmembers, device)
    nonmember_confidence = np.max(nonmember_probs, axis=1)

    n_samples = min(len(member_confidence), len(nonmember_confidence))
    member_conf_balanced = member_confidence[:n_samples]
    nonmember_conf_balanced = nonmember_confidence[:n_samples]

    all_confidence = np.concatenate([member_conf_balanced, nonmember_conf_balanced])
    all_labels = np.concatenate([np.ones(n_samples), np.zeros(n_samples)])

    thresholds = np.percentile(all_confidence, np.linspace(0, 100, 1000))
    best_accuracy = 0.0
    for threshold in thresholds:
        predictions = (all_confidence >= threshold).astype(int)
        accuracy = np.mean(predictions == all_labels)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = threshold

    attack_advantage = best_accuracy - 0.5
    return best_accuracy, attack_advantage, best_threshold
```

Résultats : baseline (dropout 0, 50 epochs, 10 000 samples) leaks (advantage > 5% threshold). **PATE student vs private data : accuracy ~50%, advantage ~0** (indistinguable de l'aléatoire — le student n'a jamais vu les données privées). PATE student vs query data : advantage mesurable (attendu, query data = public, valide la méthodo).

**🎯 Exam** : PATE résiste au MIA par **design architectural** (information bottleneck), pas par bruit à l'inférence. Le student answers deterministically sans coût privacy.

---

## 5. Challenges & Skills Assessment (Questions section — NON RÉSOLUS)

> Les 3 questions demandent le **flag `HTB{...}`** obtenu en résolvant le challenge. `user_answer` **vide** dans la source (challenges Docker interactifs non résolus). Méthode de résolution détaillée ci-dessous — le flag n'est PAS déductible de la fiche, il faut entraîner et soumettre le modèle à l'instance.

### 5.1 DP-SGD Challenge (SVHN) — id 3596

**Énoncé** : « What is the flag you get for successfully solving the challenge? »

**Objectif** : classifieur privacy-preserving sur **SVHN** avec DP-SGD.

| Metric | Requirement |
|---|---|
| `accuracy` | **≥ 55%** |
| `mia_advantage` | **≤ 5%** |

**Architecture EXACTE requise** (BatchNorm exclu pour Opacus) :

```python
class SVHNCNN(nn.Module):
    def __init__(self):
        super(SVHNCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 4 * 4, 64)
        self.fc2 = nn.Linear(64, 10)
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(-1, 64 * 4 * 4)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x
```

**Preprocessing** : `SVHN_MEAN=(0.4377,0.4438,0.4728)`, `SVHN_STD=(0.1980,0.2010,0.1970)`, `ToTensor + Normalize`. Datasets `SVHN split='train'/'test'`.

**Méthode** :
1. Charger SVHN avec la normalisation exacte.
2. Entraîner `SVHNCNN` avec Opacus : `ModuleValidator.fix()`, `PrivacyEngine(accountant="rdp")`, `make_private_with_epsilon(target_epsilon≈8-10, target_delta=1e-5, epochs, max_grad_norm=1.0)`. Viser ε qui garde accuracy ≥55% tout en poussant MIA advantage ≤5% (ε≈10 est un bon point de départ ; baisser si advantage trop haut).
3. Sauvegarder `save_file(model._module.state_dict(), "dp_model.safetensors")`.
4. `POST /validate -F "model=@dp_model.safetensors"` → si `passed:true`, lire `flag`.

**Endpoints** : `GET /health` → `{"status":"ok","data_loaded":true}` ; `POST /validate` (multipart `model`) ; `GET /` → service info.

### 5.2 PATE Challenge (EMNIST Letters) — id 3597

**Énoncé** : « What is the flag you get for successfully solving the challenge? »

**Objectif** : classifieur de lettres manuscrites (26 classes A-Z) via **PATE**.

| Metric | Requirement |
|---|---|
| `accuracy` | **≥ 80%** |
| `mia_advantage` | **≤ 3%** |

**Architecture EXACTE (student)** :

```python
class MLP(nn.Module):
    def __init__(self, input_size=784, hidden_layers=None, num_classes=26, dropout=0.2):
        super(MLP, self).__init__()
        if hidden_layers is None:
            hidden_layers = [256, 128]
        self.layers = nn.ModuleList()
        self.dropouts = nn.ModuleList()
        prev_size = input_size
        for hidden_size in hidden_layers:
            self.layers.append(nn.Linear(prev_size, hidden_size))
            self.dropouts.append(nn.Dropout(dropout))
            prev_size = hidden_size
        self.output = nn.Linear(prev_size, num_classes)
    def forward(self, x):
        for layer, dropout in zip(self.layers, self.dropouts):
            x = F.relu(layer(x))
            x = dropout(x)
        return self.output(x)
```

**Preprocessing** : EMNIST `split='letters'`, reshape(-1,784)/255.0, `y = targets − 1` (labels 1-26 → 0-25), StandardScaler fit sur train.

**Méthode** :
1. Split private/public/holdout. Partitionner private en n teachers disjoints (ex. ~100-250 selon la taille EMNIST Letters).
2. Entraîner les teachers, collecter les votes sur public data (`get_teacher_votes`).
3. `noisy_argmax(votes, noise_scale)` — choisir noise_scale pour équilibrer accuracy ≥80% et MIA advantage ≤3% (fort consensus requis pour 26 classes). Éventuellement **confident aggregation**.
4. Entraîner le student `MLP(num_classes=26)` sur pseudo-labels.
5. `save_file(student_model.state_dict(), "pate_student.safetensors")`.
6. `POST /validate -F "model=@pate_student.safetensors"` → lire `flag`.

**Endpoints** : `GET /health`, `POST /validate`, `GET /` (`service: "PATE Privacy Challenge (EMNIST Letters)"`).

### 5.3 Skills Assessment (Fashion-MNIST) — id 3598

**Énoncé** : « What is the flag you get for successfully solving the skills assessment? »

**Objectif** : classifieur Fashion-MNIST défendu contre MIA.

| Critère | Requirement |
|---|---|
| Test accuracy | **≥ 70%** |
| Réduction MIA advantage | **≥ 40%** vs baseline vulnérable |
| Architecture | `FashionMNISTCNN` exacte |

**Baseline** (via `/baseline`) : `baseline_mia_advantage: 0.0895`, `required_improvement: 0.4`, `required_test_accuracy: 0.7`. Il faut réduire 0.0895 d'au moins 40% → advantage ≤ ~0.0537.

**Normalisation** : `transforms.Normalize((0.2860,), (0.3530,))`.

**Architecture EXACTE** :

```python
class FashionMNISTCNN(nn.Module):
    def __init__(self):
        super(FashionMNISTCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(64 * 3 * 3, 128)
        self.fc2 = nn.Linear(128, 10)
    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = self.pool(self.relu(self.conv3(x)))
        x = x.view(-1, 64 * 3 * 3)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x
```

**Méthode** :
1. Entraîner `FashionMNISTCNN` avec DP-SGD (Opacus). CNN déjà Opacus-compatible (Conv/ReLU/MaxPool/Linear, pas de BatchNorm), donc `ModuleValidator.fix()` sûr.
2. Choisir ε qui garde accuracy ≥70% ET advantage ≤0.0537 (ε modéré ~8-15 souvent suffit vu que la baseline advantage est déjà modeste 0.0895 ; ajuster).
3. `save_file(model.state_dict(), "defended_model.safetensors")` (⚠️ ici state_dict direct, ou `_module.state_dict()` si wrappé Opacus — le format valide le state dict de FashionMNISTCNN).
4. `POST /submit -F "defended_model=@defended_model.safetensors"` → réponse avec `flag`, `improvement_ratio` (ex. 0.9078), `mia_advantage`.

**Endpoints** : `GET /health` (`model_loaded:true`), `GET /baseline`, `POST /query` (samples → predictions+confidences), `POST /submit`.

---

## 🎯 Questions d'examen probables

1. **Q : Définition formelle de la (ε,δ)-DP ?**
   R : `P[M(D)∈S] ≤ e^ε·P[M(D')∈S] + δ` pour D, D′ différant d'un enregistrement. ε = borne multiplicative (privacy), δ = proba d'échec.

2. **Q : Que doit satisfaire δ ?**
   R : δ < 1/n (n = taille du training set). CIFAR-10 : δ=1e-5 = 1/100000 < 1/50000.

3. **Q : Écart-type du bruit dans le mécanisme Gaussien ?**
   R : σ = Δf·√(2·ln(1.25/δ))/ε. En DP-SGD : σ = max_grad_norm × noise_multiplier.

4. **Q : Les 3 mécanismes de DP-SGD ?**
   R : (1) per-sample gradient clipping (norme L2 ≤ C=max_grad_norm), (2) ajout de bruit Gaussien, (3) privacy composition/accounting (RDP/moments accountant).

5. **Q : Après clipping, quelle est la sensitivity de la somme des gradients ?**
   R : Exactement max_grad_norm (C). Un sample change la somme d'au plus un gradient clippé (norme ≤ C).

6. **Q : Pourquoi BatchNorm est incompatible avec Opacus/DP-SGD ? Alternatives ?**
   R : BatchNorm calcule des stats sur la dimension batch, couplant les gradients des samples → empêche le per-sample clipping. Alternatives : GroupNorm, LayerNorm, InstanceNorm. `ModuleValidator.fix()` substitue GroupNorm.

7. **Q : Noise multiplier pour ε=10 vs ε=3 (CIFAR-10, batch 256, C=1.0) ?**
   R : ~1.2 pour ε=10 ; ~3.8 pour ε=3 (≈3x plus de bruit).

8. **Q : Formule du sampling rate q en Poisson subsampling ? Valeur CIFAR-10 ?**
   R : q = batch_size/dataset_size = 256/50000 = 0.00512. Faible q → forte privacy amplification.

9. **Q : Fonction Opacus qui calcule le noise multiplier pour un ε cible ?**
   R : `PrivacyEngine.make_private_with_epsilon(...)`. `get_epsilon()` reporte le budget cumulé.

10. **Q : Comment sauvegarder un modèle DP-SGD entraîné avec Opacus ?**
    R : Accéder `model._module.state_dict()` (Opacus wrappe le module), puis `save_file(...)` en safetensors.

11. **Q : Principe de PATE en une phrase ?**
    R : n teachers sur partitions disjointes de données privées → votent sur données publiques → agrégation bruitée (noisy argmax + Laplace) → student entraîné sur pseudo-labels, sans jamais voir les données privées.

12. **Q : Sensitivity du vote PATE et ε par requête ?**
    R : Sensitivity = 2 (un vote passe d'une classe à une autre : +1/−1). ε₀ = 2/noise_scale. noise_scale=20 → ε₀=0.10.

13. **Q : Formule du noisy argmax PATE ?**
    R : ŷ = arg max_j ( n_j(x) + Lap(scale) ), n_j(x) = nb de teachers votant classe j.

14. **Q : Naive vs advanced composition pour 5000 queries à ε₀=0.10 ?**
    R : Naive = k·ε₀ = 500. Advanced (∝√k) via moments accountant ≈ 8.81.

15. **Q : Pourquoi le PATE student résiste au MIA ?**
    R : Protection architecturale (information bottleneck) : le student n'accède jamais aux données privées, il apprend seulement de labels bruités agrégés. Attack advantage ≈ 0 (indistinguable de l'aléatoire). Pas de bruit à l'inférence.

16. **Q : Que protège / ne protège PAS DP-SGD ?**
    R : Protège l'influence individuelle des samples (contre MIA). Ne protège PAS : patterns agrégés, model extraction/stealing, adversarial examples.

17. **Q : MIA advantage — définition et seuils ?**
    R : advantage = attack_accuracy − 0.5. >0.15 forte vulnérabilité, 0.05-0.15 modérée, <0.05 ≈ aléatoire.

18. **Q : Exigences des 3 challenges ?**
    R : DP-SGD/SVHN : acc≥55%, mia_adv≤5%. PATE/EMNIST Letters : acc≥80%, mia_adv≤3%. Skills/Fashion-MNIST : acc≥70%, réduction MIA ≥40% vs baseline (0.0895).

---

## 🧪 Code réutilisable

### DP-SGD complet (Opacus)

```python
import torch, torch.optim as optim
from safetensors.torch import save_file
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator

MAX_GRAD_NORM = 1.0
DELTA = 1e-5
DP_EPOCHS = 20
DP_LR = 0.1
TARGET_EPSILON = 10.0
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 1. Modèle Opacus-compatible (PAS de BatchNorm)
model = SVHNCNN().to(device)                     # ou CIFAR10CNN / FashionMNISTCNN
model = ModuleValidator.fix(model)               # substitue GroupNorm si besoin
optimizer = optim.SGD(model.parameters(), lr=DP_LR, momentum=0.9)

# 2. Attacher le PrivacyEngine — calcule le noise_multiplier pour ε cible
privacy_engine = PrivacyEngine(accountant="rdp")
model, optimizer, train_loader = privacy_engine.make_private_with_epsilon(
    module=model,
    optimizer=optimizer,
    data_loader=train_loader,                    # loader DÉDIÉ (Opacus le wrappe)
    target_epsilon=TARGET_EPSILON,
    target_delta=DELTA,
    epochs=DP_EPOCHS,
    max_grad_norm=MAX_GRAD_NORM,
)

# 3. Boucle d'entraînement standard (clipping + bruit gérés par Opacus)
criterion = torch.nn.CrossEntropyLoss()
for epoch in range(DP_EPOCHS):
    model.train()
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
    eps = privacy_engine.get_epsilon(DELTA)
    print(f"Epoch {epoch+1}/{DP_EPOCHS} - ε: {eps:.2f}")

# 4. Sauvegarde (accès ._module car Opacus wrappe)
save_file(model._module.state_dict(), "dp_model.safetensors")
```

### PATE complet (teachers → noisy argmax → student)

```python
import numpy as np, torch
from safetensors.torch import save_file

NUM_TEACHERS = 250
NOISE_SCALE = 20.0          # ε₀ = 2/20 = 0.10
NUM_QUERIES = 5000
RANDOM_SEED = 1337

# --- Partitions disjointes ---
np.random.seed(RANDOM_SEED)
indices = np.random.permutation(len(X_private_norm))
partition_size = len(X_private_norm) // NUM_TEACHERS
teacher_partitions = []
for i in range(NUM_TEACHERS):
    s = i * partition_size
    idx = indices[s:] if i == NUM_TEACHERS - 1 else indices[s:s + partition_size]
    teacher_partitions.append(idx)

# --- Entraînement des teachers ---
teachers = []
for i in range(NUM_TEACHERS):
    pi = teacher_partitions[i]
    teacher = MLP(input_size=num_features, hidden_layers=[128, 64],
                  num_classes=num_classes, dropout=0.2)
    tl = create_dataloader(X_private_norm[pi], y_private[pi], 64)
    train_model(teacher, tl, holdout_loader, device=DEVICE, epochs=30, learning_rate=0.001)
    teachers.append(teacher)

# --- Voting ---
def get_teacher_votes(teachers, X, device):
    votes = np.zeros((X.shape[0], num_classes), dtype=np.int32)
    for teacher in teachers:
        preds = np.argmax(get_model_predictions(teacher, X, device), axis=1)
        for i, p in enumerate(preds):
            votes[i, p] += 1
    return votes

# --- Noisy aggregation (Laplace) ---
def noisy_argmax(votes, noise_scale):
    noise = np.random.laplace(loc=0.0, scale=noise_scale, size=votes.shape)
    return np.argmax(votes.astype(np.float64) + noise, axis=1)

query_indices = np.random.choice(len(X_public_norm), NUM_QUERIES, replace=False)
X_query = X_public_norm[query_indices]
votes = get_teacher_votes(teachers, X_query, DEVICE)
student_labels = noisy_argmax(votes, NOISE_SCALE)

# --- Budget privacy (advanced composition) ---
def compute_privacy_budget(num_queries, noise_scale, delta=1e-5):
    per_query_eps = 2.0 / noise_scale
    epsilon_sq_sum = num_queries * (per_query_eps ** 2)
    total = np.sqrt(2 * epsilon_sq_sum * np.log(1 / delta))
    total += num_queries * per_query_eps * (np.exp(per_query_eps) - 1)
    return total, per_query_eps

total_eps, per_eps = compute_privacy_budget(NUM_QUERIES, NOISE_SCALE)  # ≈ 8.81, 0.10

# --- Student (jamais de données privées, pas de budget consommé) ---
student_model = MLP(input_size=num_features, hidden_layers=[128, 64],
                    num_classes=num_classes, dropout=0.2)
student_loader = create_dataloader(X_query, student_labels, 64)
train_model(student_model, student_loader, holdout_loader, device=DEVICE,
            epochs=30, learning_rate=0.001)
save_file(student_model.state_dict(), "pate_student.safetensors")

# --- Optionnel : confident aggregation (rejette low-consensus, économise le budget) ---
def confident_aggregation(votes, noise_scale, threshold):
    max_votes = votes.max(axis=1)
    mask = max_votes >= threshold
    labels = np.full(len(votes), -1, dtype=np.int64)
    if mask.sum() > 0:
        cv = votes[mask]
        noise = np.random.laplace(0.0, noise_scale, size=cv.shape)
        labels[mask] = np.argmax(cv.astype(np.float64) + noise, axis=1)
    return labels, mask
```

### Mesure MIA (confidence threshold)

```python
def compute_mia_advantage(model, X_members, y_members, X_nonmembers, y_nonmembers, device):
    mc = np.max(get_model_predictions(model, X_members, device), axis=1)
    nc = np.max(get_model_predictions(model, X_nonmembers, device), axis=1)
    n = min(len(mc), len(nc))
    all_conf = np.concatenate([mc[:n], nc[:n]])
    all_lab = np.concatenate([np.ones(n), np.zeros(n)])   # balance → baseline 50%
    best = 0.0
    for t in np.percentile(all_conf, np.linspace(0, 100, 1000)):
        acc = np.mean((all_conf >= t).astype(int) == all_lab)
        if acc > best:
            best, best_t = acc, t
    return best, best - 0.5, best_t          # (attack_acc, advantage, threshold)
```

### Soumission challenge

```python
import requests
with open("model.safetensors", "rb") as f:
    r = requests.post(f"{BASE_URL}/validate",   # ou /submit pour Skills Assessment
        files={"model": ("model.safetensors", f, "application/octet-stream")})
print(r.json())   # {"passed": true, "accuracy": ..., "mia_advantage": ..., "flag": "HTB{...}"}
```
