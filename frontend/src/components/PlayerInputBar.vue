<template>
  <div class="input-bar-container">
    <!-- 快捷互动行动气泡 -->
    <div class="quick-actions-bar">
      <span class="quick-label">快捷互动：</span>
      <button
        v-for="action in quickSuggestions"
        :key="action.text"
        class="quick-pill"
        :disabled="disabled"
        @click="handleQuickSelect(action.text)"
      >
        <span class="pill-icon">{{ action.icon }}</span>
        <span class="pill-text">{{ action.text }}</span>
      </button>
    </div>

    <!-- 自由输入框与提交操作 -->
    <div class="input-row glass-panel">
      <input
        ref="inputRef"
        v-model="inputText"
        type="text"
        class="free-text-input"
        placeholder="在这里输入你想对林雨晴说的话……（按回车发送）"
        :disabled="disabled"
        @keydown.enter.prevent="handleSend"
      />
      <button
        class="send-btn"
        :disabled="disabled || !inputText.trim()"
        @click="handleSend"
      >
        <span v-if="!disabled" class="btn-inner">
          <span>传达心意</span>
          <span class="send-arrow">➔</span>
        </span>
        <span v-else class="loading-spinner">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'send', message: string): void
}>()

const inputText = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

const quickSuggestions = [
  { icon: '📖', text: '这本书写了什么有趣的故事吗？' },
  { icon: '🥤', text: '渴了吗？我请你喝冰镇柑橘汽水吧！' },
  { icon: '✨', text: '雨晴，你今天看起来格外有精神呢。' },
  { icon: '🏖️', text: '这周末天气很好，要不要一起去海边吹吹风？' },
]

const handleQuickSelect = (text: string) => {
  inputText.value = text
  inputRef.value?.focus()
}

const handleSend = () => {
  if (props.disabled || !inputText.value.trim()) return
  const msg = inputText.value.trim()
  inputText.value = ''
  emit('send', msg)
}
</script>

<style scoped>
.input-bar-container {
  width: 100%;
  max-width: 960px;
  margin: 12px auto 20px auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 25;
}

/* 快捷互动小气泡 */
.quick-actions-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
  overflow-x: auto;
  scrollbar-width: none;
}

.quick-actions-bar::-webkit-scrollbar {
  display: none;
}

.quick-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
}

.quick-pill {
  background: rgba(30, 41, 59, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
  padding: 4px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #e2e8f0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.quick-pill:hover:not(:disabled) {
  background: rgba(56, 189, 248, 0.2);
  border-color: #38bdf8;
  transform: translateY(-1px);
}

.quick-pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 自由输入行 */
.glass-panel {
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  padding: 6px 8px 6px 18px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.free-text-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 15px;
  outline: none;
  font-family: inherit;
}

.free-text-input::placeholder {
  color: rgba(255, 255, 255, 0.38);
}

.send-btn {
  background: linear-gradient(135deg, #0284c7, #2563eb);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #ffffff;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #38bdf8, #3b82f6);
  box-shadow: 0 0 16px rgba(56, 189, 248, 0.5);
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
}

.send-arrow {
  font-size: 15px;
}

/* 加载动画三点 */
.loading-spinner {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 4px 8px;
}

.dot {
  width: 6px;
  height: 6px;
  background: #ffffff;
  border-radius: 50%;
  animation: bounceDot 0.8s infinite alternate;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounceDot {
  0% { transform: translateY(0); opacity: 0.4; }
  100% { transform: translateY(-4px); opacity: 1; }
}
</style>
