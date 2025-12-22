<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useTheme, type Theme } from './composables/useTheme'
import { Moon, Sunny, Lightning, Sugar, GoldMedal, Brush, Back } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/projectStore'
import { computed } from 'vue'

const { currentTheme, applyTheme } = useTheme()
const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const isProjectView = computed(() => {
  return route.name !== 'home'
})

const exitProject = () => {
  projectStore.clearProject()
  router.push('/')
}

const themeIcons: Record<Theme, any> = {
  'deep-space': Moon,
  'cyberpunk': Lightning,
  'chatgpt-white': Sunny,
  'fresh-green': Sugar,
  'black-gold': GoldMedal,
  'red-black': Brush
}
</script>

<template>
  <div class="app-container">
    <header class="glass-header" v-if="isProjectView">
      <div class="header-left">
        <el-button 
          link 
          class="back-btn" 
          @click="exitProject"
          :icon="Back"
        >
          返回项目列表
        </el-button>
        <div class="separator">|</div>
        <div class="logo">
          Monster AI 
          <span class="project-title" v-if="projectStore.currentProject">
            / {{ projectStore.currentProject.title }}
          </span>
        </div>
      </div>
      <nav>
        <RouterLink to="/overview">数据看板</RouterLink>
        <RouterLink to="/workbench">工作台</RouterLink>
        <RouterLink to="/library">资产中心</RouterLink>
      </nav>
      <div class="theme-switcher">
        <el-dropdown trigger="click" @command="applyTheme">
          <span class="el-dropdown-link">
            <el-icon class="theme-icon"><component :is="themeIcons[currentTheme]" /></el-icon>
            主题
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="deep-space">深空 (默认)</el-dropdown-item>
              <el-dropdown-item command="cyberpunk">赛博朋克</el-dropdown-item>
              <el-dropdown-item command="chatgpt-white">纯净白 (ChatGPT)</el-dropdown-item>
              <el-dropdown-item command="fresh-green">小清新</el-dropdown-item>
              <el-dropdown-item command="black-gold">黑金奢华</el-dropdown-item>
              <el-dropdown-item command="red-black">红黑撞色</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main :class="{ 'no-padding': !isProjectView }">
      <RouterView v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
  </div>
</template>

<style>
/* Global Variables with CSS Vars */
:root {
  --primary-color: #d4af37;
  --bg-gradient-start: #0f172a;
  --bg-gradient-end: #1a2a6c;
  --glass-bg: rgba(15, 23, 42, 0.6);
  --glass-border: rgba(212, 175, 55, 0.3);
  --text-color: #fff;
  --accent-glow: rgba(212, 175, 55, 0.2);
}

body {
  margin: 0;
  background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
  background-attachment: fixed;
  color: var(--text-color);
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
  height: 100vh;
  overflow: hidden; /* Prevent body scroll */
  transition: background 0.5s ease;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

main {
  flex: 1;
  overflow: hidden; /* Main content shouldn't scroll unless specified by child */
  display: flex;
  flex-direction: column;
}

/* Child views should handle their own scrolling if needed, but user requested NO scrollbars */
/* We will ensure layouts fit in 100vh */

.glass-header {

  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--primary-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.5s ease;
}

.logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color);
  text-shadow: 0 0 10px var(--accent-glow);
  letter-spacing: 1px;
}

nav {
  display: flex;
  gap: 2rem;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

nav a {
  color: var(--text-color);
  opacity: 0.7;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  padding: 0.5rem 0;
}

nav a:hover {
  opacity: 1;
  color: var(--primary-color);
}

nav a.router-link-active {
  opacity: 1;
  color: var(--primary-color);
  text-shadow: 0 0 8px var(--accent-glow);
}

nav a.router-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--primary-color);
  box-shadow: 0 0 5px var(--primary-color);
}

.theme-switcher {
  cursor: pointer;
}

.el-dropdown-link {
  color: var(--text-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.theme-icon {
  font-size: 1.2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  color: var(--text-color);
  font-size: 0.9rem;
  opacity: 0.7;
}

.back-btn:hover {
  opacity: 1;
  color: var(--primary-color);
}

.separator {
  color: var(--text-color);
  opacity: 0.3;
}

.project-title {
  font-weight: normal;
  font-size: 1rem;
  opacity: 0.8;
  margin-left: 0.5rem;
}

.no-padding {
  padding: 0 !important;
}

main {
  padding: 2rem;
  flex: 1;
}

/* Global Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

::-webkit-scrollbar-thumb {
  background: var(--primary-color);
  border-radius: 4px;
  opacity: 0.5;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--primary-color);
  opacity: 1;
}
</style>
