<script setup>
import { csvParseRows } from 'd3-dsv'
import { computed, onMounted, ref, shallowRef } from 'vue'

const CSV_URL = '/data/results.csv'
const COLUMN_LABELS = {
  id: 'ID', name: 'App', category: 'Category', verdict: 'Verdict', blocker: 'Blocker',
  auth: 'Auth', developer_access: 'Developer access', production_access: 'Production access',
  api_interfaces: 'API interfaces', api_breadth: 'API breadth', mcp: 'MCP',
  description: 'Description', evidence_urls: 'Evidence', hint: 'Starting URL', composio_catalog: 'Composio catalog',
}
const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' })

const status = ref('loading')
const columns = shallowRef([])
const rows = shallowRef([])
const query = ref('')
const category = ref('')
const verdict = ref('')
const sortColumn = ref('id')
const descending = ref(false)

async function loadCsv() {
  status.value = 'loading'
  try {
    const response = await fetch(CSV_URL)
    if (!response.ok) throw new Error('Could not load the CSV export')
    const [headers, ...records] = csvParseRows((await response.text()).replace(/^\uFEFF/, ''))
    if (!headers?.includes('id') || !headers.includes('name') || records.some(row => row.length !== headers.length)) {
      throw new Error('Unexpected CSV format')
    }
    const preferred = Object.keys(COLUMN_LABELS).filter(key => headers.includes(key))
    columns.value = [...preferred, ...headers.filter(key => !preferred.includes(key))]
    rows.value = records.map(record => Object.fromEntries(headers.map((key, index) => [key, record[index]])))
    status.value = 'ready'
  }
  catch {
    status.value = 'error'
  }
}

onMounted(loadCsv)

const categories = computed(() => [...new Set(rows.value.map(row => row.category).filter(Boolean))].sort(collator.compare))
const verdicts = computed(() => [...new Set(rows.value.map(row => row.verdict).filter(Boolean))].sort(collator.compare))
const matching = computed(() => {
  const needle = query.value.toLowerCase().trim()
  const column = sortColumn.value
  const direction = descending.value ? -1 : 1
  return rows.value.filter(row => (
    (!category.value || row.category === category.value)
    && (!verdict.value || row.verdict === verdict.value)
    && (!needle || Object.values(row).some(value => value.toLowerCase().includes(needle)))
  )).sort((a, b) => direction * collator.compare(a[column], b[column]))
})

function sortBy(column) {
  descending.value = column === sortColumn.value && !descending.value
  sortColumn.value = column
}

function evidenceLinks(value) {
  return value.split('; ').filter(url => url.startsWith('https://'))
}
</script>

<template>
  <main class="csv-viewer">
    <div class="csv-shell">
      <nav class="csv-navigation" aria-label="Case study navigation">
        <a href="/7">← Back to app matrix</a>
      </nav>

      <header class="csv-header">
        <div>
          <h1>Research results<span>.</span></h1>
          <p>The original toolkit research export, with every CSV column.</p>
        </div>
        <a class="csv-download" :href="CSV_URL" download>Download CSV ↓</a>
      </header>

      <div v-if="status === 'loading'" class="csv-message" role="status">Loading the CSV…</div>
      <div v-else-if="status === 'error'" class="csv-message" role="alert">
        The CSV could not be loaded. <button type="button" @click="loadCsv">Retry</button>
      </div>
      <template v-else>
        <div class="csv-toolbar" role="search" aria-label="Filter research results">
          <label>Search<input v-model="query" type="search" placeholder="Search any column"></label>
          <label>Category<select v-model="category">
            <option value="">All categories</option>
            <option v-for="item in categories" :key="item">{{ item }}</option>
          </select></label>
          <label>Verdict<select v-model="verdict">
            <option value="">All verdicts</option>
            <option v-for="item in verdicts" :key="item">{{ item }}</option>
          </select></label>
        </div>
        <div class="csv-summary">
          <p aria-live="polite">{{ matching.length }} of {{ rows.length }} apps · {{ columns.length }} columns</p>
          <p v-if="matching.length">Scroll sideways for more columns →</p>
        </div>
        <div v-if="matching.length" class="csv-table-frame" tabindex="0" role="region" aria-label="Sortable CSV results">
          <table aria-label="Toolkit research results">
            <thead>
              <tr>
                <th v-for="column in columns" :key="column" :class="`csv-col-${column}`" scope="col"
                  :aria-sort="sortColumn === column ? (descending ? 'descending' : 'ascending') : undefined">
                  <button type="button" @click="sortBy(column)">
                    {{ COLUMN_LABELS[column] ?? column }}
                    <span aria-hidden="true">{{ sortColumn === column ? (descending ? '↓' : '↑') : '↕' }}</span>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in matching" :key="row.id">
                <component :is="column === 'name' ? 'th' : 'td'" v-for="column in columns" :key="column"
                  :scope="column === 'name' ? 'row' : undefined" :class="`csv-col-${column}`">
                  <span v-if="column === 'verdict'" class="csv-verdict">
                    <span class="status-mark" :data-verdict="row.verdict" aria-hidden="true" />{{ row.verdict }}
                  </span>
                  <details v-else-if="column === 'evidence_urls' && row[column]">
                    <summary>Source links</summary>
                    <ul>
                      <li v-for="url in evidenceLinks(row[column])" :key="url">
                        <a :href="url" target="_blank" rel="noopener noreferrer">{{ url }}</a>
                      </li>
                    </ul>
                  </details>
                  <a v-else-if="column === 'hint' && row[column]?.startsWith('https://')"
                    :href="row[column]" target="_blank" rel="noopener noreferrer">{{ row[column] }}</a>
                  <template v-else>{{ row[column] || '—' }}</template>
                </component>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="csv-message">No apps match your filters.</div>
      </template>
    </div>
  </main>
