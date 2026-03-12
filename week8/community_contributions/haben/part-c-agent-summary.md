# Part C: Autonomous Agent System - Implementation Summary

**Repository**: [ai-price-prediction-capstone](https://github.com/habeneyasu/ai-price-prediction-capstone)  
**Part**: Part C - Autonomous Agent System (Week 8)  
**Status**: ✅ Completed  
**Branch**: `main`

---

## The Story: From Price Prediction to Deal Discovery

Imagine an intelligent assistant that never sleeps, constantly scouring the internet for bargains, analyzing prices with the precision of multiple AI models, and alerting you only when it finds truly exceptional deals. This is the story of **Part C: Autonomous Agent System** – the culmination of a three-part journey that transforms price prediction into an autonomous deal-hunting companion.

### The Journey So Far

In **Part A**, we established baseline performance using frontier commercial models. In **Part B**, we fine-tuned open-source models to compete with those frontier models. Now, in **Part C**, we bring everything together into an autonomous system that doesn't just predict prices – it actively hunts for deals and notifies you of opportunities.

---

## Overview

Part C implements an autonomous agent system that collaborates with multiple models to spot deals and notify users of special bargains. The system continuously monitors RSS feeds, intelligently filters deals using LLM-powered analysis, estimates true market values through ensemble predictions, and automatically surfaces the best opportunities.

This component represents the evolution from static price prediction to an active, intelligent deal discovery system that operates autonomously in the background.

## The Architecture: A Symphony of Specialized Agents

The system operates through a coordinated ensemble of specialized agents, each with a distinct role in the deal discovery pipeline.

### 1. **Scanner Agent: The Internet Scout**

The journey begins with the **Scanner Agent**, which acts as the system's eyes on the internet.

- **RSS Feed Monitoring**: Continuously scans configured RSS feeds for new deals
- **Intelligent Parsing**: Uses GPT-5-mini with structured outputs to extract deal information
- **Deal Filtering**: Intelligently filters and selects high-potential deals from scraped content
- **Memory Management**: Tracks previously surfaced deals to avoid duplicates

The Scanner Agent transforms raw internet content into structured deal information, ensuring only relevant opportunities proceed to the next stage.

### 2. **Ensemble Agent: The Price Oracle**

Once deals are discovered, the **Ensemble Agent** determines their true market value.

- **Multi-Model Collaboration**: Combines predictions from multiple pricing models
  - Fine-tuned specialist models (from Part B)
  - Frontier models with RAG (from Part A)
  - Traditional ML models (Random Forest, XGBoost)
- **Weighted Predictions**: Intelligently weights different model outputs for optimal accuracy
- **Context-Aware Pricing**: Uses RAG (Retrieval-Augmented Generation) to provide context from similar products
- **Confidence Scoring**: Provides confidence levels for price estimates

The Ensemble Agent represents the culmination of Parts A and B, leveraging both frontier and fine-tuned models to provide the most accurate price estimates.

### 3. **Messaging Agent: The Notifier**

When exceptional deals are identified, the **Messaging Agent** ensures users are informed.

- **Push Notifications**: Sends notifications for compelling deals
- **Deal Summarization**: Formats deal information for clear communication
- **Threshold Management**: Only notifies when deals meet quality thresholds
- **User Preferences**: Can be configured for personalized notification preferences

### 4. **Autonomous Planning Agent: The Orchestrator**

The **Autonomous Planning Agent** serves as the conductor of this symphony, coordinating all other agents through function calling.

- **Workflow Orchestration**: Uses GPT-5.1 with function calling to coordinate agent activities
- **Intelligent Decision Making**: Decides when to scan, when to estimate, and when to notify
- **Opportunity Detection**: Identifies deals where estimated value significantly exceeds offer price
- **Memory Management**: Maintains context of previously processed deals

The Planning Agent embodies the "autonomous" nature of the system, making intelligent decisions about when and how to act without human intervention.

## The Workflow: A Day in the Life of a Deal Hunter

### Morning: The Scan

Every cycle begins with the Scanner Agent awakening to scan the internet. It fetches the latest deals from configured RSS feeds, parsing through hundreds of listings. Using GPT-5-mini with structured outputs, it intelligently extracts product descriptions, prices, and URLs, filtering out low-quality or irrelevant deals.

### Midday: The Analysis

Promising deals flow to the Ensemble Agent, which becomes a council of pricing experts. Each model in the ensemble provides its estimate:
- The fine-tuned specialist model draws from its training on similar products
- The frontier model with RAG retrieves context from a vector database of historical prices
- Traditional ML models provide statistical baselines

The Ensemble Agent synthesizes these predictions, weighting them based on historical performance, to arrive at a consensus estimate of true market value.

### Afternoon: The Decision

The Planning Agent reviews each deal, comparing the offer price against the estimated true value. When it discovers a deal where the discount exceeds a threshold (e.g., estimated value $100, offer price $60 = $40 savings), it recognizes an opportunity.

### Evening: The Notification

For the most compelling opportunity, the Planning Agent calls upon the Messaging Agent. A notification is crafted, summarizing the product, the deal price, the estimated value, and the potential savings. The user receives an alert about this exceptional bargain.

### Night: The Memory

The system updates its memory, recording which deals have been surfaced. This prevents duplicate notifications and helps the system learn which types of deals are most valuable to the user.

## Technical Implementation

### Agent Coordination

The system uses OpenAI's function calling API to enable the Planning Agent to orchestrate other agents:

```python
# Planning Agent has access to three tools:
1. scan_the_internet_for_bargains() → Scanner Agent
2. estimate_true_value(description) → Ensemble Agent  
3. notify_user_of_deal(...) → Messaging Agent
```

The Planning Agent uses GPT-5.1 to intelligently decide which tools to call and in what sequence, creating a truly autonomous workflow.

### Ensemble Price Prediction

The Ensemble Agent combines multiple prediction sources:

- **Specialist Models**: Fine-tuned models from Part B, deployed on Modal for scalable inference
- **Frontier Models with RAG**: GPT-4o-mini or DeepSeek with vector database retrieval
- **Traditional ML**: Random Forest and XGBoost models on product embeddings
- **Weighted Combination**: Predictions are weighted based on historical accuracy

### Deal Opportunity Detection

An opportunity is identified when:
- Estimated true value > Deal price (by significant margin)
- Deal quality meets minimum thresholds
- Deal hasn't been previously surfaced (memory check)

### RSS Feed Integration

The Scanner Agent integrates with RSS feeds to continuously monitor deal sources:
- Configurable feed URLs
- Automatic parsing of feed entries
- Intelligent extraction of product information
- Duplicate detection and filtering

## Repository Structure

Based on the [repository structure](https://github.com/habeneyasu/ai-price-prediction-capstone), Part C is organized as:

```
ai-price-prediction-capstone/
├── part-c-agent/            # Part C: Autonomous Agents
│   ├── README.md
│   ├── agents/              # Agent implementations
│   │   ├── agent.py         # Base agent class
│   │   ├── scanner_agent.py
│   │   ├── ensemble_agent.py
│   │   ├── messaging_agent.py
│   │   └── autonomous_planning_agent.py
│   ├── notifier/           # Notification system
│   └── src/                # Source code
├── shared/                  # Shared utilities (from Parts A & B)
│   └── price_prediction_utils/
│       ├── item.py
│       ├── frontier_models.py
│       ├── predictor.py
│       └── evaluator.py
└── requirements.txt
```

## Key Features

### 1. **Autonomous Operation**
- Runs continuously without human intervention
- Makes intelligent decisions about deal quality
- Manages its own workflow and memory

### 2. **Intelligent Deal Filtering**
- LLM-powered parsing and filtering
- Quality thresholds for deal selection
- Context-aware deal evaluation

### 3. **Ensemble Price Prediction**
- Combines multiple model predictions
- RAG-enhanced context retrieval
- Weighted consensus for accuracy

### 4. **Smart Notifications**
- Only notifies for exceptional deals
- Avoids notification fatigue
- Personalized deal summaries

### 5. **Memory and Learning**
- Tracks processed deals
- Avoids duplicate notifications
- Can learn user preferences over time

## Integration with Capstone Project

Part C represents the culmination of the three-part capstone:

- **Leverages Part A**: Uses frontier models (GPT-4o-mini, DeepSeek) with RAG for price estimation
- **Leverages Part B**: Incorporates fine-tuned specialist models for accurate pricing
- **Adds Autonomy**: Transforms static prediction into active deal discovery
- **Completes the Journey**: From baseline → competition → automation

## Usage

### Running the Autonomous System

```bash
cd part-c-agent/src
python main.py --feeds "feed1.xml,feed2.xml" --threshold 0.3
```

### Configuration

Environment variables (`.env` file):

```env
# OpenAI API (for Planning and Scanner agents)
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
PLANNING_MODEL=gpt-5.1
SCANNER_MODEL=gpt-5-mini

# RSS Feed Configuration
RSS_FEEDS=feed1.xml,feed2.xml,feed3.xml

# Deal Thresholds
MIN_DISCOUNT_PERCENTAGE=30
MIN_DEAL_QUALITY=0.7

# Notification Configuration
NOTIFICATION_ENABLED=true
NOTIFICATION_CHANNEL=push
```

## Dependencies

Core dependencies for Part C:

- **`openai`**: OpenAI API client for function calling and agent coordination
- **`feedparser`**: RSS feed parsing
- **`pydantic`**: Structured data models for deals and opportunities
- **`requests`**: HTTP requests for RSS feeds and APIs
- **Shared utilities**: From Parts A and B for price prediction

## The Result: An Intelligent Deal Companion

Part C transforms the price prediction capabilities from Parts A and B into an autonomous system that:

1. **Continuously Monitors**: Never misses a deal opportunity
2. **Intelligently Filters**: Only surfaces high-quality, relevant deals
3. **Accurately Prices**: Uses ensemble methods for reliable estimates
4. **Proactively Notifies**: Alerts users to exceptional bargains
5. **Learns and Adapts**: Improves over time through memory and feedback

## Conclusion

Part C: Autonomous Agent System completes the capstone journey by transforming price prediction into an intelligent, autonomous deal discovery companion. The system demonstrates how multiple AI models can collaborate through agent orchestration to create value beyond individual model capabilities.

From establishing baselines in Part A, to competing with frontier models in Part B, to building an autonomous system in Part C – this capstone showcases the full spectrum of modern AI engineering: from model selection to fine-tuning to agentic systems.

The result is not just a price prediction tool, but an intelligent assistant that actively works to find you the best deals, combining the power of frontier models, fine-tuned specialists, and traditional ML into a cohesive, autonomous system.

---

## References

- **Repository**: [habeneyasu/ai-price-prediction-capstone](https://github.com/habeneyasu/ai-price-prediction-capstone)
- **Branch**: `main`
- **Part**: Part C - Autonomous Agent System (Week 8)
- **Description**: Autonomous agent system collaborating with models to spot deals and notify you of special bargains
