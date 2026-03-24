# Amazon Book Price Estimator

This solution shows a machine learning project that fine-tunes a large language model to predict the price of a book from its title, author, genre and format alone.

The Goal...

Given only the text description of a book:

```
Title: A Brief History of Time
Author: Stephen Hawking
Genre: Science
Sub Genre: Physics
Format: Paperback
```

Can an LLM predict its price?

---

## Dataset

- **Source:** [Amazon Books Dataset — Genre, Sub-genre, and Books](https://www.kaggle.com/datasets/chhavidhankhar11/amazon-books-dataset) (Kaggle)
- **Size:** 7,167 books after cleaning
- **Price range:** $1.06 - $17.24 (converted from INR to USD at ₹84/$1)
- **Features used:** Title, Author, Genre, Sub Genre, Format
- **Features deliberately excluded:** Rating, number of reviews, original rupee price

The cleaned dataset is hosted on Google Drive and is downloaded automatically when you run `book_pricer_data.ipynb`.

To download manually: [Download books_clean.csv](https://drive.google.com/file/d/1f8wj-y-zddemezdybk8DkXJEyOp5OgJC/view?usp=sharing)

---

## Approach

### Data Pipeline

- Prices converted from Indian Rupees (₹) to USD
- Outliers removed — kept 5th to 95th percentile
- 80 / 10 / 10 train / val / test split with fixed seed (42)

### Bucket Sampling

Instead of selecting training examples randomly, I decided to experiment with equal representation across price tiers:


| Bucket                 | Range          | Examples |
| ---------------------- | -------------- | -------- |
| Cheap paperbacks       | $1.00 – $2.50  | 20 or 40 |
| Standard paperbacks    | $2.50 – $4.00  | 20 or 40 |
| Mid range              | $4.00 – $6.00  | 20 or 40 |
| Premium                | $6.00 – $10.00 | 20 or 40 |
| Expensive / hardcovers | $10.00+        | 20 or 40 |


This will prevent the model from being biased toward cheap paperbacks which dominate the dataset With random selection, the model rarely sees expensive books during training and often fails to predict them accurately.

---

## 📊 Results


| Model                                  | Average Error | Notes                             |
| -------------------------------------- | ------------- | --------------------------------- |
| Random pricer                          | $5.18         | Predicts randomly — the floor     |
| Constant pricer                        | $2.10         | Always predicts the mean          |
| Linear Regression                      | $1.80         | Word counts mapped to price       |
| Random Forest                          | $1.60         | Ensemble of decision trees        |
| **XGBoost (ML best)**                  | **$1.55**     | **Best traditional ML result**    |
| GPT-4.1-nano baseline (first-100)      | $10.28        | Random selection, 1 epoch         |
| GPT-4.1-nano bucket-100 (1 epoch)      | $4.31         | Balanced 100 examples             |
| GPT-4.1-nano bucket-200 (1 epoch)      | $37.37        | Anomalous — wrong model evaluated |
| **GPT-4.1-nano bucket-200 (3 epochs)** | **$2.29**     | **Best LLM result**               |


### Key Findings

- **Bucket sampling halved the error** — from $10.28 (random baseline) to $4.31 using the exact same number of examples. Data selection quality matters more than data quantity at small scale.
- **3 epochs with 200 balanced examples ($2.29) came within $0.74 of XGBoost ($1.55)** — which trained on the full dataset of thousands of examples.
- Traditional ML still wins on this dataset, but the fine-tuned LLM closes the gap significantly when training data is carefully curated.

---

## Files


| File                       | Purpose                                                  |
| -------------------------- | -------------------------------------------------------- |
| `clean.py`                 | Cleans raw CSV, converts prices from ₹ to USD            |
| `book_pricer_data.ipynb`   | Downloads dataset, builds Item objects, saves splits.pkl |
| `book_pricer_models.ipynb` | Runs ML baselines and fine-tuning experiments            |
| `evaluator.py`             | Evaluation framework (from Ed Donner's course)           |


---

## How to Run

### 1. Install dependencies

```bash
pip install pandas numpy scikit-learn xgboost openai python-dotenv gdown
```

### 2. Add your OpenAI API key

Create a `.env` file in the project folder:

```
OPENAI_API_KEY=your-key-here
```

### 3. Run `book_pricer_data.ipynb`

This notebook will automatically download `books_clean.csv` from Google Drive and generate `splits.pkl`.

### 4. Run `book_pricer_models.ipynb`

Runs traditional ML baselines then fine-tuning experiments. Run one experiment at a time and wait for each OpenAI fine-tuning job to finish before running the eval cell.

---

## 💡 Key Takeaway

> Bucket sampling — selecting training examples evenly across price tiers — consistently outperforms random selection with the same number of examples.
> **Data quality beats data quantity at small scale.**

