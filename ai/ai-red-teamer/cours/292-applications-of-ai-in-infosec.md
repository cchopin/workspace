# Applications of AI in InfoSec (module 292)

## En bref
Module **pratique** : construire 4 modèles AI/ML pour l'infosec. (1) **Spam Classifier** SMS avec `Multinomial Naive Bayes` + `CountVectorizer` (bag-of-words). (2) **Network Anomaly Detection** multi-classe avec `RandomForestClassifier` sur `NSL-KDD`. (3) **Malware Classifier** via `byteplots` (images grayscale de binaires PE) avec un `CNN ResNet50` pré-entraîné (transfer learning, PyTorch). (4) **Skills Assessment** : sentiment analysis sur `IMDB` (positif/négatif).
Environnement : `Miniconda` (gestion de packages `conda`) + `JupyterLab` (notebooks stateful). Librairies clés : `scikit-learn`, `PyTorch`/`torchvision`, `pandas`, `numpy`, `nltk`, `joblib`, `matplotlib`, `seaborn`.
Chaque modèle est **uploadé** à un evaluation portal (endpoints locaux 8000/8001/8002/5000) qui renvoie un **flag** si le modèle atteint le seuil de performance requis.
Métriques centrales : `accuracy`, `precision`, `recall`, `F1-score`, `confusion matrix`, `classification_report`.

---

## 1. Environment Setup

### Deux options
- **The Playground** : VM virtuelle fournie par HTB, expose Jupyter sur `http://<VM-IP>:8888`. Accès via VPN HTB ou PwnBox. Peu performante (suffisante pour suivre, pas pour expérimenter).
- **Environnement local** : recommandé si hardware suffisant. Besoin minimum : **au moins 4 GB de RAM et 4 CPU cores**.

### Miniconda
`Miniconda` = installeur minimal de la distribution `Anaconda`. Fournit le package manager `conda` + un Python core, sans la suite complète de libs data science (contrairement à `Anaconda`).

Raisons du choix (🎯 Exam) :
- **Performance** : packages optimisés.
- **Package Management** : `conda` résout les dépendances (crucial en deep learning).
- **Environment Isolation** : environnements isolés par projet.

Version affichée dans le module : `conda 24.9.2`.

**Installation :**
```powershell-session
# Windows via Scoop
C:\> Set-ExecutionPolicy RemoteSigned -scope CurrentUser
C:\> irm get.scoop.sh | iex
C:\> scoop bucket add extras
C:\> scoop install miniconda3
C:\> conda --version   # conda 24.9.2
```
```shell-session
# MacOS via Homebrew
[!bash!]$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
[!bash!]$ brew install --cask miniconda
```
```shell-session
# Linux
[!bash!]$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
[!bash!]$ chmod +x Miniconda3-latest-Linux-x86_64.sh
[!bash!]$ ./Miniconda3-latest-Linux-x86_64.sh -b -u
[!bash!]$ eval "$(/home/$USER/miniconda3/bin/conda shell.$(ps -p $$ -o comm=) hook)"
```

### Init & configuration des channels
```shell-session
[!bash!]$ conda init                       # modifie .bashrc / .zshrc
[!bash!]$ conda config --add channels defaults
[!bash!]$ conda config --add channels conda-forge
[!bash!]$ conda config --add channels nvidia    # seulement si GPU nvidia
[!bash!]$ conda config --add channels pytorch
[!bash!]$ conda config --set channel_priority strict
```

**Désactiver l'activation auto de `base`** (modifie le fichier `condarc`) :
```shell-session
[!bash!]$ conda config --set auto_activate_base false
```

### Environnements virtuels
```shell-session
[!bash!]$ conda create -n ai python=3.11     # crée env "ai" avec Python 3.11
[!bash!]$ conda activate ai                   # active -> prompt (ai)
[!bash!]$ conda deactivate                    # désactive
```
Bénéfices : Dependency Isolation, Clean Project Structure, Reproducibility, System Stability.

### Packages essentiels (🎯 Exam : liste exacte)
```shell-session
[!bash!]$ conda install -y numpy scipy pandas scikit-learn matplotlib seaborn transformers datasets tokenizers accelerate evaluate optimum huggingface_hub nltk category_encoders
[!bash!]$ conda install -y pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
[!bash!]$ pip install requests requests_toolbelt
```
Mise à jour (ne met à jour QUE les packages conda, pas ceux installés via pip) :
```shell-session
[!bash!]$ conda update --all
```
> Note : mélanger `pip` et `conda` augmente le risque de conflits de dépendances.

**🎯 Q lab 2733** : Familiarisation avec le Playground VM. `user_answer` = **done**.

---

## 2. JupyterLab

Environnement interactif web (code, data, visualisation). Installation :
```shell-session
[!bash!]$ conda install -y jupyter jupyterlab notebook ipykernel
[!bash!]$ jupyter lab        # ouvre l'interface dans le navigateur
```

Types de cellules : **Code cells** (Python, R, Julia), **Markdown cells**, **Raw cells**.
Exécuter une cellule : `Shift + Enter`. Sauvegarder : `Ctrl + S`.

**🎯 Exam — Notebook stateful** : les variables/fonctions/imports d'une cellule restent disponibles dans toutes les cellules suivantes tant que le **kernel** tourne. Exécuter les cellules dans le désordre peut donner des résultats inattendus. C'est l'inverse d'un modèle **stateless** (chaque exécution isolée).

**Restarting the Kernel** : Menu `Kernel` -> `Restart Kernel` (efface variables/fonctions/imports en mémoire, préserve les outputs) ou `Restart Kernel and Clear All Outputs`.

Exemple de plot :
```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.DataFrame({
    "column1": np.random.rand(50),
    "column2": np.random.rand(50) * 10
})
print(data.head())
plt.scatter(data["column1"], data["column2"])
plt.xlabel("Column 1"); plt.ylabel("Column 2"); plt.title("Scatter Plot")
plt.show()
```

