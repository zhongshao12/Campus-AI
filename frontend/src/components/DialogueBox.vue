<template>
  <div class="galgame-dialogue-wrapper" @click="handleBoxClick">
    <!-- 斜向漫画贴纸风格姓名铭牌 (参考 Cel Glow 漫画标签设计) -->
    <div class="speaker-tag" :class="{ 'is-narrator': speaker === '旁白' }">
      <div class="tag-corner-accent"></div>
      <span class="speaker-text">{{ speaker }}</span>
      <span class="emotion-badge" v-if="emotion && emotion !== 'neutral'">
        {{ emotionText }}
      </span>
    </div>

    <!-- 经典切角暖纸对话主框体 (TownDialogueStage 风格) -->
    <div class="dialogue-box">
      <!-- 内部装饰双层线 -->
      <div class="dialogue-inner-frame">
        <!-- 动作描写 (棕橙色贴纸风) -->
        <div class="action-hint" v-if="action">
          <span class="action-bracket">「</span>
          <span class="action-content">{{ action }}</span>
          <span class="action-bracket">」</span>
        </div>

        <!-- 核心对白内容 (逐字打字机演出，深珊瑚墨色) -->
        <div class="dialogue-content">
          <span class="text-rendered">{{ displayedText }}</span>
          <span class="typewriter-cursor" v-if="isTyping"></span>
        </div>

        <!-- 角色内心心声 (柔和紫色心声独白) -->
        <div class="inner-thought" v-if="innerThought && !isTyping">
          <span class="thought-icon">💭</span>
          <span class="thought-text">（{{ innerThought }}）</span>
        </div>

        <!-- 右下角珊瑚跳动推进指示标 -->
        <div class="continue-indicator" :class="{ ready: !isTyping }">
          ▼
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

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
    thinking: '沉思',
    pout: '微嗔',
    sad: '失落',
    angry: '生气',
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
  }, 22)
}

const handleBoxClick = () => {
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
  margin: 0 auto;
  cursor: pointer;
  user-select: none;
  z-index: 30;
}

/* 姓名铭牌：漫画斜向贴纸标签 (Cel Glow) */
.speaker-tag {
  position: absolute;
  top: -34px;
  left: 36px;
  background: var(--dialogue-paper-solid, #fffdfa);
  border: 2px solid var(--dialogue-outline, #7c7066);
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  padding: 5px 22px 4px 18px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 2px -3px 0 rgba(74, 61, 54, 0.15);
  transform: skewX(-4deg);
  z-index: 32;
}

.speaker-tag.is-narrator {
  background: #f5f0ea;
}

/* 珊瑚色贴纸小角标 */
.tag-corner-accent {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  background: var(--accent, #e07b6c);
}

.speaker-text {
  font-weight: 800;
  font-size: 16px;
  letter-spacing: 1px;
  color: var(--dialogue-speech-ink, #8e3b2e);
  transform: skewX(4deg); /* 保持文字直立 */
}

.speaker-tag.is-narrator .speaker-text {
  color: #554a43;
}

.emotion-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 9999px;
  background: rgba(224, 123, 108, 0.15);
  color: var(--accent-hover, #cc6a5c);
  border: 1px solid rgba(224, 123, 108, 0.35);
  transform: skewX(4deg);
}

/* 核心切角暖纸对话框 (TownDialogueStage) */
.dialogue-box {
  background: var(--dialogue-paper, rgba(255, 253, 250, 0.96));
  border: 2px solid var(--dialogue-outline, #7c7066);
  border-radius: 16px;
  /* 漫画切角多边形视觉 */
  clip-path: polygon(
    14px 0%, 100% 0%,
    100% calc(100% - 14px), calc(100% - 14px) 100%,
    0% 100%, 0% 14px
  );
  box-shadow: 0 8px 0 rgba(74, 61, 54, 0.22), 0 16px 36px rgba(0, 0, 0, 0.2);
  padding: 6px;
  position: relative;
  transition: transform 0.2s ease;
}

/* 内层细描边内衬 */
.dialogue-inner-frame {
  border: 1px dashed var(--dialogue-inner, #eee6df);
  border-radius: 12px;
  padding: 20px 28px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 8px;
  position: relative;
}

/* 动作描写 */
.action-hint {
  font-size: 14px;
  font-weight: 600;
  color: var(--dialogue-speech-muted, #9d6150);
  display: flex;
  align-items: center;
  gap: 2px;
}

.action-content {
  color: #c2410c;
}

/* 对话正文 */
.dialogue-content {
  font-size: 18px;
  line-height: 1.75;
  color: var(--dialogue-ink, #3e342f);
  font-weight: 600;
  letter-spacing: 0.5px;
}

.typewriter-cursor {
  display: inline-block;
  width: 3px;
  height: 18px;
  background: var(--accent, #e07b6c);
  margin-left: 4px;
  vertical-align: middle;
  animation: celCursorBlink 0.7s infinite;
}

@keyframes celCursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 内心独白 */
.inner-thought {
  margin-top: 4px;
  font-size: 14px;
  color: #8b5cf6;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 右下角跳动推进标记 */
.continue-indicator {
  position: absolute;
  right: 18px;
  bottom: 12px;
  font-size: 13px;
  color: var(--dialogue-speech-muted, #9d6150);
  opacity: 0.4;
  transition: all 0.2s;
}

.continue-indicator.ready {
  color: var(--accent, #e07b6c);
  opacity: 1;
  animation: carrotJump 0.9s infinite alternate ease-in-out;
}

@keyframes carrotJump {
  0% { transform: translateY(0); }
  100% { transform: translateY(4px); }
}
</style>
