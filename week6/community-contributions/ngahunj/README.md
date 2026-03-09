# Hyperparameter Experiments

This folder contains a **minimal exercise**: experiment with hyper-parameters to improve the Week 6 "Price is Right" models.

## Task

- Use the same data and evaluation setup as Week 6 (items from HuggingFace, `pricer.evaluator`).
- Try different hyperparameters for:
  - **Traditional ML**: Random Forest (e.g. `n_estimators`, `max_depth`, `min_samples_leaf`), and text features (`CountVectorizer` / `max_features`).
  - **Optional**: Deep neural network or other models.
- Compare validation (or test) error and report whether you improved over the default Week 6 settings.

## How to run

1. From the **week6** directory open and run:
  - `community-contributions/ngahunj/week_6_exercise.ipynb`
2. Or in a terminal from the repo root:
  ```bash
   cd week6 && jupyter notebook community-contributions/ngahunj/week_6_exercise.ipynb
  ```
3. Ensure `.env` has `HF_TOKEN` if you load data from HuggingFace Hub.

## Default Week 6 reference (from results.ipynb)

- Random Forest (Day 3): ~72.28 error  
- Deep Neural Network: ~46.49 error

Use these as baselines to try to beat with better hyperparameters.