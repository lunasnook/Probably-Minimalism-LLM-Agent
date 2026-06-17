from Core.BasePlugin import BasePlugin
import subprocess


class ShellPlugin(BasePlugin):
    name = "shell"

    @staticmethod
    def shell(command: str) -> str:
        print(f"Command to be executed: {command}, proceed? (y/n):")
        proceed = input().strip().lower()
        if proceed != "y":
            print("Command execution aborted.")
            return "Command execution aborted by user."
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += "[Error] " + result.stderr
            if not output.strip():
                output = "Command executed successfully with no output returned"
            print(output)
            return output
        except subprocess.TimeoutExpired:
            print("[Error] Maximum execution time exceeded.")
            return "[Error] Maximum execution time exceeded."
        except Exception as e:
            print(f"[Error] {str(e)}")
            return f"[Error] {str(e)}"
    tools = [
        {
            "type": "function",
            "function": {
                "name": "shell",
                "description": "This tool is used to execute shell commands on the system. Use this tool whenever functional operation is needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to be executed, e.g. 'ls -la' or 'echo hello'"
                        }
                    },
                    "required": ["command"]
                }
            }
        }
    ]
    tool_funcs = {"shell": shell.__func__}


def register():
    return ShellPlugin()
