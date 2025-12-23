<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projectStore'
import { Plus, Delete, Document , ArrowRight, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(true)
const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const currentPage = ref(0)
const itemsPerPage = 3

const createForm = reactive({
  title: '',
  description: '',
  type: ''
})

const createRules = reactive<FormRules>({
  title: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度 in 1 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请输入小说类型', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入项目描述', trigger: 'blur' }
  ]
})

onMounted(async () => {
  loading.value = true
  await projectStore.loadProjects()
  loading.value = false
})

const getProjectCover = (id: number | string) => {
  const gradients = [
    'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
    'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
    'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)',
    'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
    'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)'
  ]
  const index = typeof id === 'number' ? id % gradients.length : 0
  return gradients[index]
}

const handleSelectProject = (project: any) => {
  projectStore.selectProject(project)
  ElMessage.success({
    message: `已进入项目: ${project.title}`,
    duration: 1000
  })
  router.push('/overview')
}

const openCreateDialog = () => {
  createForm.title = ''
  createForm.description = ''
  createForm.type = ''
  createDialogVisible.value = true
}

const handleCreateProject = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        await projectStore.createProject(createForm.title, createForm.description, createForm.type)
        ElMessage.success('项目创建成功')
        createDialogVisible.value = false
        // Reset to last page to see new project if needed, or stay
        router.push('/overview')
      } catch (e) {
        ElMessage.error('创建失败，请检查后端服务')
        console.error(e)
      }
    }
  })
}

const handleDeleteProject = (id: string | number, event: Event) => {
  event.stopPropagation()
  ElMessageBox.confirm(
    '确定要删除该项目吗？此操作将永久删除所有相关章节和资产。',
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      const success = await projectStore.deleteProject(id)
      if (success) {
        ElMessage.success('项目已删除')
        // Adjust current page if empty
        if (currentPage.value > 0 && paginatedItems.value.length === 0) {
            currentPage.value--
        }
      } else {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {})
}

// Pagination Logic
const totalPages = computed(() => Math.ceil((projectStore.projects.length + 1) / itemsPerPage)) // +1 for create card

const paginatedItems = computed(() => {
  // Combine Create Card (virtual) + Projects
  // We handle Create Card rendering separately in template for better control, 
  // but let's treat indices 0 as Create Card.
  // Actually, user wants "show two projects", maybe create card is always visible or part of the grid?
  // Let's assume the grid shows 3 items total (Create + 2 Projects) or just 2 slots?
  // User said: "只展示两个作品，可以使用向右箭头的按钮切换展示更多的作品"
  // Let's interpret as: A horizontal list where only 2 items are visible at a time.
  // Item 0 is always "Create New". Then Project 1, Project 2...
  
  // Strategy: 
  // Page 0: Create Card, Project 1
  // Page 1: Project 2, Project 3
  // ...
  
  const allItems = ['create-card', ...projectStore.projects]
  const start = currentPage.value * itemsPerPage
  return allItems.slice(start, start + itemsPerPage)
})

const nextPage = () => {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++
  }
}

const prevPage = () => {
  if (currentPage.value > 0) {
    currentPage.value--
  }
}
</script>

