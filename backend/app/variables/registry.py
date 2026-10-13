from typing import Dict, Any

# 变量所有权分类:
# - ai_proposed: AI 可以提议 delta 或 replace，但受限于单轮上限、疲劳度和阶段阈值
# - system: 仅限游戏核心规则/系统代码修改（如日期、金钱、体力、地点）
# - event_engine: 仅限剧情事件裁决引擎修改（如确认恋人关系、解锁主线标记）

VARIABLE_RULES: Dict[str, Dict[str, Any]] = {
    # --- 角色关系变量 ---
    "affection": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 3,
        "min_delta_per_turn": -3,
        "owner": "ai_proposed",
        "field_name": "affection",
        "target_model": "Relationship",
    },
    "trust": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 2,
        "min_delta_per_turn": -2,
        "owner": "ai_proposed",
        "field_name": "trust",
        "target_model": "Relationship",
    },
    "familiarity": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 2,
        "min_delta_per_turn": -1,
        "owner": "ai_proposed",
        "field_name": "familiarity",
        "target_model": "Relationship",
    },
    "stage": {
        "type": "enum",
        "values": ["acquaintance", "friend", "close", "crush", "lover"],
        "owner": "event_engine",  # AI 无法直接越权提议跳跃阶段
        "field_name": "stage",
        "target_model": "Relationship",
    },

    # --- 角色状态变量 ---
    "current_mood": {
        "type": "enum",
        "values": ["neutral", "happy", "blush", "surprised", "thinking", "pout", "sad", "angry"],
        "owner": "ai_proposed",
        "field_name": "current_mood",
        "target_model": "CharacterState",
    },
    "fatigue": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 10,
        "owner": "system",
        "field_name": "fatigue",
        "target_model": "CharacterState",
    },
    "current_location": {
        "type": "string",
        "owner": "system",  # NPC 物理移动受日程系统支配，AI 对话中不能瞬移
        "field_name": "current_location",
        "target_model": "CharacterState",
    },

    # --- 玩家属性变量 ---
    "player_money": {
        "type": "integer",
        "min": 0,
        "owner": "system",  # AI 不能擅自修改玩家钱包
        "field_name": "money",
        "target_model": "Player",
    },
    "player_energy": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "owner": "system",
        "field_name": "energy",
        "target_model": "Player",
    },

    # --- 世界属性变量 ---
    "player_location": {
        "type": "string",
        "owner": "system",
        "field_name": "player_location",
        "target_model": "WorldState",
    },
    "time_slot": {
        "type": "string",
        "owner": "system",
        "field_name": "time_slot",
        "target_model": "WorldState",
    },
}
