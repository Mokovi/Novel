import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  // Public routes (no sidebar)
  {
    path: '/login',
    name: 'login',
    meta: { layout: 'auth' },
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'register',
    meta: { layout: 'auth' },
    component: () => import('../views/RegisterView.vue'),
  },

  // Book selection (simple top bar)
  {
    path: '/books',
    name: 'book-select',
    meta: { layout: 'book-select' },
    component: () => import('../views/BookSelectView.vue'),
  },

  // Book-scoped routes (full sidebar)
  {
    path: '/books/:bookId/outline',
    name: 'outline',
    meta: { layout: 'app' },
    component: () => import('../views/OutlineView.vue'),
  },
  {
    path: '/books/:bookId/editor/:id?',
    name: 'editor',
    meta: { layout: 'app' },
    component: () => import('../views/ChapterEditor.vue'),
  },
  {
    path: '/books/:bookId/dashboard',
    name: 'dashboard',
    meta: { layout: 'app' },
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/books/:bookId/worldview',
    name: 'worldview',
    meta: { layout: 'app' },
    component: () => import('../views/WorldviewEditor.vue'),
  },
  {
    path: '/books/:bookId/characters',
    name: 'characters',
    meta: { layout: 'app' },
    component: () => import('../views/CharacterList.vue'),
  },
  {
    path: '/books/:bookId/characters/:id',
    name: 'character-detail',
    meta: { layout: 'app' },
    component: () => import('../views/CharacterDetail.vue'),
  },
  {
    path: '/books/:bookId/variables',
    name: 'variables',
    meta: { layout: 'app' },
    component: () => import('../views/PromptVariables.vue'),
  },

  // Global routes (full sidebar, no bookId in path)
  {
    path: '/templates',
    name: 'templates',
    meta: { layout: 'app' },
    component: () => import('../views/TemplateLibrary.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    meta: { layout: 'app' },
    component: () => import('../views/ModelRouteSettings.vue'),
  },

  // Redirect root to books
  {
    path: '/',
    redirect: '/books',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard — check auth + book selection
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Try to restore session from stored token
  if (!authStore.isAuthenticated() && localStorage.getItem('auth_token')) {
    try {
      await authStore.fetchMe()
    } catch {
      // Token invalid, will redirect to login
    }
  }

  const requiresAuth = to.meta.layout !== 'auth'
  const isAuthenticated = authStore.isAuthenticated()

  if (!isAuthenticated && requiresAuth) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (isAuthenticated && (to.name === 'login' || to.name === 'register')) {
    return next({ name: 'book-select' })
  }

  // Select book when entering book-scoped routes
  if (to.params.bookId && isAuthenticated) {
    const { useBooksStore } = await import('../stores/books.js')
    const booksStore = useBooksStore()
    const bookId = Number(to.params.bookId)
    if (!booksStore.currentBook || booksStore.currentBook.id !== bookId) {
      await booksStore.selectBook(bookId)
    }
  }

  next()
})

export default router