<template>
  <div class="project-selection-container">
    <div class="background-animation"></div>
    
    <div class="content-wrapper animate__animated animate__fadeIn">
      <div class="header">
        <h1 class="logo">Monster AI</h1>
        <p class="subtitle">专业的网文创作辅助系统</p>
      </div>

      <div class="project-panel glass-panel">
        <div class="panel-header">
          <h2>我的项目</h2>
          <div class="pagination-controls" v-if="totalPages > 1">
            <el-button circle :icon="ArrowLeft" :disabled="currentPage === 0" @click="prevPage" />
            <span class="pagination-label">切换</span>
            <el-button circle :icon="ArrowRight" :disabled="currentPage >= totalPages - 1" @click="nextPage" />
          </div>
        </div>
        
        <div class="project-grid-wrapper" v-loading="loading">
            <div class="project-grid">
              <template v-for="item in paginatedItems" :key="typeof item === 'string' ? 'create' : item.id">
                
                <!-- Create New Card -->
                <div v-if="typeof item === 'string'" class="project-card create-card" @click="openCreateDialog">
                    <div class="create-content">
                    <div class="create-icon-wrapper">
                        <el-icon><Plus /></el-icon>
                    </div>
                    <h3>创建新作品</h3>
                    <p>开始一个新的创作项目</p>
                    </div>
                </div>

                <!-- Project Cards -->
                <div 
                    v-else
                    class="project-card"
                    @click="handleSelectProject(item)"
                >
                    <!-- Cover Image Area -->
                    <div class="card-cover" :style="{ background: getProjectCover(item.id) }">
                    <div class="cover-overlay"></div>
                    <div class="card-icon">
                        <el-icon><Document /></el-icon>
                    </div>
                    </div>

                    <!-- Content Area -->
                    <div class="card-content">
                    <h3 class="project-title" :title="item.title">{{ item.title }}</h3>
                    <p class="project-desc">{{ item.description || '暂无描述' }}</p>
                    
                    <div class="card-footer">
                        <span class="project-id">ID: {{ item.id }}</span>
                        <!-- Stop propagation moved to handler, but button needs high z-index -->
                        <el-button 
                        type="danger" 
                        circle
                        :icon="Delete" 
                        @click.stop="handleDeleteProject(item.id, $event)" 
                        class="delete-btn-visible"
                        />
                    </div>
                    </div>

                </div>
              </template>
            </div>
        </div>
      </div>
    </div>

    <!-- Create Project Dialog -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建新项目"
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
        <el-form-item label="项目名称" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="小说类型" prop="type">
          <el-input v-model="createForm.type" placeholder="请输入小说类型，如：赛博朋克、古言、克苏鲁" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入项目简要描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateProject(createFormRef)">
            立即创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.project-selection-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0f172a;
  color: #fff;
  position: relative;
  overflow: hidden;
}

.background-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 50% 50%, rgba(76, 29, 149, 0.2), transparent 70%);
  z-index: 0;
}