</template>

<style scoped>
.csv-viewer { height: 100dvh; overflow-y: auto; background: var(--paper); color: var(--ink); font-family: 'Space Grotesk Variable', sans-serif; }
.csv-shell { max-width: 96rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 4rem) 2rem; }
.csv-navigation { border-bottom: 1px solid var(--line); padding: 1rem 0; font-size: .875rem; font-weight: 700; }
.csv-viewer a { color: var(--accent); text-decoration: underline; text-underline-offset: .19em; }
.csv-viewer :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.csv-header { display: flex; align-items: end; justify-content: space-between; gap: 1rem; margin: 2rem 0; }
.csv-header h1 { font-size: clamp(2.6rem, 6.5vw, 4rem); font-weight: 680; line-height: 1; letter-spacing: -.06em; }
.csv-header h1 span { color: var(--accent); }
.csv-header p { margin-top: .6rem; color: var(--muted); font-size: 1.05rem; }
.csv-viewer .csv-download { flex-shrink: 0; padding: .68rem .9rem; background: var(--ink); color: var(--paper); text-decoration: none; font-weight: 700; }
.csv-viewer .csv-download:hover { background: var(--accent); }
.csv-toolbar { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.35fr) minmax(0, 1fr); gap: .75rem; }
.csv-toolbar label { min-width: 0; display: grid; gap: .3rem; font-size: .875rem; font-weight: 650; }
.csv-toolbar input, .csv-toolbar select { min-width: 0; width: 100%; height: 2.65rem; border: 1px solid #a89d90; background: #fffdf7; padding: 0 .7rem; font: inherit; font-weight: 450; }
.csv-summary { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .3rem 1rem; margin: .95rem 0 .55rem; color: var(--muted); font-size: .875rem; }
.csv-message { border-top: 1px solid var(--line); margin: 1rem 0; padding: 1rem 0; }
.csv-message button { margin-left: .3rem; color: var(--accent); text-decoration: underline; cursor: pointer; }
.csv-table-frame { max-height: 68dvh; overflow: auto; border: 1px solid var(--line); border-top-color: var(--ink); background: #fffdf7; }
.csv-table-frame table { width: 100%; border-spacing: 0; font-size: .9rem; line-height: 1.3; }
.csv-table-frame th, .csv-table-frame td { min-width: 8.5rem; padding: .65rem .75rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; overflow-wrap: anywhere; }
.csv-table-frame thead th { position: sticky; top: 0; z-index: 2; background: #efe9df; padding: 0; }
.csv-table-frame thead button { display: flex; justify-content: space-between; align-items: center; gap: .4rem; width: 100%; min-height: 2.6rem; padding: .5rem .75rem; font-weight: 675; text-align: left; cursor: pointer; }
.csv-table-frame thead button:focus-visible { outline-offset: -3px; }
.csv-table-frame thead button:hover, .csv-table-frame thead th[aria-sort] button { color: var(--accent); }
.csv-table-frame thead button span { color: var(--muted); }
.csv-table-frame tbody tr { --row-bg: #fffdf7; background: var(--row-bg); }
.csv-table-frame tbody tr:nth-child(even) { --row-bg: #f6f1e8; }
.csv-table-frame tbody tr:hover { --row-bg: #f2ece2; }
.csv-table-frame tbody .csv-col-name { background: var(--row-bg); font-weight: 680; }
.csv-table-frame .csv-col-id { min-width: 4rem; color: var(--muted); font-variant-numeric: tabular-nums; }
.csv-table-frame .csv-col-name { position: sticky; left: 0; z-index: 1; min-width: 10rem; box-shadow: 1px 0 var(--line); }
.csv-table-frame thead .csv-col-name { z-index: 3; }
.csv-table-frame .csv-col-category, .csv-table-frame .csv-col-api_interfaces { min-width: 11rem; }
.csv-table-frame .csv-col-blocker, .csv-table-frame .csv-col-hint, .csv-table-frame .csv-col-evidence_urls { min-width: 13rem; max-width: 22rem; }
.csv-table-frame .csv-col-description { min-width: 19rem; max-width: 24rem; }
.csv-table-frame details summary { color: var(--accent); cursor: pointer; }
.csv-table-frame details li { margin-top: .45rem; }
.csv-verdict { display: inline-flex; align-items: center; gap: .37rem; font-weight: 620; }

@media (max-width: 38rem) {
  .csv-header { align-items: start; flex-direction: column; margin: 1.45rem 0; }
  .csv-toolbar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .csv-toolbar label:first-child { grid-column: 1 / -1; }
  .csv-table-frame .csv-col-name { min-width: 8rem; }
}
</style>
