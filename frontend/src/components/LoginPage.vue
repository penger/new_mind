<template>
  <div class="login-container" ref="containerRef">
    <canvas ref="canvasRef" class="particle-canvas"></canvas>
    <div class="login-wrapper">
      <h1 class="title">🧠 知识图谱</h1>
      <div class="login-panel">
        <div class="role-selector">
          <div 
            class="role-btn"
            :class="{ active: loginForm.role === 'viewer' }"
            @click="loginForm.role = 'viewer'"
          >
            <span class="role-icon">👁️</span>
            <span class="role-text">游客</span>
          </div>
          <div 
            class="role-btn"
            :class="{ active: loginForm.role === 'admin' }"
            @click="loginForm.role = 'admin'"
          >
            <span class="role-icon">🔐</span>
            <span class="role-text">管理员</span>
          </div>
        </div>
        
        <div class="password-input" v-if="loginForm.role === 'admin'">
          <input
            v-model="loginForm.password"
            type="password"
            placeholder="密钥"
            @keyup.enter="handleLogin"
          />
        </div>
        
        <button 
          class="login-btn"
          :class="{ loading: loading }"
          :disabled="loading"
          @click="handleLogin"
        >
          <span v-if="!loading">
            {{ loginForm.role === 'admin' ? '管理员登录' : '游客登录' }}
          </span>
          <span v-else class="loading-dots">登录中...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['login'])

const loginForm = reactive({
  role: 'viewer',
  password: ''
})

const loading = ref(false)
const containerRef = ref(null)
const canvasRef = ref(null)

let animationId = null
let particles = []
let mouse = { x: null, y: null }

class Particle {
  constructor(canvas) {
    this.x = Math.random() * canvas.width
    this.y = Math.random() * canvas.height
    this.vx = (Math.random() - 0.5) * 0.5
    this.vy = (Math.random() - 0.5) * 0.5
    this.radius = Math.random() * 2 + 1
    this.canvas = canvas
  }

  update() {
    this.x += this.vx
    this.y += this.vy

    if (mouse.x !== null && mouse.y !== null) {
      const dx = mouse.x - this.x
      const dy = mouse.y - this.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      if (distance < 150) {
        this.x += dx * 0.01
        this.y += dy * 0.01
      }
    }

    if (this.x < 0 || this.x > this.canvas.width) this.vx *= -1
    if (this.y < 0 || this.y > this.canvas.height) this.vy *= -1
  }

  draw(ctx) {
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(129, 140, 248, 0.9)'
    ctx.fill()
  }
}

function initParticles() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  canvas.width = container.offsetWidth
  canvas.height = container.offsetHeight

  particles = []
  const particleCount = Math.floor((canvas.width * canvas.height) / 15000)
  
  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle(canvas))
  }
}

function drawLines(ctx) {
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const distance = Math.sqrt(dx * dx + dy * dy)

      if (distance < 120) {
        const opacity = (1 - distance / 120) * 0.25
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.strokeStyle = `rgba(139, 92, 246, ${opacity})`
        ctx.lineWidth = 1
        ctx.stroke()
      }
    }
  }
}

function animate() {
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  drawLines(ctx)
  particles.forEach(particle => {
    particle.update()
    particle.draw(ctx)
  })

  animationId = requestAnimationFrame(animate)
}

function handleMouseMove(e) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
}

function handleMouseLeave() {
  mouse.x = null
  mouse.y = null
}

function handleResize() {
  initParticles()
}

const handleLogin = async () => {
  if (loginForm.role === 'admin') {
    if (!loginForm.password) {
      ElMessage.warning('请输入密钥')
      return
    }
    
    const password = loginForm.password
    const today = new Date()
    const currentDateStr = `${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`
    
    const hasHappy = password.toLowerCase().includes('happy')
    const hasTodayDate = password.includes(currentDateStr)
    
    if (!hasHappy || !hasTodayDate) {
      ElMessage.error('密钥无效')
      return
    }
  }
  
  loading.value = true
  
  try {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    const userData = {
      role: loginForm.role,
      username: loginForm.role === 'admin' ? 'admin' : 'viewer',
      loginTime: new Date().toISOString()
    }
    
    localStorage.setItem('user', JSON.stringify(userData))
    
    ElMessage.success(loginForm.role === 'admin' ? '管理员登录成功' : '游客登录成功')
    emit('login', userData)
  } catch (error) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initParticles()
  animate()
  
  window.addEventListener('resize', handleResize)
  containerRef.value?.addEventListener('mousemove', handleMouseMove)
  containerRef.value?.addEventListener('mouseleave', handleMouseLeave)
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  window.removeEventListener('resize', handleResize)
  containerRef.value?.removeEventListener('mousemove', handleMouseMove)
  containerRef.value?.removeEventListener('mouseleave', handleMouseLeave)
})
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  overflow: hidden;
}

.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.login-wrapper {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 40px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(51, 65, 85, 0.85) 100%);
  border-radius: 24px;
  border: 1px solid rgba(129, 140, 248, 0.2);
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
}

.title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: 2px;
}

.login-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  max-width: 320px;
}

.role-selector {
  display: flex;
  gap: 12px;
}

.role-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 20px;
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid rgba(129, 140, 248, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.role-btn:hover {
  background: rgba(129, 140, 248, 0.15);
  border-color: rgba(129, 140, 248, 0.3);
  transform: translateY(-2px);
}

.role-btn.active {
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
  border-color: rgba(129, 140, 248, 0.5);
  box-shadow: 0 0 20px rgba(129, 140, 248, 0.2);
}

.role-icon {
  font-size: 18px;
}

.role-text {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
}

.password-input input {
  width: 100%;
  padding: 14px 18px;
  background: rgba(51, 65, 85, 0.6);
  border: 1px solid rgba(129, 140, 248, 0.2);
  border-radius: 12px;
  color: #f1f5f9;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.password-input input::placeholder {
  color: #94a3b8;
}

.password-input input:focus {
  border-color: rgba(129, 140, 248, 0.5);
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
}

.login-btn {
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-dots {
  display: inline-flex;
  gap: 4px;
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s infinite;
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}
</style>
