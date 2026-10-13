<template>
  <div class="input-bar-container">
    <!-- 漫画斜向贴纸快捷回应选项 (TownVnChoice 风格) -->
    <div class="quick-actions-bar">
      <span class="quick-title">快捷互动：</span>
      <div
        v-for="action in quickSuggestions"
        :key="action.text"
        class="vn-choice-pill"
        :class="{ disabled: disabled }"
        @click="!disabled && handleQuickSelect(action.text)"
      >
        <span class="choice-accent-dot"></span>
        <span class="choice-icon">{{ action.icon }}</span>
        <span class="choice-text">{{ action.text }}</span>
      </div>
    </div>

    <!-- 暖纸质感自由输入框与软糖立体发送按钮 -->
    <div class="input-row paper-input-panel">
      <input
        ref="inputRef"
        v-model="inputText"
        type="text"
        class="free-text-input"
        placeholder="写下你想对林雨晴说的话……（按回车发送）"
        :disabled="disabled"
        @keydown.enter.prevent="handleSend"
      />
      <button
        class="sticker-send-btn"
        :disabled="disabled || !inputText.trim()"
        @click="handleSend"
      >
        <span v-if="!disabled" class="btn-inner">
          <span class="btn-text">传达心意</span>
          <span class="btn-arrow">➔</span>
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
  { icon: '📖', text: '这本书讲了什么有趣的故事吗？' },
  { icon: '🥤', text: '渴了吗？我请你喝冰镇柑橘汽水吧！' },
  { icon: '🌸', text: '雨晴，你今天看起来格外有精神呢。' },
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
  max-width: 980px;
  margin: 10px auto 16px auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 30;
}

/* 漫画斜向贴纸快捷回应选项 (TownVnChoice) */
.quick-actions-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.quick-actions-bar::-webkit-scrollbar {
  display: none;
}

.quick-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--dialogue-speech-ink, #8e3b2e);
  background: var(--dialogue-paper-solid, #fffdfa);
  border: 1.5px solid var(--dialogue-outline, #7c7066);
  padding: 2px 8px;
  border-radius: 6px;
  box-shadow: 1px 2px 0 rgba(74, 61, 54, 0.15);
  white-space: nowrap;
}

.vn-choice-pill {
  background: var(--dialogue-paper-solid, #fffdfa);
  border: 1.5px solid var(--dialogue-outline, #7c7066);
  border-radius: 10px;
  padding: 5px 14px 4px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--dialogue-ink, #3e342f);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 3px 0 rgba(74, 61, 54, 0.18);
  transform: skewX(-3deg);
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  white-space: nowrap;
}

.vn-choice-pill:hover:not(.disabled) {
  border-color: var(--accent, #e07b6c);
  color: var(--dialogue-speech-ink, #8e3b2e);
  transform: translateY(-2px) skewX(-3deg);
  box-shadow: 0 5px 0 rgba(224, 123, 108, 0.3);
}

.vn-choice-pill:active:not(.disabled) {
  transform: translateY(2px) skewX(-3deg);
  box-shadow: 0 1px 0 rgba(74, 61, 54, 0.18);
}

.vn-choice-pill.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.choice-accent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent, #e07b6c);
}

.choice-icon {
  transform: skewX(3deg);
}

.choice-text {
  transform: skewX(3deg);
}

/* 暖纸输入条 */
.paper-input-panel {
  display: flex;
  align-items: center;
  background: var(--dialogue-paper, rgba(255, 253, 250, 0.96));
  border: 2px solid var(--dialogue-outline, #7c7066);
  border-radius: 14px;
  padding: 4px 6px 4px 16px;
  box-shadow: 0 5px 0 rgba(74, 61, 54, 0.2);
  transition: border-color 0.2s;
}

.paper-input-panel:focus-within {
  border-color: var(--accent, #e07b6c);
}

.free-text-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--dialogue-ink, #3e342f);
  font-size: 15px;
  font-weight: 500;
  outline: none;
  font-family: inherit;
}

.free-text-input::placeholder {
  color: var(--dialogue-speech-muted, #9d6150);
  opacity: 0.65;
}

/* 软糖立体贴纸按键 (LinsheButton 语言同源) */
.sticker-send-btn {
  background: linear-gradient(180deg, #e07b6c 0%, #e07b6c 55%, #cc6a5c 55%, #cc6a5c 100%);
  border: 2px solid var(--dialogue-outline-strong, #4a3d36);
  border-radius: 10px;
  color: #ffffff;
  padding: 8px 18px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 4px 0 rgba(74, 61, 54, 0.35);
  transition: all 0.15s ease-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sticker-send-btn:hover:not(:disabled) {
  background: linear-gradient(180deg, #ff8a7a 0%, #ff8a7a 55%, #e07b6c 55%, #e07b6c 100%);
  transform: translateY(-1px);
  box-shadow: 0 5px 0 rgba(74, 61, 54, 0.4);
}

/* 按下压扁下沉立体动效 */
.sticker-send-btn:active:not(:disabled) {
  transform: translateY(3px);
  box-shadow: 0 1px 0 rgba(74, 61, 54, 0.35);
}

.sticker-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(0.5);
  transform: none;
}

.btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-text {
  letter-spacing: 0.5px;
}

.btn-arrow {
  font-size: 14px;
}

/* 加载动画 */
.loading-spinner {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 3px 6px;
}

.dot {
  width: 5px;
  height: 5px;
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
  100% { transform: translateY(-3px); opacity: 1; }
}
</style>
