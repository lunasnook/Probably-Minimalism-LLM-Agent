class BasePlugin:
    name = ""
    tools = []
    tool_funcs = {}

    def on_init(self, **kwargs):
        return

    def on_exit(self, **kwargs):
        return

    def after_config(self, **kwargs):
        return

    def after_client(self, **kwargs):
        return

    def after_execute(self, **kwargs):
        return

    def after_input(self, **kwargs):
        return

    def after_loop(self, **kwargs):
        return

    def before_tool(self, **kwargs):
        return

    def after_tool(self, **kwargs):
        return

    def multistep(self, **kwargs):
        return

    def system_message(self, **kwargs):
        return