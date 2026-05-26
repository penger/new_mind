<template>
  <div class="login-container" ref="containerRef">
    <canvas ref="canvasRef" class="particle-canvas"></canvas>
    <div class="login-wrapper">
      <h1 class="title">知识图谱</h1>
      <div class="login-panel">
        <div class="input-group">
          <input
            v-model="username"
            type="text"
            placeholder="用户名"
            @keyup.enter="handleLogin"
          />
        </div>
        
        <div class="input-group">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="密码"
            @keyup.enter="handleLogin"
          />
          <button 
            class="toggle-password"
            @click="showPassword = !showPassword"
            type="button"
          >
            {{ showPassword ? '🙈' : '👁️' }}
          </button>
        </div>
        
        <button 
          class="login-btn"
          :class="{ loading: loading }"
          :disabled="loading"
          @click="handleLogin"
        >
          <span v-if="!loading">登录</span>
          <span v-else class="loading-dots">登录中...</span>
        </button>
        
        <div class="error-message" v-if="errorMessage">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['login'])

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)
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
  errorMessage.value = ''
  
  if (!username.value) {
    errorMessage.value = '请输入用户名'
    return
  }
  
  if (!password.value) {
    errorMessage.value = '请输入密码'
    return
  }
  
  loading.value = true
  
  try {
    const response = await fetch(`/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || '登录失败')
    }
    
    const userData = {
      id: data.id,
      role: data.role,
      username: data.username,
      themes: data.themes || [],
      loginTime: new Date().toISOString()
    }
    
    localStorage.setItem('user', JSON.stringify(userData))
    
    emit('login', userData)
    ElMessage.success(`${data.role === 'admin' ? '管理员' : '游客'}登录成功`)
    
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查用户名和密码'
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

.input-group {
  position: relative;
  display: flex;
  align-items: center;
}

.input-group input {
  width: 100%;
  padding: 14px 18px;
  padding-right: 45px;
  background: rgba(51, 65, 85, 0.6);
  border: 1px solid rgba(129, 140, 248, 0.2);
  border-radius: 12px;
  color: #f1f5f9;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.input-group input::placeholder {
  color: #94a3b8;
}

.input-group input:focus {
  border-color: rgba(129, 140, 248, 0.5);
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
}

.toggle-password {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
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

.error-message {
  text-align: center;
  color: #f87171;
  font-size: 14px;
  padding: 8px;
  background: rgba(248, 113, 113, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(248, 113, 113, 0.3);
}
</style>
