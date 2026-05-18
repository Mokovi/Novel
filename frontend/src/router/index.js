import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/outline',
    name: 'outline',
    component: () => import('../views/OutlineView.vue'),
  },
  {
    path: '/editor/:id?',
    name: 'editor',
    component: () => import('../views/ChapterEditor.vue'),
  },
  {
    path: '/worldview',
    name: 'worldview',
    component: () => import('../views/WorldviewEditor.vue'),
  },
  {
    path: '/characters',
    name: 'characters',
    component: () => import('../views/CharacterList.vue'),
  },
  {
    path: '/characters/:id',
    name: 'character-detail',
    component: () => import('../views/CharacterDetail.vue'),
  },
  {
    path: '/templates',
    name: 'templates',
    component: () => import('../views/TemplateLibrary.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/ModelRouteSettings.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
