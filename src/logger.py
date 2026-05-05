import json
import logging
from pathlib import Path


def setup_logger(log_dir: str = "logs") -> logging.Logger:
    Path(log_dir).mkdir(exist_ok=True)

    logger = logging.getLogger("recommender")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fh = logging.FileHandler(Path(log_dir) / "recommender.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def log_api_call(logger: logging.Logger, call_type: str, input_summary: str, output_summary: str) -> None:
    logger.info(json.dumps({
        "event": "api_call",
        "type": call_type,
        "input": input_summary[:200],
        "output": str(output_summary)[:200],
    }))


def log_retrieval(logger: logging.Logger, query: list, context: dict) -> None:
    logger.info(json.dumps({
        "event": "rag_retrieval",
        "query": query,
        "matched_genres": list(context.get("matched_genres", {}).keys()),
        "freq_vocab": context.get("frequency_vocabulary", []),
    }))


def log_scoring(logger: logging.Logger, profile: dict, results: list) -> None:
    top = [{"title": s["title"], "score": round(sc, 2)} for s, sc, _ in results[:3]]
    logger.info(json.dumps({
        "event": "scoring",
        "profile_genre": profile.get("genre", ""),
        "profile_mood": profile.get("mood", ""),
        "top_3": top,
    }))


def log_guardrail(logger: logging.Logger, reason: str, fallback_used: bool) -> None:
    logger.warning(json.dumps({
        "event": "guardrail",
        "reason": reason,
        "fallback_used": fallback_used,
    }))
