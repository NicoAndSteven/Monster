import { createRouter, createWebHistory } from 'vue-router'
import OverviewView from '../views/OverviewView.vue'
import WorkbenchView from '../views/WorkbenchView.vue'
import LibraryView from '../views/LibraryView.vue'
import ProjectSelectionView from '../views/ProjectSelectionView.vue'
import { useProjectStore } from '../stores/projectStore'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: ProjectSelectionView
    },
    {
      path: '/overview',
      name: 'overview',
      component: OverviewView,
      meta: { requiresProject: true }
    },
    {
      path: '/workbench',
      name: 'workbench',
      component: WorkbenchView,
      meta: { requiresProject: true }
    },
    {
      path: '/library',
      name: 'library',
      component: LibraryView,
      meta: { requiresProject: true }
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  const projectStore = useProjectStore()
  
  // Wait for initial load if refreshing page
  if (!projectStore.projects.length && localStorage.getItem('monster_active_project_id')) {
    await projectStore.loadProjects()
  }

  if (to.meta.requiresProject && !projectStore.currentProject) {
    next('/')
  } else {
    next()
  }
})

export default router
