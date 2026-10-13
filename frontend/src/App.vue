<template>
  <div class="app-root">
    <!-- 1. 首页主菜单模式 (Title Screen) -->
    <transition name="fade">
      <TitleScreen
        v-if="viewMode === 'title'"
        @start-game="handleStartGame"
        @continue-game="showSaves = true"
        @open-settings="showSettings = true"
      />
    </transition>

    <!-- 2. 游戏舞台模式 (Main Galgame Stage) -->
    <div
      v-if="viewMode === 'game'"
      class="galgame-stage"
      :class="[currentLocation, currentTimeSlot]"
    >
      <!-- 背景场景图与氛围滤镜 -->
      <div class="scene-background">
        <div class="ambient-glow"></div>
        <div class="sunbeam-overlay" v-if="currentTimeSlot !== 'night'"></div>
        <div class="night-stars" v-else></div>
      </div>

      <!-- 顶部世界状态 HUD 导航条 -->
      <WorldHud
        :world="gameStore.world"
        :character="gameStore.character"
        @open-phone="showPhone = true"
        @open-variables="showVariables = true"
        @open-map="showMap = true"
        @advance-time="gameStore.advanceTimeSlot"
        @open-history="showHistory = true"
        @open-saves="showSaves = true"
        @go-title="viewMode = 'title'"
      />

      <!-- 角色立绘舞台层 (林雨晴在场时居中展现) -->
      <main class="character-stage" v-if="isCharacterPresent">
        <CharacterSprite
          :expression="gameStore.currentExpression"
          :is-speaking="gameStore.isGenerating"
        />
      </main>
      <main class="empty-stage" v-else>
        <div class="empty-notice glass-card">
          <span>🍃 这里暂时空无一人，你可以四处看看，或者推进时间等待其他同学到来……</span>
        </div>
      </main>

      <!-- 底部互动交互区 (经典 Gal 对话框 + 自由输入栏) -->
      <footer class="interaction-area">
        <DialogueBox
          :speaker="gameStore.currentSpeaker"
          :text="gameStore.currentDialogue"
          :emotion="gameStore.currentEmotion"
          :action="gameStore.currentAction"
          :inner-thought="gameStore.currentInnerThought"
        />

        <PlayerInputBar
          :disabled="gameStore.isGenerating"
          @send="handleUserSend"
        />
      </footer>
    </div>

    <!-- 3. 全局弹窗层 (手机/地图/存档/设置/回顾/CG) -->

    <!-- 智能手机系统浮窗 -->
    <transition name="phone-slide">
      <Smartphone
        v-if="showPhone"
        @close="showPhone = false"
        @toast="gameStore.showToast"
      />
    </transition>

    <!-- 全局状态提示 Toast (好感度增加/系统事件) -->
    <transition name="toast-fade">
      <div class="toast-popup" v-if="gameStore.toastMessage">
        <span class="toast-text">{{ gameStore.toastMessage }}</span>
      </div>
    </transition>

    <!-- 专属剧情 CG 解锁弹窗 -->
    <transition name="cg-pop">
      <div class="cg-modal" v-if="gameStore.activeCgUrl" @click="gameStore.activeCgUrl = null">
        <div class="cg-frame">
          <img :src="gameStore.activeCgUrl" alt="剧情CG" class="cg-img" />
          <div class="cg-caption">✨ 获得了新的回忆插画（点击任意位置收起）</div>
        </div>
      </div>
    </transition>

    <!-- 校园地图漫步弹窗 -->
    <MapModal
      v-if="showMap"
      :current-location="gameStore.world?.player_location"
      @close="showMap = false"
      @select="gameStore.moveTo"
    />

    <!-- 存档/读档系统弹窗 -->
    <SaveModal
      v-if="showSaves"
      @close="showSaves = false"
      @toast="gameStore.showToast"
      @reloaded="handleSaveLoaded"
    />

    <!-- 对话历史回忆弹窗 -->
    <HistoryModal
      v-if="showHistory"
      :logs="gameStore.historyLogs"
      @close="showHistory = false"
    />

    <!-- 变量与状态监控面板 -->
    <VariablePanel
      v-if="showVariables"
      @close="showVariables = false"
      @toast="gameStore.showToast"
    />

    <!-- 游戏设置弹窗 (LLM Key / ComfyUI) -->
    <SettingsModal
      v-if="showSettings"
      @close="showSettings = false"
      @toast="gameStore.showToast"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useGameStore } from './stores/game'
import TitleScreen from './components/TitleScreen.vue'
import WorldHud from './components/WorldHud.vue'
import CharacterSprite from './components/CharacterSprite.vue'
import DialogueBox from './components/DialogueBox.vue'
import PlayerInputBar from './components/PlayerInputBar.vue'
import MapModal from './components/MapModal.vue'
import SaveModal from './components/SaveModal.vue'
import HistoryModal from './components/HistoryModal.vue'
import Smartphone from './components/Smartphone.vue'
import SettingsModal from './components/SettingsModal.vue'
import VariablePanel from './components/VariablePanel.vue'

const gameStore = useGameStore()

// 视图模式: 'title' (首页) | 'game' (游玩)
const viewMode = ref<'title' | 'game'>('title')

const showPhone = ref(false)
const showVariables = ref(false)
const showMap = ref(false)
const showSaves = ref(false)
const showHistory = ref(false)
const showSettings = ref(false)

