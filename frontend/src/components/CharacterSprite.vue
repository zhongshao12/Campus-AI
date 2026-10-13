<template>
  <div class="character-sprite-container" :class="[expression, { 'is-speaking': isSpeaking }]">
    <!-- 人物立绘核心矢量绘制 -->
    <div class="sprite-canvas">
      <svg viewBox="0 0 400 680" class="anime-girl-svg" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="hairGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#2c3038" />
            <stop offset="50%" stop-color="#1f232b" />
            <stop offset="100%" stop-color="#14171d" />
          </linearGradient>
          <linearGradient id="hairHighlight" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="rgba(147, 197, 253, 0.45)" />
            <stop offset="100%" stop-color="rgba(147, 197, 253, 0)" />
          </linearGradient>
          <linearGradient id="skinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#fff5f0" />
            <stop offset="100%" stop-color="#fee7dc" />
          </linearGradient>
          <linearGradient id="uniformGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" />
            <stop offset="100%" stop-color="#f0f4f8" />
          </linearGradient>
          <linearGradient id="skirtGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#1e3a8a" />
            <stop offset="100%" stop-color="#0f172a" />
          </linearGradient>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <!-- 后发 (长及肩微卷) -->
        <g class="back-hair">
          <path d="M120 180 C80 260 70 420 100 520 C120 480 140 380 140 280 Z" fill="url(#hairGrad)" />
          <path d="M280 180 C320 260 330 420 300 520 C280 480 260 380 260 280 Z" fill="url(#hairGrad)" />
        </g>

        <!-- 脖子与身体 -->
        <path d="M185 240 L215 240 L220 280 L180 280 Z" fill="url(#skinGrad)" />
        
        <!-- 水手服上衣 -->
        <g class="torso">
          <path d="M140 280 Q200 270 260 280 L280 450 L120 450 Z" fill="url(#uniformGrad)" stroke="#cbd5e1" stroke-width="1.5" />
          <!-- 水手领 (Navy Collar) -->
          <path d="M160 280 L200 360 L240 280 L275 285 L260 340 L200 390 L140 340 L125 285 Z" fill="#1e3a8a" />
          <path d="M165 285 L200 350 L235 285" fill="none" stroke="#ffffff" stroke-width="2" />
          <!-- 红色领结 (Red Ribbon) -->
          <path d="M190 350 L175 390 L195 380 L200 360 L205 380 L225 390 L210 350 Z" fill="#e11d48" />
          <circle cx="200" cy="358" r="6" fill="#be123c" />
          <!-- 百褶裙 -->
          <path d="M120 450 L280 450 L310 600 L90 600 Z" fill="url(#skirtGrad)" />
          <line x1="150" y1="450" x2="135" y2="600" stroke="#334155" stroke-width="2" />
          <line x1="180" y1="450" x2="175" y2="600" stroke="#334155" stroke-width="2" />
          <line x1="220" y1="450" x2="225" y2="600" stroke="#334155" stroke-width="2" />
          <line x1="250" y1="450" x2="265" y2="600" stroke="#334155" stroke-width="2" />
        </g>

        <!-- 脸型 -->
        <g class="head">
          <path d="M140 180 C130 250 170 275 200 275 C230 275 270 250 260 180 C250 130 150 130 140 180 Z" fill="url(#skinGrad)" />
        </g>

        <!-- 表情差分：脸红腮红 -->
        <g class="blush-layer" v-if="expression === 'blush' || expression === 'happy'">
          <ellipse cx="160" cy="225" rx="14" ry="7" fill="#fb7185" opacity="0.6" />
          <ellipse cx="240" cy="225" rx="14" ry="7" fill="#fb7185" opacity="0.6" />
          <line x1="153" y1="222" x2="167" y2="228" stroke="#f43f5e" stroke-width="1.5" />
          <line x1="233" y1="222" x2="247" y2="228" stroke="#f43f5e" stroke-width="1.5" />
        </g>

        <!-- 表情差分：眼睛 -->
        <g class="eyes">
          <!-- 左眼 -->
          <g v-if="expression === 'happy'">
            <path d="M152 215 Q165 205 178 215" fill="none" stroke="#1e293b" stroke-width="4" stroke-linecap="round" />
          </g>
          <g v-else>
            <!-- 眼白 -->
            <ellipse cx="165" cy="210" rx="12" ry="14" fill="#ffffff" />
            <!-- 瞳孔 (浅蓝眼眸) -->
            <ellipse cx="166" cy="211" rx="9" ry="11" fill="#38bdf8" />
            <circle cx="166" cy="211" r="5" fill="#0284c7" />
            <!-- 高光 -->
            <circle cx="163" cy="207" r="3.5" fill="#ffffff" />
            <circle cx="169" cy="214" r="1.8" fill="#ffffff" />
            <!-- 上睫毛 -->
            <path d="M150 205 Q165 195 180 205" fill="none" stroke="#0f172a" stroke-width="3.5" stroke-linecap="round" />
          </g>

          <!-- 右眼 -->
          <g v-if="expression === 'happy'">
            <path d="M222 215 Q235 205 248 215" fill="none" stroke="#1e293b" stroke-width="4" stroke-linecap="round" />
          </g>
          <g v-else>
            <ellipse cx="235" cy="210" rx="12" ry="14" fill="#ffffff" />
            <ellipse cx="234" cy="211" rx="9" ry="11" fill="#38bdf8" />
            <circle cx="234" cy="211" r="5" fill="#0284c7" />
            <circle cx="231" cy="207" r="3.5" fill="#ffffff" />
            <circle cx="237" cy="214" r="1.8" fill="#ffffff" />
            <path d="M220 205 Q235 195 250 205" fill="none" stroke="#0f172a" stroke-width="3.5" stroke-linecap="round" />
          </g>
        </g>

        <!-- 表情差分：眉毛 -->
        <g class="eyebrows">
          <path v-if="expression === 'sad' || expression === 'thinking'" d="M152 195 Q165 192 178 198" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" />
          <path v-else-if="expression === 'surprised'" d="M152 190 Q165 188 178 194" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" />
          <path v-else d="M152 194 Q165 190 178 195" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" />

          <path v-if="expression === 'sad' || expression === 'thinking'" d="M222 198 Q235 192 248 195" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" />
          <path v-else-if="expression === 'surprised'" d="M222 194 Q235 188 248 190" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" />
          <path v-else d="M222 195 Q235 190 248 194" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" />
        </g>

        <!-- 表情差分：嘴型 -->
        <g class="mouth">
          <!-- 微笑 -->
          <path v-if="expression === 'happy'" d="M192 246 Q200 256 208 246" fill="#fda4af" stroke="#e11d48" stroke-width="2" stroke-linecap="round" />
          <!-- 惊讶小嘴 -->
          <ellipse v-else-if="expression === 'surprised'" cx="200" cy="248" rx="4" ry="6" fill="#f43f5e" />
          <!-- 鼓嘴撅嘴 -->
          <path v-else-if="expression === 'pout'" d="M194 249 Q200 244 206 249" fill="none" stroke="#e11d48" stroke-width="2.5" stroke-linecap="round" />
          <!-- 害羞轻咬唇 -->
          <path v-else-if="expression === 'blush'" d="M194 247 Q200 251 206 247" fill="none" stroke="#e11d48" stroke-width="2" stroke-linecap="round" />
          <!-- 默认小嘴 -->
          <path v-else d="M195 248 Q200 250 205 248" fill="none" stroke="#e11d48" stroke-width="1.8" stroke-linecap="round" />
        </g>

        <!-- 前发齐刘海与发带 -->
        <g class="front-hair">
          <!-- 齐刘海发片 -->
          <path d="M135 170 Q200 130 265 170 C270 200 255 210 245 220 C235 185 220 180 200 180 C180 180 165 185 155 220 C145 210 130 200 135 170 Z" fill="url(#hairGrad)" />
          <!-- 发丝高光光环 (Angel Ring) -->
          <ellipse cx="200" cy="165" rx="60" ry="12" fill="url(#hairHighlight)" />
          <!-- 蓝色发饰蝴蝶结 -->
          <path d="M140 160 L125 145 L135 175 Z" fill="#38bdf8" />
          <path d="M140 160 L155 145 L145 175 Z" fill="#38bdf8" />
          <circle cx="140" cy="160" r="4" fill="#0284c7" />
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    expression?: string
    isSpeaking?: boolean
  }>(),
  {
    expression: 'neutral',
    isSpeaking: false,
  }
)
</script>

