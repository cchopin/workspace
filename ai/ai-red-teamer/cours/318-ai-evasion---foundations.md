# AI Evasion - Foundations (module 318)

## En bref

Ce module pose les **fondamentaux des attaques d'evasion** (evasion attacks / adversarial examples) : la manipulation d'entrées **au moment de l'inference** (inference-time) pour forcer un modèle entraîné à produire une sortie incorrecte, sans toucher aux paramètres ni au pipeline d'entraînement. On distingue les attaques **training-time** (data poisoning, label manipulation, trojan) des attaques **inference-time** (evasion, prompt injection). Le cœur pratique est la **GoodWords attack** (Lowd & Meek, 2005) : ajouter des mots légitimes (`good words`) à un message spam pour faire basculer un classificateur **Naive Bayes** vers la classe `ham`, en exploitant l'**hypothèse d'indépendance conditionnelle** et l'**additivité des log-probabilités**. On couvre les **threat models** (white-box / black-box / grey-box), **targeted vs untargeted**, les **normes de perturbation** (L0, L2, L∞), le **perturbation budget** (ici ε / k mots), la **decision boundary**, et la **transferability**. Deux implémentations concrètes : white-box (extraction directe des `feature_log_prob_`) et black-box (approximation de fonction par requêtes, multi-armed bandit, UCB, epsilon-greedy, EMA, recherche combinatoire, discovery en 3 phases). Résultat clé : evasion >90% en ~15-20 mots (white-box), 85-95% de la performance white-box en black-box avec 1000 requêtes.

> 🎯 **Exam — Nature de l'evasion** : une evasion attack agit **UNIQUEMENT à l'inference**, ne modifie **pas** les paramètres ni les données d'entraînement, et réussit en envoyant une entrée forgée par l'**interface normale** du modèle pour qu'un exemple franchisse la **decision boundary** apprise.

---

## 1. Concepts fondamentaux de l'evasion

### 1.1 Définition : adversarial example et perturbation

Un **adversarial example** est une entrée délibérément forgée pour provoquer une **misclassification** (ou une sortie incorrecte) par un modèle ML, tout en restant, pour un humain ou pour l'intention réelle, équivalente à l'entrée d'origine.

- **Perturbation** : la modification appliquée à l'entrée originale `x` pour obtenir l'exemple adverse `x' = x + δ` (ou, en NLP/bag-of-words, `x' = x ⊕ W`). δ est le vecteur de perturbation.
- Dans le module, la perturbation n'est **pas** un bruit continu sur des pixels mais l'**ajout de tokens** (good words) : `M_augmented = M_spam ∪ G`.
- L'objectif : déplacer **une seule prédiction** de l'autre côté du **seuil** (threshold) du classificateur, sans changer le sens du message pour un humain (le spam reste lisible et intact).

### 1.2 Adversarial Machine Learning : lifecycle et taxonomie

L'**adversarial machine learning** étudie les interactions hostiles avec les systèmes ML. Les attaques se placent à deux moments du lifecycle :

**Training-time attacks** (changent ce que le modèle *apprend*) :
- `Data poisoning` : injection/altération d'échantillons d'entraînement → le modèle internalise des patterns biaisés. Requiert l'accès au dataset ou au pipeline ; effet **global** sur le comportement.
- `Label manipulation` : falsification des annotations → la ground truth ne correspond plus à la réalité.
- `Trojan attacks` : implantation de **triggers cachés** qui activent un comportement spécifique quand le pattern de l'attaquant apparaît.

**Inference-time manipulation** (change seulement ce que le modèle *voit* au moment de prédire) :
- `Evasion` : laisse l'entraînement et les paramètres intacts, réussit via l'interface normale ; **un exemple** franchit la decision boundary.
- `Prompt injection` : pattern central d'evasion pour les LLM (voir 1.8).

> 🎯 **Exam — Data poisoning vs evasion** : le data poisoning nécessite l'accès aux **données/pipeline** et déplace le comportement **globalement** ; l'evasion ne touche **rien** à l'entraînement et opère au niveau d'**une seule prédiction** à l'inference.

### 1.3 Threat models : white-box, black-box, grey-box

Le **threat model** définit la connaissance/accès de l'attaquant sur le modèle cible.

| Threat model | Connaissance de l'attaquant | Dans le module |
|---|---|---|
| **White-box** | Accès **complet** : architecture, paramètres, poids, probabilités apprises, gradients, données d'entraînement | Lecture directe de `feature_log_prob_`, calcul exact des goodness scores, sélection optimale des mots |
| **Black-box** | Accès **uniquement par requêtes** (query access) : on soumet des entrées et on observe labels/scores de confiance. Aucun accès aux internals | Endpoint `/predict` renvoyant `spam_probability` ; discovery par exploration/exploitation dans un budget de requêtes |
| **Grey-box** | Connaissance **partielle** : p.ex. type d'architecture ou de features connu, mais paramètres inconnus (position intermédiaire) | Non exploité directement, mais transferability et connaissance du bag-of-words en relèvent |

- **White-box** = "peer directly into learned distributions and cherry-pick the most potent candidates". Transforme l'attaque en **problème d'optimisation direct**.
- **Black-box** = transforme l'attaque en **problème d'exploration** nécessitant une **gestion des requêtes** (query budget) et des stratégies de recherche intelligentes. On modélise le classificateur comme une fonction inconnue.

> 🎯 **Exam — Black-box** : en black-box l'attaquant **ne voit que** les sorties (label + probabilité/score), **jamais** l'architecture, les paramètres ou les données. La leçon défensive : **cacher les internals offre une sécurité limitée** — un attaquant adaptatif redécouvre des vecteurs d'attaque équivalents empiriquement.

### 1.4 Targeted vs untargeted

- **Untargeted attack** : forcer **n'importe quelle** classe incorrecte (juste "pas la bonne"). But : sortir de la classe correcte.
- **Targeted attack** : forcer une **classe cible spécifique** choisie par l'attaquant.
- La GoodWords attack est **targeted** : la cible est explicitement `ham` (`target_label: "ham"` dans le challenge). On ne veut pas juste "pas spam", on veut précisément faire prédire `ham`. Dans la Skills Assessment : flip positive→**negative** (phase 1) et negative→**positive** (phase 2), cibles imposées.

> 🎯 **Exam — Targeted** : la GoodWords attack est **targeted** (cible = classe `ham`/légitime). En binaire spam/ham, targeted et untargeted coïncident souvent, mais conceptuellement la cible est spécifiée.

### 1.5 Normes de perturbation : L0, L2, L∞

Les **normes Lp** mesurent et contraignent l'**ampleur de la perturbation** δ = x' − x. Le choix de norme définit ce qui est "petit"/imperceptible.

- **L0** (`‖δ‖₀`) : **nombre de composantes modifiées** (compte les éléments non nuls de δ). Contraint **combien** de features/pixels/tokens changent, sans limiter l'intensité de chaque changement. → attaques *sparse* (peu d'éléments modifiés).
  - **Analogie directe avec la GoodWords attack** : le **perturbation budget est une contrainte de type L0** — on limite le **nombre de mots ajoutés** (`max_added_words`, `k`), pas leur "intensité". Ajouter 15-30 mots = perturbation L0 bornée.
