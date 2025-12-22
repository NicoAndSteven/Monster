<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { MagicStick, Fold, Expand, VideoPlay, Plus, Delete, Document, List, Download, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores/projectStore'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const API_BASE = 'http://localhost:8000/api'
const projectStore = useProjectStore()

// Data
const isSidebarVisible = ref(true)
const chapters = ref<any[]>([])
const currentChapterId = ref<number | null>(null)
const generatedText = ref('')
const isSaving = ref(false)
const projectAssets = ref<any[]>([])

// Tiptap Editor Setup
const editor = useEditor({
  content: '',
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: '开始创作...',
    }),
  ],
  onUpdate: ({ editor }) => {
    generatedText.value = editor.getHTML()
  },
  editorProps: {
    attributes: {
      class: 'seamless-textarea',
    },
  },
})

// Image Generation
const imagePrompt = ref("请描述你想生成的图片内容")
const generatedImage = ref("https://via.placeholder.com/512x512.png?text=AI+Generated+Image")
const isGeneratingImage = ref(false)

// Lifecycle
onMounted(() => {
  if (projectStore.currentProject) {
    loadChapters(projectStore.currentProject.id)
    loadAssets(projectStore.currentProject.id)
  }
})

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy()
  }
})

// Watch for project change (rare but possible if store resets)
watch(() => projectStore.currentProject, (newVal) => {
  if (newVal) {
    loadChapters(newVal.id)
    loadAssets(newVal.id)
  } else {
    chapters.value = []
    currentChapterId.value = null
    generatedText.value = ''
    projectAssets.value = []
    editor.value?.commands.setContent('')
  }
})

// Methods
const loadAssets = async (novelId: string | number) => {
  try {
    const res = await fetch(`${API_BASE}/novels/${novelId}/assets`)
    if (res.ok) {
      projectAssets.value = await res.json()
    }
  } catch (e) {
    console.error("Failed to load assets", e)
  }
}

const loadChapters = async (novelId: string | number) => {
  try {
    const res = await fetch(`${API_BASE}/novels/${novelId}/chapters`)
    if (res.ok) {
      chapters.value = await res.json()
      if (chapters.value.length > 0) {
        // Select first chapter by default if none selected
        if (!currentChapterId.value) {
          currentChapterId.value = chapters.value[0].id
        } else {
            // Verify current chapter still exists
            const exists = chapters.value.find(c => c.id === currentChapterId.value)
            if (!exists) currentChapterId.value = chapters.value[0].id
        }
        await loadChapterContent(novelId, currentChapterId.value!)
      } else {
        currentChapterId.value = null
        generatedText.value = ''
      }
    }
  } catch (e) {
    ElMessage.error("加载章节失败")
  }
}

const selectChapter = async (chapterId: number) => {
  currentChapterId.value = chapterId
  // Content loading handled by watcher or explicit call? 
  // Let's use explicit call to be safe and avoid double triggers if watcher is tricky
  if (projectStore.currentProject) {
    await loadChapterContent(projectStore.currentProject.id, chapterId)
  }
}

const loadChapterContent = async (novelId: string | number, chapterId: number) => {
  try {
    const res = await fetch(`${API_BASE}/novels/${novelId}/chapters/${chapterId}`)
    if (res.ok) {
      const data = await res.json()
      generatedText.value = data.content || ''
      editor.value?.commands.setContent(data.content || '')
    }
  } catch (e) {
    console.error("Failed to load content", e)
  }
}

// Watch for chapter change to load content (optional if we use selectChapter)
// But currentChapterId might change from other sources (AI generation)
watch(currentChapterId, async (newVal) => {
  if (newVal && projectStore.currentProject) {
     await loadChapterContent(projectStore.currentProject.id, newVal)
  }
})

