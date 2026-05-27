<template>
  <div class="historical-timeline">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane name="browse">
        <template #label>
          <span>📊 浏览时间轴</span>
        </template>
        
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>📊 年龄分布图 - {{ currentYear }}年</span>
              <el-tag type="info">当前在世: {{ alivePersonsInCurrentYear.length }} 人</el-tag>
            </div>
          </template>
          <div id="age-chart" style="width: 100%; height: 350px;"></div>
        </el-card>

        <el-card class="control-card">
          <template #header>
            <span>🎛️ 年份控制器</span>
          </template>
          <div class="year-controls">
            <div class="current-year-display">{{ currentYear }}年</div>
            <el-slider
              v-model="currentYear"
              :min="minYear"
              :max="maxYear"
              :format-tooltip="formatYear"
              show-input
              @input="handleYearChange"
            />
            <div class="control-buttons">
              <el-button 
                :type="isAutoPlaying ? 'danger' : 'primary'" 
                @click="toggleAutoPlay"
              >
                {{ isAutoPlaying ? '⏸️ 暂停' : '▶️ 播放' }}
              </el-button>
              <el-button @click="resetYear">🔄 重置</el-button>
            </div>
          </div>
        </el-card>

        <el-card class="persons-card">
          <template #header>
            <div class="card-header">
              <span>👥 {{ currentYear }}年历史人物</span>
              <el-tag type="success">{{ alivePersonsInCurrentYear.length }} 人</el-tag>
            </div>
          </template>
          <div class="persons-list">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="person in alivePersonsInCurrentYear" :key="person.id">
                <el-card class="person-card" shadow="hover">
                  <template #header>
                    <div class="person-header">
                      <span class="person-name">{{ person.name }}</span>
                      <el-tag size="small" type="info">{{ calculateAge(person, currentYear) }}岁</el-tag>
                    </div>
                  </template>
                  <div class="person-content">
                    <div class="person-dates">
                      <div v-if="person.birth_date">
                        <span>📆</span> 
                        出生: {{ person.birth_date }}
                      </div>
                      <div v-if="person.death_date">
                        <span>⚰️</span> 
                        逝世: {{ person.death_date }}
                      </div>
                      <div v-else class="alive-status">
                        <span>👤</span> 
                        在世
                      </div>
                    </div>
                    <div class="person-bio" v-if="person.bio">
                      {{ person.bio }}
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <el-empty v-if="alivePersonsInCurrentYear.length === 0" description="该年份暂无在世人物" />
          </div>
        </el-card>

        <el-card class="events-card">
          <template #header>
            <div class="card-header">
              <span>📅 {{ currentYear }}年历史事件</span>
              <el-tag type="warning">{{ currentYearEvents.length }} 件</el-tag>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item 
              v-for="event in currentYearEvents" 
              :key="event.id" 
              :timestamp="event.date || `${currentYear}-01-01`"
              placement="top"
              type="primary"
            >
              <el-card>
                <h4>{{ event.event_name }}</h4>
                <p v-if="event.description">{{ event.description }}</p>
                <el-tag v-if="event.event_category" size="small" type="info">
                  {{ event.event_category }}
                </el-tag>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="currentYearEvents.length === 0" description="该年份暂无历史事件" />
        </el-card>
      </el-tab-pane>

      <el-tab-pane name="lifespan">
        <template #label>
          <span><el-icon><Histogram /></el-icon> 寿命分布</span>
        </template>
        
        <el-card class="chart-card">
          <template #header>
            <span>📈 历史人物寿命分布气泡图</span>
          </template>
          <div id="lifespan-chart" style="width: 100%; height: 600px;"></div>
        </el-card>

        <el-card class="stats-card">
          <template #header>
            <span>📊 统计信息</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="历史人物总数" :value="historicalPersons.length">
                <template #prefix>
                  <span>👤</span>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic title="历史事件总数" :value="allHistoricalEvents.length">
                <template #prefix>
                  <span>📅</span>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic title="平均寿命" :value="averageLifespan" suffix="岁">
                <template #prefix>
                  <el-icon><Timer /></el-icon>
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-backtop :right="100" :bottom="100" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Histogram, Calendar, Coin, User, Timer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { timelineApi } from '../api/timelineApi'

const activeTab = ref('browse')
const currentYear = ref(1900)
const minYear = ref(1800)
const maxYear = ref(2025)
const historicalPersons = ref([])
const allHistoricalEvents = ref([])
const isAutoPlaying = ref(false)
let autoPlayTimer = null
let ageChart = null
let lifespanChart = null

const alivePersonsInCurrentYear = computed(() => {
  return historicalPersons.value.filter(person => {
    if (!person.birth_date) return false
    const birthYear = parseInt(person.birth_date.split('-')[0])
    if (currentYear.value < birthYear) return false
    if (person.death_date) {
      const deathYear = parseInt(person.death_date.split('-')[0])
      return currentYear.value <= deathYear
    }
    return true
  })
})

const currentYearEvents = computed(() => {
  return allHistoricalEvents.value.filter(event => {
    if (!event.start_date) return false
    const eventYear = parseInt(event.start_date.split('-')[0])
    return eventYear === currentYear.value
  })
})

const averageLifespan = computed(() => {
  const personsWithLifespan = historicalPersons.value.filter(p => p.life_span)
  if (personsWithLifespan.length === 0) return 0
  const total = personsWithLifespan.reduce((sum, p) => sum + p.life_span, 0)
  return Math.round(total / personsWithLifespan.length)
})

const calculateAge = (person, year) => {
  if (!person.birth_date) return '?'
  const birthYear = parseInt(person.birth_date.split('-')[0])
  if (person.death_date) {
    const deathYear = parseInt(person.death_date.split('-')[0])
    if (year > deathYear) return `已故 (${person.life_span || '?'}岁)`
    return deathYear - birthYear
  }
  return year - birthYear
}

