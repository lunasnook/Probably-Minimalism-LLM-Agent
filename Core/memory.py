from Core.BasePlugin import BasePlugin

MEMORY_FILE = "Core/memory.txt"


class MemoryPlugin(BasePlugin):
    name = "memory"

    def after_client(self, **kwargs):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            content = ""
        if not content:
            return
        messages = kwargs.get("messages")
        if messages:
            for msg in messages:
                if msg.get("role") == "system":
                    msg["content"] += (
                        "\n======== Memory ========\n"
                        + content
                    )
                    break

    @staticmethod
    def update_memory(start: int, end: int, content: str) -> str:
        try:
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    old = f.read()
            except FileNotFoundError:
                old = ""
            new = old[:start] + content + old[end:]
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                f.write(new)
            print(f"Memory updated [{start}:{end}] -> '{content}'")
            return f"Memory updated [{start}:{end}] -> '{content}'"
        except Exception as e:
            print(f"[Error] Memory error {e}")
            return f"[Error] Failed to update memory {e}"
    tools = [
        {
            "type": "function",
            "function": {
                "name": "update_memory",
                "description": (
                    "Update long-term memory by replacing text at a specific position range."
                    "The full current memory is in the system prompt."
                    "To ADD at a position: set start and end to the same index, content to the new text."
                    "To DELETE a range: set content to empty string."
                    "To MODIFY: set start and end to the range to replace, content to the new text."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "integer",
                            "description": "Start character index (inclusive, 0-based)",
                        },
                        "end": {
                            "type": "integer",
                            "description": "End character index (exclusive, 0-based)",
                        },
                        "content": {
                            "type": "string",
                            "description": "The replacement text",
                        },
                    },
                    "required": ["start", "end", "content"],
                },
            },
        }
    ]
    tool_funcs = {"update_memory": update_memory.__func__}


def register():
    return MemoryPlugin()