"""
大模型接口封装
支持 OpenAI 兼容格式的 API
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
import requests
import urllib3

# 禁用 HTTPS 证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """大模型客户端，支持所有 OpenAI 兼容格式的 API"""
    
    def __init__(self, api_url: str, api_key: str, model: str, 
                 temperature: float = 0.3, max_tokens: int = 2000, enable_thinking: bool = False):
        """
        初始化大模型客户端
        
        Args:
            api_url: 完整的 API URL，包含 /chat/completions 路径
                    例如: http://ip:port/r/ai-deploy-dsfp-prd/qwen-max/v1/chat/completions
            api_key: API 密钥
            model: 模型名称
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大生成 token 数
            enable_thinking: 是否启用深度思考模式
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_thinking = enable_thinking
        
        logger.info(f"初始化大模型客户端")
        logger.info(f"  API URL: {self.api_url}")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  Temperature: {self.temperature}")
        logger.info(f"  Max Tokens: {self.max_tokens}")
        if self.enable_thinking:
            logger.info(f"  深度思考模式已启用")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        发送聊天请求到 OpenAI 兼容的 API
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数（如 model、temperature、max_tokens，会覆盖初始化值）
            
        Returns:
            模型响应内容
        
        深度思考支持:
            在消息末尾添加 /think 强制开启深度思考
            在消息末尾添加 /no_think 强制关闭深度思考
        """
        # 检测深度思考标签
        enable_thinking = False
        processed_messages = []
        
        for msg in messages:
            processed_msg = msg.copy()
            content = str(msg.get('content', ''))
            
            # 检查是否有深度思考标签
            if content.strip().endswith('/think'):
                enable_thinking = True
                # 移除 /think 标签
                processed_msg['content'] = content.rsplit('/think', 1)[0].rstrip()
            elif content.strip().endswith('/no_think'):
                enable_thinking = False
                # 移除 /no_think 标签
                processed_msg['content'] = content.rsplit('/no_think', 1)[0].rstrip()
            
            processed_messages.append(processed_msg)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": kwargs.get("model", self.model),
            "messages": processed_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }
        
        # 如果启用深度思考（使用实例级别的配置或消息级别的标签）
        if enable_thinking or self.enable_thinking:
            data['reasoning_effort'] = kwargs.get('reasoning_effort', 'medium')
            # 某些模型在深度思考模式下不支持 temperature 和 max_tokens
            # 但为了兼容性，我们保留这些参数
        
        try:
            logger.debug(f"调用 API: {self.api_url}")
            logger.debug(f"深度思考: {enable_thinking}")
            logger.debug(f"请求数据: {data}")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=120,
                verify=False  # 禁用 HTTPS 证书验证，使用自签光证书时需要
            )
            response.raise_for_status()
            result = response.json()
            
            logger.debug(f"API 响应: {result}")
            return result['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as e:
            # 较详记录 HTTP 错误详情
            logger.error(f"API 调用失败 [{e.response.status_code}]: {e}")
            try:
                error_detail = e.response.json()
                logger.error(f"错误详情: {error_detail}")
            except:
                logger.error(f"响应内容: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise
    
    def review_code(self, code_diff: str, file_path: str, rules: List[str], enable_thinking: bool = False) -> Dict:
        """
        使用大模型评审代码
        
        Args:
            code_diff: 代码差异
            file_path: 文件路径
            rules: 评审规则列表
            enable_thinking: 是否启用深度思考模式
            
        Returns:
            评审结果（包含 issues 数组和 summary 字符串）
            
        问题严重程度定义 (severity)：
        - critical: 严重个子 (SQL注入、内存泄漏、数据丢失等安全问题)
        - major: 主要个子 (丢失錯误处理、性能瓶颈、逻辑错误等)
        - minor: 次要个子 (代码风格不一致、命名不清晰等)
        - suggestion: 建议 (代码改进、最佳实践等)
        """
        # 构建 prompt
        rules_text = "\n".join([f"- {rule}" for rule in rules])
        
        prompt = f"""你是一个专业的代码评审专家。请对以下代码变更进行评审。

