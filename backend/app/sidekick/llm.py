import json
import sqlite3

import litellm

from app.config import settings
from app.sidekick.tools import TOOL_SCHEMAS, execute_tool

MODEL = settings.sidekick_model
MAX_TOOL_ROUNDS = 4


def _complete(messages: list[dict]):
    options = {"reasoning_effort": settings.sidekick_reasoning_effort} if settings.sidekick_reasoning_effort else {}
    return litellm.completion(model=MODEL, messages=messages, tools=TOOL_SCHEMAS, **options)

SYSTEM_PROMPT = """You are a sidekick helping an author understand and manage their own story.

Answer questions using only the topics, themes, subplots, and encoding rules
given below as context. Do not invent plot details that are not implied by
this context. If the context does not contain enough information to answer,
say so plainly.

Every topic lives in exactly one place: the single Main theme, or a
subplot's own theme - there is no "unassigned" state. You can also perform
actions using the available tools: excluding or including a topic or
theme, reassigning a topic's act (opening, conflict, or climax - this
works for topics in any subplot too, since a subplot's act buckets come
from its topics' own act field), adding, editing, or deleting encoding
rules, and managing subplots. When the author wants to start a new
subplot (e.g. "create a subplot called X", "start a new subplot called
X"), call create_subplot with that title - this creates an empty subplot
with no topics yet. After calling create_subplot, tell the author it was
created and that they can now select which topics belong to it in the
app, then tell you when they're done - the app handles that selection
directly, so you do not need to call add_topic_to_subplot yourself after
this. Only use add_topic_to_subplot / remove_topic_from_subplot when the
author names a specific topic to add or remove some other time, outside
that selection flow. To move a topic into a specific existing theme by
id, use assign_topic_to_theme; to send a topic back to Main, use
remove_topic_from_theme. When the author wants to make a different theme
the story's Main theme (e.g. "make X the main plot", "switch the main
plot to X"), call set_main_theme with that theme's id - do not try to
achieve this by deleting subplots or reassigning topics yourself. The
theme marked [Main] in the context below is the current one.

Whenever the author asks you to find, search for, show, or list topics
matching some description (e.g. "find topics about the poison gas
theory", "show me topics mentioning Q", "unassigned topics", "topics in
subplot X"), you must call filter_topics with the ids of every matching
topic from the context above - do this instead of listing the matching
topics yourself in prose, even if you can already see which ones match.
This applies both to a plain search question and to the app's guided
add-topics flow when the "Adding topics to" line below is present -
either way, filter_topics does not change anything itself, it just
tells the app which topics to display so the author can examine, move,
edit, or (in the guided flow) pick from them. When the author asks to
delete one or more subplots by name, call delete_subplot for each one
named.

When the author describes a formatting pattern and what it means (e.g.
"multi-line italics at the start of a chapter is a dream sequence",
"bold text anywhere is a flashback"), call add_encoding_rule - infer
style_kind, block_length, and position from their description, and use
their stated meaning as the label. When they ask to remove, delete, or
get rid of an encoding rule by name or description (e.g. "delete the
dream sequence rule", "I don't need the flashback rule anymore"), call
delete_encoding_rule with that rule's id from the context below - this
permanently removes it for every document, which is the point when the
author is asking to declutter the rule list, not just hide it for one
document.

Use the "Current topic" / "Current theme" lines below to resolve phrases
like "the current topic" or "the current theme" to a specific id. Other
than filter_topics, only call a tool when the author's message clearly
asks for that action on a specific, identifiable topic, theme, subplot,
or rule from the context below. After taking an action, briefly confirm
what you did."""


def _build_context(
    topics: list[dict],
    themes: list[dict],
    encoding_rules: list[dict],
    subplots: list[dict],
    current_topic_id: int | None,
    current_theme_id: int | None,
    add_target_subplot_id: int | None = None,
    add_target_is_new: bool = False,
) -> str:
    lines = [
        f"Theme (id={t['id']}){' [Main]' if t.get('is_main') else ''}: {t['title']} - {t['summary']}"
        for t in themes
    ]
    lines += [
        f"Topic (id={t['id']}, theme_id={t['theme_id']}, act={t['act']}): {t['title']} - {t['summary']}"
        for t in topics
    ]
    lines += [
        f"Subplot (id={s['id']}, theme_id={s['theme_id']}, {'resolved' if s.get('resolved') else 'open'}): "
        f"{s['title']} - topics: {s.get('topic_ids', [])}"
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
    if add_target_is_new:
        lines.append("Adding topics to: a new subplot not created yet")
    elif add_target_subplot_id is not None:
        lines.append(f"Adding topics to: subplot id={add_target_subplot_id}")
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
    add_target_subplot_id: int | None = None,
    add_target_is_new: bool = False,
    story_id: int | None = None,
) -> tuple[str, list[str], int | None, list[int] | None]:
    context = _build_context(
        topics,
        themes,
        encoding_rules,
        subplots,
        current_topic_id,
        current_theme_id,
        add_target_subplot_id,
        add_target_is_new,
    )
    messages: list[dict] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context}"},
        {"role": "user", "content": question},
    ]

    actions_taken: list[str] = []
    created_subplot_id: int | None = None
    filtered_topic_ids: list[int] | None = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = _complete(messages)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            return message.content, actions_taken, created_subplot_id, filtered_topic_ids

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
            if call.function.name == "create_subplot":
                arguments["story_id"] = story_id
            result = execute_tool(conn, call.function.name, arguments)
            actions_taken.append(call.function.name)
            if call.function.name == "create_subplot" and isinstance(result, dict) and "id" in result:
                created_subplot_id = result["id"]
            if call.function.name == "filter_topics" and isinstance(result, list):
                filtered_topic_ids = [t["id"] for t in result]
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str),
                }
            )

        # A filter only selects topics for the UI; a second model call just to describe it costs seconds.
        if filtered_topic_ids is not None and all(call.function.name == "filter_topics" for call in tool_calls):
            count = len(filtered_topic_ids)
            answer = message.content or f"Found {count} matching topic{'' if count == 1 else 's'}."
            return answer, actions_taken, created_subplot_id, filtered_topic_ids

    return (
        "I made some changes but ran out of turns to summarize them.",
        actions_taken,
        created_subplot_id,
        filtered_topic_ids,
    )
