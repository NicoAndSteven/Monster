<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { MagicStick, Fold, Expand, VideoPlay, Plus, Delete, Document, List, Download, ArrowDown, Picture, Headset, Edit, Check, Close, Refresh, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores/projectStore'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import { BubbleMenu } from '@tiptap/vue-3/menus'
import BubbleMenuExtension from '@tiptap/extension-bubble-menu'
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
const isAiEditing = ref(false)
const currentTask = ref<any>(null)

// Outline Editing Logic
const isEditingOutline = ref(false)
const outlineText = ref('')
const isGeneratingOutline = ref(false)

const startEditOutline = () => {
    outlineText.value = projectStore.currentProject?.outline || ''
    isEditingOutline.value = true
}

const cancelEditOutline = () => {
    outlineText.value = projectStore.currentProject?.outline || ''
    isEditingOutline.value = false
}

const saveOutline = async () => {
    if (!projectStore.currentProject) return
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/outline`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ outline: outlineText.value })
        })
        if (res.ok) {
            ElMessage.success('大纲更新成功')
            // Update store
            if (projectStore.currentProject) {
                projectStore.currentProject.outline = outlineText.value
            }
            isEditingOutline.value = false
        } else {
            ElMessage.error('更新失败')
        }
    } catch (e) {
        ElMessage.error('网络错误')
    }
}

const regenerateOutline = async () => {
    if (!projectStore.currentProject) return
    isGeneratingOutline.value = true
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/outline/generate`, {
            method: 'POST'
        })
        if (res.ok) {
            const data = await res.json()
            if (data.task_id) {
                ElMessage.info('大纲生成任务已提交，正在处理中...')
                await pollTask(data.task_id)
                ElMessage.success('大纲生成完成')
                
                // Refresh project to get new outline
                // Ideally we have a method to refresh current project
                // For now, let's just fetch it manually and update store
                 const novelRes = await fetch(`${API_BASE}/novels`)
                 if (novelRes.ok) {
                    const novels = await novelRes.json()
                    const updated = novels.find((n: any) => n.id === projectStore.currentProject?.id)
                    if (updated && projectStore.currentProject) {
                        projectStore.currentProject.outline = updated.outline
                    }
                 }
                 
                 // Refresh outline text if editing
                 if (isEditingOutline.value) {
                     outlineText.value = projectStore.currentProject?.outline || ''
                 }
            } else {
                 ElMessage.success('大纲生成任务已提交')
            }
        } else {
            ElMessage.error('请求失败')
        }
    } catch (e: any) {
        ElMessage.error(e.message || '网络错误')
    } finally {
        isGeneratingOutline.value = false
    }
}

