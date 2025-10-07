## Biomedical Article Abstract Summariser using Europe PMC + Ollama

This is a simple app that demonstrates an article abstract summariser leveraging Europe PMC’s API and Ollama LLMs to generate concise summaries of biomedical literature.

## 🔍 About Europe PMC (EPMC)
Europe PMC is a free, open-access database that provides access to millions of life sciences and biomedical articles, research papers, and preprints. It is part of the PubMed Central International (PMCI) network.

## Features

This solution presents 2 methods: 
1. A simple demo via a jupyter notebook
2. An interactive demo via gradio, running on your local computer. 

**Core Features:** 
- Fetch an article’s metadata and abstract via Europe PMC’s API (using a provided PMCID).
- Preprocess and clean the abstract text unnecessary tags e.g referenc tag or math formula.
- Summarise abstracts into bullet points + a short paragraph using Ollama models.



## 📌 How to Use

- Go to [Europe PMC' website](https://europepmc.org/).
- Use the search bar to find an open-access article by keywords, entity names, journal, or author. E.g Genes, Diseases, nutrition etc
- Since the app currently only runs on open-access only articles, you'll need to restrict results to `open-access` only articles: add filters like `HAS_FT:Y` or `IN_EPMC:Y` to your search syntax. E.g .`"Genes: HAS_FT:Y"`
- Select your article of interest and copy its PMCID (e.g., PMC1234567).

- Run the summariser:
  - via notebook: Paste the `PMCID` as a string in the display_response func, after running all other cells. 
  - via gradio: 
    - run the python script via CLI: 
    ```python
    python article_summariser-gradio.py
    ```
    - Paste the `PMCID` as you've copied it in the `Enter a **EuropePMC Article ID` textbox. 
    - click on the `Fetch Article Abstract and generate Summary` button. 
    **N.B**: I've observed that using `llama3.2` runs faster on my pc. You may experience some delays with all other models. Also make sure to already have ollama running via `ollama serve` on your terminal before running the script. 