// Auto-save text
let saveTimer: any = null
watch(generatedText, (newVal) => {
  if (!projectStore.currentProject || !currentChapterId.value) return
  
  if (saveTimer) clearTimeout(saveTimer)
  isSaving.value = true
  
  saveTimer = setTimeout(async () => {
    try {
      await fetch(`${API_BASE}/novels/${projectStore.currentProject!.id}/chapters/${currentChapterId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newVal })
      })
      isSaving.value = false
    } catch (e) {
      console.error("Auto-save failed", e)
      isSaving.value = false
    }
  }, 1000) // 1s debounce
})

const toggleSidebar = () => {
  isSidebarVisible.value = !isSidebarVisible.value
}

const regenerateImage = async () => {
  if (!imagePrompt.value) {
    ElMessage.warning('请输入提示词')
    return
  }
  
  isGeneratingImage.value = true
  ElMessage.info('正在启动 RPA 绘图，请留意弹出的浏览器窗口...')
  
  try {
    const response = await fetch(`${API_BASE}/generate/image/rpa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: imagePrompt.value }),
    })
    
    const data = await response.json()
    
    if (response.ok && data.image_url) {
      generatedImage.value = data.image_url
      ElMessage.success('插图已重新生成')
    } else {
       ElMessage.error(data.detail || data.error || '生成失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('生成出错，请确保后台服务已运行')
  } finally {
    isGeneratingImage.value = false
  }
}


const handleAIContinue = async () => {
  if (!projectStore.currentProject) return
  
  // Determine next chapter number
  const nextChapterNum = chapters.value.length + 1
  
  ElMessage.info(`正在生成第 ${nextChapterNum} 章...`)
  
  try {
    const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chapter_num: nextChapterNum,
        prompt: `Chapter ${nextChapterNum}`, // Use prompt if available
        mode: 'api' // or 'rpa' if supported
      })
    })
    
    if (res.ok) {
      const data = await res.json()
      // Refresh chapters
      await loadChapters(projectStore.currentProject.id)
      
      // Switch to new chapter
      currentChapterId.value = nextChapterNum
      generatedText.value = data.chapter.content
      editor.value?.commands.setContent(data.chapter.content)
      ElMessage.success('生成成功')
    } else {
      ElMessage.error('生成失败')
    }
  } catch (e) {
    ElMessage.error('请求出错')
  }
}

const handleCreateChapter = async () => {
  if (!projectStore.currentProject) return

  // Find the maximum chapter ID to avoid conflicts when deleting/adding
  // Assuming chapter.id corresponds to chapter_num in current implementation
  const maxId = chapters.value.length > 0 
    ? Math.max(...chapters.value.map(c => c.id)) 
    : 0
  const nextChapterNum = maxId + 1
  
  try {
    await ElMessageBox.confirm(
      `确定要创建第 ${nextChapterNum} 章吗？`,
      '创建章节',
      {
        confirmButtonText: '创建',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/chapters/${nextChapterNum}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: ''
      })
    })
    
    if (res.ok) {
      ElMessage.success(`第 ${nextChapterNum} 章创建成功`)
      await loadChapters(projectStore.currentProject.id)
      currentChapterId.value = nextChapterNum
      generatedText.value = ''
      editor.value?.commands.setContent('')
    } else {
      ElMessage.error('创建失败')
    }
  } catch (e) {
    if (e !== 'cancel') {
        ElMessage.error('请求出错')
    }
  }
}

const handleExport = async (format: string = 'docx') => {
  if (!projectStore.currentProject) return
  
  // Handle command event from dropdown which might pass an object if not careful, 
  // but @command passes the command value directly.
  // If clicked directly (not dropdown), default to docx.
  const exportFormat = typeof format === 'string' ? format : 'docx'

  try {
    const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/export?format=${exportFormat}`)
    if (res.ok) {
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${projectStore.currentProject.title}.${exportFormat}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('导出成功')
    } else {
      ElMessage.error('导出失败')
    }
  } catch (e) {
    ElMessage.error('请求出错')
  }
}

const handleDeleteChapter = async (chapterId: number, event: Event) => {
  event.stopPropagation()
  if (!projectStore.currentProject) return

  ElMessageBox.confirm(
    '确定要删除该章节吗？此操作无法撤销。',
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject!.id}/chapters/${chapterId}`, {
          method: 'DELETE'
        })
        
        if (res.ok) {
          ElMessage.success('章节已删除')
          // Reload chapters
          await loadChapters(projectStore.currentProject!.id)
        } else {
          ElMessage.error('删除失败')
        }
      } catch (e) {
        ElMessage.error('请求出错')
      }
    })
    .catch(() => {})
}

</script>

