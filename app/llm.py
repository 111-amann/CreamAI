
import os

from dotenv import load_dotenv

load_dotenv()


def generate_response(system_prompt: str, user_prompt: str) -> str:
    """Generate an LLM response using the configured provider."""

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
            return response.choices[0].message.content

        except NotFoundError as e:
            # Model not found or no access
            error_msg = str(e)
            raise RuntimeError(
                f"Groq model '{model}' not found or not accessible. "
                f"Please check your GROQ_MODEL configuration. Error: {error_msg}"
            ) from e

        except BadRequestError as e:
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

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        return response.text

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )
