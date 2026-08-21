import json
import sqlite3

import litellm

from app.sidekick.tools import TOOL_SCHEMAS, execute_tool

MODEL = "openrouter/google/gemini-3.7-flash"
MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = """You are a sidekick helping an author understand and manage their own story.

Answer questions using only the topics, themes, subplots, and encoding rules
given below as context. Do not invent plot details that are not implied by
this context. If the context does not contain enough information to answer,
say so plainly.

You can also perform actions using the available tools: excluding or
including a topic or theme, removing a topic from its theme, reassigning a
topic's act, adding, editing, or deleting encoding rules, and managing
subplots. When the author says "promote the current theme" (or "promote
this theme"), call promote_theme_to_subplot with the current theme's id to
carry all of its topics into a new subplot. When the author instead gives
the new subplot an explicit name, e.g. "promote the current theme with
name X", call create_subplot_from_theme with that title instead - this
creates an empty subplot linked to the theme with no topics yet. After
calling create_subplot_from_theme, tell the author the subplot was created
and that they can now select which topics belong to it in the app, then
tell you when they're done - the app handles that selection directly, so
you do not need to call add_topic_to_subplot yourself after this. Only use
add_topic_to_subplot / remove_topic_from_subplot when the author names a
specific topic to add or remove some other time, outside that selection
flow. Use the "Current topic" / "Current theme" lines below to resolve
phrases like "the current topic" or "the current theme" to a specific id.
Only call a tool when the author's message clearly asks for that action on
a specific, identifiable topic, theme, subplot, or rule from the context
below. After taking an action, briefly confirm what you did."""


def _build_context(
    topics: list[dict],
    themes: list[dict],
    encoding_rules: list[dict],
    subplots: list[dict],
    current_topic_id: int | None,
    current_theme_id: int | None,
) -> str:
    lines = [f"Theme (id={t['id']}): {t['title']} - {t['summary']}" for t in themes]
    lines += [
        f"Topic (id={t['id']}, theme_id={t['theme_id']}, act={t['act']}): {t['title']} - {t['summary']}"
        for t in topics
    ]
    lines += [
        f"Subplot (id={s['id']}, theme_id={s['theme_id']}): {s['title']} - {s['topic_count']} topics"
        for s in subplots
    ]
    lines += [
        f"Encoding rule (id={r['id']}) '{r['label']}': {r['style_kind']}, {r['block_length']}, "
        f"{r['position']} - {r['description']}"
        for r in encoding_rules
    ]
    if current_topic_id is not None:
        lines.append(f'Current topic: id={current_topic_id} (this is what "the current topic" refers to)')
    if current_theme_id is not None:
        lines.append(f'Current theme: id={current_theme_id} (this is what "the current theme" refers to)')
    return "\n".join(lines) if lines else "(no topics, themes, subplots, or encoding rules in scope)"


def answer_question(
    conn: sqlite3.Connection,
    question: str,
    topics: list[dict],
    themes: list[dict],
    encoding_rules: list[dict],
    subplots: list[dict],
    current_topic_id: int | None = None,
    current_theme_id: int | None = None,
) -> tuple[str, list[str], int | None]:
    context = _build_context(topics, themes, encoding_rules, subplots, current_topic_id, current_theme_id)
    messages: list[dict] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context}"},
        {"role": "user", "content": question},
    ]

    actions_taken: list[str] = []
    created_subplot_id: int | None = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = litellm.completion(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            return message.content, actions_taken, created_subplot_id

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
            if call.function.name == "create_subplot_from_theme" and isinstance(result, dict) and "id" in result:
                created_subplot_id = result["id"]
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    return "I made some changes but ran out of turns to summarize them.", actions_taken, created_subplot_id
