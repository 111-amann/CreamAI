import contextvars
import json
import logging
import os
import re
import time
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("pydocspal.llm")

# Context variable and global store for the most recent LLM invocation telemetry
_last_llm_metrics: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "last_llm_metrics",
    default={
        "provider": "none",
        "latency_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    },
)

_global_last_metrics: dict[str, Any] = {
    "provider": "none",
    "latency_ms": 0.0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
}


def extract_token_usage(response: Any) -> dict[str, int]:
    """
    Extract token usage metrics (prompt_tokens, completion_tokens, total_tokens)
    from Groq or Gemini responses, or fallback safely to 0 when mocked or unavailable.
    """
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    if response is None:
        return usage

    # If response is a dict (e.g. mock or serialized response)
    if isinstance(response, dict):
        raw_usage = response.get("usage", response.get("usage_metadata", response))
        if isinstance(raw_usage, dict):
            prompt = raw_usage.get("prompt_tokens", raw_usage.get("prompt_token_count", 0))
            comp = raw_usage.get("completion_tokens", raw_usage.get("candidates_token_count", 0))
            total = raw_usage.get("total_tokens", raw_usage.get("total_token_count", 0))
            usage["prompt_tokens"] = int(prompt or 0)
            usage["completion_tokens"] = int(comp or 0)
            usage["total_tokens"] = int(total or (usage["prompt_tokens"] + usage["completion_tokens"]))
            return usage

    # Groq / OpenAI ChatCompletion style response
    if hasattr(response, "usage") and response.usage:
        prompt = getattr(response.usage, "prompt_tokens", 0)
        comp = getattr(response.usage, "completion_tokens", 0)
        total = getattr(response.usage, "total_tokens", 0)
        usage["prompt_tokens"] = int(prompt or 0)
        usage["completion_tokens"] = int(comp or 0)
        usage["total_tokens"] = int(total or (usage["prompt_tokens"] + usage["completion_tokens"]))
        return usage

    # Google GenAI style response with usage_metadata
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        meta = response.usage_metadata
        prompt = getattr(meta, "prompt_token_count", 0)
        comp = getattr(meta, "candidates_token_count", 0)
        total = getattr(meta, "total_token_count", 0)
        usage["prompt_tokens"] = int(prompt or 0)
        usage["completion_tokens"] = int(comp or 0)
        usage["total_tokens"] = int(total or (usage["prompt_tokens"] + usage["completion_tokens"]))
        return usage

    return usage


def record_llm_metrics(
    latency_ms: float,
    tokens: dict[str, int],
    provider: str = "",
) -> dict[str, Any]:
    """Record LLM telemetry metrics into thread/request context and global store."""
    global _global_last_metrics
    metrics = {
        "provider": provider,
        "latency_ms": round(latency_ms, 2),
        "prompt_tokens": tokens.get("prompt_tokens", 0),
        "completion_tokens": tokens.get("completion_tokens", 0),
        "total_tokens": tokens.get("total_tokens", 0),
    }
    _last_llm_metrics.set(metrics)
    _global_last_metrics = metrics
    return metrics


def get_last_llm_metrics() -> dict[str, Any]:
    """Retrieve the most recent LLM invocation telemetry metrics."""
    ctx_metrics = _last_llm_metrics.get()
    if ctx_metrics and ctx_metrics.get("latency_ms", 0.0) > 0.0:
        return ctx_metrics
    return _global_last_metrics


