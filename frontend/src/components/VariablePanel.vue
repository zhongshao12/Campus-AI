<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="variable-card glass-modal">
      <!-- 头部：标题与 Revision 版本指示 -->
      <div class="modal-header">
        <div class="header-left">
          <h2 class="title">📊 状态与变量监控中心 (Variable Engine)</h2>
          <span class="revision-badge">Revision #{{ snapshot?.revision || 1 }}</span>
          <span class="schema-badge">Schema v{{ snapshot?.schema_version || 1 }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Tab 切换 -->
      <div class="tabs-row">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'characters' }"
          @click="activeTab = 'characters'"
        >
          💖 人物关系与心情
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'world_player' }"
          @click="activeTab = 'world_player'"
        >
          🌍 世界与玩家属性
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'logs' }"
          @click="activeTab = 'logs'; loadLogs()"
        >
          📜 变量因果审计日志
        </button>
      </div>

      <!-- 内容区 1：人物关系 -->
      <div v-if="activeTab === 'characters'" class="panel-body">
        <div class="character-var-card" v-for="(charData, charId) in snapshot?.characters" :key="charId">
          <div class="char-header">
            <span class="char-title">{{ String(charId) === 'lin_yuqing' ? '林雨晴 (同班同学)' : charId }}</span>
            <span class="mood-tag">心情：{{ getMoodLabel(charData.state.current_mood) }}</span>
          </div>

          <div class="stats-grid">
            <div class="stat-box">
              <span class="stat-name">好感度 (Affection)</span>
              <div class="meter-bar">
                <div class="meter-fill aff" :style="{ width: `${charData.relationship.affection}%` }"></div>
              </div>
              <span class="stat-val">{{ charData.relationship.affection }} / 100</span>
            </div>

            <div class="stat-box">
              <span class="stat-name">信任度 (Trust)</span>
              <div class="meter-bar">
                <div class="meter-fill trust" :style="{ width: `${charData.relationship.trust}%` }"></div>
              </div>
              <span class="stat-val">{{ charData.relationship.trust }} / 100</span>
            </div>

            <div class="stat-box">
              <span class="stat-name">熟悉度 (Familiarity)</span>
              <div class="meter-bar">
                <div class="meter-fill fam" :style="{ width: `${charData.relationship.familiarity || 20}%` }"></div>
              </div>
              <span class="stat-val">{{ charData.relationship.familiarity || 20 }} / 100</span>
            </div>

            <div class="stat-box">
              <span class="stat-name">当前关系阶段</span>
              <span class="stage-value">{{ charData.relationship.stage }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容区 2：世界与玩家 -->
      <div v-else-if="activeTab === 'world_player'" class="panel-body">
        <div class="section-box">
          <div class="section-title">👤 玩家核心状态 (Player State)</div>
          <div class="key-value-list">
            <div class="kv-item"><span class="k">体力值 (Energy):</span> <span class="v">{{ snapshot?.player.energy ?? 100 }} / 100</span></div>
            <div class="kv-item"><span class="k">钱包金钱 (Money):</span> <span class="v">¥ {{ snapshot?.player.money ?? 300 }}</span></div>
            <div class="kv-item"><span class="k">背包物品 (Inventory):</span> <span class="v">{{ JSON.stringify(snapshot?.player.inventory ?? {}) }}</span></div>
          </div>
        </div>

        <div class="section-box">
          <div class="section-title">🏫 校园时空维度 (World State)</div>
          <div class="key-value-list">
            <div class="kv-item"><span class="k">学期进度:</span> <span class="v">第 {{ snapshot?.world.day_number }} 天 ({{ snapshot?.world.weekday }})</span></div>
            <div class="kv-item"><span class="k">当前时段:</span> <span class="v">{{ snapshot?.world.time_slot }}</span></div>
            <div class="kv-item"><span class="k">当前地点:</span> <span class="v">{{ snapshot?.world.player_location }}</span></div>
            <div class="kv-item"><span class="k">当前天气:</span> <span class="v">{{ snapshot?.world.weather }}</span></div>
          </div>
        </div>
      </div>

      <!-- 内容区 3：变量审计日志 -->
      <div v-else-if="activeTab === 'logs'" class="panel-body logs-body">
        <div v-if="changeLogs.length === 0" class="empty-hint">-- 暂无变量变更日志 --</div>
        <div v-for="log in changeLogs" :key="log.id" class="log-row">
          <div class="log-top">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-path">{{ log.path }}</span>
            <span class="log-op" :class="log.op">{{ log.op }}</span>
          </div>
          <div class="log-change">
            <span class="old-v">{{ log.old_value }}</span>
            <span class="arrow">➔</span>
            <span class="new-v">{{ log.new_value }}</span>
            <span class="log-reason">（原因: {{ log.reason }}）</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toast', msg: string): void
}>()

