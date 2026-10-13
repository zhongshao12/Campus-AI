import json
import re
import logging
from typing import List, Dict, Any, Optional
import httpx

from ...core.config import settings, get_character_config
from ...models.schemas import LLMDialogueResponse, ProposedEffect

logger = logging.getLogger(__name__)

class LLMClient:
    """
    云端大模型适配器
    统一兼容 OpenAI 接口协议 (DeepSeek, 硅基流动, Qwen, Moonshot 等)
    负责 Prompt 组装、结构化 JSON 解析与容错回退。
    """

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL

    def _build_system_prompt(
        self,
        char_cfg: Dict[str, Any],
        affection: int,
        trust: int,
        stage: str,
        location_name: str,
        time_slot_name: str,
        weather: str,
        episodic_memories: List[str],
    ) -> str:
        personality = char_cfg.get("personality", {})
        traits = "、".join(personality.get("traits", []))
        speech_style = personality.get("speech_style", "")
        likes = "、".join(personality.get("likes", []))
        dislikes = "、".join(personality.get("dislikes", []))
        guidelines = char_cfg.get("prompt_guidelines", "")

        memories_text = "\n".join(episodic_memories) if episodic_memories else "（暂无特殊共同经历）"

        prompt = f"""你正在一款现代大学校园 Galgame 中扮演女角色【{char_cfg.get('name', '林雨晴')}】。
【角色人设】
- 身份：{char_cfg.get('title', '大学生')}，专业：{char_cfg.get('major', '中文系')}
- 性格：{traits}
- 语言风格：{speech_style}
- 喜好：{likes}
- 讨厌：{dislikes}

【当前世界环境】
- 当前时间：{time_slot_name}
- 当前天气：{weather}
- 当前所在地点：{location_name}

【你与玩家的关系状态】
- 好感度：{affection}/100
- 信任度：{trust}/100
- 关系阶段：{stage} (acquaintance:熟人, friend:朋友, close:亲密, lover:恋人)

【你的长期情节记忆】
{memories_text}

【扮演指导原则】
{guidelines}
请沉浸式扮演该角色与玩家对话。对话要口吻亲切自然、充满二次元青春感，绝对不要有机器人的生硬感。

【核心要求：输出格式】
你必须且仅能输出一个合法的 JSON 格式对象，禁止包含任何 JSON 之外的聊天废话。
JSON 字段规范：
{{
  "speaker": "{char_cfg.get('name', '林雨晴')}",
  "dialogue": "角色回复玩家的话（自然、符合当前好感度和场景）",
  "emotion": "当前情绪 (neutral, happy, blush, surprised, thinking, pout, sad)",
  "expression": "立绘表情标签 (neutral, happy, blush, surprised, thinking, pout, sad)",
  "action": "细微动作描写（如：轻轻撩了一下耳边的发丝）",
  "inner_thought": "内心独白（角色内心真实的小思绪）",
  "proposed_effects": [
    {{
      "type": "affection_delta",
      "value": 2,
      "reason": "玩家的话让她感到很开心"
    }}
  ],
  "event_trigger": null,
  "image_request": null
}}
注：proposed_effects 中好感变动 value 通常在 -3 到 +3 之间。若玩家提出极具纪念意义的邀约（如海边约会、天台告白），可以在 image_request 中提议生成 CG。
"""
        return prompt

    async def generate_dialogue(
        self,
        character_id: str,
        player_message: str,
        affection: int,
        trust: int,
        stage: str,
        location_name: str,
        time_slot_name: str,
        weather: str,
        episodic_memories: List[str],
        recent_history: List[Dict[str, str]],
    ) -> LLMDialogueResponse:
        """调用大模型生成结构化对白"""
        char_cfg = get_character_config(character_id)
        system_prompt = self._build_system_prompt(
            char_cfg=char_cfg,
            affection=affection,
            trust=trust,
            stage=stage,
            location_name=location_name,
            time_slot_name=time_slot_name,
            weather=weather,
            episodic_memories=episodic_memories,
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in recent_history:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", ""),
            })
        messages.append({"role": "user", "content": player_message})

        # 若未配置真实 API KEY 或为占位符，走本地智能 Mock
        if not self.api_key or self.api_key.startswith("your_api"):
            logger.info("未检测到有效 LLM_API_KEY，切换到离线规则对话引擎。")
            return self._mock_response(player_message, affection, stage)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_json_response(content)
        except Exception as e:
            logger.warning(f"云端 LLM 调用失败或超时: {e}，使用本地保障回退响应。")
            return self._mock_response(player_message, affection, stage)

    def _parse_json_response(self, text: str) -> LLMDialogueResponse:
        """鲁棒的 JSON 解析器，支持从 Markdown 代码块提取"""
        cleaned = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()

        try:
            parsed = json.loads(cleaned)
            return LLMDialogueResponse.model_validate(parsed)
        except Exception as err:
            logger.error(f"JSON 解析失败: {err}, 原文: {text}")
            return LLMDialogueResponse(
                speaker="林雨晴",
                dialogue=cleaned[:100] if len(cleaned) < 120 else "……嗯？你刚才说了什么，我好像有点走神啦。",
                emotion="neutral",
                expression="neutral",
                action="眨了眨眼睛",
                proposed_effects=[],
            )

    def _mock_response(self, msg: str, affection: int, stage: str) -> LLMDialogueResponse:
        """离线时的规则兜底生成器，模拟真实恋爱 Galgame 体验"""
        msg_lower = msg.lower()

        if any(w in msg_lower for w in ["你好", "嗨", "早", "雨晴"]):
            return LLMDialogueResponse(
                speaker="林雨晴",
                dialogue=f"嗨！你也在这里呀。今天的天气真舒服呢~",
                emotion="happy",
                expression="happy",
                action="微笑着向你挥了挥手",
                inner_thought="真巧，一抬头就看到他了。",
                proposed_effects=[ProposedEffect(type="affection_delta", value=1, reason="友善打招呼")],
            )
        elif any(w in msg_lower for w in ["看书", "小说", "文学", "村上春树", "借书"]):
            return LLMDialogueResponse(
                speaker="林雨晴",
                dialogue="你也在关注这本书吗？我刚读到第三章，里面的比喻写得太细腻了……你要一起翻翻看吗？",
                emotion="happy",
                expression="happy",
                action="把手边的精装书轻轻挪向你这边",
                inner_thought="没想到他也喜欢这本书，共同话题又增加啦。",
                proposed_effects=[ProposedEffect(type="affection_delta", value=2, reason="交流共同爱好")],
            )
        elif any(w in msg_lower for w in ["喜欢", "漂亮", "可爱", "约会", "周末"]):
            expr = "blush" if affection >= 30 else "surprised"
            delta = 2 if affection >= 20 else 0
            return LLMDialogueResponse(
                speaker="林雨晴",
                dialogue="突然这么说……真是的，你别拿我打趣啦，周围还有其他人呢！" if affection < 40 else "诶？周末吗……要是和你一起去的话，我、我倒是挺期待的。",
                emotion="blush",
                expression=expr,
                action="有些不好意思地移开视线，手指轻轻卷着衣角",
                inner_thought="心跳好像突然漏了一拍……",
                proposed_effects=[ProposedEffect(type="affection_delta", value=delta, reason="令人心动的发言")],
            )
        elif any(w in msg_lower for w in ["喝什么", "奶茶", "汽水", "请客"]):
            return LLMDialogueResponse(
                speaker="林雨晴",
                dialogue="那我要一罐冰镇柑橘汽水！待会儿自习结束我们一起去自动贩卖机吧！",
                emotion="happy",
                expression="happy",
                action="眼睛一亮，露出期待的表情",
                inner_thought="柑橘汽水加冰是夏天的救赎！",
                proposed_effects=[ProposedEffect(type="affection_delta", value=2, reason="分享喜欢的饮品")],
            )
        else:
            return LLMDialogueResponse(
                speaker="林雨晴",
                dialogue=f"“{msg}”吗？听你这么一说，确实挺有意思的。大学的生活好像总能遇到意想不到的新想法呢。",
                emotion="neutral",
                expression="neutral",
                action="托着下巴认真倾听",
                inner_thought="认真听别人讲话也是一种默契呢。",
                proposed_effects=[ProposedEffect(type="affection_delta", value=1, reason="愉快的日常交流")],
            )
