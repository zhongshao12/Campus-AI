export interface WorldState {
  day_number: number
  weekday: string
  time_slot: string
  weather: string
  player_location: string
  location_name: string
  location_description: string
  present_characters: string[]
}

export interface CharacterStatus {
  character_id: string
  name: string
  title: string
  affection: number
  trust: number
  stage: string
  current_mood: string
  current_location: string
  schedule_activity?: string
}

export interface DialogueTurn {
  speaker: string
  dialogue: string
  emotion: string
  expression: string
  action?: string
  inner_thought?: string
  affection: number
  affection_delta: number
  trust: number
  stage: string
  applied_effects: Array<{
    type: string
    delta?: number
    current?: number
    reason?: string
  }>
  cg_image_url?: string | null
  event_triggered?: string | null
}

export interface SaveSlotItem {
  slot_index: number
  title: string
  saved_at: string
  preview: {
    day: number
    time_slot: string
    location: string
    lin_affection: number
  }
}
