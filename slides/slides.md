---
theme: default
title: 100 apps, one toolkit research run
info: A Composio AI Product Ops take-home case study
colorSchema: light
canvasWidth: 1200
aspectRatio: 16/9
transition: none
presenter: false
fonts:
  provider: none
drawings:
  enabled: false
class: deck-page cover
---

<script setup>
import summary from './summary.json'
</script>

<div class="cover-grid">
  <div>
    <p class="eyebrow">Composio AI Product Ops · Take-home</p>
    <h1>100 apps,<br>one research run<span class="accent">.</span></h1>
    <p class="cover-description">Paid access was the most common confirmed gate. Nearly half the apps still needed evidence before a build decision.</p>
    <div class="cover-actions">
      <a class="deck-link primary-link" href="/2">See the findings <span aria-hidden="true">→</span></a>
      <a class="deck-link text-link" href="/7">Browse all 100 apps <span aria-hidden="true">↗</span></a>
    </div>
  </div>
  <div class="cover-evidence">
    <div class="evidence-heading"><span>Buildability</span><span>{{ summary.apps }} apps · Nov 2026</span></div>
    <VerdictGrid />
    <div class="cover-legend">
      <div v-for="(count, name) in summary.verdicts" :key="name"><span class="status-mark" :data-verdict="name"></span><strong>{{ count }}</strong><span>{{ name }}</span></div>
    </div>
  </div>
</div>

---
class: deck-page
---

<script setup>
import summary from './summary.json'
</script>

<p class="eyebrow">Portfolio patterns</p>
<h1>Where to validate first</h1>
<div class="split category-split">
  <CategoryMatrix />
  <div class="margin-notes">
    <div><strong>3 of 10 ready</strong><p>Productivity led the batch. ClickUp, Jira and Notion have catalog matches, so validate workflows on existing toolkits.</p></div>
    <div><strong>{{ summary.paidGates }} of {{ summary.verdicts.Gated }} gated</strong><p>Payment appeared in most gated verdicts. Support had six gated apps, the highest count.</p></div>
    <div><strong>8 of 10 unresolved</strong><p>Finance needs manual evidence first. Route confirmed approval or partner gates to outreach.</p></div>
  </div>
</div>
<p class="caption">Ready means documented self-serve production access and a broad API. Unresolved means the evidence was incomplete.</p>

---
class: deck-page
---

<script setup>
import summary from './summary.json'
const auth = [['API key', 'api_key'], ['OAuth 2.0', 'oauth2'], ['Token', 'token'], ['Basic', 'basic']]
</script>

<p class="eyebrow">Integration signals</p>
<h1>API keys and OAuth dominated</h1>
<div class="split signal-split">
  <div>
    <div class="chart-caption">Auth methods in the batch</div>
    <div class="measure-chart" aria-label="Authentication method counts">
      <div class="measure-row" v-for="[label, key] in auth" :key="key">
        <span>{{ label }}</span><div class="measure-track"><div :style="{ width: summary.authCounts[key] * 2 + '%' }"></div></div><strong>{{ summary.authCounts[key] }}</strong>
      </div>
    </div>
    <p class="caption">Apps can have multiple methods. Auth remained unresolved for {{ summary.authUnknown }} apps. The audit found frequent key/token mix-ups.</p>
  </div>
  <div class="signal-notes">
    <div><strong>{{ summary.paidPlans }}</strong><p>apps had a paid production path in the batch. Check development access separately.</p></div>
    <div><strong>{{ summary.rest }}</strong><p>apps had REST evidence, the most common interface.</p></div>
    <div><strong>{{ summary.officialMcp }}</strong><p>were labeled official MCP. {{ summary.mcpUnknown }} were unresolved.</p></div>
  </div>
</div>

---
class: deck-page
---

<script setup>
import summary from './summary.json'
const repo = import.meta.env.VITE_RESEARCH_REPO_URL?.trim()
</script>

<p class="eyebrow">Research agent</p>
<h1>Each claim carries its source</h1>
<ol class="pipeline" aria-label="Research pipeline">
  <li><strong>Discover</strong><p>Fetch public docs from product-specific domains.</p></li>
  <li><strong>Extract</strong><p>Save Gemini’s structured first pass with verbatim excerpts.</p></li>
  <li><strong>Verify</strong><p>Check quotes against source text, then review meaning and retry flagged fields.</p></li>
  <li><strong>Export</strong><p>Record verdicts and blockers. The Composio SDK matched {{ summary.catalogMatches }} catalog names.</p></li>
</ol>
<div class="split agent-split">
  <div class="run-panel">
    <strong>Run the six-app pilot</strong>
    <pre><code>uv run --locked --env-file .env python research.py</code></pre>
    <p>Set local OpenRouter and Composio keys using the included README.</p>
    <div class="inline-links"><a v-if="repo" :href="repo">Source repository ↗</a><a href="/data/research-source.zip" download>Download runnable source ↓</a></div>
  </div>
  <div class="human-note"><strong>Where review needed a person</strong><p>Check blocked pages, confirm the product identity, and label trial and ongoing access from vendor docs. Paygent Connect’s vendor identity remained unresolved.</p></div>
</div>

---
class: deck-page
---

<p class="eyebrow">Verification</p>
<h1>Verification lowered accuracy</h1>
<p class="slide-lead">Two separate 10-app samples were checked against primary docs. Unanswered fields count as misses.</p>
<AuditScores />
<p class="audit-takeaway"><strong>Hits and misses</strong> ClickUp matched all six fields in both original passes. The verifier withdrew two wrong answers and lost three correct Freshdesk answers. The patch lost correct developer-access answers for Lark and Harvest.</p>
<div class="inline-links"><a href="/data/holdout-report.md" download>Original audit ↓</a><a href="/data/recheck-report.md" download>Follow-up audit ↓</a></div>

---
class: deck-page
---

<p class="eyebrow">Evidence from the reruns</p>
<h1>Two fixes held up in replay</h1>
<div class="case-studies">
  <article><h2>Freshdesk</h2><p>The docs specify a trial allowance. Ongoing REST access starts on a paid plan. Repairing verbatim excerpts also restored two correct API claims.</p><a href="https://support.freshdesk.com/support/solutions/articles/225439" target="_blank" rel="noopener noreferrer">Freshdesk API limits ↗</a></article>
  <article><h2>BigCommerce</h2><p>The developer URL redirected to a docs host outside the allowlist. Adding the official host recovered REST and GraphQL with citations.</p><a href="https://docs.bigcommerce.com/developer/docs/overview/quick-start" target="_blank" rel="noopener noreferrer">BigCommerce developer quickstart ↗</a></article>
</div>
<div class="next-decision"><strong>Before scaling</strong><p>Prioritize sources that spell out plan access and credential names. Recheck on a fresh sample before replacing the batch results.</p></div>

---
class: deck-page matrix-slide
---

<p class="eyebrow">Original 100-app batch</p>
<h1>App findings and evidence</h1>
<ResultsMatrix />