---

## 3. Python Libraries for AI

### Scikit-learn
Construit sur `NumPy`, `SciPy`, `Matplotlib`. API cohérente : `fit()` / `predict()` / `fit_transform()`.

- **Supervised Learning** : Linear Regression, Logistic Regression, SVM, Decision Trees, Naive Bayes, Ensemble Methods (Random Forests, Gradient Boosting).
- **Unsupervised Learning** : Clustering (K-Means, DBSCAN), Dimensionality Reduction (PCA, t-SNE).
- Model Selection/Evaluation, Data Preprocessing.

**Feature scaling** :
- `StandardScaler` : retire la moyenne, scale à variance unitaire.
- `MinMaxScaler` : scale dans un range (typiquement 0-1).
- `RobustScaler` : scaling robuste aux outliers.
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```
**Encoding catégoriel** :
- `OneHotEncoder` : colonnes binaires (0/1) par catégorie.
- `LabelEncoder` : entier unique par catégorie.
```python
from sklearn.preprocessing import OneHotEncoder
encoder = OneHotEncoder()
X_encoded = encoder.fit_transform(X)
```
**Missing values** :
- `SimpleImputer` : remplace via une stratégie (mean, median, most_frequent).
- `KNNImputer` : impute via k-Nearest Neighbors.
```python
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy='mean')
X_imputed = imputer.fit_transform(X)
```
**Model selection/evaluation** :
```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5)   # cross-validation à 5 folds

from sklearn.metrics import accuracy_score
accuracy = accuracy_score(y_test, y_pred)
```
Métriques : `accuracy_score` (classif), `mean_squared_error` (régression), `precision_score`, `recall_score`, `f1_score` (classes déséquilibrées).

**Training/prediction** :
```python
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(C=1.0)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

### PyTorch
Développé par Facebook AI Research. Features : Deep Learning, **Dynamic Computational Graphs** (vs graphes statiques de TensorFlow), GPU Support, TorchVision, `autograd` (Automatic Differentiation).

**Tensors** (multi-dim arrays, similaires aux NumPy arrays mais GPU-capables) :
```python
import torch
x = torch.tensor([1.0, 2.0, 3.0])
if torch.cuda.is_available():
    x = x.to('cuda')
```
**Sequential API** :
```python
import torch.nn as nn
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10),
    nn.Softmax(dim=1)
)
```
**Module class** (modèles complexes) :
```python
import torch.nn as nn
class CustomModel(nn.Module):
    def __init__(self):
        super(CustomModel, self).__init__()
        self.layer1 = nn.Linear(784, 128)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(128, 10)
        self.softmax = nn.Softmax(dim=1)
    def forward(self, x):
        x = self.layer1(x); x = self.relu(x)
        x = self.layer2(x); x = self.softmax(x)
        return x
model = CustomModel()
```
**Optimizers** : `Adam`, `SGD`, `RMSprop`.
```python
import torch.optim as optim
optimizer = optim.Adam(model.parameters(), lr=0.001)
```
**Loss functions** :
- `CrossEntropyLoss` : classif multi-classe.
- `BCEWithLogitsLoss` : classif binaire.
- `MSELoss` : régression.
```python
loss_fn = nn.CrossEntropyLoss()
```
**Accuracy manuelle** :
```python
def accuracy(output, target):
    _, predicted = torch.max(output, 1)
    correct = (predicted == target).sum().item()
    return correct / len(target)
```
**Training loop** (structure canonique 🎯) :
```python
for epoch in range(epochs):
    for batch in range(num_batches):
        x_batch, y_batch = get_batch(batch)
        y_pred = model(x_batch)            # forward pass
        loss = loss_fn(y_pred, y_batch)    # loss
        optimizer.zero_grad()             # reset gradients
        loss.backward()                    # backward pass
        optimizer.step()                   # update poids
```
**Dataset / DataLoader** :
```python
from torch.utils.data import Dataset, DataLoader
class CustomDataset(Dataset):
    def __init__(self, data, labels):
        self.data = data; self.labels = labels
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]
dataset = CustomDataset(data, labels)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
```
**Save/Load** :
```python
torch.save(model.state_dict(), 'model.pth')
model = CustomModel()
model.load_state_dict(torch.load('model.pth'))
model.eval()   # mode évaluation
```

---

## 4. Datasets & Data Preprocessing

### Types de datasets
Tabular Data, Image Data (pixel arrays), Text Data, Time Series Data.

### Attributs d'un "bon" dataset (🎯 Exam — tableau)
| Attribut | Description |
|---|---|
| `Relevance` | Données pertinentes au problème. |
| `Completeness` | Peu de valeurs manquantes. |
| `Consistency` | Format/structure uniformes (ex. dates `YYYY-MM-DD`). |
| `Quality` | Données exactes, sans erreurs. |
| `Representativeness` | Représentatif de la population cible. |
| `Balance` | Équilibré (surtout classif) — oversampling/undersampling/synthétique. |
| `Size` | Assez grand pour capturer la complexité. |

### Le dataset `demo_dataset.csv`
CSV de network log entries. Colonnes :
- `log_id` : identifiant unique.
- `source_ip` : IP source.
- `destination_port` : port destination.
- `protocol` : protocole (`TCP`, `TLS`, `SSH`...).
- `bytes_transferred` : total octets transférés.
- `threat_level` : **0 = normal, 1 = low-threat, 2 = high-threat**.

Défis : mix numérique/catégoriel ; valeurs manquantes/invalides ; strings non-numériques dans colonnes numériques ; `threat_level` contient valeurs inconnues (`?`, `-1`).

**Chargement & exploration** :
```python
import pandas as pd
data = pd.read_csv("./demo_dataset.csv")
print(data.head())        # premières lignes
print(data.info())        # types + non-null counts
print(data.isnull().sum())# comptage des valeurs nulles par colonne
```

