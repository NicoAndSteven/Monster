<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch, nextTick, onUnmounted } from 'vue'
import { Search, User, PictureFilled, Headset, VideoCamera, Plus, MagicStick, Reading, Connection } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useProjectStore } from '@/stores/projectStore'
import { marked } from 'marked'
import * as echarts from 'echarts'

const activeTab = ref('knowledge')
const projectStore = useProjectStore()
const API_BASE = 'http://localhost:8000/api'

// Data
const assets = ref<any[]>([])
const loading = ref(false)
const analyzing = ref(false)

// Graph
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// Wiki Dialog
const wikiDialogVisible = ref(false)
const currentWikiAsset = ref<any>(null)
const isGeneratingWiki = ref(false)
const wikiContent = ref('')

// Create Dialog State
const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  name: '',
  role: '',
  tags: '',
  img: '' // Optional
})

const createRules = reactive<FormRules>({
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  role: [{ required: true, message: '请输入角色定位', trigger: 'blur' }]
})

const refreshingAsset = ref<string | null>(null)

// Graph Logic
const initGraph = (data?: { nodes: any[], links: any[] }) => {
  if (!chartRef.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  let nodes: any[] = []
  let links: any[] = []

  if (data && data.nodes && data.nodes.length > 0) {
      nodes = data.nodes.map((n, i) => ({
          ...n,
          id: n.name,
          itemStyle: { color: i % 2 === 0 ? '#d4af37' : '#ff0050' },
          symbolSize: n.symbolSize || 30
      }))
      links = data.links
  } else {
      // Fallback
      nodes = filteredCharacters.value.map((char, index) => ({
        id: char.name,
        name: char.name,
        symbolSize: 50,
        category: 0,
        itemStyle: { color: index % 2 === 0 ? '#d4af37' : '#ff0050' },
        value: char.role
      }))
  }

  const option = {
    backgroundColor: 'transparent',
    title: {
      text: '人物关系图谱',
      textStyle: { color: '#fff' },
      left: 'center'
    },
    tooltip: {},
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut' as any,
    series: [
      {
        type: 'graph',
        layout: 'force',
        symbolSize: 50,
        roam: true,
        label: { show: true, color: '#fff' },
        edgeSymbol: ['circle', 'arrow'],
        edgeSymbolSize: [4, 10],
        edgeLabel: { fontSize: 12, color: '#ccc' },
        data: nodes,
        links: links,
        lineStyle: { opacity: 0.9, width: 2, curveness: 0.1 },
        force: { repulsion: 1000, edgeLength: 200 }
      }
    ]
  }
  chartInstance.setOption(option)
}

const fetchGraphData = async () => {
    if (!projectStore.currentProject) return
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/relationships`)
        if (res.ok) {
            const data = await res.json()
            initGraph(data)
        } else {
            initGraph()
        }
    } catch (e) {
        initGraph()
    }
}

watch(activeTab, (newTab) => {
    if (newTab === 'relationship') {
        nextTick(() => {
            fetchGraphData()
        })
    }

})

// Resize chart on window resize
window.addEventListener('resize', () => {
    chartInstance?.resize()
})

onUnmounted(() => {
    window.removeEventListener('resize', () => {
        chartInstance?.resize()
    })
    chartInstance?.dispose()
})

// Methods
const openWiki = (asset: any) => {
    currentWikiAsset.value = asset
    wikiContent.value = asset.details || ''
    wikiDialogVisible.value = true
}

const generateWiki = async () => {
    if (!currentWikiAsset.value) return
    isGeneratingWiki.value = true
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject!.id}/assets/${currentWikiAsset.value.id}/wiki`, {
            method: 'POST'
        })
        if (res.ok) {
            const data = await res.json()
            wikiContent.value = data.data.details
            currentWikiAsset.value.details = data.data.details
            // Update in list
            const idx = assets.value.findIndex(a => a.id === currentWikiAsset.value.id)
            if (idx !== -1) {
                assets.value[idx] = data.data
            }
            ElMessage.success('百科词条生成成功')
        } else {
            ElMessage.error('生成失败')
        }
    } catch (e) {
        ElMessage.error('网络错误')
    } finally {
        isGeneratingWiki.value = false
    }
}

