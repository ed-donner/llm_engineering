# LiteLLM's one call for any provider
from litellm import completion

# no client object needed: the prefix in the model name decides which provider is called
def ask(model, system, transcript):
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": transcript},
        ],
    )
    reply = response.choices[0].message.content
    # LiteLLM works out the price; local Llama has none, so "or 0" turns None into 0
    cost = response._hidden_params["response_cost"] or 0
    # send back two things at once, as a tuple (reply, cost)
    return reply, cost