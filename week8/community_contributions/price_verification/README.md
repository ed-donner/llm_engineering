# Price verification after the selection

## Why

The estimate comes from the ensemble: a frontier model doing RAG over Amazon Reviews 2023, the
fine-tuned pricer from week 7, and the neural network from week 6. All three sit in the same 2023
price world, and train, validation and test are slices of the same shuffled data, so the week 6 and
week 7 numbers say how well they predict 2023 prices, not today's. The prompt carries no date, so
nothing in the chain can answer for another year, and more training does not fix it, because the
information is not in the data. What carries over to today is the ranking between products, not the
price level.

That matters for week 8, because a discount is the estimate minus the asking price. If the estimate
sits at a 2023 price level, so does the discount, and a deal can clear the threshold on the gap
between two years rather than on a real saving.

So for products that can be identified one to one at another retailer, this checks the estimate
against a price that exists today, and measures the saving against that instead.

## What it does

Once the planner has picked the best deal of a run, it looks up what that product currently sells
for elsewhere, and measures the discount against that price. The threshold test then runs on the
looked up price, so a deal that only cleared the threshold on a high estimate is dropped. Five deals
are estimated and only the winner is looked up, so this is one web search per run.

## Why the pipeline stays as it is

The obvious alternative is to drop the estimate and look up every deal instead. That does not work
here. A lookup only returns something when one specific product can be identified, which is not true
for a lot of what the scanner surfaces, and it costs a web search per deal rather than one per run.
The ensemble is what can put a number on everything, including the products no other retailer lists,
so it stays as the thing that ranks the five candidates. The lookup is the check on the one that
comes out on top.

## What it measures against

The lowest valid listing, not an average or a median across retailers. The question is not what the
product is worth, it is whether the same thing can be bought cheaper somewhere else, so the cheapest
offer is what the saving should be measured against.

That puts the weight on what counts as a listing, and those conditions are set in the system prompt,
and repeated in the field descriptions of the schema: the same product matched on model number, the
same condition, sold by the retailer itself rather than a third party on a marketplace, and a price
a shopper pays today rather than an MSRP or a limited time promotion. Every listing carries the URL
it came from.

## What it can and cannot do

This only works for deals where one specific product can be identified at another retailer. The
conditions are strict on purpose: the same model number, the same condition, sold by the retailer
itself. When the product cannot be pinned down that way the lookup returns `found=false`, the
estimate stays, and the deal is handled exactly as before. Those deals keep the 2023 baseline, so
this narrows the problem rather than removing it.

It does not correct the estimates themselves and it does not say how far off the model is in
general. It re-bases the one deal that was picked, on one lookup per run. This also means the
ensemble still decides which deal gets checked. A deal it undervalued is never looked up.

## Files

- `verifier_agent.py`: the `VerifierAgent`. It calls the OpenAI Responses API with the `web_search`
  tool on `gpt-5.1`, using the `OPENAI_API_KEY` the course already uses, and returns the cheapest
  valid listing or `None`.
- `verifying_planning_agent.py`: `VerifyingPlanningAgent`, a subclass of `PlanningAgent` with the
  verification step in `plan()`, and `VerifiedOpportunity`, an `Opportunity` with `verified` and
  `model_estimate` added so the models' own estimate is kept next to the verified price.

Nothing in `week8` is changed. When `DealAgentFramework` reads `memory.json` back it builds an
`Opportunity`, so those two extra fields are dropped on reload (checked with pydantic 2.11.10).

## Running it

From the `week8` directory:

```python
import sys
sys.path.append("community_contributions/price_verification")

from deal_agent_framework import DealAgentFramework
from verifying_planning_agent import VerifyingPlanningAgent

framework = DealAgentFramework()
framework.planner = VerifyingPlanningAgent(framework.collection)
framework.run()
```

## What it did, measured on 2026-09-06

- A mini PC advertised at $329 was estimated at $510.29, a discount of $181.29 and well over the
  threshold of $50. The lowest listing found online was $363.53, which makes the real saving $34.53,
  below the threshold. No alert was sent.
- A signage display from a brand with no second retailer returned `found=false`, so the estimate
  stayed and the deal was handled exactly as before.

## How reliable a verified price is

The lookup is itself a draw. The same product, an LG S80TR soundbar, returned $599.99, $909.99 and
$699.99 over three lookups, at LG and Walmart, at Target, and at Best Buy. Within one lookup the
listings are consistent, between lookups they are not. So verified here means a real price for this
exact product on that lookup, not the market price.

How often a lookup succeeds over a longer series has not been measured, and neither has the effect
on the number of alerts over time. Both figures above come from a single run each.
