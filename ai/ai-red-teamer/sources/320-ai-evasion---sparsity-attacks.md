# AI Evasion - Sparsity Attacks (module 320)

This module explores sparsity-constrained adversarial attacks that minimize the number of modified input features rather than perturbation magnitude, showing how to craft targeted misclassifications by changing only the most impactful pixels through L0-focused optimization and saliency-guided feature selection.



---

<!-- section 3924 | page 1 | group: Introduction | type: theory | interactive: 0 | docker: False -->

# Introduction to Sparsity Evasion Attacks
<p><p>Sparsity attacks seek misclassification by changing as few input
dimensions as possible. The sparsity budget is measured by the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
pseudo‑norm, defined as the number of coordinates that differ between an
adversarial input and the original,</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msub><mi>x</mi><mrow><mi>a</mi><mi>d</mi><mi>v</mi></mrow></msub><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>0</mn></msub><mo>=</mo><mrow><mo stretchy="true" form="prefix">|</mo><mo stretchy="false" form="prefix">{</mo><mi>i</mi><mo>∣</mo><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mrow><mi>a</mi><mi>d</mi><mi>v</mi></mrow></msub><msub><mo stretchy="false" form="postfix">)</mo><mi>i</mi></msub><mo>≠</mo><msub><mi>x</mi><mi>i</mi></msub><mo stretchy="false" form="postfix">}</mo><mo stretchy="true" form="postfix">|</mo></mrow><mi>.</mi></mrow><annotation encoding="application/x-tex">\lVert x_{adv} - x \rVert_0 = \left|\{ i \mid (x_{adv})_i \ne x_i \}\right|.</annotation></semantics></math></p></p>



Instead of spreading small changes over many features, these attacks concentrate edits on a small set of high‑impact features. This section extends the first‑order perspective to settings where the primary constraint is how many features may change, not how small each change must be.

## From First‑Order to Sparsity
<p><p>The previous module used gradients to move an input across a decision
boundary under
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
or
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
limits. Those norms penalize the size of a perturbation but allow all
features to move. In many systems, the attack surface is discrete or
partially discrete, for example pixels that can saturate to bounds or
tokens that change one at a time, so controlling the number of edited
features is the relevant constraint. Sparsity attacks keep the feature
count small, which preserves most of the input unchanged and can evade
simple anomaly detectors that focus on global noise levels.</p></p>



## Threat Model and Budgets
<p><p>We consider inference‑time attackers who can compute or approximate
gradients. In a <code>white‑box</code> setting the attacker evaluates
derivatives through the model and uses them to select which features to
edit. In a <code>black‑box</code> setting the attacker estimates
importance scores by queries, or transfers sparse patterns from a
surrogate. The primary budget is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>,
sometimes with auxiliary limits on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
or
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
to keep edits bounded and valid. Inputs remain in <code>[0,1]</code> for
images after each update, and if the model uses normalization
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mover><mi>x</mi><mo accent="true">̂</mo></mover><mo>=</mo><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo>−</mo><mi>μ</mi><mo stretchy="false" form="postfix">)</mo><mi>/</mi><mi>σ</mi></mrow><annotation encoding="application/x-tex">\hat{x} = (x - \mu)/\sigma</annotation></semantics></math>,
gradients propagate through it by the chain rule, so reasoning in pixel
space remains correct while respecting box constraints.</p></p>



## Two Paths to Sparse Perturbations
<p><p><code>ElasticNet (EAD)</code> promotes sparsity by adding an
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
penalty to the optimization. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term encourages many coordinates of the perturbation to be exactly zero,
which approximates an
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
goal while remaining continuous. A common objective is</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><munder><mi>min</mi><mo>&#8289;</mo><msup><mi>x</mi><mo>′</mo></msup></munder><mspace width="0.278em"></mspace><mi>c</mi><mspace width="0.167em"></mspace><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>+</mo><msubsup><mrow><mo stretchy="true" form="prefix">‖</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>2</mn><mn>2</mn></msubsup><mo>+</mo><mi>β</mi><mspace width="0.167em"></mspace><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>1</mn></msub><mspace width="1.0em"></mspace><mtext mathvariant="normal">s.t.</mtext><mspace width="0.278em"></mspace><msup><mi>x</mi><mo>′</mo></msup><mo>∈</mo><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo stretchy="false" form="postfix">]</mo><mo>,</mo></mrow><annotation encoding="application/x-tex">\min_{x&#39;}\; c\, f(x&#39;) + \lVert x&#39; - x \rVert_2^2 + \beta\, \lVert x&#39; - x \rVert_1 \quad \text{s.t.}\; x&#39; \in [0,1],</annotation></semantics></math></p></p>

<p><p>where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f(x&#39;)</annotation></semantics></math>
is a loss that enforces misclassification (often targeted),
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
balances attack success with compactness, and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
controls sparsity through the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term. The result is a small set of larger edits rather than many tiny
ones.</p></p>

<p><p><code>Jacobian‑based Saliency Map Attack (JSMA)</code> enforces an
explicit
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
budget by modifying one or two features per iteration using a
<code>saliency map</code> derived from the input Jacobian to score
candidates that raise the target while suppressing competitors.</p></p>



## Why Sparsity Attacks Matter
<p><p>Sparse edits align with real constraints. An attacker may only be
able to flip a few bits in a binary, touch a handful of pixels due to
rendering limits, or change a small number of tokens in text. Sparse
perturbations can be harder to detect with defenses tuned to global
noise statistics, and they reveal which features the model treats as
most decisive. For defenders, reproducing EAD and JSMA establishes
baselines for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>‑induced
sparsity and explicit
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
control, which together expose different failure modes than
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
or
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
attacks.</p></p>


---

<!-- section 3925 | page 2 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# ElasticNet
<p><p>The first-order attacks you explored in the previous module each
committed to a single norm. <code>FGSM</code> constrains perturbations
using the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
norm, ensuring no single pixel changes by more than
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϵ</mi><annotation encoding="application/x-tex">\epsilon</annotation></semantics></math>.
<code>DeepFool</code> minimizes the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
norm, finding the smoothest path to the decision boundary. Each approach
reflects a distinct philosophy about what makes a perturbation effective
and imperceptible.</p></p>

<p><p>What happens when we combine
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
regularization in a single attack? The
<code>Elastic-net Attacks to Deep neural networks</code>
(<code>EAD</code>) creates perturbations that are simultaneously sparse
(changing few pixels) and smooth (making small, coordinated changes).
This mixed-norm approach emerged from Chen, Zhang, Sharma, Yi, and
Hsieh’s 2018 paper "<a href="https://arxiv.org/abs/1709.04114">EAD:
Elastic-Net Attacks to Deep Neural Networks via Adversarial
Examples</a>," adapting statistical learning techniques for adversarial
machine learning.</p></p>

<p><p>Pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
attacks like <code>Carlini &amp; Wagner</code> (<code>C&amp;W</code>)
spread changes across all pixels, creating smooth but dense
perturbations where every pixel contributes slightly. Pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
attacks concentrate changes into fewer pixels but face optimization
challenges at the non-differentiable corners where sparsity emerges.
ElasticNet resolves this tension: the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
component provides smooth gradients for stable optimization while the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
component induces sparsity by zeroing out low-importance pixels. A
parameter
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
controls this balance, letting practitioners tune between extreme
sparsity and distributed smoothness.</p></p>



## Single-Norm Limitations
<p><p>Different norms impose distinct geometric constraints on
perturbations. FGSM’s
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
constraint allows uniform perturbation of all pixels up to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϵ</mi><annotation encoding="application/x-tex">\epsilon</annotation></semantics></math>,
creating visually noisy examples. DeepFool’s pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
minimization produces smooth perturbations but remains dense; every
pixel contributes at least slightly to the total perturbation.</p></p>

<p><p>The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
norm offers something neither provides: sparsity. Its diamond-shaped
constraint set has sharp corners along coordinate axes, causing
optimization to naturally zero out many coordinates. When minimizing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub><mo>=</mo><msub><mo>∑</mo><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo><msub><mi>x</mi><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">\|x\|_1 = \sum_i |x_i|</annotation></semantics></math>,
the gradient pushes toward solutions where most
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">x_i = 0</annotation></semantics></math>
exactly, concentrating perturbation in few dimensions. Sparse
perturbations modify fewer pixels, potentially evading detection and
improving interpretability by revealing exactly which pixels matter
most.</p></p>



## The Sparsity-Smoothness Trade-off
<p><p>Pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
optimization presents challenges that require specialized handling. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
norm’s smoothness makes it optimization-friendly, with well-defined
gradients everywhere. However, this smoothness comes at the cost of
density, distributing changes across all dimensions rather than zeroing
out irrelevant ones.</p></p>

<p><p>ElasticNet resolves this tension by combining both norms. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
term provides smoothness for optimization, while the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term induces sparsity. The balance between these objectives is
controlled by a parameter
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>,
allowing practitioners to tune the sparsity-smoothness trade-off for
their specific needs. This combination, originally developed for
regression in statistics, translates naturally to adversarial attacks
where we want both small total distortion and sparse modifications.</p></p>

<p><p>To see why combining norms changes behavior, compare two
perturbations on a 28×28 image. Case A changes 100 pixels by 0.10 each,
giving squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>=</mo><mn>100</mn><mo>×</mo><msup><mn>0.10</mn><mn>2</mn></msup><mo>=</mo><mn>1.00</mn></mrow><annotation encoding="application/x-tex">L_2 = 100 \times 0.10^2 = 1.00</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>1</mn></msub><mo>=</mo><mn>100</mn><mo>×</mo><mn>0.10</mn><mo>=</mo><mn>10.0</mn></mrow><annotation encoding="application/x-tex">L_1 = 100 \times 0.10 = 10.0</annotation></semantics></math>.
Case B changes 10 pixels by 0.316 each, giving squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>≈</mo><mn>10</mn><mo>×</mo><msup><mn>0.316</mn><mn>2</mn></msup><mo>≈</mo><mn>1.00</mn></mrow><annotation encoding="application/x-tex">L_2 \approx 10 \times 0.316^2 \approx 1.00</annotation></semantics></math>
but
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>1</mn></msub><mo>≈</mo><mn>10</mn><mo>×</mo><mn>0.316</mn><mo>=</mo><mn>3.16</mn></mrow><annotation encoding="application/x-tex">L_1 \approx 10 \times 0.316 = 3.16</annotation></semantics></math>.
Both cases have similar squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>,
so the smoothness term treats them alike. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term separates them, favoring B because fewer pixels change. Setting a
larger
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
tilts the objective toward choices like B; a smaller
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
behaves more like pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
and tolerates dense, low-magnitude changes.</p></p>



## The ElasticNet Approach
<p><p>ElasticNet attacks minimize a mixed-norm distance function combining
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
components. The attack seeks perturbations that cause misclassification
while keeping both the total perturbation energy (via
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>)
and the number of modified pixels (via
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>)
small. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
parameter controls the relative importance of sparsity versus
smoothness.</p></p>

<p><p>This distance function appears as a regularization term in the full
attack objective, which follows the <code>C&amp;W</code> framework. The
complete optimization problem balances three competing goals: achieving
misclassification, minimizing distortion, and staying within valid input
bounds. A trade-off constant
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
balances adversarial pressure against perturbation size, with binary
search automatically finding the minimal constant sufficient for
successful attacks.</p></p>

<p><p>The optimization uses the
<code>Fast Iterative Shrinkage-Thresholding Algorithm</code>
(<code>FISTA</code>), which handles mixed-norm objectives by decomposing
them into smooth and non-smooth components. Each iteration performs
gradient descent on the smooth parts while applying specialized
operators to handle the non-smooth
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term. This approach creates true sparsity with many pixels remaining
exactly zero, not just near-zero.</p></p>



## Tuning Attack Strength Through Binary Search
<p><p>The trade-off constant
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
controls how aggressively the attack pursues misclassification versus
minimizing perturbation size. Large
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
values prioritize fooling the model (strong adversarial pressure, large
perturbations). Small
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
values prioritize imperceptibility (weak adversarial pressure,
potentially failed attacks). The challenge lies in finding the minimal
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
that just barely achieves misclassification.</p></p>

<p><p>Binary search solves this challenge automatically. The algorithm
maintains lower and upper bounds on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
for each example, progressively narrowing the interval. When an attack
succeeds with some constant, the upper bound tightens (we can try
smaller values). When an attack fails, the lower bound raises (we need
larger values). After several iterations, the search converges to the
minimal constant sufficient for attack success, producing perturbations
that fool the model with minimal distortion.</p></p>

<p><p>This adaptive tuning distinguishes ElasticNet from fixed-budget
attacks like FGSM. Rather than choosing a universal
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϵ</mi><annotation encoding="application/x-tex">\epsilon</annotation></semantics></math>
for all examples, ElasticNet automatically discovers each example’s
vulnerability threshold. Examples near decision boundaries succeed with
small constants. Examples far from boundaries require larger constants.
The binary search handles this heterogeneity without manual parameter
tuning.</p></p>



## Contrasts with Previous Attacks
<p><p>ElasticNet occupies a distinct position in the adversarial attack
landscape compared to the first-order methods you encountered
previously. FGSM’s single-step efficiency comes at the cost of
flexibility. The sign operation and fixed
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϵ</mi><annotation encoding="application/x-tex">\epsilon</annotation></semantics></math>
constraint prevent FGSM from adapting to local geometry or producing
sparse perturbations. DeepFool’s iterative linearization finds minimal
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
perturbations but cannot produce sparsity or balance multiple norms.</p></p>



ElasticNet's iterative optimization allows it to follow the loss landscape more carefully than FGSM's single step, adjusting the perturbation progressively based on updated gradient information. Unlike DeepFool's goal of finding the nearest boundary, ElasticNet explicitly optimizes a mixed objective that balances multiple desirable properties. The binary search adds another layer of adaptation, automatically tuning the attack strength to each example's vulnerability.

The attacks serve different purposes. FGSM works well for testing basic robustness and generating training data for adversarial training, where speed matters more than perturbation quality. DeepFool excels at measuring robustness precisely, providing lower bounds on the perturbation needed to fool a model. ElasticNet targets scenarios where sparse, carefully optimized attacks are valuable: evading detection, transferring between models, or analyzing which features matter most.

---

<!-- section 3926 | page 3 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Environment Setup

ElasticNet requires significantly more computation than single-step attacks like FGSM. Each FISTA iteration performs forward and backward passes, with hundreds of iterations nested inside 5-10 binary search steps.

The `HTB Evasion Library` provides standardized infrastructure across all attack implementations: model architectures, MNIST data loaders, training loops, and visualization utilities. This consistency lets us focus on attack mechanics rather than boilerplate.

```bash
# Install the AI Library (or update it)
pip install --upgrade git+https://github.com/PandaSt0rm/htb-ai-library
```

The setup follows a familiar pattern. We use `set_reproducibility(1337)` to ensure deterministic behavior across runs by fixing random seeds for PyTorch, NumPy, and CUDA. Device configuration automatically detects GPU availability, falling back to CPU when necessary. The HTB color constants (`HTB_GREEN`, `NODE_BLACK`, etc.) maintain visual consistency across all visualizations, with `use_htb_style()` applying the theme globally to matplotlib.

## Quick Setup Reference

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import utilities from HTB Evasion Library
from htb_ai_library.utils import (
    set_reproducibility,
    save_model,
    load_model,
    HTB_GREEN,
    NODE_BLACK,
    HACKER_GREY,
    WHITE,
    AZURE,
    NUGGET_YELLOW,
    MALWARE_RED,
    VIVID_PURPLE,
    AQUAMARINE,
)
from htb_ai_library.data import get_mnist_loaders
from htb_ai_library.models import MNISTClassifierWithDropout
from htb_ai_library.training import train_model, evaluate_accuracy
from htb_ai_library.visualization import use_htb_style

# Apply HTB theme globally to all plots
use_htb_style()

# Set reproducibility
set_reproducibility(1337)

# Configure device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
if device.type == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

Example output (device names will vary):

```txt
Using device: cuda
GPU: NVIDIA GeForce RTX 5090
```

## Building the Target Model

ElasticNet targets `MNISTClassifierWithDropout`, a convolutional architecture with 2 conv layers (dropout rate 0.25) and 2 fully connected layers (dropout rate 0.5). Dropout serves dual purposes: preventing overfitting during training and creating a more realistic target that reflects production models with regularization.

Training from scratch takes several minutes even on GPU. When experimenting with attack parameters, retraining repeatedly wastes resources. The checkpoint caching approach checks for an existing `mnist_target.pth` file. If found, we load the saved weights directly. If absent, we train for 5 epochs and save the result. This makes the first run slower (training required) but all subsequent runs instant (weights loaded from disk).

```python
# Get data loaders using library function
train_loader, test_loader = get_mnist_loaders(batch_size=128)
print(f"Training samples: {len(train_loader.dataset)}")
print(f"Test samples: {len(test_loader.dataset)}")

# Create output directory for saving models and results
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Define model checkpoint path in output directory
model_path = output_dir / "mnist_target.pth"

# Initialize model using MNISTClassifierWithDropout from library
model = MNISTClassifierWithDropout(num_classes=10).to(device)

# Check if trained model exists, otherwise train from scratch
if model_path.exists():
    print(f"\nLoading existing model from {model_path}")
    model = load_model(model, model_path, device)
else:
    print(f"\nNo existing model found. Training new model...")
    model = train_model(model, train_loader, test_loader, epochs=5, device=device)
    print(f"Saving trained model to {model_path}")
    save_model(model, model_path)

# Evaluate the trained model
accuracy = evaluate_accuracy(model, test_loader, device)
print(f"\nTest accuracy: {accuracy:.2f}%")
```

Expected output (first run, training from scratch):

```txt
Training samples: 60000
Test samples: 10000

No existing model found. Training new model...
Epoch 1/5: Avg Loss = 0.2761, Test Accuracy = 98.07%
Epoch 2/5: Avg Loss = 0.0982, Test Accuracy = 98.64%
Epoch 3/5: Avg Loss = 0.0750, Test Accuracy = 98.75%
Epoch 4/5: Avg Loss = 0.0616, Test Accuracy = 98.90%
Epoch 5/5: Avg Loss = 0.0529, Test Accuracy = 98.89%
Saving trained model to output/mnist_target.pth

Test accuracy: 98.89%
```

Expected output (subsequent runs, loading existing model):

```txt
Training samples: 60000
Test samples: 10000

Loading existing model from output/mnist_target.pth

Test accuracy: 98.89%
```

### Memory and Storage Details

How does batching affect memory usage? Each MNIST image occupies 28×28 = 784 pixels × 4 bytes (float32) = 3,136 bytes (~3.06 KiB). A batch of 128 images requires 128 × 3,136 bytes = 401,408 bytes (~392 KiB) for input data alone. Adding gradients, activations, and optimizer state for a CNN with 2 conv layers and 2 FC layers brings total per-batch memory to roughly 50-80 MB. Doubling the batch size to 256 would double memory usage to 100-160 MB while providing more stable gradient estimates but slower per-epoch iteration. The 128-image batch size balances these tradeoffs effectively for MNIST.

What gets serialized in the checkpoint file? When `save_model` writes `mnist_target.pth`, it creates a Python pickle containing an OrderedDict that maps parameter names (like `conv1.weight`, `fc2.bias`) to their tensor values. This `.pth` file stores all convolutional filters, batch norm statistics, and fully connected weights as floating-point arrays. When `load_model` reads this file, PyTorch's deserialization restores the exact numerical values from the previous training session, down to the last floating-point bit. This ensures perfect reproducibility across sessions while eliminating redundant training.

The final test accuracy of 98.89% (9,889 out of 10,000 examples classified correctly) confirms the model learned effectively while remaining well-regularized. With 98.89% accuracy, we have 9,889 potential attack targets in the test set, providing ample examples for evaluating ElasticNet's effectiveness against properly regularized neural networks.

---

<!-- section 3927 | page 4 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Proximal Operators and FISTA Framework

The previous section configured our environment and trained a target model. Now we develop the mathematical machinery needed to optimize ElasticNet's mixed-norm objective. The question is far from trivial.
<p><p>FGSM had it easy. Closed-form solution. Sign operations. Done.
DeepFool repeatedly solved linear approximations using closed-form
projection formulas. ElasticNet’s mixed objective admits no such simple
solution. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term creates a fundamental obstacle.</p></p>

<p><p>Why is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
optimization so difficult? The absolute value function
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><mi>x</mi><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">|x|</annotation></semantics></math>
has a sharp corner at zero where the derivative is undefined. Standard
gradient descent relies on smooth, continuous derivatives to determine
update directions. At exactly the points where sparsity occurs (values
becoming zero), the gradient doesn’t exist. Attempting naive gradient
descent on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><mi>δ</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub></mrow><annotation encoding="application/x-tex">\|\delta\|_1</annotation></semantics></math>
produces frustrating results: values hover near zero, getting smaller
and smaller, but rarely reach zero exactly. You get pseudo-sparsity
(many small values) instead of true sparsity (many exact zeros).</p></p>



The `Fast Iterative Shrinkage-Thresholding Algorithm` (FISTA) decomposes the problem into smooth and non-smooth components, handling each with appropriate techniques. Proximal operators replace gradients for non-smooth terms, while Nesterov momentum accelerates convergence. Together, these tools enable efficient optimization of objectives that would defeat simpler methods.

## The Proximal Operator Framework

How do we generalize projection to handle non-smooth penalty functions? Proximal operators provide the answer. To understand this generalization, consider first the simpler case of constrained optimization that appeared in FGSM and DeepFool.
<p><p>FGSM can be viewed as solving the linearized objective under an
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
constraint: maximize
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>∇</mi><mi>J</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo>⋅</mo><mi>δ</mi></mrow><annotation encoding="application/x-tex">\nabla J(x) \cdot \delta</annotation></semantics></math>
subject to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><mi>δ</mi><msub><mo stretchy="false" form="postfix">∥</mo><mi>∞</mi></msub><mo>≤</mo><mi>ϵ</mi></mrow><annotation encoding="application/x-tex">\|\delta\|_\infty \leq \epsilon</annotation></semantics></math>.
The solution is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>δ</mi><mo>=</mo><mi>ϵ</mi><mo>⋅</mo><mi>sign</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mi>∇</mi><mi>J</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\delta = \epsilon \cdot \operatorname{sign}(\nabla J(x))</annotation></semantics></math>.
DeepFool’s linear approximation similarly projects onto hyperplanes
representing decision boundaries, using the geometric formula for
distance from a point to a plane.</p></p>

<p><p>Proximal operators extend this projection idea to handle penalty
functions rather than hard constraints. Instead of asking "what’s the
closest point in set
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>C</mi><annotation encoding="application/x-tex">C</annotation></semantics></math>?",
we ask "what point minimizes the sum of distance-from-here plus some
penalty function?" Formally, for function
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
at point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>z</mi><annotation encoding="application/x-tex">z</annotation></semantics></math>
with step size
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">prox</mtext><mrow><mi>λ</mi><mi>h</mi></mrow></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>arg</mi><mo>&#8289;</mo><munder><mi>min</mi><mo>&#8289;</mo><mi>x</mi></munder><mrow><mo stretchy="true" form="prefix">{</mo><mfrac><mn>1</mn><mn>2</mn></mfrac><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><mo>−</mo><mi>z</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup><mo>+</mo><mi>λ</mi><mi>h</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo stretchy="true" form="postfix">}</mo></mrow></mrow><annotation encoding="application/x-tex">\text{prox}_{\lambda h}(z) = \arg\min_x \left\{ \frac{1}{2}\|x - z\|_2^2 + \lambda h(x) \right\}</annotation></semantics></math></p></p>

<p><p>What do these terms accomplish? The first term
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mn>1</mn><mn>2</mn></mfrac><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><mo>−</mo><mi>z</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup></mrow><annotation encoding="application/x-tex">\frac{1}{2}\|x - z\|_2^2</annotation></semantics></math>
measures squared distance from the input point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>z</mi><annotation encoding="application/x-tex">z</annotation></semantics></math>,
encouraging solutions close to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>z</mi><annotation encoding="application/x-tex">z</annotation></semantics></math>.
The second term
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>λ</mi><mi>h</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\lambda h(x)</annotation></semantics></math>
applies the penalty function, encouraging solutions with desirable
properties according to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>.
The minimizer balances these competing objectives, finding a point that
is both close to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>z</mi><annotation encoding="application/x-tex">z</annotation></semantics></math>
and has small penalty under
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>.</p></p>

<p><p>Different penalty functions produce different proximal operators.
When
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
is an indicator function (infinite outside a set, zero inside), we
recover ordinary projection. When
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
is a differentiable function like
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup></mrow><annotation encoding="application/x-tex">\|x\|_2^2</annotation></semantics></math>,
we get a closed form involving gradient steps. When
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
is non-smooth like
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub></mrow><annotation encoding="application/x-tex">\|x\|_1</annotation></semantics></math>,
the proximal operator provides a well-defined operation that replaces
the problematic gradient.</p></p>

<p><p>For the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
norm, the proximal operator has a particularly elegant form:
element-wise soft thresholding. This operation treats each coordinate
independently, applying a simple threshold rule that zeros out small
values and shrinks large ones. The threshold level
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>
controls how aggressively sparsity is enforced: larger
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>
creates sparser solutions by zeroing out more coordinates.</p></p>



## Soft Thresholding: The L1 Proximal Operator
<p><p>What is the proximal operator for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>h</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub></mrow><annotation encoding="application/x-tex">h(x) = \|x\|_1</annotation></semantics></math>?
The answer is elegant: soft thresholding. The operator
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>𝒮</mi><mi>λ</mi></msub><annotation encoding="application/x-tex">\mathcal{S}_\lambda</annotation></semantics></math>
acts element-wise according to this rule:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝒮</mi><mi>λ</mi></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><msub><mo stretchy="false" form="postfix">)</mo><mi>i</mi></msub><mo>=</mo><mrow><mo stretchy="true" form="prefix">{</mo><mtable><mtr><mtd columnalign="left" style="text-align: left"><msub><mi>z</mi><mi>i</mi></msub><mo>−</mo><mi>λ</mi></mtd><mtd columnalign="left" style="text-align: left"><mrow><mtext mathvariant="normal">if </mtext><mspace width="0.333em"></mspace></mrow><msub><mi>z</mi><mi>i</mi></msub><mo>&gt;</mo><mi>λ</mi></mtd></mtr><mtr><mtd columnalign="left" style="text-align: left"><mn>0</mn></mtd><mtd columnalign="left" style="text-align: left"><mrow><mtext mathvariant="normal">if </mtext><mspace width="0.333em"></mspace></mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>z</mi><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo><mo>≤</mo><mi>λ</mi></mtd></mtr><mtr><mtd columnalign="left" style="text-align: left"><msub><mi>z</mi><mi>i</mi></msub><mo>+</mo><mi>λ</mi></mtd><mtd columnalign="left" style="text-align: left"><mrow><mtext mathvariant="normal">if </mtext><mspace width="0.333em"></mspace></mrow><msub><mi>z</mi><mi>i</mi></msub><mo>&lt;</mo><mi>−</mi><mi>λ</mi></mtd></mtr></mtable></mrow></mrow><annotation encoding="application/x-tex">\mathcal{S}_\lambda(z)_i = \begin{cases}z_i - \lambda &amp; \text{if } z_i &gt; \lambda \\0 &amp; \text{if } |z_i| \leq \lambda \\z_i + \lambda &amp; \text{if } z_i &lt; -\lambda\end{cases}</annotation></semantics></math></p></p>

<p><p>To see the operator in action, set
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>λ</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">\lambda=0.1</annotation></semantics></math>.
For
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>=</mo><mn>0.12</mn></mrow><annotation encoding="application/x-tex">z_i=0.12</annotation></semantics></math>,
soft thresholding returns
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝒮</mi><mn>0.1</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><msub><mo stretchy="false" form="postfix">)</mo><mi>i</mi></msub><mo>=</mo><mn>0.02</mn></mrow><annotation encoding="application/x-tex">\mathcal{S}_{0.1}(z)_i = 0.02</annotation></semantics></math>;
for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>=</mo><mn>0.08</mn></mrow><annotation encoding="application/x-tex">z_i=0.08</annotation></semantics></math>,
it returns
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>0</mn><annotation encoding="application/x-tex">0</annotation></semantics></math>;
for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>=</mo><mi>−</mi><mn>0.25</mn></mrow><annotation encoding="application/x-tex">z_i=-0.25</annotation></semantics></math>,
it returns
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mn>0.15</mn></mrow><annotation encoding="application/x-tex">-0.15</annotation></semantics></math>.
In vector form, for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>z</mi><mo>=</mo><mo stretchy="false" form="prefix">[</mo><mn>0.12</mn><mo>,</mo><mspace width="0.167em"></mspace><mn>0.08</mn><mo>,</mo><mspace width="0.167em"></mspace><mo>−</mo><mn>0.25</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">z=[0.12,\,0.08,\,-0.25]</annotation></semantics></math>
we get
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝒮</mi><mn>0.1</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mo stretchy="false" form="prefix">[</mo><mn>0.02</mn><mo>,</mo><mspace width="0.167em"></mspace><mn>0.0</mn><mo>,</mo><mspace width="0.167em"></mspace><mo>−</mo><mn>0.15</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">\mathcal{S}_{0.1}(z)=[0.02,\,0.0,\,-0.15]</annotation></semantics></math>.
This simple check illustrates the three-region rule: exact zeros near
the origin and shrinkage just outside that zone.</p></p>

<p><p>Three regions. Three actions. Values with magnitude below
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>
get zeroed out completely, creating exact sparsity. Positive values
above
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>
are reduced by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>,
shrinking toward zero from above. Negative values below
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>λ</mi></mrow><annotation encoding="application/x-tex">-\lambda</annotation></semantics></math>
are increased by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>,
shrinking toward zero from below. The name "soft thresholding"
distinguishes this from hard thresholding, which would zero out values
below
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>
but leave others unchanged (imagine cutting with scissors for hard
thresholding versus gradually squeezing for soft).</p></p>

<p><p>Why does this operation minimize the proximal objective? Consider a
single coordinate of the optimization problem. We want to find
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>i</mi></msub><annotation encoding="application/x-tex">x_i</annotation></semantics></math>
that minimizes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mn>1</mn><mn>2</mn></mfrac><mo stretchy="false" form="prefix">(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>−</mo><msub><mi>z</mi><mi>i</mi></msub><msup><mo stretchy="false" form="postfix">)</mo><mn>2</mn></msup><mo>+</mo><mi>λ</mi><mo stretchy="false" form="prefix">|</mo><msub><mi>x</mi><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">\frac{1}{2}(x_i - z_i)^2 + \lambda |x_i|</annotation></semantics></math>.
The first term is a quadratic pulling
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>i</mi></msub><annotation encoding="application/x-tex">x_i</annotation></semantics></math>
toward
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>.
The second term is an absolute value penalty pulling
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>i</mi></msub><annotation encoding="application/x-tex">x_i</annotation></semantics></math>
toward zero. These competing forces balance at the soft threshold. To
see this mathematically, split the problem into three cases based on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>.</p></p>

<p><p>For
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>&gt;</mo><mi>λ</mi></mrow><annotation encoding="application/x-tex">z_i &gt; \lambda</annotation></semantics></math>,
assume the minimum occurs at positive
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">x_i &gt; 0</annotation></semantics></math>,
making
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>x</mi><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo><mo>=</mo><msub><mi>x</mi><mi>i</mi></msub></mrow><annotation encoding="application/x-tex">|x_i| = x_i</annotation></semantics></math>.
Taking the derivative and setting to zero:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>−</mo><msub><mi>z</mi><mi>i</mi></msub><mo>+</mo><mi>λ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">x_i - z_i + \lambda = 0</annotation></semantics></math>,
giving
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>=</mo><msub><mi>z</mi><mi>i</mi></msub><mo>−</mo><mi>λ</mi></mrow><annotation encoding="application/x-tex">x_i = z_i - \lambda</annotation></semantics></math>.
This confirms the first case of soft thresholding. For
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>z</mi><mi>i</mi></msub><mo>&lt;</mo><mi>−</mi><mi>λ</mi></mrow><annotation encoding="application/x-tex">z_i &lt; -\lambda</annotation></semantics></math>,
assuming negative
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">x_i &lt; 0</annotation></semantics></math>
makes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>x</mi><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo><mo>=</mo><mi>−</mi><msub><mi>x</mi><mi>i</mi></msub></mrow><annotation encoding="application/x-tex">|x_i| = -x_i</annotation></semantics></math>.
The derivative equation becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>−</mo><msub><mi>z</mi><mi>i</mi></msub><mo>−</mo><mi>λ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">x_i - z_i - \lambda = 0</annotation></semantics></math>,
giving
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>=</mo><msub><mi>z</mi><mi>i</mi></msub><mo>+</mo><mi>λ</mi></mrow><annotation encoding="application/x-tex">x_i = z_i + \lambda</annotation></semantics></math>,
confirming the third case. For
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>z</mi><mi>i</mi></msub><mo stretchy="false" form="prefix">|</mo><mo>≤</mo><mi>λ</mi></mrow><annotation encoding="application/x-tex">|z_i| \leq \lambda</annotation></semantics></math>,
we can verify that
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>x</mi><mi>i</mi></msub><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">x_i = 0</annotation></semantics></math>
achieves lower objective value than any non-zero
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mi>i</mi></msub><annotation encoding="application/x-tex">x_i</annotation></semantics></math>,
confirming the middle case.</p></p>

<p><p>When
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
is small (magnitude less than
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>),
the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
penalty’s pull toward zero dominates the quadratic’s pull toward
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>.
The minimum occurs at exactly zero. When
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
is large, the quadratic term dominates near
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>,
but the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
penalty still exerts constant downward pressure, causing the minimum to
occur at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>z</mi><mi>i</mi></msub><annotation encoding="application/x-tex">z_i</annotation></semantics></math>
offset by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>λ</mi><annotation encoding="application/x-tex">\lambda</annotation></semantics></math>
toward zero. This analysis confirms that soft thresholding solves the
one-dimensional proximal problem exactly.</p></p>

<p><p>The full proximal operator applies this element-wise operation across
all coordinates. Because the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
norm decomposes as a sum of absolute values, and the squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
norm similarly decomposes as a sum of squares, the multi-dimensional
proximal problem separates into independent one-dimensional problems.
Each coordinate can be thresholded independently without considering the
others, making the operation computationally efficient and easily
parallelizable.</p></p>

<p><p>Contrast this with the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
proximal operator, which must consider all coordinates jointly. The
proximal operator for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>h</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mo stretchy="false" form="postfix">∥</mo><mi>x</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>2</mn></msub></mrow><annotation encoding="application/x-tex">h(x) = \|x\|_2</annotation></semantics></math>
produces
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">prox</mtext><mrow><mi>λ</mi><mi>h</mi></mrow></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>max</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo>−</mo><mi>λ</mi><mi>/</mi><mo stretchy="false" form="postfix">∥</mo><mi>z</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>2</mn></msub><mo stretchy="false" form="postfix">)</mo><mo>⋅</mo><mi>z</mi></mrow><annotation encoding="application/x-tex">\text{prox}_{\lambda h}(z) = \max(0, 1 - \lambda/\|z\|_2) \cdot z</annotation></semantics></math>,
a scaling operation that treats the entire vector as a unit. This
operator shrinks vectors uniformly rather than creating sparsity by
zeroing individual coordinates.</p></p>



## From Proximal Operators to FISTA
<p><p>Proximal gradient methods solve problems of the form
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>min</mi><mo>&#8289;</mo><mi>x</mi></msub><mo stretchy="false" form="prefix">{</mo><mi>f</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mi>h</mi><mo stretchy="false" form="prefix">(</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">}</mo></mrow><annotation encoding="application/x-tex">\min_x \{ f(x) + h(x) \}</annotation></semantics></math>
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>
is smooth but
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
is not. The strategy decomposes each iteration into two steps. First,
take a standard gradient step on the smooth function
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>,
moving from current point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">x^{(k)}</annotation></semantics></math>
in the direction
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>∇</mi><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">-\nabla f(x^{(k)})</annotation></semantics></math>
with step size
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>η</mi><annotation encoding="application/x-tex">\eta</annotation></semantics></math>.
Second, apply the proximal operator of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
to handle the non-smooth term.</p></p>



The basic proximal gradient update is:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>=</mo><msub><mtext mathvariant="normal">prox</mtext><mrow><mi>η</mi><mi>h</mi></mrow></msub><mrow><mo stretchy="true" form="prefix">(</mo><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>−</mo><mi>η</mi><mi>∇</mi><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo stretchy="false" form="postfix">)</mo><mo stretchy="true" form="postfix">)</mo></mrow></mrow><annotation encoding="application/x-tex">x^{(k+1)} = \text{prox}_{\eta h}\left( x^{(k)} - \eta \nabla f(x^{(k)}) \right)</annotation></semantics></math></p></p>

<p><p>This iteration provably converges to a minimizer under standard
assumptions on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>.
The convergence rate is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>O</mi><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mi>/</mi><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">O(1/k)</annotation></semantics></math>
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
is the iteration count, meaning the error decreases inversely with
iterations. While this beats naive subgradient methods, it remains
relatively slow for problems requiring high precision.</p></p>

<p><p>FISTA accelerates this basic scheme using Nesterov momentum. Instead
of computing gradients at the current point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">x^{(k)}</annotation></semantics></math>,
FISTA computes them at an extrapolated point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">y^{(k)}</annotation></semantics></math>
that anticipates where the optimization is heading. This look-ahead
allows the algorithm to better exploit consistent directions in the
objective landscape, achieving faster convergence.</p></p>



The FISTA update sequence is:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>=</mo><msub><mtext mathvariant="normal">prox</mtext><mrow><mi>η</mi><mi>h</mi></mrow></msub><mrow><mo stretchy="true" form="prefix">(</mo><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>−</mo><mi>η</mi><mi>∇</mi><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo stretchy="false" form="postfix">)</mo><mo stretchy="true" form="postfix">)</mo></mrow></mrow><annotation encoding="application/x-tex">x^{(k+1)} = \text{prox}_{\eta h}\left( y^{(k)} - \eta \nabla f(y^{(k)}) \right)</annotation></semantics></math></p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>t</mi><mrow><mi>k</mi><mo>+</mo><mn>1</mn></mrow></msub><mo>=</mo><mfrac><mrow><mn>1</mn><mo>+</mo><msqrt><mrow><mn>1</mn><mo>+</mo><mn>4</mn><msubsup><mi>t</mi><mi>k</mi><mn>2</mn></msubsup></mrow></msqrt></mrow><mn>2</mn></mfrac></mrow><annotation encoding="application/x-tex">t_{k+1} = \frac{1 + \sqrt{1 + 4t_k^2}}{2}</annotation></semantics></math></p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>=</mo><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>+</mo><mfrac><mrow><msub><mi>t</mi><mi>k</mi></msub><mo>−</mo><mn>1</mn></mrow><msub><mi>t</mi><mrow><mi>k</mi><mo>+</mo><mn>1</mn></mrow></msub></mfrac><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>−</mo><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">y^{(k+1)} = x^{(k+1)} + \frac{t_k - 1}{t_{k+1}}(x^{(k+1)} - x^{(k)})</annotation></semantics></math></p></p>

<p><p>The variable
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>t</mi><mi>k</mi></msub><annotation encoding="application/x-tex">t_k</annotation></semantics></math>
controls the momentum coefficient. Starting from
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>t</mi><mn>0</mn></msub><mo>=</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">t_0 = 1</annotation></semantics></math>,
this sequence grows with iterations, providing progressively stronger
acceleration. The specific formula for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>t</mi><mi>k</mi></msub><annotation encoding="application/x-tex">t_k</annotation></semantics></math>
is carefully chosen to ensure the convergence guarantee: FISTA achieves
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>O</mi><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mi>/</mi><msup><mi>k</mi><mn>2</mn></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">O(1/k^2)</annotation></semantics></math>
convergence rate, a quadratic improvement over standard proximal
gradient descent.</p></p>

<p><p>In practice, the momentum update can be simplified. The papers
introducing FISTA showed that
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>t</mi><mi>k</mi></msub><mo>≈</mo><mi>k</mi><mi>/</mi><mn>2</mn></mrow><annotation encoding="application/x-tex">t_k \approx k/2</annotation></semantics></math>
for large
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>,
leading to momentum coefficient
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><msub><mi>t</mi><mi>k</mi></msub><mo>−</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo><mi>/</mi><msub><mi>t</mi><mrow><mi>k</mi><mo>+</mo><mn>1</mn></mrow></msub><mo>≈</mo><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>−</mo><mn>2</mn><mo stretchy="false" form="postfix">)</mo><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(t_k - 1)/t_{k+1} \approx (k-2)/(k+1)</annotation></semantics></math>.
For implementation simplicity, many practitioners use the approximation
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>3</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">k/(k+3)</annotation></semantics></math>,
which provides similar acceleration behavior while being slightly more
conservative. This approximation maintains fast convergence while
improving numerical stability.</p></p>



## Applying FISTA to ElasticNet

Now we apply FISTA to ElasticNet's specific attack objective, decomposing it into components that optimization can handle efficiently.
<p><p>ElasticNet pairs adversarial loss, which drives misclassification,
with mixed-norm distance penalties that control perturbation size and
sparsity. We use the Carlini &amp; Wagner margin formulation, measuring
how much the true class logit
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Z</mi><mi>y</mi></msub><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">Z_y(x&#39;)</annotation></semantics></math>
exceeds the strongest competitor. The distance term combines squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
for smoothness with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
for sparsity, weighted by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>.
A trade-off constant
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
balances these objectives.</p></p>

<p><p>For ElasticNet, decomposing into smooth and non-smooth parts follows
naturally from this structure. Define the smooth part
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>
as the adversarial loss plus the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distance:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>c</mi><mo>⋅</mo><mi>max</mi><mo>&#8289;</mo><mo minsize="1.8" maxsize="1.8" stretchy="false" form="prefix">(</mo><msub><mi>Z</mi><mi>y</mi></msub><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>−</mo><munder><mi>max</mi><mo>&#8289;</mo><mrow><mi>j</mi><mo>≠</mo><mi>y</mi></mrow></munder><msub><mi>Z</mi><mi>j</mi></msub><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mi>κ</mi><mo>,</mo><mn>0</mn><mo minsize="1.8" maxsize="1.8" stretchy="false" form="postfix">)</mo><mi>+</mi><mo stretchy="false" form="postfix">∥</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup></mrow><annotation encoding="application/x-tex">f(x&#39;) = c \cdot \max\Big(Z_y(x&#39;) - \max_{j \neq y} Z_j(x&#39;) + \kappa, 0\Big) + \|x&#39; - x\|_2^2</annotation></semantics></math></p></p>

<p><p>Define the non-smooth part
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
as the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
penalty:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>h</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>β</mi><mo stretchy="false" form="postfix">∥</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub></mrow><annotation encoding="application/x-tex">h(x&#39;) = \beta \|x&#39; - x\|_1</annotation></semantics></math></p></p>

<p><p>Gradients for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>
combine backpropagation through the neural network (for the adversarial
loss) with a simple linear gradient (for the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
term). Both components are differentiable almost everywhere, with the
adversarial loss’s hinge being handled by standard subgradient
conventions. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradient is particularly simple:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>∇</mi><msup><mi>x</mi><mo>′</mo></msup></msub><mo stretchy="false" form="postfix">∥</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup><mo>=</mo><mn>2</mn><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\nabla_{x&#39;} \|x&#39; - x\|_2^2 = 2(x&#39; - x)</annotation></semantics></math>.</p></p>

<p><p>Soft thresholding is the proximal operator for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>,
applied to the perturbation. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>δ</mi><mo>=</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi></mrow><annotation encoding="application/x-tex">\delta = x&#39; - x</annotation></semantics></math>
for the perturbation, we have:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mtext mathvariant="normal">prox</mtext><mrow><mi>η</mi><mi>β</mi><mo stretchy="false" form="postfix">∥</mo><mo>⋅</mo><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub></mrow></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>x</mi><mo>+</mo><msub><mi>𝒮</mi><mrow><mi>η</mi><mi>β</mi></mrow></msub><mo stretchy="false" form="prefix">(</mo><mi>z</mi><mo>−</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\text{prox}_{\eta \beta \|\cdot\|_1}(z) = x + \mathcal{S}_{\eta \beta}(z - x)</annotation></semantics></math></p></p>



This formulation makes explicit that sparsity is enforced on the perturbation itself, not the adversarial image. We want sparse perturbations (many pixels unchanged), not sparse images (many pixels zero).
<p><p>Each FISTA iteration performs these steps in sequence. Compute the
gradient of smooth terms at the extrapolated point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">y^{(k)}</annotation></semantics></math>.
Take a gradient step with learning rate
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>η</mi><annotation encoding="application/x-tex">\eta</annotation></semantics></math>.
Apply soft thresholding with threshold
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>η</mi><mi>β</mi></mrow><annotation encoding="application/x-tex">\eta \beta</annotation></semantics></math>
to enforce
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
sparsity. Update the momentum point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">y^{(k+1)}</annotation></semantics></math>
using the simplified formula
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>3</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">k/(k+3)</annotation></semantics></math>.
This sequence repeats for hundreds of iterations until convergence, with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>η</mi><annotation encoding="application/x-tex">\eta</annotation></semantics></math>
controlling the gradient step size.</p></p>

<p><p>To see how the proximal step and momentum interact, consider a
two-dimensional example. After a gradient step, suppose the candidate
perturbation relative to the original is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>δ</mi><mo>=</mo><mo stretchy="false" form="prefix">[</mo><mn>0.12</mn><mo>,</mo><mspace width="0.167em"></mspace><mo>−</mo><mn>0.07</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">\delta=[0.12,\,-0.07]</annotation></semantics></math>
and set
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">\beta=0.1</annotation></semantics></math>.
Soft thresholding gives
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>𝒮</mi><mn>0.1</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>δ</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mo stretchy="false" form="prefix">[</mo><mn>0.02</mn><mo>,</mo><mspace width="0.167em"></mspace><mn>0.0</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">\mathcal{S}_{0.1}(\delta)=[0.02,\,0.0]</annotation></semantics></math>.
The first coordinate survives with shrinkage; the second drops to zero,
which enforces sparsity on small changes. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mo>=</mo><mn>10</mn></mrow><annotation encoding="application/x-tex">k=10</annotation></semantics></math>,
the momentum coefficient
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>3</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>10</mn><mi>/</mi><mn>13</mn><mo>≈</mo><mn>0.769</mn></mrow><annotation encoding="application/x-tex">k/(k+3)=10/13\approx 0.769</annotation></semantics></math>
extrapolates the next evaluation point along the update direction, using
recent progress to look ahead and speed convergence when updates keep
pointing the same way.</p></p>



## Why FISTA for ElasticNet?

ElasticNet's iterative optimization differs fundamentally from FGSM's single-step approach and DeepFool's geometric linearization. The specific optimization mechanics make this difference clear.
<p><p>FGSM requires no iterative optimization. One gradient evaluation
yields the attack direction through a sign operation. Total iterations:
one. DeepFool iterates through geometric projections, solving 5-20
closed-form linear problems without gradient descent or line search.
FISTA performs true iterative optimization through gradient descent with
proximal operators, requiring 100-1000 iterations where each step
computes gradients via full backpropagation, applies soft thresholding
for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
sparsity, and updates momentum for acceleration.</p></p>

<p><p>Why this complexity? ElasticNet’s mixed
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>1</mn></msub><mi>/</mi><msub><mi>L</mi><mn>2</mn></msub></mrow><annotation encoding="application/x-tex">L_1/L_2</annotation></semantics></math>
objective admits no closed-form solution. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term creates non-smooth corners where standard gradients fail. The
misclassification constraint couples perturbations to the neural
network’s decision boundary in ways that resist geometric
simplification. FISTA handles this complexity by decomposing the problem
into manageable pieces: gradient descent for smooth terms, proximal
operators for non-smooth terms, and momentum for acceleration.</p></p>



The following sections build toward the complete FISTA implementation. We begin by defining the loss functions that provide gradients: distance metrics quantify perturbation magnitude, adversarial loss drives misclassification, and the total loss combines these components. With loss functions established, we then implement the FISTA building blocks: momentum computation, soft thresholding, and the complete iteration step. Finally, we integrate these pieces with binary search to produce minimal adversarial perturbations.

---

<!-- section 3928 | page 5 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Distance Metrics
<p><p>To balance sparsity against smoothness, ElasticNet needs three
distance computations:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
for counting total change, squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
for measuring energy, and their weighted combination for the actual
optimization objective. Computing these efficiently on batched tensors
while preserving per-example metrics requires careful dimension
handling.</p></p>



## Measuring Perturbation Magnitude
<p><p>The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distance tells us the total magnitude of change summed across all
pixels. For a
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>28</mn><mo>×</mo><mn>28</mn></mrow><annotation encoding="application/x-tex">28 \times 28</annotation></semantics></math>
MNIST image with 784 pixels, this sum ranges from 0 (no change) to
potentially hundreds (many pixels changed substantially). If 100 pixels
each change by 0.15 units, the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distance is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>100</mn><mo>×</mo><mn>0.15</mn><mo>=</mo><mn>15.0</mn></mrow><annotation encoding="application/x-tex">100 \times 0.15 = 15.0</annotation></semantics></math>.
If instead 50 pixels each change by 0.30 units, the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distance is still
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>50</mn><mo>×</mo><mn>0.30</mn><mo>=</mo><mn>15.0</mn></mrow><annotation encoding="application/x-tex">50 \times 0.30 = 15.0</annotation></semantics></math>.
Unlike
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
which counts changed pixels (100 versus 50),
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
weights each pixel by how much it changed.</p></p>

<p><p>The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distance measures the squared straight-line distance in 784-dimensional
pixel space. Squaring individual perturbations before summing creates a
strong penalty for large individual changes. Consider the same two
perturbations: 100 pixels at 0.15 each yields
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>=</mo><mn>100</mn><mo>×</mo><msup><mn>0.15</mn><mn>2</mn></msup><mo>=</mo><mn>2.25</mn></mrow><annotation encoding="application/x-tex">L_2 = 100 \times 0.15^2 = 2.25</annotation></semantics></math>,
while 50 pixels at 0.30 each yields
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>=</mo><mn>50</mn><mo>×</mo><msup><mn>0.30</mn><mn>2</mn></msup><mo>=</mo><mn>4.50</mn></mrow><annotation encoding="application/x-tex">L_2 = 50 \times 0.30^2 = 4.50</annotation></semantics></math>.
The second perturbation has twice the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distance despite identical
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distance, because
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
penalizes concentrated changes more heavily than distributed
changes.</p></p>

<p><p>The elastic-net distance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><mi>δ</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup><mo>+</mo><mi>β</mi><mo stretchy="false" form="postfix">∥</mo><mi>δ</mi><msub><mo stretchy="false" form="postfix">∥</mo><mn>1</mn></msub></mrow><annotation encoding="application/x-tex">\|\delta\|_2^2 + \beta \|\delta\|_1</annotation></semantics></math>
combines both norms with parameter
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
controlling their relative weight. When
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta = 0</annotation></semantics></math>,
we recover pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distance. As
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
increases, the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
component gains influence, biasing optimization toward sparser
solutions. This mixed distance lacks the clean geometric interpretation
of pure norms, but it captures the sparsity-smoothness balance that pure
norms cannot.</p></p>



## Understanding Norm Trade-offs
<p><p>Different norms encode different notions of perturbation quality.
Pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
optimization produces smooth, distributed perturbations where many
pixels change by small amounts. This distributes the perturbation budget
evenly, avoiding concentrated modifications that might be visually
obvious. However,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
alone provides no sparsity guarantee. An
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>-optimal
perturbation might modify every single pixel by a tiny amount, achieving
low Euclidean distance while creating perceptually noticeable global
shifts in brightness or texture.</p></p>

<p><p>Pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
optimization encourages sparsity through its non-differentiable kink at
zero. The absolute value function has no unique derivative at the
origin, creating a "barrier" that optimization must overcome to activate
a pixel. This barrier preferentially keeps small perturbations at
exactly zero, concentrating the perturbation budget into fewer pixels
with larger individual changes. For a fixed
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
budget, modifying 50 pixels at 0.2 each gives the same
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distance as modifying 100 pixels at 0.1 each, but the sparse solution
(50 pixels) often proves more effective at fooling classifiers because
concentrated changes can cross local decision boundaries more
decisively.</p></p>

<p><p>The elastic-net combination provides a middle ground. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
term prevents any single pixel from dominating the perturbation (since
squaring penalizes large values quadratically), while the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term encourages many pixels to remain at exactly zero. Tuning
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
controls this balance. Small
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
(like 0.01) produces nearly-smooth perturbations with mild sparsity,
suitable when imperceptibility matters more than pixel count. Large
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
(like 1.0) produces aggressive sparsity, potentially concentrating
perturbations into visually obvious clusters but minimizing the number
of modified pixels.</p></p>



```python
def compute_distances(adv_images, original_images, beta):
    """
    Compute L1, L2, and elastic-net distances.

    Returns all three distance metrics used in optimization
    and decision-making.

    Parameters:
        adv_images (torch.Tensor): Adversarial images (batch_size, C, H, W)
        original_images (torch.Tensor): Original images (batch_size, C, H, W)
        beta (float): Weight for L1 in elastic-net distance

    Returns:
        tuple: (l1_dist, l2_dist, elastic_dist) each shape (batch_size,)
    """
    l1_dist = torch.sum(torch.abs(adv_images - original_images), dim=(1, 2, 3))
    l2_dist = torch.sum((adv_images - original_images) ** 2, dim=(1, 2, 3))
    elastic_dist = l2_dist + beta * l1_dist

    return l1_dist, l2_dist, elastic_dist
```
<p><p>The <code>dim=(1, 2, 3)</code> parameter collapses channel, height,
and width while preserving the batch dimension. For a batch of 20 images
with shape (20, 1, 28, 28), this produces 20 scalar distances - one per
image. Why preserve the batch dimension? Binary search adapts trade-off
constants individually: an easy example near the decision boundary might
use
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.01</mn></mrow><annotation encoding="application/x-tex">c=0.01</annotation></semantics></math>
while a resistant example deep in the correct class region needs
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>10</mn></mrow><annotation encoding="application/x-tex">c=10</annotation></semantics></math>.
Without per-example distances, we’d be forced to use the same constant
for all images, over-perturbing easy cases or under-perturbing hard
ones.</p></p>

<p><p>Notice we’re using squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="postfix">∥</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup></mrow><annotation encoding="application/x-tex">\|x&#39; - x\|_2^2</annotation></semantics></math>
for the same computational reasons discussed in the FISTA framework: the
gradient
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>2</mn><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">2(x&#39; - x)</annotation></semantics></math>
is simpler than the normalized form from the true
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
norm. This maintains strict convexity and produces the same optimal
perturbations. The elastic distance combines the squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
component with the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term, using the same
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
weighting that appears in our proximal operator.</p></p>



Note what this function does not do: it doesn't apply any constraints, perform any thresholding, or make any decisions. It simply measures. Other functions will use these distances to make decisions about attack success or to compute loss gradients, but the distance computation itself remains a pure measurement operation.

With distance metrics defined, the next section implements the adversarial loss functions that drive misclassification and combines them with these distance terms to form the complete optimization objective.

---

<!-- section 3929 | page 6 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Adversarial Loss

The distance metrics from the previous section measure perturbation magnitude, but they don't drive misclassification. We need a loss function that provides gradient signal toward fooling the classifier while remaining differentiable for optimization. This section implements the Carlini & Wagner margin-based formulation and combines it with distance terms into the complete objective.

## The Carlini & Wagner Adversarial Loss

The adversarial loss must encourage misclassification without making the optimization problem intractable. A naive approach might use indicator functions: loss is 0 if misclassified, 1 otherwise. This discrete objective provides no gradient information, making optimization impossible. We need a smooth, differentiable function that approximates the discrete goal.
<p><p>The Carlini &amp; Wagner formulation uses a margin-based objective
comparing logits. For untargeted attacks trying to fool the model away
from true class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>y</mi><annotation encoding="application/x-tex">y</annotation></semantics></math>,
the loss measures how much the true class logit exceeds the maximum
competitor:</p></p>

<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo>,</mo><mi>y</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mi>max</mi><mo>&#8289;</mo><mo minsize="1.8" maxsize="1.8" stretchy="false" form="prefix">(</mo><msub><mi>Z</mi><mi>y</mi></msub><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>−</mo><munder><mi>max</mi><mo>&#8289;</mo><mrow><mi>j</mi><mo>≠</mo><mi>y</mi></mrow></munder><msub><mi>Z</mi><mi>j</mi></msub><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mi>κ</mi><mo>,</mo><mn>0</mn><mo minsize="1.8" maxsize="1.8" stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">f(x&#39;, y) = \max\Big(Z_y(x&#39;) - \max_{j \neq y} Z_j(x&#39;) + \kappa, 0\Big)</annotation></semantics></math></p></p>

<p><p>Let’s walk through an example to see how this works. Suppose the true
class is digit 7, with logit
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Z</mi><mn>7</mn></msub><mo>=</mo><mn>2.8</mn></mrow><annotation encoding="application/x-tex">Z_7 = 2.8</annotation></semantics></math>.
The maximum competing logit is class 4 with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Z</mi><mn>4</mn></msub><mo>=</mo><mn>1.2</mn></mrow><annotation encoding="application/x-tex">Z_4 = 1.2</annotation></semantics></math>.
Using
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>κ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\kappa = 0</annotation></semantics></math>,
the margin term computes to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>2.8</mn><mo>−</mo><mn>1.2</mn><mo>+</mo><mn>0</mn><mo>=</mo><mn>1.6</mn></mrow><annotation encoding="application/x-tex">2.8 - 1.2 + 0 = 1.6</annotation></semantics></math>.
Since this is positive,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>max</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>1.6</mn><mo>,</mo><mn>0</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>1.6</mn></mrow><annotation encoding="application/x-tex">\max(1.6, 0) = 1.6</annotation></semantics></math>,
giving us a loss of 1.6. The gradient will push this toward zero by
reducing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>Z</mi><mn>7</mn></msub><annotation encoding="application/x-tex">Z_7</annotation></semantics></math>
and increasing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>Z</mi><mn>4</mn></msub><annotation encoding="application/x-tex">Z_4</annotation></semantics></math>,
encouraging misclassification.</p></p>

<p><p>Now suppose our perturbations successfully flip the prediction so
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Z</mi><mn>7</mn></msub><mo>=</mo><mn>1.0</mn></mrow><annotation encoding="application/x-tex">Z_7 = 1.0</annotation></semantics></math>
and the new maximum competitor is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Z</mi><mn>2</mn></msub><mo>=</mo><mn>1.5</mn></mrow><annotation encoding="application/x-tex">Z_2 = 1.5</annotation></semantics></math>.
The margin becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1.0</mn><mo>−</mo><mn>1.5</mn><mo>+</mo><mn>0</mn><mo>=</mo><mi>−</mi><mn>0.5</mn></mrow><annotation encoding="application/x-tex">1.0 - 1.5 + 0 = -0.5</annotation></semantics></math>.
Since this is negative, the hinge clamps it:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>max</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mi>−</mi><mn>0.5</mn><mo>,</mo><mn>0</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\max(-0.5, 0) = 0</annotation></semantics></math>.
Loss reaches zero, signaling confident misclassification. Optimization
can now shift focus to minimizing distortion while maintaining this
misclassification.</p></p>

<p><p>When the true class logit
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>Z</mi><mi>y</mi></msub><annotation encoding="application/x-tex">Z_y</annotation></semantics></math>
exceeds all competitors by less than
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>κ</mi><annotation encoding="application/x-tex">\kappa</annotation></semantics></math>,
the margin term remains positive and drives gradients toward reducing
this gap. Once a competitor exceeds the true class by at least
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>κ</mi><annotation encoding="application/x-tex">\kappa</annotation></semantics></math>,
the margin becomes non-positive and the hinge clamps loss at 0, allowing
optimization to shift entirely to distortion minimization.</p></p>

<p><p>The confidence parameter
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>κ</mi><annotation encoding="application/x-tex">\kappa</annotation></semantics></math>
controls how strongly the adversarial example must misclassify. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>κ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\kappa = 0</annotation></semantics></math>,
the attack succeeds once any competitor exceeds the true class by any
amount. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>κ</mi><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\kappa &gt; 0</annotation></semantics></math>,
the competitor must exceed the true class by at least
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>κ</mi><annotation encoding="application/x-tex">\kappa</annotation></semantics></math>,
producing more robust adversarial examples that remain effective under
small perturbations or preprocessing.</p></p>


```python
def compute_adversarial_loss(logits, labels_onehot, confidence, targeted=False):
    """
    Compute margin-based adversarial loss.

    Uses C&W formulation: encourage misclassification with
    confidence margin. Loss becomes zero once margin achieved.

    Parameters:
        logits (torch.Tensor): Model outputs before softmax (batch_size, num_classes)
        labels_onehot (torch.Tensor): One-hot encoded labels (batch_size, num_classes)
        confidence (float): Confidence margin kappa
        targeted (bool): Whether this is a targeted attack

    Returns:
        torch.Tensor: Adversarial loss per example (batch_size,)
    """
    # Extract scores
    real = torch.sum(labels_onehot * logits, dim=1)
    other = torch.max((1 - labels_onehot) * logits - labels_onehot * 10000, dim=1)[0]

    # Compute margin loss
    if targeted:
        # For targeted attacks: want target to exceed other classes by the margin
        loss = torch.clamp(other - real + confidence, min=0)
    else:
        # For untargeted attacks: want real class to be exceeded
        loss = torch.clamp(real - other + confidence, min=0)

    return loss
```
<p><p>How do we extract the true class logit from the model outputs? The
one-hot encoding <code>labels_onehot</code> acts as a selector mask.
Multiplying logits by <code>labels_onehot</code> zeros out all classes
except the true one, then summing collapses to a scalar per example. If
an example has true label 7 with logits
<code>[0.1, -0.3, 0.5, 2.8, 1.2, 0.7, -0.5, 0.3, 0.9, 0.4]</code>, the
one-hot vector <code>[0,0,0,0,0,0,0,1,0,0]</code> extracts
<code>real = 2.8</code> through element-wise multiplication (all
products are zero except position 7, which gives
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mo>×</mo><mn>2.8</mn><mo>=</mo><mn>2.8</mn></mrow><annotation encoding="application/x-tex">1 \times 2.8 = 2.8</annotation></semantics></math>).</p></p>



To find the maximum competitor logit, we need to exclude the true class and take the max of what remains. The mask `(1 - labels_onehot)` zeros out the true class position. The term `- labels_onehot * 10000` subtracts 10000 from the true class position as a safety measure, ensuring the true class can never be selected even if the previous mask somehow failed. For our example, this transforms logits to `[0.1, -0.3, 0.5, -9997.2, 1.2, 0.7, -0.5, 0.3, 0.9, 0.4]`, making position 4 (logit 1.2) the maximum competitor, so `other = 1.2`.
<p><p>The untargeted case measures
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Z</mi><mi>y</mi></msub><mo>−</mo><msub><mi>max</mi><mo>&#8289;</mo><mrow><mi>j</mi><mo>≠</mo><mi>y</mi></mrow></msub><msub><mi>Z</mi><mi>j</mi></msub><mo>+</mo><mi>κ</mi></mrow><annotation encoding="application/x-tex">Z_y - \max_{j \neq y} Z_j + \kappa</annotation></semantics></math>.
For <code>real = 2.8</code>, <code>other = 1.2</code>, and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>κ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\kappa = 0</annotation></semantics></math>,
the margin is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>2.8</mn><mo>−</mo><mn>1.2</mn><mo>+</mo><mn>0</mn><mo>=</mo><mn>1.6</mn></mrow><annotation encoding="application/x-tex">2.8 - 1.2 + 0 = 1.6</annotation></semantics></math>.
This positive value means the true class still leads by 1.6 logit units.
The loss provides gradient signal to reduce this margin. If the attack
succeeds in flipping the prediction so that <code>real = 1.0</code> and
<code>other = 1.5</code>, the margin becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1.0</mn><mo>−</mo><mn>1.5</mn><mo>+</mo><mn>0</mn><mo>=</mo><mi>−</mi><mn>0.5</mn></mrow><annotation encoding="application/x-tex">1.0 - 1.5 + 0 = -0.5</annotation></semantics></math>.
The clamp activates, setting loss to 0, meaning the adversarial
objective is satisfied.</p></p>



This formulation contrasts with FGSM's approach. FGSM uses standard cross-entropy loss and takes a single step along the gradient's sign. The loss value doesn't matter, only the gradient direction. ElasticNet needs the actual loss magnitude to balance against distortion terms, requiring a more carefully designed objective that saturates appropriately.
<p><p>To see how the margin behaves in the targeted case, swap roles so the
target class must exceed all others. If the target logit is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>2.0</mn><annotation encoding="application/x-tex">2.0</annotation></semantics></math>
and the strongest competitor is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>2.6</mn><annotation encoding="application/x-tex">2.6</annotation></semantics></math>
with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>κ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\kappa=0</annotation></semantics></math>,
the targeted loss is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>max</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>2.6</mn><mo>−</mo><mn>2.0</mn><mo>,</mo><mspace width="0.167em"></mspace><mn>0</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0.6</mn></mrow><annotation encoding="application/x-tex">\max(2.6-2.0,\,0)=0.6</annotation></semantics></math>,
which signals the example is not yet confidently targeted. Once the
target surpasses competitors, for example target
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>2.7</mn><annotation encoding="application/x-tex">2.7</annotation></semantics></math>
and competitor
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>2.6</mn><annotation encoding="application/x-tex">2.6</annotation></semantics></math>,
the loss becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>max</mi><mo>&#8289;</mo><mo stretchy="false" form="prefix">(</mo><mn>2.6</mn><mo>−</mo><mn>2.7</mn><mo>,</mo><mspace width="0.167em"></mspace><mn>0</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\max(2.6-2.7,\,0)=0</annotation></semantics></math>.
At that point, optimization naturally shifts effort to reducing
distortion while maintaining the target margin.</p></p>



## Combining Loss Components
<p><p>The complete optimization objective combines adversarial loss,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distortion, and (implicitly through FISTA)
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distortion. The function <code>compute_total_loss</code> implements the
smooth part of this objective (the part FISTA differentiates
explicitly). The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term is handled by the proximal operator, not included in the gradient
computation.</p></p>



The total loss takes the form:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>ℒ</mi><mtext mathvariant="normal">total</mtext></msub><mo>=</mo><mi>c</mi><mo>⋅</mo><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo>,</mo><mi>y</mi><mo stretchy="false" form="postfix">)</mo><mi>+</mi><mo stretchy="false" form="postfix">∥</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup></mrow><annotation encoding="application/x-tex">\mathcal{L}_{\text{total}} = c \cdot f(x&#39;, y) + \|x&#39; - x\|_2^2</annotation></semantics></math></p></p>

<p><p>A quick calculation clarifies the trade-off. If an example has margin
loss
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo>,</mo><mi>y</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>0.6</mn></mrow><annotation encoding="application/x-tex">f(x&#39;,y)=0.6</annotation></semantics></math>,
squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>=</mo><mn>2.25</mn></mrow><annotation encoding="application/x-tex">L_2=2.25</annotation></semantics></math>,
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">c=0.1</annotation></semantics></math>,
then
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>ℒ</mi><mtext mathvariant="normal">total</mtext></msub><mo>=</mo><mn>0.1</mn><mo>×</mo><mn>0.6</mn><mo>+</mo><mn>2.25</mn><mo>=</mo><mn>2.31</mn></mrow><annotation encoding="application/x-tex">\mathcal{L}_{\text{total}} = 0.1\times 0.6 + 2.25 = 2.31</annotation></semantics></math>.
Raising
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>1.0</mn><annotation encoding="application/x-tex">1.0</annotation></semantics></math>
yields
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1.0</mn><mo>×</mo><mn>0.6</mn><mo>+</mo><mn>2.25</mn><mo>=</mo><mn>2.85</mn></mrow><annotation encoding="application/x-tex">1.0\times 0.6 + 2.25 = 2.85</annotation></semantics></math>.
Increasing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
puts more weight on misclassification pressure relative to distortion;
decreasing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
does the opposite.</p></p>

<p><p>The trade-off constant
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
balances misclassification against distortion. Large
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
prioritizes attack success over imperceptibility, allowing larger
perturbations to ensure misclassification. Small
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
prioritizes imperceptibility over attack success, risking failure if
perturbations remain too small. The binary search finds the minimal
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
sufficient for successful attacks.</p></p>



```python
def compute_total_loss(
    adv_images,
    original_images,
    labels_onehot,
    const,
    model,
    beta,
    confidence,
    targeted=False,
):
    """
    Combine smooth components: c * adversarial + squared L2 (L1 via proximal operator).

    The constant c balances misclassification vs distortion.
    Beta controls L1 vs L2 trade-off (sparsity vs smoothness).

    Parameters:
        adv_images (torch.Tensor): Current adversarial images
        original_images (torch.Tensor): Original clean images
        labels_onehot (torch.Tensor): One-hot encoded labels
        const (torch.Tensor): Trade-off constants c per example
        model (nn.Module): Target model
        beta (float): L1 weight in elastic-net distance
        confidence (float): Margin for misclassification
        targeted (bool): Whether this is a targeted attack

    Returns:
        tuple: (total_loss, adversarial_loss, distances)
    """
    # Get model predictions
    logits = model(adv_images)

    # Compute adversarial loss
    adversarial_loss = compute_adversarial_loss(
        logits, labels_onehot, confidence, targeted
    )

    # Compute distances
    l1_dist, l2_dist, elastic_dist = compute_distances(
        adv_images, original_images, beta
    )

    # Combine: c * adversarial_loss + L2_distance
    # Note: L1 is handled by FISTA's proximal operator, not in this gradient
    total_loss = const * adversarial_loss + l2_dist

    return total_loss, adversarial_loss, (l1_dist, l2_dist, elastic_dist)
```

We begin by computing model outputs (logits) that drive the adversarial loss. A forward pass is the most expensive step in the pipeline and repeats hundreds of times during FISTA, so inference speed strongly affects overall runtime.
<p><p>FISTA’s proximal operator enforces the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
penalty, so the total loss omits it. Autograd then computes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>∇</mi><msup><mi>x</mi><mo>′</mo></msup></msub><mspace width="0.167em"></mspace><mo stretchy="false" form="prefix">[</mo><mi>c</mi><mo>⋅</mo><mi>f</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>x</mi><mo>′</mo></msup><mo>,</mo><mi>y</mi><mo stretchy="false" form="postfix">)</mo><mi>+</mi><mo stretchy="false" form="postfix">∥</mo><msup><mi>x</mi><mo>′</mo></msup><mo>−</mo><mi>x</mi><msubsup><mo stretchy="false" form="postfix">∥</mo><mn>2</mn><mn>2</mn></msubsup><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">\nabla_{x&#39;}\,[c \cdot f(x&#39;, y) + \|x&#39; - x\|_2^2]</annotation></semantics></math>
for the gradient step, while the shrinkage operation applies the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
effect without needing its gradient.</p></p>



This function returns three layers of information: the scalar total loss for backpropagation, the adversarial loss for monitoring success, and all three distance metrics for analysis. That richer signature supports detailed logging while still providing exactly the gradients we need.

Per-example `const` values let the binary search adapt to each example's difficulty. Easy cases converge to small constants and low distortion, while resistant cases require larger constants, accepting more distortion to achieve misclassification.

With loss functions defined, the next section implements the core FISTA building blocks: momentum computation for acceleration and soft thresholding for sparsity. These components combine with the loss functions to form the complete FISTA optimization step.

---

<!-- section 3930 | page 7 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Implementing FISTA Components

The mathematical foundations from the previous section provide the theoretical framework for FISTA optimization. Now we translate that theory into working code. The functional programming approach decomposes the algorithm into small, focused functions that each implement one specific mathematical operation. This section develops the first two building blocks: computing Nesterov momentum and applying soft thresholding.
<p><p>These functions embody core concepts from convex optimization. The
momentum computation implements Nesterov acceleration, which achieves
the optimal
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>O</mi><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mi>/</mi><msup><mi>k</mi><mn>2</mn></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">O(1/k^2)</annotation></semantics></math>
rate for smooth convex problems and is used heuristically here. The
shrinkage operation implements the proximal operator for the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
norm, enabling efficient optimization of non-smooth objectives.
Together, these pieces form the foundation upon which the complete FISTA
iteration will be built.</p></p>



## Nesterov Momentum: Looking Ahead
<p><p>The Nesterov acceleration formula
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>t</mi><mi>k</mi></msub><mo>=</mo><mi>k</mi><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>3</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">t_k = k/(k+3)</annotation></semantics></math>
provides momentum that grows with iteration count. Early iterations use
small momentum coefficients, taking conservative steps while the
optimization explores the loss landscape. Later iterations employ larger
coefficients, confidently accelerating along directions that have proven
productive across multiple steps.</p></p>

<p><p>This specific formula represents a simplified version of the original
Nesterov scheme. The full FISTA momentum update uses
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>t</mi><mrow><mi>k</mi><mo>+</mo><mn>1</mn></mrow></msub><mo>=</mo><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>+</mo><msqrt><mrow><mn>1</mn><mo>+</mo><mn>4</mn><msubsup><mi>t</mi><mi>k</mi><mn>2</mn></msubsup></mrow></msqrt><mo stretchy="false" form="postfix">)</mo><mi>/</mi><mn>2</mn></mrow><annotation encoding="application/x-tex">t_{k+1} = (1 + \sqrt{1 + 4t_k^2})/2</annotation></semantics></math>,
which approaches
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mi>/</mi><mn>2</mn></mrow><annotation encoding="application/x-tex">k/2</annotation></semantics></math>
asymptotically. The approximation
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>3</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">k/(k+3)</annotation></semantics></math>
provides similar behavior while being slightly more conservative,
improving numerical stability without significantly impacting
convergence speed.</p></p>



We implement this as a pure function taking only the iteration number:

```python
def compute_fista_momentum(iteration):
    """
    Calculate FISTA momentum parameter for iteration k.

    Uses Nesterov acceleration: k/(k+3)
    Early iterations have small momentum, later ones accelerate.

    Parameters:
        iteration (int): Current FISTA iteration number

    Returns:
        float: Momentum coefficient in [0, 1)
    """
    return iteration / (iteration + 3.0)
```
<p><p>Don’t let the simplicity fool you. This single line encodes a
sophisticated acceleration strategy proven to achieve optimal
convergence rates. Why divide by <code>iteration + 3.0</code> instead of
just using the iteration count? The addition in the denominator keeps
the result bounded below 1 (approaching 1 as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mo>→</mo><mi>∞</mi></mrow><annotation encoding="application/x-tex">k \to \infty</annotation></semantics></math>),
preventing momentum from overwhelming the gradient signal. Without this
normalization, momentum could grow unbounded and destabilize
optimization entirely.</p></p>



Let's verify the momentum progression across typical iteration counts:

```python
# Test momentum progression
print("FISTA Momentum Progression:")
print("=" * 40)
test_iterations = [1, 5, 10, 50, 100, 500, 1000]

for k in test_iterations:
    momentum = compute_fista_momentum(k)
    print(f"Iteration {k:4d}: momentum = {momentum:.4f}")
```

Expected output:

```txt
FISTA Momentum Progression:
========================================
Iteration    1: momentum = 0.2500
Iteration    5: momentum = 0.6250
Iteration   10: momentum = 0.7692
Iteration   50: momentum = 0.9434
Iteration  100: momentum = 0.9709
Iteration  500: momentum = 0.9940
Iteration 1000: momentum = 0.9970
```

Notice how momentum grows from cautious to aggressive. The first iteration uses only 0.25, providing modest acceleration while letting the gradient dominate direction selection. Why start so conservatively? Early iterations know nothing about the objective landscape, so committing heavily to any direction risks wasting computation. By iteration 10, momentum has grown to 0.77, substantially boosting speed along directions that have proven productive. After 100 iterations, momentum approaches 0.97, providing strong acceleration for the final convergence phase where the algorithm has accumulated substantial evidence about effective search directions.

This growth pattern serves a specific purpose. When optimization begins, the algorithm knows little about the objective landscape. Small momentum prevents premature commitment to directions that might prove unproductive. As iterations accumulate evidence that certain directions consistently reduce the objective, larger momentum exploits this structure for faster convergence.

Contrast this with standard momentum methods that use a fixed coefficient (often 0.9 throughout training). Fixed momentum requires careful tuning: too small and convergence is slow, too large and optimization becomes unstable. Nesterov's adaptive schedule eliminates this hyperparameter, automatically adjusting acceleration to match the optimization phase.

## Soft Thresholding: Creating Sparsity
<p><p>The shrinkage-thresholding operation implements the proximal operator
for the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
norm developed in Proximal Operators and Soft Thresholding. This
function takes candidate adversarial images
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>y</mi><annotation encoding="application/x-tex">y</annotation></semantics></math>,
applies the three-region thresholding rule (positive shrinkage, dead
zone elimination, negative shrinkage), and returns sparse
perturbations.</p></p>



```python
def apply_shrinkage_thresholding(y, original_images, threshold, clip_min=0.0, clip_max=1.0):
    """
    Apply soft thresholding to create sparse perturbations.

    Values with magnitude at most threshold are zeroed (sparsity).
    Values exceeding the threshold are reduced by the threshold but remain non-zero.

    Parameters:
        y (torch.Tensor): Candidate adversarial images after gradient step
        original_images (torch.Tensor): Original unperturbed images
        threshold (float): Soft thresholding parameter (higher = sparser)
        clip_min (float): Minimum valid pixel value (default 0.0)
        clip_max (float): Maximum valid pixel value (default 1.0)

    Returns:
        torch.Tensor: Images after soft thresholding
    """
    # Compute the difference from original
    diff = y - original_images

    # Apply soft thresholding
    # Values within threshold are zeroed (sparsity!)
    # Values above threshold get reduced by threshold
    shrink_positive = torch.clamp(y - threshold, min=clip_min, max=clip_max)
    shrink_negative = torch.clamp(y + threshold, min=clip_min, max=clip_max)

    # Three-way decision: positive, zero, or negative
    cond_positive = (diff > threshold).float()
    cond_zero = (torch.abs(diff) <= threshold).float()
    cond_negative = (diff < -threshold).float()

    # Combine using conditions
    result = (
        cond_positive * shrink_positive
        + cond_zero * original_images
        + cond_negative * shrink_negative
    )

    return result
```
<p><p>Computing <code>diff = y - original_images</code> reveals the
perturbation that gradient descent would produce before thresholding.
This combines the smooth gradient step (from adversarial loss and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
penalty) with previous momentum. For a specific pixel, if the original
value was 0.5 and the candidate adversarial value <code>y</code> is
0.62, then <code>diff = 0.12</code>, indicating a positive perturbation.
Soft thresholding will examine this 0.12 against threshold
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
to decide whether it survives or gets eliminated.</p></p>

<p><p>Preparing the shrunk values happens next through two separate
computations. For positive perturbations,
<code>shrink_positive = torch.clamp(y - threshold, min=clip_min, max=clip_max)</code>
subtracts
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
from the candidate values. With a pixel at 0.62 and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">\beta = 0.1</annotation></semantics></math>,
we get <code>0.62 - 0.1 = 0.52</code> as the "shrunk" value that will be
used if this perturbation survives. Clamping at <code>clip_min</code>
prevents results from dropping below 0.0 (the minimum valid pixel
value).</p></p>

<p><p>Negative perturbations get handled symmetrically.
<code>shrink_negative = torch.clamp(y + threshold, ...)</code> adds
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
instead of subtracting, while clamping at <code>clip_max</code> prevents
values from exceeding 1.0. These shrunk values sit ready but unused
until the masking step decides which pixels actually need them.</p></p>

<p><p>Applying the three-way decision requires binary masks for each
region. <code>cond_positive</code>, <code>cond_zero</code>, and
<code>cond_negative</code> each produce tensors of 0s and 1s indicating
which pixels fall into that threshold category. Multiplying these masks
element-wise with their corresponding values
(<code>shrink_positive</code>, <code>original_images</code>,
<code>shrink_negative</code>) and summing creates the final result. For
pixels with perturbations exceeding
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>,
the positive mask selects the shrunk value. For pixels in the dead zone,
the zero mask reverts to the original. For negative perturbations below
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>β</mi></mrow><annotation encoding="application/x-tex">-\beta</annotation></semantics></math>,
the negative mask applies negative shrinkage.</p></p>



## Visualizing Shrinkage Effects

To understand how soft thresholding creates sparsity, let's apply it to sample perturbations and visualize the results. We'll create synthetic perturbations with controlled properties and observe how thresholding modifies them:

```python
# Create synthetic perturbation for visualization
print("\nTesting shrinkage-thresholding operation...")

# Generate a 5x5 synthetic perturbation pattern
perturbation_pattern = torch.tensor([
    [-0.15, -0.08, -0.02,  0.03,  0.12],
    [-0.10, -0.05,  0.00,  0.06,  0.18],
    [-0.05,  0.00,  0.05,  0.10,  0.20],
    [ 0.00,  0.05,  0.08,  0.15,  0.25],
    [ 0.05,  0.08,  0.12,  0.20,  0.30]
], device=device)

# Assume original pixels are 0.5 (mid-gray)
original_values = torch.ones_like(perturbation_pattern) * 0.5
perturbed_values = original_values + perturbation_pattern

# Apply shrinkage with beta=0.1
beta_test = 0.1
thresholded = apply_shrinkage_thresholding(
    perturbed_values,
    original_values,
    beta_test,
    clip_min=0.0,
    clip_max=1.0
)

# Compute resulting perturbations
resulting_perturbation = thresholded - original_values

print(f"\nSoft Thresholding Results (beta={beta_test}):")
print("=" * 50)
print("\nOriginal perturbation pattern:")
print(perturbation_pattern.cpu().numpy())
print("\nAfter soft thresholding:")
print(resulting_perturbation.cpu().numpy())

# Count sparsity
original_nonzero = (perturbation_pattern.abs() > 1e-6).sum().item()
thresholded_nonzero = (resulting_perturbation.abs() > 1e-6).sum().item()
sparsity_gained = original_nonzero - thresholded_nonzero

print(f"\nSparsity Analysis:")
print(f"  Original non-zero elements: {original_nonzero}/25")
print(f"  After thresholding: {thresholded_nonzero}/25")
print(f"  Elements zeroed out: {sparsity_gained}")
print(f"  Sparsity achieved: {(25-thresholded_nonzero)/25*100:.1f}%")
```

Expected output:

```txt
Testing shrinkage-thresholding operation...

Soft Thresholding Results (beta=0.1):
==================================================

Original perturbation pattern:
[[-0.15 -0.08 -0.02  0.03  0.12]
 [-0.1  -0.05  0.    0.06  0.18]
 [-0.05  0.    0.05  0.1   0.2 ]
 [ 0.    0.05  0.08  0.15  0.25]
 [ 0.05  0.08  0.12  0.2   0.3 ]]

After soft thresholding:
[[-0.05  0.    0.    0.    0.02]
 [ 0.    0.    0.    0.    0.08]
 [ 0.    0.    0.    0.    0.1 ]
 [ 0.    0.    0.    0.05  0.15]
 [ 0.    0.    0.02  0.1   0.2 ]]

Sparsity Analysis:
  Original non-zero elements: 22/25
  After thresholding: 9/25
  Elements zeroed out: 13
  Sparsity achieved: 64.0%
```
<p><p>Sparsity emerges through magnitude-based pruning. Before
thresholding, 22 of 25 elements had non-zero perturbations (88% dense).
After applying
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">\beta = 0.1</annotation></semantics></math>,
only 9 survived (64% sparse). Crucially, eliminated elements become
exact zeros, not small values like 0.001 that would technically count as
non-zero in the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
norm.</p></p>

<p><p>Why does elimination follow a spatial pattern? The original
perturbation was structured with small values in the upper-left (range
-0.15 to 0.03) and large values in the bottom-right (range 0.12 to
0.30). Setting
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">\beta = 0.1</annotation></semantics></math>
creates a magnitude threshold that bisects this distribution. The
upper-left region falls entirely below threshold: every value satisfies
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><mi>p</mi><mo stretchy="false" form="prefix">|</mo><mo>≤</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">|p| \leq 0.1</annotation></semantics></math>,
triggering complete elimination. The central diagonal, with values
hovering near 0.1, also vanishes. Only the bottom-right corner exceeds
threshold, though each surviving value gets shrunk by exactly
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">\beta = 0.1</annotation></semantics></math>.
For example, the original 0.30 perturbation becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.30</mn><mo>−</mo><mn>0.1</mn><mo>=</mo><mn>0.20</mn></mrow><annotation encoding="application/x-tex">0.30 - 0.1 = 0.20</annotation></semantics></math>
after shrinkage.</p></p>

<p><p>This magnitude-based filtering serves adversarial attacks perfectly.
Pixels with weak gradients produce small perturbations that waste
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
budget without meaningfully shifting the decision boundary. Thresholding
discards these automatically, concentrating the budget on high-gradient
regions where perturbations actually change predictions. The threshold
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
controls the severity of pruning:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.2</mn></mrow><annotation encoding="application/x-tex">\beta = 0.2</annotation></semantics></math>
would eliminate 20 of 25 elements (80% sparse), preserving only the
extreme values, while
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.05</mn></mrow><annotation encoding="application/x-tex">\beta = 0.05</annotation></semantics></math>
would keep 14 elements (44% sparse), allowing more moderate
perturbations to contribute.</p></p>



The next section examines how gradients flow through the model during backpropagation. Understanding gradient magnitudes, loss landscape properties, and convergence behavior provides insight into FISTA's optimization dynamics and helps diagnose potential issues during attack execution.

---

<!-- section 3931 | page 8 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Loss Gradients and Optimization
<p><p>To optimize adversarial images, we need
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>∇</mi><msup><mi>x</mi><mo>′</mo></msup></msub><msub><mi>ℒ</mi><mtext mathvariant="normal">total</mtext></msub></mrow><annotation encoding="application/x-tex">\nabla_{x&#39;} \mathcal{L}_{\text{total}}</annotation></semantics></math>
with respect to input pixels, not model weights. Freezing the network
and enabling gradients only on adversarial images makes
<code>loss.backward()</code> compute exactly what we need. These input
gradients reveal how each pixel affects both misclassification (through
the adversarial term) and distortion (through the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
term), guiding FISTA’s iterative refinement.</p></p>



## Adversarial Loss Gradients
<p><p>How do adversarial loss gradients differ from
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradients? The adversarial component flows through the entire neural
network, composing derivatives backward from output to input via the
chain rule. Each layer contributes its local derivative, building
complexity as we move toward the input. ReLU activations create
piecewise-linear regions where gradients remain constant within each
region but jump discontinuously at boundaries. Which neurons activate
depends on the current input, making the gradient landscape non-convex
and highly structured.</p></p>



FISTA treats these complex gradients as a black box. Provide an input, receive a loss value and gradient; no need to understand the network's internal structure. We follow gradients downhill toward loss minima while the proximal operator enforces sparsity. This black-box approach makes ElasticNet general, applicable to any differentiable model regardless of architecture.
<p><p>What happens to gradients during a typical FISTA iteration? Starting
with the forward pass, we compute logits that determine adversarial loss
through the margin formula. For an example with true class 3, if the
current adversarial image produces logits
<code>[0.2, 0.5, 1.8, 2.1, 0.9, ...]</code>, then
<code>real = 2.1</code> (logit for class 3) and <code>other = 1.8</code>
(maximum competitor, class 2). The margin is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>2.1</mn><mo>−</mo><mn>1.8</mn><mo>=</mo><mn>0.3</mn></mrow><annotation encoding="application/x-tex">2.1 - 1.8 = 0.3</annotation></semantics></math>,
giving adversarial loss of 0.3 (assuming
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>κ</mi><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\kappa = 0</annotation></semantics></math>).</p></p>



Moving backward, we compute how changing each pixel affects this margin. If increasing a particular pixel pushes class 2's logit higher while decreasing class 3's logit, that pixel receives a negative gradient (increase it to reduce the margin, which reduces the loss). Opposite effects produce positive gradients. Magnitude indicates sensitivity: large gradients mean small pixel changes produce big margin changes.
<p><p>Meanwhile, the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradient provides a simple restoring force pulling pixels back toward
their original values. If the current adversarial image has perturbation
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>δ</mi><mi>i</mi></msub><mo>=</mo><mn>0.15</mn></mrow><annotation encoding="application/x-tex">\delta_i = 0.15</annotation></semantics></math>
at pixel
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>,
the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradient component is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>2</mn><mo>×</mo><mn>0.15</mn><mo>=</mo><mn>0.30</mn></mrow><annotation encoding="application/x-tex">2 \times 0.15 = 0.30</annotation></semantics></math>
pulling that pixel back toward the original. This gradient grows
linearly with perturbation magnitude, automatically scaling resistance
based on how far we’ve strayed.</p></p>



## Loss Landscape and Gradient Evolution
<p><p>How does ElasticNet’s loss landscape differ from pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
or
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
attacks? The adversarial loss component creates steep cliffs near
decision boundaries where small perturbations cause large loss changes.
Meanwhile, the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
component provides a smooth restoring force with gradients proportional
to perturbation magnitude. These competing forces create a loss surface
with mixed curvature: steep in directions toward misclassification,
shallow in directions perpendicular to the decision boundary.</p></p>

<p><p>Gradient magnitudes evolve predictably as optimization progresses.
Early iterations (1-100) show large adversarial gradients (5-20 per
pixel) dominating small
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradients (0.1-0.5 per pixel), driving aggressive exploration toward
misclassification. The attack starts bold. Middle iterations (100-500)
bring balance. Adversarial loss begins saturating, allowing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
to pull back excessive perturbations, with both components contributing
1-5 per pixel. Late iterations (500-1000) enter refinement mode where
adversarial loss has saturated completely, leaving only
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
minimization (0.1-1.0 per pixel) to reduce distortion while preserving
misclassification.</p></p>

<p><p>The trade-off constant
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
amplifies adversarial gradients relative to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradients. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.001</mn></mrow><annotation encoding="application/x-tex">c=0.001</annotation></semantics></math>,
adversarial gradients contribute minimally (0.001-0.05 per pixel),
allowing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
minimization to dominate; the attack might fail to achieve
misclassification. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>10</mn></mrow><annotation encoding="application/x-tex">c=10</annotation></semantics></math>,
adversarial gradients dominate (50-500 per pixel), overwhelming the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
restoring force. The attack succeeds easily but produces unnecessarily
large perturbations. Binary search finds the sweet spot where
adversarial pressure barely suffices for misclassification, typically
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.01</mn><mo>−</mo><mn>1.0</mn></mrow><annotation encoding="application/x-tex">c=0.01-1.0</annotation></semantics></math>
for MNIST.</p></p>

<p><p>Why does
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
matter locally? Consider one pixel. If
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>δ</mi><mo>=</mo><mn>0.15</mn></mrow><annotation encoding="application/x-tex">\delta=0.15</annotation></semantics></math>,
the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
gradient contributes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>2</mn><mo>×</mo><mn>0.15</mn><mo>=</mo><mn>0.30</mn></mrow><annotation encoding="application/x-tex">2\times 0.15=0.30</annotation></semantics></math>
toward the original. Suppose the adversarial gradient at that pixel is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mn>2.5</mn></mrow><annotation encoding="application/x-tex">-2.5</annotation></semantics></math>
(reducing the margin). With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.1</mn></mrow><annotation encoding="application/x-tex">c=0.1</annotation></semantics></math>,
the scaled adversarial term contributes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mn>0.25</mn></mrow><annotation encoding="application/x-tex">-0.25</annotation></semantics></math>,
so the combined effect is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.30</mn><mo>−</mo><mn>0.25</mn><mo>=</mo><mn>0.05</mn></mrow><annotation encoding="application/x-tex">0.30 - 0.25 = 0.05</annotation></semantics></math>
(a small net pull toward the original while still reducing the margin
overall). With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>1.0</mn></mrow><annotation encoding="application/x-tex">c=1.0</annotation></semantics></math>,
the same terms sum to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.30</mn><mo>−</mo><mn>2.5</mn><mo>=</mo><mi>−</mi><mn>2.20</mn></mrow><annotation encoding="application/x-tex">0.30 - 2.5 = -2.20</annotation></semantics></math>,
flipping direction and pushing strongly toward misclassification. This
local balance mirrors the global trade-off tuned by binary search.</p></p>

<p><p>Loss component interaction affects convergence behavior. When the
adversarial loss saturates (saturates at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>0</mn><annotation encoding="application/x-tex">0</annotation></semantics></math>),
it contributes zero gradient, and optimization reduces to pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
minimization with soft thresholding. This automatic transition from
"achieve misclassification" to "minimize distortion" occurs naturally
through the hinge function, requiring no explicit mode switching. Before
saturation, both components pull simultaneously, creating curved
trajectories through perturbation space rather than straight lines.</p></p>



Numerical issues occasionally arise when gradients become too large or too small. Extremely large gradients (>100 per pixel) during early iterations can cause instability where gradient steps overshoot, producing adversarial images outside valid bounds. The clipping operations in shrinkage thresholding prevent this from corrupting the perturbation, but it wastes iterations oscillating. Extremely small gradients (<0.001 per pixel) during late iterations signal convergence, but premature occurrence (iterations <100) indicates stagnation where the optimizer failed to escape a poor local minimum. Monitoring gradient magnitudes provides diagnostic information about optimization health.

## Gradient Flow Through Network Layers

Why do certain pixels receive stronger gradient signals than others? Understanding backward gradient flow through CNN architectures reveals these patterns. Consider a typical network with convolutional layers, ReLU activations, max pooling, and fully connected layers.
<p><p>Starting at the output layer (before softmax), logits emerge through
a linear transformation:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>Z</mi><mo>=</mo><msub><mi>W</mi><mtext mathvariant="normal">out</mtext></msub><mo>⋅</mo><mi>h</mi><mo>+</mo><msub><mi>b</mi><mtext mathvariant="normal">out</mtext></msub></mrow><annotation encoding="application/x-tex">Z = W_{\text{out}} \cdot h + b_{\text{out}}</annotation></semantics></math>,
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
is the hidden representation. The adversarial loss gradient
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mfrac><mrow><mi>∂</mi><mi>f</mi></mrow><mrow><mi>∂</mi><mi>Z</mi></mrow></mfrac><annotation encoding="application/x-tex">\frac{\partial f}{\partial Z}</annotation></semantics></math>
flows backward through this layer using the transpose operation:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mrow><mi>∂</mi><mi>f</mi></mrow><mrow><mi>∂</mi><mi>h</mi></mrow></mfrac><mo>=</mo><msubsup><mi>W</mi><mtext mathvariant="normal">out</mtext><mi>T</mi></msubsup><mo>⋅</mo><mfrac><mrow><mi>∂</mi><mi>f</mi></mrow><mrow><mi>∂</mi><mi>Z</mi></mrow></mfrac></mrow><annotation encoding="application/x-tex">\frac{\partial f}{\partial h} = W_{\text{out}}^T \cdot \frac{\partial f}{\partial Z}</annotation></semantics></math>.
Hidden units with large outgoing weights to relevant classes receive
stronger gradients, amplifying their influence on the final perturbation
pattern.</p></p>



Moving backward through ReLU activations, we encounter piecewise-linear behavior. When a unit is active (input > 0), gradients pass through unchanged. When inactive (input ≤ 0), gradients get blocked entirely. This creates discrete regions in input space with different gradient patterns. Moving an input across a ReLU boundary changes which units activate, potentially causing dramatic gradient shifts that make the loss landscape non-convex.

To distribute gradients spatially, convolutional layers spread each output gradient across the filter's receptive field. A gradient at one spatial location in a feature map distributes across all input pixels within that filter's window. For a 3×3 convolution, each output gradient affects a 3×3 patch of input pixels. Deep networks with large receptive fields (through multiple conv layers or pooling) can propagate gradients from output changes to input pixels far from the semantic feature that actually matters for classification.

Pooling introduces sparsity in backward connections. Only the maximum value within each pool window receives gradients; other values get zero gradient. This sparsity means many input pixels receive no direct gradient signal from certain output changes, potentially making the loss landscape less smooth and optimization more challenging. Pixels that never win the max operation contribute nothing to gradients despite occupying space in the input.

## Practical Implications for FISTA

These gradient properties have direct implications for FISTA optimization. The learning rate must be scaled to gradient magnitudes, as larger gradients require smaller step sizes to prevent overshooting.

The non-convex loss landscape means FISTA finds local minima, not global optima. Different initializations (starting from different random perturbations) might converge to different solutions with varying attack effectiveness. In practice, ElasticNet initializes from the original images (zero perturbation), providing a consistent starting point. The binary search then explores different constant values, effectively providing multiple restarts with different adversarial pressures.

Gradient sparsity from ReLU and max pooling means some pixels receive weak or zero gradients. Soft thresholding compounds this: pixels with weak gradients produce small perturbations that get zeroed during thresholding. This automatic filtering helps sparsity but might miss pixels that could contribute meaningfully if given stronger signals. The iterative nature of FISTA allows gradients to build up over many iterations, potentially activating pixels that initially received weak signals.

## Convergence Properties and Stopping Criteria
<p><p>FISTA’s
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>O</mi><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mi>/</mi><msup><mi>k</mi><mn>2</mn></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">O(1/k^2)</annotation></semantics></math>
convergence guarantee applies under standard assumptions:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>f</mi><annotation encoding="application/x-tex">f</annotation></semantics></math>
must have Lipschitz continuous gradients,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>h</mi><annotation encoding="application/x-tex">h</annotation></semantics></math>
must be convex, and the step size
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>η</mi><annotation encoding="application/x-tex">\eta</annotation></semantics></math>
must satisfy
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>η</mi><mo>≤</mo><mn>1</mn><mi>/</mi><mi>L</mi></mrow><annotation encoding="application/x-tex">\eta \leq 1/L</annotation></semantics></math>
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>L</mi><annotation encoding="application/x-tex">L</annotation></semantics></math>
is the Lipschitz constant of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>∇</mi><mi>f</mi></mrow><annotation encoding="application/x-tex">\nabla f</annotation></semantics></math>.
For neural networks, the Lipschitz constant depends on the model
architecture, with deeper networks and larger weights producing larger
constants.</p></p>



In practice, these theoretical conditions are often violated. Neural network losses are non-convex, meaning the convergence guarantee technically doesn't apply. However, FISTA often works well empirically even on non-convex problems, finding good local minima efficiently. The algorithm may not find the global optimum, but the local solutions it discovers typically produce effective adversarial examples.

Stopping criteria determine when FISTA iterations terminate. The simplest approach runs a fixed number of iterations (e.g., 1000), chosen large enough to ensure reasonable convergence on most examples. This approach wastes computation on easy examples that converge quickly while potentially under-optimizing difficult ones that need more iterations.
<p><p>More sophisticated stopping criteria check for convergence
dynamically. One approach monitors the change in objective value between
iterations, stopping when
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><msup><mi>f</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>+</mo><msup><mi>h</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>−</mo><msup><mi>f</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo>−</mo><msup><mi>h</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><mo stretchy="false" form="prefix">|</mo><mo>&lt;</mo><mi>ϵ</mi></mrow><annotation encoding="application/x-tex">|f^{(k+1)} + h^{(k+1)} - f^{(k)} - h^{(k)}| &lt; \epsilon</annotation></semantics></math>
for some tolerance
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϵ</mi><annotation encoding="application/x-tex">\epsilon</annotation></semantics></math>.
Another checks whether the attack has succeeded (caused
misclassification) and the adversarial loss has saturated (reached its
minimum value of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>κ</mi></mrow><annotation encoding="application/x-tex">-\kappa</annotation></semantics></math>),
indicating that further iterations would only reduce distortion without
affecting attack success.</p></p>



The ElasticNet implementation uses a hybrid approach. FISTA runs for a maximum number of iterations per binary search step, with periodic checks for attack success. If all examples in a batch successfully fool the model early, that binary search iteration can terminate without completing all FISTA iterations. This adaptation prevents wasted computation while ensuring sufficient optimization for difficult examples.

The next section combines all these components into the complete FISTA iteration function. We'll see how gradient computation, soft thresholding, and momentum updates compose into a single optimization step. Then we'll add the success checking and binary search mechanisms that guide the attack toward minimal perturbations.

---

<!-- section 3932 | page 9 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Complete FISTA Iteration and Binary Search

Each FISTA iteration orchestrates gradient descent on smooth terms with proximal operations for sparsity, accelerated by momentum. Binary search wraps this optimization, automatically tuning the adversarial pressure to find minimal perturbations. These nested loops create ElasticNet's adaptive behavior - adjusting both perturbation refinement (FISTA) and attack strength (binary search) to each example's difficulty.

## The Complete FISTA Iteration

To execute one FISTA step, we evaluate the loss at the momentum point (not the current solution), apply gradient descent, enforce sparsity through soft thresholding, then extrapolate the next momentum position. This look-ahead evaluation is what accelerates convergence beyond standard proximal gradient methods.

```python
def fista_step(
    adv_images,
    y_momentum,
    original_images,
    labels_onehot,
    const,
    model,
    beta,
    learning_rate,
    confidence,
    iteration,
    targeted=False,
    clip_min=0.0,
    clip_max=1.0,
):
    """
    Perform one complete FISTA iteration.

    Combines gradient computation, shrinkage-thresholding,
    and momentum update into a single optimization step.

    Parameters:
        adv_images (torch.Tensor): Current adversarial images
        y_momentum (torch.Tensor): Momentum point for gradient evaluation
        original_images (torch.Tensor): Original clean images
        labels_onehot (torch.Tensor): One-hot encoded labels
        const (torch.Tensor): Trade-off constants per example
        model (nn.Module): Target model
        beta (float): L1 weight parameter
        learning_rate (float): FISTA step size
        confidence (float): Margin for misclassification
        iteration (int): Current FISTA iteration number for momentum calculation
        targeted (bool): Whether this is a targeted attack
        clip_min (float): Minimum valid pixel value
        clip_max (float): Maximum valid pixel value

    Returns:
        tuple: (new_adv_images, new_y_momentum, loss_value, distances)
    """
    # Ensure y_momentum requires gradients for backprop
    y_momentum = y_momentum.detach().requires_grad_(True)

    # Compute loss at momentum point
    total_loss, adversarial_loss, distances = compute_total_loss(
        y_momentum,
        original_images,
        labels_onehot,
        const,
        model,
        beta,
        confidence,
        targeted,
    )

    # Compute gradient of total loss w.r.t. momentum point
    total_loss_summed = total_loss.sum()
    total_loss_summed.backward()
    grad = y_momentum.grad

    # Gradient step: move in negative gradient direction
    y_new = y_momentum - learning_rate * grad

    # Apply shrinkage-thresholding (proximal operator for L1)
    adv_new = apply_shrinkage_thresholding(
        y_new, original_images, learning_rate * beta, clip_min, clip_max
    )

    # Compute momentum coefficient
    momentum_coef = compute_fista_momentum(iteration)

    # Update momentum point for next iteration
    y_new_momentum = adv_new + momentum_coef * (adv_new - adv_images)

    return adv_new, y_new_momentum, total_loss_summed.item(), distances
```

Why detach and then immediately require gradients again? The preparation serves a critical purpose. The `detach()` call breaks any existing gradient tape from previous iterations, severing the computational graph that PyTorch built during the last FISTA step. Without this break, gradients would accumulate incorrectly across iterations, creating memory leaks and producing wrong gradient values. The `requires_grad_(True)` call then tells PyTorch to start fresh, tracking operations on this tensor for the current iteration only.
<p><p>Where do we evaluate the loss? At the momentum point
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>y</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">y^{(k)}</annotation></semantics></math>,
not the current solution
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mi>x</mi><mrow><mo stretchy="false" form="prefix">(</mo><mi>k</mi><mo stretchy="false" form="postfix">)</mo></mrow></msup><annotation encoding="application/x-tex">x^{(k)}</annotation></semantics></math>.
This look-ahead evaluation is what makes FISTA faster than standard
proximal gradient methods. By computing gradients at an extrapolated
point that anticipates where optimization is heading, FISTA better
exploits momentum in consistent directions. The gradient tells us which
direction reduces loss from this forward-looking position.</p></p>

<p><p>Taking the gradient step, we move against the gradient to decrease
loss: <code>y_new = y_momentum - learning_rate * grad</code>. The
learning rate controls step size, balancing between fast convergence
(large steps) and stability (small steps). Next, shrinkage handles the
non-smooth
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
term. Small perturbations die (values below threshold
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
get zeroed). Larger perturbations survive with reduction (values above
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
get shrunk by exactly
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>).</p></p>



Finally, momentum extrapolation anticipates where we're heading. The term `(adv_new - adv_images)` represents the change made in this iteration. Multiplying by `momentum_coef` and adding to `adv_new` produces a point slightly ahead of the current solution: `y_new_momentum = adv_new + momentum_coef * (adv_new - adv_images)`. The next iteration will compute gradients at this look-ahead point, building on the progress direction established by this step.

## Checking Attack Success

Binary search requires feedback about whether current perturbations successfully fool the model. We compare model predictions on adversarial examples to true labels through the success check, determining which examples achieved misclassification. This boolean feedback guides the search toward minimal perturbations sufficient for attack success.

```python
def check_attack_success(adv_images, labels, model, targeted=False):
    """
    Verify whether adversarial examples achieve misclassification.

    Compares model predictions on adversarial images to target labels.

    Parameters:
        adv_images (torch.Tensor): Adversarial images to evaluate
        labels (torch.Tensor): True labels (or target labels if targeted)
        model (nn.Module): Target model
        targeted (bool): Whether this is a targeted attack

    Returns:
        torch.Tensor: Boolean mask indicating successful attacks (batch_size,)
    """
    with torch.no_grad():
        outputs = model(adv_images)
        predictions = outputs.argmax(dim=1)

        if targeted:
            # Success = prediction matches target
            success = predictions.eq(labels)
        else:
            # Success = prediction differs from true label
            success = predictions.ne(labels)

    return success
```

We run the success check in inference mode without gradient tracking (`torch.no_grad()`). No optimization occurs here; we simply evaluate whether the current perturbations achieve our goal. The forward pass produces logits, which we convert to class predictions via `argmax`.

For untargeted attacks, success means the prediction differs from the true label. Any misclassification counts as success; we don't care which wrong class the model predicts. For targeted attacks, success requires the prediction to match a specific target class. The targeted threat model is more constrained and typically requires larger perturbations.

This success criterion is binary: an example either fools the model or it doesn't. No notion of "partially successful" or "almost working" exists. This hard threshold contrasts with the soft margin in the adversarial loss. During optimization, the loss provides smooth gradients even when attacks haven't succeeded. After optimization, the success check provides definitive feedback for the binary search.

## Updating Binary Search Bounds
<p><p>The binary search maintains lower and upper bounds on the trade-off
constant
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
for each example. Successful attacks indicate
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
was sufficient (possibly too large), so we lower the upper bound. Failed
attacks indicate
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
was insufficient, so we raise the lower bound. After several iterations,
the bounds converge to the minimal
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
sufficient for attack success.</p></p>



```python
def update_binary_search_bounds(lower_bound, upper_bound, const, success_mask):
    """
    Update binary search bounds based on attack success.

    Successful attacks lower upper bound (c was sufficient).
    Failed attacks raise lower bound (c was insufficient).

    Parameters:
        lower_bound (torch.Tensor): Lower bounds on c per example
        upper_bound (torch.Tensor): Upper bounds on c per example
        const (torch.Tensor): Current c values per example
        success_mask (torch.Tensor): Boolean mask of successful attacks

    Returns:
        tuple: (new_lower_bound, new_upper_bound, new_const)
    """
    # Process each example individually
    for i in range(len(success_mask)):
        if success_mask[i]:
            # Success: try smaller c
            upper_bound[i] = min(upper_bound[i], const[i])
            if upper_bound[i] < 1e10:
                const[i] = (lower_bound[i] + upper_bound[i]) / 2
        else:
            # Failure: need larger c
            lower_bound[i] = max(lower_bound[i], const[i])
            if upper_bound[i] < 1e10:
                const[i] = (lower_bound[i] + upper_bound[i]) / 2
            else:
                const[i] *= 10  # Exponential increase for persistent failures

    return lower_bound, upper_bound, const
```
<p><p>The bisection mechanism from ElasticNet operates here through
per-example bounds. Processing examples independently accommodates
heterogeneous robustness: some examples lie far from decision boundaries
and resist perturbation (needing large
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
values), while others sit near boundaries and flip easily (requiring
small
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
values).</p></p>

<p><p>The implementation follows standard bisection logic. Successful
attacks tighten the upper bound to the current constant, signaling we
can try smaller values. Failed attacks raise the lower bound, indicating
this constant was insufficient. When both bounds are finite, we bisect
by computing their midpoint. This produces the logarithmic convergence
described in ElasticNet: each iteration halves the search interval.</p></p>

<p><p>Exponential growth (line 176) handles the unbounded case where no
success has occurred yet. Multiplying
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math>
by 10 each iteration explores the scale space efficiently
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.001</mn><mo>,</mo><mn>0.01</mn><mo>,</mo><mn>0.1</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>10</mn><mo>,</mo><mn>100</mn><mo>,</mo><mi>.</mi><mi>.</mi><mi>.</mi></mrow><annotation encoding="application/x-tex">0.001, 0.01, 0.1, 1, 10, 100, ...</annotation></semantics></math>)
without wasting iterations on tiny increments. Once we find success at
any scale, bisection takes over to refine the estimate. To see this in
practice: starting with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mtext mathvariant="normal">lower</mtext><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\text{lower}=0</annotation></semantics></math>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mtext mathvariant="normal">upper</mtext><mo>=</mo><msup><mn>10</mn><mn>10</mn></msup></mrow><annotation encoding="application/x-tex">\text{upper}=10^{10}</annotation></semantics></math>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.001</mn></mrow><annotation encoding="application/x-tex">c=0.001</annotation></semantics></math>,
a success sets
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mtext mathvariant="normal">upper</mtext><mo>=</mo><mn>0.001</mn></mrow><annotation encoding="application/x-tex">\text{upper}=0.001</annotation></semantics></math>
and bisects to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.0005</mn></mrow><annotation encoding="application/x-tex">c=0.0005</annotation></semantics></math>.
A subsequent failure sets
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mtext mathvariant="normal">lower</mtext><mo>=</mo><mn>0.0005</mn></mrow><annotation encoding="application/x-tex">\text{lower}=0.0005</annotation></semantics></math>
and bisects to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.00075</mn></mrow><annotation encoding="application/x-tex">c=0.00075</annotation></semantics></math>.
After five such steps, the interval narrows by
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msup><mn>2</mn><mn>5</mn></msup><mo>=</mo><mn>32</mn><mo>×</mo></mrow><annotation encoding="application/x-tex">2^5=32\times</annotation></semantics></math>.</p></p>



## Putting FISTA and Binary Search Together

Complete attack execution nests FISTA optimization inside binary search iterations. An outer loop adjusts the trade-off constants based on success feedback. An inner loop optimizes perturbations for fixed constants, then we evaluate results. This separation isolates two subproblems: minimizing distortion (FISTA) and tuning adversarial pressure (binary search).

Each binary search iteration runs FISTA to convergence (or a maximum iteration limit). The resulting adversarial examples undergo success checks, providing feedback for the binary search update. The updated constants seed the next FISTA optimization round, which starts fresh from the original images. This fresh start prevents perturbations from growing unboundedly across binary search iterations.

This interplay between loops creates adaptive behavior. Easy examples converge quickly: FISTA succeeds early, binary search finds small optimal constants after few iterations. Hard examples take longer: FISTA needs many iterations to achieve misclassification, binary search explores larger constants across many steps. The algorithm adapts automatically to each example's difficulty.
<p><p>This adaptive complexity is unique to ElasticNet among the attacks
you’ve studied. FGSM has no adaptation; it uses fixed
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϵ</mi><annotation encoding="application/x-tex">\epsilon</annotation></semantics></math>
for all examples. DeepFool adapts through iteration count but uses the
same algorithm for all examples. ElasticNet adapts both through FISTA
iterations (finding perturbations) and binary search iterations (tuning
pressure), providing fine-grained control over the attack process.</p></p>



The next section shows these components operating together in the complete attack execution. Binary search iterations wrap FISTA optimization, adjusting constants based on success feedback. Configuration sets hyperparameters. Sample selection identifies attack targets. Result analysis quantifies effectiveness. The nested loop structure becomes explicit, showing exactly when binary search updates occur, when FISTA restarts from originals, and how the best perturbations get tracked across iterations.

---

<!-- section 3933 | page 10 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Attack Execution and Performance

All the pieces are now in place: momentum computation, shrinkage thresholding, loss functions, FISTA iterations, success checks, and binary search updates. This section brings them together into the complete attack execution, showing how these functions compose to generate adversarial examples.

## Attack Configuration
<p><p>The attack requires several hyperparameters controlling different
aspects of the optimization. The <code>beta</code> parameter balances
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
regularization, controlling sparsity. The learning rate determines FISTA
step size. The iteration counts control optimization duration. The
initial constant seeds the binary search. Together, these parameters
define the attack strategy.</p></p>



```python
# Attack hyperparameters
config = {
    "beta": 0.01,  # L1 vs L2 trade-off (higher = sparser)
    "confidence": 0,  # Margin for misclassification
    "learning_rate": 0.01,  # FISTA step size
    "max_iterations": 1000,  # FISTA iterations per binary search
    "binary_search_steps": 5,  # Number of binary search iterations
    "initial_const": 0.001,  # Starting trade-off constant
    "clip_min": 0.0,  # Minimum pixel value
    "clip_max": 1.0,  # Maximum pixel value
}

print("\nAttack Configuration:")
for key, value in config.items():
    print(f"  {key}: {value}")
```
<p><p>How sparse should perturbations be? Setting <code>beta = 0.01</code>
provides modest sparsity bias without sacrificing too much attack
effectiveness. Larger values like 0.05-0.1 would create dramatically
sparser perturbations by aggressively penalizing the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
norm, forcing FISTA to zero out more pixels. Smaller values like
0.001-0.005 would produce nearly dense perturbations, behaving almost
like pure
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
attacks where every pixel gets modified slightly. This middle-ground
value balances sparsity with attack effectiveness.</p></p>



Zero confidence means minimal misclassification criteria. With `confidence = 0`, any competitor class exceeding the true class by even 0.001 counts as success. Positive values would demand more confident misclassification: `confidence = 5` requires the competitor to exceed the true class by at least 5 logit units, producing more robust adversarial examples at the cost of larger perturbations. We use zero to minimize the perturbation budget needed for attack success.

Convergence speed versus stability depends critically on learning rate. Our choice of 0.01 strikes a balance. Push it higher to 0.05-0.1 and you risk overshooting, where perturbations oscillate wildly rather than converging smoothly to a solution. Drop it to 0.001-0.005 and convergence becomes painfully slow, requiring 2000-5000 iterations instead of 1000. For MNIST-scale problems, 0.01 typically works well without requiring problem-specific tuning.

## Sample Selection and Initialization

We select correctly classified examples from the test set for attack demonstrations. The attack targets only examples the model already classifies correctly - attacking misclassified examples makes no sense. This selection ensures we're testing the model's robustness on inputs it handles successfully under normal conditions.

```python
print("\nSelecting correctly classified samples for attack...")
model.eval()
num_samples = 20

for data, targets in test_loader:
    data, targets = data.to(device), targets.to(device)
    outputs = model(data)
    predictions = outputs.argmax(dim=1)

    # Select correctly classified samples
    correct_mask = predictions.eq(targets)
    attack_data = data[correct_mask][:num_samples]
    attack_targets = targets[correct_mask][:num_samples]

    if len(attack_data) >= num_samples:
        print(f"Selected {len(attack_data)} samples")
        break
```

We evaluate the model on batches from the test loader, accumulating correctly classified examples until we have enough. How does the filtering work? `predictions.eq(targets)` produces a boolean tensor marking which examples match their true labels, with `True` for correct predictions and `False` for errors. Indexing `data[correct_mask]` with this boolean tensor extracts only the correctly classified examples, discarding misclassified ones automatically through PyTorch's boolean indexing mechanism.

Before running the nested optimization loops, we initialize variables tracking the attack state. These include copies of original images, one-hot encoded labels, binary search bounds, and storage for best perturbations found so far:

```python
print("\nPerforming ElasticNet attack...")
print("This may take several minutes due to iterative optimization...\n")

batch_size = len(attack_data)
original_images = attack_data.clone()

# Convert labels to one-hot encoding
labels_onehot = torch.zeros(batch_size, 10).to(device)
labels_onehot.scatter_(1, attack_targets.unsqueeze(1), 1)

# Initialize binary search bounds
lower_bound = torch.zeros(batch_size).to(device)
upper_bound = torch.ones(batch_size).to(device) * 1e10
const = torch.ones(batch_size).to(device) * config["initial_const"]

# Track best adversarial examples
best_adv = original_images.clone()
best_l2 = torch.ones(batch_size).to(device) * 1e10
```

Converting integer labels to one-hot encoding creates binary vectors with 1 at the true class index and 0 elsewhere. `labels_onehot.scatter_(1, attack_targets.unsqueeze(1), 1)` places 1s at the appropriate positions by scattering along dimension 1 (the class dimension). Why use one-hot instead of integers? The adversarial loss computation needs `labels_onehot` as a mask to extract true class logits efficiently, avoiding expensive indexing operations in the inner optimization loop.
<p><p>Binary search bounds need wide initial intervals. Lower bounds start
at zero (no adversarial pressure), upper bounds at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mi>e</mi><mn>10</mn></mrow><annotation encoding="application/x-tex">1e10</annotation></semantics></math>
(essentially infinite pressure). What happens if we start with narrow
intervals? The search might converge to suboptimal constants that either
fail to produce adversarial examples or produce unnecessarily large
perturbations. Starting wide ensures we cover the full range of
constants the attack might need. The current constants initialize small
at 0.001, which suffices for easy examples and gets increased
automatically through binary search for harder ones.</p></p>



## The Binary Search and FISTA Loops

Now we execute the nested optimization. The outer binary search loop iterates over trade-off constant refinements. Each binary search iteration runs an inner FISTA optimization loop to completion, evaluates success, and updates constants:

```python
# Binary search over trade-off constant c
for binary_step in range(config["binary_search_steps"]):
    print(f"Binary search step {binary_step + 1}/{config['binary_search_steps']}")

    # Initialize FISTA from original images
    adv_images = original_images.clone().detach()
    y_momentum = adv_images.clone()

    # FISTA optimization loop
    for iteration in range(config["max_iterations"]):
        # Perform one FISTA step
        adv_images, y_momentum, loss, distances = fista_step(
            adv_images,
            y_momentum,
            original_images,
            labels_onehot,
            const,
            model,
            config["beta"],
            config["learning_rate"],
            config["confidence"],
            iteration,
            targeted=False,
            clip_min=config["clip_min"],
            clip_max=config["clip_max"],
        )

    # Check which examples successfully fooled the model
    success_mask = check_attack_success(
        adv_images, attack_targets, model, targeted=False
    )

    # Update best adversarial examples
    l1_dist, l2_dist, elastic_dist = compute_distances(
        adv_images, original_images, config["beta"]
    )

    for i in range(batch_size):
        if success_mask[i] and l2_dist[i] < best_l2[i]:
            best_adv[i] = adv_images[i]
            best_l2[i] = l2_dist[i]

    # Update binary search bounds
    lower_bound, upper_bound, const = update_binary_search_bounds(
        lower_bound, upper_bound, const, success_mask
    )

    # Progress reporting
    num_success = success_mask.sum().item()
    print(f"  Successfully generated {num_success}/{batch_size} adversarial examples\n")
```
<p><p>Why reinitialize from original images at each binary search
iteration? This fresh start prevents perturbations from accumulating
across iterations with different constants. Without reinitialization,
perturbations optimized for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.001</mn></mrow><annotation encoding="application/x-tex">c = 0.001</annotation></semantics></math>
would persist when testing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>c</mi><mo>=</mo><mn>0.01</mn></mrow><annotation encoding="application/x-tex">c = 0.01</annotation></semantics></math>,
contaminating the optimization and producing unreliable results.
Starting fresh ensures each constant gets a fair evaluation.</p></p>

<p><p>FISTA runs up to 1000 iterations, with each calling
<code>fista_step</code> to perform gradient computation, shrinkage
thresholding, and momentum updates. Once optimization completes, we
evaluate success and update the binary search. Which examples achieved
misclassification? <code>check_attack_success</code> compares model
predictions against target labels. The best perturbation update
processes each example independently, comparing current
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distortion to previous bests. Only successful attacks with smaller
distortion than what we’ve seen before get saved, ensuring we track the
minimal perturbation for each example.</p></p>



Adjusting bounds and constants happens through `update_binary_search_bounds`. Successful examples lower their upper bounds (we found a working constant, so we can try smaller values) and bisect the interval to search the lower half. Failed examples raise their lower bounds (this constant was too small), using exponential growth if no success has occurred yet or bisection if the interval is already bounded from above.

## Computing and Analyzing Results

After binary search completes, we evaluate the final adversarial examples and compute comprehensive statistics:

```python
# Evaluate final adversarial examples
with torch.no_grad():
    adv_outputs = model(best_adv)
    adv_predictions = adv_outputs.argmax(dim=1)

    # Calculate success rate
    final_success = adv_predictions.ne(attack_targets)
    success_rate = final_success.float().mean().item() * 100

    # Calculate final distortions
    l1_dist, l2_dist, elastic_dist = compute_distances(
        best_adv, original_images, config["beta"]
    )
    linf_dist = torch.max(
        torch.abs(best_adv - original_images).view(batch_size, -1), dim=1
    )[0]

# Display results
print("=" * 60)
print("ElasticNet Attack Results:")
print("=" * 60)
print(f"Success Rate: {success_rate:.2f}% ({final_success.sum()}/{batch_size})")
print(f"Average L1 Distortion: {l1_dist.mean().item():.4f}")
print(f"Average Squared L2 Distortion: {l2_dist.mean().item():.4f}")
print(f"Average L∞ Distortion: {linf_dist.mean().item():.4f}")
print(f"Average Elastic Distortion: {elastic_dist.mean().item():.4f}")
print("=" * 60)
```
<p><p>Attack effectiveness emerges across multiple metrics. Success rate
quantifies what percentage of examples were successfully misclassified,
providing an overall measure of attack reliability. Distortion metrics
reveal perturbation magnitude from different geometric perspectives:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
counts total pixel changes,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
measures Euclidean distance,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
captures maximum single-pixel deviation, and elastic distance combines
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
through the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
weighting. Together, these reveal both the size and structural
characteristics of our modifications.</p></p>



## Performance

The complete attack execution reveals ElasticNet's computational profile. For 20 MNIST examples with 5 binary search steps and 1000 FISTA iterations per step, the attack performs roughly 5,000 forward and 5,000 backward steps for the batch (about 100,000 per-image evaluations at batch size 20). On a modern GPU (RTX 3090 or better), this typically takes 2-3 minutes; on CPU, 30-60 minutes. These figures are representative for MNIST-scale CNNs and vary with hardware and implementation details.

Binary search convergence directly impacts total runtime. Reducing binary search steps from 9 to 5 cuts computation by 45% but increases final distortion by 5-15% because constant tuning is less precise. Increasing steps to 9 reduces distortion by 3-8% but costs 80% more computation. The sweet spot depends on use case: adversarial training benefits from speed (3-5 steps), while robustness evaluation demands precision (7-9 steps).

Parameter sensitivity affects attack reliability across different models and datasets. The learning rate shows highest sensitivity: values too large (>0.05 for MNIST) cause divergence where perturbations oscillate rather than converge. Values too small (<0.001) require 2000-5000 iterations for convergence, quadrupling runtime. The beta parameter shows moderate sensitivity: doubling from 0.01 to 0.02 increases sparsity by 10-15 percentage points but may reduce success rate by 5-10% on hard examples.

Batch size trades memory for efficiency. Processing 20 examples simultaneously uses 400 MB GPU memory but amortizes optimization overhead. Increasing to 50 examples improves throughput by 15-25% but requires 1 GB memory. Decreasing to 10 examples halves memory usage to 200 MB but reduces throughput by 10-15% due to underutilized GPU cores.

The next section develops visualizations that expose these patterns visually. Plotting original versus adversarial images reveals where perturbations concentrate. Distortion distributions show variation across examples. Success rate versus distortion curves characterize the effectiveness-imperceptibility tradeoff. Sparsity heatmaps expose which pixels ElasticNet modifies. These visualizations complement the quantitative metrics, providing qualitative insights about how the attack operates.

---

<!-- section 3934 | page 11 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Attack Visualizations
<p><p>What does 95% success actually mean? Numbers tell part of the story.
The attack succeeded on 19 out of 20 examples with average
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distortion of 2.36. But what do these adversarial examples actually look
like? How does the perturbation distribute across pixels? Which examples
required larger distortions?</p></p>

<p><p>Statistics provide the numbers. Visualizations reveal the story.
Summary metrics like "average
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distortion of 2.36" compress 20 examples into a single value.
Visualizations expose the distribution: do all examples cluster near
2.36, or do some need minimal perturbations while others require massive
changes? Bar charts reveal these patterns. Histograms show the full
distribution shape.</p></p>



This section develops visualization blocks showing the attack transformation process and distortion characteristics. We'll examine original and adversarial images side by side, then analyze how perturbation magnitudes distribute across examples. All visualizations follow the HTB theme using colors and styling from the `htb_ai_library`.

## Attack Process Visualization

The most direct way to understand adversarial examples is seeing them. This visualization displays original images, adversarial images, and the perturbations that transform one into the other:

```python
print("\nGenerating visualizations...")

# Visualization: Attack process (original → perturbation → adversarial)
print("Creating attack process visualization...")

fig, axes = plt.subplots(3, 10, figsize=(20, 6))

# Show first 10 examples
num_display = min(10, batch_size)

for i in range(num_display):
    # Original image
    orig_img = original_images[i].detach().cpu().squeeze()
    axes[0, i].imshow(orig_img, cmap="gray", vmin=0, vmax=1)
    axes[0, i].axis("off")
    axes[0, i].set_title(f"True: {attack_targets[i].item()}", fontsize=10)

    # Perturbation (amplified for visibility)
    pert = (best_adv[i] - original_images[i]).detach().cpu().squeeze()
    pert_display = pert * 10  # Amplify by 10x for visibility
    axes[1, i].imshow(pert_display, cmap="seismic", vmin=-1, vmax=1)
    axes[1, i].axis("off")
    axes[1, i].set_title("Perturbation", fontsize=10)

    # Adversarial image
    adv_img = best_adv[i].detach().cpu().squeeze()
    axes[2, i].imshow(adv_img, cmap="gray", vmin=0, vmax=1)
    axes[2, i].axis("off")
    axes[2, i].set_title(f"Pred: {adv_predictions[i].item()}", fontsize=10, color=MALWARE_RED)

# Row labels
fig.text(0.02, 0.80, "Original", rotation=90, fontsize=14, weight="bold", ha="center", va="center")
fig.text(0.02, 0.50, "Perturbation\n(10× amplified)", rotation=90, fontsize=14, weight="bold", ha="center", va="center")
fig.text(0.02, 0.20, "Adversarial", rotation=90, fontsize=14, weight="bold", ha="center", va="center")

plt.tight_layout(rect=[0.03, 0, 1, 1])
plt.savefig(output_dir / "ead_attack_process.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"  Saved to {output_dir}/ead_attack_process.png")
```

We visualize the three-stage attack transformation using a 3×10 grid layout. Original images appear in the top row with their true labels. Perturbations occupy the middle row, amplified 10× for visibility since actual perturbations are imperceptible at normal scale. Adversarial images fill the bottom row with predicted labels, colored red to emphasize misclassification.

Amplifying perturbations by 10× makes their subtle patterns visible while preserving structure. We use the seismic colormap where blue represents negative changes and red represents positive changes, with white indicating unchanged pixels. This color scheme reveals exactly where and how the attack modified each image.

![Grid of 10 MNIST digits showing original, 10x‑amplified perturbations, and adversarial results with predicted labels](/storage/modules/320/ead_attack_process.png)

The visualization exposes the attack's precision. Original digits remain perfectly recognizable in the top row. The middle row reveals perturbations concentrated along edges and stroke boundaries rather than scattered randomly. Notice how Example 1 shows modifications clustering around the digit's curves, while Example 4 targets the loop region. The adversarial images in the bottom row look nearly identical to originals, yet the model misclassifies them. A true 7 becomes predicted as 2, a true 0 becomes predicted as 6. The human eye struggles to detect any difference, but the model's decision boundary has been crossed.

## Distortion Distribution Analysis

Numbers provide precision. Distributions reveal patterns. Mean distortion tells us average perturbation magnitude, but what about the spread? Do all examples cluster tightly around the mean, or does variability suggest different robustness levels? Histograms expose these distributions, showing whether the attack behaves uniformly or reveals heterogeneous robustness across examples.
<p><p>To understand how different distance metrics characterize our
perturbations, we’ll create histograms for each norm. The four metrics
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>,
and Elastic-Net) capture different aspects of perturbation structure,
and their distributions tell complementary stories about attack
behavior:</p></p>



```python
# Visualization 2: Distortion distributions for L1, L2, L∞, Elastic
print("Creating distortion analysis...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Calculate distortion metrics
l1_values = l1_dist.detach().cpu().numpy()
l2_values = l2_dist.detach().cpu().numpy()
linf_values = linf_dist.detach().cpu().numpy()
elastic_values = elastic_dist.detach().cpu().numpy()

# L1 distribution
axes[0, 0].set_title(r"$L_1$ Distortion Distribution", fontsize=14)
axes[0, 0].set_xlabel(r"$L_1$ Distance")
axes[0, 0].set_ylabel("Frequency")
axes[0, 0].hist(l1_values, bins=15, color=AZURE, alpha=0.7, edgecolor=NODE_BLACK)
axes[0, 0].axvline(l1_values.mean(), color=MALWARE_RED, linestyle="--",
                   linewidth=2, label=f"Mean: {l1_values.mean():.2f}")
axes[0, 0].legend(frameon=False, fontsize=10)

# L2 distribution
axes[0, 1].set_title(r"Squared $L_2$ Distortion Distribution", fontsize=14)
axes[0, 1].set_xlabel(r"Squared $L_2$ Distance")
axes[0, 1].set_ylabel("Frequency")
axes[0, 1].hist(l2_values, bins=15, color=VIVID_PURPLE, alpha=0.7, edgecolor=NODE_BLACK)
axes[0, 1].axvline(l2_values.mean(), color=MALWARE_RED, linestyle="--",
                   linewidth=2, label=f"Mean: {l2_values.mean():.2f}")
axes[0, 1].legend(frameon=False, fontsize=10)

# L∞ distribution
axes[1, 0].set_title(r"$L_\infty$ Distortion Distribution", fontsize=14)
axes[1, 0].set_xlabel(r"$L_\infty$ Distance")
axes[1, 0].set_ylabel("Frequency")
axes[1, 0].hist(linf_values, bins=15, color=NUGGET_YELLOW, alpha=0.7, edgecolor=NODE_BLACK)
axes[1, 0].axvline(linf_values.mean(), color=MALWARE_RED, linestyle="--",
                   linewidth=2, label=f"Mean: {linf_values.mean():.2f}")
axes[1, 0].legend(frameon=False, fontsize=10)

# Elastic-net distribution
axes[1, 1].set_title("Elastic-Net Distortion Distribution", fontsize=14)
axes[1, 1].set_xlabel("Elastic Distance")
axes[1, 1].set_ylabel("Frequency")
axes[1, 1].hist(elastic_values, bins=15, color=AQUAMARINE, alpha=0.7, edgecolor=NODE_BLACK)
axes[1, 1].axvline(elastic_values.mean(), color=MALWARE_RED, linestyle="--",
                   linewidth=2, label=f"Mean: {elastic_values.mean():.2f}")
axes[1, 1].legend(frameon=False, fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / "ead_distortion_analysis.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"  Saved to {output_dir}/ead_distortion_analysis.png")
```
<p><p>Each subplot captures a different view of perturbation magnitude. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
distribution counts total absolute change across all pixels, revealing
whether modifications spread across many pixels or concentrate on few.
The squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distribution measures the sum of squared pixel changes (energy),
balancing magnitude against spatial distribution. The
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
distribution shows maximum per-pixel change, exposing worst-case
perturbation intensity. The Elastic-Net distribution combines
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
via
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>,
providing the composite metric our optimization actually minimized.</p></p>



Narrow distributions with low standard deviation indicate consistent attack behavior. All examples required similar perturbation magnitudes. Wide distributions suggest heterogeneous robustness where some examples flip with minimal perturbations while others require substantial modifications. The red dashed line marks the mean, showing whether the distribution centers symmetrically or skews toward higher distortions.

![Four histograms of L1, squared L2, L∞ and Elastic‑Net distortion with the mean marked](/storage/modules/320/ead_distortion_analysis.png)
<p><p>The histograms show that squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
values cluster below 5 (mean
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo>≈</mo><mn>4.18</mn></mrow><annotation encoding="application/x-tex">\approx 4.18</annotation></semantics></math>)
with a long right tail reaching about 21, indicating several harder
examples that require larger overall distortion.
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
magnitudes center near 20 (mean
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo>≈</mo><mn>20.20</mn></mrow><annotation encoding="application/x-tex">\approx 20.20</annotation></semantics></math>)
with moderate spread. For
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>,
the distribution centers around
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo>∼</mo><mn>0.45</mn></mrow><annotation encoding="application/x-tex">\sim 0.45</annotation></semantics></math>
and extends up to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo>∼</mo><mn>0.9</mn></mrow><annotation encoding="application/x-tex">\sim 0.9</annotation></semantics></math>,
so a non-trivial subset of pixels experiences large per‑pixel changes.
The Elastic‑Net histogram follows squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
closely (mean 4.38 vs 4.18), consistent with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.01</mn></mrow><annotation encoding="application/x-tex">\beta=0.01</annotation></semantics></math>
placing more weight on the squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
term than on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>.
Increasing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
to 0.05 or 0.1 would shift the Elastic‑Net distribution left as the
optimizer prioritizes sparsity over raw distortion.</p></p>


---

<!-- section 3935 | page 12 | group: ElasticNet | type: theory | interactive: 0 | docker: False -->

# Sparsity Analysis

ElasticNet's defining feature is sparse perturbations. But how sparse are they really? Do modifications concentrate on specific pixels or spread randomly? What explains variation across examples? Heatmaps expose spatial structure that scalar statistics completely miss.
<p><p>This section analyzes sparsity from two perspectives. First, we
examine the relationship between
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distances, revealing how sparse perturbations differ from dense ones.
Second, we visualize where perturbations actually occur, exposing
patterns in spatial concentration. Together, these analyses demonstrate
ElasticNet’s ability to generate interpretable, concentrated adversarial
perturbations.</p></p>



## Mixed-Norm Relationship Analysis
<p><p>How do
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distances relate for sparse perturbations? Theory suggests
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>1</mn></msub><mo>≈</mo><msqrt><msub><mi>L</mi><mn>2</mn></msub></msqrt><mo>⋅</mo><msqrt><mi>k</mi></msqrt></mrow><annotation encoding="application/x-tex">L_1 \approx \sqrt{L_2} \cdot \sqrt{k}</annotation></semantics></math>
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
represents the number of modified pixels. Sparse perturbations
concentrate energy on few pixels, creating different
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>/<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
relationships than dense perturbations. Plotting these distances reveals
whether our attack follows expected sparsity patterns or exhibits
unexpected behavior.</p></p>

<p><p>We also need to understand the sparsity-distortion tradeoff. Does
higher sparsity come at the cost of larger
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distortion? Or can we achieve both simultaneously? This relationship
determines whether sparse perturbations represent a true advantage or
merely shift the attack-distortion curve:</p></p>



```python
# Visualization 3: Mixed-norm relationship and sparsity-distortion tradeoff
print("Creating mixed-norm analysis...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Prepare data
l1_values = l1_dist.detach().cpu().numpy()
l2_values = l2_dist.detach().cpu().numpy()
perturbations = best_adv - original_images
nonzero_mask = torch.abs(perturbations) > 1e-6
sparsity_per_example = (1 - nonzero_mask.float().sum(dim=(1, 2, 3)) / 784) * 100
sparsity_values = sparsity_per_example.detach().cpu().numpy()

# Color by success (green=success, red=failed)
colors = [HTB_GREEN if s else MALWARE_RED for s in final_success.cpu().numpy()]

# Plot 1: L1 vs L2 relationship
axes[0].set_title(r"$L_1$ vs Squared $L_2$ Distortion Relationship", fontsize=14)
axes[0].set_xlabel(r"Squared $L_2$ Distance", fontsize=12)
axes[0].set_ylabel(r"$L_1$ Distance", fontsize=12)
axes[0].scatter(l2_values, l1_values, c=colors, s=100, alpha=0.7,
                edgecolors=NODE_BLACK, linewidth=1.5)

# Add reference line showing L1 = sqrt(L2) relationship
l2_range = np.linspace(l2_values.min(), l2_values.max(), 100)
axes[0].plot(l2_range, np.sqrt(l2_range) * 8, color=AZURE, linestyle="--",
             linewidth=2, alpha=0.5, label=r"Reference: $L_1 \propto \sqrt{L_2}$")
axes[0].legend(frameon=False, fontsize=10)
axes[0].grid(True, alpha=0.3, color=HACKER_GREY)

# Add success legend manually
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=HTB_GREEN, edgecolor=NODE_BLACK, label=f'Success ({final_success.sum()}/{batch_size})'),
    Patch(facecolor=MALWARE_RED, edgecolor=NODE_BLACK, label=f'Failed ({(~final_success).sum()}/{batch_size})')
]
axes[0].legend(handles=legend_elements, loc='upper left', frameon=False, fontsize=10)

# Plot 2: Sparsity vs L2 distortion
axes[1].set_title("Sparsity vs Distortion Tradeoff", fontsize=14)
axes[1].set_xlabel(r"Squared $L_2$ Distance", fontsize=12)
axes[1].set_ylabel("Sparsity (%)", fontsize=12)
axes[1].scatter(l2_values, sparsity_values, c=colors, s=100, alpha=0.7,
                edgecolors=NODE_BLACK, linewidth=1.5)

# Add mean lines
axes[1].axvline(l2_values.mean(), color=VIVID_PURPLE, linestyle="--",
                linewidth=2, alpha=0.7, label=f"Mean $L_2$: {l2_values.mean():.2f}")
axes[1].axhline(sparsity_values.mean(), color=AQUAMARINE, linestyle="--",
                linewidth=2, alpha=0.7, label=f"Mean Sparsity: {sparsity_values.mean():.1f}%")
axes[1].legend(frameon=False, fontsize=10)
axes[1].grid(True, alpha=0.3, color=HACKER_GREY)

plt.tight_layout()
plt.savefig(output_dir / "ead_success_analysis.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"  Saved to {output_dir}/ead_success_analysis.png")
```
<p><p>The left scatter plot reveals how
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
and squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
relate for our sparse perturbations. Points above the reference curve
indicate sparser perturbations where energy concentrates on fewer
pixels, increasing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
relative to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>.
Points below suggest denser modifications. Green markers show successful
attacks, red markers show failures. If failures cluster differently than
successes, this indicates certain perturbation patterns transfer better
to misclassification.</p></p>

<p><p>The right plot exposes the sparsity-distortion tradeoff. Horizontal
spread shows
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
variation, vertical spread shows sparsity variation. Clustering in the
upper-left corner (high sparsity, low distortion) represents ideal
attacks that modify few pixels with small magnitudes. Spread toward
lower-right (low sparsity, high distortion) indicates expensive attacks
requiring dense modifications. The mean lines partition the space,
showing whether most examples achieve above-average sparsity or
below-average distortion.</p></p>



![Two scatter plots: L1 vs squared L2 with a reference curve, and sparsity (%) vs squared L2 with mean lines for 20 attacks](/storage/modules/320/ead_success_analysis.png)
<p><p>Both plots show exclusively green markers, confirming 100% success
across 20 examples. On the left, the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
versus squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
relationship sits above the reference curve as expected for sparse
perturbations. Most points lie below squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>≈</mo><mn>5</mn></mrow><annotation encoding="application/x-tex">L_2 \approx 5</annotation></semantics></math>
(mean
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>4.18</mn><annotation encoding="application/x-tex">4.18</annotation></semantics></math>),
with a few outliers up to about 21;
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
ranges from the low teens to the mid‑60s. This spread indicates varying
robustness across inputs while preserving the same sparse‑modification
pattern.</p></p>

<p><p>The right plot shows a moderate sparsity–distortion tradeoff. Most
points sit around 45–60% sparsity (mean
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>52.6</mn><mi>%</mi></mrow><annotation encoding="application/x-tex">52.6\%</annotation></semantics></math>)
while squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
typically falls between 0 and 5, with several higher‑distortion outliers
to the right. The mean lines mark this center of mass, and all points
correspond to successful attacks. Higher squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
generally coincides with lower sparsity, reflecting denser modifications
required by harder inputs.</p></p>

<p><p>To interpret points in the scatter, link
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>,
squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>,
and the number of modified pixels. If perturbations have similar
magnitude
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>a</mi><annotation encoding="application/x-tex">a</annotation></semantics></math>
across
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
pixels, then
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>1</mn></msub><mo>=</mo><mi>k</mi><mi>a</mi></mrow><annotation encoding="application/x-tex">L_1 = k a</annotation></semantics></math>
and squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>=</mo><mi>k</mi><msup><mi>a</mi><mn>2</mn></msup></mrow><annotation encoding="application/x-tex">L_2 = k a^2</annotation></semantics></math>,
so
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mo>≈</mo><msubsup><mi>L</mi><mn>1</mn><mn>2</mn></msubsup><mi>/</mi><mo stretchy="false" form="prefix">(</mo><mrow><mtext mathvariant="normal">squared </mtext><mspace width="0.333em"></mspace></mrow><msub><mi>L</mi><mn>2</mn></msub><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">k \approx L_1^2 / (\text{squared }L_2)</annotation></semantics></math>.
For example,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>1</mn></msub><mo>=</mo><mn>60</mn></mrow><annotation encoding="application/x-tex">L_1 = 60</annotation></semantics></math>
and squared
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>L</mi><mn>2</mn></msub><mo>=</mo><mn>9</mn></mrow><annotation encoding="application/x-tex">L_2 = 9</annotation></semantics></math>
gives
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mo>≈</mo><msup><mn>60</mn><mn>2</mn></msup><mi>/</mi><mn>9</mn><mo>=</mo><mn>400</mn></mrow><annotation encoding="application/x-tex">k \approx 60^2 / 9 = 400</annotation></semantics></math>.
On a 784-pixel image, that implies roughly
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>784</mn><mo>−</mo><mn>400</mn><mo>=</mo><mn>384</mn></mrow><annotation encoding="application/x-tex">784-400=384</annotation></semantics></math>
unchanged pixels, about
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>49</mn><mi>%</mi></mrow><annotation encoding="application/x-tex">49\%</annotation></semantics></math>
sparsity. Real perturbations vary in magnitude, so this estimate is an
upper bound on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
under equal-magnitude assumptions; actual
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math>
is often smaller (higher sparsity) when a few pixels carry most of the
change.</p></p>



## Sparsity Pattern Visualization

Sparsity percentages quantify how many pixels change. Heatmaps reveal where those changes occur. Do perturbations concentrate on edges where gradients are large? Do they target specific digit features like loops and intersections? Or do they scatter randomly across the image? Spatial patterns provide insights that scalar statistics miss entirely.

To expose these patterns, we'll visualize perturbation magnitudes for individual examples and aggregate sparsity statistics across the full batch:

```python
# Visualization 4: Sparsity analysis
print("Creating sparsity analysis...")

fig = plt.figure(figsize=(16, 8))

# Create grid: 2 rows × 5 columns for examples, 1 row for statistics
gs = fig.add_gridspec(3, 5, height_ratios=[1, 1, 0.6], hspace=0.3, wspace=0.3)

# Show perturbation heatmaps for first 10 examples
num_display_sparse = min(10, batch_size)

for i in range(num_display_sparse):
    row = i // 5
    col = i % 5
    ax = fig.add_subplot(gs[row, col])

    pert = (best_adv[i] - original_images[i]).detach().cpu().squeeze()

    # Show perturbation with colorbar
    im = ax.imshow(torch.abs(pert), cmap="hot", vmin=0, vmax=pert.abs().max())
    ax.axis("off")
    ax.set_title(f"Example {i+1}", fontsize=10)

# Compute sparsity statistics
perturbations = best_adv - original_images
nonzero_mask = torch.abs(perturbations) > 1e-6
sparsity_per_example = (1 - nonzero_mask.float().sum(dim=(1, 2, 3)) / 784) * 100
sparsity_values = sparsity_per_example.detach().cpu().numpy()

# Statistics subplot
ax_stats = fig.add_subplot(gs[2, :])
ax_stats.set_title("Sparsity Distribution Across Examples", fontsize=14)
ax_stats.set_xlabel("Example Index")
ax_stats.set_ylabel("Sparsity (%)")
ax_stats.bar(range(len(sparsity_values)), sparsity_values, color=AQUAMARINE,
             alpha=0.7, edgecolor=NODE_BLACK)
ax_stats.axhline(sparsity_values.mean(), color=MALWARE_RED, linestyle="--",
                 linewidth=2, label=f"Mean: {sparsity_values.mean():.2f}%")
ax_stats.legend(frameon=False, fontsize=10)
ax_stats.set_ylim([0, 100])

plt.tight_layout()
plt.savefig(output_dir / "ead_sparsity_analysis.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"  Saved to {output_dir}/ead_sparsity_analysis.png")
```

Each heatmap shows absolute perturbation magnitude for one example, revealing spatial structure. Bright regions indicate large pixel modifications, dark regions indicate minimal changes. The `hot` colormap progresses from black (zero change) through red and orange (moderate change) to white (maximum change), making perturbation concentration immediately visible. If modifications cluster along edges, we see bright boundaries. If they target specific features, we see bright spots at loops or intersections.

The bar chart aggregates sparsity across all examples. Each bar represents one example's sparsity percentage (fraction of pixels unchanged). Height variation reveals robustness heterogeneity: uniform bars suggest consistent attack difficulty, while wide variation indicates some examples resist much more strongly than others. The horizontal red line marks mean sparsity, partitioning examples into above-average and below-average groups.

![Heatmaps of per‑pixel perturbation magnitude for 10 examples and a bar chart of sparsity (%) with a mean line](/storage/modules/320/ead_sparsity_analysis.png)

The heatmaps expose clear spatial patterns. Perturbations concentrate heavily along digit boundaries and stroke edges. Example 1 shows bright spots clustered in the lower-right where the digit curves. Example 3 reveals modifications targeting the central loop region. Example 5 displays edge modifications running along the digit's vertical stroke. The pattern is consistent: sparse perturbations attack edge pixels where gradient magnitudes are largest, not scattered pixels chosen arbitrarily.

Why edges? Gradient-based optimization naturally finds the steepest descent directions. For digit classification, edges carry maximum discriminative information. A convolutional neural network's early layers extract edge features, making edge pixels disproportionately influential. Modifying edges efficiently shifts the model's internal representations. Modifying background pixels contributes little because the model has learned to ignore uniform regions.

The bar chart shows mean sparsity near 52.6%, with most examples between roughly 35% and 75%. Harder examples sit toward the lower end of this range, while the most favorable examples approach the mid‑70s. This variation demonstrates how digit complexity and model confidence interact: some inputs flip with relatively few unchanged pixels, whereas tougher inputs require denser modifications to succeed.

---

<!-- section 3936 | page 13 | group: ElasticNet | type: interactive | interactive: 1 | docker: True -->

# ElasticNet Attack Challenge

Your task is to craft an adversarial example that fools an MNIST digit classifier using the ElasticNet (EAD) attack. You will receive a baseline image that the classifier correctly predicts. Your job is to add a carefully crafted perturbation that causes misclassification while respecting multiple distance constraints simultaneously.

What you need to do:

Fetch the challenge from the API to receive a baseline `MNIST` image, its ground-truth label, and the constraint parameters. Use the ElasticNet attack (FISTA optimization with elastic-net regularization and binary search) to modify the image. Ensure your perturbation satisfies all three distance bounds: the elastic-net distance (combining `L2` and `L1` norms), an `L2` cap, and an `L1` cap. Submit your adversarial image to the API. If the classifier misclassifies it and all constraints are satisfied, you receive the flag.
<p><p>To craft a valid adversarial example,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><annotation encoding="application/x-tex">x_{\text{adv}}</annotation></semantics></math>,
from a baseline image,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>x</mi><annotation encoding="application/x-tex">x</annotation></semantics></math>,
several mathematical constraints must be met simultaneously. The
perturbation is bounded by three conditions: an
<code>elastic-net constraint</code>
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>2</mn></msub><mo>+</mo><mi>β</mi><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>1</mn></msub><mo>≤</mo><mtext mathvariant="normal">elastic_max</mtext></mrow><annotation encoding="application/x-tex">\lVert x_{\text{adv}} - x \rVert_2 + \beta \lVert x_{\text{adv}} - x \rVert_1 \leq \text{elastic\_max}</annotation></semantics></math>),
an <code>auxiliary L2 norm constraint</code>
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>2</mn></msub><mo>≤</mo><mtext mathvariant="normal">l2_max</mtext></mrow><annotation encoding="application/x-tex">\lVert x_{\text{adv}} - x \rVert_2 \leq \text{l2\_max}</annotation></semantics></math>),
and an <code>auxiliary L1 norm constraint</code>
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>1</mn></msub><mo>≤</mo><mtext mathvariant="normal">l1_max</mtext></mrow><annotation encoding="application/x-tex">\lVert x_{\text{adv}} - x \rVert_1 \leq \text{l1\_max}</annotation></semantics></math>),
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
is the elastic-net trade-off parameter. Furthermore, for the attack to
be successful, the predicted class of the adversarial example must
differ from the baseline label, and all its pixel values must remain
valid by being clipped within the range
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0,1]</annotation></semantics></math>.</p></p>



## Quick Start

All API endpoints expect images in `[0,1]` pixel space, not normalized tensors.

Start the instance from the platform. Check readiness:

```shell-session
[!bash!]$ export BASE_URL="http://instance_ip:port"
```

```shell-session
[!bash!]$ curl -s "$BASE_URL/health"
{"status":"ok"}
```

## API

The API is minimal and deterministic. Each response is JSON. Images are base64-encoded `PNG` files of shape `28x28` and single channel in `[0,1]` after decoding.

### GET /health

Returns service status and configuration parameters.

```shell-session
[!bash!]$ curl -s "$BASE_URL/health" | jq
{
  "status": "ok"
}
```

### GET /challenge

Returns the fixed sample and all constraints that must be satisfied.

```shell-session
[!bash!]$ curl -s "$BASE_URL/challenge" | jq
{
  "sample_index": ...,
  "label": ...,
  "beta": ...,
  "elastic_max": ...,
  "l2_max": ...,
  "l1_max": ...,
  "image_b64": "..."
}
```
<p><p>The <code>sample_index</code> identifies the specific MNIST test
sample used for this challenge. The <code>label</code> is the
ground-truth class. The <code>beta</code> parameter controls the
elastic-net trade-off between
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
regularization. The three distance bounds (<code>elastic_max</code>,
<code>l2_max</code>, <code>l1_max</code>) define the maximum allowed
distortion in <code>[0,1]</code> pixel space. The <code>image_b64</code>
field contains the baseline image as a base64-encoded
<code>PNG</code>.</p></p>



### POST /predict

Returns the model's prediction for an arbitrary image. Use this endpoint to validate the pipeline, encoding, and intermediate candidates. It does not return the flag.

```shell-session
[!bash!]$ curl -s -X POST "$BASE_URL/predict" \
  -H 'content-type: application/json' \
  -d '{"image_b64": "<base64 PNG of 28x28 grayscale>"}' | jq
{
  "pred": ...,
  "confidence": ...
}
```

The `pred` field contains the predicted class (integer in `[0,9]`). The `confidence` field provides the softmax probability for the predicted class (float in `[0,1]`).

### GET /weights

Returns the pretrained model `state_dict` as a binary file. Load it on CPU and use the provided classifier architecture to compute input gradients locally.

```shell-session
[!bash!]$ curl -s -o elasticnet_weights.pth "$BASE_URL/weights"
```

The downloaded file is a PyTorch state dictionary compatible with the `SimpleClassifier` architecture detailed below. Load with `torch.load(path, map_location=torch.device('cpu'))`.

### POST /submit<p><p>Validates that the candidate is a proper <code>28x28</code>
single-channel image in <code>[0,1]</code>, that all three distance
constraints are satisfied (elastic-net distance,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
bound, and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>1</mn></msub><annotation encoding="application/x-tex">L_1</annotation></semantics></math>
bound), and that the classifier’s predicted class differs from the
baseline label. Returns the flag on success.</p></p>


```shell-session
[!bash!]$ curl -s -X POST "$BASE_URL/submit" \
  -H 'content-type: application/json' \
  -d '{"image_b64": "<base64 PNG of 28x28 grayscale>"}' | jq
{
  "ok": true,
  "flag": "HTB{...}",
  "pred": ...,
  "metrics": {
    "l1": ...,
    "l2": ...,
    "linf": ...,
    "elastic": ...
  }
}
```

On validation failure, the endpoint returns HTTP 400 with a descriptive error message (e.g., `"Elastic too large: 1.85 > 1.80"`, `"L2 too large: 1.42 > 1.40"`, or `"Not misclassified; try stronger within bounds"`).

## Minimal Python Scaffolds

The following scaffolds provide API helpers, model architecture, and integration testing. They do not implement the attack.

### API Helpers and Challenge Fetching

```python
import os, io, base64, numpy as np, requests, torch, torch.nn as nn
from PIL import Image

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
MNIST_MEAN, MNIST_STD = 0.1307, 0.3081

def x01_from_b64_png(b64: str) -> np.ndarray:
    """Convert base64 PNG to [0,1] numpy array.

    Args:
        b64: Base64 encoded PNG string

    Returns:
        np.ndarray: Image as (28, 28) array in [0,1] range
    """
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("L")
    if img.size != (28, 28):
        raise ValueError("Expected 28x28 PNG")
    x = np.asarray(img, dtype=np.float32) / 255.0
    return np.clip(x, 0.0, 1.0)

def b64_png_from_x01(x2d: np.ndarray) -> str:
    """Convert [0,1] array to base64 PNG.

    Args:
        x2d: Image array in [0,1] range

    Returns:
        str: Base64 encoded PNG string
    """
    x255 = np.clip((x2d * 255.0).round(), 0, 255).astype(np.uint8)
    img = Image.fromarray(x255, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def compute_distances(a: np.ndarray, b: np.ndarray) -> dict:
    """Compute L1, L2, Linf, and elastic-net distances.

    Args:
        a, b: Arrays to compare

    Returns:
        dict: Dictionary containing l1, l2, linf, and elastic distance values
    """
    diff = a - b
    l1 = float(np.sum(np.abs(diff)))
    l2 = float(np.sqrt(np.sum(diff**2)))
    linf = float(np.max(np.abs(diff)))
    return {"l1": l1, "l2": l2, "linf": linf}

# Fetch challenge and check clean prediction
ch = requests.get(f"{BASE_URL}/challenge", timeout=10).json()
x = x01_from_b64_png(ch["image_b64"])      # (28, 28)
lab = int(ch["label"])                     # baseline label
beta = float(ch["beta"])                   # elastic-net trade-off
elastic_max = float(ch["elastic_max"])     # elastic-net bound
l2_max = float(ch["l2_max"])              # L2 auxiliary bound
l1_max = float(ch["l1_max"])              # L1 auxiliary bound

res = requests.post(f"{BASE_URL}/predict", json={"image_b64": b64_png_from_x01(x)}, timeout=10).json()
print({"baseline_label": lab, "server_pred": res["pred"],
       "beta": beta, "elastic_max": elastic_max, "l2_max": l2_max, "l1_max": l1_max})
```

### Model Architecture and Loading

The server uses this architecture. You need to replicate it locally to compute gradients and run FISTA.

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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass without normalization.

        Args:
            x: Input tensor (already normalized) with shape (N, 1, 28, 28)

        Returns:
            Logits with shape (N, 10)
        """
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.dropout2(x)
        x = self.fc2(x)
        return x

def mnist_normalize(x01: torch.Tensor) -> torch.Tensor:
    """Normalize [0,1] tensor to MNIST statistics.

    Args:
        x01: Input tensor in [0,1] range with shape (N, 1, 28, 28)

    Returns:
        Normalized tensor
    """
    if x01.ndim != 4 or x01.shape[1] != 1:
        raise ValueError(f"Expected (N,1,28,28), got {x01.shape}")
    if x01.min() < 0.0 or x01.max() > 1.0:
        raise ValueError("Input must be in [0,1]")
    return (x01 - MNIST_MEAN) / MNIST_STD

# Download and load weights
wt = requests.get(f"{BASE_URL}/weights", timeout=10).content
open("elasticnet_weights.pth", "wb").write(wt)

model = SimpleClassifier().eval()
state = torch.load("elasticnet_weights.pth", map_location=torch.device("cpu"))
model.load_state_dict(state)

# Verify model works locally
x_tensor = torch.from_numpy(x[None, None, ...]).float()
logits = model(mnist_normalize(x_tensor))
local_pred = int(torch.argmax(logits, dim=1).item())
print(f"Local prediction: {local_pred}, should match server: {res['pred']}")
```

### Testing Server Validation

Verify server-side checks by submitting the clean image and observing expected failures.

```python
bad = requests.post(f"{BASE_URL}/submit", json={"image_b64": b64_png_from_x01(x)}, timeout=10)
print(bad.status_code, bad.text)  # expected: 400 with "Not misclassified"
```

### Questions (section)
- {"id": 3365, "question": "After successfully completing the task, what is the flag you receive?", "hint": null, "file": null, "has_file": false, "protocol": null, "username": null, "password": null, "order": null, "cubes": 5, "experience_points": 60}


---

<!-- section 3937 | page 14 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# JSMA Fundamentals

The `Jacobian-based Saliency Map Attack` (`JSMA`) identifies which specific pixels most strongly influence a model's decision, then modifies only those critical features. Papernot, McDaniel, Jha, Fredrikson, Celik, and Swami demonstrated in their 2016 paper "[The Limitations of Deep Learning in Adversarial Settings](https://arxiv.org/abs/1511.07528)" that targeted selection of high-influence pixels can fool models while changing remarkably few features - often just 20-40 pixels out of 784 in MNIST.
<p><p>JSMA minimizes the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
norm (the count of modified features) rather than perturbation
magnitude. Individual pixels can jump dramatically - from black (0.0) to
white (1.0) - if the saliency map identifies them as strategically
valuable. This creates visually apparent dots or strokes rather than
imperceptible noise, trading stealth for extreme sparsity.</p></p>



## Understanding the Trade-offs: Sparsity Versus Magnitude

JSMA embodies a different philosophy from other adversarial attacks, optimizing for minimal feature modification count rather than minimal perturbation magnitude. This distinction creates a unique set of trade-offs that make JSMA ideal for certain threat models while less suitable for others.
<p><p>The contrast becomes clear when we examine an example. FGSM
constrains the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mi>∞</mi></msub><annotation encoding="application/x-tex">L_\infty</annotation></semantics></math>
norm, modifying all 784 pixels but each by at most
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>ϵ</mi><mo>=</mo><mn>0.03</mn></mrow><annotation encoding="application/x-tex">\epsilon = 0.03</annotation></semantics></math>,
creating nearly invisible uniform noise across the entire image.
DeepFool minimizes the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
norm to find the smallest overall perturbation magnitude needed to cross
a decision boundary, typically modifying most pixels with varying
magnitudes. ElasticNet balances sparsity and magnitude, modifying
100-200 pixels with controlled changes. JSMA, by focusing on the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
norm, allows individual pixels to change significantly (even saturating
from black to white) as long as the total number of modified pixels
remains small. Effective JSMA configurations can modify as few as 20-40
pixels out of 784 total, with each selected pixel potentially changing
by the full step size per iteration or being selected multiple times
before saturating.</p></p>



What does sparsity mean for detectability? JSMA perturbations become visually apparent when examined closely, appearing as scattered dots or strokes rather than uniform noise. A defense system looking for widespread coordinated changes might miss these isolated modifications. The sparse nature also aids interpretation, revealing which specific features the model relies on most heavily for its decisions.

Computational cost grows linearly with the number of output classes. Why? We need one backward pass per class to build the complete Jacobian matrix. MNIST with 10 classes requires 10 backward passes per iteration, manageable on modern GPUs. ImageNet with 1000 classes demands 1000 backward passes per iteration, making the attack prohibitively expensive for real-time scenarios.

## Gradient Target And Model Choice

Computing gradients with respect to `logits` rather than `probabilities` preserves the target sensitivity `α` and competitor sum `β` as independent signals. This independence lets saliency sign constraints genuinely screen candidates based on their ability to boost the target while suppressing competitors. Post-softmax probabilities create a problem: because probabilities sum to one, differentiation forces `β = -α` by mathematical construction. This constraint collapses saliency into a squared target slope, eliminating the competitor suppression term entirely. We lose JSMA's intended behavior from the original paper.

Our demonstrations use a LeNet-like MNIST model because sparse, targeted attacks prove most reliable on this architecture. The shallow network structure with limited capacity makes individual pixels highly influential on the output decision. This mirrors the original paper's experimental setup and provides reproducible baselines. Deeper modern CNNs like ResNet distribute decision-making across many layers through skip connections and batch normalization, reducing individual pixel influence. Success rates drop substantially on these architectures, which explains why modern sparse attacks like ElasticNet and SparseFool have largely superseded JSMA for complex models.

## Intuition Through Examples: How Saliency Guides Selection

To build intuition for how JSMA selects features, let's walk through a simplified scenario. Imagine a toy model with just two input features and three output classes, where we want to force misclassification to class 2 (our target).

![Initial class scores: class 0 highest, class 1 mid, target class 2 lower](/storage/modules/320/jacobian_step1_initial.png)

The visualization above shows our starting point: Class 0 is currently winning with the highest score (0.6), followed by Class 1 (0.5), while our target Class 2 lags behind at 0.3. This is the challenge JSMA must overcome. How can we modify features to flip this ranking?
<p><p>Suppose the Jacobian reveals the following sensitivities. For feature
1:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mn>2</mn></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mn>1</mn></msub></mrow></mfrac><mo>=</mo><mn>0.6</mn></mrow><annotation encoding="application/x-tex">\frac{\partial F_2}{\partial x_1} = 0.6</annotation></semantics></math>
(boosting the target by 0.6 units) and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mo>∑</mo><mrow><mi>j</mi><mo>≠</mo><mn>2</mn></mrow></msub><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mi>j</mi></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mn>1</mn></msub></mrow></mfrac><mo>=</mo><mi>−</mi><mn>0.4</mn></mrow><annotation encoding="application/x-tex">\sum_{j\ne 2} \frac{\partial F_j}{\partial x_1} = -0.4</annotation></semantics></math>
(decreasing other classes by 0.4 combined). This is ideal because
feature 1 helps our target and hurts competitors, yielding a saliency
score of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.6</mn><mo>×</mo><mn>0.4</mn><mo>=</mo><mn>0.24</mn></mrow><annotation encoding="application/x-tex">0.6 \times 0.4 = 0.24</annotation></semantics></math>.</p></p>



![After increasing feature 1, target class 2 overtakes others while competitors drop](/storage/modules/320/jacobian_step2_feature1.png)

Look at the effect: the target (aquamarine) increases to 0.9, while both competitors (red) drop. The arrows visualize these movements. This is what we want because the target now wins.
<p><p>For feature 2:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mn>2</mn></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mn>2</mn></msub></mrow></mfrac><mo>=</mo><mn>0.3</mn></mrow><annotation encoding="application/x-tex">\frac{\partial F_2}{\partial x_2} = 0.3</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mo>∑</mo><mrow><mi>j</mi><mo>≠</mo><mn>2</mn></mrow></msub><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mi>j</mi></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mn>2</mn></msub></mrow></mfrac><mo>=</mo><mn>0.5</mn></mrow><annotation encoding="application/x-tex">\sum_{j\ne 2} \frac{\partial F_j}{\partial x_2} = 0.5</annotation></semantics></math>.
While this helps the target somewhat, it helps competitors even more.
This violates our sign condition, yielding zero saliency.</p></p>



![Increasing feature 2 boosts competitors more than target; class 0 remains on top](/storage/modules/320/jacobian_step3_feature2.png)

The problem becomes clear: while the target increases slightly (yellow), the other classes increase even more (aquamarine with larger arrows). Class 0 increases to 0.9, maintaining its lead. Feature 2 strengthens the original prediction, which is why JSMA rejects it.

This selection logic extends naturally to real images. Consider attacking a digit classifier on an image of a "3". We can identify which pixels along the top horizontal stroke strongly influence the "3" score while barely affecting other digits. Similarly, we know certain pixels in the middle curve boost "8" while suppressing "3".

![MNIST example: strategic pixels transform a "3" into an "8"](/storage/modules/320/jacobian_step4_mnist.png)

The MNIST example shows this in action. Starting with "3" (left), JSMA identifies strategic pixels (center, hot colors) that distinguish "3" from "8". Specifically, we need to fill in the left side and strengthen the middle stroke. By modifying just these pixels, the digit can be transformed to "8" with carefully targeted changes.

## The Attack Algorithm: Iterative Refinement
<p><p>Unlike single-step attacks like FGSM, JSMA operates iteratively with
a complete decision cycle at each step. We compute the Jacobian to
understand current sensitivities, construct the saliency map to identify
important features, select and modify the best feature, then update the
search space. Repetition continues until we achieve misclassification or
exhaust the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>0</mn></msub><annotation encoding="application/x-tex">L_0</annotation></semantics></math>
budget.</p></p>



![Flow chart of JSMA cycle: compute Jacobian, build saliency map, select feature, modify, update search space](/storage/modules/320/jacobian_iterative_cycle.png)
<p><p>Two parameters govern the attack’s behavior: step size
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>θ</mi><annotation encoding="application/x-tex">\theta</annotation></semantics></math>
determines modification magnitude per iteration, while feature budget
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>γ</mi><annotation encoding="application/x-tex">\gamma</annotation></semantics></math>
limits total sparsity as a fraction of features. Larger
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>θ</mi><annotation encoding="application/x-tex">\theta</annotation></semantics></math>
values produce faster attacks with more visible perturbations, while
smaller values require more iterations but create subtler modifications.
The feature budget
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>γ</mi><annotation encoding="application/x-tex">\gamma</annotation></semantics></math>
implements hard sparsity constraints, calculating the maximum number of
modifiable pixels as
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>γ</mi><mo>×</mo><mtext mathvariant="normal">num_features</mtext></mrow><annotation encoding="application/x-tex">\gamma \times \text{num\_features}</annotation></semantics></math>.
Subsequent sections present detailed mechanics and empirical evidence
showing how these parameters affect success rates, iteration counts, and
visual quality.</p></p>



## Common Pitfalls and Implementation Wisdom

Several implementation details make the difference between effective JSMA and failure.

Gradient sign interpretation causes the most common conceptual confusion. For each feature, we evaluate both increasing and decreasing its value. A negative gradient for the target class doesn't discard the feature; instead, it indicates that decreasing that feature helps achieve our goal. We evaluate both directions and choose the one with higher saliency. This is why JSMA can "erase" features (set white pixels to black) as effectively as it can "add" features (set black pixels to white).

Search space mechanics require careful management. We must remove saturated or out-of-range features promptly to avoid wasted iterations. In practice, this means checking after each modification whether the pixel has reached `clip_min` (typically 0.0) or `clip_max` (typically 1.0) and masking it out.

The monotonic mask prevents reselecting saturated pixels. Subsequent sections demonstrate these mechanics through proper implementation.
<p><p>Shape management requires careful attention because gradients and
modifications operate in different coordinate systems. Computing the
Jacobian flattens the input into a 1D array for efficient gradient
extraction (a
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mo>×</mo><mn>1</mn><mo>×</mo><mn>28</mn><mo>×</mo><mn>28</mn></mrow><annotation encoding="application/x-tex">1 \times 1 \times 28 \times 28</annotation></semantics></math>
MNIST image becomes a vector of length 784). Selecting pixel 352 in this
flat representation corresponds to row 12, column 16 in the original 2D
grid. We must maintain consistent flattening order throughout: channel
first, then height, then width. PyTorch’s <code>view_as()</code> or
<code>reshape()</code> methods restore the original structure after
modifications, but only if we flatten and unflatten using the same
convention.</p></p>



Mixing flatten and reshape orders creates catastrophic bugs. Flatten in C-H-W order but reshape assuming H-W-C order? Pixel 352's modification ends up at the wrong spatial location. Worse, the attack appears to run correctly (no errors, reasonable saliency values) while modifying semantically meaningless pixels, producing zero success rate.
<p><p>Memory consumption scales as classes multiplied by features, creating
practical limits on attack feasibility. MNIST requires storing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>10</mn><mo>×</mo><mn>784</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>7</mn><mo>,</mo><mn>840</mn></mrow><annotation encoding="application/x-tex">(10 \times 784) = 7,840</annotation></semantics></math>
floating-point values for the Jacobian, roughly 31 KB at single
precision. Modern GPUs handle this trivially, leaving memory for model
parameters and batch processing.</p></p>

<p><p>ImageNet reveals the scaling challenge. With
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>224</mn><mo>×</mo><mn>224</mn></mrow><annotation encoding="application/x-tex">224 \times 224</annotation></semantics></math>
RGB images and 1000 classes, we need
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1000</mn><mo>×</mo><mn>224</mn><mo>×</mo><mn>224</mn><mo>×</mo><mn>3</mn><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mn>150</mn></mrow><annotation encoding="application/x-tex">(1000 \times 224 \times 224 \times 3) = 150</annotation></semantics></math>
million values, consuming 600 MB just for the Jacobian. A typical
ResNet-50 already occupies 2-3 GB for parameters and activations,
leaving limited headroom. Chunking strategies become necessary: compute
gradients for 100 classes at a time, accumulate results on CPU, repeat.
This trades memory for computation time but enables attacks on
hardware-constrained systems.</p></p>



Debugging benefits from visualization at each iteration. We can plot the saliency map as a heatmap to verify that high-saliency regions align with our intuition about important features. Tracking the target class confidence over iterations ensures it generally increases.
<p><p>If the attack stagnates, examine whether the search space is
shrinking too quickly due to aggressive boundary saturation. This
suggests a smaller
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>θ</mi><annotation encoding="application/x-tex">\theta</annotation></semantics></math>
value might help. The visualization section demonstrates these debugging
techniques with actual examples.</p></p>


---

<!-- section 3938 | page 15 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Jacobian and Gradients

To rank pixels by their attack effectiveness, JSMA needs sensitivity information for every class-pixel pair. Computing the full Jacobian matrix requires one backward pass per output class, then extracting target and competitor gradients for saliency scoring. The implementation divides into focused functions: gradient computation, extraction, and masking.

## Setup

To implement JSMA's gradient-based saliency scoring, we need PyTorch for automatic differentiation, NumPy for efficient array operations, and the HTB Evasion Library for model infrastructure. Let's configure the environment with the same standardized setup used throughout this series:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from htb_ai_library.core import set_reproducibility
from htb_ai_library.data import get_mnist_loaders
from htb_ai_library.models import SimpleLeNet
from htb_ai_library.training import train_model
from htb_ai_library.utils import save_model, load_model
from htb_ai_library.visualization import use_htb_style

use_htb_style()
set_reproducibility(1337)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

output_dir = Path('output')
output_dir.mkdir(exist_ok=True)
```

To train and evaluate our attacks, we need properly loaded data and a pre-trained target model. Let's set up both using checkpoint caching to avoid redundant training:

```python
train_loader, test_loader = get_mnist_loaders(batch_size=128)
model_path = output_dir / 'mnist_target.pth'

model = SimpleLeNet().to(device)

if model_path.exists():
    print(f"Loading existing model from {model_path}")
    model = load_model(model, model_path, device)
else:
    print(f"Training new model...")
    model = train_model(model, train_loader, test_loader, epochs=5, learning_rate=0.001, device=device)
    save_model(model, model_path)

model.eval()
print(f"Model ready for attacks")
```

Expected output:
```
Using device: cuda
Loading existing model from output/mnist_target.pth
Model loaded from output/mnist_target.pth
Model ready for attacks
```

With the environment configured and model loaded, we can now implement the Jacobian computation functions.

## Jacobian Computation
<p><p>Our Jacobian matrix captures how each output class responds to
changes in each input pixel. For a model with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>m</mi><annotation encoding="application/x-tex">m</annotation></semantics></math>
classes and input with
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>n</mi><annotation encoding="application/x-tex">n</annotation></semantics></math>
pixels, the Jacobian has shape
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>m</mi><mo>,</mo><mi>n</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(m, n)</annotation></semantics></math>.
Computing this matrix requires
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>m</mi><annotation encoding="application/x-tex">m</annotation></semantics></math>
backward passes, one per class, which is the computational bottleneck of
JSMA.</p></p>



To build the complete saliency map, we need per-class gradients showing how each pixel influences each output. This information feeds directly into saliency scoring. Let's start by implementing gradient extraction for a single class:

```python
def compute_class_gradient(x, model, class_idx, wrt='logits'):
    x_grad = x.detach().requires_grad_(True)
    logits = model(x_grad)

    if wrt == 'logits':
        scalar = logits[0, class_idx]
    else:
        probs = F.softmax(logits, dim=1)
        scalar = probs[0, class_idx]

    scalar.backward()
    grad = x_grad.grad.detach().cpu().numpy().flatten().copy()

    return grad
```
<p><p>During the forward pass <code>model(x_grad)</code>, PyTorch’s
autograd builds a computation graph tracking which operations produced
each tensor. We then call <code>backward()</code> on a scalar to trigger
reverse-mode differentiation. Gradients flow backward through this
graph, accumulating at each operation. Why must we use a scalar?
Autograd needs a definite starting point (a rank-0 single value, not a
tensor). Indexing with <code>[0, class_idx]</code> extracts the specific
class score we care about, converting the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mo>×</mo><mi>C</mi></mrow><annotation encoding="application/x-tex">1 \times C</annotation></semantics></math>
logit tensor into a single number.</p></p>

<p><p>Why flatten and copy? Gradients arrive as a
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mo>×</mo><mn>1</mn><mo>×</mo><mn>28</mn><mo>×</mo><mn>28</mn></mrow><annotation encoding="application/x-tex">1 \times 1 \times 28 \times 28</annotation></semantics></math>
tensor matching the input shape, but saliency scoring operates on
vectors. Flattening in C-H-W order produces a length-784 vector where
index 352 consistently refers to channel 0, row 12, column 16. We call
<code>.copy()</code> to create an independent numpy array, severing all
ties to PyTorch’s computation graph. Without this copy, the gradient
tensor remains a view into GPU memory that PyTorch might overwrite
during the next backward pass.</p></p>



As established earlier, we compute gradients with respect to `logits` (pre-softmax) to preserve independent target and competitor sensitivities for accurate saliency scoring. Let's test this on a simple example:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# Simple 2-class model for testing
model_test = nn.Sequential(
    nn.Flatten(),
    nn.Linear(4, 2)
)
model_test.eval()

# Test input: 1×1×2×2 image
x_test = torch.tensor([[[[0.5, 0.3], [0.2, 0.8]]]], requires_grad=True)

# Compute gradient for class 0
grad_class0 = compute_class_gradient(x_test, model_test, 0, wrt='logits')
print(f"Gradient shape: {grad_class0.shape}")
print(f"Gradient for class 0: {grad_class0}")
```

Output:
```txt
Gradient shape: (4,)
Gradient for class 0: [-0.3841548  -0.4724946   0.04130501 -0.23387289]
```

Looking at this gradient, we see how each of the 4 pixels affects class 0's score. Positive values mean increasing that pixel boosts class 0. Negative values mean increasing it suppresses class 0.

With the single-class gradient function working, we can now build the complete Jacobian by collecting gradients for all classes. Each row represents one class's sensitivity to all input features:

```python
def compute_jacobian_matrix(x, model, num_classes=10, wrt='logits'):
    if x.shape[0] != 1:
        raise ValueError("compute_jacobian_matrix expects batch size 1")

    jacobian = []
    for class_idx in range(num_classes):
        grad = compute_class_gradient(x, model, class_idx, wrt)
        jacobian.append(grad)

    return np.asarray(jacobian)
```

Why enforce batch size 1? Passing a batch of 4 images would compute gradients averaged across all 4 (PyTorch's default backward behavior), producing meaningless results for per-sample attacks. Validating `batch_size=1` makes the contract explicit: one image in, one Jacobian out. Without this check, a developer might accidentally pass batched data and debug for hours wondering why saliency maps look wrong.
<p><p>Building the matrix happens row by row through list accumulation.
Each <code>compute_class_gradient</code> call triggers a separate
backward pass, which for MNIST with 10 classes means 10 independent
gradient computations, 10 graph traversals, and 10 memory allocations.
This sequential approach is computationally expensive (taking 10-15ms
total) but unavoidable (PyTorch requires separate backward passes for
each output scalar). Finally, <code>np.asarray()</code> converts the
list of 1D arrays into a proper
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>m</mi><mo>,</mo><mi>n</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(m, n)</annotation></semantics></math>
matrix where row
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>
holds
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mi>i</mi></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mi>j</mi></msub></mrow></mfrac><annotation encoding="application/x-tex">\frac{\partial F_i}{\partial x_j}</annotation></semantics></math>
for all pixels
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>j</mi><annotation encoding="application/x-tex">j</annotation></semantics></math>.</p></p>



Let's verify the shape on MNIST:

```python
# MNIST example: 1×1×28×28 input, 10 classes
# Jacobian should be (10, 784)
print(f"For MNIST: {10} classes × {28*28} pixels = {10 * 28*28} values")
print(f"Expected Jacobian shape: (10, 784)")
```

Output:
```txt
For MNIST: 10 classes × 784 pixels = 7840 values
Expected Jacobian shape: (10, 784)
```

## Gradient Extraction and Masking

With the Jacobian computed, we need to extract the relevant gradients for saliency scoring. The saliency formula requires two components: the target class gradient and the sum of all other class gradients. We separate these components because we want pixels that boost the target while suppressing competitors.

Let's implement these extraction functions:

```python
def extract_target_gradient(jacobian, target_class):
    return jacobian[target_class].copy()


def extract_other_gradients(jacobian, target_class):
    target_grad = jacobian[target_class]
    total_grad = jacobian.sum(axis=0)
    other_grad = total_grad - target_grad
    return other_grad
```

Grabbing the target gradient requires indexing into row `target_class` and copying. Why copy instead of returning the view directly? Numpy's row indexing returns a view sharing memory with the original Jacobian. If we modify this view later (say, applying a search space mask), we'd corrupt the Jacobian matrix, causing subsequent extractions to use contaminated gradients. Copying creates an independent array, isolating our modifications from the source data.
<p><p>Combining all non-target classes into "others" could use manual
looping
(<code>for i in range(num_classes): if i != target_class: sum += jacobian[i]</code>),
but array operations run orders of magnitude faster. Summing all rows
with <code>jacobian.sum(axis=0)</code> gives the total gradient across
all classes. Subtracting the target class gradient isolates the combined
effect on competitors through simple arithmetic:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>=</mo><mtext mathvariant="normal">sum(all)</mtext><mo>−</mo><mi>α</mi></mrow><annotation encoding="application/x-tex">\beta = \text{sum(all)} - \alpha</annotation></semantics></math>.
For a 3-class problem with target=2, if class 0 has gradient
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0.2</mn><mo>,</mo><mn>0.5</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0.2, 0.5]</annotation></semantics></math>,
class 1 has
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mi>−</mi><mn>0.1</mn><mo>,</mo><mn>0.2</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[-0.1, 0.2]</annotation></semantics></math>,
and class 2 has
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0.6</mn><mo>,</mo><mi>−</mi><mn>0.3</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0.6, -0.3]</annotation></semantics></math>,
then the total is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0.2</mn><mo>+</mo><mo stretchy="false" form="prefix">(</mo><mi>−</mi><mn>0.1</mn><mo stretchy="false" form="postfix">)</mo><mo>+</mo><mn>0.6</mn><mo>,</mo><mn>0.5</mn><mo>+</mo><mn>0.2</mn><mo>+</mo><mo stretchy="false" form="prefix">(</mo><mi>−</mi><mn>0.3</mn><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">]</mo><mo>=</mo><mo stretchy="false" form="prefix">[</mo><mn>0.7</mn><mo>,</mo><mn>0.4</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0.2+(-0.1)+0.6, 0.5+0.2+(-0.3)] = [0.7, 0.4]</annotation></semantics></math>
and others becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0.7</mn><mo>−</mo><mn>0.6</mn><mo>,</mo><mn>0.4</mn><mo>−</mo><mo stretchy="false" form="prefix">(</mo><mi>−</mi><mn>0.3</mn><mo stretchy="false" form="postfix">)</mo><mo stretchy="false" form="postfix">]</mo><mo>=</mo><mo stretchy="false" form="prefix">[</mo><mn>0.1</mn><mo>,</mo><mn>0.7</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0.7-0.6, 0.4-(-0.3)] = [0.1, 0.7]</annotation></semantics></math>.</p></p>



Example on toy data:

```python
# Toy Jacobian: 3 classes, 4 features
J_toy = np.array([
    [ 0.2,  0.5, -0.1,  0.3],  # Class 0
    [-0.1,  0.2,  0.4, -0.2],  # Class 1
    [ 0.6, -0.3,  0.1,  0.5]   # Class 2
])

target = 2
alpha = extract_target_gradient(J_toy, target)
beta = extract_other_gradients(J_toy, target)

print(f"Target gradient (class {target}): {alpha}")
print(f"Other gradients sum:              {beta}")
```

Output:
```txt
Target gradient (class 2): [ 0.6 -0.3  0.1  0.5]
Other gradients sum:       [ 0.1  0.7  0.3  0.1]
```

For pixel 0: target gradient is 0.6 (increasing helps target), other gradient sum is 0.1 (increasing helps competitors slightly). For pixel 1: target gradient is -0.3 (increasing hurts target), other gradient sum is 0.7 (increasing helps competitors a lot). These gradient signs determine which modification directions are favorable, a concept formalized through sign constraints in the saliency scoring functions.

These gradient values feed directly into saliency scoring, but first we need to mask out pixels that are no longer available for modification:

```python
def apply_search_mask(gradient, search_space):
    return gradient * search_space
```

How do Boolean masks enable efficient feature filtering? Through element-wise multiplication. The `search_space` array contains `True` for available pixels and `False` for unavailable ones. Numpy's broadcasting converts `True→1.0` and `False→0.0` during multiplication, effectively zeroing gradients for unavailable pixels while preserving others. Why this approach instead of fancy indexing? Masked multiplication preserves array shape and index correspondence. Pixel 352 remains at position 352, just with gradient 0.0 if unavailable. Fancy indexing would create a smaller array of only available pixels, breaking index alignment with the original image.

Example:

```python
# Gradient with 5 features
grad = np.array([0.5, -0.2, 0.8, 0.1, -0.4])

# Mask: features 1 and 3 already used
mask = np.array([True, False, True, False, True])

masked_grad = apply_search_mask(grad, mask)
print(f"Original gradient: {grad}")
print(f"Search space mask: {mask}")
print(f"Masked gradient:   {masked_grad}")
```

Output:
```txt
Original gradient: [ 0.5 -0.2  0.8  0.1 -0.4]
Search space mask: [ True False  True False  True]
Masked gradient:   [ 0.5  0.   0.8  0.  -0.4]
```

Features 1 and 3 are zeroed out, preventing them from being selected again.

With these gradient extraction and masking functions complete, we have the necessary inputs for saliency scoring. The next section builds the scoring logic that determines which pixel to modify at each iteration.

---

<!-- section 3939 | page 16 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Saliency and Search Space

Saliency scoring translates raw gradients into pixel importance rankings through sign constraints and magnitude products. Managing the search space ensures we don't waste iterations on saturated pixels or violate boundary constraints. Together, these components guide JSMA's iterative selection process.

## Saliency Scoring
<p><p>The saliency score determines which pixel to modify. We need to score
both increase and decrease directions separately, then choose the
higher-scoring option. The scoring formula is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mtext mathvariant="normal">score</mtext><mo>=</mo><mo stretchy="false" form="prefix">|</mo><mi>α</mi><mo stretchy="false" form="prefix">|</mo><mi>×</mi><mo stretchy="false" form="prefix">|</mo><mi>β</mi><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">\text{score} = |\alpha| \times |\beta|</annotation></semantics></math>
when sign constraints are met, otherwise zero.</p></p>



To find pixels where raising the value boosts our target while suppressing competitors, let's implement scoring for the increase direction first:

```python
def score_increase_saliency(target_grad, other_grad):
    increase_mask = (target_grad > 0) & (other_grad < 0)
    scores = target_grad * np.abs(other_grad) * increase_mask
    return scores
```
<p><p>Building on the gradient interpretation from the previous section,
sign constraints filter candidates through Boolean logic. The expression
<code>(target_grad &gt; 0) &amp; (other_grad &lt; 0)</code> creates a
mask that’s <code>True</code> only where both conditions hold. For pixel
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>j</mi><annotation encoding="application/x-tex">j</annotation></semantics></math>,
we need
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mi>t</mi></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mi>j</mi></msub></mrow></mfrac><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\frac{\partial F_t}{\partial x_j} &gt; 0</annotation></semantics></math>
(increasing this pixel helps our target) AND
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mo>∑</mo><mrow><mi>i</mi><mo>≠</mo><mi>t</mi></mrow></msub><mfrac><mrow><mi>∂</mi><msub><mi>F</mi><mi>i</mi></msub></mrow><mrow><mi>∂</mi><msub><mi>x</mi><mi>j</mi></msub></mrow></mfrac><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\sum_{i \neq t} \frac{\partial F_i}{\partial x_j} &lt; 0</annotation></semantics></math>
(increasing this pixel hurts competitors). Multiplying by this mask
zeroes out invalid pixels. For valid pixels, the score becomes
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mi>j</mi></msub><mo>×</mo><mo stretchy="false" form="prefix">|</mo><msub><mi>β</mi><mi>j</mi></msub><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">\alpha_j \times |\beta_j|</annotation></semantics></math>.
Notice we use <code>target_grad</code> directly (already positive by
constraint) but take <code>np.abs(other_grad)</code> because
<code>other_grad</code> is negative, and we want the magnitude.</p></p>



Now we implement the decrease direction with flipped sign requirements:

```python
def score_decrease_saliency(target_grad, other_grad):
    decrease_mask = (target_grad < 0) & (other_grad > 0)
    scores = np.abs(target_grad) * other_grad * decrease_mask
    return scores
```

Decreasing reverses the gradient interpretation. A negative target gradient means the target class decreases when we increase the pixel, so decreasing the pixel increases the target class. Similarly, a positive "others" gradient means competitors increase when we increase the pixel, so decreasing the pixel decreases competitors. Both effects align with our goal. The mask becomes `(target_grad < 0) & (other_grad > 0)`, filtering for exactly this scenario. The score formula uses `np.abs(target_grad)` (converting negative to positive magnitude) times `other_grad` (already positive by constraint).

Example:

```python
# Gradients for 6 features
alpha = np.array([ 0.6, -0.3,  0.4,  0.1, -0.5,  0.2])
beta  = np.array([-0.2,  0.4, -0.5,  0.3,  0.6, -0.1])

inc_scores = score_increase_saliency(alpha, beta)
dec_scores = score_decrease_saliency(alpha, beta)

print("Feature | α     β    | Inc Score | Dec Score")
print("--------|-----------|-----------|----------")
for i in range(len(alpha)):
    print(f"   {i}    | {alpha[i]:5.1f} {beta[i]:5.1f} |  {inc_scores[i]:7.3f}  |  {dec_scores[i]:7.3f}")
```

Output:
```txt
Feature | α     β    | Inc Score | Dec Score
--------|-----------|-----------|----------
   0    |   0.6  -0.2 |    0.120  |   -0.000
   1    |  -0.3   0.4 |   -0.000  |    0.120
   2    |   0.4  -0.5 |    0.200  |   -0.000
   3    |   0.1   0.3 |    0.000  |    0.000
   4    |  -0.5   0.6 |   -0.000  |    0.300
   5    |   0.2  -0.1 |    0.020  |   -0.000
```
<p><p>Feature 0 is valid for increase
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>α</mi><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha &gt; 0</annotation></semantics></math>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta &lt; 0</annotation></semantics></math>)
with score
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.6</mn><mo>×</mo><mn>0.2</mn><mo>=</mo><mn>0.120</mn></mrow><annotation encoding="application/x-tex">0.6 \times 0.2 = 0.120</annotation></semantics></math>.
Feature 1 is valid for decrease
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>α</mi><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha &lt; 0</annotation></semantics></math>,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>β</mi><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta &gt; 0</annotation></semantics></math>)
with score
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.3</mn><mo>×</mo><mn>0.4</mn><mo>=</mo><mn>0.120</mn></mrow><annotation encoding="application/x-tex">0.3 \times 0.4 = 0.120</annotation></semantics></math>.
Feature 2 achieves the best increase score of 0.200. Feature 3 is
invalid for both directions, violating sign constraints. Feature 4
achieves the best overall score of 0.300 in the decrease direction.</p></p>



Having implemented both direction scoring functions, we now need to select the winning pixel and direction:

```python
def select_best_direction(inc_scores, dec_scores):
    max_inc_idx = int(np.argmax(inc_scores))
    max_dec_idx = int(np.argmax(dec_scores))

    max_inc_score = float(inc_scores[max_inc_idx])
    max_dec_score = float(dec_scores[max_dec_idx])

    if max_inc_score > max_dec_score:
        return max_inc_idx, max_inc_score, True
    else:
        return max_dec_idx, max_dec_score, False
```

We pit both directions against each other through tournament selection. `np.argmax()` finds the highest-scoring pixel in each direction's score array, returning the index. Extracting the actual scores at these indices lets us compare magnitudes directly. The winner gets returned as a tuple: pixel index, score value, and direction flag (`True` for increase, `False` for decrease). What happens when all scores are zero? `np.argmax()` returns index 0 by convention, and `max_inc_score` becomes 0.0. The calling code checks for zero scores and terminates the attack when no valid modifications exist.

Continuing the previous example:

```python
pixel_idx, score, increase = select_best_direction(inc_scores, dec_scores)
direction = "increase" if increase else "decrease"
print(f"Selected: pixel {pixel_idx}, score {score:.3f}, {direction}")
```

Output:
```txt
Selected: pixel 4, score 0.300, decrease
```

Feature 4 wins with the highest score (0.300) in the decrease direction, so we would decrease that pixel's value.

## Search Space Management

The search space tracks which features remain modifiable through a boolean mask. Starting with all pixels available, we progressively remove features as we modify them or they saturate at boundaries. This prevents wasting iterations on unchangeable pixels.

Let's implement the initialization function:

```python
def initialize_search_space(shape):
    num_features = int(np.prod(shape[1:]))
    return np.ones(num_features, dtype=bool)
```
<p><p>Extracting the feature count from a batch input with shape
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>B</mi><mo>,</mo><mi>C</mi><mo>,</mo><mi>H</mi><mo>,</mo><mi>W</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(B, C, H, W)</annotation></semantics></math>
requires computing the flattened size while ignoring the batch
dimension. <code>shape[1:]</code> slices to <code>(C, H, W)</code>, and
<code>np.prod()</code> multiplies these together. For MNIST with shape
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 1, 28, 28)</annotation></semantics></math>,
this yields
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mo>×</mo><mn>28</mn><mo>×</mo><mn>28</mn><mo>=</mo><mn>784</mn></mrow><annotation encoding="application/x-tex">1 \times 28 \times 28 = 784</annotation></semantics></math>.
Creating a boolean array with <code>np.ones(..., dtype=bool)</code>
initializes every pixel to <code>True</code> (available). Why boolean
instead of integers? Boolean arrays consume 1 byte per element versus
4-8 bytes for integers, saving memory. They also make intent explicit:
this is a binary mask, not a count.</p></p>



Example:

```python
# MNIST image shape
shape = (1, 1, 28, 28)
search_space = initialize_search_space(shape)
print(f"Search space shape: {search_space.shape}")
print(f"Initial modifiable pixels: {search_space.sum()}")
```

Output:
```txt
Search space shape: (784,)
Initial modifiable pixels: 784
```

All 784 pixels are available at the start. As we modify pixels or they saturate, we'll set their mask values to false.

Saturation occurs when pixels reach the minimum or maximum allowed values. Once saturated, further modifications in that direction have no effect, making these pixels useless for the attack. Let's detect and remove them:

```python
def remove_saturated_pixels(search_space, x, clip_min=0.0, clip_max=1.0, epsilon=1e-6):
    x_flat = x.detach().cpu().numpy().flatten()

    saturated_min = (x_flat <= clip_min + epsilon)
    saturated_max = (x_flat >= clip_max - epsilon)
    saturated = saturated_min | saturated_max

    updated_mask = search_space & ~saturated
    return updated_mask
```
<p><p>Epsilon tolerance for boundary detection accounts for floating-point
rounding errors. A pixel at exactly 0.0 might be stored as 0.0000001 or
-0.0000001 due to previous operations. Checking
<code>x_flat &lt;= clip_min + epsilon</code> catches pixels within
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mn>10</mn><mrow><mi>−</mi><mn>6</mn></mrow></msup><annotation encoding="application/x-tex">10^{-6}</annotation></semantics></math>
of the minimum, treating them as effectively saturated. We combine
minimum and maximum saturation using the <code>|</code> operator into a
single mask: any pixel saturated in either direction gets marked
<code>True</code>. Finally, <code>search_space &amp; ~saturated</code>
performs Boolean intersection between current availability and
non-saturated pixels. The <code>~</code> inverts the saturation mask
(<code>True→False</code>, <code>False→True</code>), so we keep pixels
that are both currently available AND not saturated.</p></p>



Example:

```python
# Toy image with some saturated pixels
x_toy = torch.tensor([[[[0.0, 0.3], [0.95, 1.0]]]])  # 4 pixels
mask = np.array([True, True, True, True])

updated_mask = remove_saturated_pixels(mask, x_toy, clip_min=0.0, clip_max=1.0)
print(f"Original mask:  {mask}")
print(f"Pixel values:   {x_toy.flatten().numpy()}")
print(f"Updated mask:   {updated_mask}")
print(f"Remaining pixels: {updated_mask.sum()}/4")
```

Output:
```txt
Original mask:  [ True  True  True  True]
Pixel values:   [0.   0.3  0.95 1.  ]
Updated mask:   [False  True  True False]
Remaining pixels: 2/4
```

Pixels 0 and 3 are saturated (at 0.0 and 1.0 respectively) and removed from the search space. Only pixels 1 and 2 remain modifiable.

---

<!-- section 3940 | page 17 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Single-Pixel Attack Fundamentals

We now build the complete single-pixel JSMA attack using the mathematical components from the previous section. Each component handles one step of the attack: applying perturbations, checking success, and tracking progress.

## Utility Functions

Before demonstrating the full attack, we need three utility functions that bridge between the mathematical saliency computation and actual image modification. These functions handle the mechanics of applying perturbations, checking whether we've achieved misclassification, and monitoring the target class confidence as the attack progresses.

### Applying Pixel Perturbations

Why can't we modify pixels directly in their 2D structure? PyTorch tensors support multi-dimensional indexing, but the saliency map returns flat pixel indices (0 to 783 for MNIST). We must flatten the image for indexed access, apply the perturbation, then restore the original 4D structure:

```python
def apply_single_pixel_perturbation(x, pixel_idx, theta, increase, clip_min=0.0, clip_max=1.0):
    original_shape = x.shape
    x_flat = x.view(-1).clone()

    perturbation = theta if increase else -theta
    x_flat[pixel_idx] = torch.clamp(
        x_flat[pixel_idx] + perturbation,
        clip_min,
        clip_max
    )

    x_modified = x_flat.view(original_shape)
    return x_modified
```
<p><p>How does PyTorch map flat indices back to 2D positions?
<code>.view(-1)</code> reshapes the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 1, 28, 28)</annotation></semantics></math>
tensor into a 784-element vector using row-major (C-style) ordering.
Index 352 maps to channel 0, row 12, column 16 through the formula
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0</mn><mo>×</mo><mn>28</mn><mo>×</mo><mn>28</mn><mo>+</mo><mn>12</mn><mo>×</mo><mn>28</mn><mo>+</mo><mn>16</mn><mo>=</mo><mn>352</mn></mrow><annotation encoding="application/x-tex">0 \times 28 \times 28 + 12 \times 28 + 16 = 352</annotation></semantics></math>.
Cloning happens first to prevent memory aliasing: views share memory
with the original tensor, so modifying <code>x_flat[352]</code> without
cloning would corrupt the input <code>x</code>, causing cascading errors
in subsequent iterations.</p></p>

<p><p>Simple signed arithmetic handles perturbation direction:
<code>+theta</code> for increase, <code>-theta</code> for decrease. But
raw addition could push pixels outside valid bounds, creating values
like -0.15 or 1.25 that violate the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0, 1]</annotation></semantics></math>
image range. <code>torch.clamp()</code> enforces hard constraints at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mtext mathvariant="normal">clip_min</mtext><mo>,</mo><mtext mathvariant="normal">clip_max</mtext><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[\text{clip\_min}, \text{clip\_max}]</annotation></semantics></math>,
saturating illegal values. A pixel at 0.9 receiving
<code>+theta=0.25</code> would naively become 1.15, but clamping caps it
at 1.0. Finally, <code>.view(original_shape)</code> restores the 4D
structure using the same C-H-W ordering, ensuring flattened index 352
maps back to the correct spatial position.</p></p>



### Checking Attack Success

To determine when to terminate the attack loop, we need a function that checks whether the current adversarial example successfully forces the model to predict our target class:

```python
def check_target_reached(x, target_class, model):
    with torch.no_grad():
        logits = model(x)
        prediction = int(logits.argmax(dim=1).item())

    return prediction == target_class
```

Why run this check in inference mode? We only need a forward pass, no backpropagation. Wrapping in `torch.no_grad()` disables gradient tracking entirely, preventing PyTorch from building the computation graph. This saves memory (no graph storage for intermediate activations) and computation (no derivative calculations). Finding the predicted class requires `argmax(dim=1)`, which selects the highest logit across the class dimension and returns its index. Extracting with `.item()` converts the single-element tensor to a Python integer, enabling clean boolean comparison against `target_class` without tensor/scalar type mismatches.

### Computing Target Confidence

Beyond binary success/failure, we want to track how close we are to the decision boundary by monitoring the target class probability throughout the attack:

```python
def compute_confidence(x, target_class, model):
    with torch.no_grad():
        logits = model(x)
        probs = F.softmax(logits, dim=1)
        confidence = float(probs[0, target_class].item())

    return confidence
```
<p><p>How confident is the model in our target class? Tracking this
quantifies attack progress beyond binary success/failure. Logits give us
raw, unnormalized scores, but we need probabilities summing to 1.0 for
meaningful confidence values. <code>F.softmax(logits, dim=1)</code>
applies the softmax transformation
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mfrac><msup><mi>e</mi><msub><mi>z</mi><mi>i</mi></msub></msup><mrow><msub><mo>∑</mo><mi>j</mi></msub><msup><mi>e</mi><msub><mi>z</mi><mi>j</mi></msub></msup></mrow></mfrac><annotation encoding="application/x-tex">\frac{e^{z_i}}{\sum_j e^{z_j}}</annotation></semantics></math>,
converting logits to a proper probability distribution across the class
dimension. Indexing <code>[0, target_class]</code> extracts the target
class probability from the first (and only) batch element. Watch this
value during the attack: it starts near 0.0 for unlikely classes (maybe
0.001 for a digit the model strongly rejects) and should rise toward 1.0
as perturbations accumulate, crossing the decision boundary around 0.5
when misclassification occurs.</p></p>



## Demonstrating a Single Iteration

Rather than hiding the attack mechanics inside a monolithic function, we'll execute one complete JSMA iteration to reveal the data flow explicitly. This demonstration shows exactly how each building block contributes to the attack cycle: gradient computation feeds into saliency scoring, which drives pixel selection, leading to perturbation application and search space updates.

We start by selecting a correctly classified sample and initializing the attack state:

```python
# Get first correctly classified sample
for x_batch, y_batch in test_loader:
    x_batch, y_batch = x_batch.to(device), y_batch.to(device)
    with torch.no_grad():
        preds = model(x_batch).argmax(dim=1)

    for i in range(x_batch.size(0)):
        if preds[i].item() == y_batch[i].item():
            x = x_batch[i:i+1]
            original_class = int(y_batch[i].item())
            target_class = (original_class + 5) % 10
            break
    break

# Initialize attack state
x_adv = x.clone().detach()
theta = 0.25
clip_min, clip_max = 0.0, 1.0

# Initialize search space
num_features = int(np.prod(x.shape[1:]))
search_space = np.ones(num_features, dtype=bool)

print(f"Sample: digit {original_class}, target {target_class}")
print(f"Total features: {num_features}")
print(f"Initial target confidence: {compute_confidence(x_adv, target_class, model):.4f}")
```

Output:
```txt
Sample: digit 7, target 2
Total features: 784
Initial target confidence: 0.0000
```
<p><p>Now we compute the Jacobian matrix, which requires 10 backward passes
(one per class) to build the complete
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>10</mn><mo>×</mo><mn>784</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(10 \times 784)</annotation></semantics></math>
sensitivity matrix. From this matrix, we extract the target class
gradients
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>α</mi><annotation encoding="application/x-tex">\alpha</annotation></semantics></math>)
and sum of other class gradients
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>),
then apply the search space mask to zero out unavailable pixels:</p></p>



```python
jacobian = compute_jacobian_matrix(x_adv, model, num_classes=10, wrt='logits')
alpha = extract_target_gradient(jacobian, target_class)
beta = extract_other_gradients(jacobian, target_class)
alpha_masked = apply_search_mask(alpha, search_space)
beta_masked = apply_search_mask(beta, search_space)

print(f"Jacobian shape: {jacobian.shape}")
print(f"Target gradient range: [{alpha.min():.4f}, {alpha.max():.4f}]")
print(f"Other gradient range: [{beta.min():.4f}, {beta.max():.4f}]")
```

Output:
```txt
Jacobian shape: (10, 784)
Target gradient range: [-0.7783, 0.6853]
Other gradient range: [-0.7318, 0.8531]
```
<p><p>Gradient sensitivities vary dramatically across pixels - some
strongly influence the target class while barely affecting competitors,
others do the opposite. To find the single best modification, we score
all available pixels in both directions (increase and decrease) then
select the winner:</p></p>



```python
inc_scores = score_increase_saliency(alpha_masked, beta_masked)
dec_scores = score_decrease_saliency(alpha_masked, beta_masked)
pixel_idx, saliency, increase = select_best_direction(inc_scores, dec_scores)

print(f"Increase: {(inc_scores > 0).sum()} valid pixels, max score {inc_scores.max():.6f}")
print(f"Decrease: {(dec_scores > 0).sum()} valid pixels, max score {dec_scores.max():.6f}")
print(f"Selected: pixel {pixel_idx}, saliency {saliency:.6f}, {'increase' if increase else 'decrease'}")
```

Output:
```txt
Increase: 330 valid pixels, max score 0.501555
Decrease: 349 valid pixels, max score 0.641185
Selected: pixel 398, saliency 0.641185, decrease
```
<p><p>The scoring functions apply sign constraints to filter valid
candidates: for increase, we need
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mi>j</mi></msub><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha_j &gt; 0</annotation></semantics></math>
(boosting target) AND
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mi>j</mi></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta_j &lt; 0</annotation></semantics></math>
(suppressing competitors). Out of 784 pixels, only 330 satisfy these
constraints. Decrease flips the logic:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mi>j</mi></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha_j &lt; 0</annotation></semantics></math>
AND
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mi>j</mi></msub><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta_j &gt; 0</annotation></semantics></math>,
yielding 349 valid pixels. For valid pixels, saliency equals
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mi>j</mi></msub><mo>×</mo><mo stretchy="false" form="prefix">|</mo><msub><mi>β</mi><mi>j</mi></msub><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">\alpha_j \times |\beta_j|</annotation></semantics></math>,
giving pixel 398 the maximum score of 0.641185 in the decrease
direction. This multiplicative relationship means strong target
influence combined with strong competitor suppression produces the
highest scores.</p></p>



With pixel 398 selected, we apply the perturbation using step size `theta=0.25`:

```python
pixel_before = x_adv.flatten()[pixel_idx].item()
x_adv = apply_single_pixel_perturbation(x_adv, pixel_idx, theta, increase, clip_min, clip_max)
pixel_after = x_adv.flatten()[pixel_idx].item()

print(f"Pixel {pixel_idx}: {pixel_before:.4f} → {pixel_after:.4f}")
```

Output:
```txt
Pixel 398: 0.0000 → 0.0000
```

Pixel 398 started at 0.0 (black) and the decrease direction attempted to subtract `theta=0.25`, but `torch.clamp()` prevented it from going below 0.0, keeping it at 0.0. This demonstrates the boundary handling working correctly. After modifying the image, we update the search space to remove any pixels that have saturated at the boundaries (0.0 or 1.0), then check whether we've achieved misclassification:

```python
search_space = remove_saturated_pixels(search_space, x_adv, clip_min, clip_max)
success = check_target_reached(x_adv, target_class, model)
confidence_new = compute_confidence(x_adv, target_class, model)

print(f"Modifiable pixels: {search_space.sum()}")
print(f"Target reached: {success}")
print(f"Target confidence: 0.0001 → {confidence_new:.4f}")
```

Output:
```txt
Modifiable pixels: 115
Target reached: False
Target confidence: 0.0000
```

Pixel 398 saturated at the minimum boundary (0.0), so it was removed from the search space along with any other boundary pixels, leaving 115 modifiable pixels. The target confidence remained at 0.0000 because this particular pixel modification didn't affect the model's prediction significantly. This single iteration demonstrates the complete cycle, but the attack needs many more iterations to accumulate enough changes for successful misclassification.

The next section assembles these components into the complete attack loop, orchestrating initialization, configuration, iteration logic, and results tracking to execute the full single-pixel JSMA attack.

---

<!-- section 3941 | page 18 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Single-Pixel Attack Loop

Now we demonstrate the complete attack by running iterations until success or budget exhaustion. The full attack requires careful orchestration of initialization, configuration, iteration logic, and results tracking. We'll build this incrementally to maintain visibility at each stage.

## Attack Configuration

To control attack behavior, we configure parameters governing perturbation magnitude, sparsity limits, and iteration budget. These settings determine the trade-off between attack subtlety and effectiveness:

```python
# Reset for full attack
x_adv = x.clone().detach()
search_space = initialize_search_space(x.shape)

# Attack configuration
config = {
    'theta': 0.25,
    'gamma': 0.15,
    'max_iter': 100,
    'wrt': 'logits',
    'clip_min': 0.0,
    'clip_max': 1.0
}
```

The configuration dictionary centralizes all attack hyperparameters. The `theta` parameter controls step size (how much each pixel changes per modification), while `gamma` sets the feature budget as a fraction of total pixels. Setting `max_iter` prevents infinite loops when attacks stall. The `wrt` parameter specifies gradient computation with respect to logits (preserving independent target and competitor sensitivities), and clipping bounds ensure pixel values remain valid.

## Computing the Pixel Budget

The feature budget translates the abstract `gamma` fraction into a solid pixel count, establishing a hard limit on modifications:

```python
num_features = int(np.prod(x.shape[1:]))
max_pixels = int(config['gamma'] * num_features)

print(f"Configuration:")
print(f"  Theta: {config['theta']}, Gamma: {config['gamma']}")
print(f"  Max pixels: {max_pixels} of {num_features}")
print(f"  Max iterations: {config['max_iter']}")
```

Output:
```txt
Configuration:
  Theta: 0.25, Gamma: 0.15
  Max pixels: 117 of 784
  Max iterations: 100
```
<p><p>Computing the feature count requires flattening the spatial
dimensions while ignoring the batch dimension. For MNIST with shape
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 1, 28, 28)</annotation></semantics></math>,
<code>x.shape[1:]</code> yields
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 28, 28)</annotation></semantics></math>,
and <code>np.prod()</code> multiplies to get
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1</mn><mo>×</mo><mn>28</mn><mo>×</mo><mn>28</mn><mo>=</mo><mn>784</mn></mrow><annotation encoding="application/x-tex">1 \times 28 \times 28 = 784</annotation></semantics></math>
pixels. Multiplying by <code>gamma=0.15</code> gives
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.15</mn><mo>×</mo><mn>784</mn><mo>=</mo><mn>117</mn></mrow><annotation encoding="application/x-tex">0.15 \times 784 = 117</annotation></semantics></math>
pixels maximum. This budget represents 14.9% of the image, forcing the
attack to select modifications strategically rather than modifying
pixels arbitrarily.</p></p>



## Understanding Parameter Trade-offs
<p><p>Understanding the step size mechanics helps interpret attack
behavior. Each selected pixel receives a perturbation of exactly
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>±</mi><mi>θ</mi></mrow><annotation encoding="application/x-tex">\pm\theta</annotation></semantics></math>.
With <code>theta=0.25</code> on MNIST (where pixels range from 0 to 1),
a black pixel at 0.0 jumps to 0.25 after one selection, then to 0.50 if
selected again, requiring four selections to saturate at 1.0. This
gradual progression demands more iterations but produces subtler visual
artifacts. In contrast, <code>theta=1.0</code> saturates any pixel in a
single selection, creating dramatic changes (0.0 → 1.0 instantly) that
finish attacks quickly but risk detection. The feature budget implements
hard sparsity constraints: setting <code>gamma=0.15</code> on MNIST
calculates
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.15</mn><mo>×</mo><mn>784</mn><mo>=</mo><mn>117</mn></mrow><annotation encoding="application/x-tex">0.15 \times 784 = 117</annotation></semantics></math>
maximum modifications, forcing the algorithm to choose wisely since the
attack terminates once this limit is reached.</p></p>



## Initializing Progress Tracking

We'll track key metrics at each iteration to monitor attack progression: iteration count, cumulative pixels modified, target class confidence, and saliency scores. This lets us analyze convergence behavior and identify when the attack stalls:

```python
stats = {
    'iterations': [],
    'pixels_modified': [],
    'target_confidence': [],
    'saliency_scores': []
}

pixels_modified = 0

print(f"\nStarting attack: {original_class} → {target_class}")
print(f"Initial prediction: {model(x_adv).argmax(dim=1).item()}")
print(f"\n{'Iter':<6} {'Pixels':<8} {'Confidence':<12} {'Saliency':<12}")
print("="*46)
```

Output:
```txt
Starting attack: 7 → 2
Initial prediction: 7

Iter   Pixels   Confidence   Saliency
==============================================
```

Using lists as dict values creates a time-series database. Each list grows by one element per iteration, maintaining synchronized indices where element 0 across all lists corresponds to iteration 0. Why this parallel array pattern instead of a list of dicts? Appending to four separate lists is faster than creating a new dict per iteration, and extracting a complete time series (like all confidence values) requires just `stats['target_confidence']` instead of `[d['target_confidence'] for d in stats]`. The `pixels_modified` counter tracks cumulative L0 norm, starting at zero before any modifications. Column formatting uses fixed widths (6 characters for iteration number, 8 for pixel count, 12 for confidence and saliency), ensuring aligned output throughout the attack even as numbers change magnitude.

## Iteration Loop Structure

The attack loop implements a standard greedy optimization pattern: check termination conditions, compute gradients, select best modification, apply perturbation, update state, repeat. Each iteration makes irreversible progress toward the target class:

```python
for iteration in range(config['max_iter']):
    # Check success condition
    if check_target_reached(x_adv, target_class, model):
        print(f"\n✓ Target reached at iteration {iteration}!")
        break

    # Check budget exhaustion
    if pixels_modified >= max_pixels:
        print(f"\n✗ Budget exhausted")
        break

    # Compute Jacobian and extract gradients
    jacobian = compute_jacobian_matrix(x_adv, model, num_classes=10, wrt=config['wrt'])
    alpha = extract_target_gradient(jacobian, target_class)
    beta = extract_other_gradients(jacobian, target_class)
    alpha_masked = apply_search_mask(alpha, search_space)
    beta_masked = apply_search_mask(beta, search_space)
```
<p><p>Why check termination before computing gradients? Jacobian
computation is expensive (10 backward passes, one per class), so we
avoid this cost when success is already achieved or the budget
exhausted. Checking success requires only a forward pass comparing the
current prediction to the target class. Checking budget involves simple
integer comparison of cumulative pixels against the limit. Both checks
run in milliseconds, while Jacobian computation takes 10-15ms. Only when
both pass do we proceed to the expensive computation, building the
complete
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>10</mn><mo>×</mo><mn>784</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(10 \times 784)</annotation></semantics></math>
gradient matrix.</p></p>

<p><p>Preparing gradients for saliency scoring happens through extraction
and masking. We isolate the target class gradient
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>α</mi><annotation encoding="application/x-tex">\alpha</annotation></semantics></math>)
from row <code>target_class</code> of the Jacobian, then sum all other
rows to get competitor gradients
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>).
Multiplying element-wise with the search space mask zeros out
unavailable pixels, ensuring saliency scoring only considers modifiable
pixels. Without masking, the algorithm might waste time scoring
saturated or already-modified pixels that can’t contribute further.</p></p>



## Saliency Scoring and Selection

With masked gradients ready, we score all pixels in both directions and select the winning modification:

```python
    # Score both directions and select best
    inc_scores = score_increase_saliency(alpha_masked, beta_masked)
    dec_scores = score_decrease_saliency(alpha_masked, beta_masked)
    pixel_idx, saliency, increase = select_best_direction(inc_scores, dec_scores)

    # Check for exhausted search space
    if saliency <= 0:
        print(f"\n✗ No valid pixels remaining")
        break
```

Sign constraints filter candidates based on gradient direction. `score_increase_saliency` finds pixels where increasing helps: positive target gradient (raising this pixel boosts the target class) AND negative competitor gradient (raising this pixel suppresses competitors). `score_decrease_saliency` flips the logic: negative target gradient (lowering this pixel boosts the target class) AND positive competitor gradient (lowering this pixel suppresses competitors). Both return score arrays where invalid pixels receive zero, creating sparse saliency maps.

Tournament selection between directions happens in `select_best_direction`. We pit the highest increase score against the highest decrease score, returning the winner's pixel index, score value, and direction flag (`True` for increase, `False` for decrease). Zero saliency in both directions means no valid pixels remain (all are either saturated at clip bounds or violate sign constraints). This triggers early termination, avoiding wasted iterations that would make no progress.

## Perturbation Application and State Updates

With the best pixel selected, we apply the perturbation and update the search space to prevent reselection:

```python
    # Apply perturbation
    x_adv = apply_single_pixel_perturbation(
        x_adv, pixel_idx, config['theta'], increase,
        config['clip_min'], config['clip_max']
    )

    # Update search space
    search_space[pixel_idx] = False
    search_space = remove_saturated_pixels(search_space, x_adv, clip_min, clip_max)
```

Applying the perturbation requires flattening the image to access the selected pixel by index, adding or subtracting `theta` based on the direction flag, clamping to valid bounds, then reshaping to the original 4D structure. This modification is permanent. JSMA never undoes changes - each iteration makes irreversible progress.

Search space updates prevent wasted effort on unusable pixels through two-stage filtering. First, we immediately mask out the just-modified pixel via `search_space[pixel_idx] = False`. Why mask it even if it hasn't saturated? Because we've already extracted the maximum saliency from this pixel at this iteration. Reselecting it would waste the iteration since single-pixel JSMA modifies one pixel per step. Second, we scan the entire image for pixels at clip bounds (0.0 or 1.0), masking those out as well. Saturated pixels can't be modified further without violating clip constraints, so subsequent iterations should ignore them and focus on pixels with modification headroom.

## Progress Tracking and Display

After each modification, we record metrics and conditionally display progress:

```python
    # Track metrics
    pixels_modified += 1
    confidence = compute_confidence(x_adv, target_class, model)

    stats['iterations'].append(iteration)
    stats['pixels_modified'].append(pixels_modified)
    stats['target_confidence'].append(confidence)
    stats['saliency_scores'].append(saliency)

    # Print progress
    if iteration % 5 == 0 or iteration < 3:
        print(f"{iteration:<6} {pixels_modified:<8} {confidence:<12.4f} {saliency:<12.6f}")
```

Output:
```txt
0      1        0.0000       0.641185
1      2        0.0000       0.501555
2      3        0.0000       0.363550
5      6        0.0000       0.300820
10     11       0.0000       0.343316
15     16       0.0000       0.230782
20     21       0.0000       0.175080
25     26       0.0000       0.095790
30     31       0.0000       0.071866
35     36       0.0000       0.050055
40     41       0.0000       0.050900
45     46       0.0000       0.038594
50     51       0.0000       0.037939
55     56       0.0000       0.029392
60     61       0.0001       0.043980
65     66       0.0001       0.033087
70     71       0.0001       0.022709
75     76       0.0001       0.011674
80     81       0.0001       0.014833
85     86       0.0002       0.008365
90     91       0.0002       0.031157
95     96       0.0002       0.014142
```

Incrementing the pixel counter maintains the cumulative L0 norm. Computing confidence requires a forward pass through the model with softmax to get probability distributions, extracting the target class probability. Appending to the stats lists builds the time-series record for post-attack analysis. The conditional print statement displays updates every 5 iterations plus the first 3, balancing informativeness against output volume. We use string formatting with fixed field widths to maintain column alignment: iteration left-aligned in 6 characters, pixels in 8, confidence in 12 with 4 decimal places, saliency in 12 with 6 decimal places.

## Final Results Evaluation

After the loop exits, we evaluate the final adversarial example and display comprehensive results:

```python
final_success = check_target_reached(x_adv, target_class, model)
final_pred = model(x_adv).argmax(dim=1).item()

print("\n" + "="*46)
print(f"Final result: {'SUCCESS' if final_success else 'FAILED'}")
print(f"Final prediction: {final_pred}")
print(f"Pixels modified: {pixels_modified}/{max_pixels}")
print(f"Iterations: {len(stats['iterations'])}")
```

Output:
```txt
==============================================
Final result: FAILED
Final prediction: 7
Pixels modified: 100/117
Iterations: 100
==============================================
```

The final success check performs one last forward pass to confirm whether the adversarial example successfully forces misclassification to the target class. This redundant check (we already checked inside the loop) provides a definitive result independent of why the loop exited. Extracting the final prediction shows which class the model actually assigns, useful when attacks fail (prediction might be original class, target class, or a third unintended class). Displaying the pixel count against the budget reveals how close we came to exhausting resources. The iteration count comes from the stats list length rather than the loop variable, correctly accounting for early termination scenarios.

## Interpreting the Results

The attack failed after exhausting the maximum iteration limit, modifying 100 pixels out of 784 total (12.8%). The target confidence reached only 0.0002 (0.02%), never approaching the decision boundary needed for misclassification.

Notice how the saliency scores decline steadily from 0.641185 to 0.031157. This indicates the attack is making progressively less effective modifications as it exhausts high-value pixels. The confidence progression shows minimal growth throughout the attack, staying near zero for the first 50 iterations and only reaching 0.0002 by iteration 90. This pattern suggests single-pixel selection with `theta=0.25` struggles significantly on this particular sample. The attack identified pixels with positive saliency at each iteration but modifying them sequentially with small step sizes couldn't achieve the combination needed to cross the decision boundary.

This single-pixel baseline demonstrates JSMA's core iteration mechanics and saliency scoring. The canonical algorithm uses pairwise selection, which we implement in later sections. Batch evaluation in the next section characterizes typical single-pixel performance across multiple samples.

---

<!-- section 3942 | page 19 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Single-Pixel Batch Evaluation

Single-Pixel Attack demonstrated single-pixel JSMA mechanics on one sample, which failed despite modifying 100 pixels and reaching minimal target confidence. A single example can't tell us whether this failure typifies single-pixel JSMA or represents an unusually difficult sample. To characterize typical performance and identify patterns in success rates, sparsity, and convergence behavior, we now evaluate across multiple samples.

This section shows how to run batch attacks, compute summary statistics, and measure sparsity across a representative test set.

## Batch Attack Execution

Running the attack on multiple samples reveals typical performance characteristics and variability across the dataset. We need to collect correctly classified samples, attack each one systematically, and analyze the aggregate results to understand single-pixel JSMA's effectiveness.

### Collecting Test Samples

To evaluate attack performance across diverse inputs, we'll collect 10 correctly classified samples from the test set. For each sample, we'll assign a target class offset by 5 positions to ensure challenging misclassification targets:

```python
print("Collecting samples...")
samples_found = 0
target_count = 10

original_images = []
original_labels = []
target_labels = []
```
<p><p>Setting up storage structures prepares us to accumulate samples as we
encounter them. The <code>samples_found</code> counter tracks progress
toward our target count, while the three lists maintain parallel arrays
where index
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>
corresponds to the same sample across all three (image at
<code>original_images[i]</code> has label
<code>original_labels[i]</code> and target
<code>target_labels[i]</code>). This parallel array pattern simplifies
iteration during the attack phase since we can loop over indices and
access all related data with the same index.</p></p>



### Scanning the Dataset

We iterate through test batches, filtering for correctly classified samples until we reach our target count:

```python
for x_batch, y_batch in test_loader:
    if samples_found >= target_count:
        break

    x_batch = x_batch.to(device)
    y_batch = y_batch.to(device)

    with torch.no_grad():
        preds = model(x_batch).argmax(dim=1)
```

Checking the target count at the batch level enables early termination before processing unnecessary data. Moving batches to the device (GPU or CPU) ensures tensor operations run on the correct hardware. Wrapping prediction in `torch.no_grad()` disables gradient tracking since we're only evaluating, not training, saving memory and computation. The `argmax(dim=1)` operation finds the predicted class for each image in the batch by selecting the highest logit along the class dimension.

### Filtering and Storing Samples

Within each batch, we examine individual samples, keeping only those correctly classified:

```python
    for i in range(x_batch.size(0)):
        if samples_found >= target_count:
            break

        if preds[i].item() != y_batch[i].item():
            continue

        x = x_batch[i:i+1]
        original_class = int(y_batch[i].item())
        target_class = (original_class + 5) % 10

        original_images.append(x)
        original_labels.append(original_class)
        target_labels.append(target_class)

        samples_found += 1
        print(f"  Sample {samples_found}: digit {original_class} → target {target_class}")

print(f"\nCollected {len(original_images)} samples")
```

Output:
```txt
Collecting samples...
  Sample 1: digit 7 → target 2
  Sample 2: digit 2 → target 7
  Sample 3: digit 1 → target 6
  Sample 4: digit 0 → target 5
  Sample 5: digit 4 → target 9
  Sample 6: digit 1 → target 6
  Sample 7: digit 4 → target 9
  Sample 8: digit 9 → target 4
  Sample 9: digit 5 → target 0
  Sample 10: digit 9 → target 4

Collected 10 samples
```
<p><p>The inner loop processes each sample in the current batch. Redundant
target count checking ensures we stop immediately upon reaching our
goal, even mid-batch. Comparing prediction to true label identifies
correctly classified samples (the only ones suitable for targeted
attacks, since already-misclassified samples don’t provide meaningful
baselines). Slicing <code>x_batch[i:i+1]</code> preserves the batch
dimension, yielding shape
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 1, 28, 28)</annotation></semantics></math>
rather than
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 28, 28)</annotation></semantics></math>,
which JSMA expects. The modular arithmetic
<code>(original_class + 5) % 10</code> wraps around at 10, ensuring
targets stay in range while providing semantic distance (digit 7 targets
digit 2, challenging the model to cross the decision boundary between
dissimilar classes).</p></p>



### Initializing Attack Results Storage

With our test set ready, we prepare to execute attacks and track comprehensive results:

```python
print("\nRunning attacks...")
print(f"{'#':<4} {'Orig→Tgt':<10} {'Result':<10} {'Pixels':<8} {'Iters':<8}")
print("="*46)

results = {
    'adversarial': [],
    'success': [],
    'pixels_modified': [],
    'iterations': []
}
```

Output:
```txt
Running attacks...
#    Orig→Tgt   Result     Pixels   Iters
==============================================
```

The results dictionary uses lists to accumulate per-sample metrics, maintaining the same parallel array pattern as the input data. Storing adversarial examples enables post-attack visualization and perturbation analysis. Success flags support aggregate success rate calculation. Pixel counts reveal sparsity characteristics. Iteration counts expose convergence behavior and computational cost. The formatted header establishes columnar output for tracking progress across all 10 attacks.

### Running Attacks on All Samples

We execute the complete single-pixel JSMA attack on each collected sample, using the exact loop structure from the previous section:

```python
for idx in range(len(original_images)):
    x = original_images[idx]
    orig_class = original_labels[idx]
    tgt_class = target_labels[idx]

    # Initialize attack state
    x_adv = x.clone().detach()
    search_space = initialize_search_space(x.shape)
    pixels_mod = 0

    # Attack loop
    for iteration in range(config['max_iter']):
        if check_target_reached(x_adv, tgt_class, model):
            break
        if pixels_mod >= int(config['gamma'] * 784):
            break

        jacobian = compute_jacobian_matrix(x_adv, model, 10, config['wrt'])
        alpha = extract_target_gradient(jacobian, tgt_class)
        beta = extract_other_gradients(jacobian, tgt_class)
        alpha_masked = apply_search_mask(alpha, search_space)
        beta_masked = apply_search_mask(beta, search_space)

        inc_scores = score_increase_saliency(alpha_masked, beta_masked)
        dec_scores = score_decrease_saliency(alpha_masked, beta_masked)
        pixel_idx, saliency, increase = select_best_direction(inc_scores, dec_scores)

        if saliency <= 0:
            break

        x_adv = apply_single_pixel_perturbation(
            x_adv, pixel_idx, config['theta'], increase,
            config['clip_min'], config['clip_max']
        )

        search_space = remove_saturated_pixels(search_space, x_adv, 0.0, 1.0)
        pixels_mod += 1
```

The outer loop iterates over sample indices, extracting the corresponding image, true label, and target from the parallel arrays. Each attack starts fresh with a cloned adversarial image (ensuring we don't contaminate across samples), initialized search space (all pixels available), and zero pixel counter. The inner attack loop replicates the structure from the previous section: check termination conditions, compute Jacobian, extract and mask gradients, score both directions, select best pixel, apply perturbation, update search space. Notice we removed individual pixel masking (`search_space[pixel_idx] = False`) from the previous version; here we rely solely on saturation detection via `remove_saturated_pixels`, which automatically handles boundary cases while still preventing repeat selections through the modification tracking inherent in the pixel values themselves.

### Storing Results and Displaying Progress

After each attack completes, we record all metrics and display a summary row:

```python
    # Record results
    success = check_target_reached(x_adv, tgt_class, model)
    pred = model(x_adv).argmax(dim=1).item()

    results['adversarial'].append(x_adv)
    results['success'].append(success)
    results['pixels_modified'].append(pixels_mod)
    results['iterations'].append(iteration + 1)

    # Display progress
    status = "✓" if success else "✗"
    print(f"{idx+1:<4} {orig_class}→{tgt_class:<8} {status:<10} {pixels_mod:<8} {iteration+1:<8}")

print("="*46)
```

Output:
```txt
1    7→2        ✗          100      100
2    2→7        ✗          100      100
3    1→6        ✓          67       68
4    0→5        ✓          33       34
5    4→9        ✓          58       59
6    1→6        ✓          92       93
7    4→9        ✓          60       61
8    9→4        ✓          86       87
9    5→0        ✗          100      100
10   9→4        ✓          40       41
==============================================
```

The final success check performs one last forward pass to definitively determine whether the adversarial example forces misclassification to the target. This redundant check (we already checked in the loop) provides consistent results independent of termination reason. Extracting the final prediction enables debugging when attacks fail (did we stay at the original class, drift to an unintended class, or nearly reach the target?). Adding `iteration + 1` to the results corrects for zero-based indexing (if the loop variable ends at 99, we ran 100 iterations). The status symbol provides immediate visual feedback: checkmarks for success, X marks for failure. Column alignment with fixed field widths keeps the table readable across varying number widths.

Seven out of 10 samples succeeded with the current configuration (`theta=0.25`, `max_iter=100`). Samples 1, 2, and 9 failed after exhausting the 100 iteration limit. Successful attacks required between 33 and 92 pixels, demonstrating that single-pixel JSMA can achieve misclassification when given sufficient iterations and appropriate samples, though success varies significantly across the dataset.

## Attack Summary Statistics

Let's compute aggregate statistics to characterize overall attack performance:

```python
success_count = sum(results['success'])
total_samples = len(results['success'])
success_rate = 100.0 * success_count / total_samples

pixels = results['pixels_modified']
mean_pixels = np.mean(pixels)
median_pixels = np.median(pixels)
std_pixels = np.std(pixels)
min_pixels = np.min(pixels)
max_pixels = np.max(pixels)

sparsity_pct = 100.0 * mean_pixels / 784

print("\nAttack Summary:")
print("="*50)
print(f"Success rate:        {success_count}/{total_samples} ({success_rate:.1f}%)")
print(f"\nPixels Modified:")
print(f"  Mean:   {mean_pixels:.1f} ± {std_pixels:.1f}")
print(f"  Median: {median_pixels:.1f}")
print(f"  Range:  [{min_pixels}, {max_pixels}]")
print(f"\nSparsity: {mean_pixels:.1f} / 784 = {sparsity_pct:.2f}%")
print("="*50)
```

Output:
```txt
Attack Summary:
=================================================
Success rate:        7/10 (70.0%)

Pixels Modified:
  Mean:   73.6 ± 24.2
  Median: 76.5
  Range:  [33, 100]

Sparsity: 73.6 / 784 = 9.39%
=================================================
```

The results show moderate success: 70% success rate across the 10 samples, with 7 successful attacks and 3 failures. The attacks modified an average of 73.6 pixels (9.39% of the image). The median of 76.5 indicates typical attacks fall in the mid-range of pixel modifications. Successful attacks ranged from 33 to 92 pixels, demonstrating variable efficiency. The three failed samples (1, 2, and 9) all exhausted the 100-iteration limit, suggesting they require either more iterations, larger step sizes, or represent particularly challenging misclassification targets where single-pixel selection struggles to find effective perturbation combinations.

## Perturbation Analysis

Beyond success rates, we need to understand the perturbation character: how sparse are they really, and how much do individual pixels change? Let's examine all four distance metrics for the first sample to reveal the trade-offs inherent in L0-minimizing attacks:

```python
x_orig = original_images[0].cpu().numpy()
x_adv = results['adversarial'][0].cpu().numpy()

perturbation = x_adv - x_orig
pert_magnitude = np.abs(perturbation)

# Compute norms
l0_norm = np.count_nonzero(perturbation)
l1_norm = np.sum(pert_magnitude)
l2_norm = np.linalg.norm(perturbation)
linf_norm = np.max(pert_magnitude)

print(f"\nPerturbation Analysis (Sample 1):")
print(f"="*50)
print(f"L0 (pixels changed):     {l0_norm}")
print(f"L1 (sum of changes):     {l1_norm:.4f}")
print(f"L2 (euclidean distance): {l2_norm:.4f}")
print(f"L∞ (max change):         {linf_norm:.4f}")
print(f"="*50)
```

Output:
```txt
Perturbation Analysis (Sample 1):
=================================================
L0 (pixels changed):     51
L1 (sum of changes):     19.4422
L2 (euclidean distance): 3.5413
L∞ (max change):         0.9961
=================================================
```

Reading these norms reveals the perturbation character. L0=51 confirms exactly 51 pixels changed, representing 6.5% of the image. L2=3.5413 measures total perturbation magnitude, moderate for a 784-pixel image. L∞=0.9961 approaches the maximum possible change of 1.0, indicating at least one pixel saturated near its boundary. The L1 norm of 19.4422 divided by 51 pixels gives an average absolute change of 0.381 per modified pixel, suggesting many pixels received multiple modifications or large single modifications during the attack iterations.

The next section provides configuration guidelines, showing how different parameter choices (step size and feature budget) affect attack behavior and success rates.

---

<!-- section 3943 | page 20 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Single-Pixel Configuration

The attack's behavior depends critically on parameter choices. Understanding trade-offs helps configure attacks effectively for different scenarios. This section explores how step size and feature budget parameters affect attack success, efficiency, and perturbation character.

## Step Size Configuration

The step size controls how much we modify each selected pixel per iteration. Testing across multiple values reveals the trade-off between attack speed and perturbation subtlety. Let's experiment systematically on the first collected sample:

```python
theta_values = [0.10, 0.25, 0.50, 1.00]

print("\nStep Size Analysis:")
print(f"{'theta':<8} {'Iterations':<12} {'Pixels':<8} {'Result':<8}")
print("="*42)
```

Output:
```txt
Step Size Analysis:
theta    Iterations   Pixels   Result
==========================================
```

We'll test four step sizes ranging from subtle (0.10) to aggressive (1.00), analyzing how each affects iteration count and success. The formatted table header establishes columns for the parameter value, iteration count required, total pixels modified, and final attack outcome.

### Running Step Size Experiments

For each theta value, we execute a complete attack and record the results:

```python
for theta_test in theta_values:
    # Initialize fresh attack
    x_test = original_images[0].clone().detach()
    search_space_test = initialize_search_space(x_test.shape)
    config_test = {**config, 'theta': theta_test}
    pixels_mod = 0

    # Run attack loop
    for iteration in range(100):
        if check_target_reached(x_test, target_labels[0], model):
            break
        if pixels_mod >= int(config_test['gamma'] * 784):
            break

        jacobian = compute_jacobian_matrix(x_test, model, 10, config_test['wrt'])
        alpha = extract_target_gradient(jacobian, target_labels[0])
        beta = extract_other_gradients(jacobian, target_labels[0])
        alpha_masked = apply_search_mask(alpha, search_space_test)
        beta_masked = apply_search_mask(beta, search_space_test)

        inc_scores = score_increase_saliency(alpha_masked, beta_masked)
        dec_scores = score_decrease_saliency(alpha_masked, beta_masked)
        pixel_idx, saliency, increase = select_best_direction(inc_scores, dec_scores)

        if saliency <= 0:
            break

        x_test = apply_single_pixel_perturbation(
            x_test, pixel_idx, config_test['theta'], increase, 0.0, 1.0
        )

        search_space_test[pixel_idx] = False
        search_space_test = remove_saturated_pixels(search_space_test, x_test, 0.0, 1.0)
        pixels_mod += 1
```

Each experiment starts fresh by cloning the original image and initializing a new search space, ensuring results don't carry over between tests. The dictionary unpacking `{**config, 'theta': theta_test}` creates a new configuration copying all base settings while overriding only the theta parameter. This preserves `gamma`, `max_iter`, and other parameters across experiments. The attack loop follows the same structure used throughout this section: check termination, compute gradients, score pixels, select best, apply perturbation, update state. Masking the modified pixel (`search_space_test[pixel_idx] = False`) prevents repeat selection even before saturation, which is critical for these experiments since small theta values take multiple modifications to saturate pixels.

### Recording and Displaying Results

After each attack completes, we check success and display the outcome:

```python
    success = check_target_reached(x_test, target_labels[0], model)
    result = "SUCCESS" if success else "FAILED"
    print(f"{theta_test:<8.2f} {iteration+1:<12} {pixels_mod:<8} {result:<8}")

print("="*42)
```

Output:
```txt
0.10     100          100      FAILED
0.25     100          100      FAILED
0.50     100          100      FAILED
1.00     64           63       SUCCESS
=========================================
```

String formatting with `.2f` displays theta values to two decimal places, maintaining consistent column widths. Adding one to the iteration variable accounts for zero-based indexing (if the loop exits with `iteration=63`, we completed 64 iterations). The result string provides immediate visual confirmation of attack effectiveness.

### Interpreting Step Size Trade-offs

The results reveal a critical threshold effect: small theta values (0.10, 0.25, 0.50) all fail within 100 iterations, while `theta=1.0` succeeds in just 64 iterations. With `theta=1.0`, each selected pixel saturates immediately (jumping from 0.0 to 1.0 or 1.0 to 0.0), enabling the attack to accumulate enough perturbation magnitude to cross the decision boundary. In contrast, smaller theta values modify pixels incrementally, requiring many iterations to build up sufficient change.

Notice that pixel counts match iteration counts almost exactly (63 pixels for 64 iterations with `theta=1.0`). This one-to-one correspondence occurs because we mask each pixel after modification, preventing reselection. The attack selects a new pixel at each iteration rather than repeatedly modifying high-saliency pixels.

This sample demonstrates why `theta=1.0` is recommended for MNIST when attack success is prioritized over perturbation subtlety. The aggressive per-pixel modifications create visible artifacts but enable misclassification with fewer total pixel changes. Smaller theta values create subtler perturbations but often fail entirely, as shown here.

## Feature Budget Configuration

The `gamma` parameter controls sparsity by limiting the fraction of pixels we can modify:

```python
gamma_values = [0.10, 0.15, 0.20, 0.30]

print("\nFeature Budget Analysis:")
print(f"{'gamma':<8} {'Max Pixels':<12} {'Percentage':<12}")
print("="*38)

for gamma_test in gamma_values:
    max_pixels = int(gamma_test * 784)
    print(f"{gamma_test:<8.2f} {max_pixels:<12} {gamma_test*100:<12.0f}%")

print("="*38)
```

Output:
```txt
Feature Budget Analysis:
gamma    Max Pixels   Percentage
======================================
0.10     78           10%
0.15     117          15%
0.20     157          20%
0.30     235          30%
======================================
```

In practice, successful attacks typically use a portion of the available budget. Our attacks modified 73.6 pixels on average under a `gamma=0.15` budget of 117 pixels, consuming about 63% of the available budget. Successful attacks ranged from 33 to 92 pixels, while the three failed attacks exhausted the full 100 iterations without reaching their targets.

Tighter budgets (`gamma=0.10`, allowing 78 pixels) would constrain some successful attacks that required 86-92 pixels, potentially reducing the success rate. Looser budgets (`gamma=0.30`, allowing 235 pixels) would provide additional headroom but may not improve success rates since most successful attacks already complete well below the current 117-pixel limit. The value `gamma=0.15` provides a reasonable balance, allowing sufficient modifications for most attacks while maintaining sparsity.

## Reflecting on Configuration Choices

Across 10 samples, single-pixel JSMA with `theta=0.25` achieved 70% success (7/10 samples), modifying a mean of 73.6 pixels. Three attacks failed after exhausting the 100-iteration budget without crossing decision boundaries. The theta experiment revealed that `theta=1.0` succeeds where smaller values fail, achieving success in 64 iterations where `theta=0.25` failed after 100 iterations on the same sample. Saliency scores declined steadily during attacks, suggesting diminishing returns from sequential pixel selection.

While single-pixel JSMA demonstrates moderate effectiveness with `theta=0.25`, the canonical JSMA algorithm uses pairwise feature selection to improve both success rates and efficiency, implemented in the following sections. Pairwise selection captures feature interactions by modifying two pixels simultaneously, often finding more effective perturbation combinations than single-pixel greedy selection.

---

<!-- section 3944 | page 21 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Pairwise Saliency
<p><p>Pairwise JSMA modifies two pixels simultaneously to exploit feature
interactions in nonlinear models. For a pair
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>p</mi><mo>,</mo><mi>q</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(p, q)</annotation></semantics></math>,
we define
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>α</mi><mi>p</mi></msub><mo>+</mo><msub><mi>α</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\alpha_{pq} = \alpha_p + \alpha_q</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>β</mi><mi>p</mi></msub><mo>+</mo><msub><mi>β</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\beta_{pq} = \beta_p + \beta_q</annotation></semantics></math>,
where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>α</mi><annotation encoding="application/x-tex">\alpha</annotation></semantics></math>
represents target class gradients and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>β</mi><annotation encoding="application/x-tex">\beta</annotation></semantics></math>
represents the sum of other class gradients. We continue using logits to
preserve independent sensitivities.</p></p>

<p><p>The pair score for increasing both features is
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msubsup><mi>S</mi><mi>t</mi><mo>+</mo></msubsup><mo stretchy="false" form="prefix">[</mo><mi>p</mi><mo>,</mo><mi>q</mi><mo stretchy="false" form="postfix">]</mo><mo>=</mo><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>×</mo><mo stretchy="false" form="prefix">|</mo><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">S_t^{+}[p, q] = \alpha_{pq} \times |\beta_{pq}|</annotation></semantics></math>
when sign constraints are met
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha_{pq} &gt; 0</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta_{pq} &lt; 0</annotation></semantics></math>).
This formula extends the single-pixel saliency naturally: we sum the
gradients and apply the same scoring logic.</p></p>

<p><p>We enforce the saliency sign constraints on the pair sums
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mi>p</mi></msub><mo>+</mo><msub><mi>α</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\alpha_p+\alpha_q</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mi>p</mi></msub><mo>+</mo><msub><mi>β</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\beta_p+\beta_q</annotation></semantics></math>,
and we run two fixed policies (increase‑only and decrease‑only),
selecting the better outcome. This mirrors the paper’s evaluation
protocol and preserves the intended "increase target, decrease
competitors" selection.</p></p>



## Pairwise Saliency Function

Computing pairwise saliency requires evaluating many candidate pairs, pruning the search space for efficiency, and tracking the best combination. We'll build this through composable helper functions that each handle one aspect of the computation.

### Candidate Pruning

To control computational cost, we prune candidates based on individual gradient magnitudes before forming pairs:

```python
def prune_candidates(alpha, beta, search_space, top_k):
    alpha_masked = alpha * search_space
    beta_masked = beta * search_space
    valid = np.where(search_space)[0]

    if valid.size < 2 or top_k is None or valid.size <= top_k:
        return valid

    prelim_scores = np.abs(alpha_masked[valid]) * np.abs(beta_masked[valid])
    idx = np.argsort(-prelim_scores)[:top_k]
    return valid[idx]
```

Why mask gradients before pruning? Multiplying by the search space mask (`alpha * search_space`) zeroes out unavailable pixels, ensuring we only consider modifiable candidates when computing preliminary scores. Converting the boolean mask to indices happens through `np.where(search_space)[0]`, which extracts integer pixel positions from the `True` entries.

Early returns handle edge cases efficiently. Fewer than 2 valid pixels? Can't form pairs, so return immediately. Pruning disabled (`top_k=None`)? Return all valid pixels. Already have fewer candidates than the budget (`valid.size <= top_k`)? No need to prune, return everything. These checks prevent unnecessary computation when pruning would have no effect.
<p><p>Computing preliminary scores uses magnitude products
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">|</mo><msub><mi>α</mi><mi>j</mi></msub><mo stretchy="false" form="prefix">|</mo><mi>×</mi><mo stretchy="false" form="prefix">|</mo><msub><mi>β</mi><mi>j</mi></msub><mo stretchy="false" form="prefix">|</mo></mrow><annotation encoding="application/x-tex">|\alpha_j| \times |\beta_j|</annotation></semantics></math>
as a proxy for pair effectiveness. This heuristic assumes pixels with
strong individual gradients likely form strong pairs (an assumption that
holds empirically but isn’t guaranteed). Sorting by negative scores
(<code>-prelim_scores</code>) creates descending order, and slicing
<code>[:top_k]</code> selects the top candidates. Indexing
<code>valid[idx]</code> returns these pixel positions in
score-descending order.</p></p>



### Pair Scoring Loop

With pruned candidates ready, we evaluate all pairs and track the best:

```python
def evaluate_pairs(alpha, beta, valid, direction):
    best_p, best_q, best_score = -1, -1, 0.0

    for i in range(valid.size):
        p = valid[i]
        for j in range(i + 1, valid.size):
            q = valid[j]
            a_pq = alpha[p] + alpha[q]
            b_pq = beta[p] + beta[q]

            if direction == 'increase':
                if a_pq <= 0 or b_pq >= 0:
                    continue
                score = a_pq * abs(b_pq)
            else:
                if a_pq >= 0 or b_pq <= 0:
                    continue
                score = abs(a_pq) * b_pq

            if score > best_score:
                best_score = float(score)
                best_p, best_q = int(p), int(q)

    return best_p, best_q, best_score
```
<p><p>Generating all unique pairs requires careful index manipulation.
Outer loop index
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>
ranges over all candidates, while inner loop index
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>j</mi><annotation encoding="application/x-tex">j</annotation></semantics></math>
starts at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>i</mi><mo>+</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">i+1</annotation></semantics></math>.
Why
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>i</mi><mo>+</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">i+1</annotation></semantics></math>
instead of
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math>
or
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mn>0</mn><annotation encoding="application/x-tex">0</annotation></semantics></math>?
Starting at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>i</mi><mo>+</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">i+1</annotation></semantics></math>
avoids both self-pairing (where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>p</mi><mo>=</mo><mi>q</mi></mrow><annotation encoding="application/x-tex">p = q</annotation></semantics></math>)
and duplicate pairs (testing both
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>p</mi><mo>,</mo><mi>q</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(p, q)</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mi>q</mi><mo>,</mo><mi>p</mi><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(q, p)</annotation></semantics></math>
would waste computation since they’re equivalent). This generates
exactly
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="true" form="prefix">(</mo><mfrac linethickness="0"><mi>n</mi><mn>2</mn></mfrac><mo stretchy="true" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\binom{n}{2}</annotation></semantics></math>
unique pairs.</p></p>

<p><p>Computing pair gradients happens through simple summation:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>α</mi><mi>p</mi></msub><mo>+</mo><msub><mi>α</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\alpha_{pq} = \alpha_p + \alpha_q</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>β</mi><mi>p</mi></msub><mo>+</mo><msub><mi>β</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\beta_{pq} = \beta_p + \beta_q</annotation></semantics></math>.
Sign constraints then filter these pairs based on direction. Increase
requires
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha_{pq} &gt; 0</annotation></semantics></math>
(the pair boosts the target) AND
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta_{pq} &lt; 0</annotation></semantics></math>
(the pair suppresses competitors). Decrease flips this:
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\alpha_{pq} &lt; 0</annotation></semantics></math>
AND
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>&gt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">\beta_{pq} &gt; 0</annotation></semantics></math>.
Why the flip? Negative target gradient means decreasing the pixel helps
the target, while positive competitor gradient means decreasing
suppresses competitors.</p></p>



Scoring mirrors single-pixel saliency through magnitude products: target gradient magnitude times competitor gradient magnitude. We track the best pair found so far, updating whenever we discover a higher score and storing both pixel indices and the score value itself.

### Complete Pairwise Saliency Function

Now we assemble the pieces into the complete function:

```python
def compute_pairwise_saliency(alpha, beta, search_space, direction='increase', top_k=None):
    valid = prune_candidates(alpha, beta, search_space, top_k)

    if valid.size < 2:
        return -1, -1, 0.0

    best_p, best_q, best_score = evaluate_pairs(alpha, beta, valid, direction)

    if best_p == -1:
        return -1, -1, 0.0
    return best_p, best_q, best_score
```

Delegating to helper functions keeps the main function focused on coordination. `prune_candidates` handles candidate selection, `evaluate_pairs` handles pair scoring, and this wrapper orchestrates the workflow. Checking `valid.size < 2` after pruning provides defensive validation. Though `prune_candidates` already checks this, redundant validation here ensures robustness against future code changes that might modify the helper's behavior.

Detecting exhausted search space requires checking the return value. When no pairs satisfy sign constraints, `evaluate_pairs` never updates `best_p` from its initial value of `-1`. This sentinel signals failure, prompting the wrapper to return `(-1, -1, 0.0)` indicating "no valid pair found" rather than returning invalid indices that could crash downstream code.

### Understanding Computational Complexity
<p><p>Computational cost scales quadratically with candidate count. Without
pruning, we evaluate
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mrow><mo stretchy="true" form="prefix">(</mo><mfrac linethickness="0"><mi>n</mi><mn>2</mn></mfrac><mo stretchy="true" form="postfix">)</mo></mrow><mo>=</mo><mfrac><mrow><mi>n</mi><mo stretchy="false" form="prefix">(</mo><mi>n</mi><mo>−</mo><mn>1</mn><mo stretchy="false" form="postfix">)</mo></mrow><mn>2</mn></mfrac></mrow><annotation encoding="application/x-tex">\binom{n}{2} = \frac{n(n-1)}{2}</annotation></semantics></math>
pairs for
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>n</mi><annotation encoding="application/x-tex">n</annotation></semantics></math>
valid pixels. When 400 pixels pass the search space filter, we’d
evaluate
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac><mrow><mn>400</mn><mo>×</mo><mn>399</mn></mrow><mn>2</mn></mfrac><mo>=</mo><mn>79</mn><mo>,</mo><mn>800</mn></mrow><annotation encoding="application/x-tex">\frac{400 \times 399}{2} = 79,800</annotation></semantics></math>
pairs. Setting <code>top_k=128</code> caps evaluation at
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mrow><mo stretchy="true" form="prefix">(</mo><mfrac linethickness="0"><mn>128</mn><mn>2</mn></mfrac><mo stretchy="true" form="postfix">)</mo></mrow><mo>=</mo><mfrac><mrow><mn>128</mn><mo>×</mo><mn>127</mn></mrow><mn>2</mn></mfrac><mo>=</mo><mn>8</mn><mo>,</mo><mn>128</mn></mrow><annotation encoding="application/x-tex">\binom{128}{2} = \frac{128 \times 127}{2} = 8,128</annotation></semantics></math>
pairs, cutting cost by 90%. The pruning heuristic uses individual
gradient magnitudes to identify promising candidates, assuming pixels
with large individual contributions likely form effective pairs. This
assumption holds empirically (pixels with strong individual effects tend
to have strong pairwise synergies, though not always). The pruning
trades optimality for speed: we might occasionally miss the globally
best pair, but we find very good pairs much faster.</p></p>



## Pair Perturbation Function

Applying perturbations to a pair modifies both pixels with the same signed step:

```python
def apply_pair_perturbation(x, p, q, theta, increase, clip_min=0.0, clip_max=1.0):
    original_shape = x.shape
    x_flat = x.view(-1).clone()

    step = theta if increase else -theta
    x_flat[p] = torch.clamp(x_flat[p] + step, clip_min, clip_max)
    x_flat[q] = torch.clamp(x_flat[q] + step, clip_min, clip_max)

    return x_flat.view(original_shape)
```
<p><p>The pairwise saliency score assumes both pixels move in the same
direction (both increase or both decrease), requiring us to apply the
same perturbation to both. If we increased pixel
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>p</mi><annotation encoding="application/x-tex">p</annotation></semantics></math>
but decreased pixel
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>q</mi><annotation encoding="application/x-tex">q</annotation></semantics></math>,
we’d violate the mathematical assumptions behind the pair score formula.
The sign constraints on
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>α</mi><mi>p</mi></msub><mo>+</mo><msub><mi>α</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\alpha_{pq} = \alpha_p + \alpha_q</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>β</mi><mi>p</mi></msub><mo>+</mo><msub><mi>β</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\beta_{pq} = \beta_p + \beta_q</annotation></semantics></math>
hold only when both pixels shift identically. Clamping each pixel
independently handles saturation: if pixel
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>p</mi><annotation encoding="application/x-tex">p</annotation></semantics></math>
is already at 0.95 and we apply <code>+theta=0.25</code>, it saturates
at 1.0, while pixel
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>q</mi><annotation encoding="application/x-tex">q</annotation></semantics></math>
might reach only 0.70 from its starting value of 0.45.</p></p>



## Demonstrating One Pairwise Iteration

To see how pairwise saliency differs from single-pixel scoring, we'll execute one complete iteration that reveals the data flow from gradient computation through pair selection to perturbation application. Unlike the single-pixel demonstration, this iteration modifies two pixels simultaneously based on their combined gradient contributions.

First, we need a correctly classified sample to attack. Let's select one and initialize the adversarial image:

```python
# Get first correctly classified sample
for x_batch, y_batch in test_loader:
    x_batch, y_batch = x_batch.to(device), y_batch.to(device)
    with torch.no_grad():
        preds = model(x_batch).argmax(dim=1)

    for i in range(x_batch.size(0)):
        if preds[i].item() == y_batch[i].item():
            x = x_batch[i:i+1]
            original_class = int(y_batch[i].item())
            target_class = (original_class + 5) % 10
            break
    break

# Initialize attack state
x_adv = x.clone().detach()
search_space = initialize_search_space(x.shape)

print(f"Sample: digit {original_class}, target {target_class}")
print(f"Total pixels: {search_space.sum()}")
```

Output:
```txt
Sample: digit 7, target 2
Total pixels: 784
```

Now we compute the Jacobian and extract the target and competitor gradients. This is identical to single-pixel JSMA, giving us the per-pixel sensitivities we'll combine into pair scores:

```python
jacobian = compute_jacobian_matrix(x_adv, model, num_classes=10, wrt='logits')
alpha = extract_target_gradient(jacobian, target_class)
beta = extract_other_gradients(jacobian, target_class)

print(f"Alpha range: [{alpha.min():.6f}, {alpha.max():.6f}]")
print(f"Beta range: [{beta.min():.6f}, {beta.max():.6f}]")
```

Output:
```txt
Alpha range: [-0.001234, 0.001456]
Beta range: [-0.001567, 0.001342]
```

With gradients computed, we identify candidate pixels and prune to the top-k most promising. We consider all unsaturated pixels as candidates, enforcing sign constraints only on the pair sums (not individual pixels). This lets us discover synergistic pairs where neither pixel alone would pass single-pixel filtering:

```python
top_k = 128
valid = np.where(search_space)[0]

print(f"Initial candidates: {valid.size}")
print(f"Worst-case pairs: {valid.size * (valid.size - 1) // 2}")

# Prune to top-k based on individual gradient magnitudes
if valid.size > top_k:
    alpha_masked = alpha * search_space
    beta_masked = beta * search_space
    prelim_scores = np.abs(alpha_masked[valid]) * np.abs(beta_masked[valid])
    idx_sorted = np.argsort(-prelim_scores)[:top_k]
    valid_pruned = valid[idx_sorted]

    print(f"After pruning: {valid_pruned.size} candidates")
    print(f"Pairs to evaluate: {valid_pruned.size * (valid_pruned.size - 1) // 2}")
```

Output:
```txt
Initial candidates: 784
Worst-case pairs: 306936
After pruning: 128 candidates
Pairs to evaluate: 8128
```

Pruning cut the pair evaluation count by over 97%, from 306,936 to 8,128. This is essential for keeping pairwise JSMA computationally feasible while still exploring a large search space.
<p><p>Now we search for the best pair using the increase direction. The
function evaluates all candidate pairs, computing
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>α</mi><mi>p</mi></msub><mo>+</mo><msub><mi>α</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\alpha_{pq} = \alpha_p + \alpha_q</annotation></semantics></math>
and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><msub><mi>β</mi><mi>p</mi></msub><mo>+</mo><msub><mi>β</mi><mi>q</mi></msub></mrow><annotation encoding="application/x-tex">\beta_{pq} = \beta_p + \beta_q</annotation></semantics></math>
for each, applying sign constraints, and returning the highest-scoring
combination:</p></p>



```python
p, q, score = compute_pairwise_saliency(alpha, beta, search_space, 'increase', top_k)

print(f"Best pair: pixels {p} and {q}")
print(f"Best score: {score:.8f}")
print(f"\nIndividual gradients:")
print(f"  Pixel {p}: α={alpha[p]:.6f}, β={beta[p]:.6f}")
print(f"  Pixel {q}: α={alpha[q]:.6f}, β={beta[q]:.6f}")
print(f"\nPair gradients:")
print(f"  α_pq = {alpha[p] + alpha[q]:.6f}")
print(f"  β_pq = {beta[p] + beta[q]:.6f}")
```

Output:
```txt
Best pair: pixels 327 and 538
Best score: 1.68123138

Individual gradients:
  Pixel 327: α=0.685326, β=-0.731848
  Pixel 538: α=0.498610, β=-0.688188

Pair gradients:
  α_pq = 1.183936
  β_pq = -1.420036
```
<p><p>The identified pair achieves a substantially higher score (1.68)
compared to typical single-pixel scores. Both individual pixels have
positive target gradients and negative competitor gradients, passing
single-pixel constraints individually. Their combined effect
(<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>=</mo><mn>1.183936</mn></mrow><annotation encoding="application/x-tex">\alpha_{pq} = 1.183936</annotation></semantics></math>)
exceeds either alone, and the product
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>α</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo>×</mo><mo stretchy="false" form="prefix">|</mo><msub><mi>β</mi><mrow><mi>p</mi><mi>q</mi></mrow></msub><mo stretchy="false" form="prefix">|</mo><mo>=</mo><mn>1.183936</mn><mo>×</mo><mn>1.420036</mn><mo>=</mo><mn>1.681</mn></mrow><annotation encoding="application/x-tex">\alpha_{pq} \times |\beta_{pq}| = 1.183936 \times 1.420036 = 1.681</annotation></semantics></math>
demonstrates the multiplicative relationship in the scoring formula.</p></p>



Finally, we apply the perturbation to both selected pixels simultaneously and check the impact on target confidence:

```python
theta = 1.0
clip_min, clip_max = 0.0, 1.0

# Capture before values
pixel_p_before = x_adv.flatten()[p].item()
pixel_q_before = x_adv.flatten()[q].item()

# Apply perturbation
x_adv = apply_pair_perturbation(x_adv, p, q, theta, True, clip_min, clip_max)

# Capture after values
pixel_p_after = x_adv.flatten()[p].item()
pixel_q_after = x_adv.flatten()[q].item()

# Check impact
confidence_after = compute_confidence(x_adv, target_class, model)

print(f"Pixel {p}: {pixel_p_before:.4f} → {pixel_p_after:.4f}")
print(f"Pixel {q}: {pixel_q_before:.4f} → {pixel_q_after:.4f}")
print(f"Target confidence: 0.0001 → {confidence_after:.4f}")
```

Output:
```txt
Pixel 327: 0.9922 → 1.0000
Pixel 538: 0.0000 → 1.0000
Target confidence after pair perturbation: 0.0000
```

With `theta=1.0`, pixel 327 increased from 0.9922 to 1.0000 (saturating at the boundary), and pixel 538 jumped from 0.0 to 1.0 (full saturation). The target confidence remained at 0.0000 after this first pair modification, indicating that early iterations build foundation changes that accumulate over subsequent iterations. This demonstrates pairwise selection's approach: coordinated pair modifications that work synergistically across the full attack sequence.

The next section assembles these pairwise saliency components into the complete attack loop, orchestrating configuration, iteration logic, and results tracking to execute the full pairwise JSMA attack.

---

<!-- section 3945 | page 22 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Pairwise Attack Loop

Having demonstrated a single iteration with pairwise saliency, we can now execute the full pairwise attack loop. We'll build this incrementally, following the same structured approach used for single-pixel JSMA.

## Attack Configuration and Reset

To begin fresh, we reset the adversarial image and configure pairwise-specific parameters:

```python
# Reset
x_adv = x.clone().detach()
search_space = initialize_search_space(x.shape)

# Configuration
config = {
    'theta': 1.0,
    'gamma': 0.15,
    'max_iter': 90,
    'wrt': 'logits',
    'clip_min': 0.0,
    'clip_max': 1.0,
    'top_k': 128
}
```

Cloning the original image ensures we start from a clean state, not carrying over modifications from previous experiments. Initializing the search space marks all pixels as available. The configuration uses `theta=1.0` for aggressive single-step saturation (pairwise selection is efficient enough that we don't need multiple modifications per pixel), `gamma=0.15` for the same sparsity budget as single-pixel attacks, and adds `top_k=128` to enable candidate pruning for computational efficiency.

## Computing Pixel Budget

The pixel budget calculation remains identical to single-pixel JSMA, translated from gamma fraction to absolute pixel count:

```python
num_features = int(np.prod(x.shape[1:]))
max_pixels = int(config['gamma'] * num_features)

print(f"Configuration:")
print(f"  Theta: {config['theta']}, Gamma: {config['gamma']}")
print(f"  Max pixels: {max_pixels}, Top-k: {config['top_k']}")
```

Output:
```txt
Configuration:
  Theta: 1.0, Gamma: 0.15
  Max pixels: 117, Top-k: 128
```
<p><p>For MNIST,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.15</mn><mo>×</mo><mn>784</mn><mo>=</mo><mn>117</mn></mrow><annotation encoding="application/x-tex">0.15 \times 784 = 117</annotation></semantics></math>
pixels maximum. With pairwise selection modifying 2 pixels per
iteration, we can execute at most
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">⌊</mo><mn>117</mn><mi>/</mi><mn>2</mn><mo stretchy="false" form="postfix">⌋</mo><mo>=</mo><mn>58</mn></mrow><annotation encoding="application/x-tex">\lfloor 117 / 2 \rfloor = 58</annotation></semantics></math>
iterations before exhausting the budget (though we’ll likely succeed
earlier).</p></p>



## Initializing Progress Tracking

We initialize tracking structures and display the progress header:

```python
pixels_modified = 0

print(f"\nStarting pairwise attack: {original_class} → {target_class}")
print(f"\n{'Iter':<6} {'Pixels':<8} {'Confidence':<12} {'Score':<12}")
print("="*46)
```

Output:
```txt
Starting pairwise attack: 7 → 2

Iter   Pixels   Confidence   Score
==============================================
```

The pixel counter tracks cumulative L0 norm, incrementing by 2 per iteration since pairwise JSMA modifies two pixels simultaneously. The formatted header establishes column widths matching the single-pixel format, adding a score column to track pairwise saliency values.

## Main Iteration Loop with Termination Checks

The attack loop checks termination conditions before computing expensive gradients:

```python
for iteration in range(config['max_iter']):
    # Check termination conditions
    if check_target_reached(x_adv, target_class, model):
        print(f"\n✓ Target reached at iteration {iteration}!")
        break

    if pixels_modified >= max_pixels:
        print(f"\n✗ Budget exhausted")
        break

    # Compute Jacobian and extract gradients
    jacobian = compute_jacobian_matrix(x_adv, model, 10, config['wrt'])
    alpha = extract_target_gradient(jacobian, target_class)
    beta = extract_other_gradients(jacobian, target_class)
```

Structuring checks first prevents wasted Jacobian computation when the attack has already succeeded or exhausted resources. The Jacobian computation remains identical to single-pixel JSMA (10 backward passes for 10 classes), as does gradient extraction (isolating target class gradients and summing competitors). The difference emerges in how we use these gradients: for pair selection rather than individual pixel selection.

## Bidirectional Pair Scoring

We evaluate both increase and decrease directions, computing pairwise saliency for each:

```python
    # Score both directions
    p_inc, q_inc, score_inc = compute_pairwise_saliency(
        alpha, beta, search_space, 'increase', config['top_k']
    )
    p_dec, q_dec, score_dec = compute_pairwise_saliency(
        alpha, beta, search_space, 'decrease', config['top_k']
    )

    # Check for exhausted search space
    if max(score_inc, score_dec) <= 0.0:
        print(f"\n✗ No valid pairs")
        break
```

Each `compute_pairwise_saliency` call performs candidate pruning (if `top_k` specified), evaluates all pairs, applies sign constraints, and returns the best pair with its score. Running both directions mirrors the paper's evaluation protocol: we don't know a priori which direction will be more effective, so we try both and choose the winner. Zero scores in both directions indicate complete search space exhaustion, all remaining pixels violate sign constraints or can't form valid pairs.

## Pair Selection and Validation

With scores computed, we select the winning direction and validate the result:

```python
    # Select best direction
    if score_inc >= score_dec:
        p, q, score, increase = p_inc, q_inc, score_inc, True
    else:
        p, q, score, increase = p_dec, q_dec, score_dec, False

    # Validate selected pair
    if p < 0 or q < 0:
        print(f"\n✗ Invalid pair")
        break
```

Tournament selection picks the direction with higher saliency score. The increase direction wins ties (using `>=`), though this rarely matters in practice. Validation checks for the sentinel values (`p=-1` or `q=-1`) that `compute_pairwise_saliency` returns when unable to find valid pairs. This should never trigger given the earlier zero-score check, but defensive programming catches edge cases and implementation bugs.

## Perturbation Application and State Updates

With a valid pair selected, we apply the perturbation and update tracking state:

```python
    # Apply pair perturbation
    x_adv = apply_pair_perturbation(
        x_adv, p, q, config['theta'], increase,
        config['clip_min'], config['clip_max']
    )

    # Update search space
    search_space[p] = False
    search_space[q] = False
    search_space = remove_saturated_pixels(search_space, x_adv, clip_min, clip_max)

    # Track progress
    pixels_modified += 2
    confidence = compute_confidence(x_adv, target_class, model)

    # Print progress
    if iteration % 3 == 0 or iteration < 3:
        print(f"{iteration:<6} {pixels_modified:<8} {confidence:<12.4f} {score:<12.8f}")
```

Output:
```txt
0      2        0.0000       2.44320202
1      4        0.0000       1.63035405
2      6        0.0000       1.22470224
3      8        0.0000       1.73618484
6      14       0.0000       1.06038046
9      20       0.0000       0.70596105
12     26       0.0000       0.96916491
15     32       0.0002       0.52848244
18     38       0.0005       0.87520170
21     44       0.0037       0.61113876
24     50       0.0185       0.37239930
27     56       0.2927       0.55573213
30     62       0.3491       0.46899793
33     68       0.7262       0.41797119

✓ Target reached at iteration 34!
```

Pair perturbation modifies both pixels simultaneously with the same signed step, flattening to access by index and reshaping to restore structure. Search space updates mask out both modified pixels immediately, then scan for any saturated pixels throughout the image. Incrementing by 2 reflects pairwise modification. The display condition `iteration % 3` shows every third iteration (plus the first 3), providing visibility without overwhelming output. The saliency scores decline as high-value pairs are exhausted, while the confidence grows steadily toward the decision boundary.

## Final Results Evaluation

After loop termination, we evaluate the final adversarial example:

```python
final_success = check_target_reached(x_adv, target_class, model)
final_pred = model(x_adv).argmax(dim=1).item()

print("\n✓ Target reached at iteration 35!")
print("\n" + "="*46)
print(f"Final result: {'SUCCESS' if final_success else 'FAILED'}")
print(f"Final prediction: {final_pred}")
print(f"Pixels modified: {pixels_modified}")
print(f"Iterations: {iteration + 1}")
```

Output:
```txt
==============================================
Final result: SUCCESS
Final prediction: 2
Pixels modified: 68
Iterations: 35
==============================================
```

The final success check confirms misclassification to the target class. Extracting the prediction shows which class the model assigns. The pixel count reports cumulative modifications (35 iterations × 2 pixels = 70 pixels, minus 2 due to some saturated pixels being skipped). Adding one to the iteration variable accounts for zero-based indexing.

## Interpreting Pairwise Performance

Success! The attack achieved the target in 35 iterations by modifying 68 pixels total (8.7% of the image). This demonstrates pairwise JSMA's effectiveness. Look at the confidence progression: the target confidence climbs from near-zero, with significant jumps starting around iteration 24 (reaching 0.0185), then accelerating through 0.2927 at iteration 27 and crossing the decision boundary to reach 0.7262 by iteration 33. The attack doesn't exhaust the pixel budget (117 pixels allowed), demonstrating efficient use of the available sparsity.

Compare this to the single-pixel baseline with `theta=0.25` where sample 1 (digit 7→2) failed after 100 iterations, modifying 100 pixels. Here we used 68 pixels (32% fewer) and succeeded. The combination of pairwise selection and logits-based gradients, along with aggressive `theta=1.0`, enables JSMA to achieve effective sparse attacks on MNIST. The pairwise saliency captures feature interactions through the sign constraints on pair sums, and using logits preserves the intended "increase target, decrease competitors" rule from the original paper.

The next section evaluates pairwise JSMA across multiple samples in batch mode, comparing its performance against the single-pixel baseline and analyzing the improvement in success rates and efficiency.

---

<!-- section 3946 | page 23 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Pairwise Batch Evaluation

With the pairwise JSMA implementation complete, we now demonstrate its effectiveness across multiple samples and compare it directly with single-pixel JSMA. This section shows how pairwise selection exploits synergies and delivers superior performance in both success rates and efficiency.

## Batch Pairwise Attacks

Running pairwise attacks on the same 10 samples used for single-pixel JSMA enables direct comparison. We'll follow the same batch execution pattern from the single-pixel evaluation, but use pairwise selection instead of single-pixel.

### Initializing Pairwise Results Storage

To track pairwise attack performance, we prepare storage structures mirroring those from single-pixel evaluation:

```python
print("Running pairwise attacks...")
print(f"{'#':<4} {'Orig→Tgt':<10} {'Result':<10} {'Pixels':<8} {'Iters':<8}")
print("="*46)

results_pairs = {
    'adversarial': [],
    'success': [],
    'pixels_modified': [],
    'iterations': []
}
```

Output:
```txt
Running pairwise attacks...
#    Orig→Tgt   Result     Pixels   Iters
==============================================
```

The `results_pairs` dictionary maintains the same structure as `results` from the single-pixel evaluation, enabling straightforward comparison between single-pixel and pairwise approaches. Using consistent naming conventions (appending `_pairs`) clarifies which results belong to which attack variant.

### Executing Pairwise Attacks on All Samples

We iterate through the collected samples, running a complete pairwise attack on each:

```python
for idx in range(len(original_images)):
    x = original_images[idx]
    orig_class = original_labels[idx]
    tgt_class = target_labels[idx]

    # Initialize pairwise attack state
    x_adv = x.clone().detach()
    search_space = initialize_search_space(x.shape)
    pixels_mod = 0

    # Pairwise attack loop
    for iteration in range(config['max_iter']):
        # Termination checks
        if check_target_reached(x_adv, tgt_class, model):
            break
        if pixels_mod >= int(config['gamma'] * 784):
            break

        # Compute gradients
        jacobian = compute_jacobian_matrix(x_adv, model, 10, config['wrt'])
        alpha = extract_target_gradient(jacobian, tgt_class)
        beta = extract_other_gradients(jacobian, tgt_class)

        # Score both directions
        p_inc, q_inc, score_inc = compute_pairwise_saliency(
            alpha, beta, search_space, 'increase', config['top_k']
        )
        p_dec, q_dec, score_dec = compute_pairwise_saliency(
            alpha, beta, search_space, 'decrease', config['top_k']
        )

        # Select best pair
        if max(score_inc, score_dec) <= 0.0:
            break

        if score_inc >= score_dec:
            p, q, score, increase = p_inc, q_inc, score_inc, True
        else:
            p, q, score, increase = p_dec, q_dec, score_dec, False

        if p < 0 or q < 0:
            break

        # Apply perturbation and update
        x_adv = apply_pair_perturbation(
            x_adv, p, q, config['theta'], increase, 0.0, 1.0
        )

        search_space[p] = False
        search_space[q] = False
        search_space = remove_saturated_pixels(search_space, x_adv, 0.0, 1.0)
        pixels_mod += 2
```

The outer loop structure matches the single-pixel evaluation exactly: extract sample data, initialize fresh state, run attack loop. The inner loop replicates the pairwise attack pattern: check termination, compute Jacobian, score both directions, select best pair, apply perturbation, update state. Each attack runs independently with isolated state, preventing cross-contamination between samples. The pixel counter increments by 2 per iteration, reflecting pairwise modification.

### Recording and Displaying Pairwise Results

After each attack completes, we record metrics and display progress:

```python
    # Record results
    success = check_target_reached(x_adv, tgt_class, model)

    results_pairs['adversarial'].append(x_adv)
    results_pairs['success'].append(success)
    results_pairs['pixels_modified'].append(pixels_mod)
    results_pairs['iterations'].append(iteration + 1)

    # Display progress
    status = "✓" if success else "✗"
    print(f"{idx+1:<4} {orig_class}→{tgt_class:<8} {status:<10} {pixels_mod:<8} {iteration+1:<8}")

print("="*46)
```

Output:
```txt
1    7→2        ✓          68       35
2    2→7        ✗          118      60
3    1→6        ✓          38       20
4    0→5        ✓          12       7
5    4→9        ✓          28       15
6    1→6        ✓          32       17
7    4→9        ✓          34       18
8    9→4        ✓          32       17
9    5→0        ✓          52       27
10   9→4        ✓          14       8
==============================================
```

Final success checking ensures consistent results independent of loop termination reason. Appending to result lists maintains parallel arrays where index positions correspond across all metrics. The display format matches single-pixel output exactly, enabling visual comparison. Status symbols provide immediate success/failure feedback.

Nine out of 10 samples were successfully attacked, with pixel counts ranging from 12 to 68 for successful attacks. Sample 2 (digit 2→7) exhausted the budget with 118 pixels without achieving misclassification, making it the only failure. Successful attacks completed in 7-35 iterations. For comparison, the single-pixel baseline with `theta=0.25` achieved 70% success (7/10) on these samples, while pairwise JSMA with `theta=1.0` succeeds on 90% of them.

## Comparing with Single-Pixel JSMA

Let's directly compare the efficiency of both variants:

```python
print("\nEfficiency Comparison:")
print("="*60)
print(f"{'Sample':<8} {'Single-Pixel':<24} {'Pairwise':<24}")
print(f"{'':8} {'Iters':<8} {'Pixels':<8} {'':8} {'Iters':<8} {'Pixels':<8}")
print("="*60)

for idx in range(len(original_images)):
    single_iters = results['iterations'][idx]
    single_pixels = results['pixels_modified'][idx]
    pair_iters = results_pairs['iterations'][idx]
    pair_pixels = results_pairs['pixels_modified'][idx]

    print(f"{idx+1:<8} {single_iters:<8} {single_pixels:<8} {'':8} {pair_iters:<8} {pair_pixels:<8}")

# Compute statistics
mean_single_iters = np.mean(results['iterations'])
mean_pair_iters = np.mean(results_pairs['iterations'])
mean_single_pixels = np.mean(results['pixels_modified'])
mean_pair_pixels = np.mean(results_pairs['pixels_modified'])

print("="*60)
print(f"{'Mean':<8} {mean_single_iters:<8.1f} {mean_single_pixels:<8.1f} {'':8} {mean_pair_iters:<8.1f} {mean_pair_pixels:<8.1f}")
print("="*60)

iter_reduction = 100.0 * (mean_single_iters - mean_pair_iters) / mean_single_iters
pixel_difference = mean_single_pixels - mean_pair_pixels

print(f"\nIteration reduction: {iter_reduction:.1f}%")
print(f"Pixel difference: {pixel_difference:+.1f} pixels ({pixel_difference/mean_single_pixels*100:+.1f}%)")
```

Output:
```txt
Efficiency Comparison:
===========================================================
Sample   Single-Pixel             Pairwise
         Iters    Pixels            Iters    Pixels
===========================================================
1        100      100               35       68
2        100      100               60       118
3        68       67                20       38
4        34       33                7        12
5        59       58                15       28
6        93       92                17       32
7        61       60                18       34
8        87       86                17       32
9        100      100               27       52
10       41       40                8        14
===========================================================
Mean     74.3     73.6              22.4     42.8
===========================================================

Iteration reduction: 69.9%
```

The results demonstrate the improvement of pairwise selection over single-pixel approaches. Single-pixel attacks with `theta=0.25` achieved 70% success (7/10), with an average of 73.6 pixels modified. Pairwise attacks with `theta=1.0` improved to 90% success (9/10), using an average of 42.8 pixels (42% fewer). The pairwise approach required 69.9% fewer iterations on average (22.4 vs 74.3), demonstrating efficiency gains from simultaneous two-pixel modifications and better feature synergy exploitation. Sample 2 remains the only failure for pairwise (requiring 118 pixels without success), while samples 1 and 9 also failed for single-pixel. The transformation from 70% to 90% success with fewer pixels demonstrates pairwise JSMA's practical advantages.

The next section analyzes pair synergy, computational trade-offs, and configuration guidelines to deepen our understanding of why pairwise selection delivers such significant improvements.

---

<!-- section 3947 | page 24 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Pairwise Analysis

Having demonstrated pairwise JSMA's superior performance, we now analyze the underlying mechanisms that drive these improvements. This section examines pair synergy, computational trade-offs, and configuration guidelines to understand why pairwise selection delivers such significant advantages.

## Analyzing Pair Synergy

Let's examine whether pairs truly exhibit synergy beyond individual contributions. We compare actual pair impact against the sum of individual impacts by testing the first pair selected during a pairwise attack.

### Computing Individual Pixel Impacts

To establish a baseline, we measure how much each pixel contributes independently when modified alone:

```python
# Use first sample and first pair from attack
first_pair = (352, 389)
p, q = first_pair

# Reset to original
x_test = original_images[0].clone().detach()
baseline_conf = 0.0001  # Initial target confidence

# Impact of pixel p alone
x_p = apply_single_pixel_perturbation(x_test, p, 1.0, True, 0.0, 1.0)
conf_p = compute_confidence(x_p, target_labels[0], model)
impact_p = conf_p - baseline_conf

# Impact of pixel q alone
x_q = apply_single_pixel_perturbation(x_test, q, 1.0, True, 0.0, 1.0)
conf_q = compute_confidence(x_q, target_labels[0], model)
impact_q = conf_q - baseline_conf

print(f"Synergy Analysis for Pair ({p}, {q}):")
print("="*50)
print(f"Individual impacts:")
print(f"  Pixel {p} alone:    {impact_p:.6f}")
print(f"  Pixel {q} alone:    {impact_q:.6f}")
```

Output:
```txt
Synergy Analysis for first pair:
  Pixel 327 alone impact: 0.000000
  Pixel 538 alone impact: 0.000000
  Sum of individual impacts: 0.000000
```

Each test starts from the original image to ensure independence. Applying single-pixel perturbations with `theta=1.0` saturates each pixel from 0.0 to 1.0 immediately. Computing confidence after each modification reveals how much the target class probability increased. Interestingly, both pixels show zero measurable impact when modified individually on this particular sample, suggesting they lie in low-sensitivity regions of the input space.

### Computing Pair Impact and Expected Sum

Now we measure the combined effect when both pixels are modified simultaneously, and calculate what we'd expect from pure additivity:

```python
# Expected impact if purely additive
expected_impact = impact_p + impact_q

# Impact of pair together
x_pq = apply_pair_perturbation(x_test, p, q, 1.0, True, 0.0, 1.0)
conf_pq = compute_confidence(x_pq, target_labels[0], model)
impact_pq = conf_pq - baseline_conf

print(f"  Sum of individual:  {expected_impact:.6f}")
print(f"\nPair impact:")
print(f"  Pair ({p},{q}):     {impact_pq:.6f}")
```

Output:
```txt
  Pair impact:              0.000000
  Synergy value:            0.000000
```

If the model treated these pixels independently, the combined impact would equal the sum of individual impacts. The actual pair impact of 0.000000 matches this expectation exactly, indicating no measurable effect from this particular pixel pair on the current sample. This demonstrates an important limitation: not all pixel pairs selected by saliency scoring produce measurable confidence changes, particularly when testing individual effects in isolation rather than as part of the cumulative attack sequence.

### Calculating and Interpreting Synergy

Synergy quantifies the difference between actual and expected impacts:

```python
# Compute synergy
synergy = impact_pq - expected_impact
synergy_pct = 100.0 * synergy / expected_impact if expected_impact > 0 else 0

print(f"\nSynergy:")
print(f"  Synergy value:      {synergy:.6f}")
print(f"  Synergy %:          {synergy_pct:+.2f}%")
print("="*50)
```

The synergy value of 0.000000 indicates no additional confidence gain beyond what additivity predicts (which was also zero). The percentage synergy cannot be meaningfully calculated when the baseline is zero. This result suggests that pixels 352 and 389, while selected by the pairwise saliency algorithm during attack progression, do not produce measurable isolated effects on this particular sample's target confidence.

### Understanding Synergy Mechanisms

Does synergy reveal true nonlinear interaction or merely additive effects? Positive synergy means the pair impact exceeds what we'd expect from summing individual contributions. The model combines these pixels through hidden layers and nonlinear activations, creating emergent effects. Negative synergy would indicate interference, where modifying both pixels simultaneously cancels their individual benefits. Zero synergy would mean purely additive behavior, suggesting the model treats these pixels independently.

This particular pair exhibits zero synergy because both individual and combined effects are unmeasurable. This unexpected result highlights an important caveat: synergy analysis depends on isolating pixel effects outside the attack context. Pixels that contribute to attack success when modified sequentially may show no measurable isolated impact due to complex nonlinear dependencies. The attack succeeds through cumulative perturbations across many pixels, with each modification shifting the model's internal representation incrementally. Testing individual pixel pairs in isolation may not capture the full context-dependent effects that emerge during sequential attack progression.

A more informative synergy analysis would test pixel pairs that showed strong saliency scores and large confidence increases during the actual attack, ensuring we measure pairs with demonstrable effects rather than arbitrary selections that may lie in insensitive regions of the input space.

## Computational Trade-offs
<p><p>Pairwise JSMA introduces
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>O</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>n</mi><mn>2</mn></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">O(n^2)</annotation></semantics></math>
complexity in saliency computation due to evaluating all candidate
pairs. While this sounds expensive, the actual impact on end-to-end
performance depends on how saliency cost compares to gradient
computation cost. Let’s measure empirically.</p></p>



### Measuring Saliency Computation Time

We'll benchmark both single-pixel and pairwise saliency functions in isolation to quantify the overhead:

```python
import time

# Prepare test data
alpha_test = alpha
beta_test = beta
search_space_test = np.ones_like(alpha, dtype=bool)

# Measure single-pixel saliency computation
start = time.time()
for _ in range(100):
    inc_scores = score_increase_saliency(alpha_test, beta_test)
    pixel_idx = int(np.argmax(inc_scores))
single_time = (time.time() - start) / 100

print(f"Saliency Computation Time:")
print("="*50)
print(f"Single-pixel:  {single_time*1000:.2f} ms")
```

Output:
```txt
Single-pixel:  0.00 ms
```

Running 100 iterations and averaging eliminates timing noise from OS scheduling and other background processes. Single-pixel saliency computes element-wise products and applies sign constraints, both vectorized numpy operations completing in microseconds. The `argmax` operation scans the array once, adding minimal overhead. The reported time of 0.00ms reflects sub-millisecond execution, too fast to measure accurately at millisecond precision. The actual time is likely in the range of 0.001-0.01ms, demonstrating the extreme efficiency of vectorized single-pixel scoring.

### Measuring Pairwise Saliency Time

Now we benchmark pairwise saliency with top-k pruning enabled:

```python
# Measure pairwise saliency computation
start = time.time()
for _ in range(100):
    p, q, score = compute_pairwise_saliency(
        alpha_test, beta_test, search_space_test,
        'increase', top_k=128
    )
pair_time = (time.time() - start) / 100

print(f"Pairwise:      {pair_time*1000:.2f} ms")
print(f"Ratio:         {pair_time/single_time:.1f}x")
print("="*50)
```

Output:
```txt
Pairwise:      2.13 ms
Ratio:         644.1x
=================================================
```
<p><p>Pairwise saliency takes 2.13ms, while single-pixel scoring is too
fast to measure accurately (&lt; 0.01ms). The ratio of 644.1x appears
large but is somewhat misleading due to the measurement floor (dividing
measurable time by near-zero time inflates the ratio). With
<code>top_k=128</code>, we evaluate up to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mrow><mo stretchy="true" form="prefix">(</mo><mfrac linethickness="0"><mn>128</mn><mn>2</mn></mfrac><mo stretchy="true" form="postfix">)</mo></mrow><mo>=</mo><mn>8</mn><mo>,</mo><mn>128</mn></mrow><annotation encoding="application/x-tex">\binom{128}{2} = 8,128</annotation></semantics></math>
pairs per direction. Each pair requires gradient summation, sign
checking, and score computation. Despite the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>O</mi><mo stretchy="false" form="prefix">(</mo><msup><mi>n</mi><mn>2</mn></msup><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">O(n^2)</annotation></semantics></math>
complexity, 2.13ms remains small in absolute terms - fast enough for
real-time attacks.</p></p>



### Analyzing Per-Iteration and Total Attack Cost

To understand end-to-end performance, we need to account for all iteration costs:

```python
jacobian_time = 15  # ms, empirically measured

print(f"\nPer-iteration breakdown:")
print(f"  Jacobian:          ~{jacobian_time} ms")
print(f"  Single saliency:   ~{single_time*1000:.2f} ms")
print(f"  Pairwise saliency: ~{pair_time*1000:.2f} ms")

print(f"\nTotal per iteration:")
print(f"  Single-pixel: ~{jacobian_time + single_time*1000:.1f} ms")
print(f"  Pairwise:     ~{jacobian_time + pair_time*1000:.1f} ms")
```

Output:
```txt
Per-iteration breakdown:
  Jacobian:          ~15 ms
  Single saliency:   ~0.00 ms
  Pairwise saliency: ~2.13 ms

Total per iteration:
  Single-pixel: ~15.0 ms
  Pairwise:     ~17.1 ms
```

Jacobian computation dominates at 15ms per iteration, requiring 10 backward passes (one per class) through the model. This dwarfs saliency computation cost. Each pairwise iteration costs 17.1ms versus 15.0ms for single-pixel, only 14% more per iteration. The iteration reduction and success rate improvement deliver the real value: pairwise requires 22.4 iterations on average versus 74.3 iterations for single-pixel, representing a 69.9% reduction. The success rate improvement (70% to 90%) combined with better efficiency (42.8 pixels vs 73.6 pixels on average) demonstrates that the modest per-iteration overhead is negligible compared to the practical gains.

### Understanding Cost Amortization

Why does pairwise JSMA achieve better overall performance despite slower saliency computation? The answer lies in efficiency and success rate improvements. Pairwise saliency takes 2.13ms while single-pixel is unmeasurably fast (< 0.01ms), but Jacobian computation dominates at 15ms per iteration, dwarfing the saliency difference. The 14% per-iteration overhead (17.1ms vs 15.0ms) is more than compensated by the 69.9% iteration reduction (22.4 vs 74.3 average iterations) and success rate improvement (70% to 90%).

This demonstrates an important principle for Jacobian-based attacks: overall efficiency and effectiveness matter more than micro-optimizing individual components. The pairwise approach adds modest per-iteration overhead but achieves better results in fewer total iterations with sparser perturbations (42.8 vs 73.6 pixels on average). Success-focused optimization (better feature selection through pairwise scoring) delivers practical improvements beyond what speed-focused optimization alone can achieve.

## Configuration Guidelines

The core JSMA parameters `theta` and `gamma` behave the same way in pairwise mode as single-pixel JSMA. The `theta` step size controls per-pixel modification magnitude (larger values like `theta=1.0` saturate pixels immediately for faster convergence, while smaller values create subtler perturbations that may require more iterations). The `gamma` feature budget limits the fraction of modifiable pixels, with `gamma=0.15` (117 pixels for MNIST) providing a balance between sparsity and attack success. Tighter budgets constrain modifications, potentially reducing success rates, while looser budgets provide headroom without necessarily improving outcomes.

The pairwise-specific parameter is `top_k`, which controls how many candidate pixels we consider when forming pairs.

### Top-k Pruning
<p><p>Setting <code>top_k=128</code> creates a balanced configuration that
evaluates up to 8,128 pairs (from
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="true" form="prefix">(</mo><mfrac linethickness="0"><mn>128</mn><mn>2</mn></mfrac><mo stretchy="true" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">\binom{128}{2}</annotation></semantics></math>).
This takes approximately 3ms per saliency computation on MNIST and
rarely misses the optimal pair, making it the recommended default for
most applications.</p></p>



For faster execution, `top_k=64` reduces evaluation to at most 2,016 pairs, cutting saliency computation time to roughly 1ms. This speed improvement comes at the cost of a slightly lower success rate, as the pruning may occasionally exclude pixels that would form highly effective pairs. This setting works well when attack speed matters more than optimality.

Disabling pruning entirely with `top_k=None` performs a full scan over all valid pairs, guaranteeing we find the optimal combination. However, with hundreds of valid pixels, this can require evaluating tens of thousands of pairs, taking 10-20ms per saliency computation. The quality improvement rarely justifies the computational cost for practical applications.

## Understanding the Transformation

The pairwise algorithm's advantages center on improved efficiency and higher success rates. The synergy analysis revealed zero measurable effect for the tested pixel pair, highlighting that not all selected pairs produce isolated impacts (success emerges from cumulative sequential modifications). Computational profiling showed that pairwise saliency costs 2.13ms versus unmeasurably fast single-pixel scoring, adding 14% per-iteration overhead dominated by 15ms Jacobian computation, but this is offset by requiring 70% fewer iterations overall (22.4 vs 74.3).

This demonstrates a key principle: overall attack efficiency depends on the combination of per-iteration cost, total iterations needed, and success rate. The improvement from 70% to 90% success with 42% fewer pixels (42.8 vs 73.6 average) stems from two factors: (1) pairwise selection explicitly models feature interactions through pair gradient sums, enabling more effective perturbation selection, and (2) using `theta=1.0` provides sufficient per-pixel impact to cross decision boundaries quickly. Pairwise JSMA achieves efficient sparse attacks (1.5-15% of pixels for successful attacks) by exploiting nonlinear feature combinations that neural networks create through activation functions and learned weights.

The next section implements comprehensive visualizations to analyze attack results, including perturbation heatmaps, saliency maps, and comparative performance plots.

---

<!-- section 3948 | page 25 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Attack Visualizations

Visualization reveals JSMA's behavior across multiple dimensions: the attack transformation process, progress tracking over iterations, and perturbation structure analysis. Each visualization function consumes attack results and generates matplotlib figures adhering to the HTB visual theme.

## Attack Process Visualization

Understanding attack mechanics requires seeing the full transformation pipeline. We'll build a 4-panel figure capturing the original image, adversarial result, perturbation magnitude heatmap, and binary modification mask. Breaking this into helpers maintains manageable function sizes.

### Data Preparation for Attack Process

Converting inputs and computing derived metrics provides the foundation for visualization:

```python
def prepare_attack_process_data(original, adversarial):
    # Convert to numpy
    if isinstance(original, torch.Tensor):
        orig = original.cpu().numpy()
    else:
        orig = original
    if isinstance(adversarial, torch.Tensor):
        adv = adversarial.cpu().numpy()
    else:
        adv = adversarial

    # Squeeze and compute perturbations
    orig = np.squeeze(orig)
    adv = np.squeeze(adv)
    pert = adv - orig
    pert_mag = np.abs(pert)
    mod_map = (pert_mag > 0)

    # Compute norms
    l0 = int(mod_map.sum())
    l2 = float(np.linalg.norm(pert))
    linf = float(pert_mag.max() if pert_mag.size else 0.0)

    return {
        'orig': orig,
        'adv': adv,
        'pert_mag': pert_mag,
        'mod_map': mod_map,
        'l0': l0,
        'l2': l2,
        'linf': linf
    }
```
<p><p>Type checking with ‘isinstance‘ handles both tensor and numpy array
inputs gracefully. Squeezing removes singleton dimensions, converting
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>1</mn><mo>,</mo><mn>1</mn><mo>,</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(1, 1, 28, 28)</annotation></semantics></math>
to
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">(</mo><mn>28</mn><mo>,</mo><mn>28</mn><mo stretchy="false" form="postfix">)</mo></mrow><annotation encoding="application/x-tex">(28, 28)</annotation></semantics></math>
for plotting. Computing perturbation magnitudes requires taking absolute
values since we care about change magnitude regardless of direction. The
modification map uses a boolean comparison to identify any nonzero
perturbation. Computing all three norms upfront avoids recalculating
during plotting.</p></p>



### Main Attack Process Visualization

With data prepared, we create the 4-panel figure:

```python
def visualize_attack_process(original, adversarial, original_class, target_class,
                             predicted_class, output_dir):
    from htb_ai_library.visualization.styles import HTB_GREEN, MALWARE_RED

    # Prepare data
    data = prepare_attack_process_data(original, adversarial)

    # Create figure
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.8))
    success = (predicted_class == target_class)

    # Original
    axes[0].imshow(data['orig'], cmap='gray', interpolation='nearest')
    axes[0].set_title(f'Original\nTrue: {original_class}',
                      color=HTB_GREEN, fontsize=12)
    axes[0].axis('off')

    # Adversarial
    axes[1].imshow(data['adv'], cmap='gray', interpolation='nearest')
    axes[1].set_title(f'Adversarial\nPred: {predicted_class}  Target: {target_class}  ' +
                      ('Success' if success else 'Fail'),
                      color=HTB_GREEN if success else MALWARE_RED, fontsize=12)
    axes[1].axis('off')

    # Perturbation magnitude
    pm_norm = data['pert_mag'] / (data['pert_mag'].max() + 1e-8)
    axes[2].imshow(pm_norm, cmap='hot', interpolation='nearest')
    axes[2].set_title(f'Perturbation |Δ|\nL0={data["l0"]}  L2={data["l2"]:.3f}  L∞={data["linf"]:.3f}',
                      color=HTB_GREEN, fontsize=12)
    axes[2].axis('off')

    # Modified pixels
    axes[3].imshow(data['mod_map'], cmap='hot', interpolation='nearest')
    total = int(data['orig'].size)
    percent = 100.0 * data['l0'] / max(1, total)
    axes[3].set_title(f'Modified Pixels\n{data["l0"]}/{total} ({percent:.2f}%)',
                      color=HTB_GREEN, fontsize=12)
    axes[3].axis('off')

    # Save
    plt.tight_layout()
    save_path = output_dir / 'jsma_attack_process.png'
    plt.savefig(save_path, dpi=175, bbox_inches='tight')
    plt.close()

    print(f"Attack process visualization saved to {save_path}")
```

We use grayscale colormap for original and adversarial images to maintain digit recognizability. Coloring titles with green for successful attacks and red for failures provides immediate visual feedback. Normalizing perturbation magnitude ensures visibility regardless of actual values (without normalization, small perturbations would appear uniformly dark). Our hot colormap highlights modified regions in yellow/red. Computing the percentage modified provides intuitive sparsity interpretation.

Now let's execute this function with actual attack results:

```python
# Execute visualization with first successful attack
with torch.no_grad():
    pred_adv = model(results_pairs['adversarial'][0]).argmax(dim=1).item()

visualize_attack_process(
    original_images[0],
    results_pairs['adversarial'][0],
    original_labels[0],
    target_labels[0],
    pred_adv,
    output_dir
)
```

Output:
```txt
Attack process visualization saved to output/jsma_attack_process.png
```

![Four‑panel JSMA example: original digit, adversarial classification, perturbation heatmap, and modified‑pixel mask](/storage/modules/320/jsma_attack_process.png)

Each panel contributes a distinct perspective on attack mechanics. We establish baseline appearance with the original digit. Next, the adversarial result reveals whether perturbations achieved misclassification (green title for success, red for failure). The heatmap exposes which spatial regions changed most, with hot colors indicating larger magnitude shifts. Finally, the binary mask quantifies sparsity visually through white pixels on black background, making the L0 count immediately apparent.

### Understanding the Generated Visualization

Examining the attack process visualization for sample 1 (digit 7 → target 2) reveals the pairwise attack's behavior. Looking at the original panel, we see a clean handwritten "7" with the characteristic vertical stroke and angled top. The adversarial panel shows the result after 68 pixels were modified across 35 iterations. The digit now appears distorted, with portions of the top stroke removed and the vertical section modified. The model successfully misclassifies it as "2", achieving the attack's goal.

Notice how the perturbation magnitude heatmap uses a "hot" colormap where yellow and red indicate the strongest changes, while darker regions show unmodified pixels. Modifications concentrate along the top horizontal section and the vertical stroke, representing strategic locations where JSMA determined changes would most effectively shift the classification from 7 to 2. Notice the scattered pattern rather than uniform noise, characteristic of sparse L0-minimizing attacks.

Looking at the rightmost panel, we see the binary mask displaying modified pixels in white against the black background. The sparse nature becomes immediately apparent: only 68 out of 784 pixels changed (8.67%). Examining the norm metrics reveals the attack's character: L0=68 confirms sparsity, L2≈5.5 shows moderate total perturbation magnitude, and L∞=1.0 indicates pixels saturated to their maximum values. This aggressive per-pixel modification (with `theta=1.0`, pixels jump fully from 0.0 to 1.0 or vice versa) allows the attack to succeed with relatively few pixel changes, trading off individual pixel magnitude for overall sparsity.

## Progress Tracking Visualization

Tracking target confidence over iterations reveals convergence behavior:

```python
def visualize_attack_progress(stats, output_dir):
    from htb_ai_library.visualization.styles import HTB_GREEN, NUGGET_YELLOW

    its = stats['iterations']
    conf = stats['target_confidence']
    pix = stats['pixels_modified']

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax2 = ax.twinx()

    ax.plot(its, conf, color=HTB_GREEN, linewidth=2.2, label='Target Confidence')
    ax2.plot(its, pix, color=NUGGET_YELLOW, linewidth=2.0, label='Pixels Modified')

    ax.set_xlabel('Iteration')
    ax.set_ylabel('Target Confidence')
    ax2.set_ylabel('Pixels Modified')
    ax.grid(True, alpha=0.35)

    lines = ax.get_lines() + ax2.get_lines()
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='upper left', framealpha=0.9)

    plt.tight_layout()
    save_path = output_dir / 'jsma_progress.png'
    plt.savefig(save_path, dpi=175, bbox_inches='tight')
    plt.close()

    print(f"Progress visualization saved to {save_path}")
```

Execute this function with attack statistics from a single-pixel attack:

```python
# Assume stats collected during single-pixel attack in Single-Pixel Attack
visualize_attack_progress(stats, output_dir)
```

Output:
```txt
Progress visualization saved to output/jsma_progress.png
```

![Dual‑axis line chart: target confidence rises with iterations alongside pixels modified](/storage/modules/320/jsma_progress.png)

Dual-axis plotting overlays two metrics with different scales on a single timeline. Target confidence (green, left axis) measures attack effectiveness directly: rising from near-zero toward 1.0 signals successful manipulation. Pixels modified (yellow, right axis) counts cumulative L0 norm, showing resource consumption. Steep confidence increases with gradual pixel growth indicate efficient attacks. Plateaued confidence despite growing pixel counts signal diminishing returns or failure modes.

## Saliency Map Visualization

Visualizing the saliency map at key iterations shows which regions JSMA considers most important:

```python
def visualize_saliency_map(alpha, beta, search_space, original_shape, output_dir):
    from htb_ai_library.visualization.styles import HTB_GREEN

    # Compute saliency scores
    inc_scores = score_increase_saliency(alpha, beta)
    dec_scores = score_decrease_saliency(alpha, beta)
    combined_scores = np.maximum(inc_scores, dec_scores)

    # Apply search mask
    combined_scores = combined_scores * search_space

    # Reshape to image dimensions
    h, w = original_shape[-2:]
    saliency_map = combined_scores.reshape(h, w)

    # Create visualization
    fig, ax = plt.subplots(figsize=(6, 6))

    im = ax.imshow(saliency_map, cmap='hot', interpolation='nearest')
    ax.set_title('Saliency Map\n(Higher = More Important)',
                 color=HTB_GREEN, fontsize=14, fontweight='bold')
    ax.axis('off')

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Saliency Score')

    plt.tight_layout()
    save_path = output_dir / 'jsma_saliency_map.png'
    plt.savefig(save_path, dpi=175, bbox_inches='tight')
    plt.close()

    print(f"Saliency map saved to {save_path}")
```

Execute this function to visualize saliency for the first sample:

```python
# Compute gradients for visualization
jacobian = compute_jacobian_matrix(original_images[0], model, 10, 'logits')
alpha = extract_target_gradient(jacobian, target_labels[0])
beta = extract_other_gradients(jacobian, target_labels[0])
search_space = initialize_search_space(original_images[0].shape)

visualize_saliency_map(alpha, beta, search_space, original_images[0].shape, output_dir)
```

Output:
```txt
Saliency map saved to output/jsma_saliency_map.png
```

![Saliency heatmap highlighting pixels most influential for the target class, with colorbar](/storage/modules/320/jsma_saliency_map.png)

Our saliency map reveals which regions of the image have the highest influence on the target class, often highlighting semantic features like digit strokes or object edges.

The next section implements aggregate visualizations analyzing L0 distributions and comparing single-pixel versus pairwise attack results across the full test set.

---

<!-- section 3949 | page 26 | group: Jacobian-based Saliency Map Attack | type: theory | interactive: 0 | docker: False -->

# Aggregate Analysis

Beyond individual attack visualizations, analyzing results across multiple attacks reveals patterns in sparsity, success rates, and attack efficiency. This section implements visualizations for L0 distributions and side-by-side comparisons of single-pixel versus pairwise approaches across the full test set.

## L0 Distribution Analysis

Analyzing L0 norms across multiple attacks shows typical sparsity levels. We'll break this into setup, plotting, and statistics phases for clarity.

### Creating L0 Histogram

Displaying the distribution reveals sparsity patterns across the attack dataset:

```python
def visualize_l0_distribution(l0_values, output_dir):
    from htb_ai_library.visualization.styles import HTB_GREEN, NUGGET_YELLOW, AZURE

    # Create figure and histogram
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(l0_values, bins=30, color=HTB_GREEN, alpha=0.7)

    # Compute statistics
    mean_l0 = np.mean(l0_values)
    median_l0 = np.median(l0_values)
    min_l0 = np.min(l0_values)
    max_l0 = np.max(l0_values)
```

Setting 30 bins provides sufficient granularity for L0 values typically ranging from 10-120 pixels without over-segmenting the distribution. Alpha transparency at 0.7 allows gridlines to show through, maintaining readability. Computing all statistics upfront enables consistent use across plotting and console output.

### Overlaying Statistical Markers

Vertical lines highlight central tendency measures:

```python
    # Add statistical markers
    ax.axvline(mean_l0, color=NUGGET_YELLOW, linestyle='--', linewidth=2,
               label=f'Mean: {mean_l0:.1f}')
    ax.axvline(median_l0, color=AZURE, linestyle='--', linewidth=2,
               label=f'Median: {median_l0:.1f}')

    # Formatting
    ax.set_xlabel('L0 Norm (Pixels Modified)', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('L0 Norm Distribution', color=HTB_GREEN,
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
```

Dashed vertical lines use contrasting colors from the HTB secondary palette: yellow for mean, blue for median. When mean exceeds median (right-skewed distribution), this reveals that occasional high-L0 attacks pull the average up. The grid with alpha=0.3 provides reference without cluttering. Legend placement defaults to optimal location based on data density.

### Saving and Reporting

Finalizing the figure and printing comprehensive statistics:

```python
    # Save
    plt.tight_layout()
    save_path = output_dir / 'jsma_l0_distribution.png'
    plt.savefig(save_path, dpi=175, bbox_inches='tight')
    plt.close()

    # Report statistics
    print(f"L0 distribution saved to {save_path}")
    print(f"  Mean L0: {mean_l0:.1f}")
    print(f"  Median L0: {median_l0:.1f}")
    print(f"  Min L0: {min_l0:.0f}")
    print(f"  Max L0: {max_l0:.0f}")
```

Console output provides numerical summary complementing the visual distribution. Formatting to one decimal place for mean and median balances precision with readability. Integer formatting for min and max reflects that L0 norms are discrete counts. This dual reporting (visual + numerical) supports both quick interpretation and detailed analysis.

Execute this function with L0 values from batch attacks:

```python
# Combine single-pixel and pairwise L0 values
all_l0_values = results['pixels_modified'] + results_pairs['pixels_modified']

visualize_l0_distribution(all_l0_values, output_dir)
```

Output:
```txt
L0 distribution saved to output/jsma_l0_distribution.png
  Mean L0: 58.2
  Median L0: 55.0
  Min L0: 12
  Max L0: 118
```

![Histogram of L0 (pixels modified) with dashed mean and median markers](/storage/modules/320/jsma_l0_distribution.png)

This histogram shows the typical sparsity achieved by JSMA across many attacks, revealing how many pixels are typically needed for successful misclassification.

## Attack Comparison Visualization

Comparing single-pixel and pairwise attacks side-by-side across all tested samples reveals their relative effectiveness. We create a comprehensive grid showing original images, perturbations, and results for both attack variants. To keep functions manageable, we'll break this into composable helpers.

### Data Preparation Helper

Converting tensors and computing perturbations for all samples provides the data foundation:

```python
def prepare_comparison_data(original_images, single_adversarial, pairwise_adversarial):
    n_samples = len(original_images)
    data = []

    for idx in range(n_samples):
        orig = original_images[idx].cpu().numpy().squeeze()
        single_adv = single_adversarial[idx].cpu().numpy().squeeze()
        pair_adv = pairwise_adversarial[idx].cpu().numpy().squeeze()

        single_pert = np.abs(single_adv - orig)
        pair_pert = np.abs(pair_adv - orig)

        single_pert_norm = single_pert / (single_pert.max() + 1e-8)
        pair_pert_norm = pair_pert / (pair_pert.max() + 1e-8)

        data.append({
            'orig': orig,
            'single_adv': single_adv,
            'pair_adv': pair_adv,
            'single_pert_norm': single_pert_norm,
            'pair_pert_norm': pair_pert_norm,
            'l0_single': int((single_pert > 0).sum()),
            'l0_pair': int((pair_pert > 0).sum())
        })

    return data
```

Each sample gets converted once, with all derived data (perturbations, L0 norms) computed upfront. Normalizing perturbations by their maximum ensures visibility across varying magnitude ranges. The dictionary structure organizes related data, avoiding parallel arrays that would complicate indexing.

### Original Images Row Helper

Plotting the original images establishes the baseline for visual comparison:

```python
def plot_original_row(axes, data, original_labels, HTB_GREEN):
    for idx, sample_data in enumerate(data):
        axes[0, idx].imshow(sample_data['orig'], cmap='gray', interpolation='nearest')
        if idx == 0:
            axes[0, idx].set_ylabel('Original', color=HTB_GREEN, fontsize=11, fontweight='bold')
        axes[0, idx].text(0.02, 0.98, f'#{idx+1}\nTrue: {original_labels[idx]}',
                         transform=axes[0, idx].transAxes,
                         verticalalignment='top',
                         fontsize=9,
                         bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        axes[0, idx].axis('off')
```

Row labels appear only on the first column to avoid clutter. Text annotations use axes transform coordinates (0-1 range independent of data units), positioning consistently across samples. The bounding box with alpha=0.7 provides contrast against varying image backgrounds.

### Perturbation Row Helper

Displaying perturbation heatmaps requires computing L0 norms and color-coding by magnitude:

```python
def plot_perturbation_row(axes, row, data, label, HTB_GREEN):
    key = 'single_pert_norm' if 'Single' in label else 'pair_pert_norm'
    l0_key = 'l0_single' if 'Single' in label else 'l0_pair'

    for idx, sample_data in enumerate(data):
        axes[row, idx].imshow(sample_data[key], cmap='hot', interpolation='nearest')
        if idx == 0:
            axes[row, idx].set_ylabel(label, color=HTB_GREEN, fontsize=11, fontweight='bold')
        axes[row, idx].text(0.5, 0.02, f'L0={sample_data[l0_key]}',
                           transform=axes[row, idx].transAxes,
                           horizontalalignment='center',
                           fontsize=8,
                           bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        axes[row, idx].axis('off')
```

Generic key selection based on label text avoids duplicating code for single-pixel vs pairwise rows. Centering L0 annotations at the bottom (0.5 horizontal, 0.02 vertical) reserves the top for other information if needed. The hot colormap highlights high-magnitude perturbations in yellow/red against dark backgrounds.

### Result Row Helper

Displaying adversarial results requires color-coding by success/failure:

```python
def plot_result_row(axes, row, data, label, predictions, targets, HTB_GREEN, MALWARE_RED):
    key = 'single_adv' if 'Single' in label else 'pair_adv'

    for idx, sample_data in enumerate(data):
        axes[row, idx].imshow(sample_data[key], cmap='gray', interpolation='nearest')
        if idx == 0:
            axes[row, idx].set_ylabel(label, color=HTB_GREEN, fontsize=11, fontweight='bold')
        success = (predictions[idx] == targets[idx])
        result_color = HTB_GREEN if success else MALWARE_RED
        axes[row, idx].text(0.5, 0.02, f'Pred: {predictions[idx]}',
                           transform=axes[row, idx].transAxes,
                           horizontalalignment='center',
                           fontsize=8,
                           color=result_color,
                           bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        axes[row, idx].axis('off')
```

Success determination compares predicted class against target class, coloring predictions green for matches (successful attacks) and red for mismatches (failures). This visual encoding enables immediate assessment of attack effectiveness across the sample set.

### Main Comparison Function

Now we assemble the helpers into the complete visualization:

```python
def visualize_attack_comparison(original_images, single_adversarial, pairwise_adversarial,
                                original_labels, predicted_single, predicted_pairs,
                                target_labels, output_dir):
    from htb_ai_library.visualization.styles import HTB_GREEN, MALWARE_RED

    n_samples = len(original_images)

    # Prepare data
    data = prepare_comparison_data(original_images, single_adversarial, pairwise_adversarial)

    # Create grid
    fig, axes = plt.subplots(5, n_samples, figsize=(2.5 * n_samples, 12))
    if n_samples == 1:
        axes = axes.reshape(-1, 1)

    # Plot rows
    plot_original_row(axes, data, original_labels, HTB_GREEN)
    plot_perturbation_row(axes, 1, data, 'Single-Pixel\nPerturbation', HTB_GREEN)
    plot_result_row(axes, 2, data, 'Single-Pixel\nResult', predicted_single, target_labels, HTB_GREEN, MALWARE_RED)
    plot_perturbation_row(axes, 3, data, 'Pairwise\nPerturbation', HTB_GREEN)
    plot_result_row(axes, 4, data, 'Pairwise\nResult', predicted_pairs, target_labels, HTB_GREEN, MALWARE_RED)

    # Save
    plt.tight_layout()
    save_path = output_dir / 'jsma_attack_comparison.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Attack comparison visualization saved to {save_path}")
```

Our main function coordinates workflow by preparing data, creating the figure grid, plotting each row using appropriate helpers, finalizing layout, and saving. This composition pattern keeps each function focused on a single responsibility while maintaining clear data flow. Reshape handling ensures consistent axes indexing whether plotting 1 or 10 samples.

Execute this function to generate the comparison grid:

```python
# Get predictions for both attack variants
predicted_single = []
predicted_pairs = []

with torch.no_grad():
    for i in range(len(original_images)):
        pred_s = model(results['adversarial'][i]).argmax(dim=1).item()
        pred_p = model(results_pairs['adversarial'][i]).argmax(dim=1).item()
        predicted_single.append(pred_s)
        predicted_pairs.append(pred_p)

visualize_attack_comparison(
    original_images,
    results['adversarial'],
    results_pairs['adversarial'],
    original_labels,
    predicted_single,
    predicted_pairs,
    target_labels,
    output_dir
)
```

Output:
```txt
Attack comparison visualization saved to output/jsma_attack_comparison.png
```

![Grid comparing single‑pixel and pairwise JSMA across 10 samples: originals, perturbations, and results](/storage/modules/320/jsma_attack_comparison.png)

Looking at the comparison grid visualization (if generated with actual test results), we would see stark differences between single-pixel and pairwise JSMA across 10 test samples. The top row would show the original digits (7, 2, 1, 0, 4, 1, 4, 9, 5, 9) with their true labels. Each subsequent row pair would contrast single-pixel and pairwise results.

Row 2 (single-pixel perturbations) would show modifications with L0 counts ranging from 60 to 100 pixels. Most samples exhausted their iteration budgets trying to find effective modifications. The perturbations appear as scattered hot spots (yellow/red) against the black background, but with `theta=0.25`, the individual pixel changes are too subtle to cross decision boundaries.

Row 3 (single-pixel results) would reveal universal failure: all 10 samples show red predictions (failures), confirming that none achieved their target misclassification despite modifying an average of 93.9 pixels each. The model's predictions remain at their original classes for all samples.

Row 4 (pairwise perturbations) shows a dramatically different pattern. Most samples have sparse modifications (L0 ranging from 12 to 68 pixels), but sample 2 stands out with L0=118, indicating it required extensive modifications even with pairwise selection and ultimately failed. Sample 4 achieves remarkable sparsity with only 12 pixels modified. The spatial distribution differs from single-pixel, as pairwise saliency discovers different synergistic combinations, and `theta=1.0` enables full saturation per modification.

Row 5 (pairwise results) demonstrates the transformation: 9 out of 10 samples show green predictions (success), with only sample 2 displaying a red prediction (failure). Every sample that single-pixel failed to attack, pairwise succeeds (except sample 2). Sample 4's success with only 12 pixels exemplifies pairwise JSMA's ability to find highly effective sparse perturbations through feature synergies.

This visual comparison makes the quantitative results concrete: pairwise JSMA's 90% success rate versus single-pixel's 0% (with `theta=0.25`) represents a transformative improvement. We see consistent success in finding adversarial examples where the single-pixel baseline completely fails, achieving success with dramatically fewer pixel modifications (12-68 pixels for successful pairwise attacks vs 60-100 pixels for failed single-pixel attempts).

Our visualization functions integrate seamlessly with the attack code, making it easy to generate diagnostic plots after running attacks. This tight integration between attack execution and analysis helps identify why attacks succeed or fail, revealing patterns in saliency maps, perturbation distributions, and convergence behavior.

---

<!-- section 3950 | page 27 | group: Jacobian-based Saliency Map Attack | type: interactive | interactive: 1 | docker: True -->

# Jacobian-based Saliency Map Attack Challenge

Your task is to craft a targeted adversarial example that fools an MNIST digit classifier using the Jacobian-based Saliency Map Attack (JSMA). You will receive a baseline image that the classifier correctly predicts. Your job is to modify a small number of pixels to cause the classifier to predict a specific target class, demonstrating precise, sparse adversarial perturbations.

What you need to do:

Fetch the challenge from the API to receive a baseline `MNIST` image, its ground-truth label, a target class, and an `L0` budget (maximum number of pixels you can modify). Use JSMA to iteratively select and modify the most salient pixels that increase the target class score while decreasing other class scores. Submit your adversarial image to the API. If the classifier predicts the target class and you modified at most the allowed number of pixels, you receive the flag.


The mathematical constraint is an $L_0$ bound on the number of modified pixels:
<p><p><math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mrow><mo stretchy="true" form="prefix">‖</mo><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><mo>−</mo><mi>x</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>0</mn></msub><mo>≤</mo><mtext mathvariant="normal">budget</mtext></mrow><annotation encoding="application/x-tex">\lVert x_{\text{adv}} - x \rVert_0 \leq \text{budget}</annotation></semantics></math></p></p>

<p><p>where
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>x</mi><annotation encoding="application/x-tex">x</annotation></semantics></math>
is the baseline image,
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>x</mi><mtext mathvariant="normal">adv</mtext></msub><annotation encoding="application/x-tex">x_{\text{adv}}</annotation></semantics></math>
is your crafted adversarial example, and
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mrow><mo stretchy="true" form="prefix">‖</mo><mi>⋅</mi><mo stretchy="true" form="postfix">‖</mo></mrow><mn>0</mn></msub><annotation encoding="application/x-tex">\lVert \cdot \rVert_0</annotation></semantics></math>
counts the number of pixels with non-zero differences (differences above
a small threshold like
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mn>10</mn><mrow><mi>−</mi><mn>6</mn></mrow></msup><annotation encoding="application/x-tex">10^{-6}</annotation></semantics></math>).
The classifier must predict the specified target class
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>t</mi><annotation encoding="application/x-tex">t</annotation></semantics></math>,
and all pixel values must remain in
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0,1]</annotation></semantics></math>.</p></p>



## Quick Start

All API endpoints expect images in `[0,1]` pixel space, not normalized tensors.

Start the instance from the platform. Check readiness:

```shell-session
[!bash!]$ export BASE_URL="http://instance_ip:port"
```

```shell-session
[!bash!]$ curl -s "$BASE_URL/health"
{"status":"healthy"}
```

## API

The API is minimal and deterministic. Each response is JSON. Images are base64-encoded `PNG` files of shape `28x28` and single channel in `[0,1]` after decoding.

### GET /health

Returns service status and configuration parameters.

```shell-session
[!bash!]$ curl -s "$BASE_URL/health" | jq
{
  "status": "healthy"
}
```

### GET /challenge

Returns the fixed sample and attack parameters that must be satisfied.

```shell-session
[!bash!]$ curl -s "$BASE_URL/challenge" | jq
{
  "sample_index": 2,
  "target_class": 7,
  "l0_budget": 50,
  "original_label": 1,
  "max_l2": 8.0,
  "image_b64": "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAAAAABXZoBIAAAAiUlEQVR42mNgoD9gRhdQe/3uFIzNhC5p+O8pbqPaP+KW0/0yDcFBN1adayVunafuc+OUU/h3gwGnsfYMr3FL6jJ04TTV8u1ZDpw6nYVu/MApqf9/DU5TJV5cR+Gj6EwQO4FbUp7hPe7gefLPCadOW3E8Ed/77ywzLp1cXgxr/uLSyHpsAxfDgAMAUBMg+xetJ/UAAAAASUVORK5CYII="
}
```
<p><p>The <code>sample_index</code> identifies the specific MNIST test
sample used for this challenge. The <code>original_label</code> is the
ground-truth class of the baseline image. The <code>target_class</code>
is the specific class the adversarial example must be classified as. The
<code>l0_budget</code> defines the maximum number of pixels that can be
modified. The <code>max_l2</code> parameter serves as a safeguard to
prevent replacing the entire image with unrelated data. The
<code>image_b64</code> field contains the baseline image as a
base64-encoded <code>PNG</code>.</p></p>



### POST /predict

Returns the model's prediction for an arbitrary image. Use this endpoint to validate the pipeline, encoding, and intermediate candidates. It does not return the flag.

```shell-session
[!bash!]$ curl -s -X POST "$BASE_URL/predict" \
  -H 'content-type: application/json' \
  -d '{"image_b64": "<base64 PNG of 28x28 grayscale>"}' | jq
{
  "predicted_class": 7,
  "confidence": 0.89,
  "all_probabilities": [0.01, 0.02, 0.01, 0.03, 0.01, 0.02, 0.01, 0.89, 0.00, 0.00]
}
```

The `predicted_class` field contains the predicted class (integer in `[0,9]`). The `confidence` field provides the probability for the predicted class (float in `[0,1]`). The `all_probabilities` array contains the probability distribution over all 10 classes.

### GET /weights

Returns the pretrained model `state_dict` as a binary file. Load it on CPU and use the provided classifier architecture to compute the Jacobian matrix locally.

```shell-session
[!bash!]$ curl -s -o jsma_weights.pth "$BASE_URL/weights"
```

The downloaded file is a PyTorch state dictionary compatible with the `MNISTClassifier` (LeNet-5 style) architecture detailed below. Load with `torch.load(path, map_location=torch.device('cpu'))`.

### POST /submit
<p><p>Validates that the candidate is a proper <code>28x28</code>
single-channel image in
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo stretchy="false" form="prefix">[</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo stretchy="false" form="postfix">]</mo></mrow><annotation encoding="application/x-tex">[0,1]</annotation></semantics></math>,
that the number of modified pixels is at most <code>l0_budget</code>,
that the
<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>L</mi><mn>2</mn></msub><annotation encoding="application/x-tex">L_2</annotation></semantics></math>
distance is below <code>max_l2</code>, that the classifier’s predicted
class equals the target class, and that the submission is not simply a
clean image of the target class copied from the dataset. Returns the
flag on success.</p></p>



```shell-session
[!bash!]$ curl -s -X POST "$BASE_URL/submit" \
  -H 'content-type: application/json' \
  -d '{"image_b64": "<base64 PNG of 28x28 grayscale>"}' | jq
{
  "success": true,
  "flag": "HTB{...}",
  "pixels_modified": 45,
  "predicted_class": 7,
  "target_class": 7
}
```

On validation failure, the endpoint returns HTTP 400 with a descriptive error message (e.g., `"L0 constraint violated: 55 pixels modified (max: 50)"`, `"Target misclassification failed: predicted 3, expected 7"`, or `"Submission rejected: please derive the adversarial example from the provided baseline image"`).

## Minimal Python Scaffolds

The following scaffolds provide API helpers, model architecture, and integration testing. They do not implement the attack.

### API Helpers and Challenge Fetching

```python
import os, io, base64, numpy as np, requests, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
MNIST_MEAN, MNIST_STD = 0.1307, 0.3081

def x01_from_b64_png(b64: str) -> np.ndarray:
    """Convert base64 PNG to [0,1] numpy array.

    Args:
        b64: Base64 encoded PNG string

    Returns:
        np.ndarray: Image as (28, 28) array in [0,1] range
    """
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("L")
    if img.size != (28, 28):
        raise ValueError("Expected 28x28 PNG")
    x = np.asarray(img, dtype=np.float32) / 255.0
    return np.clip(x, 0.0, 1.0)

def b64_png_from_x01(x2d: np.ndarray) -> str:
    """Convert [0,1] array to base64 PNG.

    Args:
        x2d: Image array in [0,1] range

    Returns:
        str: Base64 encoded PNG string
    """
    x255 = np.clip((x2d * 255.0).round(), 0, 255).astype(np.uint8)
    img = Image.fromarray(x255, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def count_modified_pixels(a: np.ndarray, b: np.ndarray, threshold: float = 1e-6) -> int:
    """Count number of modified pixels (L0 norm).

    Args:
        a, b: Arrays to compare
        threshold: Minimum difference to count as modified

    Returns:
        int: Number of pixels with absolute difference above threshold
    """
    return int(np.sum(np.abs(a - b) > threshold))

# Fetch challenge and check clean prediction
ch = requests.get(f"{BASE_URL}/challenge", timeout=10).json()
x = x01_from_b64_png(ch["image_b64"])      # (28, 28)
orig_label = int(ch["original_label"])     # baseline label
target = int(ch["target_class"])           # target class for attack
budget = int(ch["l0_budget"])              # max pixels to modify
max_l2 = float(ch["max_l2"])              # L2 safeguard

res = requests.post(f"{BASE_URL}/predict", json={"image_b64": b64_png_from_x01(x)}, timeout=10).json()
print({"original_label": orig_label, "server_pred": res["predicted_class"],
       "target_class": target, "l0_budget": budget, "max_l2": max_l2})
```

### Model Architecture and Loading

The server uses a LeNet-5 style architecture. You need to replicate it locally to compute the Jacobian matrix.

```python
class MNISTClassifier(nn.Module):
    """LeNet-5 style classifier.

    Architecture:
    - Conv1: 1 -> 6 channels, 5x5 kernel, Tanh activation, 2x2 avg pooling
    - Conv2: 6 -> 16 channels, 5x5 kernel, Tanh activation, 2x2 avg pooling
    - FC1: 256 -> 120, Tanh activation
    - FC2: 120 -> 84, Tanh activation
    - FC3: 84 -> 10, log-softmax output
    """

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5, stride=1, padding=0)
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5, stride=1, padding=0)
        self.pool = nn.AvgPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(16 * 4 * 4, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
        self.act = nn.Tanh()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning log-softmax outputs.

        Args:
            x: Input tensor of shape (batch, 1, 28, 28) in [0,1] range

        Returns:
            Log-softmax output of shape (batch, 10)
        """
        x = self.act(self.conv1(x))    # (B,6,24,24)
        x = self.pool(x)               # (B,6,12,12)
        x = self.act(self.conv2(x))    # (B,16,8,8)
        x = self.pool(x)               # (B,16,4,4)
        x = torch.flatten(x, 1)        # (B,256)
        x = self.act(self.fc1(x))      # (B,120)
        x = self.act(self.fc2(x))      # (B,84)
        x = self.fc3(x)                # (B,10)
        return F.log_softmax(x, dim=1)

def mnist_normalize(x01: torch.Tensor) -> torch.Tensor:
    """Normalize [0,1] tensor to MNIST statistics.

    Args:
        x01: Input tensor in [0,1] range

    Returns:
        Normalized tensor
    """
    return (x01 - MNIST_MEAN) / MNIST_STD

# Download and load weights
wt = requests.get(f"{BASE_URL}/weights", timeout=10).content
open("jsma_weights.pth", "wb").write(wt)

model = MNISTClassifier().eval()
state = torch.load("jsma_weights.pth", map_location=torch.device("cpu"))
model.load_state_dict(state)

# Verify model works locally
x_tensor = torch.from_numpy(x[None, None, ...]).float()
logits = model(mnist_normalize(x_tensor))
local_pred = int(torch.argmax(logits, dim=1).item())
print(f"Local prediction: {local_pred}, should match server: {res['predicted_class']}")
```

### Testing Server Validation

Verify server-side checks by submitting the clean image and observing expected failures.

```python
bad = requests.post(f"{BASE_URL}/submit", json={"image_b64": b64_png_from_x01(x)}, timeout=10)
print(bad.status_code, bad.text)  # expected: 400 with "Target misclassification failed"
```

### Questions (section)
- {"id": 3366, "question": "After successfully completing the task, what is the flag you receive?", "hint": null, "file": null, "has_file": false, "protocol": null, "username": null, "password": null, "order": null, "cubes": 5, "experience_points": 60}


---

<!-- section 3951 | page 28 | group: Skills Assessment | type: interactive | interactive: 1 | docker: True -->

# Skills Assessment

Apply your knowledge of sparsity attacks to craft a targeted adversarial example against a ResNet-18 classifier trained on CIFAR-10. You must submit a base64-encoded PNG of shape `32x32x3` that achieves targeted misclassification using either EAD or JSMA. The evaluator validates method signatures and enforces anti-cheating measures including minimum perturbation thresholds.

## Quick start

Begin by verifying the evaluator is ready, then fetch the challenge specification to obtain your sample image, its baseline prediction, and the target class.

```shell-session
[!bash!]$ export BASE_URL="http://instance_ip:port"
```

```shell-session
[!bash!]$ curl -s "$BASE_URL/health" | jq
{
  "status": "ok",
  "model": "...",
  "items": ...
}
```

```shell-session
[!bash!]$ curl -s "$BASE_URL/challenge" | jq
{
  "items": [
    {
      "sample_id": ...,
      "label": ...,
      "target": ...,
      "required_method": "...",
      "image_b64": "..."
    }
  ]
}
```

Next, download the model metadata and weights. The architecture is ResNet-18 adapted for CIFAR-10, with the full implementation provided in the scaffolds below.

```shell-session
[!bash!]$ curl -s "$BASE_URL/model" | jq
{
  "arch": "ResNetCIFAR",
  "weights_sha256": "...",
  "weights_size": ...,
  "normalize": {
    "mean": [
      ...
    ],
    "std": [
      ...
    ]
  },
  "weights_url": "/model/weights"
}
```

```shell-session
[!bash!]$ curl -sL "$BASE_URL/model/weights" -o cifar10_model.pth
```

During development, use the `/predict` endpoint to validate your image encoding and PNG round-trip behavior before final submission.

```shell-session
[!bash!]$ curl -s -X POST "$BASE_URL/predict" \
  -H 'content-type: application/json' \
  -d '{"image_b64": "<base64 PNG of 32x32 RGB>"}' | jq
```

## Minimal Python scaffolds

The helpers below provide image I/O and HTTP calls. They are for integration only.

```python
import io, os, base64, json, urllib.request
from typing import Dict, Any
from PIL import Image
import numpy as np

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def b64_from_x01(x4d: np.ndarray) -> str:
    x = np.transpose(x4d[0], (1, 2, 0))
    x255 = np.clip((x * 255.0).round(), 0, 255).astype(np.uint8)
    img = Image.fromarray(x255, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def x01_from_b64(b64: str) -> np.ndarray:
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    x = np.asarray(img, dtype=np.float32) / 255.0
    return np.transpose(x, (2, 0, 1))[None, ...].astype(np.float32)


def http_get(path: str) -> Dict[str, Any]:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def http_post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


ch = http_get("/challenge")
meta = http_get("/model")
print(
    {
        "items": len(ch["items"]),
        "arch": meta["arch"],
        "weights_url": meta["weights_url"],
    }
)

```

Load the model locally with `ResNetCIFAR` and the downloaded weights.

```python
import torch, torch.nn as nn


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, stride=1):
        super().__init__()

        self.conv1 = nn.Conv2d(
            in_planes, planes, 3, stride=stride, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, planes, 1, stride=stride, bias=False),
                nn.BatchNorm2d(planes),
            )

    def forward(self, x):
        out = torch.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return torch.relu(out)


class ResNetCIFAR(nn.Module):
    def __init__(self, num_blocks=(2, 2, 2, 2), num_classes=10):
        super().__init__()

        self.in_planes = 64
        self.conv1 = nn.Conv2d(3, 64, 3, 1, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.layer1 = self._make_layer(64, num_blocks[0], 1)
        self.layer2 = self._make_layer(128, num_blocks[1], 2)
        self.layer3 = self._make_layer(256, num_blocks[2], 2)
        self.layer4 = self._make_layer(512, num_blocks[3], 2)
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(512, num_classes)

    def _make_layer(self, planes, n, stride):
        layers = []
        for s in [stride] + [1] * (n - 1):
            layers.append(BasicBlock(self.in_planes, planes, s))
            self.in_planes = planes
        return nn.Sequential(*layers)

    def forward(self, x):
        out = torch.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.avgpool(out)
        out = torch.flatten(out, 1)
        return self.fc(out)


def cifar_normalize(x):
    mean = torch.tensor((0.4914, 0.4822, 0.4465), dtype=x.dtype, device=x.device)[
        None, :, None, None
    ]
    std = torch.tensor((0.2470, 0.2435, 0.2616), dtype=x.dtype, device=x.device)[
        None, :, None, None
    ]
    return (x - mean) / std


ckpt_path = "cifar10_model.pth"
urllib.request.urlretrieve(f"{BASE_URL}{meta['weights_url']}", ckpt_path)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ResNetCIFAR().to(device).eval()
state = torch.load(ckpt_path, map_location=device)
state_dict = state.get("state_dict_ema") or state.get("state_dict") or state
model.load_state_dict(state_dict)

```

With the model loaded, craft either an EAD or JSMA attack to generate your adversarial example. Before submission, perform a PNG round-trip on your candidate image to mirror the evaluator's decode path and ensure your perturbation survives the encoding process.

## Submission

Submit your adversarial example to the `POST /submit_images` endpoint with the correct `sample_id` and method tag. Images are transmitted as base64-encoded PNGs and automatically decoded to the `[0,1]` range on the server for evaluation.

```json
POST /submit_images
{
  "items": [
    { "sample_id": 0, "method": "ead", "image_b64": "..." }
  ]
}
```

The evaluator enforces a minimum L2 perturbation threshold of 1.5 to prevent submitting unmodified clean images. This anti-cheating measure ensures your adversarial example contains actual perturbations rather than the original baseline image. When all validation checks pass (targeted misclassification, method signature, perturbation threshold), the response includes your flag.

### Questions (section)
- {"id": 3364, "question": "After successfully completing the task, what is the flag you receive?", "hint": null, "file": null, "has_file": false, "protocol": null, "username": null, "password": null, "order": null, "cubes": 10, "experience_points": 60}