- **L2** (`‖δ‖₂ = √(Σδᵢ²)`) : **distance euclidienne**. Contraint l'**énergie totale** de la perturbation ; répartit de petits changements sur beaucoup de composantes. Norme classique des attaques sur images (Carlini-Wagner L2, etc.).
- **L∞** (`‖δ‖∞ = maxᵢ|δᵢ|`) : **changement maximal sur une seule composante**. Contraint que **aucun** élément ne bouge de plus de ε ; permet de modifier *tous* les pixels un tout petit peu. Norme dominante en vision adverse (FGSM, PGD utilisent typiquement une boule L∞ de rayon ε).

> 🎯 **Exam — À quoi sert chaque norme** :
> - **L0** = *combien* d'éléments changent (sparsité). GoodWords ≈ budget L0 sur le nombre de mots.
> - **L2** = énergie/distance euclidienne globale de la perturbation.
> - **L∞** = amplitude **maximale** par élément (borne ε sur chaque composante) ; permet de perturber tous les éléments légèrement.

### 1.6 Perturbation budget ε (epsilon)

Le **perturbation budget** ε borne l'ampleur admissible de la perturbation : `‖δ‖p ≤ ε`. C'est le compromis central **subtilité vs succès** :
- ε trop petit → perturbation insuffisante → l'attaque échoue.
- ε trop grand → perturbation détectable (message non naturel, dépasse les limites, déclenche d'autres heuristiques).

Dans ce module, le budget prend **trois formes distinctes** (attention aux collisions de notation) :

1. **Budget de mots `k` / `max_added_words`** = le vrai perturbation budget de la GoodWords attack (contrainte type L0). Optimisation : `min_{W ⊆ 𝒱, |W| ≤ k} f(x ⊕ W)`. Empiriquement : 15-30 mots → >90% d'evasion ; challenge = 25 mots ; assessment = 30 (WB) / 40 (BB).
2. **ε de lissage** dans le goodness score `S(w) = P(w|ham) / (P(w|spam) + ε)` : petite constante (`1e-10`) pour éviter la division par zéro et garder un score fini/stable.
3. **ε (exploration rate)** de l'epsilon-greedy en black-box (`0.2` puis `0.1`) : probabilité d'explorer plutôt qu'exploiter.

> 🎯 **Exam — ε multiple** : distinguer le **perturbation budget** (nombre de mots `k`), l'**ε de lissage** (évite `÷0` dans le goodness score, `1e-10`), et l'**ε d'exploration** (epsilon-greedy, `0.2`). Ce sont **trois ε différents**.

### 1.7 Decision boundary et transferability

**Decision boundary** : la surface apprise séparant les classes. Une prédiction est déterminée par le côté de la frontière où tombe l'entrée. En Naive Bayes binaire, la frontière est **la probabilité 0.5** : la décision compare `prob[0]` (ham) et `prob[1]` (spam).
- Point critique : la décision est **binaire** — `prob = [0.501, 0.499]` évade **aussi bien** que `[0.99, 0.01]`. La magnitude de confiance est **jetée**. → cible d'optimisation : il suffit de **franchir 0.5**, pas de pousser aux extrêmes.
- L'attaque **déplace** l'exemple à travers la decision boundary par accumulation d'évidence ham.

**Transferability** : un adversarial example forgé contre un **modèle de substitution** (surrogate) trompe souvent **d'autres modèles de production**, surtout si architectures/données sont similaires. Conséquences :
- Permet la **préparation offline** et les attaques **black-box** (le défenseur n'expose qu'une API, pas les internals).
- Explique pourquoi masquer les internals protège peu : on entraîne un surrogate, on forge dessus, on transfère.

> 🎯 **Exam — Transferability** : un adversarial example forgé sur un **surrogate model** transfère fréquemment vers un modèle cible différent (architectures/données proches). C'est le fondement des attaques **black-box** et de la préparation **offline**.

### 1.8 Evasion : ML traditionnel vs LLMs

| Aspect | ML traditionnel | LLMs |
|---|---|---|
| Cible | **features fixes** (bag-of-words, byte patterns) | texte ouvert + **instruction following** |
| Levier | statistiques qui alimentent le classificateur (term frequencies, imports, sections) | **conversational state** et priorisation d'instructions |
| Pattern central | edits qui poussent l'exemple à travers un **seuil de label** | **prompt injection** (directives adverses dans le prompt/contexte pour surpasser le `system` guidance) |
| Surface de sortie | un label | la **sortie est elle-même une surface d'action** (code, requête SQL, markup exécuté/rendu) ; tool routing / API calling → comportement en aval |
| Exemples | spam filter (ajout de tokens benins change les term frequencies) ; malware detector statique (réarranger sections, perturber imports) | injection d'instructions surpassant le system prompt |

**Idée commune** : modifier **uniquement l'entrée vue au moment de la prédiction** pour orienter le comportement. On commence par les classificateurs structurés (mécanique **observable et mesurable**), puis on mappe l'intuition vers les prompts LLM (surface plus riche, même objectif).

> 🎯 **Exam — Prompt injection** : c'est le pattern d'evasion **central pour les LLM** ; l'attaquant place des directives adverses dans le prompt/contexte pour que le modèle priorise ces instructions sur le `system` guidance, **sans changer les paramètres** (donc inference-time). Danger accru car la sortie est une **surface d'action**.

---

## 2. La GoodWords Attack (mécanisme exact)

### 2.1 Origine et principe

- Introduite par **Lowd et Meek, 2005**, *"Good Word Attacks on Statistical Spam Filters"*.
- Technique adverse exploitant les **hypothèses probabilistes fondamentales** des classificateurs **Naive Bayes** (spam detection).
- Mécanisme : **appender des mots légitimes** soigneusement choisis à un message malveillant → déguise le contenu spam avec des termes d'apparence légitime.
- **Point clé** : n'obfusque **pas** et ne modifie **pas** le contenu spam ; le message spam reste **intact** ; on **augmente** avec des tokens qui déplacent la distribution de probabilité globale. Le sens/intention du spam est préservé tout en convainquant le classificateur que le message est légitime.

### 2.2 Rappel Naive Bayes

Théorème de Bayes appliqué à la classification :

```latex
P(C|D) = \frac{P(D|C) \cdot P(C)}{P(D)}
```

Probabilité que le message `D` appartienne à la classe `C` (`spam` ou `ham`). Règle de décision (comparaison des posteriors) :

```latex
\text{class} = \arg\max_{c \in \{spam, ham\}} P(c|D)
```

Hypothèse **"naïve"** = **indépendance conditionnelle** des features → la vraisemblance se factorise :

```latex
P(D|C) = \prod_{i=1}^{n} P(w_i|C)
```

où chaque mot `w_i` contribue **indépendamment**. Pour éviter l'**underflow numérique**, on travaille en **log space** :

```latex
\text{class} = \arg\max_{c \in \{spam, ham\}} \left[ \log P(c) + \sum_{i=1}^{n} \log P(w_i|c) \right]
```

**Pourquoi le log space ?** Multiplier 3000 petites probabilités (ex. `0.001^3000`) underflow à zéro autour de `10^{-308}`. Le log transforme la **multiplication en addition** → stabilité numérique. C'est **cette additivité** qui rend l'attaque possible : ajouter des mots **décale la somme courante**.

> 🎯 **Exam — Vulnérabilité racine** : l'**hypothèse d'indépendance conditionnelle** + l'**additivité en log space** font que chaque mot ajouté **décale simplement la somme**. Le classificateur ne modélise **aucune relation entre mots ni contexte**, donc il ne peut pas pénaliser le mismatch sémantique entre les good words et le contenu spam. La **quantité l'emporte sur la qualité**.

### 2.3 Mécanique de l'attaque et manipulation des probabilités

**Analogie** : le classificateur est une balance ; chaque mot ajoute du poids d'un côté (`FREE`, `WINNER` → spam). L'attaque ajoute assez de mots légitimes côté ham pour **faire basculer** la balance, contenu spam inchangé.

Message spam `M_spam` avec mots `{w_1, ..., w_m}`. Le classificateur calcule normalement :

```latex
\log P(spam|M_{spam}) = \log P(spam) + \sum_{i=1}^{m} \log P(w_i|spam)
```

```latex
\log P(ham|M_{spam}) = \log P(ham) + \sum_{i=1}^{m} \log P(w_i|ham)
```

Classification correcte en spam si :

```latex
\log P(spam|M_{spam}) > \log P(ham|M_{spam})
```

**L'attaque** : appender un ensemble de "good words" `G = {g_1, g_2, ..., g_k}`, créant `M_{augmented} = M_{spam} \cup G`. Nouveaux calculs :

```latex
\log P(spam|M_{augmented}) = \log P(spam) + \sum_{i=1}^{m} \log P(w_i|spam) + \sum_{j=1}^{k} \log P(g_j|spam)
```

```latex
\log P(ham|M_{augmented}) = \log P(ham) + \sum_{i=1}^{m} \log P(w_i|ham) + \sum_{j=1}^{k} \log P(g_j|ham)
```

Les mots spam d'origine contribuent **toujours** la même évidence ; les good words ajoutent du poids côté ham. L'attaque **réussit** quand l'inégalité s'inverse :

```latex
\log P(ham|M_{augmented}) > \log P(spam|M_{augmented})
```

**Condition exacte de renversement** (le good words doivent apporter plus d'évidence ham que le message n'apportait d'évidence spam) :

```latex
\sum_{j=1}^{k} [\log P(g_j|ham) - \log P(g_j|spam)] > \sum_{i=1}^{m} [\log P(w_i|spam) - \log P(w_i|ham)] + [\log P(spam) - \log P(ham)]
```

- **Membre gauche** = contribution nette des good words (chaque good word décale vers ham de `log P(g_j|ham) − log P(g_j|spam)`).
- **Membre droit** = obstacle à surmonter = signal spam d'origine + biais de classe (`log P(spam) − log P(ham)`).

**Exemple chiffré** : message avec mots spam forts contribuant une différence combinée de **8.0** vers spam. Ajouter `meeting`, `tomorrow`, `thanks` contribuant chacun **3.0** vers ham → il faut au moins **3 mots** (3 × 3.0 = 9.0 > 8.0) pour renverser.

But de l'attaque : sélectionner les `g_j` qui **maximisent** :

```latex
\log P(g_j|ham) - \log P(g_j|spam)
```

### 2.4 Good Word Selection Strategy

**Goodness score** d'un mot `w` :

```latex
S(w) = \frac{P(w|ham)}{P(w|spam) + \epsilon}
```

où `ε` = petite constante anti-division-par-zéro. Score élevé = mot **fréquent en ham, rare/absent en spam**.

Processus systématique :
1. Analyser le corpus d'entraînement → calculer les probabilités conditionnelles de tous les termes.
2. Ranker les mots par goodness score → liste priorisée de candidats (considère ratios de proba **et** fréquences absolues, pour que les mots choisis soient représentatifs).
3. Éviter les mots qui déclencheraient d'**autres heuristiques** (rule-based filters) ou paraîtraient suspects à un reviewer humain → contraintes de cohérence/plausibilité linguistique.

**Nombre de mots** : paramètre équilibrant efficacité vs longueur. Trop peu → shift insuffisant ; trop → message non naturel / dépasse les limites de transmission. **La plupart des spams sont mal classés en ajoutant 15 à 30 good words**, avec des **taux d'evasion > 90%**.

> 🎯 **Exam — Goodness score** : `S(w) = P(w|ham) / (P(w|spam) + ε)`. Les meilleurs good words sont fréquents en ham et rares en spam. L'`ε` évite la division par zéro (mots absents du spam) et garde le score fini.

### 2.5 Pourquoi l'attaque fonctionne (facteurs aggravants)

Facteurs d'implémentation qui augmentent la susceptibilité :
- **Distributions statiques** : les probabilités mot-classe sont fixées à l'entraînement depuis des données historiques → étudiables par l'adversaire.
- **Laplace smoothing** : assigne une proba non nulle aux mots rares/inconnus → empêche le rejet de combinaisons inhabituelles et **élargit la gamme de mots** disponibles pour l'attaquant.
- Ensemble : **indépendance conditionnelle** + **scoring additif en log space** + **distributions apprises statiques** + **smoothing** = conditions exploitées par la GoodWords attack.

---

## 3. Implémentation du spam filter (cible)

### 3.1 Installation de la librairie

```bash
# Install the AI Library (or update it)
pip install --upgrade git+https://github.com/PandaSt0rm/htb-ai-library
```

### 3.2 Setup et dépendances

```python
import json
import pickle
import random
import re
import urllib.request
import zipfile
from pathlib import Path
import numpy as np

# Reproducibility
random.seed(1337)
np.random.seed(1337)
```

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score
```

```python
from htb_ai_library import (
    AZURE,
    HACKER_GREY,
    HTB_GREEN,
    MALWARE_RED,
    NODE_BLACK,
    NUGGET_YELLOW,
    WHITE,
    AQUAMARINE,
    load_model,
    save_model,
)
```

- Seed `1337` = reproductibilité (essentiel pour vérifier l'efficacité de l'attaque de façon consistante).
- `pathlib.Path` gère les différences de chemin Windows/Linux automatiquement.

### 3.3 Dataset SMS Spam (UCI)

Dataset **SMS Spam Collection** (UCI), 5 574 messages labellisés, avec cache local :

```python
print("\n[*] Loading SMS Spam Dataset...")

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
dataset_path = data_dir / "sms_spam.csv"
```

```python
if dataset_path.exists():
    print(f"[+] Using cached dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
else:
    print("[*] Downloading from UCI repository...")
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
    zip_path = data_dir / "sms_spam.zip"

    urllib.request.urlretrieve(url, zip_path)
```

Extraction en mémoire + parsing TSV (validation `len(parts) == 2` contre les enregistrements corrompus) :

```python
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open("SMSSpamCollection") as f:
            lines = [line.decode("utf-8").strip() for line in f]

    # Parse tab-separated format
    data = []
    for line in lines:
        parts = line.split('\t')
        if len(parts) == 2:
            data.append({"label": parts[0].lower(), "message": parts[1]})

    df = pd.DataFrame(data)
    df.to_csv(dataset_path, index=False)
    zip_path.unlink()
    print(f"[+] Dataset saved to {dataset_path}")
```

Distribution initiale : **5572 messages, 747 spam (13.4%), 4825 ham (86.6%)** → **class imbalance** réaliste (le ham domine), qui crée des biais exploitables vers la classe majoritaire.

### 3.4 Preprocessing (deux niveaux)

**Minimal cleaning** (préserve les spam indicators) :

```python
def minimal_clean(text):
    """
    Minimal cleaning that preserves spam indicators.
    ...
    """
    # Decode HTML entities (e.g., &amp; -> &)
    text = html_module.unescape(text)

    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)

    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\r+', ' ', text)

    return text.strip()
```

- `html.unescape` → `&amp;` devient `&`. Normalisation `NFKC` → la ligature "ﬁ" devient "fi" (évite que du contenu identique soit traité différemment).

**Final cleaning** (pour la vectorisation) — **garde** chiffres, symboles monétaires, ponctuation car ce sont des **spam features** :

```python
def clean_text(text):
    """
    Final cleaning for vectorization.
    ...
    """
    text = text.lower()
    # Keep numbers, currency symbols, punctuation - they're spam features!
    # Only remove truly problematic characters
    text = re.sub(r'[^\w\s£$€¥!?.,;:\'\"-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
```

- Lowercase → "FREE" = "free" (évite la duplication de vocabulaire).
- On préserve `\w`, `\s`, ponctuation (`!!!` = urgence, `£900` = offre monétaire).

Application + nettoyage du dataset :

```python
df['preprocessed'] = df['message'].apply(minimal_clean)
df['clean_message'] = df['preprocessed'].apply(clean_text)
```

```python
# Remove only exact duplicates
df = df.drop_duplicates(subset=['label', 'clean_message'])
# Remove empty messages
df = df[df['clean_message'].str.len() > 0]
```

Après nettoyage : **419 duplicates retirés**, 0 vides → **5153 messages, 638 spam (12.4%), 4515 ham (87.6%)**. Le taux de duplicates plus élevé en spam révèle leur **nature répétitive** (exploitée par l'attaque).

### 3.5 Split train/test (stratifié)

```python
X = df['clean_message'].values
y = df['label'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

→ **Training : 4122**, **Testing : 1031**. `stratify=y` maintient le ratio 12.4% de spam dans les deux ensembles.

### 3.6 Entraînement du MultinomialNB

Vectorizer avec `token_pattern` custom (capture les features spam-specific) :

```python
    vectorizer = CountVectorizer(
        max_features=3000,
        token_pattern=r'\b\w+\b|[£$€¥]+|\d+|!!+|\?\?+|\.\.+',
        lowercase=True,
        stop_words='english'
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
```

```python
    classifier = MultinomialNB()
    classifier.fit(X_train_vec, y_train)

    # Save model for reproducibility
    with open(model_path, 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'classifier': classifier}, f)
```

- `token_pattern` capture mots (`\b\w+\b`), symboles monétaires (`[£$€¥]+`), nombres (`\d+`), ponctuation répétée (`!!+`, `\?\?+`, `\.\.+`).
- `max_features=3000` (limite l'overfitting), `stop_words='english'` (retire "the", "is" non discriminants).
- Chargement d'un modèle sauvé → `transform()` (pas `fit_transform()`) pour garder le **vocabulaire d'origine**.

**Performance** : Training accuracy **0.9922**, Testing accuracy **0.9864** (gap minimal 0.58% → bonne généralisation). Ham : precision/recall 0.99 ; **Spam : precision 0.95, recall 0.94** (métriques spam plus basses à cause du class imbalance). Cible réaliste et idéale pour démontrer l'attaque.

---

## 4. Implémentation White-Box de la GoodWords attack

### 4.1 Extraction des GoodWords (accès direct aux paramètres)

```python
# Get feature names and probabilities
feature_names = vectorizer.get_feature_names_out()
ham_log_probs = classifier.feature_log_prob_[0]  # Ham class
spam_log_probs = classifier.feature_log_prob_[1]  # Spam class
```

- `get_feature_names_out()` = vocabulaire de 3000 mots.
- `feature_log_prob_` contient `log P(w|c)`. Index `[0]` = ham, `[1]` = spam.

### 4.2 Calcul des goodness scores

```python
# Calculate goodness scores
goodness_scores = []
for i, word in enumerate(feature_names):
    ham_prob = np.exp(ham_log_probs[i])
    spam_prob = np.exp(spam_log_probs[i])
    goodness = ham_prob / (spam_prob + 1e-10)
    goodness_scores.append((word, goodness, ham_prob, spam_prob))
```

- `np.exp` récupère la proba depuis le log space (`exp(-5.3) ≈ 0.005`).
- **ε = `1e-10`** évite `÷0` ; un mot 100× en ham / 0× en spam donne `goodness ≈ 300000000` (stable).
- Tuple `(word, goodness, ham_prob, spam_prob)` = info complète (deux distributions peuvent donner le même ratio 50 mais impacter différemment).

### 4.3 Sélection des top good words

```python
# Sort by goodness
goodness_scores.sort(key=lambda x: x[1], reverse=True)
top_good_words = goodness_scores[:100]
```

**Top 10** (les plus "ham-like") :

```txt
    lor             | goodness:    50.22 | ham_p: 0.0047 | spam_p: 0.0001
    ü               | goodness:    47.99 | ham_p: 0.0045 | spam_p: 0.0001
    ...             | goodness:    45.65 | ham_p: 0.0299 | spam_p: 0.0007
    da              | goodness:    45.39 | ham_p: 0.0042 | spam_p: 0.0001
    later           | goodness:    29.39 | ham_p: 0.0027 | spam_p: 0.0001
    doing           | goodness:    25.67 | ham_p: 0.0024 | spam_p: 0.0001
    ask             | goodness:    25.30 | ham_p: 0.0024 | spam_p: 0.0001
    really          | goodness:    24.55 | ham_p: 0.0023 | spam_p: 0.0001
    cos             | goodness:    23.81 | ham_p: 0.0022 | spam_p: 0.0001
    lol             | goodness:    23.81 | ham_p: 0.0022 | spam_p: 0.0001
```

- `lor` (slang singapourien) domine (50.22, apparaît 50× plus en ham). Mots conversationnels / temporels / verbes d'action dominent (nature interactive du ham légitime).

### 4.4 Boucle d'attaque et courbe d'efficacité

Points de test de 0 (baseline) à 40 (saturation) :

```python
word_counts = [0, 5, 10, 15, 20, 25, 30, 35, 40]
```

Augmentation = simple concaténation (append-only) :

```python
def augment_message(message, words_to_add):
    """Append good words to a message"""
    if len(words_to_add) > 0:
        return message + " " + " ".join(words_to_add)
    return message
```

Test d'evasion (frontière à 0.5) :

```python
        vec = vectorizer.transform([augmented])
        prob = classifier.predict_proba(vec)[0][1]
        ...
        if prob[0] > prob[1]:
            evaded += 1
```

**Sélection greedy** : on prend toujours les good words les mieux rankés en premier. Non globalement optimal (synergies ignorées) mais efficace. Tester toutes les combinaisons de 20 parmi 100 exigerait :

```latex
{100 \choose 20} \approx 5.4 \times 10^{20}
```

Le greedy termine en secondes.

**Résultats (128 messages spam de test)** :

```txt
  Words:  0 | Evasion:   6.25% (8/128)
  Words:  5 | Evasion:  41.41% (53/128)
  Words: 10 | Evasion:  74.22% (95/128)
  Words: 15 | Evasion:  96.09% (123/128)
  Words: 20 | Evasion: 100.00% (128/128)
  Words: 25 | Evasion: 100.00% (128/128)
  Words: 30 | Evasion: 100.00% (128/128)
  Words: 35 | Evasion: 100.00% (128/128)
  Words: 40 | Evasion: 100.00% (128/128)
```

- **Baseline 6.25%** = false negative rate naturel (8/128).
- Explosion catastrophique entre 5 et 15 mots (41% → 96%). **100% à 20 mots.**
- Le bag-of-words **ne peut pas** distinguer un ham légitime d'un spam augmenté : additivité en log space + aucun mécanisme pour détecter le mismatch sémantique.

### 4.5 Forme sigmoïde de la courbe

Accumulation linéaire en log space :

```latex
\log P(\text{ham}\mid \text{message}) = \log P(\text{ham}) + \sum_{w \in \text{words}} \log P(w\mid \text{ham})
```

Cette accumulation **linéaire en log space** devient une **réponse sigmoïde non linéaire** en probability space (via softmax). Trois phases :
- **Phase 1** (0→5 mots) : evasion basse (6.25% baseline).
- **Phase 2** (transition rapide 5→15) : montée explosive.
- **Phase 3** (15→20) : saturation à 100%. Au-delà de 20, aucun bénéfice marginal.

> 🎯 **Exam — Seuil binaire** : la decision boundary est à **0.5**. `[0.501, 0.499]` évade autant que `[0.99, 0.01]`. La cible d'optimisation est de **franchir 0.5**, la magnitude de confiance est ignorée.

### 4.6 Analyse d'impact par mot

Test individuel de chaque mot (top 20) sur 50 messages, mesure de la réduction de spam proba :

```python
    for message in sample_spam:
        # Calculate original spam probability
        vec_orig = vectorizer.transform([message])
        prob_orig = classifier.predict_proba(vec_orig)[0][1]  # spam prob

        # Calculate probability after adding the word
        vec_aug = vectorizer.transform([message + " " + word])
        prob_aug = classifier.predict_proba(vec_aug)[0][1]

        # Measure the probability reduction
        impact = prob_orig - prob_aug
        total_impact += impact
```

**Résultat** : `lor` réduit la spam proba de seulement **~4.0 points** en solo. **Pas de "silver bullet"** — aucun mot ne flip seul. L'evasion vient de l'**accumulation orchestrée** de plusieurs mots.

> 🎯 **Exam — Goodness vs impact** : un **goodness score élevé** (association ham théorique isolée) ≠ **impact pratique élevé** (capacité réelle à déplacer un message *déjà* spam-laden). `lor` : goodness 50.22 mais impact ~4%. Un mot fortement ham peut ne pas surmonter plusieurs indicateurs spam forts.

---

## 5. Black-Box GoodWords Attack

### 5.1 Contexte black-box

Contraintes réalistes : on soumet des messages et on observe **seulement** les scores de confiance / estimations de probabilité. Pas d'accès à l'architecture, aux paramètres, aux données. Transforme l'optimisation directe en **problème d'exploration** avec gestion de requêtes.

### 5.2 Approximation de fonction par requêtes

Modéliser le classificateur comme une fonction inconnue :

```latex
f: \mathcal{X} \rightarrow [0, 1]
```

Trouver une transformation `T` qui minimise `f(T(x))` pour les spams tout en préservant le sens :

```latex
T: \mathcal{X} \rightarrow \mathcal{X}
```

Problème d'optimisation (sous budget `k`) :

```latex
\min_{W \subseteq \mathcal{V},\; |W|\le k} \; f\!\bigl(x \oplus W\bigr)
```

- `𝒱` = vocabulaire candidat, `W` = petit ensemble de mots appendés, `⊕` = concaténation (bag-of-words addition, **pas** union ensembliste).

**Estimation par finite differences** (pas de gradient) — reward d'un mot :

```latex
r_w(x) \;\equiv\; f(x)\;-\;f(x \oplus \{w\})
```

Pour un ensemble :

```latex
r_W(x) = f(x) - f(x \oplus W)
```

Reward positif = le mot **réduit** le spam score. Ex. `thanks` fait passer 0.95 → 0.80 = reward 0.15 (efficace) ; 0.95 → 0.94 = reward 0.01 (marginal).

### 5.3 Exploration vs exploitation & multi-armed bandit

**Dilemme exploration-exploitation** : tester de nouveaux mots (exploration) vs utiliser des mots connus efficaces (exploitation), sous **budget de requêtes limité**.

**Multi-armed bandit** : chaque mot = un "bras" de machine à sous avec efficacité inconnue. Tester un mot = tirer un bras = consommer une requête. Tension : explorer risque de gaspiller des requêtes ; exploiter risque de rater de meilleurs mots.

### 5.4 Upper Confidence Bound (UCB)

```latex
\text{UCB}_w = \underbrace{\bar{r}_w}_{\text{exploitation term}} + \underbrace{c\sqrt{\frac{\ln(t)}{n_w}}}_{\text{exploration bonus}}
```

- `r̄_w` = reward moyen observé (exploitation).
- `c√(ln(t)/n_w)` = bonus d'exploration ; **grandit** pour les mots peu testés.
- `n_w` = nombre de tests du mot `w` (dénominateur → moins testé = bonus plus grand).
- `t` = total de requêtes (croissance lente du bonus).
- `c` = constante d'exploration (**typiquement 2.0**).

**Exemple (t=200)** :

```latex
\text{UCB} = 0.15 + 2\sqrt{\ln(200)/50} = 0.15 + 0.47 = 0.62
```
```latex
\text{UCB} = 0.12 + 2\sqrt{\ln(200)/5} = 0.12 + 1.48 = 1.60
```
```latex
\text{UCB} = 0 + \infty = \infty
```

- `thanks` (50 tests, moy 0.15) → 0.62 ; `appreciate` (5 tests, moy 0.12) → **1.60** ; `wonderful` (0 test) → **∞** (toujours explorer les mots non testés d'abord).
- **Contre-intuitif** : UCB choisit `appreciate` malgré une moyenne plus basse, car le grand bonus d'incertitude compense.

**Garanties théoriques** : regret **logarithmique** `O(log T)` (croissance sublinéaire) sous hypothèses i.i.d., stationnaires, rewards bornés (UCB1). En pratique, la variabilité par message ajoute du bruit mais UCB reste une heuristique efficace.

> 🎯 **Exam — UCB** : `UCB_w = r̄_w + c·√(ln t / n_w)`. Premier terme = exploitation (reward moyen) ; second = exploration (décroît quand `n_w` augmente). `c ≈ 2.0`. Mots non testés → bonus infini (explorés en premier). Regret `O(log T)`.

### 5.5 Construction du vocabulaire candidat

Miner les tokens des messages ham + filtres + liste curée :

```python
def extract_ham_word_freq(X_train, y_train, sample_size=500):
    ...
    ham_msgs = X_train[y_train == 'ham']
    limit = min(sample_size, len(ham_msgs))
    freq = {}
    for msg in ham_msgs[:limit]:
        for w in str(msg).split():
            if 2 < len(w) < 10:  # keep typical conversational tokens
                freq[w] = freq.get(w, 0) + 1
    return freq
```

- Filtre longueur `2 < len(w) < 10` : retire "a"/"I"/"to" (stopwords) et les URLs/numéros >10 chars.

```python
def select_high_frequency_words(word_freq, max_words=100, min_freq=5):
    ...
    sorted_by_freq = sorted(word_freq.items(), key=lambda x: (-x[1], x[0]))
    top = [w for w, c in sorted_by_freq if c > min_freq][:max_words]
    return top
```

- Tri à deux niveaux `(-x[1], x[0])` : fréquence décroissante puis lexicographique (**déterministe**).

```python
def merge_with_curated(top_words, additional_candidates=None):
    ...
    if additional_candidates is None:
        additional_candidates = [
            "ok", "cos", "ill", "thats", "later", "said", "ask", "didnt",
            "dont", "doing", "going", "come", "home", "tomorrow", "today", "sorry",
            "thanks", "yeah", "yes", "sure", "see", "tell", "know", "think",
        ]
    merged = set(top_words) | set(additional_candidates)
    return sorted(merged)
```

- Termes conversationnels curés (contractions informelles, temporels, polis) : hedge contre le biais d'échantillonnage et le distribution shift en black-box.

`build_candidate_vocabulary` compose le tout → **~112 candidats** (ordre déterministe : fréquence ham puis lexicographique). Cette phase offline **consomme 0 requête**.

### 5.6 Query management & allocation de budget (40-40-20)

```python
query_budget = 1000
queries_used = 0
query_log = []
```

```python
def estimate_budget_allocation(total_budget):
    ...
    explore = int(0.4 * total_budget)
    exploit = int(0.4 * total_budget)
    combine = total_budget - explore - exploit  # absorb rounding
    return {
        'exploration': explore,
        'exploitation': exploit,
        'combination': combine,
    }
```

→ **exploration 400 (40%), exploitation 400 (40%), combination 200 (20%)** = 1000. `discovery` = `exploration + combination` (60%). Budget de 1000 = rate limits / coûts typiques d'API de production.

### 5.7 Scoring adaptatif : epsilon-greedy + EMA

```python
def initialize_adaptive_scorer():
    """Initialize adaptive scoring data structures"""
    return {
        'word_scores': {},      # Maps word -> effectiveness score
        'word_counts': {},      # Maps word -> number of times tested
        'exploration_rate': 0.2  # 20% exploration for discovery phase
    }
```

**Epsilon-greedy** (exploration) :

```python
def epsilon_greedy_select(scorer, available_words):
    ...
    if random.random() < scorer['exploration_rate']:
        # Exploration: try untested or rarely tested words
        untested = [w for w in available_words if w not in scorer['word_counts']]
        if untested:
            return random.choice(untested)
        else:
            # Choose least tested word
            return min(available_words,
                      key=lambda w: scorer['word_counts'].get(w, 0))
```

**Exploitation** (branche else) :

```python
    else:
        # Exploitation: choose best performing word
        return max(available_words,
                  key=lambda w: scorer['word_scores'].get(w, 0))
```

- ε constant = simple/efficace mais **pas** de garantie de regret logarithmique (peut avoir un **regret linéaire** au pire cas). `O(log T)` exige UCB ou un ε qui **décroît** (annealed epsilon).

**Exponential Moving Average (EMA)** — mise à jour du score :

```python
def update_word_score(scorer, word, impact, alpha=0.3):
    ...
    if word not in scorer['word_scores']:
        scorer['word_scores'][word] = impact
        scorer['word_counts'][word] = 1
    else:
        # Exponential moving average
        old_score = scorer['word_scores'][word]
        scorer['word_scores'][word] = (1 - alpha) * old_score + alpha * impact
        scorer['word_counts'][word] += 1
```

- `alpha=0.3` : nouvelle obs = 30%, historique = 70%. Ex. score 0.10, impact 0.15 → `(0.7×0.10)+(0.3×0.15) = 0.115`. Évite la surréaction aux outliers.

### 5.8 Recherche combinatoire (synergies)

```python
def discover_word_combinations(message, test_words, max_size=3):
    ...
    from itertools import combinations
    combination_scores = {}
    message_vec = vectorizer.transform([message])
    message_score = classifier.predict_proba(message_vec)[0][1]
```

Individuels d'abord (baseline pour la synergie) :

```python
    for word in test_words[:20]:
        test_message = message + " " + word
        test_vec = vectorizer.transform([test_message])
        score = classifier.predict_proba(test_vec)[0][1]
        impact = message_score - score
        combination_scores[(word,)] = impact
```

Paires (synergie = impact réel − somme des impacts individuels) :

```python
    if max_size >= 2:
        for word1, word2 in combinations(test_words[:15], 2):
            test_message = message + " " + word1 + " " + word2
            test_vec = vectorizer.transform([test_message])
            score = classifier.predict_proba(test_vec)[0][1]

            # Calculate synergy
            individual_impact = combination_scores.get((word1,), 0) + combination_scores.get((word2,), 0)
            actual_impact = message_score - score
            synergy = actual_impact - individual_impact

            if synergy > 0:  # Positive synergy detected
                combination_scores[(word1, word2)] = actual_impact
```

- 15 mots → 105 paires. Synergie **super-additive** : ex. `got` (0.22) + `like` (0.12), attendu 0.34, réel 0.38 → synergie 0.04. Fréquent pour mots sémantiquement liés (`meeting` + `tomorrow` = scheduling légitime).

Triplets (top 5 paires × top 10 mots) :

```python
    if max_size >= 3:
        top_pairs = sorted(
            [(k, v) for k, v in combination_scores.items() if len(k) == 2],
            key=lambda x: x[1], reverse=True
        )[:5]

        for pair, pair_score in top_pairs:
            for word in test_words[:10]:
                if word not in pair:
                    triplet = tuple(sorted(pair + (word,)))
                    test_message = message + " " + " ".join(triplet)
                    test_vec = vectorizer.transform([test_message])
                    score = classifier.predict_proba(test_vec)[0][1]
                    combination_scores[triplet] = message_score - score

    return combination_scores
```

- `tuple(sorted(...))` → stockage cohérent quel que soit l'ordre. Triplets comme `("meeting","tomorrow","thanks")` peuvent réduire de **40-50%**.

### 5.9 Discovery en trois phases

Perspective information theory — chaque requête apporte de l'**information gain** :

```latex
I(Q) = H(W) - H(W\mid Q)
```

- `H(W)` = entropie (incertitude) de l'efficacité des mots avant la requête ; `H(W|Q)` = après. `I(Q)` = réduction d'incertitude.

Les 3 phases maximisent le gain d'information cumulé :
- **Exploration** : maximise la réduction d'entropie sur tout le vocabulaire (large filet).
- **Exploitation** : raffine les estimations des mots à forte valeur (là où la variance/incertitude importe).
- **Combination** : découvre les synergies non linéaires imprévisibles depuis les scores individuels.

**Phase 1 — Exploration** (budget 400) : sélection message aléatoire + `epsilon_greedy_select`, **2 requêtes par test** (baseline + augmenté), `impact = prob_orig − prob_aug`, update EMA, `queries_used += 2` :

```python
        impact = prob_orig - prob_aug
        update_word_score(scorer, word, impact)
        queries_used += 2
```

**Phase 2 — Exploitation** (budget 400) : `exploration_rate = 0.1`, focus sur les **top 30** (puis top 15) mots et **20** messages :

```python
    scorer['exploration_rate'] = 0.1  # Reduce exploration
    top_words = sorted(scorer['word_scores'].items(), key=lambda x: x[1], reverse=True)[:30]
    ...
        test_message = random.choice(spam_messages[:20])  # Focus on fewer messages
        word = random.choice(top_word_list[:15])  # Focus on best words
```

**Phase 3 — Combination** (budget 200, si `> 50`) : `discover_word_combinations` sur ≤3 messages, garde le meilleur score par combinaison, ~2 requêtes par combinaison.

Retour :

```python
    final_words = sorted(scorer['word_scores'].items(), key=lambda x: x[1], reverse=True)
    return final_words, best_combinations, queries_used
```

### 5.10 Résultats black-box et comparaison

Discovery sur 50 messages, complète **exactement à 1000/1000** requêtes. Top mot découvert : **`really` impact 0.121** (12.1 points) — plus fort que le top white-box `lor` (4.0 points).

**Pourquoi ?** White-box ranke par **ratio théorique** :

```latex
\frac{P(w\mid\text{ham})}{P(w\mid\text{spam})}
```

Black-box mesure l'**impact empirique** (shifts réels sur de vrais spams). Les deux métriques peuvent **diverger** : goodness élevé ≠ impact pratique élevé, et vice-versa.

Test des mots découverts (messages 30-50, différents de la discovery) :

```python
test_counts = [0, 5, 10, 15, 20, 25, 30]
...
        if prob < 0.5:  # evasion threshold
            evaded += 1
```

Progression typique : 0 mots → 5-10%, 10 mots → 70-75%, 15 mots → 90-95%, 20+ mots → 95-100%. **Légèrement moins raide** que white-box.

**Conclusions clés** :
- Black-box atteint **85-95% de la performance white-box** malgré des contraintes d'info sévères.
- Trouve **des mots différents mais aussi efficaces** → **surface d'attaque large**, pas étroite (multiples vecteurs).
- **Défense** : cacher les internals offre une sécurité limitée. La vulnérabilité est **architecturale** (Naive Bayes combine additivement en log space), pas dans la fuite d'information.

> 🎯 **Exam — WB vs BB** : white-box = optimisation directe via `feature_log_prob_`, goodness = ratio théorique. Black-box = exploration empirique par requêtes (MAB/UCB/epsilon-greedy/EMA/combinations), impact = mesure réelle. BB atteint 85-95% de WB avec 1000 requêtes. La vulnérabilité racine est **architecturale**.

---

## 6. Challenges (labs) — énoncés et méthode

> **Note** : les labs de ce module sont **interactifs (docker)** et les réponses (`user_answer`) sont **vides / non résolues**. Ci-dessous : l'énoncé exact de chaque challenge + la **méthode de résolution** attendue d'après le cours. Les flags sont statiques et propres à chaque instance (`HTB{...}`), non fournis ici.

### 6.1 GoodWords Challenge (section 3871, id 3325)

**Énoncé** : *"What is the flag you get after a successful attack?"* (cubes 5, XP 40).

**Contexte** : prendre un message spam fort et appender une séquence compacte de mots légitimes pour qu'un **Multinomial Naive Bayes** prédise `ham`. Service **black-box** : on ne voit que labels et spam_probabilities via `/predict`. Contrainte **append-only** + word budget. `/submit` renvoie un flag statique.

**API** :
- `GET /health` → readiness.
- `GET /challenge` → `{ "base_message", "max_added_words": 25, "target_label": "ham" }`.
- `POST /predict` `{"text": ...}` → `{"label", "spam_probability"}`.
- `POST /submit` `{"augmented_text": "<base> ..."}` → valide append-only + budget + label ham → `{"result":"success", "details":{...}, "flag":"HTB{...}"}`.

**Méthode attendue** (scaffold fourni) :
1. `GET /challenge` → récupérer `base_message` et `budget = max_added_words` (25).
2. Mesurer la spam_probability baseline du `base_message` via `/predict`.
3. Pour chaque mot d'un petit vocabulaire (`["please","thanks","meeting","tomorrow","coffee","home","support","good","great","safe"]`), mesurer l'impact `base_p − predict(base + " " + w)` (approche **finite differences** black-box).
4. Trier par impact décroissant, garder les mots à impact positif.
5. **Greedy append** sous budget : ajouter les mots un à un, re-tester le label après chaque ajout, s'arrêter dès que `label == "ham"` (respecte append-only et minimise le nombre de mots).
6. `POST /submit` avec l'`augmented_text` → récupérer le flag.

Scaffold Python fourni :

```python
import os, requests, random, numpy as np
random.seed(1337); np.random.seed(1337)
host = os.getenv("BASE_URL", "http://127.0.0.1:8080")
ch = requests.get(f"{host}/challenge", timeout=10).json()
base, budget = ch["base_message"], int(ch["max_added_words"])

def predict(t):
    return requests.post(f"{host}/predict", json={"text": t}, timeout=15).json()

base_p = predict(base)["spam_probability"]
vocab = ["please","thanks","meeting","tomorrow","coffee","home","support","good","great","safe"]
imp = []
for w in vocab:
    p2 = predict(base + " " + w)["spam_probability"]
    imp.append((w, base_p - p2))
imp.sort(key=lambda x: x[1], reverse=True)
top = [w for w, d in imp if d > 0][: max(2*budget, 20)]

aug = base
for i, w in enumerate(top, 1):
    if i > budget: break
    aug = aug + " " + w
    lab = predict(aug)["label"]
    if lab == "ham":
        break

print(requests.post(f"{host}/submit", json={"augmented_text": aug}, timeout=15).json())
```

### 6.2 Skills Assessment: Feature Obfuscation Attack (section 3876, id 3326)

**Énoncé** : *"What is the flag value you get from the instance api after completing the skills assessment?"* (cubes 15, XP 40).

**Contexte** : GoodWords contre **deux** classificateurs Naive Bayes, deux phases (sentiment de reviews de films). Il faut réussir **les deux** phases pour obtenir le flag.
- **Phase 1 (White-box)** : flipper **10 reviews positives → negative**. Accès complet au modèle (download). Max **30 mots** par review.
- **Phase 2 (Black-box)** : flipper **10 reviews negatives → positive**. Seulement requêtes API, pas d'accès au modèle. Max **40 mots** par review.

**API** :
- `GET /health` → `{"status":"healthy","service":"skills_assessment_lab"}`.
- `GET /challenge/whitebox` → reviews (`id`, `text`, `target_sentiment`), `max_added_words:30`, `model_endpoint:/model/download`, `submit_endpoint:/submit/whitebox`.
- `GET /model/download` → bundle pickle (classifier, vectorizer, feature_names, class labels).
- `POST /submit/whitebox` `{"solutions":[{"id","augmented_text"}, ...]}`.
- `GET /challenge/blackbox` → même forme, 40 mots.
- `POST /predict` `{"text"}` → `{"label","negative_probability","positive_probability"}`.
- `POST /submit/blackbox` → même format.
- `GET /status` → progression.

**Méthode attendue** :

*Phase 1 (white-box)* :
1. `GET /challenge/whitebox` ; `GET /model/download` → charger le bundle pickle (`bundle['classifier']`, `bundle['feature_names']`).
2. Extraire `feature_log_prob_[0]` (negative) et `[1]` (positive) — cible = **negative**, donc les "good words" sont ceux fréquents en **negative**, rares en positive (goodness `= P(w|neg)/(P(w|pos)+ε)`).
3. Ranker par goodness, sélectionner greedy les top mots.
4. Pour chaque review positive : append ≤30 mots jusqu'à ce que le modèle (local) prédise negative. Vérifier append-only.
5. `POST /submit/whitebox` avec les 10 solutions.

*Phase 2 (black-box)* :
1. `GET /challenge/blackbox` ; cible = **positive**.
2. Construire un vocabulaire candidat (mots typiques des reviews positives) ; mesurer l'impact par `/predict` (finite differences sur `negative_probability` / vers `positive_probability`).
3. Discovery adaptative (epsilon-greedy / EMA / éventuellement combinations) sous budget de requêtes.
4. Greedy append ≤40 mots par review negative jusqu'à `label == positive`.
5. `POST /submit/blackbox`.
6. Les deux phases validées → `GET /status` / réponse de submit contient le flag `HTB{...}`.

**Success criteria** : les 10 reviews de chaque phase doivent flipper ; le serveur indique lesquelles réussissent/échouent pour raffiner.

---

## 7. Points de synthèse défensifs

- La faille est **architecturale** : indépendance conditionnelle + additivité log space + distributions statiques + smoothing.
- Naive Bayes **ne modélise pas** les relations entre mots ni le contexte → aveugle au mismatch sémantique.
- Masquer les internals (security by obscurity) = protection **limitée** (transferability + discovery empirique black-box).
- Contre-mesures implicites : modèles contextuels (n-grams, features de co-occurrence), détection de longueur/incohérence, rate limiting des requêtes (contre le black-box discovery), monitoring des distributions d'entrée.

---

## 🎯 Questions d'examen probables

**Q1. Qu'est-ce qu'une evasion attack et à quel moment du lifecycle agit-elle ?**
R : Une manipulation d'entrée **à l'inference** (inference-time) qui force un modèle entraîné à produire une sortie incorrecte, **sans** modifier paramètres ni données d'entraînement. Elle réussit en envoyant une entrée forgée via l'interface normale pour qu'un exemple franchisse la **decision boundary**. À distinguer des attaques training-time (data poisoning, label manipulation, trojan).

**Q2. Différence entre white-box, black-box et grey-box ?**
R : **White-box** = accès complet (architecture, paramètres, gradients, données) → optimisation directe. **Black-box** = accès par requêtes seulement (labels/scores) → problème d'exploration sous budget. **Grey-box** = connaissance partielle (ex. type de features/architecture connu, paramètres inconnus).

**Q3. Targeted vs untargeted, et de quel type est la GoodWords attack ?**
R : Untargeted = forcer n'importe quelle classe incorrecte ; targeted = forcer une **classe cible spécifique**. La GoodWords attack est **targeted** (cible = `ham`/classe légitime).

**Q4. Que contraignent respectivement L0, L2 et L∞ ?**
R : **L0** = nombre d'éléments modifiés (sparsité) — c'est la nature du budget GoodWords (nombre de mots `k`). **L2** = distance euclidienne / énergie totale de la perturbation. **L∞** = amplitude maximale par élément (borne ε sur chaque composante, permet de perturber tous les éléments légèrement).

**Q5. Qu'est-ce que le perturbation budget ε, et sous quelles formes apparaît-il dans le module ?**
R : Borne l'ampleur admissible de la perturbation (`‖δ‖ ≤ ε`), compromis subtilité/succès. Formes : (1) **budget de mots `k`/`max_added_words`** (vrai budget, type L0) ; (2) **ε de lissage `1e-10`** dans le goodness score (anti-÷0) ; (3) **ε d'exploration `0.2`** de l'epsilon-greedy. Trois ε distincts.

**Q6. Qu'est-ce que la transferability et pourquoi est-elle centrale ?**
R : Un adversarial example forgé contre un **surrogate model** trompe souvent d'autres modèles de production (architectures/données similaires). Elle permet la préparation **offline** et les attaques **black-box**, et explique pourquoi masquer les internals protège peu.

**Q7. Où se situe la decision boundary d'un Naive Bayes binaire et quelle en est l'implication d'attaque ?**
R : À **probabilité 0.5** (comparaison `prob[0]` ham vs `prob[1]` spam). Décision **binaire** : `[0.501,0.499]` évade autant que `[0.99,0.01]`. Il suffit donc de **franchir 0.5**, pas d'aller aux extrêmes.

**Q8. Pourquoi la GoodWords attack fonctionne-t-elle contre Naive Bayes ?**
R : Hypothèse d'**indépendance conditionnelle** → vraisemblance factorisée `P(D|C)=∏P(w_i|C)` → en **log space** les contributions s'**additionnent**. Chaque good word décale la somme vers ham ; le modèle ne modélise ni relations ni contexte, donc ne détecte pas le mismatch. Aggravé par distributions statiques + Laplace smoothing.

**Q9. Écrire le goodness score et expliquer ses termes.**
R : `S(w) = P(w|ham) / (P(w|spam) + ε)`. Score élevé = mot fréquent en ham et rare en spam. `ε` (petit, `1e-10`) évite la division par zéro et garde le score fini pour les mots absents du spam.

**Q10. Condition mathématique de renversement (succès) de l'attaque ?**
R : `Σ_j [log P(g_j|ham) − log P(g_j|spam)] > Σ_i [log P(w_i|spam) − log P(w_i|ham)] + [log P(spam) − log P(ham)]`. Gauche = contribution nette des good words ; droite = signal spam d'origine + biais de classe.

**Q11. Combien de good words pour évader, et quelle forme a la courbe d'efficacité ?**
R : Typiquement **15-30 mots** → evasion >90% (dans le lab : 15→96%, 20→100%). Courbe **sigmoïde** : accumulation linéaire en log space → réponse non linéaire en probability space via softmax (3 phases : basse, transition explosive, saturation).

**Q12. Différence entre goodness score et impact pratique d'un mot ?**
R : Le **goodness score** mesure l'association ham théorique isolée (ratio de probas) ; l'**impact pratique** mesure la réduction réelle de spam proba quand le mot est ajouté à un *vrai* spam. Ils divergent : `lor` a goodness 50.22 mais impact ~4%. Un mot fortement ham ne surmonte pas forcément plusieurs indicateurs spam.

**Q13. Formule UCB et rôle de chaque terme ?**
R : `UCB_w = r̄_w + c·√(ln(t)/n_w)`. `r̄_w` = exploitation (reward moyen) ; `c·√(ln t/n_w)` = exploration (grand pour mots peu testés `n_w`). `c ≈ 2.0`. Mots non testés → bonus ∞. Garantie de regret `O(log T)` sous i.i.d./bornés.

**Q14. Comment l'attaquant estime-t-il l'effet d'un mot en black-box (sans gradient) ?**
R : Par **finite differences** : `r_w(x) = f(x) − f(x ⊕ {w})` (spam score baseline moins spam score après ajout du mot). Reward positif = mot efficace. Optimisation globale : `min_{|W|≤k} f(x ⊕ W)`.

**Q15. Comment se répartit le budget de 1000 requêtes en black-box, et quelle performance atteint-on ?**
R : **40-40-20** : exploration 400, exploitation 400, combination 200 (`discovery` = exploration+combination = 60%). Résultat : **85-95% de la performance white-box**, prouvant que la vulnérabilité est **architecturale** et non due à la fuite d'information ; cacher les internals protège peu.
