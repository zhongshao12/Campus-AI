<template>
  <div class="title-screen-container">
    <!-- 专属封面背景图 (恋爱物语) -->
    <div class="title-bg">
      <div class="vignette-overlay"></div>
      <div class="sakura-layer"></div>
    </div>

    <!-- 左侧主视觉排版与核心操作区 -->
    <div class="title-content-layout">
      <!-- 品牌与标题标识 -->
      <div class="title-header">
        <div class="game-badge">AI POWERED OPEN CAMPUS GALGAME</div>
        <h1 class="english-title">Campus AI</h1>
        <div class="sub-description">
          <span>AI 校园恋爱物语 · 青春与记忆的序章</span>
        </div>
      </div>

      <!-- 核心菜单操作按钮组 (精致磨砂玻璃与二次元光效) -->
      <div class="menu-actions">
        <button class="menu-btn primary-btn" @click="$emit('start-game')">
          <span class="btn-glow"></span>
          <span class="btn-icon">🌸</span>
          <span class="btn-text">开始新篇章 (START)</span>
        </button>

        <button class="menu-btn secondary-btn" @click="$emit('continue-game')">
          <span class="btn-icon">💾</span>
          <span class="btn-text">继续回忆 (CONTINUE)</span>
        </button>

        <button class="menu-btn secondary-btn" @click="$emit('open-settings')">
          <span class="btn-icon">⚙️</span>
          <span class="btn-text">系统设置 (CONFIG)</span>
        </button>
      </div>

      <!-- 特性说明 -->
      <div class="title-feature-tags">
        <span class="tag">自由对话</span>
        <span class="tag">动态生图</span>
        <span class="tag">智能手机</span>
        <span class="tag">变量系统</span>
        <span class="tag">真实好感</span>
      </div>
    </div>

    <!-- 底部状态与版本信息 -->
    <div class="title-footer">
      <span>Windows 单机优先 · 虚构大学校园沙盒 · 角色自主生活模拟</span>
      <span class="version-tag">v0.2.0 Variable Engine</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  (e: 'start-game'): void
  (e: 'continue-game'): void
  (e: 'open-settings'): void
}>()
</script>

<style scoped>
.title-screen-container {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 50px 60px 24px 60px;
  overflow: hidden;
  z-index: 100;
  user-select: none;
}

/* 封面背景层 (恋爱物语.png) */
.title-bg {
  position: absolute;
  inset: 0;
  background-image: url('/cover.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: -1;
  transform: scale(1.02);
  transition: transform 10s ease-out;
  animation: slowZoom 20s infinite alternate ease-in-out;
}

@keyframes slowZoom {
  0% { transform: scale(1.0); }
  100% { transform: scale(1.04); }
}

/* 左侧柔和暗角蒙版：保障文字清晰度的同时，让右侧女主角和校园完全明亮通透 */
.vignette-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(15, 23, 42, 0.88) 0%,
    rgba(15, 23, 42, 0.65) 35%,
    rgba(15, 23, 42, 0.15) 65%,
    rgba(15, 23, 42, 0.05) 100%
  );
  pointer-events: none;
}

/* 樱花飞舞点缀层 */
.sakura-layer {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 30%, rgba(244, 63, 94, 0.12) 0%, transparent 60%);
  pointer-events: none;
}

/* 左侧主体内容区 */
.title-content-layout {
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 460px;
  height: 80%;
  animation: fadeInLeft 1.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.title-header {
  margin-bottom: 36px;
}

.game-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  padding: 4px 14px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  margin-bottom: 12px;
}

.english-title {
  font-size: 56px;
  font-weight: 900;
  letter-spacing: 3px;
  line-height: 1.1;
  background: linear-gradient(135deg, #ffffff 40%, #e0f2fe 70%, #fbcfe8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.5));
}

.sub-description {
  margin-top: 10px;
  font-size: 15px;
  letter-spacing: 1.5px;
  color: #f1f5f9;
  font-weight: 500;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}

/* 菜单按钮列表 */
.menu-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.menu-btn {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 28px;
  border-radius: 18px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

.primary-btn {
  background: linear-gradient(135deg, rgba(2, 132, 199, 0.88), rgba(236, 72, 153, 0.88));
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.4);
}

.primary-btn:hover {
  transform: translateX(8px) scale(1.02);
  background: linear-gradient(135deg, #0ea5e9, #f43f5e);
  box-shadow: 0 14px 35px rgba(236, 72, 153, 0.5);
  border-color: #ffffff;
}

.secondary-btn {
  background: rgba(15, 23, 42, 0.75);
  color: #f8fafc;
}

.secondary-btn:hover {
  transform: translateX(6px);
  background: rgba(30, 41, 59, 0.9);
  border-color: rgba(56, 189, 248, 0.6);
  box-shadow: 0 10px 25px rgba(56, 189, 248, 0.3);
}

.btn-icon {
  font-size: 20px;
}

.btn-text {
  letter-spacing: 1.5px;
}

/* 标签组 */
.title-feature-tags {
  display: flex;
  gap: 8px;
  margin-top: 24px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
}

/* 底部状态 */
.title-footer {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: rgba(241, 245, 249, 0.75);
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  padding-top: 12px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.version-tag {
  font-family: monospace;
  color: #38bdf8;
  background: rgba(15, 23, 42, 0.7);
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-40px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
