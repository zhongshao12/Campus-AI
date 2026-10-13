<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="map-card glass-modal">
      <div class="modal-header">
        <h2 class="title">🗺️ 校园地点漫步</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <p class="subtitle">选择你想前往的校园区域，不同的时段可能偶遇不同的角色与事件：</p>

      <div class="locations-grid">
        <div
          v-for="loc in locations"
          :key="loc.id"
          class="location-item"
          :class="{ active: currentLocation === loc.id }"
          @click="selectLocation(loc.id)"
        >
          <div class="loc-icon-large">{{ loc.icon }}</div>
          <div class="loc-info">
            <div class="loc-header">
              <span class="loc-name">{{ loc.name }}</span>
              <span class="current-badge" v-if="currentLocation === loc.id">当前所在</span>
            </div>
            <p class="loc-desc">{{ loc.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentLocation?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', locationId: string): void
}>()

const locations = [
  {
    id: 'library',
    name: '大学图书馆',
    icon: '📚',
    desc: '阳光透过的整齐书架与长桌，空气中飘散着纸墨清香，是自习与偶遇的最佳场所。',
  },
  {
    id: 'classroom',
    name: '主教学楼·302教室',
    icon: '🏫',
    desc: '洒满阳光的明亮阶梯教室，同桌之间的悄悄话与课间嬉闹。',
  },
  {
    id: 'cafeteria',
    name: '第二食堂',
    icon: '🍱',
    desc: '饭点时热闹非凡的美食街区，靠窗的双人座很适合一起喝饮料聊天。',
  },
  {
    id: 'sports_ground',
    name: '田径运动场',
    icon: '🏃',
    desc: '红白相间的开阔跑道，黄昏时晚霞如燃烧般艳丽，看台微风让人心旷神怡。',
  },
  {
    id: 'dormitory',
    name: '学生宿舍区·林荫道',
    icon: '🌙',
    desc: '静谧温馨的生活区，常青樟树下有自动贩卖机与微风，夜间灯火温暖。',
  },
]

const selectLocation = (id: string) => {
  emit('select', id)
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 50;
  padding: 20px;
}

.glass-modal {
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  width: 100%;
  max-width: 640px;
  padding: 24px 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
  color: #f8fafc;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.title {
  font-size: 20px;
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
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 20px;
}

.locations-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.location-item {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  display: flex;
  gap: 14px;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.location-item:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: #38bdf8;
  transform: translateY(-2px);
}

.location-item.active {
  background: rgba(14, 165, 233, 0.25);
  border-color: #0ea5e9;
  box-shadow: 0 0 16px rgba(14, 165, 233, 0.3);
}

.loc-icon-large {
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loc-info {
  flex: 1;
}

.loc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.loc-name {
  font-weight: 700;
  font-size: 15px;
  color: #f1f5f9;
}

.current-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 9999px;
  background: #0284c7;
  color: #ffffff;
}

.loc-desc {
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
  margin: 0;
}
</style>