def reset_llm_metrics() -> None:
    """Reset LLM telemetry metrics."""
    global _global_last_metrics
    initial = {
        "provider": "none",
        "latency_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    _last_llm_metrics.set(initial)
    _global_last_metrics = initial


def _recover_tool_call_from_groq_error(exc: Exception) -> Optional[str]:
    """
    Recover tool call JSON when Groq raises BadRequestError with code 'tool_use_failed'.
    When models (like openai/gpt-oss-20b or llama) output function-calling format,
    Groq's API can raise a 400 error because tools were not registered in API parameters,
    storing the actual output in 'failed_generation'.
    """
    failed_gen = None
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error", {})
        if isinstance(err, dict):
            failed_gen = err.get("failed_generation")

    if not failed_gen:
        # Check error string for failed_generation pattern
        err_str = str(exc)
        match = re.search(r"['\"]failed_generation['\"]\s*:\s*['\"](\{.*?\})['\"]", err_str)
        if match:
            try:
                failed_gen = match.group(1).encode("utf-8").decode("unicode_escape")
            except Exception:
                failed_gen = match.group(1)

    if not failed_gen:
        return None

    try:
        data = json.loads(failed_gen) if isinstance(failed_gen, str) else failed_gen
        if isinstance(data, dict):
            if "action" in data:
                return json.dumps(data)
            if "name" in data:
                args = data.get("arguments", data.get("args", {}))
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                return json.dumps({
                    "action": "call_tool",
                    "tool": data["name"],
                    "args": args if isinstance(args, dict) else {},
                })
    except Exception as parse_err:
        logger.warning("Failed to parse failed_generation JSON: %s", parse_err)

    return None


def generate_response(system_prompt: str, user_prompt: str) -> str:
    """Generate an LLM response using the configured provider, logging latency and token telemetry."""

    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        from groq import BadRequestError, Groq, NotFoundError

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        client = Groq(api_key=api_key)

        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

        # Models that support JSON mode in Groq (as of November 2026)
        # Reference: https://console.groq.com/docs/models
        # Note: llama3-8b-8192 and llama3-70b-8192 have been deprecated
        json_mode_supported_models = [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-safeguard-20b",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "qwen/qwen3.8-27b",
        ]

        # Check if current model supports JSON mode
        supports_json_mode = any(
            supported in model.lower()
            for supported in json_mode_supported_models
        )

        start_time = time.perf_counter()
        try:
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
            }

            # Only add response_format for models that support it
            if supports_json_mode:
                request_params["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**request_params)
            latency_ms = (time.perf_counter() - start_time) * 1000
            tokens = extract_token_usage(response)
            record_llm_metrics(latency_ms=latency_ms, tokens=tokens, provider="groq")

            logger.info(
                "Groq LLM call succeeded | latency_ms=%.2f | prompt_tokens=%d | completion_tokens=%d | total_tokens=%d",
                latency_ms,
                tokens["prompt_tokens"],
                tokens["completion_tokens"],
                tokens["total_tokens"],
            )

            return response.choices[0].message.content

        except NotFoundError as e:
            # Model not found or no access
            error_msg = str(e)
            raise RuntimeError(
                f"Groq model '{model}' not found or not accessible. "
                f"Please check your GROQ_MODEL configuration. Error: {error_msg}"
            ) from e

        except BadRequestError as e:
            # Check if this is a recoverable tool_use_failed error from Groq
            recovered = _recover_tool_call_from_groq_error(e)
            if recovered:
                latency_ms = (time.perf_counter() - start_time) * 1000
                tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                record_llm_metrics(latency_ms=latency_ms, tokens=tokens, provider="groq")
                logger.info(
                    "Recovered tool call from Groq tool_use_failed | latency_ms=%.2f",
                    latency_ms,
                )
                return recovered

            # Re-raise Groq API errors with clear message
            error_msg = str(e)
            if "json_validate_failed" in error_msg:
                raise RuntimeError(
                    f"Groq JSON validation failed. Model '{model}' may not support JSON mode. "
                    f"Error: {error_msg}"
                ) from e
            raise RuntimeError(f"Groq API request failed: {error_msg}") from e

    elif provider == "gemini":
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=api_key)

        start_time = time.perf_counter()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        tokens = extract_token_usage(response)
        record_llm_metrics(latency_ms=latency_ms, tokens=tokens, provider="gemini")

        logger.info(
            "Gemini LLM call succeeded | latency_ms=%.2f | prompt_tokens=%d | completion_tokens=%d | total_tokens=%d",
            latency_ms,
            tokens["prompt_tokens"],
            tokens["completion_tokens"],
            tokens["total_tokens"],
        )

        return response.text

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )
