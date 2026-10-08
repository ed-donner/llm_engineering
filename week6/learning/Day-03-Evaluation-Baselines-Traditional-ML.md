# Day 03 — Evaluation, Baselines & Traditional Machine Learning

> AI Course Capstone: **The Price is Right**

## Introduction

Day 3 focuses on building models that predict a product's price from its description.

Pipeline:

```text
Raw Amazon Data
      │
      ▼
Feature Engineering / Text Vectorization
      │
      ▼
Machine Learning Model
      │
      ▼
Predicted Price
      │
      ▼
Evaluation
```

## 1. Why Evaluate Models?

Training accuracy alone is meaningless if the model cannot generalize.

- **Train**: Learn patterns.
- **Validation**: Compare models and tune.
- **Test**: Final unbiased evaluation.

The notebook uses `evaluate(model, test)` to compare predictions with real prices.

---

# 2. Baseline Models

## Random Pricer

```python
def random_pricer(item):
    return random.randrange(1,1000)
```

Purpose:
- Establish the worst reasonable baseline.
- If your ML model cannot beat random guessing, something is wrong.

## Constant Pricer

Predicts the average training price.

```python
training_average = sum(prices)/len(prices)
```

Purpose:
- Stronger baseline.
- Shows whether learning from features actually helps.

---

# 3. Feature Engineering

A **feature** is information given to the ML model.

Notebook features:

- weight
- weight_unknown
- text_length

Example:

| Weight | Missing? | Length | Price |
|--------:|---------:|-------:|------:|
|2.1|0|120|59.99|

Better features usually improve models more than changing algorithms.

---

# 4. Preparing Data

```python
X_train
y_train
```

`X` = Inputs (features)

`y` = Target (price)

```text
Features ─────► Model ─────► Price
```

---

# 5. Linear Regression

Goal:

Find a straight-line relationship.

Formula:

Price = b0 + b1*x1 + b2*x2 + ...

Where:

- b0 = intercept
- b1,b2 = coefficients

`fit()` learns coefficients.

`predict()` uses them.

## Why "Linear"?

Because each feature contributes linearly.

Example:

Weight coefficient = 8

Every extra kg increases predicted price by about $8.

### Limitations

- Assumes linear relationships.
- Cannot model complex interactions.

---

# 6. Evaluation Metrics

## Mean Squared Error (MSE)

Average squared prediction error.

Lower is better.

## R² Score

Measures how much variance is explained.

1 = perfect

0 = no improvement over average

Negative = worse than predicting the average.

---

# 7. NLP Introduction

ML cannot understand English.

Text must become numbers.

```text
Sentence
   │
   ▼
Numbers
   │
   ▼
Machine Learning
```

---

# 8. CountVectorizer

Purpose:

Convert text into numeric vectors.

Example:

Documents:

- Apple TV
- Samsung TV
- Apple Watch

Vocabulary:

|Index|Word|
|---:|---|
|0|apple|
|1|samsung|
|2|tv|
|3|watch|

Vectors:

Apple TV

```
[1,0,1,0]
```

Samsung TV

```
[0,1,1,0]
```

## Important Parameters

### max_features

Keep only the most frequent words.

### stop_words='english'

Remove common words:

- the
- is
- for
- with

### fit()

Learn vocabulary.

### transform()

Use existing vocabulary on new data.

### fit_transform()

Shortcut:

Learn vocabulary + transform.

⚠ Never call `fit_transform()` on test data.

---

# 9. Text-based Linear Regression

Instead of:

- weight
- length

Features become:

- apple
- laptop
- gaming
- wireless
- tv
- ...

The algorithm remains Linear Regression.

Only the features become richer.

---

# 10. Decision Trees

Decision Trees learn IF-ELSE rules.

Example:

```
IF gaming
    IF laptop
        Price = High
ELSE
    Price = Low
```

Pros:

- Easy to understand
- Handles non-linear data

Cons:

- Easily overfits

---

# 11. Random Forest

Random Forest = Many Decision Trees.

Each tree trains independently.

Prediction:

```
Tree1 → 520
Tree2 → 500
Tree3 → 510

Average = 510
```

Important parameters:

- n_estimators
- random_state
- n_jobs

Advantages:

- Better than a single tree
- Less overfitting
- Handles complex relationships

---

# 12. XGBoost

Boosting instead of Bagging.

Idea:

```
Tree1

↓

Errors

↓

Tree2 fixes errors

↓

Tree3 fixes remaining errors
```

Parameters:

- n_estimators
- learning_rate
- random_state
- n_jobs

Usually stronger than Random Forest on structured data.

---

# 13. Comparison

|Model|Idea|Strength|Weakness|
|---|---|---|---|
|Random|Guess|Baseline|No learning|
|Constant|Average|Simple baseline|Ignores features|
|Linear Regression|Linear equation|Fast, interpretable|Only linear|
|Random Forest|Average many trees|Captures non-linearity|Slower|
|XGBoost|Sequential trees|Very accurate|More tuning|

---

# 14. Common Mistakes

❌ Using `fit_transform()` on test data.

❌ Thinking CountVectorizer understands meaning.

❌ Confusing X and y.

❌ Believing Random Forest averages the data instead of predictions.

---

# 15. Interview Notes

Q. What is Regression?

Predicting continuous values.

Q. Why CountVectorizer?

Converts text into numeric features.

Q. Difference between Random Forest and XGBoost?

Random Forest builds trees independently.

XGBoost builds trees sequentially to correct previous errors.

Q. What is Bagging?

Independent trees + averaging.

Q. What is Boosting?

Sequential trees correcting mistakes.

---

# 16. 10 Things to Remember

1. Regression predicts continuous values.
2. `fit()` learns.
3. `predict()` performs inference.
4. Better features often matter more than better algorithms.
5. ML models need numbers.
6. CountVectorizer counts words.
7. Decision Trees learn IF-ELSE rules.
8. Random Forest = Bagging.
9. XGBoost = Boosting.
10. Evaluate on unseen test data.

---

# Cheat Sheet

```text
Text
 │
 ▼
CountVectorizer
 │
 ▼
Word Vector
 │
 ├── Linear Regression
 ├── Random Forest
 └── XGBoost
 │
 ▼
Predicted Price
 │
 ▼
Evaluate (MSE, R²)
```


# 🏷️ "The Price Is Right" — DAY 3: Evaluation, Baselines & Traditional ML
### LLM Engineering Course — Week 6 Capstone Notes

> **What we're doing today:** Build progressively smarter models to predict Amazon product prices from text descriptions, evaluate them fairly, and understand *why* each works (or doesn't).

---

## 📋 Table of Contents

