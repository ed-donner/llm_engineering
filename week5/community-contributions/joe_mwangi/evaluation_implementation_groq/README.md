# Evaluation implementation notes

Within this folder, I have implemented the week5 evaluation module from scratch after studying the code provided within the evaluation parent folder.

In addition, I have included other retrieval metric evaluation implementations along with descriptions of their:
- Importance
- Implementation
- Pros and Cons

`Note`:
- You need to place this folder within `week5/evaluation` the imports and file paths to work.
- If you feel comfortable working with file paths, feel free to place the folder as prefered and alter the paths and module imports.
- I opted to use GROQ (the abstraction layer) to run the answer evaluations to:
        - minimize on costs
        - avoid api rate limits from gemini
        - ensure speed

I have divided the metric implementations into two:
- Prediction metrics:
    - precision
    - recal
    - f-beta score
- Ranking metrics:
    - MAP (Mean Average Precision)
    - MRR (Mean Reciprical Rank)
    - NDCG (Normalized Discounted Gain)
    - Hit Rate

On average the answer evaluations take between 20 and 25 minutes to complete 150 tests.