### Identification des valeurs invalides
```python
import re
def is_valid_ip(ip):
    pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    return bool(pattern.match(ip))
invalid_ips = data[~data['source_ip'].astype(str).apply(is_valid_ip)]

def is_valid_port(port):
    try:
        port = int(port); return 0 <= port <= 65535   # range valide 0-65535
    except ValueError:
        return False
invalid_ports = data[~data['destination_port'].apply(is_valid_port)]

valid_protocols = ['TCP', 'TLS', 'SSH', 'POP3', 'DNS', 'HTTPS', 'SMTP', 'FTP', 'UDP', 'HTTP']
invalid_protocols = data[~data['protocol'].isin(valid_protocols)]

def is_valid_bytes(bytes):
    try:
        bytes = int(bytes); return bytes >= 0
    except ValueError:
        return False
invalid_bytes = data[~data['bytes_transferred'].apply(is_valid_bytes)]

def is_valid_threat_level(threat_level):
    try:
        threat_level = int(threat_level); return 0 <= threat_level <= 2
    except ValueError:
        return False
invalid_threat_levels = data[~data['threat_level'].apply(is_valid_threat_level)]
```

### Traitement : dropping
```python
data = data.drop(invalid_ips.index, errors='ignore')
data = data.drop(invalid_ports.index, errors='ignore')
data = data.drop(invalid_protocols.index, errors='ignore')
data = data.drop(invalid_bytes.index, errors='ignore')
data = data.drop(invalid_threat_levels.index, errors='ignore')
print(data.describe(include='all'))
```
> 🎯 Après le drop, il ne reste que **77 clean entries**. `errors='ignore'` gère l'overlap entre index.

### Traitement : imputing
Étape 1 — convertir valeurs corrompues en `NaN` :
```python
import pandas as pd, numpy as np, re
from ipaddress import ip_address
df = pd.read_csv('demo_dataset.csv')

invalid_ips = ['INVALID_IP', 'MISSING_IP']
invalid_ports = ['STRING_PORT', 'UNUSED_PORT']
invalid_bytes = ['NON_NUMERIC', 'NEGATIVE']
invalid_threat = ['?']
df.replace(invalid_ips + invalid_ports + invalid_bytes + invalid_threat, np.nan, inplace=True)

df['destination_port'] = pd.to_numeric(df['destination_port'], errors='coerce')
df['bytes_transferred'] = pd.to_numeric(df['bytes_transferred'], errors='coerce')
df['threat_level']      = pd.to_numeric(df['threat_level'], errors='coerce')

def is_valid_ip(ip):
    pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?\d?\d)\.){3}(25[0-5]|2[0-4]\d|[01]?\d?\d)$')
    if pd.isna(ip) or not pattern.match(str(ip)):
        return np.nan
    return ip
df['source_ip'] = df['source_ip'].apply(is_valid_ip)
```
Étape 2 — imputation (median pour numérique, most_frequent pour catégoriel) :
```python
from sklearn.impute import SimpleImputer
numeric_cols = ['destination_port', 'bytes_transferred', 'threat_level']
categorical_cols = ['protocol']

num_imputer = SimpleImputer(strategy='median')
df[numeric_cols] = num_imputer.fit_transform(df[numeric_cols])

cat_imputer = SimpleImputer(strategy='most_frequent')
df[categorical_cols] = cat_imputer.fit_transform(df[categorical_cols])
```
Étape 3 — imputation avancée (`KNNImputer` avec `n_neighbors=5`, ou `IterativeImputer`) :
```python
from sklearn.impute import KNNImputer
knn_imputer = KNNImputer(n_neighbors=5)
df[numeric_cols] = knn_imputer.fit_transform(df[numeric_cols])
```
Étape 4 — domain knowledge :
```python
valid_protocols = ['TCP', 'TLS', 'SSH', 'POP3', 'DNS', 'HTTPS', 'SMTP', 'FTP', 'UDP', 'HTTP']
df.loc[~df['protocol'].isin(valid_protocols), 'protocol'] = df['protocol'].mode()[0]
df['source_ip'] = df['source_ip'].fillna('0.0.0.0')          # IP défaut
df['destination_port'] = df['destination_port'].clip(lower=0, upper=65535)
```

---

## 5. Data Transformation

