# Batched Embeddings Fix

This contribution provides a modified version of the ingestion script that fixes an OpenAI embeddings API error caused by sending too many input items in a single request.

## Problem

The original implementation sends all chunk texts to the embeddings API in one call. When the number of chunks is greater than the OpenAI embeddings API limit, this can cause the following error:

```text
openai.BadRequestError: Error code: 400 - Invalid 'input': array length must be 2048 or less.
```

## Solution

The modified version updates `create_embeddings()` to process chunks in smaller batches.

Instead of embedding all texts at once, it:

1. Splits the chunks into batches
2. Creates embeddings for each batch
3. Adds each batch to the Chroma collection
4. Prints the final vectorstore document count

The default batch size is set to `500`, which keeps each embeddings request safely below the API limit.

## Model Change

The modified version also updates the LiteLLM model value from:

```python
MODEL = "openai/gpt-4.1-nano"
```

to:

```python
MODEL = "openai/gpt-5.4-nano"
```

This change is included in the modified file, but the main purpose of this contribution is the batched embeddings fix.

## Notes

No original course files were modified. This is provided as a community contribution showing a safer way to create embeddings when the number of chunks is large.
