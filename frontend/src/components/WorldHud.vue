<template>
  <header class="hud-container">
    <!-- 左侧：世界时空与地点信息 -->
    <div class="hud-left glass-card">
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

    <!-- 中间：角色好感度与心动仪表盘 -->
    <div class="hud-center glass-card" v-if="character">
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

    <!-- 右侧：全局操作按钮组 -->
    <div class="hud-right glass-card">
      <button class="hud-btn phone-btn-highlight" @click="$emit('open-phone')" title="智能手机 (P)">
        <span class="btn-icon">📱</span>
        <span class="btn-label">手机</span>
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
  top: 16px;
  left: 20px;
  right: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 30;
  pointer-events: none;
}

.glass-card {
  pointer-events: auto;
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 9999px;
  padding: 8px 18px;
  display: flex;
  align-items: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  color: #f8fafc;
}

.hud-left {
  gap: 12px;
}

.date-badge {
  display: flex;
  gap: 6px;
  font-weight: 700;
  font-size: 14px;
}

.day-number {
  color: #38bdf8;
}

.weekday {
  color: #94a3b8;
}

.divider {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.15);
}

.time-slot-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}

.slot-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 8px #fbbf24;
}

.time-slot-badge.dusk .slot-dot {
  background: #f97316;
  box-shadow: 0 0 8px #f97316;
}

.time-slot-badge.night .slot-dot {
  background: #818cf8;
  box-shadow: 0 0 8px #818cf8;
}

.location-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #e2e8f0;
}

/* 中间好感度 */
.hud-center {
  flex-direction: column;
  padding: 6px 20px;
  gap: 4px;
}

.character-hud-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.char-name {
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.5px;
}

.stage-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 9999px;
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.4);
}

.stage-tag.close {
  background: rgba(244, 63, 94, 0.2);
  color: #fb7185;
  border-color: rgba(244, 63, 94, 0.4);
}

.stage-tag.lover {
  background: rgba(236, 72, 153, 0.3);
  color: #f472b6;
  border-color: #ec4899;
}

.affection-meter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.heart-icon {
  font-size: 13px;
  animation: pulseHeart 1.8s infinite;
}

@keyframes pulseHeart {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

.meter-track {
  width: 110px;
  height: 7px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 9999px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, #ec4899, #f43f5e);
  border-radius: 9999px;
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.affection-num {
  font-size: 12px;
  color: #cbd5e1;
  font-family: monospace;
}

/* 右侧操作按钮 */
.hud-right {
  gap: 8px;
  padding: 4px 12px;
}

.hud-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 8px;
  color: #e2e8f0;
  transition: all 0.2s ease;
}

.hud-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.hud-btn.phone-btn-highlight {
  background: rgba(56, 189, 248, 0.2);
  border: 1px solid rgba(56, 189, 248, 0.4);
}

.hud-btn.phone-btn-highlight:hover {
  background: rgba(56, 189, 248, 0.35);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
}

.btn-icon {
  font-size: 15px;
}

.btn-label {
  font-size: 13px;
  font-weight: 500;
}
</style>