const handleRefreshAsset = async (asset: any) => {
    refreshingAsset.value = asset.id
    ElMessage.info(`正在重新分析角色：${asset.name}...`)
    
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject!.id}/assets/${asset.name}/refresh`, {
            method: 'POST'
        })
        
        if (res.ok) {
            const data = await res.json()
            if (data.status === 'success') {
                ElMessage.success('角色信息已更新')
                loadAssets()
            } else {
                ElMessage.info('未发现新信息')
            }
        } else {
            ElMessage.error('更新失败')
        }
    } catch (e) {
        ElMessage.error('请求出错')
    } finally {
        refreshingAsset.value = null
    }
}

const autoAnalyzeAssets = async () => {
    if (!projectStore.currentProject) return
    
    analyzing.value = true
    ElMessage.info('正在分析最新章节内容以提取资产...')
    
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/analyze-assets`, {
            method: 'POST'
        })
        
        if (res.ok) {
            const data = await res.json()
            if (data.new_assets_count > 0 || data.updated_assets_count > 0) {
                ElMessage.success(`分析完成：新增 ${data.new_assets_count} 个资产，更新 ${data.updated_assets_count} 个资产`)
                loadAssets()
            } else {
                ElMessage.info('分析完成，未发现新的资产变更')
            }
        } else {
            ElMessage.error('分析失败')
        }
    } catch (e) {
        ElMessage.error('请求出错')
    } finally {
        analyzing.value = false
    }
}

// Fetch Assets
const loadAssets = async () => {
  if (!projectStore.currentProject) return
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/assets`)
    if (res.ok) {
      assets.value = await res.json()
    }
  } catch (e) {
    ElMessage.error('加载资产失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAssets()
})

watch(() => projectStore.currentProject, (newVal) => {
  if (newVal) loadAssets()
})

// Local placeholder generator to avoid external requests
const getPlaceholder = (text: string, bgColor = '#1a2a6c') => {
  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="150" height="200" viewBox="0 0 150 200">
    <rect width="100%" height="100%" fill="${bgColor}"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#ffffff">${text}</text>
  </svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

const characters = computed(() => {
  return assets.value.filter(a => a.type === 'character').map(c => ({
    ...c,
    img: c.img || getPlaceholder(c.name, '#1e293b')
  }))
})

const mediaAssets = computed(() => {
  // Now includes audio
  return assets.value.filter(a => ['audio', 'video', 'image'].includes(a.type))
})

const filterText = ref('')

const filteredCharacters = computed(() => {
  if (!filterText.value) return characters.value
  const query = filterText.value.toLowerCase()
  return characters.value.filter(char => 
    char.name.toLowerCase().includes(query) || 
    (char.role && char.role.toLowerCase().includes(query)) ||
    (char.tags && char.tags.some((tag: string) => tag.toLowerCase().includes(query)))
  )
})

const filteredMedia = computed(() => {
  if (!filterText.value) return mediaAssets.value
  const query = filterText.value.toLowerCase()
  return mediaAssets.value.filter(item => 
    item.name.toLowerCase().includes(query) ||
    item.type.toLowerCase().includes(query)
  )
})

const openCreateDialog = () => {
  createForm.name = ''
  createForm.role = ''
  createForm.tags = ''
  createDialogVisible.value = true
}

const handleCreateCharacter = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid && projectStore.currentProject) {
      try {
        const newAsset = {
          id: Date.now(),
          type: 'character',
          name: createForm.name,
          role: createForm.role,
          tags: createForm.tags.split(/[,， ]+/).filter(Boolean),
          img: null
        }
        
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/assets`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newAsset)
        })
        
        if (res.ok) {
          ElMessage.success('创建成功')
          createDialogVisible.value = false
          loadAssets()
        } else {
           const err = await res.json()
           ElMessage.error(err.detail || '创建失败')
        }
      } catch (e) {
        ElMessage.error('请求出错')
      }
    }
  })
}


const deleteAsset = async (id: number) => {
  if (!projectStore.currentProject) return
  
  try {
    await ElMessageBox.confirm('确定要删除这个资源吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/assets/${id}`, {
      method: 'DELETE'
    })
    
    if (res.ok) {
      ElMessage.success('删除成功')
      loadAssets()
    } else {
      ElMessage.error('删除失败')
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('请求出错')
    }
  }
}

// const deleteMedia = deleteAsset -> Removed, use deleteAsset directly


  const editCharacter = (char: any) => {
   ElMessageBox.prompt('修改角色名称', '编辑角色', {
     confirmButtonText: '保存',
     cancelButtonText: '取消',
     inputValue: char.name,
   }).then(async () => {
     // TODO: Implement full edit, for now just name
     ElMessage.info('暂仅支持删除操作，完整编辑功能开发中')
   }).catch(() => {})
}

const previewMedia = (item: any) => {
  ElMessage.success(`正在预览: ${item.name}`)
}


</script>

