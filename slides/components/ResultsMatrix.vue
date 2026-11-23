<script setup>
import { computed, nextTick, onMounted, ref, shallowRef, watch } from 'vue'
import summary from '../summary.json'

const PAGE_SIZE = 6
const DETAIL_FIELDS = {
  auth: 'Authentication', developer_access: 'Developer credentials', production_access: 'Production credentials',
  api_interfaces: 'API interfaces', api_breadth: 'API breadth', mcp: 'MCP server',
}
const LABELS = {
  oauth2: 'OAuth 2.0', api_key: 'API key', basic: 'Basic', token: 'Token', none_required: 'None required',
  free: 'Free', free_trial: 'Trial', paid_plan: 'Paid', admin_approval: 'Admin approval',
  vendor_approval: 'Vendor approval', contact_sales: 'Contact sales', partnership: 'Partnership',
  rest: 'REST', graphql: 'GraphQL', grpc: 'gRPC', local_cli: 'Local CLI', no_public_interface: 'No public interface',
  explicitly_unavailable: 'Unavailable', other: 'Other', broad: 'Broad', limited: 'Limited', none: 'None',
  official: 'Official', community: 'Community', unavailable: 'Unavailable',
}
const rows = shallowRef([])
const isLoading = ref(true)
const loadError = ref(false)
const query = ref('')
const category = ref('')
const verdict = ref('')
const page = ref(1)
const selected = shallowRef(null)
const closeButton = ref(null)
let returnFocus = null

async function loadRows() {
  isLoading.value = true
  loadError.value = false
  try {
    const response = await fetch('/data/results.json')
    if (!response.ok) throw new Error('Could not read the app export')
    rows.value = await response.json()
  }
  catch {
    loadError.value = true
  }
  finally {
    isLoading.value = false
  }
}

onMounted(loadRows)
watch([query, category, verdict], () => { page.value = 1 })

const filtered = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return rows.value.filter(row => (
    (!needle || row.name.toLowerCase().includes(needle))
    && (!category.value || row.category === category.value)
    && (!verdict.value || row.verdict === verdict.value)
  ))
})
const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))
const start = computed(() => (page.value - 1) * PAGE_SIZE)
const visible = computed(() => filtered.value.slice(start.value, start.value + PAGE_SIZE))

function formatClaim(claim) {
  if (claim.conflict) return 'Unresolved conflict'
  return claim.values.map(value => LABELS[value] ?? value).join(', ') || 'Unverified'
}

function sourceHost(url) {
  return new URL(url).hostname
}

async function openApp(row, event) {
  returnFocus = event.currentTarget
  selected.value = row
  await nextTick()
  closeButton.value?.focus()
}

async function closeApp() {
  selected.value = null
  await nextTick()
  returnFocus?.focus()
}
</script>

<template>
  <section class="matrix-ui" aria-label="Research results">
    <div v-show="!selected">
      <div class="matrix-toolbar">
        <input v-model="query" type="search" aria-label="Search by app name" placeholder="Search by app name">
        <select v-model="category" aria-label="Category">
          <option value="">All categories</option>
          <option v-for="item in summary.categories" :key="item.name" :value="item.name">{{ item.name }}</option>
        </select>
        <select v-model="verdict" aria-label="Verdict">
          <option value="">All verdicts</option>
          <option v-for="name in Object.keys(summary.verdicts)" :key="name">{{ name }}</option>
        </select>
        <div class="matrix-downloads">
          <a href="/csv">View CSV ↗</a>
          <a href="/data/results.csv" download>CSV ↓</a>
          <a href="/data/results.json" download>JSON ↓</a>
        </div>
      </div>

      <div v-if="isLoading" class="matrix-message" role="status">Loading app findings…</div>
      <div v-else-if="loadError" class="matrix-message" role="alert">The results did not load. <button type="button" @click="loadRows">Retry</button></div>
      <div v-else-if="!visible.length" class="matrix-message" role="status">No apps match those filters.</div>
      <table v-else class="results-table">
        <thead><tr><th scope="col">App</th><th scope="col">Auth</th><th scope="col">Production</th><th scope="col">Interface</th><th scope="col">MCP</th><th scope="col">Verdict</th></tr></thead>
        <tbody>
          <tr v-for="row in visible" :key="row.id">
            <th scope="row"><button type="button" class="app-link" :aria-label="'Evidence for ' + row.name" @click="openApp(row, $event)">{{ row.name }} <span aria-hidden="true">↗</span></button></th>
            <td>{{ formatClaim(row.claims.auth) }}</td>
            <td>{{ formatClaim(row.claims.production_access) }}</td>
            <td>{{ formatClaim(row.claims.api_interfaces) }}</td>
            <td>{{ formatClaim(row.claims.mcp) }}</td>
            <td><span class="verdict-text" :data-verdict="row.verdict"><span class="status-mark" :data-verdict="row.verdict" />{{ row.verdict }}</span></td>
          </tr>
        </tbody>
      </table>

      <div v-if="visible.length" class="matrix-pager">
        <span aria-live="polite">{{ start + 1 }}–{{ start + visible.length }} of {{ filtered.length }} apps · Select an app to see evidence</span>
        <button type="button" :disabled="page === 1" @click="page--">Previous</button>
        <button type="button" :disabled="page === pageCount" @click="page++">Next</button>
      </div>
    </div>

    <article v-if="selected" class="app-detail" @keydown.esc.stop="closeApp">
      <div class="detail-header">
        <div><h2>{{ selected.name }}</h2><p>{{ selected.category }}</p></div>
        <button ref="closeButton" type="button" @click="closeApp">← Back to results</button>
      </div>
      <div class="detail-scroll" tabindex="0" aria-label="App evidence">
        <p v-if="selected.claims.description.values.length" class="app-description">{{ selected.claims.description.values.join(' ') }}</p>
        <p class="app-blocker"><strong>{{ selected.verdict }}</strong><span v-if="selected.blocker"> · {{ selected.blocker }}</span>.</p>
        <p v-if="selected.composio_catalog.status === 'found'" class="catalog-detail"><a :href="selected.composio_catalog.catalog_url" target="_blank" rel="noopener noreferrer">Composio catalog match ↗</a></p>
        <p v-else class="catalog-detail">No exact catalog name match found in this run.</p>

        <div class="detail-fields">
          <details v-for="(label, field) in DETAIL_FIELDS" :key="field">
            <summary><strong>{{ label }}</strong><span>{{ formatClaim(selected.claims[field]) }}</span></summary>
            <p v-if="!selected.claims[field].evidence.length">No supporting excerpt recorded.</p>
            <div v-for="(item, index) in selected.claims[field].evidence" :key="index" class="field-source">
              <q>{{ item.quote }}</q>
              <a v-if="item.url" :href="item.url" target="_blank" rel="noopener noreferrer">{{ sourceHost(item.url) }} ↗</a>
            </div>
          </details>
        </div>
      </div>
    </article>
  </section>
</template>
