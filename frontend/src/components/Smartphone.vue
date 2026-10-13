<template>
  <div class="phone-backdrop" @click.self="$emit('close')">
    <div class="phone-chassis">
      <!-- 手机顶部硬件装饰与状态栏 -->
      <div class="phone-island">
        <div class="island-camera"></div>
        <div class="island-speaker"></div>
      </div>

      <div class="phone-status-bar">
        <span class="status-time">{{ currentTime }}</span>
        <div class="status-icons">
          <span>5G</span>
          <span>📶</span>
          <span>100% 🔋</span>
        </div>
      </div>

      <!-- 手机屏幕主视图 -->
      <div class="phone-screen">
        <!-- 页面 1：聊天消息列表与会话详情 -->
        <div v-if="currentTab === 'chats'" class="screen-view">
          <!-- 会话详情页 -->
          <div v-if="activeContact" class="chat-detail-view">
            <div class="chat-header">
              <button class="back-btn" @click="activeContact = null">❮ 返回</button>
              <span class="chat-title">{{ activeContact.name }}</span>
              <button
                class="photo-req-btn"
                v-if="!activeContact.is_group"
                @click="handleRequestPhoto"
                title="请求发送自拍照片"
              >
                📸 索要自拍
              </button>
            </div>

            <!-- 消息气泡流 -->
            <div class="messages-scroll" ref="msgListRef">
              <div
                v-for="msg in currentMessages"
                :key="msg.id"
                class="message-row"
                :class="{ 'is-me': msg.is_me }"
              >
                <div class="msg-avatar" v-if="!msg.is_me">
                  {{ activeContact.avatar || '👧' }}
                </div>
                <div class="msg-bubble-container">
                  <span class="sender-hint" v-if="activeContact.is_group && !msg.is_me">
                    {{ msg.sender_name }}
                  </span>
                  
                  <!-- 普通文字气泡 -->
                  <div class="msg-bubble" v-if="msg.type === 'text'">
                    {{ msg.text }}
                  </div>

                  <!-- 自拍/生图照片气泡 -->
                  <div class="msg-bubble photo-bubble" v-else-if="msg.type === 'image' || msg.type === 'photo_prompt'">
                    <div class="photo-text">{{ msg.text }}</div>
                    <div class="photo-card" v-if="msg.image_url">
                      <img :src="msg.image_url" alt="自拍照片" class="chat-photo-img" />
                    </div>
                    <div class="photo-card-placeholder" v-else>
                      <span>📷 [林雨晴的自拍已存入手机相册]</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部输入条 -->
            <div class="chat-input-row">
              <input
                type="text"
                v-model="inputMsg"
                class="chat-input"
                placeholder="发送私信……"
                @keydown.enter.prevent="handleSend"
              />
              <button class="chat-send-btn" @click="handleSend" :disabled="!inputMsg.trim()">
                发送
              </button>
            </div>
          </div>

          <!-- 消息列表页 -->
          <div v-else class="chats-list-view">
            <div class="app-header">
              <h2>消息 (Chats)</h2>
            </div>
            <div class="contacts-list">
              <div
                v-for="c in contacts"
                :key="c.id"
                class="contact-item"
                @click="openChat(c)"
              >
                <div class="contact-avatar">{{ c.avatar }}</div>
                <div class="contact-meta">
                  <div class="contact-top">
                    <span class="name">{{ c.name }}</span>
                    <span class="status-tag" v-if="c.affection !== null">
                      💖 好感 {{ c.affection }}
                    </span>
                  </div>
                  <div class="signature">{{ c.signature }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 页面 2：通讯录 -->
        <div v-else-if="currentTab === 'contacts'" class="screen-view">
          <div class="app-header">
            <h2>通讯录 (Contacts)</h2>
          </div>
          <div class="contacts-list">
            <div
              v-for="c in contacts"
              :key="c.id"
              class="contact-item"
              @click="openChat(c)"
            >
              <div class="contact-avatar">{{ c.avatar }}</div>
              <div class="contact-meta">
                <div class="contact-top">
                  <span class="name">{{ c.name }}</span>
                  <span class="online-dot" :class="{ away: c.online_status === '离开' }"></span>
                  <span class="online-label">{{ c.online_status }}</span>
                </div>
                <div class="signature">{{ c.signature }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 页面 3：朋友圈 (Moments) -->
        <div v-else-if="currentTab === 'moments'" class="screen-view moments-view">
          <div class="app-header">
            <h2>校园朋友圈 (Moments)</h2>
          </div>

          <div class="moments-feed">
            <div v-for="m in moments" :key="m.id" class="moment-card">
              <div class="moment-header">
                <div class="author-avatar">{{ m.avatar }}</div>
                <div class="author-info">
                  <span class="author-name">{{ m.author_name }}</span>
                  <span class="moment-time">{{ m.time_str }}</span>
                </div>
              </div>

              <div class="moment-content">{{ m.content }}</div>

              <div class="moment-actions">
                <button
                  class="moment-act-btn"
                  :class="{ liked: m.likes.includes('你') }"
                  @click="handleLike(m.id)"
                >
                  {{ m.likes.includes('你') ? '❤️ 已赞' : '🤍 点赞' }} ({{ m.likes.length }})
                </button>
              </div>

              <!-- 点赞列表 -->
              <div class="likes-box" v-if="m.likes.length > 0">
                <span>❤️ {{ m.likes.join('、') }} 觉得很赞</span>
              </div>

              <!-- 评论列表 -->
              <div class="comments-box" v-if="m.comments.length > 0">
                <div v-for="(cmt, idx) in m.comments" :key="idx" class="comment-line">
                  <span class="cmt-author">{{ cmt.author }}:</span>
                  <span class="cmt-text">{{ cmt.text }}</span>
                </div>
              </div>

              <!-- 发表评论 -->
              <div class="comment-input-row">
                <input
                  type="text"
                  v-model="commentInputs[m.id]"
                  class="comment-input"
                  placeholder="写下你的评论……"
                  @keydown.enter.prevent="handleComment(m.id)"
                />
                <button class="comment-btn" @click="handleComment(m.id)">发送</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 页面 4：手机相册 / CG 收藏 -->
        <div v-else-if="currentTab === 'gallery'" class="screen-view gallery-view">
          <div class="app-header">
            <h2>回忆相册 (Photos)</h2>
          </div>
          <div class="gallery-grid">
            <div class="photo-thumb-card" @click="previewPhoto('selfie_library')">
              <div class="thumb-inner">
                <span class="photo-icon">📷</span>
                <span class="photo-title">图书馆午后自拍</span>
              </div>
            </div>
            <div class="photo-thumb-card" @click="previewPhoto('sunset_sports')">
              <div class="thumb-inner">
                <span class="photo-icon">🌅</span>
                <span class="photo-title">操场夕阳抓拍</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部系统导航栏 (Dock Bar) -->
      <div class="phone-dock">
        <button
          class="dock-item"
          :class="{ active: currentTab === 'chats' }"
          @click="currentTab = 'chats'"
        >
          <span class="dock-icon">💬</span>
          <span class="dock-label">消息</span>
        </button>

        <button
          class="dock-item"
          :class="{ active: currentTab === 'contacts' }"
          @click="currentTab = 'contacts'"
        >
          <span class="dock-icon">👥</span>
          <span class="dock-label">通讯录</span>
        </button>

        <button
          class="dock-item"
          :class="{ active: currentTab === 'moments' }"
          @click="currentTab = 'moments'"
        >
          <span class="dock-icon">⭕</span>
          <span class="dock-label">朋友圈</span>
        </button>

        <button
          class="dock-item"
          :class="{ active: currentTab === 'gallery' }"
          @click="currentTab = 'gallery'"
        >
          <span class="dock-icon">🖼️</span>
          <span class="dock-label">相册</span>
        </button>
      </div>

      <!-- 底部小横条 Home Indicator -->
      <div class="home-indicator" @click="$emit('close')"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toast', msg: string): void
}>()

const currentTab = ref<'chats' | 'contacts' | 'moments' | 'gallery'>('chats')
const activeContact = ref<any | null>(null)
const contacts = ref<any[]>([])
const currentMessages = ref<any[]>([])
const moments = ref<any[]>([])
const inputMsg = ref('')
const commentInputs = ref<Record<string, string>>({})
const msgListRef = ref<HTMLDivElement | null>(null)

const currentTime = ref('15:45')

const loadContacts = async () => {
  try {
    const { data } = await axios.get('/api/phone/contacts')
    contacts.value = data
  } catch (err) {
    console.error('加载通讯录失败', err)
  }
}

const loadMoments = async () => {
  try {
    const { data } = await axios.get('/api/phone/moments')
    moments.value = data
  } catch (err) {
    console.error('加载朋友圈失败', err)
  }
}

const openChat = async (contact: any) => {
  activeContact.value = contact
  try {
    const { data } = await axios.get(`/api/phone/messages/${contact.id}`)
    currentMessages.value = data
    scrollToBottom()
  } catch (err) {
    console.error('获取消息失败', err)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (msgListRef.value) {
      msgListRef.value.scrollTop = msgListRef.value.scrollHeight
    }
  })
}

