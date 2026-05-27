const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const timelineApi = {
  async getPersons() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timeline/persons`)
      if (!response.ok) throw new Error('获取人物数据失败')
      return await response.json()
    } catch (error) {
      console.error('获取人物数据失败:', error)
      return []
    }
  },

  async getPersonById(personId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timeline/persons/${personId}`)
      if (!response.ok) throw new Error('获取人物详情失败')
      return await response.json()
    } catch (error) {
      console.error('获取人物详情失败:', error)
      return null
    }
  },

  async getEvents() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timeline/events`)
      if (!response.ok) throw new Error('获取事件数据失败')
      return await response.json()
    } catch (error) {
      console.error('获取事件数据失败:', error)
      return []
    }
  },

  async getEventsByYear(year) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timeline/events/year/${year}`)
      if (!response.ok) throw new Error('获取事件数据失败')
      return await response.json()
    } catch (error) {
      console.error(`获取${year}年事件失败:`, error)
      return []
    }
  },

  async getStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timeline/stats`)
      if (!response.ok) throw new Error('获取统计信息失败')
      return await response.json()
    } catch (error) {
      console.error('获取统计信息失败:', error)
      return {
        person_count: 0,
        event_count: 0,
        year_range: { min: 1800, max: 2025 }
      }
    }
  }
}