// Tiptap Editor Setup
const editor = useEditor({
  content: '',
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: '开始创作...',
    }),
    BubbleMenuExtension.configure({
        pluginKey: 'bubbleMenu',
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

const handleAiEdit = async (instruction: string) => {
    if (!editor.value) return
    
    // Get selected text
    const { from, to } = editor.value.state.selection
    const selectedText = editor.value.state.doc.textBetween(from, to)
    
    if (!selectedText) {
        ElMessage.warning('请先选择要处理的文字')
        return
    }

    isAiEditing.value = true
    try {
        const res = await fetch(`${API_BASE}/ai/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: selectedText,
                instruction: instruction
            })
        })

        if (res.ok) {
            const data = await res.json()
            if (data.result) {
                // Replace selection with new text
                editor.value.commands.insertContent(data.result)
                ElMessage.success('AI 修改完成')
            }
        } else {
            ElMessage.error('请求失败')
        }
    } catch (e) {
        ElMessage.error('网络错误')
    } finally {
        isAiEditing.value = false
    }
}


// Image Generation
const imagePrompt = ref("请描述你想生成的图片内容")
const generatedImage = ref("https://placehold.co/512x512?text=AI+Generated+Image")
const isGeneratingImage = ref(false)
const chapterImages = ref<any[]>([])
const plotChoices = ref<string[]>([])
const showPlotChoiceDialog = ref(false)
const targetChapterNum = ref<number>(0)
const isFetchingChoices = ref(false)

// Audio
const isPlayingAudio = ref(false)
const audioUrl = ref('')
const audioPlayer = ref<HTMLAudioElement | null>(null)

// Lifecycle
onMounted(() => {
  if (projectStore.currentProject) {
    loadChapters(projectStore.currentProject.id)
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
  } else {
    chapters.value = []
    currentChapterId.value = null
    generatedText.value = ''
    chapterImages.value = []
    editor.value?.commands.setContent('')
  }
})

// Methods
const pollTask = async (taskId: string) => {
    while (true) {
        try {
            const res = await fetch(`${API_BASE}/tasks/${taskId}`)
            if (!res.ok) throw new Error("Failed to check status")
            const task = await res.json()
            
            if (task.status === 'completed') {
                return task.result
            }
            if (task.status === 'failed') {
                throw new Error(task.step || "Task failed")
            }
            
            // Wait 1s
            await new Promise(resolve => setTimeout(resolve, 1000))
        } catch (e) {
            throw e
        }
    }
}

const playChapterAudio = async () => {
    if (!editor.value) return
    const text = editor.value.getText()
    if (!text.trim()) {
        ElMessage.warning('章节内容为空')
        return
    }

    if (isPlayingAudio.value) {
        audioPlayer.value?.pause()
        isPlayingAudio.value = false
        return
    }

    ElMessage.info('正在合成并保存语音...')
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject!.id}/chapters/${currentChapterId.value}/generate-audio`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        })
        
        if (res.ok) {
            const data = await res.json()
            // Backend returns asset object with file_path relative to storage root (which is mounted as /data? No, wait)
            // The file_path in asset is "novels/{id}/audio/{filename}"
            // We mounted "data" directory to "/data" in backend
            // But wait, storage path is "d:\Monster\monster\data". 
            // So if asset.file_path is "novels/...", full path is "d:\Monster\monster\data\novels..."
            // So URL should be "http://localhost:8000/data/novels/..."
            
            audioUrl.value = `http://localhost:8000/data/${data.asset.file_path}`
            ElMessage.success('语音已保存至资产中心')
            
            // Wait for DOM update
            setTimeout(() => {
                if (audioPlayer.value) {
                    audioPlayer.value.play()
                    isPlayingAudio.value = true
                }
            }, 100)
        } else {
            ElMessage.error('语音合成失败')
        }
    } catch (e) {
        ElMessage.error('请求出错')
    }
}

const handleAudioEnded = () => {
    isPlayingAudio.value = false
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
      chapterImages.value = data.images || []
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
  ElMessage.info('正在生成 AI 绘图，请稍候...')
  
  try {
    const response = await fetch(`${API_BASE}/generate/image`, {
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

const saveToGallery = async () => {
    if (!projectStore.currentProject || !currentChapterId.value) return
    
    const newImage = {
        id: `img_${Date.now()}`,
        prompt: imagePrompt.value,
        url: generatedImage.value,
        segment_text: "用户手动生成"
    }
    
    // Add to local state
    chapterImages.value.push(newImage)
    
    // Update chapter with new images list
    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/chapters/${currentChapterId.value}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                images: chapterImages.value
            })
        })
        
        if (res.ok) {
            ElMessage.success('已保存到插图画廊')
        } else {
            ElMessage.error('保存失败')
        }
    } catch (e) {
        ElMessage.error('请求出错')
    }
}

const handleAIContinue = async () => {
  if (!projectStore.currentProject) return
  
  // Determine next chapter number
  const nextChapterNum = chapters.value.length + 1

  // 1. Fetch Plot Choices first
  isFetchingChoices.value = true
  ElMessage.info('正在构思剧情走向...')

  try {
    const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/plot-choices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        chapter_num: nextChapterNum,
        context_window: 2000 
      })
    })

    if (res.ok) {
      const data = await res.json()
      // Backend returns a list directly or an object with choices. Handle both.
      // Assuming backend returns list directly based on code inspection.
      // But keeping fallback to data.choices just in case.
      plotChoices.value = Array.isArray(data) ? data : (data.choices || [])
      
      targetChapterNum.value = nextChapterNum
      showPlotChoiceDialog.value = true
    } else {
      ElMessage.error('获取剧情选项失败')
    }
  } catch (e) {
    ElMessage.error('请求出错')
    console.error(e)
  } finally {
    isFetchingChoices.value = false
  }
}

const confirmGeneration = async (choice: string) => {
    showPlotChoiceDialog.value = false
    if (!projectStore.currentProject) return

    const nextChapterNum = targetChapterNum.value
    ElMessage.info(`正在根据选择生成第 ${nextChapterNum} 章...`)

    try {
        const res = await fetch(`${API_BASE}/novels/${projectStore.currentProject.id}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chapter_num: nextChapterNum,
                plot_choice: choice,
                mode: 'api'
            })
        })

        if (res.ok) {
            const data = await res.json()
            
            let content = ''
            if (data.task_id) {
                // Async polling
                const result = await pollTask(data.task_id, (task) => currentTask.value = task)
                currentTask.value = null
                content = result.content
            } else {
                // Fallback for sync
                content = data.chapter.content
            }
            
            await loadChapters(projectStore.currentProject.id)
            currentChapterId.value = nextChapterNum
            generatedText.value = content
            editor.value?.commands.setContent(content)
            ElMessage.success('生成成功')
        } else {
            ElMessage.error('生成失败')
        }
    } catch (e: any) {
        ElMessage.error(e.message || '请求出错')
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
                    <el-button size="small" :type="isPlayingAudio ? 'primary' : 'default'" @click="playChapterAudio" title="朗读章节">
                        <el-icon><Headset /></el-icon>
                    </el-button>
                </div>
              </div>
              <div class="editor-actions">
                <audio ref="audioPlayer" :src="audioUrl" @ended="handleAudioEnded" style="display: none;"></audio>
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
                            <el-dropdown-item command="epub">导出 EPUB (.epub)</el-dropdown-item>
                            <el-dropdown-item command="txt">导出 Text (.txt)</el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
              </div>
            </div>
            <div class="editor-scroll-area">
              <bubble-menu
                  v-if="editor"
                  :editor="editor"
                  :tippy-options="{ duration: 100 }"
                  class="ai-bubble-menu"
                >
                  <el-button-group>
                    <el-button size="small" type="primary" @click="handleAiEdit('请润色这段文字，使其更加生动细腻')">润色</el-button>
                    <el-button size="small" type="success" @click="handleAiEdit('请扩写这段文字，增加细节描写')">扩写</el-button>
                    <el-button size="small" type="warning" @click="handleAiEdit('请精简这段文字，保留核心信息')">精简</el-button>
                    <el-button size="small" type="info" @click="handleAiEdit('请修正这段文字中的错别字和语病')">纠错</el-button>
                  </el-button-group>
              </bubble-menu>
              <editor-content :editor="editor" class="tiptap-editor" />
            </div>
          </div>
        </div>

        <!-- Right: Preview & Assets -->
        <div class="preview-column">
          <el-tabs class="preview-tabs">
            <el-tab-pane label="大纲" name="outline">
                 <div class="outline-content-wrapper">
                    <div class="outline-actions" style="margin-bottom: 10px; display: flex; gap: 5px;">
                        <el-button v-if="!isEditingOutline" type="primary" size="small" @click="startEditOutline">
                            <el-icon><Edit /></el-icon> 编辑
                        </el-button>
                        <template v-else>
                            <el-button type="success" size="small" @click="saveOutline">
                                <el-icon><Check /></el-icon> 保存
                            </el-button>
                            <el-button type="info" size="small" @click="cancelEditOutline">
                                <el-icon><Close /></el-icon> 取消
                            </el-button>
                        </template>
                        <el-button type="warning" size="small" @click="regenerateOutline" :loading="isGeneratingOutline">
                            <el-icon><Refresh /></el-icon> 重生
                        </el-button>
                    </div>

                     <div v-if="projectStore.currentProject?.outline" class="outline-text-container">
                         <el-input
                            v-if="isEditingOutline"
                            v-model="outlineText"
                            type="textarea"
                            :rows="20"
                            placeholder="在此编辑大纲..."
                        />
                         <div v-else class="markdown-body" style="white-space: pre-wrap; line-height: 1.6; max-height: 60vh; overflow-y: auto;">
                             {{ projectStore.currentProject.outline }}
                         </div>
                     </div>
                     <div v-else class="no-outline">
                         <el-empty description="大纲生成中或未创建大纲" />
                         <p class="hint-text">大纲生成可能需要几秒钟，请稍候刷新页面。</p>
                     </div>
                 </div>
            </el-tab-pane>
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
                        <el-button type="success" size="small" :icon="Plus" @click="saveToGallery">
                        保存到画廊
                        </el-button>
                    </div>
                    </div>
                </div>
            </el-tab-pane>
            <el-tab-pane label="插图画廊" name="gallery">
                <div class="gallery-container">
                    <div class="gallery-grid" v-if="chapterImages.length > 0">
                        <div v-for="img in chapterImages" :key="img.id" class="gallery-item">
                             <div class="gallery-img-wrapper">
                                 <el-image 
                                    :src="img.url" 
                                    :preview-src-list="[img.url]"
                                    fit="cover"
                                    loading="lazy"
                                 >
                                    <template #error>
                                        <div class="image-slot">
                                            <el-icon><Picture /></el-icon>
                                        </div>
                                    </template>
                                 </el-image>
                             </div>
                             <div class="gallery-info">
                                 <p class="gallery-prompt" :title="img.prompt">{{ img.prompt }}</p>
                                 <p class="gallery-segment" :title="img.segment_text">对应文本: {{ img.segment_text }}</p>
                             </div>
                        </div>
                    </div>
                    <div v-else class="no-images">
                         <el-empty description="本章暂无插图">
                             <template #extra>
                                 <p class="hint-text">请在“实时绘图”中生成满意的图片并保存</p>
                             </template>
                         </el-empty>
                    </div>
                </div>
            </el-tab-pane>
          </el-tabs>
        </div>

      </div>
    </main>
    <!-- Plot Choice Dialog -->
    <el-dialog
      v-model="showPlotChoiceDialog"
      title="选择剧情走向"
      width="600px"
      align-center
      class="custom-dialog"
    >
      <div class="plot-choices" v-if="plotChoices.length > 0">
        <p class="choice-hint">AI 为您构思了以下三种发展方向，请选择一项：</p>
        <div 
          v-for="(choice, index) in plotChoices" 
          :key="index" 
          class="choice-card"
          @click="confirmGeneration(choice)"
        >
          <span class="choice-index">{{ index + 1 }}</span>
          <p class="choice-text">{{ choice }}</p>
        </div>
      </div>
      <div v-else class="empty-choices">
        <p>未获取到有效选项，请重试。</p>
      </div>
    </el-dialog>
    <!-- Task Progress Overlay -->
    <div v-if="currentTask" class="task-overlay">
      <div class="task-card glass-panel">
        <div class="task-header">
            <h3><el-icon class="is-loading mr-2"><Loading /></el-icon> {{ currentTask.description }}</h3>
        </div>
        
        <div class="task-body">
            <!-- Stage Stepper -->
            <div v-if="currentTask.stages && currentTask.stages.length > 0" class="task-stages">
                <el-steps :active="currentTask.current_stage_index" finish-status="success" align-center>
                    <el-step v-for="(stage, index) in currentTask.stages" :key="index" :title="stage" />
                </el-steps>
            </div>

            <!-- Progress Bar -->
            <div class="task-progress-bar">
                <el-progress 
                    :percentage="currentTask.progress" 
                    :status="currentTask.status === 'failed' ? 'exception' : (currentTask.status === 'completed' ? 'success' : '')"
                    :stroke-width="15"
                    striped
                    striped-flow
                    :duration="20"
                />
            </div>
            
            <!-- Console/Log View -->
            <div class="task-console-mini">
                <span class="console-prompt">></span>
                <span class="console-msg">{{ currentTask.step }}</span>
            </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Task Overlay */
.task-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(5px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.task-card {
    width: 600px;
    max-width: 90vw;
    background: #1a1a1a;
    border: 1px solid var(--primary-color);
    box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
    padding: 2rem;
    border-radius: 12px;
}

.task-header h3 {
    margin: 0 0 1.5rem 0;
    color: var(--primary-color);
    display: flex;
    align-items: center;
    gap: 10px;
}

.task-stages {
    margin-bottom: 2rem;
}

.task-progress-bar {
    margin-bottom: 1.5rem;
}

.task-console-mini {
    background: #000;
    padding: 1rem;
    border-radius: 4px;
    font-family: monospace;
    color: #ccc;
    display: flex;
    gap: 10px;
    align-items: center;
}

.console-prompt {
    color: var(--primary-color);
    font-weight: bold;
}

/* Plot Choice Styles */
.plot-choices {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.choice-hint {
  color: var(--text-color);
  opacity: 0.8;
  margin-bottom: 1rem;
}

.choice-card {
  background: transparent;
  border: 1px solid var(--glass-border);
  padding: 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  gap: 1rem;
  transition: all 0.2s;
}

.choice-card:hover {
  background: var(--accent-glow);
  border-color: var(--primary-color);
  transform: translateX(5px);
}

.choice-index {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color);
  opacity: 0.8;
}

.choice-text {
  margin: 0;
  color: var(--text-color);
  line-height: 1.5;
}

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

.no-chapters.no-assets {
    text-align: center;
    color: #888;
    margin-top: 2rem;
    font-size: 0.9rem;
}

.outline-content-wrapper {
    padding: 1rem;
    height: 100%;
    overflow-y: auto;
    color: var(--text-color);
}

.outline-text {
    white-space: pre-wrap;
    line-height: 1.6;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-color);
    opacity: 0.9;
    padding: 0.5rem;
}

.hint-text {
    text-align: center;
    color: #64748b;
    font-size: 0.85rem;
    margin-top: -10px;
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
/* Gallery Styles */
.gallery-container {
    padding: 1rem;
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.gallery-header {
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: center;
}

.gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1.5rem;
}

.gallery-item {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.2s;
}

.gallery-item:hover {
    transform: translateY(-5px);
}

.gallery-img-wrapper {
    width: 100%;
    height: 150px;
    background: #000;
}

.gallery-img-wrapper .el-image {
    width: 100%;
    height: 100%;
}

.gallery-info {
    padding: 10px;
}

.gallery-prompt {
    font-size: 0.8rem;
    color: #e2e8f0;
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.gallery-segment {
    font-size: 0.75rem;
    color: #94a3b8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: var(--glass-bg);
  color: #909399;
  font-size: 30px;
}

.generate-btn {
    width: 100%;
}
.ai-bubble-menu {
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 5px;
  border: 1px solid var(--glass-border);
  box-shadow: var(--card-hover-shadow);
  display: flex;
  gap: 5px;
}
</style>

<style>
/* Global overrides for Element Plus Dialog to match Theme */
.custom-dialog {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid var(--glass-border) !important;
  box-shadow: var(--card-hover-shadow) !important;
}

.custom-dialog .el-dialog__header {
  margin-right: 0;
  border-bottom: 1px solid var(--glass-border);
  padding-bottom: 20px;
}

.custom-dialog .el-dialog__title {
  color: var(--text-color) !important;
  font-weight: 600;
}

.custom-dialog .el-dialog__body {
  color: var(--text-color) !important;
  padding-top: 20px;
}

.custom-dialog .el-dialog__close {
  color: var(--text-color) !important;
  font-size: 1.2rem;
  opacity: 0.7;
}

.custom-dialog .el-dialog__close:hover {
  color: var(--primary-color) !important;
  opacity: 1;
}
</style>