const handleSend = async () => {
  if (!inputMsg.value.trim() || !activeContact.value) return
  const text = inputMsg.value.trim()
  inputMsg.value = ''

  try {
    const { data } = await axios.post('/api/phone/messages/send', {
      target_id: activeContact.value.id,
      text,
      is_group: activeContact.value.is_group,
    })
    
    // 刷新消息列表
    const res = await axios.get(`/api/phone/messages/${activeContact.value.id}`)
    currentMessages.value = res.data
    scrollToBottom()
  } catch (err) {
    emit('toast', '发送消息失败')
  }
}

const handleRequestPhoto = async () => {
  if (!activeContact.value) return
  emit('toast', '正在向林雨晴请求发送自拍照片……')
  try {
    const { data } = await axios.post('/api/phone/request_photo', {
      character_id: activeContact.value.id,
      scene_description: 'smiling, university library, natural lighting',
    })
    emit('toast', data.message || '自拍已收到！')
    
    // 重新拉取消息
    const res = await axios.get(`/api/phone/messages/${activeContact.value.id}`)
    currentMessages.value = res.data
    scrollToBottom()
  } catch (err) {
    emit('toast', '请求照片失败')
  }
}

const handleLike = async (momentId: string) => {
  try {
    const { data } = await axios.post(`/api/phone/moments/${momentId}/like`)
    const m = moments.value.find((item) => item.id === momentId)
    if (m) {
      m.likes = data.likes
    }
    if (data.liked) {
      emit('toast', '点赞成功！林雨晴对你的好感度微增 💕')
    }
  } catch (err) {
    emit('toast', '点赞失败')
  }
}

const handleComment = async (momentId: string) => {
  const content = commentInputs.value[momentId]
  if (!content || !content.trim()) return

  try {
    const { data } = await axios.post(`/api/phone/moments/${momentId}/comment`, {
      content: content.trim(),
    })
    commentInputs.value[momentId] = ''
    const m = moments.value.find((item) => item.id === momentId)
    if (m) {
      m.comments = data.comments
    }
    emit('toast', '评论已发表！')
  } catch (err) {
    emit('toast', '评论失败')
  }
}

const previewPhoto = (name: string) => {
  emit('toast', `正在查看【${name}】高清画作`)
}

onMounted(() => {
  loadContacts()
  loadMoments()
})
</script>

<style scoped>
.phone-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 70;
  user-select: none;
}

/* 拟物化手机外壳 */
.phone-chassis {
  position: relative;
  width: 380px;
  height: 740px;
  background: #090d16;
  border-radius: 44px;
  border: 10px solid #1e293b;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8), 0 0 0 2px rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #f1f5f9;
}

/* 灵动岛 */
.phone-island {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 22px;
  background: #000000;
  border-radius: 9999px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 10px;
}

.island-camera {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0f172a;
}

.island-speaker {
  width: 30px;
  height: 4px;
  border-radius: 2px;
  background: #1e293b;
}

/* 顶部状态栏 */
.phone-status-bar {
  padding: 12px 24px 6px 24px;
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #cbd5e1;
  font-weight: 600;
  z-index: 5;
}

.status-icons {
  display: flex;
  gap: 6px;
  font-size: 10px;
}

/* 屏幕主内容区 */
.phone-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  overflow: hidden;
}

.screen-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-header {
  padding: 14px 18px 8px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.app-header h2 {
  font-size: 18px;
  margin: 0;
  color: #38bdf8;
}

/* 通讯录/会话项 */
.contacts-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.2s;
}

