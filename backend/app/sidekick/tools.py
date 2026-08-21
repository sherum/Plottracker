import sqlite3
from typing import Any, Callable

from app.db import repository

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "set_topic_excluded",
            "description": "Exclude or include a topic. Excluded topics are hidden from the plot view and from your own context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {"type": "integer"},
                    "excluded": {"type": "boolean"},
                },
                "required": ["topic_id", "excluded"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_theme_excluded",
            "description": "Exclude or include a theme.",
            "parameters": {
                "type": "object",
                "properties": {
                    "theme_id": {"type": "integer"},
                    "excluded": {"type": "boolean"},
                },
                "required": ["theme_id", "excluded"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "promote_theme_to_subplot",
            "description": "Promote a theme to a subplot, carrying its current topics along.",
            "parameters": {
                "type": "object",
                "properties": {"theme_id": {"type": "integer"}},
                "required": ["theme_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_subplot_from_theme",
            "description": (
                "Create a new, empty subplot from a theme with a custom title, linked to that theme "
                "but without carrying over its topics. Use this when the author names the subplot "
                "explicitly, so they can add specific topics to it afterward with add_topic_to_subplot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "theme_id": {"type": "integer"},
                    "title": {"type": "string"},
                },
                "required": ["theme_id", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_topic_to_subplot",
            "description": "Add a topic to an existing subplot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subplot_id": {"type": "integer"},
                    "topic_id": {"type": "integer"},
                },
                "required": ["subplot_id", "topic_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_topic_from_subplot",
            "description": "Remove a topic from a subplot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subplot_id": {"type": "integer"},
                    "topic_id": {"type": "integer"},
                },
                "required": ["subplot_id", "topic_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_subplot",
            "description": "Permanently delete a subplot (its topic memberships too, not the topics themselves).",
            "parameters": {
                "type": "object",
                "properties": {"subplot_id": {"type": "integer"}},
                "required": ["subplot_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_topics",
            "description": (
                "Report which topics (from the context above) match a filter the author described, e.g. "
                "'unassigned topics', 'topics in subplot X', 'topics starting with Q'. This does not change "
                "anything - it just tells the app which topic ids to show the author so they can pick from "
                "them. Pass the ids of every topic that matches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["topic_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_topic_from_theme",
            "description": "Unassign a topic from its theme, without excluding it.",
            "parameters": {
                "type": "object",
                "properties": {"topic_id": {"type": "integer"}},
                "required": ["topic_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_topic_act",
            "description": "Move a topic to a different act of the three-act structure, or unassign its act.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {"type": "integer"},
                    "act": {
                        "type": "string",
                        "enum": ["opening", "conflict", "climax", "unassigned"],
                        "description": "Use 'unassigned' to clear the topic's act.",
                    },
                },
                "required": ["topic_id", "act"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_encoding_rule",
            "description": "Add a new encoding rule describing what an author-defined text style means (e.g. italic means a dream sequence).",
            "parameters": {
                "type": "object",
                "properties": {
                    "style_kind": {"type": "string", "description": "e.g. italic, bold, highlight"},
                    "block_length": {"type": "string", "enum": ["single", "multi"]},
                    "position": {"type": "string", "enum": ["chapter_start", "anywhere"]},
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["style_kind", "block_length", "position", "label"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_encoding_rule",
            "description": "Edit an existing encoding rule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rule_id": {"type": "integer"},
                    "style_kind": {"type": "string"},
                    "block_length": {"type": "string", "enum": ["single", "multi"]},
                    "position": {"type": "string", "enum": ["chapter_start", "anywhere"]},
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["rule_id", "style_kind", "block_length", "position", "label"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_encoding_rule",
            "description": "Delete an encoding rule.",
            "parameters": {
                "type": "object",
                "properties": {"rule_id": {"type": "integer"}},
                "required": ["rule_id"],
            },
        },
    },
]


def _set_topic_excluded(conn: sqlite3.Connection, args: dict) -> Any:
    return repository.set_topic_excluded(conn, args["topic_id"], args["excluded"])


def _set_theme_excluded(conn: sqlite3.Connection, args: dict) -> Any:
    return repository.set_theme_excluded(conn, args["theme_id"], args["excluded"])


def _promote_theme_to_subplot(conn: sqlite3.Connection, args: dict) -> Any:
    subplot_id = repository.promote_theme_to_subplot(conn, args["theme_id"])
    return repository.get_subplot(conn, subplot_id)


def _create_subplot_from_theme(conn: sqlite3.Connection, args: dict) -> Any:
    subplot_id = repository.create_named_subplot_from_theme(conn, args["theme_id"], args["title"])
    return repository.get_subplot(conn, subplot_id)


def _add_topic_to_subplot(conn: sqlite3.Connection, args: dict) -> Any:
    repository.add_topic_to_subplot(conn, args["subplot_id"], args["topic_id"])
    return repository.get_subplot(conn, args["subplot_id"])


def _remove_topic_from_subplot(conn: sqlite3.Connection, args: dict) -> Any:
    repository.remove_topic_from_subplot(conn, args["subplot_id"], args["topic_id"])
    return repository.get_subplot(conn, args["subplot_id"])


def _delete_subplot(conn: sqlite3.Connection, args: dict) -> Any:
    repository.delete_subplot(conn, args["subplot_id"])
    return {"deleted": args["subplot_id"]}


def _filter_topics(conn: sqlite3.Connection, args: dict) -> Any:
    return repository.get_topics_by_ids(conn, args["topic_ids"])


def _remove_topic_from_theme(conn: sqlite3.Connection, args: dict) -> Any:
    return repository.unassign_topic_theme(conn, args["topic_id"])


def _set_topic_act(conn: sqlite3.Connection, args: dict) -> Any:
    act = args["act"]
    return repository.set_topic_act(conn, args["topic_id"], None if act == "unassigned" else act)


def _add_encoding_rule(conn: sqlite3.Connection, args: dict) -> Any:
    rule_id = repository.insert_encoding_rule(
        conn,
        style_kind=args["style_kind"],
        block_length=args["block_length"],
        position=args["position"],
        label=args["label"],
        description=args.get("description", ""),
    )
    return {"id": rule_id, **args}


def _update_encoding_rule(conn: sqlite3.Connection, args: dict) -> Any:
    return repository.update_encoding_rule(
        conn,
        args["rule_id"],
        style_kind=args["style_kind"],
        block_length=args["block_length"],
        position=args["position"],
        label=args["label"],
        description=args.get("description", ""),
    )


def _delete_encoding_rule(conn: sqlite3.Connection, args: dict) -> Any:
    repository.delete_encoding_rule(conn, args["rule_id"])
    return {"deleted": args["rule_id"]}


TOOL_FUNCTIONS: dict[str, Callable[[sqlite3.Connection, dict], Any]] = {
    "set_topic_excluded": _set_topic_excluded,
    "set_theme_excluded": _set_theme_excluded,
    "promote_theme_to_subplot": _promote_theme_to_subplot,
    "create_subplot_from_theme": _create_subplot_from_theme,
    "add_topic_to_subplot": _add_topic_to_subplot,
    "remove_topic_from_subplot": _remove_topic_from_subplot,
    "delete_subplot": _delete_subplot,
    "filter_topics": _filter_topics,
    "remove_topic_from_theme": _remove_topic_from_theme,
    "set_topic_act": _set_topic_act,
    "add_encoding_rule": _add_encoding_rule,
    "update_encoding_rule": _update_encoding_rule,
    "delete_encoding_rule": _delete_encoding_rule,
}


def execute_tool(conn: sqlite3.Connection, name: str, arguments: dict) -> Any:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return func(conn, arguments)
    except Exception as exc:
        return {"error": str(exc)}
