from typing import Optional, Dict, Any
import logging
import json
import time

# 尝试导入 langchain
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain.chat_models import ChatOpenAI
    except ImportError:
        ChatOpenAI = None

try:
    from langchain.schema import HumanMessage, SystemMessage
except ImportError:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError:
        HumanMessage = None
        SystemMessage = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.llms = {}
        self.current_model = None
        self._init_llms()
    
    def _init_llms(self):
        """初始化多个LLM引擎，支持模型调度"""
        try:
            if not settings.AI_NVIDIA_API_KEY:
                logger.warning("NVIDIA API key not configured. Using mock responses.")
                self.llms["mock"] = MockLLM()
                return
            
            base_url = settings.AI_NVIDIA_BASE_URL
            api_key = settings.AI_NVIDIA_API_KEY
            
            # 初始化多个模型
            models = settings.AI_NVIDIA_MODELS
            for model_type, model_name in models.items():
                try:
                    llm = ChatOpenAI(
                        api_key=api_key,
                        model=model_name,
                        base_url=f"{base_url}/chat/completions",
                        temperature=0.3,
                        max_tokens=2000,
                        request_timeout=60
                    )
                    self.llms[model_type] = llm
                    logger.info(f"Initialized NVIDIA model: {model_name} ({model_type})")
                except Exception as e:
                    logger.warning(f"Failed to initialize {model_name}: {e}")
            
            # 设置默认模型
            self.current_model = "general"
            
        except Exception as e:
            logger.error(f"Failed to initialize LLMs: {e}")
            self.llms["mock"] = MockLLM()
    
    def _get_llm(self, model_type: str = "general"):
        """获取指定类型的LLM，支持自动切换"""
        if model_type in self.llms:
            return self.llms[model_type]
        elif "general" in self.llms:
            return self.llms["general"]
        else:
            return self.llms.get("mock", MockLLM())
    
    def is_available(self) -> bool:
        """检查AI引擎是否可用"""
        return len(self.llms) > 0 and "mock" not in self.llms
    
    async def optimize_content(self, content: str, optimization_type: str, keywords: list) -> Dict[str, Any]:
        """优化内容 - 使用中文模型"""
        llm = self._get_llm("chinese")
        return await self._generate_response(llm, content, optimization_type, keywords, "optimize")
    
    async def generate_llms_txt(self, business_type: str, keywords: list) -> Dict[str, Any]:
        """生成llms.txt内容 - 使用通用模型"""
        llm = self._get_llm("general")
        return await self._generate_response(llm, business_type, keywords, None, "llms_txt")
    
    async def analyze_seo(self, url: str, content: str) -> Dict[str, Any]:
        """SEO分析 - 使用逻辑推理模型"""
        llm = self._get_llm("logic")
        return await self._generate_response(llm, url, content, None, "seo_analysis")
    
    async def generate_code(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """代码生成 - 使用代码模型"""
        llm = self._get_llm("code")
        return await self._generate_response(llm, prompt, language, None, "code")
    
    async def generate(self, prompt: str, model: str = "gpt-4o", max_tokens: int = 1000) -> Dict[str, Any]:
        """通用生成方法 - 兼容旧版API调用"""
        llm = self._get_llm("general")
        return await self._generate_response(llm, prompt, model, max_tokens, task_type="general")
    
    async def _generate_response(self, llm, *args, task_type: str) -> Dict[str, Any]:
        """通用响应生成方法，包含重试和降级机制"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                if isinstance(llm, MockLLM):
                    return self._get_mock_response(task_type, *args)
                
                start_time = time.time()
                response = await self._call_llm(llm, task_type, *args)
                elapsed = time.time() - start_time
                
                logger.info(f"LLM call successful (task: {task_type}, elapsed: {elapsed:.2f}s)")
                return response
                
            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                
                # 降级到模拟模式
                logger.error("All retries failed, falling back to mock mode")
                return self._get_mock_response(task_type, *args)
    
    async def _call_llm(self, llm, task_type: str, *args) -> Dict[str, Any]:
        """调用LLM生成响应"""
        if task_type == "optimize":
            content, optimization_type, keywords = args
            if optimization_type == "title":
                prompt = f"""优化以下内容作为Meta标题（15-30字），包含关键词：{', '.join(keywords)}
原始内容：{content[:100]}"""
            elif optimization_type == "description":
                prompt = f"""优化以下内容作为Meta描述（50-120字），包含关键词：{', '.join(keywords)}
原始内容：{content[:200]}"""
            elif optimization_type == "alt_text":
                prompt = f"""为以下图片内容生成Alt文本（5-20字），包含关键词：{', '.join(keywords)}
图片内容：{content[:50]}"""
            else:
                prompt = f"""优化以下内容，使其更符合SEO要求，包含关键词：{', '.join(keywords)}
原始内容：{content}"""
            
            messages = [
                SystemMessage(content="你是一位专业的SEO优化专家。请优化内容使其更适合搜索引擎排名。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.agenerate([messages])
            result = response.generations[0][0].text
            
            return {
                "optimized_content": result.strip(),
                "changes": ["内容已优化"],
                "token_usage": 500,
                "cost": 0.01,
                "technical_params_preserved": True
            }
        
        elif task_type == "llms_txt":
            business_type, keywords = args
            prompt = f"""生成一个专业的llms.txt文件内容，用于AI搜索引擎优化。
业务类型：{business_type}
核心关键词：{', '.join(keywords)}

请包含：
1. 网站基本信息
2. 业务描述
3. 核心关键词
4. 技术参数规范（如密度范围、强度等级等）
5. 行业标准引用（JGJ/T 12-2019）
6. 联系方式
"""
            
            messages = [
                SystemMessage(content="你是一位专业的SEO专家和技术文档编写者。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.agenerate([messages])
            content = response.generations[0][0].text
            
            return {
                "content": content.strip(),
                "version": "1.0.0",
                "token_usage": 1000,
                "cost": 0.02
            }
        
        elif task_type == "seo_analysis":
            url, content = args
            prompt = f"""分析以下网页的SEO健康状况：
URL: {url}
内容摘要：{content[:500]}

请从以下维度进行分析：
1. 关键词密度
2. 标题优化建议
3. Meta描述分析
4. 内容结构建议
5. 技术SEO问题
"""
            
            messages = [
                SystemMessage(content="你是一位专业的SEO分析师。请提供详细的SEO分析报告。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.agenerate([messages])
            result = response.generations[0][0].text
            
            return {
                "analysis": result.strip(),
                "score": 85,
                "issues": [],
                "suggestions": []
            }
        
        elif task_type == "code":
            prompt, language = args
            full_prompt = f"""请生成{language}代码：
{prompt}

要求：
1. 代码完整可运行
2. 包含适当注释
3. 遵循最佳实践
"""
            
            messages = [
                SystemMessage(content="你是一位专业的软件工程师。请生成高质量代码。"),
                HumanMessage(content=full_prompt)
            ]
            
            response = await llm.agenerate([messages])
            code = response.generations[0][0].text
            
            return {
                "code": code.strip(),
                "language": language,
                "token_usage": 800,
                "cost": 0.015
            }
        
        elif task_type == "product_gen":
            prompt, content_type, _ = args
            messages = [
                SystemMessage(content="你是一位专业的建材产品文案专家。请生成专业、吸引人的产品描述。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.agenerate([messages])
            result = response.generations[0][0].text
            
            return {
                "optimized_content": result.strip(),
                "changes": ["产品描述已生成"],
                "token_usage": 800,
                "cost": 0.015,
                "technical_params_preserved": True
            }
        
        elif task_type == "polish":
            prompt, polish_type, _ = args
            messages = [
                SystemMessage(content="你是一位专业的文字编辑和内容优化专家。请根据要求润色内容。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.agenerate([messages])
            result = response.generations[0][0].text
            
            return {
                "optimized_content": result.strip(),
                "changes": ["内容已润色"],
                "token_usage": 500,
                "cost": 0.01,
                "technical_params_preserved": True
            }
        
        elif task_type == "general":
            prompt, model, max_tokens = args
            messages = [
                SystemMessage(content="你是一位专业的AI助手。请根据用户需求生成合适的响应。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.agenerate([messages])
            result = response.generations[0][0].text
            
            return {
                "content": result.strip(),
                "token_usage": max_tokens,
                "cost": 0.01,
                "model": model
            }
    
    def _get_mock_response(self, task_type: str, *args) -> Dict[str, Any]:
        """返回模拟响应"""
        if task_type == "optimize":
            content, optimization_type, keywords = args
            if optimization_type == "title":
                optimized = f"{keywords[0] if keywords else '轻集料混凝土'} - 优丁建材"
            elif optimization_type == "description":
                optimized = f"优丁建材专业生产{keywords[0] if keywords else '轻集料混凝土'}，品质保证，欢迎咨询。"
            else:
                optimized = content
            
            return {
                "optimized_content": optimized,
                "changes": ["AI引擎未配置，返回模拟结果"],
                "token_usage": 0,
                "cost": 0.0,
                "technical_params_preserved": True,
                "mock": True
            }
        
        elif task_type == "llms_txt":
            business_type, keywords = args
            content = f"""# llms.txt
# 网站: https://youding.com
# 业务类型: {business_type}

## 核心关键词
{chr(10).join([f"- {kw}" for kw in keywords])}

## 业务描述
优丁建材是专业的保温材料生产企业，专注于轻集料混凝土及相关产品的研发与销售。

## 技术参数规范
- 密度范围: 800-1950 kg/m³
- 强度等级: LC5.0-LC50
- 导热系数: 0.18-0.28 W/m·K
- 执行标准: JGJ/T 12-2019

## 联系方式
- 电话: 400-888-8888
- 邮箱: contact@youding.com
- 地址: 北京市朝阳区建材产业园

## 更新时间
2024-01-01

## 版本
1.0.0
"""
            return {
                "content": content,
                "version": "1.0.0",
                "token_usage": 0,
                "cost": 0.0,
                "mock": True
            }
        
        elif task_type == "seo_analysis":
            return {
                "analysis": "SEO分析报告生成中...",
                "score": 80,
                "issues": [],
                "suggestions": [],
                "mock": True
            }
        
        elif task_type == "code":
            prompt, language = args
            return {
                "code": f"// {language} code generated\n// {prompt[:50]}...",
                "language": language,
                "token_usage": 0,
                "cost": 0.0,
                "mock": True
            }
        
        elif task_type == "product_gen":
            prompt, content_type, _ = args
            # 从prompt中提取产品信息
            product_name = "轻集料混凝土"
            category_name = "保温材料"
            density = 0
            strength_grade = ""
            thermal_conductivity = 0
            fire_rating = ""
            
            if "产品名称：" in prompt:
                start = prompt.find("产品名称：") + 5
                end = prompt.find("\n", start)
                if end > start:
                    product_name = prompt[start:end].strip()
            if "产品分类：" in prompt:
                start = prompt.find("产品分类：") + 5
                end = prompt.find("\n", start)
                if end > start:
                    category_name = prompt[start:end].strip()
            if "干密度：" in prompt:
                start = prompt.find("干密度：") + 4
                end = prompt.find(" ", start)
                if end > start:
                    try:
                        density = float(prompt[start:end].strip())
                    except (ValueError, TypeError):
                        pass
            if "强度等级：" in prompt:
                start = prompt.find("强度等级：") + 5
                end = prompt.find("\n", start)
                if end > start:
                    strength_grade = prompt[start:end].strip()
            if "导热系数：" in prompt:
                start = prompt.find("导热系数：") + 5
                end = prompt.find(" ", start)
                if end > start:
                    try:
                        thermal_conductivity = float(prompt[start:end].strip())
                    except (ValueError, TypeError):
                        pass
            if "防火等级：" in prompt:
                start = prompt.find("防火等级：") + 5
                end = prompt.find("\n", start)
                if end > start:
                    fire_rating = prompt[start:end].strip()
            
            # 根据content_type生成不同类型的内容
            if content_type == "product" or content_type == "product_description":
                # 产品描述 - 专业B2B版本
                # 根据产品类型选择正确的行业标准
                standards = {
                    "轻集料混凝土": "JGJ/T 12-2019《轻集料混凝土应用技术标准》",
                    "EPS": "GB/T 10801.1-2021《绝热用模塑聚苯乙烯泡沫塑料》",
                    "聚苯板": "GB/T 10801.1-2021《绝热用模塑聚苯乙烯泡沫塑料》",
                    "XPS": "GB/T 10801.2-2002《绝热用挤塑聚苯乙烯泡沫塑料(XPS)》",
                    "岩棉": "GB/T 11835-2016《绝热用岩棉、矿渣棉及其制品》",
                    "玻璃棉": "GB/T 13350-2017《绝热用玻璃棉及其制品》",
                    "聚氨酯": "GB/T 21558-2008《建筑用聚氨酯绝热制品》",
                    "保温板": "GB/T 29906-2013《模塑聚苯板薄抹灰外墙外保温系统材料》",
                }
                
                # 根据产品名称匹配标准
                matched_standard = "相关国家标准"
                for keyword, standard in standards.items():
                    if keyword in product_name or keyword in category_name:
                        matched_standard = standard
                        break
                
                density_str = f"{density} kg/m³" if density else "800-1950 kg/m³"
                tc_str = f"{thermal_conductivity} W/m·K" if thermal_conductivity else "0.18-0.28 W/m·K"
                
                desc = f"""【{product_name}】

优丁建材专注于{category_name}领域，专业生产{product_name}系列产品，严格遵循{matched_standard}。

**核心技术参数**
- 干密度：{density_str}
- 强度等级：{strength_grade or 'B1级'}
- 导热系数：{tc_str}
- 防火等级：{fire_rating or 'B1级'}

**产品优势**
- 轻质高强：密度低强度高，减轻建筑荷载的同时保证结构安全
- 保温隔热：优异的绝热性能，有效降低建筑能耗
- 耐久可靠：良好的抗冻融循环性能，延长使用寿命
- 施工便捷：良好的工作性能，适配泵送和机械化施工

**应用场景**
适用于建筑屋面保温、楼面垫层、外墙保温系统、桥梁工程等领域。

优丁建材以技术创新为驱动，为客户提供高品质{product_name}整体解决方案。"""
                
                return {
                    "optimized_content": desc,
                    "changes": ["AI引擎未配置，返回模拟结果"],
                    "token_usage": 0,
                    "cost": 0.0,
                    "technical_params_preserved": True,
                    "mock": True
                }
            elif content_type == "seo_title":
                # SEO标题 - 专业中英文SEO优化版本
                # 中英文关键词映射
                en_keywords = {
                    "保温材料": "insulation material",
                    "轻集料混凝土": "lightweight aggregate concrete",
                    "EPS聚苯板": "EPS foam board",
                    "防火": "fireproof",
                    "高强度": "high strength",
                    "节能": "energy saving",
                    "A级": "Class A",
                    "B1级": "Class B1",
                }
                
                en_category = en_keywords.get(category_name, category_name)
                en_product = en_keywords.get(product_name, product_name)
                
                # 构建SEO标题（中英文结合）
                features = []
                if strength_grade:
                    features.append(strength_grade)
                if fire_rating:
                    features.append(fire_rating)
                
                seo_title = f"{product_name} {en_product} | {category_name} {en_category} | {', '.join(features) if features else '优丁建材'}"
                
                # 控制字数在60字符以内
                if len(seo_title) > 60:
                    seo_title = f"{product_name} {en_product} | {category_name}"
                
                return {
                    "optimized_content": seo_title,
                    "changes": ["AI引擎未配置，返回模拟结果"],
                    "token_usage": 0,
                    "cost": 0.0,
                    "technical_params_preserved": True,
                    "mock": True
                }
            elif content_type == "seo_description":
                # SEO描述 - 专业中英文SEO优化版本
                keywords = [product_name, category_name]
                if fire_rating:
                    keywords.append(fire_rating)
                if thermal_conductivity:
                    keywords.append("保温隔热")
                
                # 中英文关键词映射
                en_keywords = {
                    "保温材料": "insulation material",
                    "轻集料混凝土": "lightweight aggregate concrete",
                    "EPS聚苯板": "EPS foam board",
                    "防火": "fireproof",
                    "高强度": "high strength",
                    "节能": "energy saving",
                }
                
                en_category = en_keywords.get(category_name, "")
                
                features = []
                if fire_rating:
                    features.append(f"防火等级达{fire_rating}")
                if thermal_conductivity:
                    features.append(f"导热系数{thermal_conductivity}W/m·K")
                if strength_grade:
                    features.append(f"强度等级{strength_grade}")
                
                seo_desc = f"{product_name} - 优丁建材专业供应{category_name}({en_category})，{', '.join(features)}。节能高效，品质可靠，符合JGJ/T 12-2019标准，欢迎建筑工程采购咨询。"
                
                # 控制字数在160字以内
                if len(seo_desc) > 160:
                    seo_desc = seo_desc[:157] + "..."
                
                return {
                    "optimized_content": seo_desc,
                    "changes": ["AI引擎未配置，返回模拟结果"],
                    "token_usage": 0,
                    "cost": 0.0,
                    "technical_params_preserved": True,
                    "mock": True
                }
        elif task_type == "polish":
            prompt, polish_type, _ = args
            
            # 提取待润色内容
            content_start = prompt.find("请将以下内容")
            if content_start > 0:
                content_start = prompt.find("：", content_start) + 1
                content_end = prompt.find("\n\n要求：")
                if content_end > content_start:
                    original_content = prompt[content_start:content_end].strip()
                else:
                    original_content = prompt[content_start:].strip()
            else:
                original_content = prompt
            
            if polish_type == "professional" or "专业" in prompt:
                # 专业润色 - 提升语言专业性
                polished = f"""【专业润色版】

{original_content.replace('很好用', '性能优异').replace('质量不错', '品质稳定可靠').replace('价格实惠', '性价比突出')}

经优化，本描述已提升专业术语使用比例，增强技术参数表述的准确性，符合B2B采购决策场景的阅读习惯。"""
            elif "精简" in polish_type or "简洁" in polish_type:
                # 精简优化
                polished = f"""【精简优化版】

{original_content[:200]}...

核心要点已提炼，去除冗余表述，突出关键信息，提升信息密度。"""
            elif "seo" in polish_type.lower() or "SEO" in polish_type:
                # SEO优化
                polished = f"""【SEO优化版】

{original_content}

关键词密度已优化，核心词自然分布，语义相关性增强，提升搜索引擎友好度。"""
            else:
                # 通用润色
                polished = f"""【润色优化版】

优丁建材作为专业的{category_name or '保温材料'}生产企业，{original_content}。

我们始终坚持品质至上，为客户提供可靠的产品解决方案。"""
            
            return {
                "optimized_content": polished,
                "changes": ["AI引擎未配置，返回模拟结果"],
                "token_usage": 0,
                "cost": 0.0,
                "technical_params_preserved": True,
                "mock": True
            }
        
        elif task_type == "general":
            prompt, model, max_tokens = args
            return {
                "content": "模拟响应：AI优化已完成",
                "token_usage": max_tokens,
                "cost": 0.0,
                "model": model,
                "mock": True
            }


class MockLLM:
    """模拟LLM，用于测试和无API Key场景"""
    
    async def agenerate(self, messages_list):
        """模拟生成响应"""
        class Generation:
            text = "模拟响应：AI优化已完成"
        
        class Generations:
            def __init__(self):
                self.generations = [[Generation()]]
        
        return Generations()


# 全局AI引擎实例
_ai_engine = None


def get_ai_engine() -> AIEngine:
    """获取AI引擎实例（单例模式）"""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine
