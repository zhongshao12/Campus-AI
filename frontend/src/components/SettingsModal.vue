<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="settings-card glass-modal">
      <div class="modal-header">
        <h2 class="title">⚙️ 游戏运行设置</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="settings-body">
        <!-- 云端 LLM 配置 -->
        <div class="section-group">
          <div class="section-title">🤖 云端大模型配置 (LLM API)</div>
          
          <div class="form-item">
            <label>API Key：</label>
            <input
              type="password"
              v-model="form.llm_api_key"
              placeholder="sk-xxxxxxxx（留空或默认使用内置智能交互）"
              class="form-input"
            />
          </div>

          <div class="form-item">
            <label>Base URL：</label>
            <input
              type="text"
              v-model="form.llm_base_url"
              placeholder="https://api.deepseek.com/v1"
              class="form-input"
            />
          </div>

          <div class="form-item">
            <label>模型名称 (Model)：</label>
            <input
              type="text"
              v-model="form.llm_model"
              placeholder="deepseek-chat"
              class="form-input"
            />
          </div>
        </div>

        <!-- 本地 ComfyUI 配置 -->
        <div class="section-group">
          <div class="section-title">🎨 本地 ComfyUI 生图配置 (RTX 4070 适配)</div>
          
          <div class="form-item">
            <label>ComfyUI 地址：</label>
            <div class="input-with-status">
              <input
                type="text"
                v-model="form.comfyui_base_url"
                placeholder="http://127.0.0.1:8188"
                class="form-input"
              />
              <span class="status-pill" :class="{ online: comfyOnline }">
                {{ comfyOnline ? '● 服务在线' : '○ 未连接' }}
              </span>
            </div>
            <p class="field-hint">
              本地 RTX 4070 显卡启动 ComfyUI 监听 8188 端口后，剧情关键节点与自拍将实时调用生成高质量 CG。
            </p>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="action-btn cancel-btn" @click="$emit('close')">取消</button>
        <button class="action-btn save-btn" @click="handleSave">保存配置</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toast', msg: string): void
}>()

const form = ref({
  llm_api_key: '',
  llm_base_url: 'https://api.deepseek.com/v1',
  llm_model: 'deepseek-chat',
  comfyui_base_url: 'http://127.0.0.1:8188',
})

const comfyOnline = ref(false)

const loadSettings = async () => {
  try {
    const { data } = await axios.get('/api/settings')
    form.value.llm_base_url = data.llm_base_url || 'https://api.deepseek.com/v1'
    form.value.llm_model = data.llm_model || 'deepseek-chat'
    form.value.comfyui_base_url = data.comfyui_base_url || 'http://127.0.0.1:8188'
    comfyOnline.value = data.comfyui_online
  } catch (err) {
    console.warn('获取设置失败', err)
  }
}

const handleSave = async () => {
  try {
    await axios.post('/api/settings', form.value)
    emit('toast', '设置已成功保存并立即生效！')
    emit('close')
  } catch (err) {
    emit('toast', '保存设置失败')
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 80;
  padding: 20px;
}

.glass-modal {
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  width: 100%;
  max-width: 580px;
  padding: 24px 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7);
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

.title {
  font-size: 19px;
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

.settings-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-group {
  background: rgba(30, 41, 59, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #cbd5e1;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 12px;
  color: #94a3b8;
}

.form-input {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 8px 12px;
  color: #ffffff;
  font-size: 13px;
  outline: none;
}

.form-input:focus {
  border-color: #38bdf8;
}

.input-with-status {
  display: flex;
  gap: 10px;
  align-items: center;
}

.input-with-status .form-input {
  flex: 1;
}

.status-pill {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 9999px;
  background: rgba(148, 163, 184, 0.2);
  color: #94a3b8;
  white-space: nowrap;
}

.status-pill.online {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.field-hint {
  font-size: 11px;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.action-btn {
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.16);
}

.save-btn {
  background: linear-gradient(135deg, #0284c7, #2563eb);
  color: #ffffff;
}

.save-btn:hover {
  background: linear-gradient(135deg, #38bdf8, #3b82f6);
}
</style>