文件路径: {file_path}

代码差异:
```diff
{code_diff}
```

请根据以下评审规则进行检查:
{rules_text}

=== 重要 ===
你必须只返回有效的JSON格式,不要包含任何其他内容,包括思考过程、解释或markdown代码块。
直接返回JSON对象,格式必须完全符合以下要求。

请以纯JSON格式返回评审结果:
{{
    "issues": [
        {{
            "severity": "critical/major/minor/suggestion",
            "line": "具体行号或行号范围(如 42 或 42-58)",
            "method": "涉及的方法名称(如 getUserInfo, render等,可选)",
            "category": "code_style/security/performance/best_practices",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ],
    "summary": "整体评价"
}}

要求:
1. 每个问题必须包含具体的行号(不能是'N/A'),格式为 '42' 或 '42-58'
2. 对于前端/后端代码,尽量识别并填写涉及的方法/函数名称
3. 如果没有发现问题,issues数组可以为空,但请给出正面的summary
4. 必须严格遵守JSON格式,不要包含注释,不要有多余的逗号
5. 所有字符串值必须用双引号包围,不要使用单引号
6. description和suggestion中如果包含双引号,请使用转义 \\"
7. 只返回JSON,不要有任何其他内容
8. 确保JSON完整且格式正确,否则无法被系统处理"""

        messages = [
            {"role": "system", "content": "你是一个专业的代码评审专家,擅长发现代码中的问题并给出改进建议。"},
            {"role": "user", "content": prompt}
        ]
        
        # 如果启用深度思考，在最后一个消息添加 /think 标签
        if enable_thinking:
            messages[-1]["content"] += "\n/think"
        
        try:
            response = self.chat(messages)
            # 提取JSON部分
            import json
            import re
            
            # 移除think标签或思考梯段（处理启用深度思考时的输出）
            # 如果包含<think>...</think>，先移除它
            cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            if not cleaned_response.strip():
                # 如果整个响应都是思考，使用原始响应
                cleaned_response = response
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # 尝试修复常见的JSON错误
                # 1. 移除尾随逗号 (trailing comma)
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                # 2. 将单引号改为双引号 (只在键名和字符串值中)
                # 注意:这可能不完美,但可以处理大部分情况
                json_str = json_str.replace("\'", '"')
                # 3. 修复缺少逗号的问题（在相邻的对象/数组之间）
                # 例如：}\n{ 应该是},\n{
                json_str = re.sub(r'(\})\s*(["\{])', r'\1,\2', json_str)
                # 4. 修复数组元素之间缺少逗号的问题
                # 检查 JSON 结构中可能缺少逗号的地方
                json_str = re.sub(r'(")}\s*(["\{])', r'\1}},\2', json_str)
                
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    # JSON解析失败，尝试更激进的修复
                    logger.debug(f"首次JSON解析失败，尝试激进修复: {json_error}")
                    
                    # 尝试修复：为缺少的对象属性添加逗号
                    # 匹配模式："key": "value"\n"key": 应该变成 "key": "value",\n"key":
                    json_str = re.sub(r'("\s*:\s*[^,}\]\n]*)(\s*")', r'\1,\2', json_str)
                    
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError as json_error2:
                        # 记录详细信息
                        logger.error(f"JSON解析失败: {json_error2}")
                        logger.error(f"LLM原始响应: {response[:1000]}...")  # 显示更多字符
                        logger.error(f"提取的JSON字符串: {json_str[:1000]}...")  # 显示更多字符
                        
                        # 返回空结果,但在summary中说明问题
                        result = {
                            "issues": [], 
                            "summary": f"JSON解析错误: {str(json_error2)}. LLM返回格式不符合要求。请检查LLM的prompt或模型输出设置。"
                        }
            else:
                logger.warning(f"未找到JSON格式，原始响应: {response[:500]}...")
                result = {"issues": [], "summary": response}
            
            return result
        except Exception as e:
            logger.error(f"代码评审失败: {e}")
            return {
                "issues": [],
                "summary": f"评审失败: {str(e)}"
            }