const currentLocation = computed(() => gameStore.world?.player_location || 'library')
const currentTimeSlot = computed(() => gameStore.world?.time_slot || 'afternoon')

// 判断林雨晴是否真实在当前地点 (修复旧 speaker 残留导致缺席 NPC 仍显示在立绘层的问题)
const isCharacterPresent = computed(() => {
  const chars = gameStore.world?.present_characters || []
  return chars.includes('lin_yuqing')
})

const handleStartGame = async () => {
  viewMode.value = 'game'
  await gameStore.startNewGame()
}

const handleSaveLoaded = async () => {
  await gameStore.reloadFromSave()
  viewMode.value = 'game'
}

const handleUserSend = (msg: string) => {
  gameStore.sendMessage(msg)
}

// 键盘快捷键监听: 'P' 呼出/关闭手机, 'ESC' 关闭任意弹窗
const handleKeyDown = (e: KeyboardEvent) => {
  const targetTag = (e.target as HTMLElement)?.tagName?.toLowerCase()
  if (targetTag === 'input' || targetTag === 'textarea') return

  if (e.key === 'p' || e.key === 'P') {
    if (viewMode.value === 'game') {
      showPhone.value = !showPhone.value
    }
  } else if (e.key === 'v' || e.key === 'V') {
    if (viewMode.value === 'game') {
      showVariables.value = !showVariables.value
    }
  } else if (e.key === 'Escape') {
    showPhone.value = false
    showVariables.value = false
    showMap.value = false
    showSaves.value = false
    showHistory.value = false
    showSettings.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style>
/* 全局基础重置与二次元字体设置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif;
  background-color: #020617;
  color: #f8fafc;
  overflow: hidden;
  user-select: none;
  -webkit-font-smoothing: antialiased;
}

#app, .app-root {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
}
</style>

<style scoped>
.galgame-stage {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* 舞台背景：根据地点与时段自动动态变色 */
.scene-background {
  position: absolute;
  inset: 0;
  z-index: 1;
  transition: all 0.8s ease;
  background-size: cover;
  background-position: center;
}

/* 地点氛围渐变 (免图内置沉浸背景) */
.library.afternoon .scene-background {
  background: radial-gradient(circle at 70% 30%, #3b82f6 0%, #1e3a8a 45%, #0f172a 100%);
}

.library.dusk .scene-background {
  background: radial-gradient(circle at 70% 30%, #f97316 0%, #9a3412 40%, #1c1917 100%);
}

.library.night .scene-background {
  background: radial-gradient(circle at 50% 20%, #312e81 0%, #1e1b4b 50%, #09090b 100%);
}

.classroom .scene-background {
  background: radial-gradient(circle at 60% 40%, #0284c7 0%, #0369a1 45%, #0c4a6e 100%);
}

.cafeteria .scene-background {
  background: radial-gradient(circle at 50% 40%, #fb923c 0%, #ea580c 45%, #431407 100%);
}

.sports_ground .scene-background {
  background: radial-gradient(circle at 50% 30%, #ec4899 0%, #be185d 40%, #18181b 100%);
}

/* 阳光与氛围光照层 */
.ambient-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 100%, rgba(255, 255, 255, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.sunbeam-overlay {
  position: absolute;
  top: -20%;
  right: -10%;
  width: 80%;
  height: 140%;
  background: linear-gradient(135deg, rgba(254, 240, 138, 0.12) 0%, transparent 60%);
  transform: rotate(-15deg);
  pointer-events: none;
}

.night-stars {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(2px 2px at 20px 30px, #ffffff, rgba(0,0,0,0)),
                    radial-gradient(2px 2px at 90px 40px, #ffffff, rgba(0,0,0,0)),
                    radial-gradient(1px 1px at 150px 80px, #ffffff, rgba(0,0,0,0));
  background-repeat: repeat;
  background-size: 200px 200px;
  opacity: 0.4;
  pointer-events: none;
}

/* 立绘主舞台 */
.character-stage {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  padding-bottom: 210px;
  pointer-events: none;
}

.empty-stage {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}

.empty-notice {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(12px);
  padding: 14px 28px;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 14px;
  color: #cbd5e1;
}

/* 底部交互区 */
.interaction-area {
  position: relative;
  z-index: 20;
  width: 100%;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
}

/* Toast 浮动提示 */
.toast-popup {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #ec4899, #f43f5e);
  color: #ffffff;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 9999px;
  box-shadow: 0 10px 25px rgba(244, 63, 94, 0.45);
  z-index: 100;
  font-size: 14px;
  letter-spacing: 0.5px;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px) scale(0.9);
}

/* 手机滑入动效 */
.phone-slide-enter-active,
.phone-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.phone-slide-enter-from,
.phone-slide-leave-to {
  opacity: 0;
  transform: translateY(40px) scale(0.95);
}

/* CG 弹窗 */
.cg-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  z-index: 90;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  padding: 20px;
}

.cg-frame {
  max-width: 900px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.cg-img {
  width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 18px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.cg-caption {
  color: #f1f5f9;
  font-size: 14px;
  letter-spacing: 1px;
}

.cg-pop-enter-active,
.cg-pop-leave-active {
  transition: all 0.4s ease;
}

.cg-pop-enter-from,
.cg-pop-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
