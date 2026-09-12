# Fundamentals of AI (module 290) — Fiche de révision

## En bref

- L'**AI** est le champ large ; le **ML** en est un sous-ensemble (apprendre depuis des données sans programmation explicite) ; le **DL** est un sous-ensemble du ML utilisant des neural networks à plusieurs couches. Emboîtement : AI ⊃ ML ⊃ Neural Nets ⊃ DL.
- Trois paradigmes ML : **supervised** (données labellisées → classification/regression), **unsupervised** (données non labellisées → clustering, dimensionality reduction, anomaly detection), **reinforcement** (apprentissage par essai-erreur via rewards/penalties).
- Algorithmes supervised : **Linear Regression** (OLS), **Logistic Regression** (sigmoid, classification binaire), **Decision Trees** (Gini/entropy/information gain), **Naive Bayes** (Bayes' theorem + indépendance conditionnelle), **SVM** (margin, support vectors, kernel trick).
- Algorithmes unsupervised : **K-Means** (centroids, Euclidean distance, Elbow/Silhouette), **PCA** (eigenvectors/eigenvalues, covariance matrix), **anomaly detection** (One-Class SVM, Isolation Forest, LOF).
- Algorithmes RL : **Q-Learning** (off-policy, model-free, Q-table, Bellman) et **SARSA** (on-policy).
- DL : perceptron, MLP, activation functions (sigmoid/ReLU/tanh/softmax), backpropagation + gradient descent, loss functions (MSE, cross-entropy), optimizers (SGD, Adam, RMSprop), **CNNs** (images), **RNNs/LSTM/GRU** (séquences).
- Generative AI : **GANs**, **VAEs**, **autoregressive models**, **diffusion models**, **LLMs** (transformers, self-attention, tokenization, embeddings).

---

# 1. Introduction to Machine Learning

## AI vs ML vs DL (relation d'emboîtement)

🎯 **Exam** : Ordre des cercles concentriques → **Artificial Intelligence ⊃ Machine Learning ⊃ Neural Nets ⊃ Deep Learning**.

### Artificial Intelligence (AI)
Champ large visant à développer des systèmes intelligents capables de tâches requérant l'intelligence humaine : comprendre le langage naturel, reconnaître des objets, prendre des décisions, résoudre des problèmes, apprendre de l'expérience. Capacités cognitives : reasoning, perception, problem-solving.

Domaines clés de l'AI :
- **Natural Language Processing (NLP)** : comprendre, interpréter, générer le langage humain.
- **Computer Vision** : « voir » et interpréter images et vidéos.
- **Robotics** : robots effectuant des tâches de façon autonome ou guidée.
- **Expert Systems** : systèmes imitant la prise de décision d'experts humains.

Objectif premier : **augmenter** les capacités humaines, pas seulement remplacer. Domaines d'application : healthcare (diagnostic, drug discovery), finance (détection de fraude, stratégies d'investissement), cybersecurity (identification et mitigation des menaces).

### Machine Learning (ML)
Sous-champ de l'AI permettant aux systèmes d'apprendre depuis des données et d'améliorer leur performance sur une tâche **sans programmation explicite**. Utilise des techniques statistiques pour identifier patterns, trends et anomalies.

Trois types principaux :
- **Supervised Learning** : apprend depuis des **labeled data** (chaque point a un outcome/label connu). Ex : image classification, spam detection, fraud prevention.
- **Unsupervised Learning** : apprend depuis des **unlabeled data**. Ex : customer segmentation, anomaly detection, dimensionality reduction.
- **Reinforcement Learning** : apprend par essai-erreur en interagissant avec un environnement, feedback sous forme de rewards/penalties. Ex : game playing, robotics, autonomous driving.

Applications : Healthcare, Finance (fraud detection, risk assessment, algorithmic trading), Marketing (recommendation systems), Cybersecurity (threat detection, intrusion prevention, malware analysis), Transportation (traffic prediction, route optimization).

### Deep Learning (DL)
Sous-champ du ML utilisant des **neural networks à multiples couches** pour apprendre et extraire des features de données complexes. Puissant pour données non structurées / haute dimension (images, audio, texte).

Caractéristiques clés :
- **Hierarchical Feature Learning** : chaque couche capture des features de plus en plus abstraites (ex : bords/textures → formes → objets).
- **End-to-End Learning** : mappe directement raw input → output sans manual feature engineering.
- **Scalability** : passe bien à l'échelle avec grands datasets et ressources.

Types de neural networks en DL :
- **CNNs (Convolutional Neural Networks)** : données image/vidéo, convolutional layers, patterns locaux et hiérarchies spatiales.
- **RNNs (Recurrent Neural Networks)** : données séquentielles (texte, parole), boucles permettant à l'information de persister à travers les time steps.
- **Transformers** : avancée récente, très efficace en NLP, utilise les **self-attention mechanisms** pour gérer les dépendances longue portée.

🎯 **Exam** : Différence ML classique vs DL → le DL apprend automatiquement les features depuis raw data (pas de manual feature engineering).

---

# 2. Mathematics Refresher for AI

> Section de référence : pas besoin de tout maîtriser, sert de rappel de notation.

## Arithmétique
- Multiplication `*` : `3 * 4 = 12`
- Division `/` : `10 / 2 = 5`
- Addition `+` : `5 + 3 = 8`
- Subtraction `-` : `9 - 4 = 5`

## Notations algébriques
- **Subscript** `x_t` : variable indexée par `t` (time step / état dans une séquence). Ex : `x_t = q(x_t | x_{t-2})`.
- **Superscript** `x^n` : exposant/puissance. `x^2 = x * x`.
- **Norm** `||...||` : taille/longueur d'un vecteur.
  - Euclidean norm : `||v|| = sqrt{v_1^2 + v_2^2 + ... + v_n^2}`
  - **L1 norm** (Manhattan distance) : `||v||_1 = |v_1| + |v_2| + ... + |v_n|`
  - **L∞ norm** (max absolute value) : `||v||_∞ = max(|v_1|, ..., |v_n|)`
  - Usages : distance entre vecteurs, regularization (anti-overfitting), normalisation.
- **Summation** `Σ` : `Σ_{i=1}^{n} a_i` = somme de `a_1 ... a_n`. Sert aux means, variances, séries.

## Logarithmes et exponentielles
- **log2(x)** : logarithme base 2, utilisé en information theory (entropy). `log2(8) = 3`.
- **ln(x)** : natural logarithm, base `e`. `ln(e^2) = 2`.
- **e^x** : exponential function. `e^2 ≈ 7.389`. Modélise croissance/décroissance, distributions (normal).
- **2^x** : exponentielle base 2. `2^3 = 8`. Systèmes binaires, information theory.

## Matrices et vecteurs
- **Matrix-Vector mult** `A * v` : `[[1,2],[3,4]] * [5,6] = [17, 39]`.
- **Matrix-Matrix mult** `A * B` : `[[1,2],[3,4]] * [[5,6],[7,8]] = [[19,22],[43,50]]`. Utilisé entre couches en DL.
- **Transpose** `A^T` : échange lignes/colonnes. `[[1,2],[3,4]]^T = [[1,3],[2,4]]`.
- **Inverse** `A^{-1}` : `A * A^{-1} = I`. Ex : inverse de `[[1,2],[3,4]] = [[-2,1],[1.5,-0.5]]`.
- **Determinant** `det(A)` : scalaire. `det([[1,2],[3,4]]) = 1*4 - 2*3 = -2`. Non-nul ⇒ matrice inversible.
- **Trace** `tr(A)` : somme de la diagonale principale. `tr([[1,2],[3,4]]) = 1 + 4 = 5`. Sert au calcul des eigenvalues.

