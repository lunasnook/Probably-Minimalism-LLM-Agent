from Core.BasePlugin import BasePlugin


class OptionsPlugin(BasePlugin):
    name = "options"

    @staticmethod
    def options(options: list[str]) -> str:
        i = 0
        for option in options:
            i += 1
            print("Option " + str(i) + ": " + option)
        iiput = input("Input: ")
        return iiput
    tools = [
        {
            "type": "function",
            "function": {
                "name": "options",
                "description": "This tool is used for users to choose from a list of options to answer questions or clarify demands."
                               "Users can also enter questions or answers manually. Use this tool whenever a response or feedback is needed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of options for users to choose from",
                        }
                    },
                    "required": ["options"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    tool_funcs = {"options": options.__func__}


def register():
    return OptionsPlugin()