<template>
  <div class="library-view animate__animated animate__fadeIn">
    <div class="header-actions">
      <h2>资产中心</h2>
      <div class="header-right" style="display: flex; gap: 10px;">
          <el-button type="warning" :icon="MagicStick" :loading="analyzing" @click="autoAnalyzeAssets">
            智能提取/更新资产
          </el-button>
          <el-input
            v-model="filterText"
            placeholder="搜索资产..."
            :prefix-icon="Search"
            class="search-input"
          />
      </div>
    </div>

    <div class="library-container glass-effect">
      <el-tabs v-model="activeTab" class="custom-tabs">
        
        <!-- Tab 1: Knowledge Base -->
        <el-tab-pane name="knowledge">
          <template #label>
            <span class="tab-label"><el-icon><User /></el-icon> 角色/场景库</span>
          </template>
          
          <div class="card-grid">
            <div class="asset-card" v-for="char in filteredCharacters" :key="char.id">
              <div class="card-image">
                <img :src="char.img" :alt="char.name" />
                <div class="hover-overlay">
                  <el-button size="small" type="primary" :icon="Reading" @click="openWiki(char)">百科</el-button>
                  <el-button size="small" @click="editCharacter(char)">编辑</el-button>
                  <el-button size="small" type="danger" @click="deleteAsset(char.id)">删除</el-button>
                  <el-button 
                    size="small" 
                    type="warning" 
                    :loading="refreshingAsset === char.id"
                    @click="handleRefreshAsset(char)"
                  >
                    更新
                  </el-button>
                </div>
              </div>
              <div class="card-info">
                <h4>{{ char.name }}</h4>
                <p class="role">{{ char.role }}</p>
                <div class="tags">
                  <span v-for="tag in char.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
            <!-- Add New Card -->
            <div class="asset-card add-card" @click="openCreateDialog">
              <div class="add-content">
                <el-icon class="plus-icon"><Plus /></el-icon>
                <span>新建角色</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: Relationship Graph -->
        <el-tab-pane name="relationship">
            <template #label>
                <span class="tab-label"><el-icon><Connection /></el-icon> 关系图谱</span>
            </template>
            <div class="graph-wrapper">
                <div ref="chartRef" class="chart-container"></div>
                <div class="graph-controls" v-if="filteredCharacters.length === 0">
                    <el-empty description="暂无角色数据，请先在【角色库】添加角色" />
                </div>
            </div>
        </el-tab-pane>

        <!-- Tab 3: Multimedia -->
        <el-tab-pane name="multimedia">
          <template #label>
            <span class="tab-label"><el-icon><PictureFilled /></el-icon> 多媒体仓库</span>
          </template>

          <div class="waterfall-grid">
            <div class="media-item glass-effect" v-for="item in filteredMedia" :key="item.id">
              <div class="media-icon">
                <el-icon v-if="item.type === 'audio'"><Headset /></el-icon>
                <el-icon v-else-if="item.type === 'video'"><VideoCamera /></el-icon>
                <el-icon v-else><PictureFilled /></el-icon>
              </div>
              <div class="media-info">
                <h5>{{ item.name }}</h5>
                <p>{{ item.role }}</p> <!-- Description -->
                <p class="date" v-if="item.file_path">
                    <audio v-if="item.type === 'audio'" controls :src="`http://localhost:8000/data/${item.file_path}`" style="width: 100%; height: 30px; margin-top: 5px;"></audio>
                </p>
              </div>
              <div class="media-actions">
                 <el-button v-if="item.type !== 'audio'" link type="primary" @click="previewMedia(item)">预览</el-button>
                 <!-- Audio has inline controls -->
                 <el-button link type="danger" @click="deleteAsset(item.id)">删除</el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Create Character Dialog -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建角色"
      width="500px"
      align-center
      class="custom-dialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
        status-icon
      >
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色定位" prop="role">
          <el-input v-model="createForm.role" placeholder="例如：主角、反派、配角" />
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-input v-model="createForm.tags" placeholder="使用逗号或空格分隔，如：赛博朋克 勇敢" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateCharacter(createFormRef)">
            立即创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Wiki Dialog -->
    <el-dialog
      v-model="wikiDialogVisible"
      :title="currentWikiAsset?.name + ' - 百科档案'"
      width="700px"
      align-center
      class="custom-dialog wiki-dialog"
    >
      <div v-if="currentWikiAsset" class="wiki-container">
          <div class="wiki-header">
              <div class="wiki-avatar-wrapper" v-if="currentWikiAsset.img">
                 <img :src="currentWikiAsset.img" class="wiki-avatar"/>
              </div>
              <div class="wiki-basic-info">
                  <h3>{{ currentWikiAsset.name }}</h3>
                  <p class="role-tag">{{ currentWikiAsset.role }}</p>
                  <div class="tags">
                      <span v-for="tag in currentWikiAsset.tags" :key="tag" class="tag">{{ tag }}</span>
                  </div>
              </div>
              <div class="wiki-actions">
                  <el-button type="primary" :loading="isGeneratingWiki" @click="generateWiki" :icon="MagicStick">
                      {{ currentWikiAsset.details ? '重新生成' : '生成百科词条' }}
                  </el-button>
              </div>
          </div>
          <el-divider />
          <div class="wiki-content markdown-body" v-html="marked.parse(wikiContent)" v-if="wikiContent"></div>
          <el-empty v-else description="暂无详细百科信息，请点击右上角生成" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.library-view {
  padding: 1rem 2rem;
  color: var(--text-color);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.search-input {
  width: 300px;
}

:deep(.search-input .el-input__wrapper) {
  background: var(--glass-bg);
  box-shadow: none;
  border: 1px solid var(--glass-border);
}

:deep(.search-input .el-input__inner) {
  color: var(--text-color);
}

:deep(.search-input .el-input__inner::placeholder) {
  color: var(--text-color);
  opacity: 0.6;
}

.library-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0; /* Remove padding here, move to grid or handle inside */
}

