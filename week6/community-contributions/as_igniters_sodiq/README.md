# House Rent Pricer Project

This project explores various approaches to predicting house rent prices in Lagos, Nigeria, using the dataset [`adiscodex/nigeria-lagos-rent-2022`](https://huggingface.co/datasets/adiscodex/nigeria-lagos-rent-2022). The goal is to evaluate both traditional machine learning models and state-of-the-art frontier language models for the rent prediction task.

## Dataset

We use the `adiscodex/nigeria-lagos-rent-2022` dataset, which contains thousands of rental listings from Lagos, Nigeria, with features such as property type, location, number of bedrooms, and a summary description.

## Evaluation Metrics

All models are evaluated on a held-out test set using standard regression metrics such as Mean Squared Error (MSE) and R² score.

## Models Evaluated

### 1. Constant Pricer

A simple baseline that always predicts the average price from the training set.

### 2. NLP + Linear Regression

- Text features are extracted from property summaries using a bag-of-words approach.
- A linear regression model is trained on these features to predict rent prices.

### 3. Random Forest

- Uses the same text features as above.
- A random forest regressor is trained for improved non-linear modeling.

### 4. Frontier Language Models

These models leverage world knowledge and advanced language understanding for zero-shot price estimation:
- **GPT 4.1 Nano**
- **Gemini 2.5 Flash**
- **Claude Opus 4.5**

Each model is prompted with the property summary and asked to estimate the rent.

### 5. Fine-Tuned GPT 4.1 Nano

A version of GPT 4.1 Nano fine-tuned specifically on the Lagos rent dataset for improved accuracy.

## Results

The performance of each model is compared based on prediction error. The results demonstrate the strengths and weaknesses of traditional ML models versus large language models, as well as the impact of fine-tuning.