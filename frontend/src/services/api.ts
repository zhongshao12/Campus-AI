import axios from 'axios'
import type { WorldState, CharacterStatus, DialogueTurn, SaveSlotItem } from '../types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 35000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const gameApi = {
  // 游戏会话生命周期
  async startNewGame(): Promise<any> {
    const { data } = await apiClient.post('/game/new')
    return data
  },

  async getCurrentGame(): Promise<any> {
    const { data } = await apiClient.get('/game/current')
    return data
  },

  // 世界与场景
  async getWorldState(): Promise<WorldState> {
    const { data } = await apiClient.get<WorldState>('/world/state')
    return data
  },

  async moveToLocation(locationId: string): Promise<WorldState> {
    const { data } = await apiClient.post<WorldState>(`/world/move/${locationId}`)
    return data
  },

  async advanceTime(targetLocation?: string): Promise<WorldState> {
    const { data } = await apiClient.post<WorldState>('/world/advance_time', {
      target_location: targetLocation,
    })
    return data
  },

  // 角色信息
  async getCharacterStatus(characterId: string): Promise<CharacterStatus> {
    const { data } = await apiClient.get<CharacterStatus>(`/characters/${characterId}/status`)
    return data
  },

  async getCharacterConfig(characterId: string): Promise<any> {
    const { data } = await apiClient.get(`/characters/${characterId}/config`)
    return data
  },

  // 对话
  async sendDialogue(message: string, characterId: string = 'lin_yuqing', actionType: string = 'speak'): Promise<DialogueTurn> {
    const { data } = await apiClient.post<DialogueTurn>('/dialogue/chat', {
      message,
      character_id: characterId,
      action_type: actionType,
    })
    return data
  },

  // 存档管理
  async listSaveSlots(): Promise<SaveSlotItem[]> {
    const { data } = await apiClient.get<SaveSlotItem[]>('/saves/slots')
    return data
  },

  async saveGame(slotIndex: number, title?: string): Promise<any> {
    const { data } = await apiClient.post(`/saves/save/${slotIndex}`, null, {
      params: { title: title || '手动存档' },
    })
    return data
  },

  async loadGame(slotIndex: number): Promise<any> {
    const { data } = await apiClient.post(`/saves/load/${slotIndex}`)
    return data
  },
}
