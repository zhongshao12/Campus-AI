<template>
  <div class="title-screen-container">
    <!-- 唯美背景与粒子光斑 -->
    <div class="title-bg">
      <div class="ambient-overlay"></div>
      <div class="cherry-petals"></div>
    </div>

    <!-- 标题与副标题 -->
    <div class="title-header">
      <div class="game-logo-badge">AI POWERED GALGAME</div>
      <h1 class="main-title">Campus AI</h1>
      <div class="sub-title">AI 校园恋爱物语 · 青春与记忆的序章</div>
    </div>

    <!-- 菜单按钮组 -->
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

    <!-- 底部版本与特性标识 -->
    <div class="title-footer">
      <span>Windows 单机优先 · 自由对话 · 动态生图 · 真实关系演化</span>
      <span class="version-tag">v0.1.0 Alpha</span>
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
  align-items: center;
  padding: 60px 40px 30px 40px;
  overflow: hidden;
  z-index: 100;
  user-select: none;
}

.title-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 30%, #1e3a8a 0%, #0f172a 60%, #020617 100%);
  z-index: -1;
}

.ambient-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 60%, rgba(244, 63, 94, 0.15) 0%, transparent 70%);
}

.title-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 40px;
  animation: fadeInDown 1.2s ease-out;
}

.game-logo-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  padding: 4px 16px;
  border-radius: 9999px;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
  margin-bottom: 12px;
}

.main-title {
  font-size: 64px;
  font-weight: 900;
  letter-spacing: 4px;
  background: linear-gradient(135deg, #ffffff 30%, #93c5fd 70%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  text-shadow: 0 10px 30px rgba(56, 189, 248, 0.35);
}

.sub-title {
  margin-top: 10px;
  font-size: 16px;
  letter-spacing: 2px;
  color: #cbd5e1;
}

/* 按钮组 */
.menu-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 340px;
  margin-bottom: 40px;
  animation: fadeInUp 1.2s ease-out;
}

.menu-btn {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 28px;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(12px);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.primary-btn {
  background: linear-gradient(135deg, rgba(2, 132, 199, 0.8), rgba(37, 99, 235, 0.85));
  color: #ffffff;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
}

.primary-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 12px 30px rgba(56, 189, 248, 0.6);
  border-color: #38bdf8;
}

.secondary-btn {
  background: rgba(15, 23, 42, 0.7);
  color: #e2e8f0;
}

.secondary-btn:hover {
  transform: translateY(-2px);
  background: rgba(30, 41, 59, 0.85);
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-icon {
  font-size: 18px;
}

.btn-text {
  letter-spacing: 1px;
}

.title-footer {
  width: 100%;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 14px;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
