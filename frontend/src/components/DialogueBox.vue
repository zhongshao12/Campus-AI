<template>
  <div class="galgame-dialogue-wrapper" @click="handleBoxClick">
    <!-- 角色名字标签牌 -->
    <div class="speaker-tag" :class="{ 'is-narrator': speaker === '旁白' }">
      <span class="speaker-dot"></span>
      <span class="speaker-text">{{ speaker }}</span>
      <span class="emotion-badge" v-if="emotion && emotion !== 'neutral'">
        {{ emotionText }}
      </span>
    </div>

    <!-- 经典半透明对话主框体 -->
    <div class="dialogue-box">
      <!-- 细微小动作提示 -->
      <div class="action-hint" v-if="action">
        <span class="action-bracket">[</span>
        <span class="action-content">{{ action }}</span>
        <span class="action-bracket">]</span>
      </div>

      <!-- 核心对白内容 (支持打字机动效) -->
      <div class="dialogue-content">
        <span class="text-rendered">{{ displayedText }}</span>
        <span class="typewriter-cursor" v-if="isTyping">|</span>
      </div>

      <!-- 内心独白 (微弱浅紫半透明) -->
      <div class="inner-thought" v-if="innerThought && !isTyping">
        <span class="thought-icon">💭</span>
        <span class="thought-text">（{{ innerThought }}）</span>
      </div>

      <!-- 右下角闪烁小箭头 -->
      <div class="continue-indicator" :class="{ ready: !isTyping }">
        ▼
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'

const props = withDefaults(
  defineProps<{
    speaker?: string
    text: string
    emotion?: string
    action?: string | null
    innerThought?: string | null
  }>(),
  {
    speaker: '林雨晴',
    emotion: 'neutral',
    action: null,
    innerThought: null,
  }
)

const displayedText = ref('')
const isTyping = ref(false)
let timer: any = null

const emotionText = computed(() => {
  const map: Record<string, string> = {
    happy: '微笑',
    blush: '脸红心动',
    surprised: '惊讶',
    thinking: '思考',
    pout: '鼓嘴微嗔',
    sad: '低落',
  }
  return map[props.emotion || 'neutral'] || ''
})

const startTypewriter = (fullText: string) => {
  if (timer) clearInterval(timer)
  displayedText.value = ''
  isTyping.value = true

  let index = 0
  timer = setInterval(() => {
    if (index < fullText.length) {
      displayedText.value += fullText[index]
      index++
    } else {
      isTyping.value = false
      clearInterval(timer)
      timer = null
    }
  }, 22) // 22ms 逐字流畅呈现
}

const handleBoxClick = () => {
  // 点击快速跳过打字机，直接显示完整对白
  if (isTyping.value && timer) {
    clearInterval(timer)
    timer = null
    displayedText.value = props.text
    isTyping.value = false
  }
}

watch(
  () => props.text,
  (newVal) => {
    startTypewriter(newVal || '')
  },
  { immediate: true }
)
</script>

<style scoped>
.galgame-dialogue-wrapper {
  position: relative;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  cursor: pointer;
  user-select: none;
  z-index: 25;
}

/* 角色姓名标牌 */
.speaker-tag {
  position: absolute;
  top: -36px;
  left: 28px;
  background: linear-gradient(135deg, rgba(30, 58, 138, 0.95), rgba(15, 23, 42, 0.95));
  border: 1px solid rgba(147, 197, 253, 0.45);
  border-bottom: none;
  border-radius: 14px 14px 0 0;
  padding: 6px 24px;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(10px);
}

.speaker-tag.is-narrator {
  background: linear-gradient(135deg, rgba(71, 85, 105, 0.95), rgba(30, 41, 59, 0.95));
  border-color: rgba(203, 213, 225, 0.3);
}

.speaker-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
}

.speaker-text {
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 1px;
}

.emotion-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 9999px;
  background: rgba(244, 63, 94, 0.25);
  color: #fb7185;
  border: 1px solid rgba(244, 63, 94, 0.5);
  margin-left: 4px;
}

/* 对话框主体 */
.dialogue-box {
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 18px;
  padding: 24px 32px;
  min-height: 125px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 8px;
}

.action-hint {
  font-size: 14px;
  color: #93c5fd;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-content {
  color: #60a5fa;
}

.dialogue-content {
  font-size: 18px;
  line-height: 1.7;
  color: #f8fafc;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.typewriter-cursor {
  display: inline-block;
  margin-left: 2px;
  color: #38bdf8;
  animation: blink 0.7s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.inner-thought {
  margin-top: 4px;
  font-size: 14px;
  color: #c084fc;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 6px;
}

.continue-indicator {
  position: absolute;
  right: 24px;
  bottom: 14px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.continue-indicator.ready {
  color: #38bdf8;
  animation: floatArrow 1.2s infinite ease-in-out;
}

@keyframes floatArrow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(4px); }
}
</style>
