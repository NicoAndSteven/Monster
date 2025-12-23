import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Novel {
  id: string | number
  title: string
  description?: string
  cover?: string
  updated_at?: string
  outline?: string
  type?: string
}

export const useProjectStore = defineStore('project', () => {
  const currentProject = ref<Novel | null>(null)
  const projects = ref<Novel[]>([])
  
  // Persistence: Check localStorage on init
  const savedProjectId = localStorage.getItem('monster_active_project_id')
  
  const API_BASE = 'http://localhost:8000/api'

  const loadProjects = async () => {
    try {
      const res = await fetch(`${API_BASE}/novels`)
      if (res.ok) {
        projects.value = await res.json()
        
        // Restore session if exists
        if (savedProjectId && !currentProject.value) {
          const found = projects.value.find(p => String(p.id) === savedProjectId)
          if (found) {
            currentProject.value = found
          }
        }
      }
    } catch (e) {
      console.error("Failed to load projects", e)
    }
  }

  const selectProject = (project: Novel) => {
    currentProject.value = project
    localStorage.setItem('monster_active_project_id', String(project.id))
  }

  const clearProject = () => {
    currentProject.value = null
    localStorage.removeItem('monster_active_project_id')
  }

  const createProject = async (title: string, description: string, type?: string) => {
    const newId = Date.now().toString()
    try {
      const res = await fetch(`${API_BASE}/novels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: newId,
          title: title,
          description: description,
          type: type
        })
      })
      
      if (res.ok) {
        const data = await res.json()
        projects.value.push(data.novel)
        selectProject(data.novel)
        return data.novel
      }
    } catch (e) {
      console.error("Failed to create project", e)
      throw e
    }
  }
  
  const deleteProject = async (id: string | number) => {
    try {
      const res = await fetch(`${API_BASE}/novels/${id}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        projects.value = projects.value.filter(p => p.id !== id)
        if (currentProject.value?.id === id) {
          clearProject()
        }
        return true
      }
    } catch (e) {
      console.error("Failed to delete project", e)
      return false
    }
    return false
  }

  return {
    currentProject,
    projects,
    loadProjects,
    selectProject,
    clearProject,
    createProject,
    deleteProject
  }
})