<style scoped>
.character-sprite-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  pointer-events: none;
  animation: breathing 4s ease-in-out infinite alternate;
}

.sprite-canvas {
  width: 520px;
  max-width: 90vw;
  height: 90%;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  filter: drop-shadow(0 12px 30px rgba(0, 0, 0, 0.45));
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.anime-girl-svg {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 角色呼吸微动效 */
@keyframes breathing {
  0% {
    transform: translateY(0px) scale(1);
  }
  100% {
    transform: translateY(-8px) scale(1.008);
  }
}

/* 害羞时轻微扭动与小跳动 */
.character-sprite-container.blush .sprite-canvas {
  animation: shyWiggle 2.5s ease-in-out infinite alternate;
}

@keyframes shyWiggle {
  0% {
    transform: rotate(-1deg) translateY(2px);
  }
  100% {
    transform: rotate(1.2deg) translateY(-4px);
  }
}

/* 惊讶时小震颤 */
.character-sprite-container.surprised .sprite-canvas {
  transform: translateY(-16px) scale(1.02);
}

/* 说话时轻微上下节奏 */
.character-sprite-container.is-speaking .sprite-canvas {
  animation: speakingMotion 0.6s ease-in-out infinite alternate;
}

@keyframes speakingMotion {
  0% {
    transform: translateY(0);
  }
  100% {
    transform: translateY(-4px);
  }
}
</style>
