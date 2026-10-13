from typing import Dict, Any

# 变量所有权分类:
# - ai_proposed: AI 可以提议变动（受限于单轮上限、疲劳度和阶段阈值）
# - system: 仅限游戏核心规则/系统代码修改（如日期、金钱、体力、地点）
# - event_engine: 仅限剧情事件裁决引擎修改（如确认恋人关系、解锁主线标记）

VARIABLE_RULES: Dict[str, Dict[str, Any]] = {
    # --- 角色关系变量 (characters.relationship.*) ---
    "characters.relationship.affection": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 3,
        "min_delta_per_turn": -3,
        "allowed_ops": ["delta"],
        "owner": "ai_proposed",
        "field_name": "affection",
        "target_model": "Relationship",
    },
    "characters.relationship.trust": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 2,
        "min_delta_per_turn": -2,
        "allowed_ops": ["delta"],
        "owner": "ai_proposed",
        "field_name": "trust",
        "target_model": "Relationship",
    },
    "characters.relationship.familiarity": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 2,
        "min_delta_per_turn": -1,
        "allowed_ops": ["delta"],
        "owner": "ai_proposed",
        "field_name": "familiarity",
        "target_model": "Relationship",
    },
    "characters.relationship.stage": {
        "type": "enum",
        "values": ["acquaintance", "friend", "close", "crush", "lover"],
        "allowed_ops": ["replace"],
        "owner": "event_engine",  # AI 无法越权提议跳跃阶段
        "field_name": "stage",
        "target_model": "Relationship",
    },

    # --- 角色状态变量 (characters.state.*) ---
    "characters.state.current_mood": {
        "type": "enum",
        "values": ["neutral", "happy", "blush", "surprised", "thinking", "pout", "sad", "angry"],
        "allowed_ops": ["replace"],
        "owner": "ai_proposed",
        "field_name": "current_mood",
        "target_model": "CharacterState",
    },
    "characters.state.fatigue": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "max_delta_per_turn": 10,
        "allowed_ops": ["delta", "replace"],
        "owner": "system",
        "field_name": "fatigue",
        "target_model": "CharacterState",
    },
    "characters.state.current_location": {
        "type": "string",
        "allowed_ops": ["replace"],
        "owner": "system",  # NPC 物理移动受日程支配，AI 不能擅自瞬移
        "field_name": "current_location",
        "target_model": "CharacterState",
    },

    # --- 玩家属性变量 (player.*) ---
    "player.money": {
        "type": "integer",
        "min": 0,
        "allowed_ops": ["delta", "replace"],
        "owner": "system",  # AI 不能修改玩家钱包
        "field_name": "money",
        "target_model": "Player",
    },
    "player.energy": {
        "type": "integer",
        "min": 0,
        "max": 100,
        "allowed_ops": ["delta", "replace"],
        "owner": "system",
        "field_name": "energy",
        "target_model": "Player",
    },
    "player.mood": {
        "type": "string",
        "allowed_ops": ["replace"],
        "owner": "system",
        "field_name": "mood",
        "target_model": "Player",
    },

    # --- 世界属性变量 (world.*) ---
    "world.player_location": {
        "type": "string",
        "allowed_ops": ["replace"],
        "owner": "system",
        "field_name": "player_location",
        "target_model": "WorldState",
    },
    "world.time_slot": {
        "type": "string",
        "allowed_ops": ["replace"],
        "owner": "system",
        "field_name": "time_slot",
        "target_model": "WorldState",
    },
}
