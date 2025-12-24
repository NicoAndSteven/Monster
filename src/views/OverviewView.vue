<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Monitor, TrendCharts, Money, User, Picture, Microphone, Loading } from '@element-plus/icons-vue'

interface Analytics {
  assets_count: {
    characters: number
    scenes: number
    audio_files: number
  }
  distribution: {
    douyin: number[]
    xiaohongshu: number[]
  }
}

const analytics = ref<Analytics>({
  assets_count: { characters: 12, scenes: 45, audio_files: 88 },
  distribution: { douyin: [], xiaohongshu: [] }
})

const loading = ref(true)
const activeTasks = ref<any[]>([])
let pollTimer: any = null

const fetchStats = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/dashboard/stats')
    if (res.ok) {
      const data = await res.json()
      
      if (data.analytics) {
        analytics.value = { ...analytics.value, ...data.analytics }
      }

      if (data.asset_types) {
         analytics.value.assets_count = {
            characters: data.asset_types['character'] || 0,
            scenes: data.asset_types['scene'] || 0,
            audio_files: data.asset_types['audio'] || 0
         }
      }
    }
  } catch (e) {
    console.error("Failed to fetch stats", e)
  } finally {
    loading.value = false
  }
}

const fetchTasks = async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/api/tasks')
        if (res.ok) {
            activeTasks.value = await res.json()
        }
    } catch (e) {
        console.error(e)
    }
}

onMounted(() => {
  fetchStats()
  fetchTasks()
  pollTimer = setInterval(fetchTasks, 2000)
})

onBeforeUnmount(() => {
    if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="dashboard-view animate__animated animate__fadeIn">
    
    <!-- 1. Real-time Task Center -->
    <div class="section-card glass-panel mb-4">
      <div class="section-header">
        <h3><el-icon><Monitor /></el-icon> 实时任务中心</h3>
        <span class="status-tag" :class="activeTasks.length > 0 ? 'processing' : ''">
          {{ activeTasks.length > 0 ? `${activeTasks.length} 个任务运行中` : '系统空闲' }}
        </span>
      </div>
      
      <div v-if="activeTasks.length === 0" class="empty-tasks">
        <el-empty description="当前无后台任务" :image-size="80" />
      </div>

      <div v-else class="task-list">
        <div v-for="task in activeTasks" :key="task.id" class="task-item">
            <div class="task-header">
                <span class="task-title">
                    <span class="task-type-badge">{{ task.type === 'outline_generation' ? '大纲' : '章节' }}</span>
                    {{ task.description }}
                </span>
                <span class="task-time">{{ new Date(task.updated_at).toLocaleTimeString() }}</span>
            </div>
            
            <div class="task-body">
                <!-- Stage Stepper -->
                <div v-if="task.stages && task.stages.length > 0" class="task-stages">
                    <el-steps :active="task.current_stage_index" finish-status="success" align-center simple>
                        <el-step v-for="(stage, index) in task.stages" :key="index" :title="stage" />
                    </el-steps>
                </div>

                <!-- Progress Bar -->
                <div class="task-progress">
                    <el-progress 
                        :percentage="task.progress" 
                        :status="task.status === 'failed' ? 'exception' : (task.status === 'completed' ? 'success' : '')"
                        :stroke-width="12"
                        striped
                        striped-flow
                        :duration="20"
                    />
                </div>
                
                <!-- Console/Log View -->
                <div class="task-console">
                    <div class="console-line">
                        <span class="console-prompt">></span>
                        <span class="console-time">[{{ new Date(task.updated_at).toLocaleTimeString() }}]</span>
                        <span class="console-msg" :class="task.status">
                            <el-icon v-if="task.status === 'processing'" class="is-loading"><Loading /></el-icon>
                            {{ task.step }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- 2. Asset Statistics (New) -->
      <div class="section-card glass-panel animate__animated animate__fadeInUp" style="animation-delay: 0.1s;">
        <div class="section-header">
          <h3><el-icon><Money /></el-icon> 资源统计</h3>
        </div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon character-icon">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ analytics.assets_count.characters }}</span>
              <span class="stat-label">角色立绘</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon scene-icon">
              <el-icon><Picture /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ analytics.assets_count.scenes }}</span>
              <span class="stat-label">场景图</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon audio-icon">
              <el-icon><Microphone /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ analytics.assets_count.audio_files }}</span>
              <span class="stat-label">音频文件</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Distribution Performance (Analytics) -->
      <div class="section-card glass-panel animate__animated animate__fadeInUp" style="animation-delay: 0.2s;">
        <div class="section-header">
          <h3><el-icon><TrendCharts /></el-icon> 分发表现分析</h3>
        </div>
        <div class="chart-placeholder">
          <!-- Simple CSS Bar Chart for MVP -->
          <div class="bar-chart">
            <div class="chart-column">
              <div class="bars-group">
                <div class="bar douyin" style="height: 60%"></div>
                <div class="bar xiaohongshu" style="height: 40%"></div>
              </div>
              <span class="label">周一</span>
            </div>
            <div class="chart-column">
              <div class="bars-group">
                <div class="bar douyin" style="height: 70%"></div>
                <div class="bar xiaohongshu" style="height: 45%"></div>
              </div>
              <span class="label">周二</span>
            </div>
            <div class="chart-column">
              <div class="bars-group">
                <div class="bar douyin" style="height: 85%"></div>
                <div class="bar xiaohongshu" style="height: 50%"></div>
              </div>
              <span class="label">周三</span>
            </div>
             <div class="chart-column">
              <div class="bars-group">
                <div class="bar douyin" style="height: 50%"></div>
                <div class="bar xiaohongshu" style="height: 30%"></div>
              </div>
              <span class="label">周四</span>
            </div>
             <div class="chart-column">
              <div class="bars-group">
                <div class="bar douyin" style="height: 90%"></div>
                <div class="bar xiaohongshu" style="height: 60%"></div>
              </div>
              <span class="label">周五</span>
            </div>
          </div>
          <div class="legend">
            <span class="dot douyin"></span> 抖音
            <span class="dot xiaohongshu"></span> 小红书
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.dashboard-view {
  max-width: 1400px;
  margin: 0 auto;
  color: var(--text-color);
}