### Encoding catégoriel
- `OneHotEncoder` : features binaires indicatrices (pas d'ordre implicite).
- `LabelEncoder` : entiers (peut impliquer un ordre non désiré).
- `HashingEncoder` / méthodes fréquentielles : high-cardinality.

**One-Hot Encoding du `protocol`** (🎯 exam : `sparse_output=False`, `handle_unknown='ignore'`) :
```python
from sklearn.preprocessing import OneHotEncoder
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
encoded = encoder.fit_transform(df[['protocol']])
encoded_df = pd.DataFrame(encoded, columns=encoder.get_feature_names_out(['protocol']))
df = pd.concat([df.drop('protocol', axis=1), encoded_df], axis=1)
```

### Handling skewed data — log transform
`np.log1p` = log(1+x), défini même en 0 :
```python
import numpy as np
df["bytes_transferred"] = np.log1p(df["bytes_transferred"])  # +1 pour éviter log(0)
```

### Data splitting (🎯 Exam — ratios)
- **Training Set** : ~60-80% (fit le modèle).
- **Validation Set** : ~10-20% (tuning hyperparamètres, model selection).
- **Test Set** : ~10-20% (uniquement à la fin).
```python
from sklearn.model_selection import train_test_split
X = df.drop("threat_level", axis=1)
y = df["threat_level"]
# 80% train / 20% test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1337)
# depuis les 80%, 25% -> validation => 0.8 * 0.25 = 0.2 (20% global) ; reste 60% train
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=1337)
```
> 🎯 `test_size=0.25` du 2e split = 25% du subset train (qui vaut 80% du total) => 20% global en validation, 60% en train.

---

## 6. Metrics for Evaluating a Model (🎯 Exam — formules exactes)

| Métrique | Formule | Notes |
|---|---|---|
| **Accuracy** | `(TP + TN) / (all instances)` | Trompeur en cas de class imbalance. Ex : 99% ham -> modèle "tout ham" = accuracy 0.99 mais 0 spam détecté. |
| **Precision** | `TP / (TP + FP)` | Qualité des positifs prédits. Haute precision = moins de fausses alertes. |
| **Recall** | `TP / (TP + FN)` | Complétude de la détection. Haut recall = moins de cas critiques manqués. |
| **F1-score** | `2 * (precision * recall) / (precision + recall)` | Moyenne harmonique ; utile en class imbalance. |

Exemples numériques du module : `accuracy: 0.9950`, `precision: 0.9949`, `recall: 0.9950`, `F1-score: 0.9949`.
Autres : contexte `accuracy: 0.9750`, `precision: 0.9300`, `recall: 0.9100`, `F1-score: 0.9200`.

**Additional considerations** : `Specificity` (identification des négatifs), `AUC` (Area Under the ROC Curve), `Matthews Correlation Coefficient` (datasets très déséquilibrés), `Confusion Matrix`.

**Trade-offs** : threat detection favorise le **recall** (ne pas rater une menace) ; ressources limitées favorisent la **precision** (moins de fausses alertes à traiter).

---

## 7. Cas d'usage 1 — Spam Classification (Naive Bayes)

### Théorie Bayes
```python
P(A|B) = (P(B|A) * P(A)) / P(B)
P(Spam|Features) = (P(Features|Spam) * P(Spam)) / P(Features)
```
**Naive assumption** : features indépendantes entre elles (given the class) :
```python
P(Features|Spam) = P(feature1|Spam) * P(feature2|Spam) * ... * P(featureN|Spam)
```
**Exemple calcul (🎯 apprécié en QCM)** :
P(Spam)=0.3, P(Not Spam)=0.7, P(F1|Spam)=0.4, P(F2|Spam)=0.5, P(F1|Not Spam)=0.2, P(F2|Not Spam)=0.3.
```
P(F1,F2|Spam)     = 0.4 * 0.5 = 0.2
P(F1,F2|Not Spam) = 0.2 * 0.3 = 0.06
P(F1,F2) = (0.2*0.3) + (0.06*0.7) = 0.06 + 0.042 = 0.102
P(Spam|F1,F2)     = 0.06 / 0.102 ≈ 0.588
P(Not Spam|F1,F2) = 0.042 / 0.102 ≈ 0.412
```
=> 0.588 > 0.412 => classé **spam**.

### Dataset
**SMS Spam Collection dataset** (UCI, Almeida & Yamakami + Gómez Hidalgo, 2011 ACM Symposium on Document Engineering). **5,574 messages** labellisés `ham` (légitime) ou `spam`. Format TSV. Sources : Grumbletext, NUS SMS Corpus, thèse de Caroline Tag.

**Download & extraction** :
```python
import requests, zipfile, io
url = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
response = requests.get(url)
if response.status_code == 200:
    print("Download successful")
with zipfile.ZipFile(io.BytesIO(response.content)) as z:
    z.extractall("sms_spam_collection")
import os
extracted_files = os.listdir("sms_spam_collection")   # fichier : SMSSpamCollection
```
**Loading** (TSV, pas de header) :
```python
import pandas as pd
df = pd.read_csv("sms_spam_collection/SMSSpamCollection",
                 sep="\t", header=None, names=["label", "message"])
print(df.head()); print(df.describe()); print(df.info())
print("Missing values:\n", df.isnull().sum())
print("Duplicate entries:", df.duplicated().sum())
df = df.drop_duplicates()
```

### Preprocessing (NLTK)
Downloads NLTK requis : `punkt`, `punkt_tab`, `stopwords`.
```python
import nltk
nltk.download("punkt"); nltk.download("punkt_tab"); nltk.download("stopwords")
```
Pipeline texte (ordre 🎯 Exam) :
```python
# 1. Lowercasing
df["message"] = df["message"].str.lower()

# 2. Remove punctuation & numbers, GARDE $ et !
import re
df["message"] = df["message"].apply(lambda x: re.sub(r"[^a-z\s$!]", "", x))

# 3. Tokenization
from nltk.tokenize import word_tokenize
df["message"] = df["message"].apply(word_tokenize)

# 4. Stop words removal
from nltk.corpus import stopwords
stop_words = set(stopwords.words("english"))
df["message"] = df["message"].apply(lambda x: [w for w in x if w not in stop_words])

# 5. Stemming (Porter)
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
df["message"] = df["message"].apply(lambda x: [stemmer.stem(w) for w in x])

# 6. Rejoin tokens en string (pour vectorization)
df["message"] = df["message"].apply(lambda x: " ".join(x))
```
> 🎯 On garde `$` et `!` car ils portent du contexte spam (montant, emphase).

### Feature extraction — CountVectorizer (bag-of-words)
Paramètres (🎯 Exam) :
- `min_df=1` : terme présent dans au moins 1 document.
- `max_df=0.9` : exclut les termes présents dans >90% des documents.
- `ngram_range=(1, 2)` : unigrams **et** bigrams.
```python
from sklearn.feature_extraction.text import CountVectorizer
vectorizer = CountVectorizer(min_df=1, max_df=0.9, ngram_range=(1, 2))
X = vectorizer.fit_transform(df["message"])
y = df["label"].apply(lambda x: 1 if x == "spam" else 0)  # spam=1, ham=0
```
3 étapes de `CountVectorizer` : Tokenization -> Building Vocabulary (via min_df/max_df) -> Vectorization. Les bigrams capturent un ordre local (ex : `free prize`) ; l'ordre global est perdu.

### Training — MultinomialNB + Pipeline + GridSearchCV
```python
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

pipeline = Pipeline([
    ("vectorizer", vectorizer),
    ("classifier", MultinomialNB())
])

# grid sur alpha (smoothing factor, gère les mots inconnus / proba nulle)
param_grid = {"classifier__alpha": [0.01, 0.1, 0.15, 0.2, 0.25, 0.5, 0.75, 1.0]}
grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring="f1")   # 5-fold CV, scoring F1
grid_search.fit(df["message"], y)
best_model = grid_search.best_estimator_
print("Best model parameters:", grid_search.best_params_)
```
> 🎯 Classifieur = **Multinomial Naive Bayes**. Hyperparamètre tuné = **`alpha`** (Laplace/Lidstone smoothing). Scoring = **F1**, cv=5.

### Evaluation
Confusion matrix du module : **889 TN, 5 FP, 0 FN, 140 TP**.
```python
new_messages = [
    "Congratulations! You've won a $1000 Walmart gift card. Go to http://bit.ly/1234 to claim now.",
    "Hey, are we still meeting up for lunch today?",
    "Urgent! Your account has been compromised. Verify your details here: www.fakebank.com/verify",
    "Reminder: Your appointment is scheduled for tomorrow at 10am.",
    "FREE entry in a weekly competition to win an iPad. Just text WIN to 80085 now!",
]
import numpy as np, re
def preprocess_message(message):
    message = message.lower()
    message = re.sub(r"[^a-z\s$!]", "", message)
    tokens = word_tokenize(message)
    tokens = [w for w in tokens if w not in stop_words]
    tokens = [stemmer.stem(w) for w in tokens]
    return " ".join(tokens)

processed_messages = [preprocess_message(m) for m in new_messages]
X_new = best_model.named_steps["vectorizer"].transform(processed_messages)
predictions = best_model.named_steps["classifier"].predict(X_new)
prediction_probabilities = best_model.named_steps["classifier"].predict_proba(X_new)

for i, msg in enumerate(new_messages):
    prediction = "Spam" if predictions[i] == 1 else "Not-Spam"
    spam_probability = prediction_probabilities[i][1]
    ham_probability  = prediction_probabilities[i][0]
    print(f"Message: {msg}\nPrediction: {prediction}")
    print(f"Spam Probability: {spam_probability:.2f}")
    print(f"Not-Spam Probability: {ham_probability:.2f}")
```
Résultats attendus : gift card -> Spam 1.00 ; lunch -> Not-Spam 1.00 ; fakebank -> Spam 0.94 ; appointment -> Not-Spam 1.00 ; iPad competition -> Spam 1.00.

### Sauvegarde — joblib
```python
import joblib
model_filename = 'spam_detection_model.joblib'
joblib.dump(best_model, model_filename)
# reload
loaded_model = joblib.load(model_filename)
new_data_processed = [preprocess_message(m) for m in new_messages]
predictions = loaded_model.predict(new_data_processed)
```
> `joblib` = sérialisation/désérialisation optimisée pour gros arrays NumPy / modèles scikit-learn.

### Upload & flag
```python
import requests, json
url = "http://localhost:8000/api/upload"      # spam = port 8000
model_file_path = "spam_detection_model.joblib"
with open(model_file_path, "rb") as model_file:
    files = {"model": model_file}
    response = requests.post(url, files=files)
print(json.dumps(response.json(), indent=4))
```
**🎯 Q lab 2729** — flag : **`HTB{sp4m_cla55if13r_3v4lu4t0r}`**

---

## 8. Cas d'usage 2 — Network Anomaly Detection (Random Forest)

### Random Forests
Ensemble de `decision trees`. Classif = **majority voting** ; régression = **moyenne**. Réduit l'overfitting vs un seul arbre.
3 concepts : **Bootstrapping** (sampling avec remplacement), **Tree Construction** (subset aléatoire de features à chaque split), **Voting**.
Pour l'anomaly detection : entraîné sur données normales ; points à faible confiance = anomalies potentielles.

### Dataset NSL-KDD
Raffine `KDD Cup 1999` (retire redondances, corrige déséquilibres). Permet binaire (normal vs abnormal) et multi-classe. Fichier utilisé : `KDD+.txt`.

**Download** :
```python
import requests, zipfile, io
url = "https://academy.hackthebox.com/storage/modules/292/KDD_dataset.zip"
response = requests.get(url)
z = zipfile.ZipFile(io.BytesIO(response.content))
z.extractall('.')
```
**Imports & loading** :
```python
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import seaborn as sns, matplotlib.pyplot as plt

file_path = r'KDD+.txt'
columns = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login', 'is_guest_login',
    'count', 'srv_count', 'serror_rate', 'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate',
    'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'attack', 'level'
]
df = pd.read_csv(file_path, names=columns)
print(df.head())
```
Labels : `attack`, `level`. Catégoriels : `protocol_type`, `service`, `flag`.

### Preprocessing
**Binary target** :
```python
df['attack_flag'] = df['attack'].apply(lambda a: 0 if a == 'normal' else 1)  # 0 normal, 1 attaque
```
**Multi-class target** (🎯 Exam — mapping des 5 classes) :
```python
dos_attacks = ['apache2', 'back', 'land', 'neptune', 'mailbomb', 'pod',
               'processtable', 'smurf', 'teardrop', 'udpstorm', 'worm']
probe_attacks = ['ipsweep', 'mscan', 'nmap', 'portsweep', 'saint', 'satan']
privilege_attacks = ['buffer_overflow', 'loadmdoule', 'perl', 'ps',
                     'rootkit', 'sqlattack', 'xterm']
access_attacks = ['ftp_write', 'guess_passwd', 'http_tunnel', 'imap',
                  'multihop', 'named', 'phf', 'sendmail', 'snmpgetattack',
                  'snmpguess', 'spy', 'warezclient', 'warezmaster',
                  'xclock', 'xsnoop']
def map_attack(attack):
    if attack in dos_attacks:        return 1
    elif attack in probe_attacks:    return 2
    elif attack in privilege_attacks:return 3
    elif attack in access_attacks:   return 4
    else:                            return 0
df['attack_map'] = df['attack'].apply(map_attack)
```
Codes : **0=Normal, 1=DoS, 2=Probe, 3=Privilege Escalation, 4=Access**.

**Encoding catégoriel via `pd.get_dummies`** (one-hot) :
```python
features_to_encode = ['protocol_type', 'service']
encoded = pd.get_dummies(df[features_to_encode])
```
**Numeric features sélectionnées** :
```python
numeric_features = [
    'duration', 'src_bytes', 'dst_bytes', 'wrong_fragment', 'urgent', 'hot',
    'num_failed_logins', 'num_compromised', 'root_shell', 'su_attempted',
    'num_root', 'num_file_creations', 'num_shells', 'num_access_files',
    'num_outbound_cmds', 'count', 'srv_count', 'serror_rate',
    'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
    'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
    'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate',
    'dst_host_serror_rate', 'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
    'dst_host_srv_rerror_rate'
]
```
**Assemblage** :
```python
train_set = encoded.join(df[numeric_features])
multi_y = df['attack_map']
```

### Splitting (🎯 : 2 splits, random_state=1337)
```python
# 80% train / 20% test
train_X, test_X, train_y, test_y = train_test_split(train_set, multi_y, test_size=0.2, random_state=1337)
# validation = 30% du train
multi_train_X, multi_val_X, multi_train_y, multi_val_y = train_test_split(train_X, train_y, test_size=0.3, random_state=1337)
```

### Training
```python
rf_model_multi = RandomForestClassifier(random_state=1337)
rf_model_multi.fit(multi_train_X, multi_train_y)
```

### Evaluation (validation puis test)
Metrics avec `average='weighted'` :
```python
multi_predictions = rf_model_multi.predict(multi_val_X)
accuracy  = accuracy_score(multi_val_y, multi_predictions)
precision = precision_score(multi_val_y, multi_predictions, average='weighted')
recall    = recall_score(multi_val_y, multi_predictions, average='weighted')
f1        = f1_score(multi_val_y, multi_predictions, average='weighted')

conf_matrix = confusion_matrix(multi_val_y, multi_predictions)
class_labels = ['Normal', 'DoS', 'Probe', 'Privilege', 'Access']
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_labels, yticklabels=class_labels)
plt.title('Network Anomaly Detection - Validation Set')
plt.xlabel('Predicted'); plt.ylabel('Actual'); plt.show()
print(classification_report(multi_val_y, multi_predictions, target_names=class_labels))

# Test set final
test_multi_predictions = rf_model_multi.predict(test_X)
test_accuracy  = accuracy_score(test_y, test_multi_predictions)
test_precision = precision_score(test_y, test_multi_predictions, average='weighted')
test_recall    = recall_score(test_y, test_multi_predictions, average='weighted')
test_f1        = f1_score(test_y, test_multi_predictions, average='weighted')
```
Confusion matrix test (module) : ~15,349 Normal, 10,708 DoS, 2,788 Probe, 703 Access.

### Sauvegarde & upload
```python
import joblib
joblib.dump(rf_model_multi, 'network_anomaly_detection_model.joblib')
```
```python
url = "http://localhost:8001/api/upload"   # network anomaly = port 8001
```
**🎯 Q lab 2730** — flag : **`HTB{n3tw0rk_tr4ff1c_4n0m4ly_d3t3ct0r}`**

---

## 9. Cas d'usage 3 — Malware Image Classification (CNN ResNet50)

### Principe des byteplots
Chaque **byte** du binaire PE = **1 pixel** grayscale : `0` -> noir, `255` -> blanc, intermédiaire -> gris. Encodage sans perte (reconstruction exacte du binaire). Avantage : manipuler des **images**, pas des binaires malveillants dangereux. Basé sur arxiv 2010.16108 et le paper malimg (dl.acm.org 2016908).

### Dataset malimg
**9,339 images**, **25 malware families** (1 dossier = 1 famille, nom = famille). Format PNG grayscale.
```shell-session
[!bash!]$ wget https://www.kaggle.com/api/v1/datasets/download/ikrambenabd/malimg-original -O malimg.zip
[!bash!]$ unzip malimg.zip
[!bash!]$ ls malimg_paper_dataset_imgs
```
Familles (extrait) : Adialer.C, Agent.FYI, Allaple.A, Allaple.L, Alueron.gen!J, Autorun.K, C2LOP.gen!g, C2LOP.P, Dialplatform.B, Dontovo.A, Fakerean, Instantaccess, Lolyda.AA1/AA2/AA3/AT, Malex.gen!J, Obfuscator.AD, Rbot!gen, Skintrim.N, Swizzor.gen!E/I, VB.AT, Wintrim.BX, Yuner.A. (Allaple.A et Allaple.L = les plus fréquentes.)

**Class distribution** :
```python
import os, matplotlib.pyplot as plt, seaborn as sns
DATA_BASE_PATH = "./malimg_paper_dataset_imgs/"
dist = {}
for mlw_class in os.listdir(DATA_BASE_PATH):
    mlw_dir = os.path.join(DATA_BASE_PATH, mlw_class)
    dist[mlw_class] = len(os.listdir(mlw_dir))
```

### Preprocessing & DataLoaders
Split 80-20 via `split-folders` :
```shell-session
[!bash!]$ pip3 install split-folders
```
```python
import splitfolders
DATA_BASE_PATH = "./malimg_paper_dataset_imgs/"
TARGET_BASE_PATH = "./newdata/"
TRAINING_RATIO = 0.8
TEST_RATIO = 1 - TRAINING_RATIO
splitfolders.ratio(input=DATA_BASE_PATH, output=TARGET_BASE_PATH, ratio=(TRAINING_RATIO, 0, TEST_RATIO))
```
> Crée `./newdata/{train,val,test}`. `ratio=(0.8, 0, 0.2)` -> val vide. Comptes : test=**1880**, train=**7459**, val=**0**.

**Transforms PyTorch** (🎯 Exam : valeurs exactes) :
```python
from torchvision import transforms
transform = transforms.Compose([
    transforms.Resize((75, 75)),                       # resize 75x75
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],   # normalisation ImageNet
                         std=[0.229, 0.224, 0.225])
])
```
**ImageFolder + DataLoader** :
```python
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
import os
BASE_PATH = "./newdata/"
train_dataset = ImageFolder(root=os.path.join(BASE_PATH, "train"), transform=transform)
test_dataset  = ImageFolder(root=os.path.join(BASE_PATH, "test"),  transform=transform)

TRAIN_BATCH_SIZE = 1024
TEST_BATCH_SIZE = 1024
train_loader = DataLoader(train_dataset, batch_size=TRAIN_BATCH_SIZE, shuffle=True,  num_workers=2)
test_loader  = DataLoader(test_dataset,  batch_size=TEST_BATCH_SIZE,  shuffle=False, num_workers=2)
```
Fonction combinée (retourne aussi `n_classes = len(train_dataset.classes)`) :
```python
def load_datasets(base_path, train_batch_size, test_batch_size):
    transform = transforms.Compose([
        transforms.Resize((75, 75)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    train_dataset = ImageFolder(root=os.path.join(base_path, "train"), transform=transform)
    test_dataset  = ImageFolder(root=os.path.join(base_path, "test"),  transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True,  num_workers=2)
    test_loader  = DataLoader(test_dataset,  batch_size=test_batch_size,  shuffle=False, num_workers=2)
    n_classes = len(train_dataset.classes)
    return train_loader, test_loader, n_classes
```

### Le modèle — ResNet50 (transfer learning)
`ResNet50` : proposé 2015 (arxiv 1512.03385), **50 layers**, ~**23 millions de paramètres**. On charge des poids pré-entraînés puis on **freeze toutes les couches sauf la dernière** (fully connected) qu'on remplace.
```python
import torch.nn as nn
import torchvision.models as models
HIDDEN_LAYER_SIZE = 1000

class MalwareClassifier(nn.Module):
    def __init__(self, n_classes):
        super(MalwareClassifier, self).__init__()
        self.resnet = models.resnet50(weights='DEFAULT')   # poids pré-entraînés
        for param in self.resnet.parameters():
            param.requires_grad = False                    # freeze
        num_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Sequential(                    # nouvelle tête
            nn.Linear(num_features, HIDDEN_LAYER_SIZE),
            nn.ReLU(),
            nn.Linear(HIDDEN_LAYER_SIZE, n_classes)
        )
    def forward(self, x):
        return self.resnet(x)

model = MalwareClassifier(25)   # 25 classes (ou n_classes dynamique)
```

### Training / Evaluation
Loss = `CrossEntropyLoss`, optimizer = `Adam` (lr par défaut).
```python
import torch, time
def train(model, train_loader, n_epochs, verbose=False):
    model.train()
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters())
    training_data = {"accuracy": [], "loss": []}
    for epoch in range(n_epochs):
        running_loss = 0; n_total = 0; n_correct = 0
        checkpoint = time.time() * 1000
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            _, predicted = outputs.max(1)
            n_total += labels.size(0)
            n_correct += predicted.eq(labels).sum().item()
            running_loss += loss.item()
        epoch_loss = running_loss / len(train_loader)
        epoch_accuracy = compute_accuracy(n_correct, n_total)
        training_data["accuracy"].append(epoch_accuracy)
        training_data["loss"].append(epoch_loss)
    return training_data

def save_model(model, path):          # sauvegarde via TorchScript
    model_scripted = torch.jit.script(model)
    model_scripted.save(path)

def predict(model, test_data):
    model.eval()
    with torch.no_grad():
        output = model(test_data)
        _, predicted = torch.max(output.data, 1)
    return predicted

def compute_accuracy(n_correct, n_total):
    return round(100 * n_correct / n_total, 2)

def evaluate(model, test_loader):
    model.eval(); n_correct = 0; n_total = 0
    with torch.no_grad():
        for data, target in test_loader:
            predicted = predict(model, data)
            n_total += target.size(0)
            n_correct += (predicted == target).sum().item()
    return compute_accuracy(n_correct, n_total)
```
> 🎯 Sauvegarde CNN = **`torch.jit.script` (TorchScript)** en `.pth`, PAS `joblib` (joblib = modèles scikit-learn).

**Script principal** (🎯 hyperparamètres) :
```python
DATA_PATH = "./newdata/"
N_EPOCHS = 10
TRAINING_BATCH_SIZE = 512
TEST_BATCH_SIZE = 1024
HIDDEN_LAYER_SIZE = 1000
MODEL_FILE = "malware_classifier.pth"

train_loader, test_loader, n_classes = load_datasets(DATA_PATH, TRAINING_BATCH_SIZE, TEST_BATCH_SIZE)
model = MalwareClassifier(n_classes)
training_information = train(model, train_loader, N_EPOCHS, verbose=True)
save_model(model, MODEL_FILE)
accuracy = evaluate(model, test_loader)
print(f"[i] Inference accuracy: {accuracy}%.")
```
Résultat module : **inference accuracy = 88.54%** après 10 epochs (train accuracy ~96% à l'epoch 9-10). Sur le Playground, **3 epochs suffisent** pour atteindre le seuil (~10 min/epoch).

### Upload & flag
```python
url = "http://localhost:8002/api/upload"   # malware = port 8002
model_file_path = "malware_classifier.pth"
```
**🎯 Q lab 2731** — flag : **`HTB{9569648083a8106ba057bbbe2d00d8ec}`**

---

## 10. Skills Assessment — Sentiment Analysis (IMDB)

**IMDB dataset** (Maas et al., 2011) : reviews de films IMDB annotées pour sentiment analysis. **50,000 reviews** (split 50/50 train/test). Objectif : prédire review positive (**1**) ou négative (**0**). Techniques identiques au spam classifier (text -> vectorization -> classifieur) ; applicable aussi à la text moderation.

Download : `https://academy.hackthebox.com/storage/modules/292/skills_assessment_data.zip`.
Upload :
```python
url = "http://localhost:5000/api/upload"      # skills assessment = port 5000
model_file_path = "skills_assessment.joblib"
```
**🎯 Q lab 2732** — flag : **`HTB{s3nt1m3nt_4n4lys1s_d4t4}`**

---

## Récapitulatif des 4 modèles (🎯 tableau de synthèse)

| Cas | Modèle | Librairie | Features / Input | Métrique clé | Endpoint | Save |
|---|---|---|---|---|---|---|
| Spam | Multinomial Naive Bayes | scikit-learn | CountVectorizer bag-of-words (uni+bigrams) | F1 (GridSearch alpha) | 8000 | joblib |
| Network anomaly | RandomForestClassifier | scikit-learn | get_dummies + numeric NSL-KDD | precision/recall/F1 weighted | 8001 | joblib |
| Malware | CNN ResNet50 (transfer) | PyTorch/torchvision | images 75x75 normalisées | accuracy (88.54%) | 8002 | torch.jit.script (.pth) |
| Sentiment (IMDB) | (text classifier, ex. NB) | scikit-learn | text vectorisé | — | 5000 | joblib |

---

## 🎯 Questions d'examen probables

1. **Q : Quel classifieur est utilisé pour la détection de spam SMS et quel hyperparamètre est tuné ?**
   R : `MultinomialNB` (Multinomial Naive Bayes) ; hyperparamètre `alpha` (smoothing) via `GridSearchCV(cv=5, scoring="f1")` sur `[0.01, 0.1, 0.15, 0.2, 0.25, 0.5, 0.75, 1.0]`.

2. **Q : Dans le preprocessing du spam, quels caractères spéciaux sont conservés et pourquoi ?**
   R : `$` et `!` (`re.sub(r"[^a-z\s$!]", "", x)`) car ils portent du contexte spam (montant / emphase).

3. **Q : Quelle transformation applique-t-on à une feature skewed comme `bytes_transferred` ?**
   R : Log transform via `np.log1p` (log(1+x), défini en 0).

4. **Q : Formules exactes de precision, recall et F1 ?**
   R : precision = `TP/(TP+FP)` ; recall = `TP/(TP+FN)` ; F1 = `2*(precision*recall)/(precision+recall)`.

5. **Q : Pourquoi l'accuracy est trompeuse en cas de class imbalance ?**
   R : Ex. 99% ham : un modèle prédisant toujours "ham" atteint accuracy 0.99 mais recall 0 sur le spam. D'où precision/recall/F1.

6. **Q : Quel algorithme pour la network anomaly detection et sur quel dataset ?**
   R : `RandomForestClassifier` (ensemble de decision trees, majority voting) sur `NSL-KDD` (raffinement de KDD Cup 1999), fichier `KDD+.txt`.

7. **Q : Quelles sont les 5 classes multi-class de NSL-KDD et leurs codes ?**
   R : 0=Normal, 1=DoS, 2=Probe, 3=Privilege Escalation, 4=Access (fonction `map_attack`).

8. **Q : Comment sont encodées les features catégorielles `protocol_type` et `service` dans le cas network ?**
   R : One-hot encoding via `pd.get_dummies(df[['protocol_type','service']])`, joint aux numeric features (`encoded.join(df[numeric_features])`).

9. **Q : Qu'est-ce qu'un byteplot / image de malware ?**
   R : Chaque byte du binaire PE = 1 pixel grayscale (0=noir, 255=blanc). Encodage sans perte, permet de classifier sans manipuler le binaire malveillant.

10. **Q : Quel modèle CNN, combien de couches/paramètres, et quelle technique d'accélération ?**
    R : `ResNet50` (50 couches, ~23M paramètres), transfer learning avec poids `DEFAULT` pré-entraînés + freeze de toutes les couches sauf la dernière (fully connected remplacée : Linear(→1000)+ReLU+Linear(1000→n_classes)).

11. **Q : Quels transforms de preprocessing pour les images malware ?**
    R : `Resize((75,75))`, `ToTensor()`, `Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])` (valeurs ImageNet).

12. **Q : Comment sauver un modèle scikit-learn vs un modèle PyTorch ?**
    R : scikit-learn -> `joblib.dump` (.joblib) ; PyTorch CNN -> `torch.jit.script(model).save(path)` (TorchScript, .pth). Alternative PyTorch : `torch.save(model.state_dict())`.

13. **Q : Détail du double train_test_split (ratios) ?**
    R : 1er split test_size=0.2 (80/20) ; 2e split sur les 80% avec test_size=0.25 -> 0.8×0.25=0.2 en validation, soit 60% train / 20% val / 20% test. `random_state=1337`.

14. **Q : Différence loss function classif binaire vs multi-classe en PyTorch ?**
    R : `BCEWithLogitsLoss` (binaire), `CrossEntropyLoss` (multi-classe), `MSELoss` (régression).

15. **Q : Quel est le comportement "stateful" d'un notebook Jupyter ?**
    R : Variables/fonctions/imports persistent entre cellules tant que le kernel tourne ; exécuter dans le désordre peut donner des résultats inattendus. `Restart Kernel` efface la mémoire.

### Flags des labs (récap)
- Q2733 (Playground) : `done`
- Q2729 (Spam) : `HTB{sp4m_cla55if13r_3v4lu4t0r}`
- Q2730 (Network anomaly) : `HTB{n3tw0rk_tr4ff1c_4n0m4ly_d3t3ct0r}`
- Q2731 (Malware) : `HTB{9569648083a8106ba057bbbe2d00d8ec}`
- Q2732 (Sentiment/IMDB) : `HTB{s3nt1m3nt_4n4lys1s_d4t4}`