## Set theory
- **Cardinality** `|S|` : nombre d'éléments. `|{1,2,3,4,5}| = 5`.
- **Union** `∪` : `{1,2,3} ∪ {3,4,5} = {1,2,3,4,5}`.
- **Intersection** `∩` : `{1,2,3} ∩ {3,4,5} = {3}`.
- **Complement** `A^c` : éléments hors de A. `U={1..5}, A={1,2,3} ⇒ A^c={4,5}`.

## Opérateurs de comparaison
`>=`, `<=`, `==` (égalité), `!=` (inégalité).

## Eigenvalues et scalaires
- **Lambda `λ`** : eigenvalue en algèbre linéaire, ou paramètre scalaire. `A * v = λ * v, λ = 3`. Usages : PCA, comportement des transformations linéaires.
- **Eigenvector** : vecteur non-nul qui, multiplié par une matrice, donne un multiple scalaire de lui-même (`A * v = λ * v`). Directions de variance maximale ⇒ PCA, dimensionality reduction.

## Fonctions et opérateurs
- **max(...)** : `max(4,7,2) = 7`. **min(...)** : `min(4,7,2) = 2`.
- **Reciprocal** `1/x` : `1/5 = 0.2`.
- **Ellipsis** `...` : continuation d'un pattern. `a_1 + a_2 + ... + a_n`.

## Fonctions et probabilité
- **Function notation** `f(x)` : `f(x) = x^2 + 2x + 1`.
- **Conditional probability** `P(x | y)` : proba de x sachant y. Bayesian inference.
- **Expectation** `E[...]` : valeur attendue/moyenne. `E[X] = Σ x_i P(x_i)`.
- **Variance** `Var(X) = E[(X - E[X])^2]` : dispersion autour de la moyenne.
- **Standard Deviation** `σ(X) = sqrt(Var(X))`.
- **Covariance** `Cov(X, Y) = E[(X - E[X])(Y - E[Y])]` : variation conjointe de deux variables.
- **Correlation** `ρ(X, Y) = Cov(X, Y) / (σ(X) * σ(Y))` : covariance normalisée, **range de -1 à 1**.

---

# 3. Supervised Learning Algorithms

Chaque data point associé à un outcome/label connu. But : apprendre une **mapping function** pour prédire le label de nouvelles données (généralisation).

Deux types de problèmes :
1. **Classification** : prédire un label **catégoriel** (spam/not spam, cat/dog/bird).
2. **Regression** : prédire une valeur **continue** (prix maison, marché boursier).

## Core Concepts (à connaître par cœur)

