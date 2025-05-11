import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DnsView from '../views/DnsView.vue'
import BlockchainView from '../views/BlockchainView.vue'
import RegisterView from '../views/RegisterView.vue'
import WalletView from '../views/WalletView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/dns',
      name: 'dns',
      component: DnsView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/blockchain',
      name: 'blockchain',
      component: BlockchainView,
    },
    {
      path: '/wallet',
      name: 'wallet',
      component: WalletView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    }
  ],
})

export default router
