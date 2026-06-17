import argparse
import copy
import importlib
import pkgutil
import json
from openai import OpenAI


# ======== 参数 ========
parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="")
parser.add_argument("--api-key", default="")
parser.add_argument("--model", default="")
parser.add_argument("--system", default="")
parser.add_argument("--user", default="")
parser.add_argument("--stream", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--think", action=argparse.BooleanOptionalAction, default=True)
# 思考预算：OpenAI/o 系列走 effort，Claude 走 max_tokens
parser.add_argument("--reasoning-effort", choices=["low", "medium", "high"], default="medium")
parser.add_argument("--reasoning-tokens", type=int, default=10000)
parser.add_argument("--showthink", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--includethink", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--temp", type=float, default=1.0)
parser.add_argument("--topp", type=float, default=0.95)
parser.add_argument("--topk", type=int, default=64)
parser.add_argument("--structure", choices=["NONE", "json", "schema"], default="NONE")
parser.add_argument("--schema", default=None)
parser.add_argument("--tool-use", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--tool-choice", choices=["auto", "none", "required"], default="auto")
# 若要强制调用某个具体函数，用这个（优先级高于上面）
parser.add_argument("--force-tool", default=None)
parser.add_argument("--multistep", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--messages", default=None)
args = parser.parse_args()
# ======== 参数 ========
DEFAULT_CONFIG = {
    "URL" : args.base_url,
    "API" : args.api_key,
    "MODEL" : args.model,
    "SYSTEM" : args.system,
    "USER" : args.user,
    "STREAM" : args.stream,
    "THINK" : args.think,
    "REFFORT" : args.reasoning_effort,
    "RTOKEN" : args.reasoning_tokens,
    "SHOWTHINK" : args.showthink,
    "INCLUDETHINK" : args.includethink,
    "TEMP" : args.temp,
    "TOPP" : args.topp,
    "TOPK" : args.topk,
    "LSTRUCTURE" : args.structure,
    "SCHEMA" : args.schema,
    "TOOL_USE" : args.tool_use,
    "TCHOICE" : args.tool_choice,
    "TFORCE" : args.force_tool,
    "MULTISTEP" : args.multistep,
    "MESSAGES" : args.messages,
    "THINK_TOKEN" : "======== Think ========",
    "ANSWER_TOKEN" : "======== Answer ========",
    "FUNCTION_TOKEN" : "======== TOOL ========",
    "RESULT_TOKEN" : "======== RESULT ========",
}
# ======== 参数 ========


def load_plugins(package_name):
    package = importlib.import_module(package_name)
    plugins = []
    tools = []
    tool_funcs = {}
    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = f"{package_name}.{module_info.name}"
        module = importlib.import_module(module_name)
        if hasattr(module, "register"):
            plugin = module.register()
            if hasattr(plugin, 'tools'):
                tools.extend(plugin.tools)
            if hasattr(plugin, 'tool_funcs'):
                tool_funcs.update(plugin.tool_funcs)
            plugins.append(plugin)
            print(f"- Loaded Plugin {module_name}")
    return plugins, tools, tool_funcs


class LLMAgent:
    def __init__(self, config: dict | None = None):
        config = config or {}
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(config)
        for key, value in cfg.items():
            setattr(self, key, value)
        if self.LSTRUCTURE == "schema":
            def schema_prompt(schema, prefix=""):
                lines = []
                for k, v in schema.get("properties", {}).items():
                    path = f"{prefix}.{k}" if prefix else k
                    lines.append(f"- {path}: {v.get('description', '')}")
                    if v.get("type") == "object":
                        lines += schema_prompt(v, path)
                    if v.get("type") == "array" and v.get("items", {}).get("type") == "object":
                        lines += schema_prompt(v["items"], path + "[]")
                return lines
            self.SYSTEM += "\n".join(schema_prompt(self.SCHEMA))
        if self.MESSAGES is None:
            self.MESSAGES = [{'role': 'system', 'content': self.SYSTEM}]
            if self.USER != "":
                self.MESSAGES.append({'role': 'assistant', 'content': self.USER})
        self.plugins, self.tools,  self.tool_funcs = load_plugins("Core")
        self.client = OpenAI(base_url=self.URL, api_key=self.API)

    def get_params(self, *args):
        result = {}
        for key in args:
            if not hasattr(self, key):
                raise AttributeError(f"Unknown parameter: {key}")
            result[key] = getattr(self, key)
        return result

    def set_params(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Unknown parameter: {key}")
            setattr(self, key, value)
            if key == "URL" or key == "API":
                self.client = OpenAI(base_url=self.URL, api_key=self.API)
        return self

    def llm_print_wrapper(self, content, *args, **kwargs):
        print(content, *args, **kwargs)

    def prompt_user(self, content):
        self.MESSAGES.append({'role': 'user', 'content': content})

    def execute(self):
        # 处理参数
        def build_kwargs():
            kwargs = {
                "model": self.MODEL,
                "messages": self.MESSAGES,
                "stream": self.STREAM,
                "temperature": self.TEMP,
                "top_p": self.TOPP,
            }
            extra_body = {}
            if self.THINK:
                m = self.MODEL.lower()
                if any(k in m for k in ("gpt-5", "/o1", "/o3", "/o4")):
                    # OpenAI / o 系列：effort 风格
                    extra_body["reasoning"] = {"effort": self.REFFORT}
                elif "claude" in m:
                    # Anthropic 扩展思考：token 预算风格
                    extra_body["reasoning"] = {"max_tokens": self.RTOKEN}
                else:
                    # 通用兜底（Qwen / DeepSeek / 等）
                    extra_body["reasoning"] = {"enabled": True}
                if not self.SHOWTHINK:
                    extra_body["reasoning"]["exclude"] = True
            extra_body["top_k"] = self.TOPK
            kwargs["extra_body"] = extra_body
            if self.LSTRUCTURE == "json":
                kwargs["response_format"] = {"type": "json_object"}
            elif self.LSTRUCTURE == "schema":
                schema = copy.deepcopy(self.SCHEMA)
                schema["additionalProperties"] = False
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "JSONSCHEMA",
                        "schema": schema,
                        "strict": True,
                    },
                }
            if self.TOOL_USE:
                kwargs["tools"] = self.tools
                if self.TFORCE:
                    kwargs["tool_choice"] = {
                        "type": "function",
                        "function": {"name": self.TFORCE},
                    }
                else:
                    kwargs["tool_choice"] = self.TCHOICE
            return kwargs
        client_kwargs = build_kwargs()

        def get_reasoning(delta_or_msg):
            # 兼容 OpenRouter(reasoning) / DeepSeek(reasoning_content)，以及 OpenAI SDK 把非标准字段塞进 model_extra 的情况
            for attr in ("reasoning", "reasoning_content"):
                v = getattr(delta_or_msg, attr, None)
                if v:
                    return v
            extra = getattr(delta_or_msg, "model_extra", None) or {}
            return extra.get("reasoning") or extra.get("reasoning_content")


        # 工具调用
        def function_calling(tool_calls):
            # ======== begin before_tool ========
            for plugin in self.plugins:
                plugin.before_tool()
            # ======== end before_tool ========
            for call in tool_calls:
                func_name = call["function"]["name"]
                func_args = call["function"]["arguments"]
                self.llm_print_wrapper(self.FUNCTION_TOKEN + " " + func_name + " " + func_args)
                try:
                    func_args = json.loads(call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    func_args = {}
                tool_function = self.tool_funcs.get(func_name)
                if tool_function and callable(tool_function):
                    result = tool_function(**func_args)
                else:
                    result = f"unknown tool: {func_name}"
                self.llm_print_wrapper(self.RESULT_TOKEN + " " + result)
                self.MESSAGES.append({
                    'role': 'tool',
                    'tool_call_id': call["id"],
                    'content': str(result),
                })
            # ======== begin after_tool ========
            for plugin in self.plugins:
                plugin.after_tool()
            # ======== end after_tool ========


        # 运行及输出
        while True:
            # ======== 运行 ========
            response = self.client.chat.completions.create(**client_kwargs)
            # ======== 运行 ========
            if self.STREAM:
                in_thinking = False
                answer_line = True
                thinking = ''
                content = ''
                tool_buffer = {} # index -> {id, type, function:{name, arguments}}
                for chunk in response:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if self.THINK and get_reasoning(delta):
                        if not in_thinking:
                            in_thinking = True
                            self.llm_print_wrapper(self.THINK_TOKEN + '\n', end='', flush=True)
                        self.llm_print_wrapper(get_reasoning(delta), end='', flush=True)
                        thinking += get_reasoning(delta)
                    if delta.content: # content
                        if in_thinking or answer_line:
                            in_thinking = False
                            answer_line = False
                            self.llm_print_wrapper('\n' + self.ANSWER_TOKEN + '\n', end='', flush=True)
                        self.llm_print_wrapper(delta.content, end='', flush=True)
                        content += delta.content
                    if self.TOOL_USE and delta.tool_calls: # tool call
                        for tc in delta.tool_calls:
                            idx = tc.index
                            slot = tool_buffer.setdefault(idx, {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            })
                            if tc.id:
                                slot["id"] = tc.id
                            if tc.function and tc.function.name:
                                slot["function"]["name"] = tc.function.name
                            if tc.function and tc.function.arguments:
                                slot["function"]["arguments"] += tc.function.arguments
                self.llm_print_wrapper('\n')
                if self.INCLUDETHINK:
                    self.MESSAGES.append({'role': 'assistant', 'content': thinking})
                self.MESSAGES.append({'role': 'assistant', 'content': content}) # MESSAGE
                if self.TOOL_USE:
                    tool_called = [tool_buffer[i] for i in sorted(tool_buffer)]
                    if tool_called:
                        self.MESSAGES.append({'role': 'assistant', 'tool_calls': tool_called})
                        function_calling(tool_called)
                    else: # tool call
                        break
                if not self.MULTISTEP:
                    break
                else:
                    # ======== begin multistep ========
                    for plugin in self.plugins:
                        plugin.multistep()
                    # ======== end multistep ========
            else:
                message = response.choices[0].message
                if self.THINK and get_reasoning(message):
                    self.llm_print_wrapper(self.THINK_TOKEN + '\n' + get_reasoning(message) + '\n')
                    if self.INCLUDETHINK:
                        self.MESSAGES.append({'role': 'assistant', 'content': get_reasoning(message)})
                self.llm_print_wrapper(self.ANSWER_TOKEN + '\n' + content + '\n')
                self.MESSAGES.append({'role': 'assistant', 'content': message.content})
                if self.TOOL_USE:
                    if message.tool_calls:
                        assistant_message = {'role': 'assistant'}
                        assistant_message['tool_calls'] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ]
                        self.MESSAGES.append(assistant_message)
                        function_calling(assistant_message['tool_calls'])
                    else:
                        break
                if not self.MULTISTEP:
                    break
                else:
                    # ======== begin multistep ========
                    for plugin in self.plugins:
                        plugin.multistep()
                    # ======== end multistep ========

        return self.MESSAGES

if __name__ == "__main__":
    llmagent = LLMAgent()
    global_message = llmagent.execute()
    print(str(global_message))
