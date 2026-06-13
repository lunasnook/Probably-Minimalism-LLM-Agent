# Probably-Minimalism-LLM-Agent
(大概是)最简约的语言模型代理

# Ollama.py 使用指南
## 1. 介绍
这是一个基于 [Ollama Python SDK](https://github.com/ollama/ollama-python) 的命令行聊天脚本，通过调用 Ollama 本地大语言模型来实现LLM Agent。支持的功能有：

- 命令行参数传递
- 本地模型选择及加载
- 可自定义系统指示
- 流式传输开关
- 思考模式开关
- 可定义温度、Top-p采样、Top-k采样参数
- 可强制输出json格式，或用json schema引导输出格式
- 可调用自定义工具
- 单次回答可调用多个工具(Parallel tool calling)
- 多轮工具调用以完成复杂任务(Multi-turn tool calling, Agent loop)
- 142行代码实现单轮会话，方便在其基础上扩充多轮会话、Memory、MCP、Skills等功能
- ~~_古法编程浓度88.03%_~~

本项目建立在 [Ollama 文档](https://docs.ollama.com) 所示代码的基础上
## 2. 安装指南
### 克隆仓库

```
git clone https://github.com/lunasnook/Probably-Minimalism-LLM-Agent.git
cd Probably-Minimalism-LLM-Agent
python3 -m venv venv
source venv/bin/activate
```
### 安装依赖项
1. 确保安装了Python3.10或更高版本
2. 安装Ollama
3. 安装Ollama Python SDK及Pydantic：

    `pip install ollama pydantic`
### 准备模型
1. 下载并安装所需模型，例如 `gemma4:12b`，`qwen3.5:9b`等。以本脚本默认模型`gemma4:12b`为例：

    `ollama pull gemma4:12b`
### 开始使用
1. 运行

    `python3 Ollama.py`
2. 若一切顺利，命令行上应显示`输入：`
## 3. 使用说明
### 命令行参数
| 参数 |           默认 | 说明                                |
|---|-------------:|-----------------------------------|
| `--model` | `gemma4:12b` | 使用的 Ollama 模型                     |
| `--system` |         `""` | 系统提示词                             |
| `--stream` / `--no-stream` |       `True` | 是否启用流式输出                          |
| `--think` / `--no-think` |       `True` | 是否启用思考模式并输出                       |
| `--temp` |        `1.0` | 温度参数，控制随机性                        |
| `--topp` |       `0.95` | Top-p 采样参数                        |
| `--topk` |         `64` | Top-k 采样参数                        |
| `--structure` |       `NONE` | 结构化输出模式，可选 `NONE`、`json`、`schema` |
| `--tool-use` / `--no-tool-use` |       `True` | 是否启用工具调用                          |
### 完整示例

    `python3 Ollama.py --model gemma4:12b --system "" --stream --think --temp 1.0 --topp 0.95 --topk 64 --structure "NONE" --tool-use`
### 结构化输出说明
本脚本支持三种结构化输出模式：
- `NONE`：不进行结构化输出，直接输出文本
- `json`：将输出结果转换为任意json格式
- `schema`：将输出结果转换为指定的json schema格式

请定位至代码第22～24行修改默认的json schema格式。以
```python
class JSONANSWER(BaseModel):
    a: int = Field(..., description="填最喜欢的数字")
    b: list[str] = Field(..., description="最喜欢的水果")
```
为例，`a`、`b`为需要的json字段的变量名，`int`、`list[str]`各字段的所需类型，description则告诉模型该字段的含义或如何填写
### 工具调用说明
请在任意地方加上所需实现的函数功能，或引进外部函数。在函数中用`"""`框起该函数的含义，说明何时该调用此函数，如
```python
def my_function(input: int) -> int:
    """应该在...时调用..."""
    output = some_function(input)
    return output
```
模型可知晓函数的返回结果。
### Agent能力解释
通常，为了能够完成复杂任务，agent需要实现单次可调用多个工具(Parallel tool calling)以及多轮工具调用(Multi-turn tool calling)这两个功能。前者允许agent同时调用多个互不影响的工具，如从不同的来源收集信息；后者允许agent依序调用多个工具，可将前一轮工具调用所获得的信息作为参考，输入至后面一轮。本脚本中，前者由`for call in response.message.tool_calls`实现，后者则由`while`循环至模型认为无需再调用任何工具来实现。
