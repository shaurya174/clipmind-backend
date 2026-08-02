"""
JSON Schemas used by the AI layer.

These schemas ensure that the AI always returns structured,
predictable responses.
"""

CHUNK_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "A concise title describing this section of the video."
        },
        "summary": {
            "type": "string",
            "description": "A detailed summary of what is discussed in this section."
        },
        "key_points": {
            "type": "array",
            "description": "The most important points covered in this section.",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "title",
        "summary",
        "key_points"
    ],
    "additionalProperties": False
}
FINAL_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_summary": {
            "type": "string",
            "description": "A concise but comprehensive summary of the entire video."
        },
        "key_takeaways": {
            "type": "array",
            "description": "The most important learnings from the entire video.",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "overall_summary",
        "key_takeaways"
    ],
    "additionalProperties": False
}
CHAT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "Answer to the user's question."
        },
        "used_transcript": {
            "type": "boolean",
            "description": "True if the transcript directly supported the answer."
        },
        "related_topic": {
            "type": "boolean",
            "description": "True if the question is related to the video's topic."
        },
        "sources": {
            "type": "array",
            "description": "Transcript timestamps used to answer.",
            "items": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string"
                    },
                    "end_time": {
                        "type": "string"
                    }
                },
                "required": [
                    "start_time",
                    "end_time"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "answer",
        "used_transcript",
        "related_topic",
        "sources"
    ],
    "additionalProperties": False
}
MIND_MAP_SCHEMA = {
    "type": "object",
    "properties": {
        "root": {
            "type": "string",
            "description": "The main topic of the video."
        },
        "nodes": {
            "type": "array",
            "description": "Hierarchical concept nodes for the mind map.",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique node identifier."
                    },
                    "parent": {
                        "type": ["string", "null"],
                        "description": "Parent node ID. Null for the root node."
                    },
                    "title": {
                        "type": "string",
                        "description": "Concept title displayed in the mind map."
                    },
                    "details": {
                        "type": "object",
                        "properties": {
                            "what_is_it": {
                                "type": "string",
                                "description": "Simple explanation of the concept."
                            },
                            "role_in_video": {
                                "type": "string",
                                "description": "How this concept is used or discussed in the video."
                            },
                            "how_it_is_used": {
                                "type": "string",
                                "description": "How the concept works or is applied."
                            },
                            "why_it_matters": {
                                "type": "string",
                                "description": "Why the concept is important."
                            },
                            "related_concepts": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Concepts closely related to this one."
                            }
                        },
                        "required": [
                            "what_is_it",
                            "role_in_video",
                            "how_it_is_used",
                            "why_it_matters",
                            "related_concepts"
                        ],
                        "additionalProperties": False
                    }
                },
                "required": [
                    "id",
                    "parent",
                    "title",
                    "details"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "root",
        "nodes"
    ],
    "additionalProperties": False
}