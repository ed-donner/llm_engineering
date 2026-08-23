#!/usr/bin/env python3
"""
Health checks for Deal Intel readiness:
- Environment variables presence
- Modal pricer availability
- ChromaDB collection populated
- Model artifacts load
- Agent instantiation
"""

import os
import joblib
import chromadb

from logging_utils import init_logger
import config as cfg

logger = init_logger("DealIntel.Health")

def check_env() -> bool:
    ok = True
    required_any = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY"]
    required = ["HF_TOKEN", "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"]
    push_vars = ["PUSHOVER_USER", "PUSHOVER_TOKEN"]

    logger.info("Checking environment variables")
    if not any(os.getenv(k) for k in required_any):
        logger.warning("Missing OPENAI_API_KEY or DEEPSEEK_API_KEY")
        ok = False
    for k in required:
        if not os.getenv(k):
            logger.warning(f"Missing {k}")
            ok = False
    if not all(os.getenv(k) for k in push_vars):
        logger.info("Pushover tokens not found — push alerts will be disabled")
    return ok

def check_modal() -> bool:
    import modal
    logger.info("Checking Modal pricer wake_up()")
    try:
        try:
            Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        except Exception:
            Pricer = modal.Cls.lookup("pricer-service", "Pricer")
        pricer = Pricer()
        reply = pricer.wake_up.remote()
        logger.info(f"Modal wake_up reply: {reply}")
        return True
    except Exception as e:
        logger.error(f"Modal pricer check failed: {e}")
        return False

def check_chroma() -> bool:
    logger.info(f"Checking ChromaDB at '{cfg.DB_PATH}' collection '{cfg.COLLECTION_NAME}'")
    try:
        client = chromadb.PersistentClient(path=cfg.DB_PATH)
        collection = client.get_or_create_collection(cfg.COLLECTION_NAME)
        result = collection.get(include=['embeddings'], limit=10)
        count = len(result.get("embeddings") or [])
        logger.info(f"ChromaDB sample embeddings count: {count}")
        return count > 0
    except Exception as e:
        logger.error(f"ChromaDB check failed: {e}")
        return False

def check_models() -> bool:
    logger.info("Checking model artifacts load")
    ok = True
    try:
        joblib.load("random_forest_model.pkl")
        logger.info("Random Forest model loaded")
    except Exception as e:
        logger.error(f"Random Forest model load failed: {e}")
        ok = False
    try:
        joblib.load("ensemble_model.pkl")
        logger.info("Ensemble model loaded")
    except Exception as e:
        logger.error(f"Ensemble model load failed: {e}")
        ok = False
    return ok

def check_agents() -> bool:
    logger.info("Checking agent instantiation")
    try:
        from agents.random_forest_agent import RandomForestAgent
        from agents.frontier_agent import FrontierAgent
        from agents.specialist_agent import SpecialistAgent

        client = chromadb.PersistentClient(path=cfg.DB_PATH)
        collection = client.get_or_create_collection(cfg.COLLECTION_NAME)

        rf = RandomForestAgent()
        fr = FrontierAgent(collection)
        sp = SpecialistAgent()
        _ = (rf, fr, sp)
        logger.info("Agents instantiated")
        return True
    except Exception as e:
        logger.error(f"Agent instantiation failed: {e}")
        return False

def run_all() -> bool:
    env_ok = check_env()
    modal_ok = check_modal()
    chroma_ok = check_chroma()
    models_ok = check_models()
    agents_ok = check_agents()

    overall = all([env_ok, modal_ok, chroma_ok, models_ok, agents_ok])
    if overall:
        logger.info("Health check passed — system ready")
    else:
        logger.warning("Health check failed — see logs for details")
    return overall

if __name__ == "__main__":
    ready = run_all()
    if not ready:
        raise SystemExit(1)