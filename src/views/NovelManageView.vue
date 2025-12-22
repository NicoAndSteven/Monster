<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

interface Chapter {
  id: number
  num: number
  title: string
  flipped: boolean
}

const chapters = ref<Chapter[]>([
  { id: 1, num: 1, title: '第一章：开端', flipped: false },
  { id: 2, num: 2, title: '第二章：遭遇', flipped: false },
  { id: 3, num: 3, title: '第三章：冲突', flipped: false },
])

const generationMode = ref('api') // 'api' or 'rpa'

const generateNext = async (e: MouseEvent) => {
  createParticles(e.clientX, e.clientY)
  
  // 模拟发送请求到后端
  // 实际代码中应使用 fetch/axios 调用后端 API
  try {
    const nextNum = chapters.value.length + 1
    
    // 构造请求体
    const payload = {
      chapter_num: nextNum,
      prompt: `第${nextNum}章剧情`,
      mode: generationMode.value
    }

    console.log('Generating with mode:', generationMode.value)
    
    // 这里使用 fetch 模拟调用
    const response = await fetch(`http://127.0.0.1:8000/api/novels/novel-123/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) {
        throw new Error('Generation failed')
    }

    await response.json()
    
    chapters.value.push({
      id: nextNum,
      num: nextNum,
      title: `第${nextNum}章：${generationMode.value === 'rpa' ? '(RPA抓取)' : '(API生成)'}`,
      flipped: false
    })

    ElMessage.success(`生成成功 (${generationMode.value === 'rpa' ? 'RPA模式' : 'API模式'})`)
  } catch (error) {
    ElMessage.error('生成失败，请检查后端服务')
    console.error(error)
  }
}

const createParticles = (x: number, y: number) => {
  for (let i = 0; i < 20; i++) {
    const particle = document.createElement('div')
    particle.classList.add('particle')
    document.body.appendChild(particle)
    
    const angle = Math.random() * Math.PI * 2
    const velocity = 2 + Math.random() * 2
    const tx = Math.cos(angle) * velocity * 50
    const ty = Math.sin(angle) * velocity * 50
    
    particle.style.left = `${x}px`
    particle.style.top = `${y}px`
    particle.style.setProperty('--tx', `${tx}px`)
    particle.style.setProperty('--ty', `${ty}px`)
    
    setTimeout(() => particle.remove(), 1000)
  }
}
</script>

<template>
  <div class="novel-manage animate__animated animate__fadeIn">
    <div class="header">
      <h2>小说管理</h2>
      <div class="controls">
        <el-select v-model="generationMode" placeholder="选择生成模式" style="width: 150px; margin-right: 1rem;">
          <el-option label="API 生成" value="api" />
          <el-option label="RPA 抓取" value="rpa" />
        </el-select>
        <el-button @click="generateNext" class="generate-btn" type="warning">
          生成下一章
        </el-button>
      </div>
    </div>

    <div class="chapter-grid">
      <div 
        v-for="chapter in chapters" 
        :key="chapter.id" 
        class="chapter-card-container"
        @mouseenter="chapter.flipped = true"
        @mouseleave="chapter.flipped = false"
      >
        <div class="chapter-card" :class="{ flipped: chapter.flipped }">
          <div class="card-face front">
            <h3>第 {{ chapter.num }} 章</h3>
            <p>{{ chapter.title }}</p>
          </div>
          <div class="card-face back">
            <p>内容预览...</p>
            <el-button size="small" link>编辑</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.controls {
  display: flex;
  align-items: center;
}

.chapter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 2rem;
}

.chapter-card-container {
  perspective: 1000px;
  height: 250px;
  cursor: pointer;
}

.chapter-card {
  width: 100%;
  height: 100%;
  position: relative;
  transition: transform 0.6s;
  transform-style: preserve-3d;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
  border-radius: 8px;
}

.chapter-card.flipped {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  box-sizing: border-box;
}

.front {
  background: #1e1e1e;
  border: 1px solid #333;
  color: #fff;
}

.back {
  background: #1a2a6c;
  color: #d4af37;
  transform: rotateY(180deg);
  border: 1px solid #d4af37;
}

.generate-btn {
  background-color: #d4af37;
  color: #000;
  border: none;
}
</style>

<style>
/* Global styles for particles */
.particle {
  position: fixed;
  width: 6px;
  height: 6px;
  background: #d4af37;
  border-radius: 50%;
  pointer-events: none;
  animation: explode 0.8s ease-out forwards;
  z-index: 9999;
}

@keyframes explode {
  0% { transform: translate(0, 0) scale(1); opacity: 1; }
  100% { transform: translate(var(--tx), var(--ty)) scale(0); opacity: 0; }
}
</style>
