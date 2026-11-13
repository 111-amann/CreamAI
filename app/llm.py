
import os

from dotenv import load_dotenv

load_dotenv()


def generate_response(system_prompt: str, user_prompt: str) -> str:
    """Generate an LLM response using the configured provider."""

    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=os.getenv(
                "GROQ_MODEL",
                "llama-3.3-70b-versatile"
            ),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content

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
