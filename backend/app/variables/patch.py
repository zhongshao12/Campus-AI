import re
from typing import Optional

# 标准路径格式正则支持:
# 1. /characters/{char_id}/relationship/{prop}
# 2. /characters/{char_id}/state/{prop}
# 3. /player/{prop}
# 4. /world/{prop}

CHAR_PATH_PATTERN = re.compile(r"^/characters/([^/]+)/(relationship|state)/([^/]+)$")
PLAYER_PATH_PATTERN = re.compile(r"^/player/([^/]+)$")
WORLD_PATH_PATTERN = re.compile(r"^/world/([^/]+)$")

class ParsedPath:
    def __init__(
        self,
        domain: str,               # "characters", "player", "world"
        entity_id: Optional[str],  # 例如 "lin_yuqing" 或 None
        sub_domain: Optional[str], # "relationship", "state" 或 None
        property_name: str,        # "affection", "current_mood", "money" 等
    ):
        self.domain = domain
        self.entity_id = entity_id
        self.sub_domain = sub_domain
        self.property_name = property_name

    def to_rule_key(self) -> str:
        """
        映射到 VARIABLE_RULES 注册表中的完整规范键
        例: characters.relationship.affection, characters.state.current_mood, player.money
        """
        if self.domain == "characters" and self.sub_domain:
            return f"characters.{self.sub_domain}.{self.property_name}"
        elif self.domain == "player":
            return f"player.{self.property_name}"
        elif self.domain == "world":
            return f"world.{self.property_name}"
        return f"{self.domain}.{self.property_name}"

def parse_variable_path(path: str) -> Optional[ParsedPath]:
    """解析标准化变量路径"""
    if not path or not path.startswith("/"):
        return None

    m_char = CHAR_PATH_PATTERN.match(path)
    if m_char:
        return ParsedPath(
            domain="characters",
            entity_id=m_char.group(1),
            sub_domain=m_char.group(2),
            property_name=m_char.group(3),
        )

    m_player = PLAYER_PATH_PATTERN.match(path)
    if m_player:
        return ParsedPath(
            domain="player",
            entity_id=None,
            sub_domain=None,
            property_name=m_player.group(1),
        )

    m_world = WORLD_PATH_PATTERN.match(path)
    if m_world:
        return ParsedPath(
            domain="world",
            entity_id=None,
            sub_domain=None,
            property_name=m_world.group(1),
        )

    return None
