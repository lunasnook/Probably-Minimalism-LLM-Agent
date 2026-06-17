import importlib
import pkgutil
from OpenAILLM import LLMAgent


def load_plugins(package_name):
    package = importlib.import_module(package_name)
    plugins = []
    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = f"{package_name}.{module_info.name}"
        module = importlib.import_module(module_name)
        if hasattr(module, "register"):
            plugin = module.register()
            plugins.append(plugin)
            print(f"- Loaded Plugin {module_name}")
    return plugins


def main():
    plugins= load_plugins("Core")
    # ======== begin on_init ========
    for plugin in plugins:
        plugin.on_init()
    # ======== end on_init ========

    run_config = {
        "URL": "http://localhost:11434/v1/",
        "API": "ollama",
        "MODEL": "gemma4:12b",
    }
    # ======== begin after_config ========
    for plugin in plugins:
        plugin.after_config()
    # ======== end after_config ========

    llmagent = LLMAgent(run_config)
    # ======== begin after_client ========
    for plugin in plugins:
        plugin.after_client(messages=llmagent.get_params("MESSAGES")["MESSAGES"])
    # ======== end after_client ========

    print("======== System ========")
    for msg in llmagent.get_params("MESSAGES")["MESSAGES"]:
        if msg.get("role") == "system":
            print(msg["content"])
            break
    global_message = ""
    while True:
        exit_flag = False
        user_input = input("======== Input ========\n")
        proceed = user_input.strip().lower()
        while proceed[0] == "/":
            if proceed == "/bye":
                exit_flag = True
                break
            else:
                continue
        if exit_flag:
            break
        # ======== begin after_input ========
        for plugin in plugins:
            plugin.after_input()
        # ======== end after_input ========

        llmagent.prompt_user(user_input)
        global_message = llmagent.execute()
        # ======== begin after_execute ========
        for plugin in plugins:
            plugin.after_execute()
        # ======== end after_execute ========
    # ======== begin after_loop ========
    for plugin in plugins:
        plugin.after_loop()
    # ======== end after_loop ========

    print(str(global_message))
    # ======== begin on_exit ========
    for plugin in plugins:
        plugin.on_exit()
    # ======== end on_exit ========


if __name__ == "__main__":
    main()

    # task-agent-(plugin)
    # rag-memory/profile-skill
    # (tool)-mcp

    # test