const activeTab = ref<'characters' | 'world_player' | 'logs'>('characters')
const snapshot = ref<any | null>(null)
const changeLogs = ref<any[]>([])

const loadSnapshot = async () => {
  try {
    const { data } = await axios.get('/api/variables/snapshot')
    snapshot.value = data
  } catch (err) {
    console.error('获取变量快照失败', err)
  }
}

const loadLogs = async () => {
  try {
    const { data } = await axios.get('/api/variables/changes?limit=40')
    changeLogs.value = data
  } catch (err) {
    console.error('获取变更日志失败', err)
  }
}

const getMoodLabel = (m: string) => {
  const map: Record<string, string> = {
    happy: '愉快微笑 😊',
    blush: '脸红心动 ⁄(⁄ ⁄•⁄-⁄•⁄ ⁄)⁄',
    surprised: '惊讶睁大眼 😲',
    thinking: '若有所思 🤔',
    pout: '鼓嘴微嗔 😤',
    sad: '失落低落 🥺',
    neutral: '平静自然 🍃',
  }
  return map[m] || m || '自然'
}

onMounted(() => {
  loadSnapshot()
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 75;
  user-select: none;
}

.glass-modal {
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  width: 100%;
  max-width: 720px;
  height: 580px;
  padding: 24px 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7);
  color: #f8fafc;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: #38bdf8;
  margin: 0;
}

.revision-badge, .schema-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.4);
}

.schema-badge {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
  border-color: rgba(168, 85, 247, 0.4);
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
}

.tabs-row {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.character-var-card {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 16px;
}

.char-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.char-title {
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
}

.mood-tag {
  font-size: 12px;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  padding: 2px 10px;
  border-radius: 9999px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-box {
  background: rgba(15, 23, 42, 0.6);
  padding: 10px 12px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-name {
  font-size: 12px;
  color: #94a3b8;
}

.meter-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.3s;
}

.meter-fill.aff {
  background: linear-gradient(90deg, #ec4899, #f43f5e);
}

.meter-fill.trust {
  background: linear-gradient(90deg, #38bdf8, #0284c7);
}

.meter-fill.fam {
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
}

.stat-val {
  font-size: 11px;
  color: #cbd5e1;
  font-family: monospace;
}

.stage-value {
  font-size: 14px;
  font-weight: 700;
  color: #fb7185;
}

.section-box {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 14px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #cbd5e1;
  margin-bottom: 10px;
}

.key-value-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kv-item {
  font-size: 12px;
  display: flex;
  justify-content: space-between;
}

.kv-item .k {
  color: #94a3b8;
}

.kv-item .v {
  color: #e2e8f0;
  font-family: monospace;
}

/* 日志列表 */
.logs-body {
  gap: 10px;
}

.empty-hint {
  text-align: center;
  color: #64748b;
  padding: 30px;
  font-size: 13px;
}

.log-row {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-top {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
}

.log-time {
  color: #64748b;
}

.log-path {
  color: #38bdf8;
  font-family: monospace;
  flex: 1;
}

.log-op {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  text-transform: uppercase;
}

.log-op.delta {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.log-op.replace {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
}

.log-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.old-v {
  color: #94a3b8;
}

.arrow {
  color: #64748b;
  font-size: 10px;
}

.new-v {
  color: #4ade80;
  font-weight: 700;
}

.log-reason {
  color: #cbd5e1;
  font-size: 11px;
  margin-left: 6px;
}
</style>
