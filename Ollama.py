import argparse
from ollama import chat
from pydantic import BaseModel, Field
parser = argparse.ArgumentParser()

# 设置
THINK_TOKEN = "思考："
ANSWER_TOKEN = "回答："
USER = input("输入：")
# ======== 参数 ========
parser.add_argument("--model", default="gemma4:12b")
parser.add_argument("--system", default="")
parser.add_argument("--stream", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--think", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--temp", type=float, default=1.0)
parser.add_argument("--topp", type=float, default=0.95)
parser.add_argument("--topk", type=int, default=64)
parser.add_argument("--structure", choices=["NONE", "json", "schema"], default="NONE")
parser.add_argument("--tool-use", action=argparse.BooleanOptionalAction, default=True)
args = parser.parse_args()
# ======== 参数 ========
class JSONANSWER(BaseModel):
    a: int = Field(..., description="填最喜欢的数字")
    b: list[str] = Field(..., description="最喜欢的水果")
def options(options: list[str]) -> str:
    """用于让用户从一系列选项中选择来回答问题或澄清诉求，用户也可以自行输入问题或答案"""
    i = 0
    print('\n')
    for option in options:
        i += 1
        print("选项"+str(i)+"：" + option)
    iiput = input("选择：")
    return iiput
TOOLS = [options]

# 处理参数
MODEL = args.model
SYSTEM = args.system
STRUCTURE = args.structure
if STRUCTURE == "schema":
    SYSTEM += "\n".join(
        f"{k}:{v.description}"
        for k, v in JSONANSWER.model_fields.items()
        if v.description
    )
MESSAGES = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': USER}]
STREAM = args.stream
THINK = args.think
TEMP = args.temp
TOPP = args.topp
TOPK = args.topk
ARGUS = {'temperature': TEMP, 'top_p': TOPP, 'top_k': TOPK}
TOOL_USE = args.tool_use
while True:
    KWARGS = {
            "model":MODEL,
            "messages":MESSAGES,
            "stream":STREAM,
            "think":THINK,
            "options":ARGUS,
        }
    if STRUCTURE == "json":
        KWARGS["format"] = "json"
    elif STRUCTURE == "schema":
        KWARGS["format"] = JSONANSWER.model_json_schema()
    if TOOL_USE:
        KWARGS["tools"] = TOOLS
    
# 聊天与工具调用
    response = chat(**KWARGS)
    def function_calling(tool_body):
        for call in tool_body:
            func_name = call.function.name
            func_args = call.function.arguments
            tool_function = globals().get(func_name)
            if tool_function and callable(tool_function):
                result = tool_function(**func_args)
            else:
                result = f"unknown tool: {func_name}"
            tool_content = {
                    'role': 'tool',
                    'tool_name': call.function.name,
                    'content': str(result)
                }
            MESSAGES.append(tool_content)
    
# 输出
    if STREAM:
        in_thinking = False
        thinking = ''
        content = ''
        tool_called = []
        for chunk in response:
            if chunk.message.thinking:
                if not in_thinking:
                    in_thinking = True
                    print(THINK_TOKEN+'\n', end='', flush=True)
                print(chunk.message.thinking, end='', flush=True)
                thinking += chunk.message.thinking
            if chunk.message.content:
                if in_thinking:
                    in_thinking = False
                    print('\n'+ANSWER_TOKEN+'\n', end='', flush=True)
                print(chunk.message.content, end='', flush=True)
                content += chunk.message.content
            if chunk.message.tool_calls:
                tool_called.extend(chunk.message.tool_calls)
        assistant_message = {
            'role': 'assistant',
            'content': content,
        }
        if tool_called:
            assistant_message['tool_calls'] = tool_called
        MESSAGES.append(assistant_message)
        if not tool_called:
            break
        if TOOL_USE:
            function_calling(tool_called)
    else:
        if THINK:
            thinking = response.message.thinking
            print(THINK_TOKEN+'\n' + thinking)
        content = response.message.content
        print('\n'+ANSWER_TOKEN+'\n' + content)
        assistant_message = {
            'role': 'assistant',
            'content': content,
        }
        if response.message.tool_calls:
            assistant_message['tool_calls'] = response.message.tool_calls
        MESSAGES.append(assistant_message)
        if not response.message.tool_calls:
            break
        if TOOL_USE:
            function_calling(response.message.tool_calls)
# debug
print('\n' + str(MESSAGES) + '\n')

        
# jsonanswer = JSONANSWER.model_validate_json(content)
# print(jsonanswer)
