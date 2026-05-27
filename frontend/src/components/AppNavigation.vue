<template>
  <div class="app-navigation">
    <el-header class="nav-header">
      <div class="header-left">
        <h2>📚 应用导航</h2>
      </div>
      <div class="header-right">
        <el-button @click="goBack" type="primary">
          ← 返回主应用
        </el-button>
      </div>
    </el-header>

    <el-main class="nav-main">
      <div class="apps-grid">
        <el-card 
          v-for="app in apps" 
          :key="app.id" 
          class="app-card"
          shadow="hover"
          @click="navigateTo(app)"
        >
          <div class="app-icon">{{ app.icon }}</div>
          <div class="app-name">{{ app.name }}</div>
          <div class="app-description">{{ app.description }}</div>
        </el-card>
      </div>
    </el-main>
  </div>
</template>

<script setup>
const emit = defineEmits(['navigate', 'back']);

const apps = [
  {
    id: 1,
    name: '关系图谱编辑器',
    icon: '🕸️',
    description: '创建和管理知识关系图谱',
    path: 'graph',
    type: 'component'
  },
  {
    id: 2,
    name: '历史时间轴',
    icon: '📅',
    description: '探索历史人物和事件',
    path: '/timeline.html',
    type: 'external'
  },
  {
    id: 3,
    name: '滑块拼图',
    icon: '🧩',
    description: '益智滑块拼图游戏',
    path: '/puzzle.html',
    type: 'external'
  }
];

const navigateTo = (app) => {
  emit('navigate', app);
};

const goBack = () => {
  emit('back');
};
</script>

<style scoped>
.app-navigation {
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 20px 40px;
}

.nav-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.nav-main {
  padding: 40px;
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.app-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 16px;
  overflow: hidden;
  background: white;
}

.app-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}

.app-icon {
  font-size: 64px;
  text-align: center;
  padding: 30px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-name {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  padding: 20px 20px 10px;
  color: #303133;
}

.app-description {
  font-size: 14px;
  text-align: center;
  padding: 0 20px 20px;
  color: #909399;
}
</style>
