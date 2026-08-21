import json
import sqlite3

import litellm

from app.sidekick.tools import TOOL_SCHEMAS, execute_tool

MODEL = "openrouter/google/gemini-3.7-flash"
MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = """You are a sidekick helping an author understand and manage their own story.

Answer questions using only the topics, themes, and encoding rules given below
as context. Do not invent plot details that are not implied by this context.
If the context does not contain enough information to answer, say so plainly.

You can also perform actions using the available tools: excluding or
including a topic or theme, removing a topic from its theme, promoting a
theme to a subplot, reassigning a topic's act, and adding, editing, or
deleting encoding rules. Only call a tool when the author's message clearly
asks for that action on a specific, identifiable topic, theme, or rule from
the context below. After taking an action, briefly confirm what you did."""


def _build_context(topics: list[dict], themes: list[dict], encoding_rules: list[dict]) -> str:
    lines = [f"Theme (id={t['id']}): {t['title']} - {t['summary']}" for t in themes]
    lines += [
        f"Topic (id={t['id']}, theme_id={t['theme_id']}, act={t['act']}): {t['title']} - {t['summary']}"
        for t in topics
    ]
    lines += [
        f"Encoding rule (id={r['id']}) '{r['label']}': {r['style_kind']}, {r['block_length']}, "
        f"{r['position']} - {r['description']}"
        for r in encoding_rules
    ]
    return "\n".join(lines) if lines else "(no topics, themes, or encoding rules in scope)"


def answer_question(
    conn: sqlite3.Connection,
    question: str,
    topics: list[dict],
    themes: list[dict],
    encoding_rules: list[dict],
) -> tuple[str, list[str]]:
    context = _build_context(topics, themes, encoding_rules)
    messages: list[dict] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context}"},
        {"role": "user", "content": question},
    ]

    actions_taken: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = litellm.completion(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            return message.content, actions_taken

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in tool_calls
                ],
            }
        )
        for call in tool_calls:
            arguments = json.loads(call.function.arguments)
            result = execute_tool(conn, call.function.name, arguments)
            actions_taken.append(call.function.name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    return "I made some changes but ran out of turns to summarize them.", actions_taken