.contact-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.contact-avatar {
  font-size: 26px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.contact-meta {
  flex: 1;
  min-width: 0;
}

.contact-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.contact-top .name {
  font-weight: 700;
  font-size: 14px;
}

.status-tag {
  font-size: 10px;
  background: rgba(236, 72, 153, 0.2);
  color: #f472b6;
  padding: 1px 6px;
  border-radius: 9999px;
}

.signature {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 聊天详情页面 */
.chat-detail-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.back-btn {
  background: transparent;
  border: none;
  color: #38bdf8;
  font-size: 12px;
  cursor: pointer;
}

.chat-title {
  font-weight: 700;
  font-size: 14px;
}

.photo-req-btn {
  background: rgba(224, 123, 108, 0.15);
  border: 1.5px solid var(--accent, #e07b6c);
  border-radius: 9999px;
  color: var(--accent, #e07b6c);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.photo-req-btn:hover {
  background: var(--accent, #e07b6c);
  color: #ffffff;
}

.messages-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
  gap: 8px;
  max-width: 85%;
}

.message-row.is-me {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg-avatar {
  font-size: 18px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg-bubble-container {
  display: flex;
  flex-direction: column;
}

.sender-hint {
  font-size: 10px;
  color: #64748b;
  margin-bottom: 2px;
}

.msg-bubble {
  background: #ffffff;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  color: #3e342f;
  border: 1px solid #e0dcd6;
  box-shadow: 0 2px 0 rgba(74, 61, 54, 0.08);
}

.message-row.is-me .msg-bubble {
  background: var(--accent, #e07b6c);
  color: #ffffff;
  border-color: var(--accent-dark, #8e3b2e);
  box-shadow: 0 2px 0 rgba(142, 59, 46, 0.25);
}

.photo-bubble {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chat-photo-img {
  width: 160px;
  border-radius: 8px;
  object-fit: cover;
}

.photo-card-placeholder {
  font-size: 11px;
  color: #38bdf8;
  padding: 4px;
}

.chat-input-row {
  padding: 8px 12px;
  display: flex;
  gap: 8px;
  background: rgba(15, 23, 42, 0.9);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.chat-input {
  flex: 1;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 6px 10px;
  color: #ffffff;
  font-size: 12px;
  outline: none;
}

.chat-send-btn {
  background: var(--accent, #e07b6c);
  border: 1.5px solid #4a3d36;
  border-radius: 8px;
  color: #ffffff;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 0 rgba(74, 61, 54, 0.25);
  transition: all 0.15s;
}

.chat-send-btn:active {
  transform: translateY(2px);
  box-shadow: none;
}

/* 朋友圈 */
.moments-view {
  overflow-y: auto;
}

.moments-feed {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.moment-card {
  background: #ffffff;
  border: 1.5px solid #d0c3b8;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 3px 0 rgba(74, 61, 54, 0.12);
}

.moment-header {
  display: flex;
  gap: 8px;
  align-items: center;
}

.author-avatar {
  font-size: 22px;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-size: 13px;
  font-weight: 800;
  color: var(--dialogue-speech-ink, #8e3b2e);
}

.moment-time {
  font-size: 10px;
  color: #8c8074;
}

.moment-content {
  font-size: 13px;
  line-height: 1.5;
  color: #3e342f;
  font-weight: 500;
}

.moment-actions {
  display: flex;
  justify-content: flex-end;
}

.moment-act-btn {
  background: var(--dialogue-paper-solid, #fffdfa);
  border: 1.5px solid #7c7066;
  border-radius: 9999px;
  color: #554a43;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 12px;
  cursor: pointer;
  box-shadow: 0 2px 0 rgba(74, 61, 54, 0.15);
  transition: all 0.15s;
}

.moment-act-btn:hover {
  border-color: var(--accent, #e07b6c);
  color: var(--accent, #e07b6c);
}

.moment-act-btn.liked {
  background: rgba(224, 123, 108, 0.15);
  color: #e11d48;
  border-color: #f43f5e;
}

.likes-box {
  background: rgba(15, 23, 42, 0.6);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 10px;
  color: #94a3b8;
}

.comments-box {
  background: rgba(15, 23, 42, 0.6);
  padding: 6px 8px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
}

.cmt-author {
  font-weight: 600;
  color: #38bdf8;
  margin-right: 4px;
}

.cmt-text {
  color: #cbd5e1;
}

.comment-input-row {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.comment-input {
  flex: 1;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 4px 8px;
  color: #ffffff;
  font-size: 11px;
  outline: none;
}

.comment-btn {
  background: rgba(56, 189, 248, 0.2);
  border: 1px solid #38bdf8;
  color: #38bdf8;
  border-radius: 6px;
  font-size: 11px;
  padding: 0 8px;
  cursor: pointer;
}

/* 相册 */
.gallery-grid {
  padding: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.photo-thumb-card {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.photo-thumb-card:hover {
  transform: scale(1.02);
  border-color: #38bdf8;
}

.thumb-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.photo-icon {
  font-size: 26px;
}

.photo-title {
  font-size: 11px;
  color: #cbd5e1;
}

/* 底部 Dock */
.phone-dock {
  height: 54px;
  background: rgba(15, 23, 42, 0.95);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.dock-item {
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  color: #64748b;
  transition: color 0.2s;
}

.dock-item.active {
  color: #38bdf8;
}

.dock-icon {
  font-size: 18px;
}

.dock-label {
  font-size: 10px;
  font-weight: 500;
}

.home-indicator {
  width: 120px;
  height: 4px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 9999px;
  margin: 6px auto 8px auto;
  cursor: pointer;
}
</style>
