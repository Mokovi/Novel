import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  // Book-scoped routes
  {
    path: '/books/:bookId/outline',
    name: 'book-outline',
    component: () => import('../views/OutlineView.vue'),
  },
  {
    path: '/books/:bookId/editor/:id?',
    name: 'book-editor',
    component: () => import('../views/ChapterEditor.vue'),
  },
  {
    path: '/books/:bookId/worldview',
    name: 'book-worldview',
    component: () => import('../views/WorldviewEditor.vue'),
  },
  {
    path: '/books/:bookId/characters',
    name: 'book-characters',
    component: () => import('../views/CharacterList.vue'),
  },
  {
    path: '/books/:bookId/characters/:id',
    name: 'book-character-detail',
    component: () => import('../views/CharacterDetail.vue'),
  },
  // Legacy routes (redirect or keep for backward compatibility)
  {
    path: '/outline',
    redirect: '/',
  },
  {
    path: '/editor/:id?',
    redirect: '/',
  },
  {
    path: '/worldview',
    redirect: '/',
  },
  {
    path: '/characters',
    redirect: '/',
  },
  {
    path: '/characters/:id',
    redirect: '/',
  },
  // Global (non-book-scoped) routes
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
