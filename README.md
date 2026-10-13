# Campus AI — AI 校园恋爱物语

![Campus AI 恋爱物语](assets/cover.png)

> **Windows 桌面单机优先 · AI 驱动的开放式 2D 校园恋爱 Galgame**
>
> 核心机制：云端大模型驱动自然对话与人设演绎，规则引擎（Arbitrator）裁决好感度与世界状态，本地 ComfyUI / 预制图谱呈现立绘与 CG，全自主校园时空与分层长期记忆。

---

## 目录结构

```text
CampusAI/
│
├── backend/                   # FastAPI 核心游戏逻辑服务端
│   ├── app/
│   │   ├── ai/
│   │   │   ├── llm/client.py       # OpenAI-compatible 大模型适配器 (JSON 解析/容错降级)
│   │   │   └── comfyui/client.py   # 本地 ComfyUI 生图适配器 (8188 端口异步任务提交)
│   │   ├── api/                    # HTTP 接口 (dialogue, world, characters, saves)
│   │   ├── core/
│   │   │   ├── arbitrator.py       # 规则裁决器 (好感度Clamp裁决、疲劳衰减、阶段锁)
│   │   │   └── config.py           # 角色卡与时空配置装配器
│   │   ├── database/               # SQLite + SQLAlchemy 2.0 异步数据库
│   │   ├── memory/manager.py       # 多级记忆系统 (短期对话缓冲 + 情节事件检索)
│   │   ├── models/schemas.py       # Pydantic 数据契约规范
│   │   └── main.py                 # FastAPI 入口
│   ├── config/                     # YAML 策划配置 (无需改动核心代码即可新增角色/地图)
│   │   ├── characters/lin_yuqing.yaml
│   │   ├── world.yaml
│   │   └── settings.yaml
│   ├── tests/test_flow.py          # 后端全链路闭环自测套件
│   ├── requirements.txt            # Python 依赖
│   └── run.py                      # 后端启动脚本
│
├── frontend/                  # Vue 3 + TypeScript + Pinia 游戏表现端
│   ├── src/
│   │   ├── components/
│   │   │   ├── CharacterSprite.vue # 动态二次元立绘 (表情差分/呼吸/微动效)
│   │   │   ├── DialogueBox.vue     # Galgame 对话框 (打字机效果/小动作/心声/铭牌)
│   │   │   ├── PlayerInputBar.vue  # 自由文本输入与快捷行动气泡
│   │   │   ├── WorldHud.vue        # 校园时空 HUD 与好感度仪表盘
│   │   │   ├── MapModal.vue        # 校园全景地图漫步 (图书馆/教室/食堂/操场)
│   │   │   ├── SaveModal.vue       # 6 槽位完整快照存档/读档系统
│   │   │   └── HistoryModal.vue    # 对话回忆录 (Backlog 回顾)
│   │   ├── stores/game.ts          # Pinia 全局游戏舞台状态管理
│   │   ├── services/api.ts         # 后端 API 通信契约
│   │   └── App.vue                 # 游戏主舞台与氛围光影
│   ├── package.json
│   └── vite.config.ts
│
├── data/                      # 运行时持久化数据 (自动生成)
│   └── game.db                # 本地 SQLite 数据库
│
└── start_game.bat             # Windows 一键全量启动脚本
```

---

## 快速启动体验

### 1. 配置云端大模型 (可选)
编辑 `backend/.env`（可复制自 `backend/.env.example`）：
```ini
LLM_API_KEY=sk-xxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```
*注：未配置 API Key 时系统会自动切换至智能离线交互模式，保证零网络也能顺畅游玩。*

### 2. 本地 ComfyUI 生图 (可选)
如果已启动本地 ComfyUI 服务（默认 `http://127.0.0.1:8188`），触发特定关键约会或回忆剧情时将自动生成高质感剧情 CG。未启动时会自动平滑降级，绝不卡死游戏主进程。

### 3. 一键启动
双击根目录下的 `start_game.bat`，即可同时拉起后端与前端，并在浏览器打开：
- 游戏主界面：`http://127.0.0.1:5173`
- 后端 API 文档：`http://127.0.0.1:8000/docs`
