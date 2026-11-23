import { defineRoutesSetup } from '@slidev/types'

export default defineRoutesSetup(routes => [
  ...routes,
  { path: '/csv', component: () => import('../pages/CsvViewer.vue') },
])
