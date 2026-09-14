# Week5 EXERCISE 
Beat Ed's RAG Evaluation Board

> I was able to beat Ed's best RAG Evaluation Board on LangChain Experiement but failed several times on No LangChain Experiment.
`code`


## LangChain Experiment
> In experiment, blah, blah
- Implementation folder
- MODEL = "gpt-4.1-nano"
- embeddings = OpenAIEmbeddings(model="text-embedding-3-large”)
- 3,072 dimensions

| LANGHAIN             | ed's best     | auroraa E1    | auroraa E2     | auroraa E3     | auroraa E4     |
| -------------------- | ------------- | ------------- | -------------- | -------------- | -------------- |
| RAG                  |RETRIEVAL_K=10 |RETRIEVAL_K=10 |RETRIEVAL_K=3   |RETRIEVAL_K=3   |RETRIEVAL_K=10  |
| Evaluation           |TextSplitter   |TextSplitter   |TextSplitter    |MarkdownSplitter|MarkdownSplitter|    
| Board                |chunksize=500  |chunksize=10   |chunk_size=1667 |                |                |    
|                      |970 vectors    |970 vectors    |235 vectors     |109 vectors     |109 vectors     |   
|`Retrieval Evaluation`|               |               |                |                |                |
| MRR                  | 0.7903        | 0.7945        | 0.8836         | 0.9286         | 0.9333         |
| nDCG                 | 0.7901        | 0.7943        | 0.8901         | 0.9288         | 0.9020         |
| Keyword Coverage     | 92.5%         | 92.8%         | 92.9           | 95.4%          | 97.7%          |
|`Answer Evaluation`   |               |               |                |                |                |
| Accuracy             | 4.21/5        | 4.24/5        | 4.41/5         | 4.45/5         | 4.73/5         |
| Completeness         | 4.05/5        | 4.02/5        | 4.17/5         | 4.27/5         | 4.41/5         |
| Relevance            | 4.71/5        | 4.76/5        | 4.74/5         | 4.8/5          | 4.89/5         |



## No LangChain Experiment
> In this experiment, blah, blah
- Pro-implementation folder
ingest
 - MODEL = "openai/gpt-4.1-nano" 
 - AVERAGE_CHUNK_SIZE = 100
answer
 - MODEL = "groq/openai/gpt-oss-120b" or "openai/gpt-4.1-nano"
 - RETRIEVAL_K = 20
 - FINAL_K = 10 

| NO LANGCHAIN         | ed's best      | auroraa E1     | auroraa E2     | auroraa E3     | auroraa E4     |
| -------------------- | -------------  | -------------- | -------------- | -------------- | -------------- |
| RAG                  |RETRIEVAL_K=20  |RETRIEVAL_K=20  |RETRIEVAL_K=20  |RETRIEVAL_K=20  |RETRIEVAL_K=20  |
| Evaluation           |WORKERS=10      |WORKERS=10      |WORKERS=10      |WORKERS=5       |WORKERS=10      |    
| Board                |gpt-oss-120b    |gpt-oss-120b    |gpt-4.1-nano    |gpt-4.1-nano    |gpt-oss-120b    |    
|                      |created 534 docs|created 534 docs|created 557 docs|created 515 docs|created 507 docs|
|`Retrieval Evaluation`|                |                |                |                |                |
| MRR                  | 0.9116         |    FAIL        | 0.8650         | 0.8459         | 0.8745         |
| nDCG                 | 0.9025         |    FAIL        | 0.8393         | 0.8264         | 0.8475         |
| Keyword Coverage     | 96.0%          |    FAIL        | 93.7%          | 93.0%          | 94.9%          |
|`Answer Evaluation`   |                |                |                |                |                |
| Accuracy             | 4.62/5         |                | 4.44/5         | 4.46/5         | 4.28/5         |
| Completeness         | 4.35/5         |                | 4.13/5         | 4.17/5         | 4.10/5         |
| Relevance            | 4.84/5         |                | 4.74/5         | 4.74/5         | 4.72/5         |