<template>
  <div class="workbench-container animate__animated animate__fadeIn">
    
    <!-- Sidebar: Chapter List (Changed from Novel List) -->
    <aside class="sidebar glass-panel" :class="{ 'sidebar-hidden': !isSidebarVisible }">
      <div class="sidebar-header">
        <h3>章节列表</h3>
        <el-button link :icon="Plus" @click="handleCreateChapter" title="新建章节" />
      </div>
      <div class="chapter-list">
        <div v-if="chapters.length === 0" class="no-chapters">
            暂无章节
        </div>
        <div 
          v-for="chapter in chapters" 
          :key="chapter.id" 
          class="chapter-item"
          :class="{ active: currentChapterId === chapter.id }"
          @click="selectChapter(chapter.id)"
        >
          <div class="chapter-icon"><el-icon><Document /></el-icon></div>
          <div class="chapter-info">
            <span class="chapter-title">{{ chapter.title }}</span>
          </div>
          <el-button 
            link 
            type="danger" 
            :icon="Delete" 
            class="delete-chapter-btn"
            @click="handleDeleteChapter(chapter.id, $event)"
          />
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="main-stage">
      <div class="workspace-layout glass-panel" :class="{ 'full-mode': !isSidebarVisible }">
        
        <!-- Center: Editor -->
        <div class="editor-column">
          <div class="editor-content">
            <div class="editor-header">
              <div class="header-left" style="display: flex; align-items: center; gap: 10px;">
                <el-button v-if="!isSidebarVisible" link @click="toggleSidebar" title="展开列表">
                  <el-icon><Expand /></el-icon>
                </el-button>
                <el-button v-else link @click="toggleSidebar" title="收起列表">
                  <el-icon><Fold /></el-icon>
                </el-button>
                <span class="novel-name" v-if="currentChapterId">
                    {{ chapters.find(c => c.id === currentChapterId)?.title }}
                </span>
                <!-- Toolbar -->
                <div class="editor-toolbar" v-if="editor">
                    <el-button size="small" :class="{ 'is-active': editor.isActive('bold') }" @click="editor.chain().focus().toggleBold().run()">
                        <b>B</b>
                    </el-button>
                    <el-button size="small" :class="{ 'is-active': editor.isActive('italic') }" @click="editor.chain().focus().toggleItalic().run()">
                        <i>I</i>
                    </el-button>
                    <el-button size="small" :class="{ 'is-active': editor.isActive('bulletList') }" @click="editor.chain().focus().toggleBulletList().run()">
                        <el-icon><List /></el-icon>
                    </el-button>
                </div>
              </div>
              <div class="editor-actions">
                <el-button type="primary" link @click="handleAIContinue">
                  <el-icon class="mr-1"><MagicStick /></el-icon> AI 创作
                </el-button>
                <el-dropdown @command="handleExport">
                    <el-button type="success" link>
                        <el-icon class="mr-1"><Download /></el-icon> 导出 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                        <el-dropdown-menu>
                            <el-dropdown-item command="docx">导出 Word (.docx)</el-dropdown-item>
                            <el-dropdown-item command="txt">导出 Text (.txt)</el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
              </div>
            </div>
            <div class="editor-scroll-area">
              <editor-content :editor="editor" class="tiptap-editor" />
            </div>
          </div>
        </div>

        <!-- Right: Preview & Assets -->
        <div class="preview-column">
          <el-tabs class="preview-tabs">
            <el-tab-pane label="实时绘图" name="image">
                <div class="preview-content">
                    <div class="image-box" v-loading="isGeneratingImage">
                    <img :src="generatedImage" class="preview-img" />
                    </div>
                    <div class="prompt-box">
                    <label>Prompt:</label>
                    <textarea v-model="imagePrompt" rows="3"></textarea>
                    <div class="prompt-actions">
                        <el-button type="primary" size="small" :icon="VideoPlay" :loading="isGeneratingImage" @click="regenerateImage">
                        生成
                        </el-button>
                    </div>
                    </div>
                </div>
            </el-tab-pane>
            <el-tab-pane label="资产参考" name="assets">
                <div class="assets-list">
                    <div v-for="asset in projectAssets" :key="asset.id" class="asset-card">
                        <div class="asset-header">
                            <span class="asset-type">{{ asset.type === 'character' ? '角色' : '场景' }}</span>
                            <span class="asset-name">{{ asset.name }}</span>
                        </div>
                        <div class="asset-role">{{ asset.role }}</div>
                        <div class="asset-tags">
                            <el-tag size="small" v-for="tag in asset.tags" :key="tag" class="mr-1">{{ tag }}</el-tag>
                        </div>
                    </div>
                     <div v-if="projectAssets.length === 0" class="no-assets">
                        暂无资产，请去资产中心添加
                    </div>
                </div>
            </el-tab-pane>
          </el-tabs>
        </div>

      </div>
    </main>
  </div>
</template>

<style scoped>
.workbench-container {
  display: flex;
  height: 100%; /* Fill remaining height from main */
  overflow: hidden;
  color: var(--text-color);
}

/* Glass Panel Utility */
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
}

/* Sidebar */
.sidebar {
  width: 260px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--glass-border);
  flex-shrink: 0;
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
}

.sidebar.sidebar-hidden {
  width: 0;
  padding: 0;
  border-right: none;
  opacity: 0;
  pointer-events: none;
}

.sidebar-header {
  padding: 1.5rem;
  margin-top: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--primary-color);
}

.chapter-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.no-chapters {
    text-align: center;
    color: #888;
    margin-top: 2rem;
    font-size: 0.9rem;
}