- **Training Data** : dataset labellisé pour entraîner le modèle (input features + output labels). Qualité + quantité impactent accuracy et généralisation.
- **Features** : propriétés mesurables servant d'input (ex prix maison : taille, chambres, localisation, âge).
- **Labels** : outcomes connus / target variables (les « bonnes réponses »).
- **Model** : représentation mathématique de la relation features → labels.
- **Training** : ajustement des paramètres du modèle pour minimiser l'erreur de prédiction.
- **Prediction** : application spécifique de l'inference, génère des outputs actionnables (classer un email, prévoir un prix).
- **Inference** : concept plus large — inclut la prediction mais aussi la compréhension de la structure/patterns, l'estimation de paramètres, l'interprétation (ex : importance des features, coefficients d'une régression). *Prediction = outputs actionnables ; Inference = expliquer/interpréter.*
- **Evaluation** : mesure de performance.

🎯 **Exam — Métriques d'évaluation** :
- **Accuracy** : proportion de prédictions correctes.
- **Precision** : proportion de vrais positifs parmi **toutes les prédictions positives**.
- **Recall** : proportion de vrais positifs parmi **tous les positifs réels**.
- **F1-score** : **moyenne harmonique** de precision et recall (mesure équilibrée).

- **Generalization** : capacité à bien prédire sur données nouvelles/non vues.
- **Overfitting** : le modèle apprend trop bien le training data (y compris bruit/outliers) ⇒ mauvaise généralisation (il a mémorisé).
- **Underfitting** : modèle trop simple ⇒ mauvaise performance sur training ET nouvelles données.
- **Cross-Validation** : découpe les données en plusieurs subsets (folds), entraîne sur combinaisons de folds et valide sur le fold restant ⇒ réduit l'overfitting, estimation plus fiable.
- **Regularization** : pénalité ajoutée à la loss function pour éviter l'overfitting.

🎯 **Exam — L1 vs L2 Regularization** :
- **L1 Regularization** : pénalité = **valeur absolue** de la magnitude des coefficients (`Σ|w|`).
- **L2 Regularization** : pénalité = **carré** de la magnitude des coefficients (`Σ w²`).

---

## 3.1 Linear Regression

Algorithme supervised qui prédit une **target continue** via une relation **linéaire** entre target et prédicteurs. But : trouver la best-fitting line qui minimise la somme des carrés des différences (predicted vs actual).

**Regression** = supervised learning prédisant une valeur continue (vs classification = label catégoriel).

### Simple Linear Regression (1 prédicteur)
```
y = mx + c
```
- `y` = target prédite, `x` = prédicteur, `m` = slope (pente), `c` = y-intercept (valeur de y quand x=0).
- Optimisation des `m` et `c` via **Ordinary Least Squares (OLS)** (minimise la somme des squared errors).

### Multiple Linear Regression (plusieurs prédicteurs)
```
y = b0 + b1x1 + b2x2 + ... + bnxn
```
- `b0` = y-intercept, `b1...bn` = coefficients.

### Ordinary Least Squares (OLS)
Méthode d'estimation des coefficients optimaux. Étapes :
1. **Calculate Residuals** : résidu = différence entre y actuel et y prédit.
2. **Square the Residuals** : chaque résidu au carré (positif + poids aux grosses erreurs).
3. **Sum the Squared Residuals** : somme = **Residual Sum of Squares (RSS)**.
4. **Minimize** : ajuste les coefficients pour le plus petit RSS possible.

### Assumptions de Linear Regression
- **Linearity** : relation linéaire predicteur↔target.
- **Independence** : observations indépendantes.
- **Homoscedasticity** : variance des erreurs constante à tous niveaux des prédicteurs.
- **Normality** : erreurs distribuées normalement (important pour l'inference sur les coefficients).

---

## 3.2 Logistic Regression

⚠️ Malgré son nom, c'est un algorithme de **classification** (binaire), pas de régression. Prédit une target catégorielle à **deux issues** (0/1, true/false). Output = **probabilité entre 0 et 1** (likelihood d'appartenir à la classe positive '1').

**Classification** = assigner des data points à des catégories/classes discrètes.

### Sigmoid Function
Mappe toute valeur d'input (−∞ à +∞) vers [0, 1]. Forme en « S ». Introduit la non-linéarité.
```
P(x) = 1 / (1 + e^-z)
```
- `P(x)` = probabilité prédite.
- `e` ≈ 2.718 (base du natural logarithm).
- `z` = combinaison linéaire des features : `z = m1x1 + m2x2 + ... + mnxn + c`.

### Spam Detection
Le modèle calcule un score de probabilité ; si score > threshold (ex 0.8) ⇒ spam.

### Decision Boundary
Séparateur entre classes. En 2 features = une ligne ; en dimensions supérieures = un **hyperplane**. Défini par les paramètres appris + le threshold choisi.

### Hyperplane
Sous-espace de dimension = (dimension de l'espace ambiant − 1).
- 2D : une ligne divise le plan en 2 régions.
- 3D : un plan divise l'espace en 2 moitiés.

### Threshold Probability
Souvent **0.5** par défaut, ajustable selon le compromis true/false positives.
- `P(x)` ≥ threshold ⇒ classe positive ; sinon négative.
- Ex : proba spam = 0.8, threshold 0.5 ⇒ spam. Threshold à 0.6 ⇒ exige plus de certitude.

### Data Assumptions (moins strictes que Linear Regression)
- **Binary Outcome** : target catégorielle à 2 issues.
- **Linearity of Log Odds** : relation linéaire entre prédicteurs et **log-odds** (log du odds ratio = proba événement / proba non-événement).
- **No/Little Multicollinearity** : prédicteurs peu corrélés entre eux.
- **Large Sample Size** : meilleure estimation avec grands datasets.

🎯 **Exam** : Logistic regression = classification, sigmoid, output ∈ [0,1], threshold par défaut 0.5.

---

## 3.3 Decision Trees

Algorithme supervised pour **classification ET regression**. Structure arborescente intuitive et interprétable ; apprend des règles de décision simples depuis les features.

Composants :
- **Root Node** : point de départ, contient tout le dataset.
- **Internal Nodes** : représentent features/attributs, se ramifient selon des règles.
- **Leaf Nodes** : nœuds terminaux = outcome/prediction final(e).

### Critères de split (mesures d'homogénéité)

**Gini Impurity** — proba de mal classer un élément choisi au hasard. Plus bas = plus pur.
```
Gini(S) = 1 - Σ (pi)^2
```
Exemple (30 classe A, 20 classe B) : pA=0.6, pB=0.4 ⇒ `Gini = 1 - (0.36 + 0.16) = 0.48`.

**Entropy** — désordre/incertitude. Plus bas = plus homogène.
```
Entropy(S) = - Σ pi * log2(pi)
```
Même exemple : `Entropy = -(0.6*log2(0.6) + 0.4*log2(0.4)) = 0.970954`.

**Information Gain** — réduction d'entropy après split sur une feature. On choisit la feature au **plus haut information gain**.
```
Information Gain(S, A) = Entropy(S) - Σ ((|Sv| / |S|) * Entropy(Sv))
```
Exemple détaillé (50 instances, feature F ∈ {1,2}) :
- F=1 : 30 instances (20 A, 10 B) ⇒ Entropy(S1) = 0.9183.
- F=2 : 20 instances (10 A, 10 B) ⇒ Entropy(S2) = 1.0.
- Weighted Entropy = (30/50)*0.9183 + (20/50)*1.0 = 0.55098 + 0.4 = 0.95098.
- Information Gain = 0.970954 − 0.95098 = **0.019974**.

### Building the Tree — conditions d'arrêt (stopping criteria)
- **Maximum Depth** : profondeur max atteinte (évite l'overfitting).
- **Minimum Number of Data Points** : nombre de points dans un nœud sous un seuil.
- **Pure Nodes** : tous les points du nœud sont de la même classe.

### Exemple « Playing Tennis »
Features : Outlook (Sunny/Overcast/Rainy), Temperature (Hot/Mild/Cool), Humidity (High/Normal), Wind (Weak/Strong). Target : Play Tennis (Yes/No). L'algo calcule information gain / Gini par feature ; **Outlook** donne souvent le plus haut information gain ⇒ root node. Puis récursion (ex sous-arbre Sunny → Humidity).

### Data Assumptions (minimales — grand avantage)
- **No Linearity Assumption** : gère relations linéaires ET non-linéaires.
- **No Normality Assumption** : pas besoin de distribution normale.
- **Handles Outliers** : robuste aux outliers (partitionne par valeurs, pas de calculs de distance).

---

## 3.4 Naive Bayes

Algorithme **probabiliste** de **classification** basé sur le **Bayes' theorem**. Populaire pour spam filtering et sentiment analysis (simple, efficace, bonne performance réelle).

### Bayes' Theorem
```
P(A|B) = [P(B|A) * P(A)] / P(B)
```
- `P(A|B)` : posterior — proba de A sachant B.
- `P(B|A)` : likelihood — proba de B sachant A.
- `P(A)` : prior de A. `P(B)` : prior de B.

**Exemple maladie** : P(A)=0.01 (prévalence 1%), P(B|A)=0.95 (test 95% correct), false positive rate 5%.
- `P(B) = P(B|A)*P(A) + P(B|¬A)*P(¬A) = (0.95*0.01) + (0.05*0.99) = 0.0095 + 0.0495 = 0.059`.
- `P(A|B) = (0.95*0.01)/0.059 = 0.0095/0.059 ≈ 0.161` ⇒ **~16.1%**.
- 🎯 **Exam** : Leçon — même avec un test précis, une faible prévalence rend un test positif peu concluant (~16%).

### Fonctionnement — hypothèse « naive »
Suppose l'**indépendance conditionnelle** des features (la présence d'une feature n'affecte pas les autres, sachant la classe). Étapes :
1. **Calculate Prior Probabilities** (proba de chaque classe a priori).
2. **Calculate Likelihoods** (proba de chaque feature sachant chaque classe).
3. **Apply Bayes' Theorem** ⇒ **posterior probability** pour chaque classe.
4. **Predict the Class** : classe à la plus haute posterior probability.

L'hypothèse d'indépendance est souvent violée mais Naive Bayes performe bien quand même.

### Types de Naive Bayes classifiers
- **Gaussian Naive Bayes** : features **continues** supposées suivre une **distribution gaussienne** (ex âge, revenu).
- **Multinomial Naive Bayes** : features **discrètes**, souvent text classification (fréquence de mots comme "free", "money").
- **Bernoulli Naive Bayes** : features **binaires** (présence/absence d'un mot).

### Data Assumptions
- **Feature Independence** (hypothèse centrale, conditionnelle à la classe).
- **Data Distribution** : le choix du classifier dépend de la distribution supposée.
- **Sufficient Training Data** : nécessaire pour estimer les probas correctement.

---

## 3.5 Support Vector Machines (SVMs)

Algorithme supervised puissant pour **classification et regression**. Efficace en haute dimension et pour relations non-linéaires. But : trouver l'**hyperplane optimal** qui **maximise la margin** séparant les classes.

### Maximizing the Margin
- **Margin** : distance entre l'hyperplane et les points les plus proches de chaque classe.
- **Support vectors** : ces points les plus proches ; ils définissent l'hyperplane et la margin.
- Plus grande margin ⇒ decision boundary robuste, meilleure généralisation.

### Linear SVM
Utilisé si données **linéairement séparables**. Hyperplane défini par :
```
w * x + b = 0
```
- `w` = weight vector (perpendiculaire à l'hyperplane), `x` = feature vector, `b` = bias (décale l'hyperplane vs l'origine).

### Non-Linear SVM — Kernel Trick
Quand les données ne sont pas linéairement séparables : une **kernel function** mappe les points vers un espace de **dimension supérieure** où ils deviennent séparables linéairement (hyperplane linéaire ↔ boundary non-linéaire dans l'espace original).

### Kernel Functions
- **Polynomial Kernel** : introduit des termes polynomiaux (x², x³...) — ajoute des courbes à la boundary.
- **Radial Basis Function (RBF) Kernel** : fonction gaussienne ; le plus populaire et versatile, capture des patterns complexes.
- **Sigmoid Kernel** : similaire à la sigmoid de logistic regression, boundary en forme de sigmoid.

### The SVM Function (problème d'optimisation)
```
Minimize: 1/2 ||w||^2
Subject to: yi(w * xi + b) >= 1 for all i
```
- `w` weight vector, `xi` feature vector du point i, `yi` label (−1 ou 1), `b` bias.
- Minimiser `||w||` ⇒ maximiser la margin, tout en classant correctement avec margin ≥ 1.

### Data Assumptions
- **No Distributional Assumptions**.
- **Handles High Dimensionality** (efficace même si #features > #points).
- **Robust to Outliers** (focus sur la margin, pas sur tous les points).

---

# 4. Unsupervised Learning Algorithms

Explore des **unlabeled data** pour découvrir patterns/structures cachés (pas de « bonnes réponses »).

Trois catégories :
1. **Clustering** : grouper des points similaires.
2. **Dimensionality Reduction** : réduire le nombre de variables en préservant l'information essentielle.
3. **Anomaly Detection** : identifier les points déviant fortement de la norme.

## Core Concepts
- **Unlabeled Data** : pas de labels/targets, l'algo se fie aux caractéristiques inhérentes.
- **Similarity Measures** :
  - **Euclidean Distance** : distance en ligne droite.
  - **Cosine Similarity** : angle entre deux vecteurs (valeur haute = plus similaire).
  - **Manhattan Distance** : somme des différences absolues des coordonnées.
- **Clustering Tendency** : propension inhérente des données à former des clusters (à évaluer avant clustering).
- **Cluster Validity** :
  - **Cohesion** : similarité intra-cluster (haute = cluster compact).
  - **Separation** : différence inter-clusters (haute = clusters distincts).
  - Indices : **silhouette score**, **Davies-Bouldin index**.
- **Dimensionality** : nombre de features. Haute dimension ⇒ « **curse of dimensionality** » (données sparse, distances moins signifiantes).
- **Intrinsic Dimensionality** : dimensionnalité sous-jacente réelle (souvent < nombre de features).
- **Anomaly** : point déviant fortement de la norme (événement inhabituel, erreur, fraude).
- **Outlier** : point éloigné de la majorité (sens plus large qu'anomaly).
- **Feature Scaling** :
  - **Min-Max Scaling** : échelle vers une plage fixe.
  - **Standardization (Z-score normalization)** : moyenne zéro, variance unitaire.

---

## 4.1 K-Means Clustering

Partitionne un dataset en **K clusters** distincts et non chevauchants. Itératif, minimise la **variance intra-cluster**.

Étapes :
1. **Initialization** : sélectionne aléatoirement K points comme **centroids** initiaux.
2. **Assignment** : assigne chaque point au centroid le plus proche (via distance métrique, ex Euclidean).
3. **Update** : recalcule les centroids = moyenne des points assignés.
4. **Iteration** : répète 2-3 jusqu'à stabilisation des centroids ou max iterations.

### Euclidean Distance
```
d(x, y) = sqrt(Σ (xi - yi)^2)
```

### Choix du K optimal
**Elbow Method** (WCSS = within-cluster sum of squares) :
1. Run K-means pour une gamme de K.
2. Calculer WCSS pour chaque K.
3. Tracer WCSS vs K.
4. Identifier le **elbow point** (coude) où le WCSS décroît plus lentement.
- Au-delà du coude ⇒ risque d'overfitting.

**Silhouette Analysis** — score ∈ [−1, 1] :
- proche de **1** : point bien assigné à son cluster.
- proche de **0** : point sur la decision boundary entre deux clusters.
- proche de **−1** : point probablement mal assigné.
- On choisit le K au **plus haut average silhouette score**.

**Autres considérations** : domain expertise, Computational Cost (K élevé = plus coûteux), Interpretability.

### Data Assumptions
- **Cluster Shape** : suppose clusters **sphériques** de tailles similaires.
- **Feature Scale** : sensible à l'échelle ⇒ standardiser/normaliser avant.
- **Outliers** : sensible aux outliers (distordent les centroids).

---

## 4.2 Principal Component Analysis (PCA)

Technique de **dimensionality reduction** : transforme des données haute dimension en représentation basse dimension en préservant un max d'information (variance). Identifie les **principal components** (combinaisons linéaires des features capturant la variance max). Usages : feature extraction, data visualization, noise reduction (ex eigenfaces en reconnaissance faciale).

Trois concepts clés :
- **Variance** : dispersion autour de la moyenne (PCA maximise la variance).
- **Covariance** : relation entre deux variables.
- **Eigenvectors & Eigenvalues** : eigenvectors = directions des principal components ; eigenvalues = quantité de variance expliquée par chaque composante.

### Étapes de l'algorithme PCA
1. **Standardize the data** (soustraire moyenne, diviser par std).
2. **Calculate the covariance matrix** des données standardisées.
3. **Compute eigenvectors et eigenvalues** de la covariance matrix.
4. **Sort the eigenvectors** par eigenvalue décroissante.
5. **Select principal components** : top `k` eigenvectors.
6. **Transform the data** : projeter sur les composantes sélectionnées.

### Eigenvalue Equation
```
A * v = λ * v
```
Exemple rubber band : `A = [[2,0],[0,1]]`, `v = [1,0]` ⇒ `A*v = [2,0]` (même direction, étiré ×2) ⇒ eigenvalue `λ = 2`.

En PCA :
```
C * v = λ * v
```
- `C` = covariance matrix des données standardisées, `v` = eigenvector (direction de variance max), `λ` = eigenvalue (variance expliquée).

### Méthodes de résolution
- **Eigenvalue Decomposition** : calcul direct.
- **Singular Value Decomposition (SVD)** : plus stable numériquement.

### Transformation
```
Y = X * V
```
- `Y` données transformées (basse dim), `X` données originales, `V` matrice des eigenvectors sélectionnés.

### Choix du nombre de composantes
Tracer l'**explained variance ratio** vs nombre de composantes ; choisir assez de composantes pour capturer un % élevé de variance totale (ex **95%**).

### Data Assumptions
- **Linearity** : relations linéaires entre features.
- **Correlation** : marche mieux avec features corrélées.
- **Scale** : sensible à l'échelle ⇒ standardiser avant.

---

## 4.3 Anomaly Detection (Outlier Detection)

Identifie les points déviant fortement du comportement normal. Applications : fraude, system failures, medical emergencies.

Trois types d'anomalies :
- **Point Anomalies** : point individuel très différent (spike de trafic réseau, transaction énorme).
- **Contextual Anomalies** : anormal dans un contexte spécifique (30°C normal en été, anormal en hiver).
- **Collective Anomalies** : groupe de points collectivement anormal (surge de login attempts depuis plusieurs IP).

Techniques :
- **Statistical Methods** : supposent une distribution (ex gaussienne) ; z-score, modified z-score, boxplots.
- **Clustering-Based Methods** : outliers = points hors clusters / dans petits clusters sparse (K-means, density-based).
- **Machine Learning-Based Methods** : One-Class SVM, Isolation Forest, Local Outlier Factor.

### One-Class SVM
Apprend une **boundary** englobant les données normales ; tout point hors boundary = outlier. Gère le non-linéaire via kernel functions.

### Isolation Forest
Isole les anomalies en partitionnant aléatoirement les données (**isolation trees**). Les anomalies (« few and different ») ont des **chemins plus courts**. À chaque étape : feature aléatoire + valeur de split aléatoire jusqu'à isolation.
```
score(x) = 2^(-E(h(x)) / c(n))
```
- `E(h(x))` : average path length de x dans les isolation trees.
- `c(n)` : average path length d'une recherche infructueuse dans un BST à n nœuds (facteur de normalisation).
- `n` : nombre de points.
- Score **proche de 1** = anomalie ; **proche de 0.5** = normal.

### Local Outlier Factor (LOF)
Density-based : compare la densité locale d'un point à celle de ses voisins.
```
LOF(p) = (Σ lrd(o) / k) / lrd(p)
```
- `lrd(p)` = local reachability density de p ; `lrd(o)` = celle d'un des k plus proches voisins ; `k` = nombre de voisins.
- **LOF élevé ⇒ probable outlier**.

**Local Reachability Density** :
```
lrd(p) = 1 / (Σ reach_dist(p, o) / k)
```
- `reach_dist(p, o)` = max(distance réelle p↔o, k-distance de o).
- **k-distance** d'un point o = distance à son k-ième plus proche voisin.

### Data Assumptions
- **Normal Data Distribution** (certaines méthodes supposent une distribution, ex gaussienne).
- **Feature Relevance**.
- **Labeled Data** (requise pour certaines méthodes ML).

🎯 **Exam** : Isolation Forest → anomalies = chemins courts ; LOF → basé densité locale ; One-Class SVM → boundary autour des normaux.

---

# 5. Reinforcement Learning Algorithms

Un **agent** apprend en interagissant avec un **environment**, guidé par rewards/penalties (essai-erreur). Vise une **policy** optimale (stratégie maximisant les rewards cumulés).

Deux catégories :
1. **Model-Based RL** : l'agent apprend un modèle de l'environnement pour prédire les états futurs et planifier (comme avoir une carte du labyrinthe).
2. **Model-Free RL** : apprend directement de l'expérience sans modéliser l'environnement (labyrinthe sans carte).

## Core Concepts
- **Agent** : apprenant et décideur.
- **Environment** : système externe où opère l'agent, répond aux actions.
- **State** : situation/condition actuelle de l'environnement (snapshot).
- **Action** : décision de l'agent affectant l'environnement.
- **Reward** : feedback scalaire (positif/négatif/zéro) indiquant la désirabilité d'une action.
- **Policy** : mapping states → actions ; peut être **deterministic** (toujours la même action) ou **stochastic** (probabiliste).
- **Value Function** : estime la valeur long terme d'un état/action (expected cumulative reward). Deux types :
  - **State-value function** : reward cumulé attendu depuis un état, en suivant une policy.
  - **Action-value function** : reward cumulé attendu en prenant une action dans un état, puis en suivant une policy.
- **Discount Factor (γ)** : ∈ [0, 1] ; valeur présente des rewards futurs.
  - `γ=0` : seulement rewards immédiats.
  - `γ=1` : tous les rewards futurs valorisés également.
- **Episodic vs Continuous Tasks** : episodic = épisodes finissant à un terminal state (labyrinthe) ; continuous = pas de fin explicite (bras robotique).

---

## 5.1 Q-Learning

RL **model-free**, apprend une policy optimale en estimant le **Q-value** (expected cumulative reward pour une action dans un état + policy optimale ensuite). **Off-policy**.

### Q-Table
Table stockant les Q-values de toutes les paires state-action. Lignes = states, colonnes = actions. Exemple grid world :

| State/Action | Up   | Down | Left | Right |
| ------------ | ---- | ---- | ---- | ----- |
| S1           | -1.0 | 0.0  | -0.5 | 0.2   |
| S2           | 0.0  | 1.0  | 0.0  | -0.3  |
| S3           | 0.5  | -0.5 | 1.0  | 0.0   |
| S4           | -0.2 | 0.0  | -0.3 | 1.0   |

### Update Rule (basée sur l'équation de Bellman)
```
Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
```
- `α` (alpha) = **learning rate** (poids de l'info nouvelle).
- `r` = reward reçu.
- `γ` (gamma) = **discount factor**.
- `max(Q(s', a'))` = Q-value max du prochain état s' (⇒ off-policy).

**Exemple de calcul** : S1, action Right → S2, r=0.5, α=0.1, γ=0.9, max Q(S2)=1.0.
```
Q(S1, Right) = 0.2 + 0.1 * [0.5 + 0.9*1.0 - 0.2]
             = 0.2 + 0.1 * 1.2 = 0.2 + 0.12 = 0.32
```

### Algorithme (étapes)
1. **Initialization** (Q-table, souvent zéros).
2. **Choose an Action** (balance exploration/exploitation).
3. **Take Action and Observe** (nouveau state + reward).
4. **Update Q-value** (update rule).
5. **Update State**.
6. **Iteration** jusqu'à convergence.

### Exploration-Exploitation Trade-off
- **Exploration** : essayer de nouvelles actions.
- **Exploitation** : choisir les actions à haut reward connu.

**Epsilon-Greedy Strategy** : action aléatoire avec proba `ε`, action greedy (Q max) avec proba `1-ε`.
- **High Epsilon (ex 0.9)** : plus d'exploration (début).
- **Low Epsilon (ex 0.1)** : plus d'exploitation (expérience acquise).

### Data Assumptions
- **Markov Property** : le prochain état dépend seulement de l'état + action actuels (pas de l'historique).
- **Stationary Environment** : dynamique (transitions, rewards) constante dans le temps.

---

## 5.2 SARSA (State-Action-Reward-State-Action)

RL **model-free**, **on-policy**. Diff clé vs Q-learning : met à jour le Q-value avec le Q-value de l'action **réellement prise** dans le prochain état (selon la policy courante), pas le max.

### Update Rule
```
Q(s, a) <- Q(s, a) + α * (r + γ * Q(s', a') - Q(s, a))
```
- `Q(s', a')` = Q-value du prochain state-action pair, déterminé par la policy courante (⇒ on-policy).

### Algorithme (étapes)
1. Initialization (Q-table).
2. Choose an Action `a` (ex epsilon-greedy).
3. Take Action and Observe (`s'`, `r`).
4. **Choose Next Action `a'`** selon la policy courante (clé du on-policy).
5. Update Q-value pour (s, a).
6. Update State and Action : `s = s'`, `a = a'`.
7. Iteration jusqu'à convergence.

### On-Policy vs Off-Policy
🎯 **Exam — distinction majeure** :
- **SARSA = on-policy** : apprend la valeur de la policy courante (y compris les steps d'exploration). Plus **conservateur/sûr et stable**, évite les actions risquées.
- **Q-learning = off-policy** : apprend la policy optimale indépendamment de la policy suivie (utilise `max`). Plus **exploratoire**, trouve parfois l'optimal plus efficacement.

### Stratégies exploration-exploitation en SARSA
- **Epsilon-Greedy** : aléatoire avec ε, greedy avec 1-ε ⇒ exploration plus prudente en SARSA.
- **Softmax** : probabilités assignées selon les Q-values (Q haut = proba haute) ⇒ exploration plus lisse/nuancée.

### Convergence et Parameter Tuning
- **Learning Rate (α)** : α haut = updates rapides mais instables ; α bas = convergence stable mais lente.
- **Discount Factor (γ)** : γ haut (≈1) = rewards long terme ; γ bas = rewards immédiats.
- Tuning via grid search ou cross-validation. Convergence garantie sous conditions (α suffisamment petit, toutes les paires state-action visitées une infinité de fois).

### Data Assumptions
- **Markov Property** et **Stationary Environment** (comme Q-learning).

---

# 6. Introduction to Deep Learning

DL = sous-ensemble du ML utilisant des ANNs à multiples couches (« deep »), inspirés du cerveau humain. Apprend automatiquement les features (vs manual feature engineering du ML classique) ⇒ hierarchical representations.

Motivations : **Solving Complex Problems** et **Mimicking the Human Brain**.

## Concepts importants
- **Artificial Neural Networks (ANNs)** : nœuds/**neurons** interconnectés en couches ; chaque connexion a un **weight** (force). Apprend en ajustant les weights.
- **Layers** :
  - **Input Layer** : reçoit les données initiales.
  - **Hidden Layers** : calculs + extraction de features (plusieurs = patterns complexes).
  - **Output Layer** : produit le résultat final.
- **Activation Functions** : introduisent la **non-linéarité**. Communes :
  - **Sigmoid** : squash vers [0, 1].
  - **ReLU (Rectified Linear Unit)** : 0 pour input négatif, input pour positif.
  - **Tanh (Hyperbolic Tangent)** : squash vers [−1, 1].
- **Backpropagation** : calcule le gradient de la loss function par rapport aux weights, puis les met à jour dans la direction minimisant la loss.
- **Loss Function** : mesure l'erreur predictions vs targets. Régression ⇒ **mean squared error (MSE)** ; classification ⇒ **cross-entropy loss**.
- **Optimizer** : détermine la mise à jour des weights via les gradients. Populaires : **SGD (Stochastic Gradient Descent)**, **Adam**, **RMSprop**.
- **Hyperparameters** : fixés avant l'entraînement (learning rate, nombre de hidden layers, neurons par couche).

🎯 **Exam — activation functions** : Sigmoid [0,1] / Tanh [−1,1] centré 0 / ReLU (0 si négatif, sinon input) / Softmax = distribution de probabilité (output multi-classes).

---

## 6.1 Perceptrons

Bloc fondamental des neural networks ; modèle simplifié d'un neurone biologique, décisions basiques.

Composants :
- **Input Values (x1...xn)** : features.
- **Weights (w1...wn)** : force/importance de chaque input (positifs ou négatifs).
- **Summation Function (∑)** : `∑(wi * xi)`.
- **Bias (b)** : décale l'activation function (permet activation même si tous inputs = 0).
- **Activation Function (f)** : non-linéarité, output selon threshold.
- **Output (y)** : typiquement binaire (0/1).

### Exemple « Play Tennis »
Inputs encodés : Outlook (Sunny=0, Overcast=1, Rainy=2), Temperature (Hot=0, Mild=1, Cool=2), Humidity (High=0, Normal=1), Wind (Weak=0, Strong=1).
Weights : w1=0.3, w2=0.2, w3=−0.4, w4=−0.2 ; bias b=0.1.
Step activation : `f(x) = 1 if x > 0 else 0`.

Jour : Outlook=0, Temp=1, Humidity=0, Wind=0.
```
Weighted sum = (0.3*0)+(0.2*1)+(-0.4*0)+(-0.2*0) = 0.2
+ bias = 0.2 + 0.1 = 0.3
f(0.3) = 1  ⇒ Play Tennis
```

### Limitations
Un **single-layer perceptron** ne peut apprendre que des decision boundaries **linéaires** ⇒ incapable de résoudre les problèmes non linéairement séparables. Exemple classique : le **XOR problem** (impossible de séparer par une seule ligne droite).

---

## 6.2 Neural Networks (Multi-Layer Perceptrons / MLPs)

Pour dépasser les limites du single-layer perceptron : réseaux à multiples couches = **MLPs** (input layer + un ou plusieurs hidden layers + output layer).

- **Neuron** : unité de calcul ; reçoit inputs, applique weights + bias, puis activation function. Contrairement au perceptron (step function), peut utiliser sigmoid, ReLU, tanh ⇒ relations non-linéaires + outputs continus.
- **Input Layer** : chaque neuron = une feature.
- **Hidden Layers** : chaque neuron (1) reçoit les inputs de la couche précédente, (2) fait la somme pondérée, (3) ajoute un bias, (4) applique l'activation function. Multiples hidden layers ⇒ abstractions croissantes.
- **Output Layer** : nombre de neurons dépend de la tâche.
  - Binary classification ⇒ **1 output neuron** (activation **Sigmoid**).
  - Multi-class classification ⇒ **1 neuron par classe** (activation **Softmax**).

**Power of Multiple Layers** : les MLPs apprennent des decision boundaries non-linéaires ⇒ résolvent le XOR problem ; structure hiérarchique = features de plus en plus complexes.

### Types d'Activation Functions (rappel)
- **Sigmoid** [0,1] : historiquement populaire, aujourd'hui moins utilisé (**vanishing gradients**).
- **ReLU** : simple, très utilisé, entraînement plus rapide, meilleure performance.
- **Tanh** [−1,1] : comme sigmoid mais centré à 0.
- **Softmax** : output layer multi-classes, vecteur de scores → distribution de probabilité.

### Training MLPs = Backpropagation + Gradient Descent

**Backpropagation** (calcule les gradients) :
1. **Forward Pass** : input → output.
2. **Calculate Error** : loss function (predicted vs target).
3. **Backward Pass** : propage l'erreur en arrière, gradient par rapport aux weights/biases via la **chain rule** du calcul.
4. **Update Weights and Biases** (via optimizer type gradient descent).

**Gradient Descent** (utilise les gradients pour minimiser la loss) :
1. **Initialize Weights and Biases** (aléatoire).
2. **Calculate Gradient** (via backpropagation).
3. **Update Weights and Biases** : soustraire une fraction du gradient (fraction = **learning rate**).
4. **Repeat** jusqu'à convergence.

🎯 **Exam** : Backpropagation calcule les gradients ; gradient descent les utilise pour mettre à jour les paramètres. Le learning rate contrôle la taille du pas.

---

## 6.3 Convolutional Neural Networks (CNNs)

Neural networks spécialisés pour données en **grille** (images). Excellent pour capturer les **spatial hierarchies of features** ⇒ image recognition, object detection, image segmentation.

Trois types de couches :
- **Convolutional Layers** : cœur du CNN. Appliquent des **filters** apprenables qui glissent sur l'input, calculant le **dot product** filter↔input à chaque position ⇒ extraction de features (edges, corners, textures). Sortie = **feature map**. Plusieurs filters par couche.
- **Pooling Layers** : réduisent la dimensionnalité des feature maps (moins coûteux, moins d'overfitting) ; downsampling par fenêtre. Types : **max pooling** et **average pooling**.
- **Fully Connected Layers** : comme dans les MLPs, chaque neuron connecté à tous ; en fin de réseau pour le raisonnement high-level et les prédictions.

Convolutional + pooling alternées ⇒ hiérarchie de features ; sortie finale flattened → fully connected layers.

### Hierarchical Feature Learning
- **Initial Layers** : features simples/low-level (edges, blobs).
- **Intermediate Layers** : patterns plus complexes (corners en combinant des edges).
- **Deeper Layers** : high-level features (shapes, object parts, ex roues/fenêtres/voitures).
- Exemple digit "7" : layer 1 = bords/edges ; layer 2 = intérieur/structure.

### Data Assumptions
- **Grid-Like Data Structure** : images = grilles 2D (height, width, channels RGB) ; vidéos = 3D (+ time).
- **Spatial Hierarchy of Features** : lower-level (early layers) → higher-level (deeper layers).
- **Feature Locality** : relations pertinentes surtout dans les voisinages locaux ; filters focalisés sur petites régions (**receptive fields**).
- **Feature Stationarity** : une feature garde son sens quelle que soit sa position ⇒ **weight sharing** (même filter appliqué partout).
- **Sufficient Data and Normalization** : CNNs data-hungry (gros datasets labellisés, sinon overfitting) ; input normalisé (ex pixels [0,1] ou [−1,1]).

🎯 **Exam** : Weight sharing ⇒ feature stationarity ; pooling ⇒ réduction de dimension + robustesse aux translations ; feature map = sortie d'un convolutional filter.

---

## 6.4 Recurrent Neural Networks (RNNs)

Conçus pour données **séquentielles** (l'ordre compte). Ont une « mémoire » des inputs passés via des **recurrent connections** (boucles) ⇒ capturent les dépendances temporelles. Usages : NLP, speech recognition, time series.

À chaque time step, le module prend : (1) l'input courant, (2) le **hidden state** du step précédent. Il produit : (1) l'output du step courant, (2) un hidden state mis à jour. Exemple "The cat sat on the mat" : hidden state initial ≈ 0, accumulation du contexte mot par mot.

### The Vanishing Gradient Problem
Pendant l'entraînement par **backpropagation through time (BPTT)**, les gradients propagés en arrière deviennent de plus en plus petits (multiplication répétée de gradients < 1 ⇒ diminution exponentielle) ⇒ le réseau n'apprend pas les **long-term dependencies** (les weights des inputs anciens reçoivent des updates minimes).

### LSTMs et GRUs (résolvent le vanishing gradient via gating)
**LSTM (Long Short-Term Memory)** — memory cells + **3 gates** :
- **Input gate** : régule l'entrée de nouvelle information.
- **Forget gate** : contrôle ce qui est retenu/écarté de la memory cell.
- **Output gate** : détermine ce qui sort vers le prochain time step.

**GRU (Gated Recurrent Unit)** — alternative plus simple, **2 gates** :
- **Update gate** : combien du hidden state précédent est retenu.
- **Reset gate** : combien du hidden state précédent est combiné à l'input courant.
- Performance comparable aux LSTMs, plus efficace computationnellement.

### Bidirectional RNNs
Traitent la séquence dans **les deux sens** (forward + backward) simultanément ⇒ capturent contexte passé ET futur. Deux RNNs (gauche→droite et droite→gauche), hidden states combinés à chaque step.

🎯 **Exam** : LSTM = 3 gates (input/forget/output) ; GRU = 2 gates (update/reset) ; vanishing gradient = obstacle aux long-term dependencies dans les RNNs.

---

# 7. Introduction to Generative AI

Génère du **nouveau contenu** ressemblant à l'output humain (texte, images, musique, code), vs AI traditionnelle qui reconnaît/classe/prédit.

Processus : **Training** (apprend les patterns statistiques d'un grand dataset) → **Generation** (échantillonne depuis la distribution apprise) → **Evaluation** (qualité, originalité, ressemblance).

## Types de modèles Generative AI
- **Generative Adversarial Networks (GANs)** : deux réseaux en compétition — un **generator** (crée des samples) et un **discriminator** (distingue réel vs généré) ; processus adversarial ⇒ réalisme croissant.
- **Variational Autoencoders (VAEs)** : apprennent une représentation compressée (latent space) pour générer ; bons pour capturer la structure sous-jacente, génération contrôlée/diverse.
- **Autoregressive Models** : génèrent séquentiellement, un élément à la fois selon les précédents (ex text generation mot par mot).
- **Diffusion Models** : ajoutent du bruit jusqu'au bruit pur, puis apprennent à inverser le processus.

## Concepts importants
- **Latent Space** : représentation cachée/compressée capturant les features essentielles (points similaires proches). Ex VAEs.
- **Sampling** : générer en tirant depuis la distribution apprise (choisir valeurs dans le latent space → output space).
- **Mode Collapse** : le generator ne produit qu'une variété limitée d'outputs (manque de diversité, coincé dans un « mode »).
- **Overfitting** : apprend trop bien le training data (bruit inclus) ⇒ limite créativité/originalité.
- **Evaluation Metrics** :
  - **Inception Score (IS)** : qualité + diversité d'images générées (clarté + diversité des classes prédites).
  - **Fréchet Inception Distance (FID)** : compare distributions générées vs réelles ; **FID bas = meilleur**.
  - **BLEU score** (text generation) : similarité texte généré vs référence (fluency, accuracy).

---

## 7.1 Large Language Models (LLMs)

Type d'AI comprenant et générant du texte humain, entraîné sur d'énormes quantités de texte. Tâches : translation, summarization, question answering, creative writing. Basés sur les **transformers**, capturent les dépendances longue portée via **self-attention**. Entraînement coûteux ⇒ hardware spécialisé (**GPUs**, **TPUs**).

Trois caractéristiques :
- **Massive Scale** : des milliards, voire trillions de paramètres.
- **Few-Shot Learning** : nouvelles tâches avec quelques exemples seulement.
- **Contextual Understanding** : compréhension du contexte.

### Concepts clés (tableau)
| Concept | Description |
| --- | --- |
| **Transformer Architecture** | Traite des phrases entières **en parallèle** ⇒ plus rapide/efficace que les RNNs. |
| **Tokenization** | Conversion du texte en **tokens** (mots, subwords, ou caractères). |
| **Embeddings** | Représentations numériques des tokens capturant le sens sémantique (mots similaires = embeddings proches en espace haute dimension). |
| **Encoders and Decoders** | Encoders traitent l'input (capturent le sens) ; decoders génèrent l'output. |
| **Self-Attention Mechanism** | Calcule des attention scores entre mots ⇒ dépendances longue portée. |
| **Training** | Massive text data + **unsupervised learning**, minimise l'erreur via **gradient descent**. |

- **Transformer Architecture** : innovation = **self-attention** ; traitement parallèle (vs RNN séquentiel).
- **Tokenization** : ex "I love artificial intelligence" → `["I", "love", "artificial", "intelligence"]`.
- **Embeddings** : "king" et "queen" plus proches que "king" et "table".
- **Encoders/Decoders** : l'encoder traite l'input, le decoder génère depuis sa sortie.
- **Self-attention** ("Attention is All You Need") : attention scores entre chaque paire de mots ; ex "The cat sat on the mat, which was blue" → "which" réfère à "mat" malgré la distance.
- **Training** : unsupervised learning, minimise la différence predictions vs texte réel via une variante de gradient descent.

🎯 **Exam** : Les transformers = base des LLMs ; self-attention pondère l'importance des mots ; traitement parallèle vs RNN séquentiel.

---

## 7.2 Diffusion Models

Modèles génératifs produisant des images haute qualité. Vs GANs/VAEs : utilisent l'**ajout et le retrait de bruit** pour apprendre la data distribution. Images, audio, etc.

### Text-to-image (ex "a cat in a hat")
Intègrent un **text encoder** (ex **Transformer** ou **CLIP**) pour convertir le texte en représentation latente conditionnant le denoising.
1. **Text Encoding** : prompt → vecteur haute dimension (conditioning input).
2. **Conditioning the Denoising Process** : le denoising network prédit le bruit à retirer, aligné sur le prompt (loss modifiée avec un terme mesurant l'écart image↔text embedding).
3. **Sampling Process** : démarre du bruit pur ; à chaque step, le network utilise l'image bruitée + le text embedding.
4. **Final Image Generation** : après assez de steps, image cohérente avec le prompt.

### Forward Process (ajout de bruit / "noising")
```
x_T = q(x_T | x_0)
```
- `x_0` = données originales, `x_T` = bruit pur, `q(x_T | x_0)` = distribution des données bruitées.
Étapes intermédiaires : `x_t = q(x_t | x_{t-1})` (`t` de 0 à T).

### Reverse Process (retrait de bruit / "denoising")
```
x_{t-1} = p_θ(x_{t-1} | x_t)
```
- `p_θ` = distribution apprise (paramètres `θ`). Entraîné à minimiser la différence bruit prédit vs réel, via **MSE** :
```
L = E[||ε - ε_pred||^2]
```
- `ε` = bruit réel, `ε_pred` = bruit prédit.

### Noise Schedule
Détermine la quantité de bruit ajoutée à chaque step. Schedule linéaire courant :
```
β_t = β_min + (t / T) * (β_max - β_min)
```
- `β_t` = variance du bruit au step t ; `β_min`/`β_max` = variances min/max.

### Denoising Network
Neural network prédisant le bruit à chaque step ; typiquement **CNN profond** ou **transformer**. Input = `x_t`, output = bruit prédit.

### Training (étapes)
1. Initialize the Model (`θ`).
2. Forward Process (ajouter bruit via schedule).
3. Reverse Process (entraîner à prédire le bruit).
4. Loss Calculation (bruit prédit vs réel).
5. Parameter Update (gradient descent).
6. Iterate (multiples epochs jusqu'à convergence).

### Sampling
```
x_0 = p_θ(x_0 | x_T)
```
1. Start with Noise (`x_T`).
2. Iterative Denoising (de T à 1).
3. Final Sample (`x_0` = image générée).

### Data Assumptions
- **Markov Property** : chaque step (forward et reverse) dépend seulement du step immédiatement précédent.
- **Static Data Distribution** : distribution fixe durant l'entraînement.
- **Smoothness Assumption** : performent mieux si la distribution est lisse (petits changements input → petits changements output).

🎯 **Exam** : Diffusion = forward (noising) + reverse (denoising) ; loss = MSE sur le bruit ; text-to-image via encoder CLIP/Transformer ; Markov property.

---

# 8. Skills Assessment (questions officielles + réponses validées)

> Module entièrement théorique ; l'évaluation teste la compréhension. Réponses = champ `user_answer` validé.

1. **Q (id 2709)** : Quel algorithme probabiliste, basé sur le Bayes' theorem, est communément utilisé pour la classification (spam filtering, sentiment analysis) et connu pour sa simplicité, efficacité et bonne performance réelle ?
   **R : Naive Bayes**

2. **Q (id 2710)** : Quelle technique de dimensionality reduction transforme des données haute dimension en représentation basse dimension tout en préservant un max d'information originale, largement utilisée pour feature extraction, data visualization et noise reduction ?
   **R : Principal Component Analysis (PCA)**

3. **Q (id 2711)** : Quel algorithme de reinforcement learning model-free apprend une policy optimale en estimant le Q-value (expected cumulative reward pour une action dans un état + policy optimale ensuite), directement par essai-erreur ?
   **R : Q-Learning**

4. **Q (id 2712)** : Quelle est l'unité de calcul fondamentale des neural networks qui reçoit des inputs, les traite via weights et bias, et applique une activation function ? Contrairement au perceptron (step function), elle peut utiliser sigmoid, ReLU, tanh.
   **R : Neuron**

5. **Q (id 2713)** : Quelle architecture de deep learning, capable de traiter des données séquentielles comme le texte en capturant les dépendances longue portée via self-attention, forme la base des LLMs (translation, summarization, question answering, creative writing) ?
   **R : Transformer**

---

# 🎯 Questions d'examen probables

1. **Q** : Quel est l'ordre d'emboîtement AI/ML/DL/Neural Nets ?
   **R** : AI ⊃ ML ⊃ Neural Nets ⊃ Deep Learning.

2. **Q** : Différence entre L1 et L2 regularization ?
   **R** : L1 = pénalité sur la valeur absolue des coefficients (Σ|w|) ; L2 = pénalité sur le carré des coefficients (Σw²).

3. **Q** : Precision vs Recall ?
   **R** : Precision = vrais positifs / toutes prédictions positives ; Recall = vrais positifs / tous positifs réels. F1 = moyenne harmonique des deux.

4. **Q** : Quelle est la fonction de sortie de la logistic regression et sa plage ?
   **R** : La sigmoid function, `P(x) = 1/(1+e^-z)`, output ∈ [0, 1] ; threshold par défaut 0.5.

5. **Q** : Trois critères de split d'un decision tree ?
   **R** : Gini impurity, entropy, information gain (on choisit la feature au plus haut information gain).

6. **Q** : Overfitting vs underfitting ?
   **R** : Overfitting = apprend trop bien le training (bruit inclus), mauvaise généralisation ; underfitting = modèle trop simple, mauvais partout.

7. **Q** : Qu'est-ce que le kernel trick des SVM et citez 3 kernels ?
   **R** : Mapper les données vers une dimension supérieure où elles sont linéairement séparables. Kernels : Polynomial, RBF (Radial Basis Function), Sigmoid.

8. **Q** : Bayes' theorem — formule ?
   **R** : `P(A|B) = [P(B|A) * P(A)] / P(B)`. Types Naive Bayes : Gaussian (continu), Multinomial (discret/texte), Bernoulli (binaire).

9. **Q** : Deux méthodes pour choisir K en K-means ?
   **R** : Elbow Method (WCSS) et Silhouette Analysis (score ∈ [−1,1], on prend le K au plus haut average silhouette score).

10. **Q** : En PCA, que représentent eigenvectors et eigenvalues ?
    **R** : Eigenvectors = directions des principal components (variance max) ; eigenvalues = quantité de variance expliquée. Équation `C * v = λ * v` (C = covariance matrix).

11. **Q** : Q-learning vs SARSA (on/off-policy) ?
    **R** : Q-learning = off-policy (utilise `max Q(s', a')`, plus exploratoire) ; SARSA = on-policy (utilise l'action réellement prise `Q(s', a')`, plus conservateur/sûr).

12. **Q** : Rôle du discount factor γ en RL ?
    **R** : ∈ [0,1], importance des rewards futurs. γ=0 = immédiats seulement ; γ=1 = tous futurs égaux.

13. **Q** : Trois activation functions et leurs plages ?
    **R** : Sigmoid [0,1], Tanh [−1,1] (centré 0), ReLU (0 si négatif sinon input). Softmax = distribution de probabilité pour multi-classes.

14. **Q** : Backpropagation vs gradient descent ?
    **R** : Backpropagation calcule les gradients de la loss par rapport aux weights (chain rule) ; gradient descent utilise ces gradients pour mettre à jour les paramètres (pas = learning rate).

15. **Q** : Quel problème affecte les RNNs et comment le résout-on ?
    **R** : Le vanishing gradient problem (empêche d'apprendre les long-term dependencies), résolu par LSTM (3 gates : input/forget/output) et GRU (2 gates : update/reset).

16. **Q** : Composants d'un GAN ?
    **R** : Un generator (crée des samples) et un discriminator (distingue réel/généré), en compétition adversariale.

17. **Q** : Loss function typique du reverse process d'un diffusion model ?
    **R** : MSE sur le bruit : `L = E[||ε - ε_pred||^2]`. Le modèle suppose la Markov property.

18. **Q** : Pourquoi les CNNs utilisent le weight sharing ?
    **R** : Pour la feature stationarity — le même filter détecte une feature quelle que soit sa position dans l'image. Pooling (max/average) réduit la dimension et donne la robustesse aux translations.
