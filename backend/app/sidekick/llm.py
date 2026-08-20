import litellm

MODEL = "openrouter/google/gemini-3.7-flash"

SYSTEM_PROMPT = """You are a sidekick helping an author understand their own story.

Answer the author's question using only the topics and themes given below as
context. Do not invent plot details that are not implied by this context. If
the context does not contain enough information to answer, say so plainly."""


def answer_question(question: str, topics: list[dict], themes: list[dict]) -> str:
    context_lines = [f"Theme: {t['title']} - {t['summary']}" for t in themes]
    context_lines += [f"Topic: {t['title']} - {t['summary']}" for t in topics]
    context = "\n".join(context_lines) if context_lines else "(no topics or themes in scope)"

    response = litellm.completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context}"},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content