.chapter-item {
  display: flex;
  align-items: center;
  padding: 0.8rem;
  margin-bottom: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.chapter-item:hover {
  background: rgba(255,255,255,0.05);
}

.chapter-item:hover .delete-chapter-btn {
  opacity: 1;
}

.delete-chapter-btn {
  opacity: 0;
  transition: opacity 0.2s;
  padding: 4px;
}

.chapter-item.active {
  background: var(--accent-glow);
  border-color: var(--primary-color);
}

.chapter-icon {
  width: 28px;
  height: 28px;
  background: rgba(255,255,255,0.1);
  border-radius: 6px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 0.8rem;
  color: var(--primary-color);
  font-size: 0.9rem;
}

.chapter-info {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 1rem;
}

.chapter-title {
  font-size: 0.9rem;
  font-weight: 500;
}

/* Main Stage */
.main-stage {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  opacity: 0.5;
}

.logo-large {
  font-size: 3rem;
  font-weight: bold;
  color: var(--primary-color);
  margin-bottom: 1rem;
  letter-spacing: 2px;
}

/* Workspace Layout */
.workspace-layout {
  display: flex;
  width: 100%;
  height: 100%;
  padding: 0; /* Remove internal padding to let columns fill */
  gap: 0; /* Remove gap */
  max-width: 1600px;
  overflow: hidden; /* Ensure rounded corners clip content */
}

.editor-column {
  flex: 6; /* 60% */
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--glass-border); /* Separator */
}

.preview-column {
  flex: 4; /* 40% */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-header {
  padding: 1rem 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.novel-name {
  font-weight: 600;
  color: var(--text-color);
  font-size: 1.1rem;
  margin-right: 0.5rem;
  white-space: nowrap;
}

.divider {
  color: var(--glass-border);
  margin-right: 0.5rem;
  font-weight: 300;
}

.chapter-selector {
  width: 160px;
}

:deep(.chapter-selector .el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0;
}

:deep(.chapter-selector .el-input__inner) {
  color: var(--primary-color);
  font-weight: bold;
  font-size: 1.1rem;
  cursor: pointer;
  padding-left: 0;
}

:deep(.chapter-selector .el-select__caret) {
  color: var(--primary-color);
  font-weight: bold;
}

/* Hover effect for selector */
:deep(.chapter-selector:hover .el-input__inner) {
  opacity: 0.8;
}

.editor-scroll-area {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
}

.editor-scroll-area::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.editor-toolbar {
  display: flex;
  gap: 0.5rem;
  margin-left: 1rem;
  border-left: 1px solid rgba(255,255,255,0.1);
  padding-left: 1rem;
}

.editor-toolbar .el-button.is-active {
  background: var(--primary-color);
  color: #fff;
}

:deep(.tiptap-editor) {
  height: 100%;
  outline: none;
}

:deep(.ProseMirror) {
  height: 100%;
  outline: none;
  font-family: 'Georgia', serif;
  font-size: 1.1rem;
  line-height: 1.8;
  color: var(--text-color);
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

.preview-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__nav-scroll) {
  display: flex;
  justify-content: center;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(255,255,255,0.1);
}

:deep(.el-tabs__item) {
  color: #888;
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
}

.assets-list {
  padding: 1rem 0;
}

.asset-card {
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
}

.asset-card:hover {
  border-color: rgba(255,255,255,0.1);
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.asset-type {
  font-size: 0.75rem;
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.asset-name {
  font-weight: 600;
  color: #fff;
}

.asset-role {
  font-size: 0.9rem;
  color: #ccc;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.no-assets {
    text-align: center;
    color: #888;
    margin-top: 2rem;
}

.preview-column::-webkit-scrollbar {
  display: none;
}

/* Hide scrollbars for novel list too */
.novel-list::-webkit-scrollbar {
  display: none;
}
.novel-list {
  scrollbar-width: none;
}

/* Full Mode Layout */
.workspace-layout.full-mode .editor-column {
  flex: 6; /* Keep ratio or change? keeping ratio as per request "split in 6:4" */
}

.workspace-layout.full-mode .preview-column {
  flex: 4;
}

.preview-header {
  margin-bottom: 1rem;
  font-weight: 600;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.image-box {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: #000;
  margin-bottom: 1rem;
  border: 1px solid rgba(255,255,255,0.1);
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hover-actions {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-box:hover .hover-actions {
  opacity: 1;
}

.prompt-box label {
  display: block;
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.prompt-box textarea {
  width: 100%;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(255,255,255,0.1);
  color: #ccc;
  border-radius: 6px;
  padding: 0.5rem;
  resize: vertical;
  font-size: 0.9rem;
}

.prompt-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.mr-1 {
  margin-right: 4px;
}
</style>
