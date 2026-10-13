<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="save-card glass-modal">
      <div class="modal-header">
        <div class="tabs">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'save' }"
            @click="activeTab = 'save'"
          >
            💾 保存游戏
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'load' }"
            @click="activeTab = 'load'"
          >
            📂 读取游戏
          </button>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="slots-container">
        <div
          v-for="idx in 6"
          :key="idx"
          class="slot-item"
          :class="{ empty: !getSlot(idx) }"
          @click="handleSlotAction(idx)"
        >
          <div class="slot-num">SLOT 0{{ idx }}</div>
          <div class="slot-body" v-if="getSlot(idx)">
            <div class="slot-title">{{ getSlot(idx)?.title }}</div>
            <div class="slot-meta">
              <span>📅 Day {{ getSlot(idx)?.preview.day }}</span>
              <span>📍 {{ getSlot(idx)?.preview.location }}</span>
              <span>💖 好感度 {{ getSlot(idx)?.preview.lin_affection }}</span>
            </div>
            <div class="slot-time">{{ getSlot(idx)?.saved_at }}</div>
          </div>
          <div class="slot-empty-body" v-else>
            <span>-- 空白记录存档位 --</span>
            <span class="slot-action-tip">
              {{ activeTab === 'save' ? '点击保存至此处' : '暂无数据' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { gameApi } from '../services/api'
import type { SaveSlotItem } from '../types'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toast', msg: string): void
  (e: 'reloaded'): void
}>()

const activeTab = ref<'save' | 'load'>('save')
const slots = ref<SaveSlotItem[]>([])

const loadSlots = async () => {
  try {
    slots.value = await gameApi.listSaveSlots()
  } catch (err) {
    console.error('加载存档列表失败:', err)
  }
}

const getSlot = (idx: number) => {
  return slots.value.find((s) => s.slot_index === idx)
}

const handleSlotAction = async (idx: number) => {
  if (activeTab.value === 'save') {
    try {
      await gameApi.saveGame(idx, `大学漫步日记 #0${idx}`)
      emit('toast', `已成功保存到 0${idx} 号槽位！`)
      await loadSlots()
    } catch (err) {
      emit('toast', '保存失败')
    }
  } else {
    // 读取
    const target = getSlot(idx)
    if (!target) {
      emit('toast', '该槽位没有可读取的数据')
      return
    }
    try {
      await gameApi.loadGame(idx)
      emit('toast', `已载入 0${idx} 号存档进度！`)
      emit('reloaded')
      emit('close')
    } catch (err) {
      emit('toast', '读档失败')
    }
  }
}

onMounted(() => {
  loadSlots()
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 50;
  padding: 20px;
}

.glass-modal {
  background: var(--dialogue-paper-solid, #fffdfa);
  border: 2px solid var(--dialogue-outline, #7c7066);
  border-radius: 20px;
  width: 100%;
  max-width: 680px;
  padding: 24px 28px;
  box-shadow: 0 10px 0 rgba(74, 61, 54, 0.25), 0 24px 50px rgba(0, 0, 0, 0.35);
  color: var(--dialogue-ink, #3e342f);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1.5px solid var(--dialogue-rule, #e5dcd4);
  padding-bottom: 12px;
}

.tabs {
  display: flex;
  gap: 12px;
}

.tab-btn {
  background: transparent;
  border: 1.5px solid transparent;
  font-size: 15px;
  font-weight: 800;
  color: var(--dialogue-speech-muted, #9d6150);
  cursor: pointer;
  padding: 6px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--accent, #e07b6c);
  border-color: var(--accent-dark, #8e3b2e);
  color: #ffffff;
  box-shadow: 0 3px 0 rgba(142, 59, 46, 0.3);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--dialogue-speech-muted, #9d6150);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}

.close-btn:hover {
  background: rgba(224, 123, 108, 0.15);
  color: var(--accent, #e07b6c);
}

.slots-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.slot-item {
  background: #ffffff;
  border: 1.5px solid #d0c3b8;
  border-radius: 14px;
  padding: 14px 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 3px 0 rgba(74, 61, 54, 0.12);
  transition: all 0.2s;
}

.slot-item:hover {
  border-color: var(--accent, #e07b6c);
  transform: translateY(-2px);
  box-shadow: 0 5px 0 rgba(224, 123, 108, 0.25);
}

.slot-item.empty {
  opacity: 0.65;
}

.slot-num {
  font-size: 11px;
  font-weight: 800;
  color: var(--accent, #e07b6c);
  letter-spacing: 1px;
}

.slot-title {
  font-weight: 700;
  font-size: 14px;
  color: var(--dialogue-speech-ink, #8e3b2e);
}

.slot-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--dialogue-ink, #3e342f);
}

.slot-time {
  font-size: 11px;
  color: var(--dialogue-speech-muted, #9d6150);
}

.slot-empty-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
  color: var(--dialogue-speech-muted, #9d6150);
  font-size: 13px;
  gap: 4px;
}

.slot-action-tip {
  font-size: 11px;
  color: var(--accent, #e07b6c);
  font-weight: 700;
}
</style>
