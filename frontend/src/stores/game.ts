import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gameApi } from '../services/api'
import type { WorldState, CharacterStatus, DialogueTurn } from '../types'

export const useGameStore = defineStore('game', () => {
  // 世界与角色状态
  const world = ref<WorldState | null>(null)
  const character = ref<CharacterStatus | null>(null)
  
  // 对话演出状态
  const currentSpeaker = ref('林雨晴')
  const currentDialogue = ref('（窗外的微风轻轻拂过树梢，阳光斜斜地落在摊开的笔记本上……）')
  const currentEmotion = ref('neutral')
  const currentExpression = ref('neutral')
  const currentAction = ref<string | null>('静静看着窗外')
  const currentInnerThought = ref<string | null>(null)
  
  // 交互控制
  const isGenerating = ref(false)
  const toastMessage = ref<string | null>(null)
  const activeCgUrl = ref<string | null>(null)
  
  // 历史记录
  const historyLogs = ref<Array<{ speaker: string; text: string; emotion?: string }>>([])

  // 快捷飘字提示
  const showToast = (msg: string, duration: number = 2500) => {
    toastMessage.value = msg
    setTimeout(() => {
      if (toastMessage.value === msg) {
        toastMessage.value = null
      }
    }, duration)
  }

  // 开启全新游戏 (彻底重置后端与前端演出状态)
  const startNewGame = async () => {
    try {
      isGenerating.value = true
      await gameApi.startNewGame()
      await initGame()

      // 重置全部前端演出状态
      historyLogs.value = []
      currentSpeaker.value = '林雨晴'
      currentDialogue.value = '嗨！你也来图书馆自习呀？今天下午阳光真好呢~'
      currentEmotion.value = 'happy'
      currentExpression.value = 'happy'
      currentAction.value = '微笑着抬起头看向你'
      currentInnerThought.value = '新学期的第一天，好巧又遇见他了。'
      showToast('🌸 全新大学恋爱篇章已开启！')
    } catch (err) {
      console.error('开启新游戏失败:', err)
      showToast('重置新游戏失败')
    } finally {
      isGenerating.value = false
    }
  }

  // 读档后重置演出状态
  const reloadFromSave = async () => {
    await initGame()
    historyLogs.value = []
    currentSpeaker.value = '旁白'
    currentDialogue.value = `记忆浮现……你回到了【${world.value?.location_name || '大学校园'}】。`
    currentEmotion.value = 'neutral'
    currentExpression.value = 'neutral'
    currentAction.value = null
    currentInnerThought.value = null
    showToast('💾 进度已恢复！')
  }

  // 初始化游戏状态
  const initGame = async () => {
    try {
      const [w, c] = await Promise.all([
        gameApi.getWorldState(),
        gameApi.getCharacterStatus('lin_yuqing'),
      ])
      world.value = w
      character.value = c
    } catch (err) {
      console.error('初始化游戏状态失败:', err)
      showToast('连接游戏后端失败，请确认后端已启动')
    }
  }

  // 发送对话
  const sendMessage = async (userText: string) => {
    if (!userText.trim() || isGenerating.value) return
    
    // 记录玩家自身历史
    historyLogs.value.push({ speaker: '你', text: userText })
    isGenerating.value = true

    try {
      const res: DialogueTurn = await gameApi.sendDialogue(userText, 'lin_yuqing')
      
      // 更新演出表现
      currentSpeaker.value = res.speaker
      currentDialogue.value = res.dialogue
      currentEmotion.value = res.emotion
      currentExpression.value = res.expression
      currentAction.value = res.action || null
      currentInnerThought.value = res.inner_thought || null

      // 更新角色好感与阶段
      if (character.value) {
        character.value.affection = res.affection
        character.value.trust = res.trust
        character.value.stage = res.stage
        character.value.current_mood = res.emotion
      }

      // 处理飘字提示 (好感变动)
      if (res.affection_delta > 0) {
        showToast(`💕 林雨晴好感度 +${res.affection_delta}！`)
      } else if (res.affection_delta < 0) {
        showToast(`💔 林雨晴好感度 ${res.affection_delta}……`)
      }

      // 如果有生成专属CG
      if (res.cg_image_url) {
        activeCgUrl.value = res.cg_image_url
        showToast('🎉 解锁新剧情专属CG！')
      }

      // 记录角色历史
      historyLogs.value.push({
        speaker: res.speaker,
        text: res.dialogue,
        emotion: res.emotion,
      })

    } catch (err: any) {
      console.error('发送对话出错:', err)
      showToast('对话交互异常，已自动启用备用演播')
    } finally {
      isGenerating.value = false
    }
  }

  // 地点移动
  const moveTo = async (locationId: string) => {
    try {
      isGenerating.value = true
      const newWorld = await gameApi.moveToLocation(locationId)
      world.value = newWorld
      
      // 刷新角色状态（查看角色是否也在此地点）
      character.value = await gameApi.getCharacterStatus('lin_yuqing')
      
      currentSpeaker.value = '旁白'
      currentDialogue.value = `你来到了【${newWorld.location_name}】。${newWorld.location_description}`
      currentAction.value = null
      currentInnerThought.value = null
      currentExpression.value = 'neutral'
    } catch (err) {
      showToast('移动地点失败')
    } finally {
      isGenerating.value = false
    }
  }

  // 推进时间
  const advanceTimeSlot = async () => {
    try {
      isGenerating.value = true
      const newWorld = await gameApi.advanceTime()
      world.value = newWorld
      character.value = await gameApi.getCharacterStatus('lin_yuqing')
      
      currentSpeaker.value = '旁白'
      currentDialogue.value = `时间流逝到了【${newWorld.time_slot}】。校园里的光线悄悄发生着改变……`
      currentAction.value = null
      currentInnerThought.value = null
      currentExpression.value = 'neutral'
      showToast(`🕒 时间推进到了: ${newWorld.time_slot}`)
    } catch (err) {
      showToast('时间推进失败')
    } finally {
      isGenerating.value = false
    }
  }

  return {
    world,
    character,
    currentSpeaker,
    currentDialogue,
    currentEmotion,
    currentExpression,
    currentAction,
    currentInnerThought,
    isGenerating,
    toastMessage,
    activeCgUrl,
    historyLogs,
    showToast,
    startNewGame,
    reloadFromSave,
    initGame,
    sendMessage,
    moveTo,
    advanceTimeSlot,
  }
})
