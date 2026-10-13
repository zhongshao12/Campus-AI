<template>
  <header class="hud-container">
    <!-- 左侧：世界时空与地点 (暖纸漫画标签) -->
    <div class="hud-left paper-card">
      <div class="date-badge">
        <span class="day-number">Day {{ world?.day_number || 1 }}</span>
        <span class="weekday">{{ world?.weekday || '星期三' }}</span>
      </div>
      <div class="divider"></div>
      <div class="time-slot-badge" :class="world?.time_slot || 'afternoon'">
        <span class="slot-dot"></span>
        <span class="slot-name">{{ slotDisplayName }}</span>
      </div>
      <div class="divider"></div>
      <div class="location-badge">
        <span class="loc-icon">📍</span>
        <span class="loc-name">{{ world?.location_name || '大学图书馆' }}</span>
      </div>
    </div>

    <!-- 中间：角色好感度与心动槽 (珊瑚粉暖色仪表盘) -->
    <div class="hud-center paper-card" v-if="character">
      <div class="character-hud-info">
        <span class="char-name">{{ character.name }}</span>
        <span class="stage-tag" :class="character.stage">{{ stageDisplayName }}</span>
      </div>
      <div class="affection-meter">
        <div class="heart-icon">💖</div>
        <div class="meter-track">
          <div
            class="meter-fill"
            :style="{ width: `${Math.min(100, character.affection)}%` }"
          ></div>
        </div>
        <span class="affection-num">{{ character.affection }} / 100</span>
      </div>
    </div>

    <!-- 右侧：全局操作漫画贴纸按钮组 -->
    <div class="hud-right paper-card">
      <button class="hud-btn phone-btn-highlight" @click="$emit('open-phone')" title="智能手机 (P)">
        <span class="btn-icon">📱</span>
        <span class="btn-label">手机</span>
      </button>
      <button class="hud-btn" @click="$emit('open-variables')" title="变量监控 (V)">
        <span class="btn-icon">📊</span>
        <span class="btn-label">变量</span>
      </button>
      <button class="hud-btn" @click="$emit('open-map')" title="校园地图">
        <span class="btn-icon">🗺️</span>
        <span class="btn-label">地图</span>
      </button>
      <button class="hud-btn" @click="$emit('advance-time')" title="推进时间">
        <span class="btn-icon">⏳</span>
        <span class="btn-label">时钟</span>
      </button>
      <button class="hud-btn" @click="$emit('open-history')" title="对话回顾">
        <span class="btn-icon">📜</span>
        <span class="btn-label">回顾</span>
      </button>
      <button class="hud-btn" @click="$emit('open-saves')" title="存档/读档">
        <span class="btn-icon">💾</span>
        <span class="btn-label">系统</span>
      </button>
      <button class="hud-btn" @click="$emit('go-title')" title="返回主菜单">
        <span class="btn-icon">🏠</span>
        <span class="btn-label">主页</span>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { WorldState, CharacterStatus } from '../types'

const props = defineProps<{
  world: WorldState | null
  character: CharacterStatus | null
}>()

defineEmits<{
  (e: 'open-map'): void
  (e: 'advance-time'): void
  (e: 'open-history'): void
  (e: 'open-saves'): void
  (e: 'open-phone'): void
  (e: 'open-variables'): void
  (e: 'go-title'): void
}>()

const slotDisplayName = computed(() => {
  const map: Record<string, string> = {
    morning: '早晨 08:30',
    noon: '午间 12:15',
    afternoon: '午后 15:45',
    dusk: '傍晚 18:20',
    night: '夜晚 21:00',
  }
  return map[props.world?.time_slot || 'afternoon'] || '此时'
})

const stageDisplayName = computed(() => {
  const map: Record<string, string> = {
    acquaintance: '普通同学',
    friend: '熟悉好友',
    close: '暧昧亲密',
    lover: '恋人契约',
  }
  return map[props.character?.stage || 'friend'] || '朋友'
})
</script>

<style scoped>
.hud-container {
  position: absolute;
  top: 14px;
  left: 20px;
  right: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 40;
  pointer-events: none;
}

/* Cel Glow 暖纸漫画卡片基础类 */
.paper-card {
  pointer-events: auto;
  background: var(--dialogue-paper-solid, #fffdfa);
  border: 2px solid var(--dialogue-outline, #7c7066);
  border-radius: 12px;
  padding: 6px 16px;
  display: flex;
  align-items: center;
  box-shadow: 0 4px 0 rgba(74, 61, 54, 0.2);
  color: var(--dialogue-ink, #3e342f);
}

.hud-left {
  gap: 12px;
}

.date-badge {
  display: flex;
  gap: 6px;
  font-weight: 800;
  font-size: 14px;
}

.day-number {
  color: var(--dialogue-speech-ink, #8e3b2e);
}

.weekday {
  color: var(--dialogue-speech-muted, #9d6150);
}

.divider {
  width: 1.5px;
  height: 15px;
  background: var(--dialogue-rule, #e5dcd4);
}

.time-slot-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
}

.slot-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
}

.time-slot-badge.dusk .slot-dot {
  background: #ea580c;
}

.time-slot-badge.night .slot-dot {
  background: #6366f1;
}

.location-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  color: var(--dialogue-ink, #3e342f);
}

/* 中间好感度 */
.hud-center {
  flex-direction: column;
  padding: 5px 18px;
  gap: 3px;
}

.character-hud-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.char-name {
  font-weight: 800;
  font-size: 14px;
  color: var(--dialogue-speech-ink, #8e3b2e);
}

.stage-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 9999px;
  background: rgba(224, 123, 108, 0.15);
  color: var(--accent-hover, #cc6a5c);
  border: 1px solid rgba(224, 123, 108, 0.35);
}

.stage-tag.close {
  background: rgba(244, 63, 94, 0.18);
  color: #e11d48;
}

.stage-tag.lover {
  background: linear-gradient(135deg, #f43f5e, #ec4899);
  color: #ffffff;
}

.affection-meter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.heart-icon {
  font-size: 12px;
}

.meter-track {
  width: 100px;
  height: 7px;
  background: var(--dialogue-inner, #eee6df);
  border: 1px solid var(--dialogue-rule, #e5dcd4);
  border-radius: 9999px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, #f43f5e, #e07b6c);
  border-radius: 9999px;
  transition: width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.affection-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--dialogue-speech-muted, #9d6150);
  font-family: monospace;
}

/* 右侧操作按钮 */
.hud-right {
  gap: 6px;
  padding: 4px 10px;
}

.hud-btn {
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
  color: var(--dialogue-ink, #3e342f);
  font-weight: 700;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hud-btn:hover {
  background: rgba(224, 123, 108, 0.12);
  border-color: rgba(224, 123, 108, 0.3);
  color: var(--accent-hover, #cc6a5c);
  transform: translateY(-1px);
}

.hud-btn:active {
  transform: translateY(1px);
}

.hud-btn.phone-btn-highlight {
  background: rgba(224, 123, 108, 0.15);
  border-color: var(--accent, #e07b6c);
  color: var(--dialogue-speech-ink, #8e3b2e);
}

.btn-icon {
  font-size: 14px;
}

.btn-label {
  font-size: 12px;
}
</style>