const formatYear = (val) => {
  return `${val}年`
}

const handleYearChange = () => {
  updateAgeChart()
}

const toggleAutoPlay = () => {
  isAutoPlaying.value = !isAutoPlaying.value
  if (isAutoPlaying.value) {
    startAutoPlay()
  } else {
    stopAutoPlay()
  }
}

const startAutoPlay = () => {
  stopAutoPlay()
  autoPlayTimer = setInterval(() => {
    if (currentYear.value >= maxYear.value) {
      currentYear.value = minYear.value
    } else {
      currentYear.value += 1
    }
    updateAgeChart()
  }, 500)
}

const stopAutoPlay = () => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
}

const resetYear = () => {
  currentYear.value = 1900
  updateAgeChart()
}

const initAgeChart = () => {
  const chartDom = document.getElementById('age-chart')
  if (!chartDom) return
  
  if (ageChart) {
    ageChart.dispose()
  }
  
  ageChart = echarts.init(chartDom)
  updateAgeChart()
}

const updateAgeChart = () => {
  if (!ageChart) return
  
  const ageGroups = {
    '0-20岁': 0,
    '21-40岁': 0,
    '41-60岁': 0,
    '61-80岁': 0,
    '80岁以上': 0
  }
  
  alivePersonsInCurrentYear.value.forEach(person => {
    const age = calculateAge(person, currentYear.value)
    if (typeof age === 'number') {
      if (age <= 20) ageGroups['0-20岁']++
      else if (age <= 40) ageGroups['21-40岁']++
      else if (age <= 60) ageGroups['41-60岁']++
      else if (age <= 80) ageGroups['61-80岁']++
      else ageGroups['80岁以上']++
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: Object.keys(ageGroups),
      axisLabel: { interval: 0, rotate: 0 }
    },
    yAxis: {
      type: 'value',
      name: '人数'
    },
    series: [{
      name: '在世人数',
      type: 'bar',
      data: Object.values(ageGroups),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409EFF' },
          { offset: 1, color: '#66b1ff' }
        ])
      },
      label: {
        show: true,
        position: 'top'
      }
    }]
  }
  
  ageChart.setOption(option)
}

const initLifespanChart = () => {
  nextTick(() => {
    const chartDom = document.getElementById('lifespan-chart')
    if (!chartDom) return
    
    if (lifespanChart) {
      lifespanChart.dispose()
    }
    
    lifespanChart = echarts.init(chartDom)
    
    const data = historicalPersons.value
      .filter(p => p.birth_date && p.life_span)
      .map(p => {
        const birthYear = parseInt(p.birth_date.split('-')[0])
        return {
          name: p.name,
          value: [birthYear, p.life_span, p.life_span * 10],
          bio: p.bio
        }
      })
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const data = params.data
          return `<strong>${data.name}</strong><br/>
                  出生年份: ${data.value[0]}<br/>
                  寿命: ${data.value[1]}岁<br/>
                  ${data.bio ? '简介: ' + data.bio.substring(0, 50) + '...' : ''}`
        }
      },
      xAxis: {
        type: 'value',
        name: '出生年份',
        min: 1500,
        max: 2000
      },
      yAxis: {
        type: 'value',
        name: '寿命（岁）'
      },
      series: [{
        type: 'scatter',
        symbolSize: (val) => Math.sqrt(val[2]) / 2,
        data: data,
        itemStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.5, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.8)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.2)' }
          ])
        }
      }],
      grid: {
        left: '60px',
        right: '40px',
        bottom: '60px',
        top: '40px'
      }
    }
    
    lifespanChart.setOption(option)
  })
}

const loadData = async () => {
  try {
    ElMessage.info('正在加载历史数据...')
    
    const [persons, events, stats] = await Promise.all([
      timelineApi.getPersons(),
      timelineApi.getEvents(),
      timelineApi.getStats()
    ])
    
    historicalPersons.value = persons
    allHistoricalEvents.value = events
    
    if (stats.year_range) {
      minYear.value = Math.max(1500, stats.year_range.min - 50)
      maxYear.value = Math.min(2025, stats.year_range.max + 10)
    }
    
    ElMessage.success(`加载完成: ${persons.length} 位人物, ${events.length} 件事件`)
    
    await nextTick()
    initAgeChart()
    initLifespanChart()
  } catch (error) {
    ElMessage.error('加载数据失败: ' + error.message)
  }
}

const handleResize = () => {
  if (ageChart) ageChart.resize()
  if (lifespanChart) lifespanChart.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoPlay()
  if (ageChart) ageChart.dispose()
  if (lifespanChart) lifespanChart.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.historical-timeline {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 40px);
}

.chart-card,
.control-card,
.persons-card,
.events-card,
.stats-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.current-year-display {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  text-align: center;
  margin-bottom: 20px;
}

.year-controls {
  padding: 10px 20px;
}

.control-buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
}

.persons-list {
  max-height: 600px;
  overflow-y: auto;
}

.person-card {
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.person-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.person-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.person-name {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
}

.person-content {
  font-size: 14px;
}

.person-dates {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 10px;
  color: #606266;
}

.person-dates .el-icon {
  margin-right: 5px;
}

.alive-status {
  color: #67C23A;
  font-weight: bold;
}

.person-bio {
  color: #909399;
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

:deep(.el-timeline-item__content) {
  cursor: pointer;
}

:deep(.el-timeline-item__content h4) {
  margin: 0 0 10px 0;
  color: #303133;
}

:deep(.el-timeline-item__content p) {
  margin: 0 0 10px 0;
  color: #606266;
}
</style>