.mb-4 {
  margin-bottom: 2rem;
}

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: var(--card-hover-shadow);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 0.5rem;
}

.section-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--primary-color);
  font-size: 1.2rem;
}

.status-tag {
  font-size: 0.9rem;
  padding: 0.2rem 0.8rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
}

.status-tag.processing {
  background: var(--accent-glow);
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  animation: pulse 2s infinite;
}

/* Custom Pipeline */
.custom-pipeline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 1rem;
}

.pipeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  margin-bottom: 1rem;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.icon-emoji {
  font-size: 1.8rem;
  z-index: 2;
}

.step-label {
  font-size: 0.9rem;
  color: #888;
  font-weight: 500;
}

.step-line {
  position: absolute;
  top: 30px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: rgba(255,255,255,0.1);
  z-index: 0;
}

/* Step States */
.pipeline-step.active .step-icon {
  background: var(--accent-glow);
  border-color: var(--primary-color);
  transform: scale(1.1);
  box-shadow: 0 0 20px var(--primary-color);
}

.pipeline-step.active .step-label {
  color: var(--primary-color);
}

.pipeline-step.completed .step-icon {
  background: var(--primary-color);
  color: #000;
}

.pipeline-step.completed .step-label {
  color: var(--primary-color);
}

.pipeline-step.completed .step-line {
  background: var(--primary-color);
}

/* Spinner for Active State */
.spinner-ring {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border: 2px solid transparent;
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Balance Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.balance-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.balance-item {
  background: rgba(0, 0, 0, 0.2);
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1px solid transparent;
  transition: all 0.3s;
  cursor: default;
}

.hover-scale:hover {
  transform: translateY(-5px);
  border-color: var(--primary-color);
  background: var(--accent-glow);
}

.balance-item.low-balance {
  border-color: #ff4757;
  animation: pulse-red 2s infinite;
}

.provider {
  font-size: 0.9rem;
  color: #aaa;
}

.amount {
  font-size: 1.8rem;
  font-weight: bold;
  color: var(--text-color);
}

.unit {
  font-size: 0.8rem;
  color: #666;
}

/* Chart */
.chart-placeholder {
  height: 250px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.bar-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 100%;
  padding-bottom: 1rem;
}

.chart-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  width: 40px;
}

.bars-group {
  display: flex;
  gap: 6px;
  align-items: flex-end;
  height: 80%;
  width: 100%;
}

.bar {
  flex: 1;
  border-radius: 4px 4px 0 0;
  transition: height 1s ease;
  opacity: 0.8;
}

.bar:hover {
  opacity: 1;
  filter: brightness(1.2);
}

.header-actions {
    display: flex;
    gap: 1rem;
}

.outline-content {
    padding: 1rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    margin-top: 1rem;
    color: #e2e8f0;
}


.bar.douyin {
  background: #ff0050; 
  box-shadow: 0 0 10px rgba(255,0,80,0.3);
}

.bar.xiaohongshu {
  background: #ff2442; 
  box-shadow: 0 0 10px rgba(255,36,66,0.3);
}

.label {
  margin-top: 0.8rem;
  font-size: 0.8rem;
  color: #aaa;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  transition: transform 0.3s ease, background 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.character-icon {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

.scene-icon {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.audio-icon {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.8;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
}

.dot.douyin { background: #ff0050; }
.dot.xiaohongshu { background: #ff2442; }

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(212, 175, 55, 0); }
  100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
}

@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(255, 71, 87, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
}
/* Task Item Styles */
.task-item {
    background: rgba(0,0,0,0.2);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.05);
}

.task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.task-title {
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.task-type-badge {
    font-size: 0.8rem;
    background: var(--primary-color);
    color: #000;
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    font-weight: bold;
}

.task-time {
    color: #666;
    font-size: 0.9rem;
}

.task-stages {
    margin-bottom: 2rem;
}

/* Console View */
.task-console {
    background: #1e1e1e;
    border-radius: 6px;
    padding: 1rem;
    margin-top: 1.5rem;
    font-family: 'Consolas', 'Monaco', monospace;
    border: 1px solid #333;
}

.console-line {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    font-size: 0.9rem;
    line-height: 1.5;
}

.console-prompt {
    color: var(--primary-color);
    font-weight: bold;
}

.console-time {
    color: #666;
}

.console-msg {
    color: #ccc;
}

.console-msg.processing {
    color: var(--primary-color);
    animation: blink 1s infinite;
}

@keyframes blink {
    50% { opacity: 0.5; }
}

.task-progress {
    margin-top: 1rem;
}
</style>
