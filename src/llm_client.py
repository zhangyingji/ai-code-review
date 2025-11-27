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
                 temperature: float = 0.3, max_tokens: int = 2000, enable_thinking: bool = False,
                 severity_definitions: Optional[Dict] = None):
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
            severity_definitions: 严重程度定义，从配置文件中传入
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_thinking = enable_thinking
        self.severity_definitions = severity_definitions or {}
        
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
        """
        # 构建严重程度定义描述 - 使用配置或默认值
        severity_descriptions = self._build_severity_definitions()
        
        # 构建 prompt
        rules_text = "\n".join([f"- {rule}" for rule in rules])
        
        prompt = f"""你是专业的代码评审专家。根据以下信息对代码进行评审。

{severity_descriptions}

文件: {file_path}
代码差异:
```
{code_diff}
```

评审规则:
{rules_text}

请输出以下JSON格式的评审结果（仅输出JSON，无其他内容）:
{{
    "issues": [
        {{
            "severity": "critical/major/minor/suggestion",
            "line": "行号",
            "method": "方法",
            "category": "问题类别",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ],
    "summary": "总体评价"
}}

【必须遵循的要求】
1. 严格按照上述JSON格式输出，不加任何前缀/后缀
2. severity分类必须严格遵循定义，相同类型问题给出一致的严重程度
3. 优先按影响范围判断：安全性/数据完整性 > 功能正确性/性能 > 代码质量 > 最佳实践
4. 所有文字内容必须使用中文（description/suggestion/summary）
5. 不使用<think>标签或任何思考过程标记
"""

        messages = [
            {"role": "system", "content": "你是代码评审专家。只输出JSON格式的结果，所有内容必须使用中文。"},
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
            
            # 移除think标签或思考段落（处理启用深度思考时的输出）
            cleaned_response = response
            
            # 情况 1：处理成对的 <think>...</think> 标签
            if '<think>' in cleaned_response and '</think>' in cleaned_response:
                logger.debug("检测到成对的 <think></think> 标签，清除思考内容")
                cleaned_response = re.sub(r'<think>.*?</think>', '', cleaned_response, flags=re.DOTALL)
            
            # 情况 2：QwQ模型特殊情况 - 只有 </think> 而没有 <think>
            # 移除 </think> 之前的所有内容
            elif '</think>' in cleaned_response:
                logger.debug("检测到单独的 </think> 标签（QwQ模式），清除之前的思考内容")
                # 找到 </think> 的位置，只保留之后的内容
                think_end_pos = cleaned_response.find('</think>')
                if think_end_pos != -1:
                    # 保留 </think> 之后的内容
                    cleaned_response = cleaned_response[think_end_pos + len('</think>'):]
                    logger.debug(f"清除后的响应长度: {len(cleaned_response)} 字符")
            
            # 如果清除后为空，使用原始响应
            if not cleaned_response.strip():
                logger.warning("清除思考内容后响应为空，使用原始响应")
                cleaned_response = response
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # 修复常见的JSON错误
                json_str = self._fix_json_errors(json_str)
                
                try:
                    result = json.loads(json_str)
                    logger.debug(f"JSON解析成功，问题数量: {len(result.get('issues', []))}")
                except json.JSONDecodeError as json_error:
                    # JSON解析失败，尝试激进修复
                    logger.debug(f"首次JSON解析失败，尝试激进修复: {json_error}")
                    json_str = self._fix_json_errors(json_str, aggressive=True)
                    
                    try:
                        result = json.loads(json_str)
                        logger.debug(f"激进修复JSON解析成功")
                    except json.JSONDecodeError as json_error2:
                        # 记录详细信息并返回错误
                        logger.error(f"JSON解析最终失败: {json_error2}")
                        logger.error(f"LLM原始响应: {response[:1000]}...")
                        logger.error(f"提取的JSON: {json_str[:1000]}...")
                        
                        result = {
                            "issues": [], 
                            "summary": f"JSON解析错误: {str(json_error2)}. LLM返回格式不符合要求。"
                        }
            else:
                logger.warning(f"未找JSON格式 (response: {len(response)} chars)")
                logger.warning(f"\u5185容\uff1a{response[:500]}...")
                result = {"issues": [], "summary": "LLM 输出格式不符合要求，无法解析"}
            
            return result
        except Exception as e:
            logger.error(f"代码评审失败: {e}")
            return {
                "issues": [],
                "summary": f"评审失败: {str(e)}"
            }
    
    def _fix_json_errors(self, json_str: str, aggressive: bool = False) -> str:
        """
        修复JSON字符串中的常见错误
        
        Args:
            json_str: 需要修复的JSON字符串
            aggressive: 是否使用激进修复路略
            
        Returns:
            修复后的JSON字符串
        """
        # 基础修复: 移除尾随逗号、单引号等
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # 移除尾随逗号
        json_str = json_str.replace("\'", '\\"')  # 单引号改双引号
        json_str = re.sub(r'(\})\s*(["{\[])', r'\1,\2', json_str)  # 补充对象间逗号
        
        if aggressive:
            # 激进修复: 为属性值创需要的逗号
            # 匹配模式: "key": "value"\n"key" 应该变成 "key": "value",\n"key"
            json_str = re.sub(r'("\s*:\s*[^,}\]\n]*)(\s*")', r'\1,\2', json_str)
        
        return json_str
    
    def _build_severity_definitions(self) -> str:
        """
        构建严重程度定义描述文本
        返回帧形待添加的文本
        """
        if not self.severity_definitions:
            # 使用默认定义
            return self._get_default_severity_definitions()
        
        # 从配置中构建
        result = "问题严重程度定义 (severity) - 严格遵循以下标准进行分类：\n"
        
        for severity_level in ['critical', 'major', 'minor', 'suggestion']:
            if severity_level in self.severity_definitions:
                config = self.severity_definitions[severity_level]
                result += f"- {severity_level}: {config.get('description', '')}\n"
                
                # 添加例子
                examples = config.get('examples', [])
                if examples:
                    for example in examples:
                        result += f"  * {example}\n"
        
        return result
    
    def _get_default_severity_definitions(self) -> str:
        """
        返回默认的严重程度定义
        """
        return """问题严重程度定义 (severity) - 严格遵循以下标准进行分类：
- critical: 严重问题，影响系统安全性或数据完整性
  * SQL注入、XSS漏洞等安全漏洞
  * 内存泄漏、数据丢失、资源泄露
  * 逻辑错误导致功能完全不可用
  * 竞态条件导致数据不一致
- major: 主要问题，影响功能正确性或性能
  * 缺少必要的错误处理
  * 性能瓶颈（复杂度过高、数据库查询优化不足）
  * 业务逻辑错误导致功能异常
  * 死锁或无限循环风险
- minor: 次要问题，影响代码质量但不影响功能
  * 代码风格不一致
  * 命名不清晰或不符合规范
  * 代码重复、可读性不足
  * 注释缺失或不完善
- suggestion: 建议，代码改进和最佳实践
  * 可以优化的代码模式
  * 遵循最佳实践的建议
  * 代码结构改进建议"""
        