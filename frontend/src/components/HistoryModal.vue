<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="history-card glass-modal">
      <div class="modal-header">
        <h2 class="title">📜 对话回忆录 (Backlog)</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="history-list" ref="listRef">
        <div v-if="logs.length === 0" class="empty-hint">
          -- 暂无历史对话记录，去跟林雨晴打个招呼吧 --
        </div>
        <div
          v-for="(log, i) in logs"
          :key="i"
          class="history-row"
          :class="{ 'is-player': log.speaker === '你' }"
        >
          <div class="speaker-label">{{ log.speaker }}:</div>
          <div class="dialogue-bubble">{{ log.text }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'

const props = defineProps<{
  logs: Array<{ speaker: string; text: string; emotion?: string }>
}>()

defineEmits<{
  (e: 'close'): void
}>()

const listRef = ref<HTMLDivElement | null>(null)

onMounted(() => {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
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
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  padding-bottom: 10px;
}

.title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: #38bdf8;
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 6px;
}

.empty-hint {
  text-align: center;
  color: #64748b;
  padding: 40px 0;
  font-size: 14px;
}

.history-row {
  display: flex;
  gap: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.speaker-label {
  font-weight: 700;
  color: #38bdf8;
  min-width: 60px;
}

.history-row.is-player .speaker-label {
  color: #94a3b8;
}

.dialogue-bubble {
  color: #e2e8f0;
  flex: 1;
}
</style>
