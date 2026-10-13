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
  background: rgba(15, 23, 42, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  width: 100%;
  max-width: 680px;
  padding: 24px 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
  color: #f8fafc;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  padding-bottom: 12px;
}

.tabs {
  display: flex;
  gap: 12px;
}

.tab-btn {
  background: transparent;
  border: none;
  font-size: 16px;
  font-weight: 700;
  color: #94a3b8;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 8px;
  transition: all 0.2s;
}

.tab-btn.active {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.slots-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.slot-item {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 14px 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.2s;
}

.slot-item:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: #38bdf8;
  transform: translateY(-2px);
}

.slot-item.empty {
  opacity: 0.6;
}

.slot-num {
  font-size: 11px;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: 1px;
}

.slot-title {
  font-weight: 600;
  font-size: 14px;
  color: #f1f5f9;
}

.slot-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #cbd5e1;
}

.slot-time {
  font-size: 11px;
  color: #64748b;
}

.slot-empty-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
  color: #64748b;
  font-size: 13px;
  gap: 4px;
}

.slot-action-tip {
  font-size: 11px;
  color: #0284c7;
}
</style>