.content-wrapper {
  z-index: 1;
  width: 100%;
  max-width: 1200px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.header {
  text-align: center;
}

.logo {
  font-size: 4rem;
  margin: 0;
  background: linear-gradient(to right, #fff, #a5b4fc);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  letter-spacing: -2px;
}

.subtitle {
  font-size: 1.2rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

.glass-panel {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.pagination-label {
  color: #94a3b8;
  font-size: 0.9rem;
  font-weight: 500;
}

.project-grid-wrapper {
  min-height: 320px; /* Match card height to prevent jumping */
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 2 items + potentially create card, or just fixed slots */
  /* Actually, user wants 2 items visible. But we need to handle layout.
     If we show 2 items, we should use 1fr 1fr. 
     Wait, user said "只展示两个作品". This implies a viewport of 2 items.
  */
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

/* Base Card Styles */
.project-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 320px;
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.2);
  cursor: pointer;
}

/* Cover Image Area */
.card-cover {
  height: 140px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.2);
}

.card-icon {
  position: relative;
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(4px);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: #fff;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Content Area */
.card-content {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.project-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-desc {
  margin: 0;
  color: #94a3b8;
  font-size: 0.875rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.card-footer {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 20; /* Ensure footer is above hover overlay */
}

.project-id {
  font-size: 0.75rem;
  color: #64748b;
  font-family: monospace;
}

.delete-btn-visible {
  /* position: relative; removed as parent has z-index now */
  /* z-index: 20; removed */
  opacity: 1;
  pointer-events: auto;
}

/* Create Card Specifics */
.create-card {
  border-style: dashed;
  border-width: 2px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
}

.create-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: #818cf8;
}

.create-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
}

.create-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(129, 140, 248, 0.1);
  color: #818cf8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
}

.create-card:hover .create-icon-wrapper {
  transform: scale(1.1) rotate(90deg);
  background: #818cf8;
  color: #fff;
}

.create-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  color: #fff;
}

.create-content p {
  margin: 0;
  color: #94a3b8;
  font-size: 0.875rem;
}

/* Hover Actions Overlay - REMOVED */

/* Fix: Make sure delete button is clickable even when overlay is active 
   Actually, if overlay covers everything, delete button (z-index 20) should be above it.
   But overlay has z-index 10.
   Let's check card structure. 
   Card
     Cover
     Content
       Footer
         DeleteBtn (z-index 20)
     Overlay (z-index 10)
   
   If overlay covers the whole card (top:0, left:0, w:100%, h:100%), then it covers Content too.
   If DeleteBtn has z-index 20, it should be on top of Overlay (z-index 10).
   However, DeleteBtn is inside Content. Content is a sibling of Overlay?
   
   Structure:
   .project-card (relative)
     .card-cover
     .card-content
       ...
       .delete-btn-visible (z-index 20)
     .card-hover-actions (absolute, z-index 10)
     
   Since .card-content is static by default, z-index might not work unless positioned.
   We need to make .card-content relative or z-index effective.
*/

.card-content {
  position: relative; 
  z-index: 15; /* Above overlay? If overlay is 10, content is 15.
                 But wait, if content is 15, then overlay (10) is BEHIND content.
                 Then overlay won't dim the content.
                 We want overlay to be ON TOP of content, but DeleteBtn ON TOP of overlay.
                 
                 So:
                 Content: z-index 5 (default)
                 Overlay: z-index 10
                 DeleteBtn: z-index 20 (must be positioned)
  */
}

/* Let's reset card-content z-index logic */
.card-content {
  position: relative;
  z-index: 5;
}

.card-hover-actions {
  z-index: 10;
}

.delete-btn-visible {
  position: relative;
  z-index: 20;
}

/* Enter button in overlay */
.enter-btn {
  transform: translateY(20px);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 99px;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
}

.project-card:hover .enter-btn {
  transform: translateY(0);
}

/* Custom Dialog */
.custom-dialog :deep(.el-dialog) {
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.custom-dialog :deep(.el-dialog__title) {
  color: #fff;
}

.custom-dialog :deep(.el-form-item__label) {
  color: #94a3b8;
}

.custom-dialog :deep(.el-input__wrapper),
.custom-dialog :deep(.el-textarea__inner) {
  background-color: #0f172a;
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
}

.custom-dialog :deep(.el-input__wrapper:hover),
.custom-dialog :deep(.el-textarea__inner:hover) {
  border-color: rgba(255, 255, 255, 0.2);
}

.custom-dialog :deep(.el-input__wrapper.is-focus),
.custom-dialog :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
}


/* Content Area */
.card-content {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e293b;
}

.project-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-desc {
  margin: 0;
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.5;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.card-footer {
  margin-top: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 1rem;
}

.project-id {
  font-size: 0.75rem;
  color: #64748b;
  font-family: monospace;
}

.delete-btn {
  padding: 4px;
  font-size: 1.1rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.delete-btn:hover {
  opacity: 1;
}

/* Create Card Styles */
.create-card {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.create-card:hover {
  border-color: #818cf8;
  background: rgba(99, 102, 241, 0.05);
}

.create-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #94a3b8;
  transition: color 0.3s;
}

.create-card:hover .create-content {
  color: #818cf8;
}

.create-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  transition: all 0.3s;
}

.create-card:hover .create-icon-wrapper {
  background: rgba(99, 102, 241, 0.2);
  transform: scale(1.1);
}

.create-text {
  font-weight: 600;
  font-size: 1.1rem;
}

/* Hover Actions Overlay */
.card-hover-actions {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none; /* Let clicks pass through initially */
}

.project-card:hover .card-hover-actions {
  opacity: 1;
  pointer-events: auto;
}

.enter-btn {
  transform: translateY(20px);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 12px 24px;
  font-size: 1.1rem;
  border-radius: 99px;
  font-weight: 600;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.project-card:hover .enter-btn {
  transform: translateY(0);
}
</style>