.glass-effect {
  /* Use CSS variables for theme adaptation */
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
}

.custom-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 1.5rem; /* Add padding here for content */
}

/* Graph Styles */
.graph-wrapper {
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
}
.chart-container {
    width: 100%;
    height: 600px; /* Fixed height or flex */
    min-height: 500px;
}
.graph-controls {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

/* Wiki Dialog Styles */
.wiki-container {
    color: var(--text-color);
}
.wiki-header {
    display: flex;
    gap: 20px;
    align-items: flex-start;
    margin-bottom: 20px;
}
.wiki-avatar {
    width: 100px;
    height: 100px;
    border-radius: 8px;
    object-fit: cover;
    border: 2px solid var(--primary-color);
}
.wiki-basic-info {
    flex: 1;
}
.wiki-basic-info h3 {
    margin: 0 0 5px 0;
    font-size: 1.5rem;
}
.role-tag {
    color: var(--primary-color);
    font-weight: bold;
    margin-bottom: 10px;
}
.wiki-content {
    line-height: 1.8;
    max-height: 500px;
    overflow-y: auto;
    padding-right: 10px;
}
/* Basic Markdown Styles for Wiki */
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
    margin-top: 1em;
    margin-bottom: 0.5em;
    color: var(--primary-color);
}
.markdown-body ul {
    padding-left: 20px;
}
.markdown-body strong {
    color: var(--text-color);
    font-weight: 700;
}

:deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto; /* Allow scrolling inside tabs */
  padding-right: 0.5rem; /* Space for scrollbar */
}

/* Custom Scrollbar for tab pane */
:deep(.el-tab-pane)::-webkit-scrollbar {
  width: 6px;
}
:deep(.el-tab-pane)::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}
:deep(.el-tab-pane)::-webkit-scrollbar-track {
  background: transparent;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

/* Custom Tabs */
:deep(.el-tabs__item) {
  color: var(--text-color);
  opacity: 0.7;
}
:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  opacity: 1;
}
:deep(.el-tabs__active-bar) {
  background-color: var(--primary-color);
}
:deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(255, 255, 255, 0.1);
}

/* Card Grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
  padding: 1rem 0;
}

.asset-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.3s;
  border: 1px solid transparent;
}

.asset-card:hover {
  transform: translateY(-5px);
  border-color: var(--primary-color);
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.card-image {
  height: 200px;
  position: relative;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.card-image:hover .hover-overlay {
  opacity: 1;
}

.card-info {
  padding: 1rem;
}

.card-info h4 {
  margin: 0;
  color: var(--text-color);
  font-size: 1.1rem;
}

.role {
  color: var(--primary-color);
  font-size: 0.9rem;
  margin: 0.5rem 0;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.8;
}

.add-card {
  border: 1px dashed rgba(255, 255, 255, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  min-height: 300px;
}

.add-card:hover {
  border-color: var(--primary-color);
  background: var(--accent-glow);
}

.add-content {
  text-align: center;
  color: var(--text-color);
  opacity: 0.6;
}

.plus {
  display: block;
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

/* Multimedia List */
.waterfall-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.media-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2) !important; /* Override glass-effect slightly */
  border: 1px solid transparent;
  border-radius: 8px;
  transition: all 0.3s;
}

.media-item:hover {
  border-color: var(--primary-color);
  background: rgba(0, 0, 0, 0.3) !important;
}

.media-icon {
  width: 50px;
  height: 50px;
  background: var(--accent-glow);
  color: var(--primary-color);
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.5rem;
  margin-right: 1rem;
}

.media-info {
  flex: 1;
}

.media-info h5 {
  margin: 0 0 0.5rem 0;
  color: var(--text-color);
}

.media-info p {
  margin: 0;
  font-size: 0.8rem;
  color: #888;
}

.media-actions {
  display: flex;
  gap: 0.5rem;
}
</style>