1. [Real World Context](#real-world-context)
2. [Setup & Imports](#setup--imports)
3. [Why Train/Val/Test Splits?](#why-trainvaltest-splits)
4. [Baseline Model 1 — Random Pricer](#baseline-model-1--random-pricer)
5. [Baseline Model 2 — Constant/Average Pricer](#baseline-model-2--constantaverage-pricer)
6. [Feature Engineering — The Bridge Step](#feature-engineering--the-bridge-step)
7. [Model 3 — Linear Regression (Numeric Features)](#model-3--linear-regression-numeric-features)
8. [Model 4 — NLP + Linear Regression (CountVectorizer)](#model-4--nlp--linear-regression-countvectorizer)
9. [Model 5 — Random Forest](#model-5--random-forest)
10. [Model 6 — XGBoost](#model-6--xgboost)
11. [Summary & Remember This](#summary--remember-this)
12. [Revision Sheet](#revision-sheet)
13. [Common Mistakes](#common-mistakes)
14. [Exercises](#exercises)
15. [Future Connections to LLMs](#future-connections-to-llms)

---

## 🌍 Real World Context

**What problem are we solving?**

Amazon has millions of products. A seller uploads a product description — can a model automatically suggest a fair price?

This is a **regression** problem (predict a number, not a category). Real companies use exactly this:

| Company | Use Case |
|---|---|
| Amazon | Dynamic pricing engine |
| Airbnb | Smart pricing for hosts |
| Uber | Surge pricing prediction |
| Insurance firms | Premium prediction from claim descriptions |

**Why start with Traditional ML before LLMs?**

LLMs are powerful but slow and expensive. Traditional ML models like Linear Regression and Random Forest are:
- Fast to train and deploy
- Interpretable (you can explain *why* they made a prediction)
- Still competitive for well-structured data

A good ML engineer always starts simple and proves the complex approach is worth it.

---

## 🔧 Setup & Imports

```python
import random
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestRegressor
from pricer.evaluator import evaluate
from pricer.items import Item

LITE_MODE = True
```

### What each import does

| Import | Why it's here |
|---|---|
| `random` | For the random baseline pricer |
| `pandas` | Turns list of items into a DataFrame (rows & columns) |
| `numpy` | Numerical operations, random seed control |
| `LinearRegression` | First real ML model |
| `mean_squared_error`, `r2_score` | Evaluation metrics |
| `CountVectorizer` | Converts text descriptions into word-count numbers |
| `RandomForestRegressor` | Ensemble model using decision trees |
| `evaluate` | Custom function to test any pricer uniformly |
| `Item` | Custom class representing a product with price, weight, summary |

### What is `LITE_MODE`?

```python
LITE_MODE = True
dataset = f"{username}/items_lite" if LITE_MODE else f"{username}/items_full"
```

- `LITE_MODE = True` → smaller dataset, faster runs, for experimentation
- `LITE_MODE = False` → full 800k+ item dataset, used for final production training
- **Pattern:** Always prototype on small data, scale up only when the approach works.

---

## 📊 Why Train/Val/Test Splits?

```python
train, val, test = Item.from_hub(dataset)
print(f"Loaded {len(train):,} training items, {len(val):,} validation items, {len(test):,} test items")
```

### The "Exam Analogy"

> Imagine you memorize answers to 100 questions. Then I ask one of those same 100 questions. You'll score 100% — but that doesn't prove you *understand* the subject.

| Split | Purpose | Analogy |
|---|---|---|
| **Train** | Model learns patterns from this | Textbook you study from |
| **Validation** | Tune hyperparameters, compare models | Practice mock tests |
| **Test** | Final, untouched evaluation | The actual final exam |

### Key Rule: Never touch the test set during training

Once you've seen test results, your brain is now "contaminated" — you'll unconsciously make choices that happen to work on the test. This is called **data leakage**, and it's a serious mistake in industry.

---

## 🎲 Baseline Model 1 — Random Pricer

```python
def random_pricer(item):
    return random.randrange(1, 1000)

random.seed(42)
evaluate(random_pricer, test)
```

### Why `random.seed(42)`?

Without a seed, every run gives different results. With `seed(42)`, the "random" sequence is reproducible — you and your teammate get the same numbers.

`42` is a convention — any number works. It refers humorously to "the answer to life, the universe, and everything" from *The Hitchhiker's Guide to the Galaxy*.

### Why build a random model at all?

This sets the **floor** — the absolute worst intelligent baseline. Every future model must beat this. If your fancy model barely beats random, something is deeply wrong.

### Interview Insight 💼

> **Q: What is a baseline model and why do we need one?**
>
> A: A baseline is the simplest possible model that represents "doing nothing smart." It's essential because it defines *what improvement actually means.* Without a baseline, you can't tell if your model is genuinely learning or just getting lucky. In production systems, you always compare against: random baseline → simple heuristic → ML model → deep learning.

---

## 📈 Baseline Model 2 — Constant/Average Pricer

```python
training_prices = [item.price for item in train]
training_average = sum(training_prices) / len(training_prices)
print(training_average)

def constant_pricer(item):
    return training_average

evaluate(constant_pricer, test)
```

### Why predict the average?

If you know nothing about a specific product, the **expected value** (average) is statistically the safest single guess — it minimizes squared error across all predictions.

### The Key ML Concept

> When we later train Linear Regression, Random Forest, and XGBoost, we're asking: *Can this model do better than simply predicting the average price for everything?*
>
> If not, the model hasn't learned anything useful.

This is actually formalized in the **R² score** metric:
- R² = 0 means the model is as good as just predicting the average
- R² = 1 means perfect predictions
- R² < 0 means the model is *worse* than predicting the average (a red flag!)

---

## 🔨 Feature Engineering — The Bridge Step

```python
def get_features(item):
    return {
        "weight": item.weight,
        "weight_unknown": 1 if item.weight == 0 else 0,
        "text_length": len(item.summary)
    }
```

### What is Feature Engineering?

Feature engineering is the process of converting raw data into numbers that a model can understand.

Before this step:
```
Item Object
  → summary: "Apple iPhone 15 Pro 256GB..."
  → weight: 0.174
  → price: 999
```

After this step:
```
weight | weight_unknown | text_length | price
0.174  |       0        |     180     |  999
```

### Why these three features?

| Feature | Hypothesis |
|---|---|
| `weight` | Heavier items (TVs, furniture) tend to cost more |
| `weight_unknown` | If weight is 0, it might be missing data — a signal itself |
| `text_length` | Longer descriptions may indicate more complex/expensive items |

### Converting to a DataFrame

```python
def list_to_dataframe(items):
    features = [get_features(item) for item in items]
    df = pd.DataFrame(features)
    df['price'] = [item.price for item in items]
    return df

train_df = list_to_dataframe(train)
test_df = list_to_dataframe(test)
```

**Visual:**
```
weight | weight_unknown | text_length | price
------------------------------------------------
0.02   | 0              | 80          | 5
2.10   | 0              | 120         | 1200
15.00  | 0              | 200         | 700
0.00   | 1              | 45          | 12
```

**Important limitation:** This DataFrame has lost almost all product description information. The model doesn't know if it's an iPhone or a plastic spoon — only how heavy it is and how long the description is. That's why this model won't be very accurate. We fix this next with CountVectorizer.

---

## 📐 Model 3 — Linear Regression (Numeric Features)

```python
np.random.seed(42)

feature_columns = ['weight', 'weight_unknown', 'text_length']

X_train = train_df[feature_columns]
y_train = train_df['price']
X_test = test_df[feature_columns]
y_test = test_df['price']

model = LinearRegression()
model.fit(X_train, y_train)

for feature, coef in zip(feature_columns, model.coef_):
    print(f"{feature}: {coef}")
print(f"Intercept: {model.intercept_}")

y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse}")
print(f"R-squared Score: {r2}")
```

### How Linear Regression Works

Linear Regression finds a line (or plane in multiple dimensions) that best fits the data:

```
Price = (weight × W₁) + (weight_unknown × W₂) + (text_length × W₃) + intercept
```

The `model.fit()` call finds the best values for W₁, W₂, W₃, and intercept.

### Reading the Coefficients

```python
for feature, coef in zip(feature_columns, model.coef_):
    print(f"{feature}: {coef}")
```

This prints something like:
```
weight: 12.4
weight_unknown: -30.2
text_length: 0.8
Intercept: 45.0
```

Interpretation:
- Every 1 kg increase in weight → price increases by $12.40
- If weight is unknown → price decreases by $30.20 (suspicious products?)
- Every extra character in description → price increases by $0.80

### Why is this useful?

Unlike deep learning, Linear Regression is **fully interpretable** — you can literally explain why it made a prediction. This matters hugely in finance, healthcare, and legal contexts where "the model said so" isn't good enough.

### Wrapping into a pricer function

```python
def linear_regression_pricer(item):
    features = get_features(item)
    features_df = pd.DataFrame([features])
    return model.predict(features_df)[0]

evaluate(linear_regression_pricer, test)
```

This wraps the trained model in the same interface as all other pricers — good software design that allows apples-to-apples comparison via the same `evaluate()` function.

### Interview Insight 💼

> **Q: What are the assumptions of Linear Regression?**
>
> 1. Linear relationship between features and target
> 2. Features are independent of each other (no multicollinearity)
> 3. Errors are normally distributed
> 4. Constant variance of errors (homoscedasticity)
>
> For product pricing, these assumptions are often violated — prices are skewed, features correlate — which is why more powerful models usually do better here.

---

## 🗣️ Model 4 — NLP + Linear Regression (CountVectorizer)

```python
prices = np.array([float(item.price) for item in train])
documents = [item.summary for item in train]

np.random.seed(42)
vectorizer = CountVectorizer(max_features=2000, stop_words='english')
X = vectorizer.fit_transform(documents)

selected_words = vectorizer.get_feature_names_out()
print(f"Number of selected words: {len(selected_words)}")
print("Selected words:", selected_words[1000:1020])

regressor = LinearRegression()
regressor.fit(X, prices)
```

### What is CountVectorizer?

CountVectorizer converts text into a **Bag of Words** — a matrix where:
- Each row = one product description
- Each column = one word from the vocabulary
- Each cell = how many times that word appears

```
          "iphone" "samsung" "spoon" "gaming" "tv"  ...
Product 1:    2        0        0       0       0
Product 2:    0        1        0       0       1
Product 3:    0        0        3       0       0
Product 4:    0        0        0       2       0
```

### Parameters explained

| Parameter | Value | Meaning |
|---|---|---|
| `max_features` | 2000 | Keep only the 2000 most frequent words |
| `stop_words='english'` | — | Remove common words like "the", "is", "a" (they don't carry pricing info) |

### How the model now reasons

With CountVectorizer feeding Linear Regression, it learns:

```
"iphone" appears → price likely higher
"gaming" appears → price likely higher  
"spoon" appears → price likely very low
"samsung" appears → moderate boost
```

This is far more powerful than just knowing weight and text length!

### Making predictions

```python
def natural_language_linear_regression_pricer(item):
    x = vectorizer.transform([item.summary])
    return max(regressor.predict(x)[0], 0)
```

Note the `max(..., 0)` — prices can't be negative. This guards against the model predicting a negative number (which Linear Regression can do mathematically).

### Interview Insight 💼

> **Q: What are the limitations of Bag of Words / CountVectorizer?**
>
> 1. **No word order** — "dog bites man" and "man bites dog" are identical
> 2. **No semantics** — "iPhone" and "smartphone" are treated as completely different
> 3. **Sparse matrix** — most cells are 0, wasteful for memory
> 4. **Vocabulary is fixed at training time** — new words at test time are ignored
>
> This is exactly why we eventually move to LLMs — they understand context and meaning.

---

## 🌲 Model 5 — Random Forest

```python
subset = 15_000
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=4)
rf_model.fit(X[:subset], prices[:subset])

def random_forest(item):
    x = vectorizer.transform([item.summary])
    return max(0, rf_model.predict(x)[0])

evaluate(random_forest, test)
```

### What is a Decision Tree?

A Decision Tree makes predictions by asking a series of yes/no questions about the features:

```
IF "gaming" appears > 1 time
  → IF "laptop" appears ≥ 1 time
      → IF "rtx" appears ≥ 1 time
          → Price = $1,800
      → ELSE
          → Price = $900
  → ELSE
      → Price = $300
ELSE
  → ...
```

Decision trees are fast and interpretable, but they **overfit** — they memorize the training data too closely.

### What is Random Forest?

Random Forest is an **ensemble** method — it builds 100 different decision trees, each trained on:
- A **random subset** of the training data (row sampling)
- A **random subset** of the features (column sampling)

Then it averages all 100 predictions.

```
Tree 1 prediction: $450
Tree 2 prediction: $520
Tree 3 prediction: $480
...
Tree 100 prediction: $490
→ Final prediction: average = $488
```

### Why does this work better?

Each tree makes different errors (because it saw different data and features). When you average them, the errors cancel out. This is called the **wisdom of crowds** principle.

### Why only `subset = 15_000`?

Random Forest is memory-intensive with a sparse CountVectorizer matrix. Using 15,000 items keeps training fast while still learning meaningful patterns. Full training (800k items) took ~15 hours but achieved $56.40 error.

### Interview Insight 💼

> **Q: What is the difference between bagging and boosting?**
>
> - **Bagging (Random Forest):** Trees are built independently, in parallel. Each tree is trained on a random subset of data. Final answer = average of all trees. Reduces variance.
> - **Boosting (XGBoost):** Trees are built sequentially. Each new tree corrects errors made by previous trees. Final answer = weighted sum. Reduces bias.
>
> Bagging is safer and less prone to overfitting. Boosting is often more accurate but can overfit if not tuned carefully.

---

## ⚡ Model 6 — XGBoost

```python
import xgboost as xgb

np.random.seed(42)

xgb_model = xgb.XGBRegressor(n_estimators=1000, learning_rate=0.1, random_state=42, n_jobs=4)
xgb_model.fit(X, prices)

def xg_boost(item):
    x = vectorizer.transform([item.summary])
    return max(0, xgb_model.predict(x)[0])

evaluate(xg_boost, test)
```

### How XGBoost differs from Random Forest

| Aspect | Random Forest | XGBoost |
|---|---|---|
| Tree building | Parallel, independent | Sequential, each corrects last |
| Method | Bagging (averaging) | Gradient Boosting |
| Speed | Slower on large data | Faster |
| Typical accuracy | Good | Often better |
| Overfitting risk | Lower | Higher (needs tuning) |

### What does `learning_rate=0.1` do?

Each new tree corrects the previous trees' errors — but not by 100%. The learning rate controls how much each tree's correction is applied.

- `learning_rate = 1.0` → each tree fully corrects errors → aggressive, can overfit
- `learning_rate = 0.1` → each tree makes a small correction → slower but more stable
- More trees needed with smaller learning rate (hence `n_estimators=1000`)

### What is Gradient Descent doing here?

XGBoost uses gradient descent — instead of descending on a loss function over model weights (like neural networks), it descends by adding better and better trees.

```
Iteration 1: Predict average → Error = 200
Iteration 2: Build tree to predict error → Total Error = 150
Iteration 3: Build tree to predict remaining error → Total Error = 110
...
Iteration 1000: Total Error = ~60
```

### Interview Insight 💼

> **Q: Why is XGBoost so popular in Kaggle competitions and industry?**
>
> 1. Handles missing values natively
> 2. Built-in regularization (prevents overfitting)
> 3. Extremely fast (written in C++)
> 4. Works well on tabular/structured data
> 5. Easy to tune (learning rate, max depth, n_estimators)
>
> For many tabular data problems in industry (fraud detection, credit scoring, click prediction), XGBoost or LightGBM still outperform deep learning.

---

## 📦 Summary & Remember This

### Model Performance Progression (expected behavior)

```
Random Pricer          →  Very high error  (floor baseline)
Constant/Average       →  High error       (smart baseline)
Linear Reg (3 features)→  Moderate error   (learns some patterns)
Linear Reg (NLP)       →  Better error     (words help!)
Random Forest          →  Lower error      (non-linear patterns)
XGBoost                →  Lowest error     (gradient boosting wins)
```

---

> ### 🟡 Remember This: The ML Pipeline Pattern
>
> **Every model in this notebook follows the same pattern:**
> 1. Extract features from raw data
> 2. Convert to numerical format the algorithm accepts
> 3. Train (`.fit()`)
> 4. Wrap in a `pricer(item)` function
> 5. Evaluate with the same `evaluate()` function
>
> **This is the standard ML workflow. Memorize it.**

---

> ### 🟡 Remember This: Baselines Are Not Optional
>
> Before building any ML model in industry, always define:
> - Worst possible baseline (random)
> - Smartest simple baseline (average / mode / last value)
>
> Your model must meaningfully beat both. If it doesn't, you have a problem with your features, data, or approach — not a model problem.

---

> ### 🟡 Remember This: max(0, prediction)
>
> Regression models can predict negative prices. Always clip at 0 for quantities that can't be negative. This small guard saves embarrassing production bugs.

---

## 📝 Revision Sheet

| Concept | One-Line Definition |
|---|---|
| Train/Val/Test split | Separate data to measure real-world generalization |
| Baseline model | Simplest possible model to define the performance floor |
| Feature engineering | Converting raw data into numbers models can learn from |
| Linear Regression | Finds best-fit line/plane through data points |
| CountVectorizer | Converts text into word-count matrix (Bag of Words) |
| Stop words | Common words removed because they carry no signal |
| Random Forest | Average predictions of 100 decision trees (bagging) |
| Ensemble model | Combines multiple weak learners into one strong one |
| XGBoost | Builds trees sequentially; each corrects previous errors (boosting) |
| MSE | Mean Squared Error — average of squared prediction errors |
| R² score | How much better the model is vs. just predicting the average |
| Gradient Descent | Optimization method that iteratively reduces error |
| `random.seed(42)` | Makes randomness reproducible |
| `n_jobs=4` | Use 4 CPU cores for parallel training |
| Data leakage | Accidentally training on test data — invalidates evaluation |

---

## ❌ Common Mistakes

1. **Evaluating on training data** — always evaluate on the test set the model has never seen.

2. **Forgetting `max(0, prediction)`** — regression can predict negative prices.

3. **Using `vectorizer.fit_transform()` on test data** — you must use `vectorizer.transform()` (not `fit_transform`) on test/validation data. The vocabulary is fixed from training.
   ```python
   # WRONG:
   X_test = vectorizer.fit_transform(test_documents)  # learns new vocabulary!
   
   # CORRECT:
   X_test = vectorizer.transform(test_documents)  # uses training vocabulary
   ```

4. **Confusing bagging and boosting** — Random Forest = parallel trees averaged. XGBoost = sequential trees, each correcting the last.

5. **Not setting a random seed** — results become non-reproducible, making debugging and comparison unreliable.

6. **Training on the full dataset too early** — always use `LITE_MODE` or a subset to prototype fast. Full training on 800k items takes hours.

7. **Ignoring the baseline** — declaring a model "good" without comparing it to the constant pricer baseline. A model with R²=0.3 sounds decent until you realize the average pricer got R²=0.

---

## 🏋️ Exercises

**Beginner:**
1. Change `max_features` in CountVectorizer to 500, 1000, 5000. How does error change?
2. Add a new feature to `get_features()` — for example, number of words in the summary. Does Linear Regression improve?
3. Change `n_estimators` in Random Forest from 100 to 10. How does accuracy change? How does training time change?

**Intermediate:**
4. Use `TfidfVectorizer` instead of `CountVectorizer`. TF-IDF gives rarer words more weight. Does it perform better?
5. Build a feature that detects if a product name contains brand keywords like "Apple", "Samsung", "Sony". Does adding this feature improve Linear Regression?
6. Add bigrams to CountVectorizer: `CountVectorizer(ngram_range=(1,2))`. This captures phrases like "gaming laptop". Does it help?

**Advanced:**
7. Try LightGBM as an alternative to XGBoost. Compare training speed and accuracy.
8. Use `GridSearchCV` to tune XGBoost hyperparameters (`learning_rate`, `max_depth`, `n_estimators`).
9. Log-transform the prices before training (since prices are right-skewed). Does this improve R² score?
   ```python
   log_prices = np.log1p(prices)  # log(1 + price) to handle price=0
   ```

---

## 🔮 Future Connections to LLMs

Understanding Day 3 makes Day 4 and Day 5 much clearer:

| Day 3 (Traditional ML) | Day 4/5 (Deep Learning + LLMs) |
|---|---|
| CountVectorizer bag-of-words | **Tokenization** in LLMs (subword units via BPE) |
| Fixed vocabulary of 2000 words | LLM vocabulary of 50,000+ tokens |
| No word order | **Attention mechanism** captures word order and context |
| "iPhone" ≠ "smartphone" (different columns) | **Embeddings** place similar words near each other |
| Linear weights on word counts | **Transformer layers** — deep non-linear feature extraction |
| XGBoost sequential tree correction | **Residual connections** in neural networks do something similar |
| `max(0, prediction)` guard | LLM output post-processing (temperature, top-k, structured output) |

The entire progression of this capstone (Day 1 → Day 5) mirrors the history of ML itself:

```
Random Guessing (1950s)
     ↓
Simple Statistics / Average (1960s)
     ↓
Linear Models (1970-80s)
     ↓
Bag of Words + Linear Models (1990s, early NLP)
     ↓
Random Forest / Gradient Boosting (2000s, XGBoost 2014)
     ↓
Deep Learning (2010s)
     ↓
Transformer / LLMs (2017–now)
```

By building all of these yourself, you now have an intuition for *why* LLMs are powerful — and *when* simpler models might be preferred (interpretability, speed, cost, small datasets).

---

> ### 🟡 Remember This: The Golden Rule of ML Projects
>
> **Always build the simplest possible thing first.**
>
> Random → Average → Linear → Tree → Neural → LLM
>
> Each step must justify its added complexity with meaningfully better results.
> If your Linear Regression already achieves R²=0.85, you probably don't need to fine-tune GPT-4.

---

*Notes compiled from "The Price Is Right" Capstone, LLM Engineering Course — Week 6, Day 3*
*Course by Ed Donner | Dataset: HuggingFace Hub `ed-donner/items_lite`*