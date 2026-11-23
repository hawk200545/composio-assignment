<script setup>
import summary from '../summary.json'

const verdicts = Object.keys(summary.verdicts)
const shorterNames = [
  'CRM & Sales', 'Support & Helpdesk', 'Communications', 'Marketing & Social', 'Ecommerce',
  'Data, SEO & Scraping', 'Developer & Infrastructure', 'Productivity & Projects', 'Finance & Fintech', 'AI, Research & Media',
]
</script>

<template>
  <table class="category-table">
    <thead>
      <tr>
        <th scope="col">10 apps per category</th>
        <th v-for="name in verdicts" :key="name" scope="col"><span class="status-mark" :data-verdict="name" />{{ name }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="({ name, counts }, index) in summary.categories" :key="name">
        <th scope="row" :title="name">{{ shorterNames[index] }}</th>
        <td v-for="state in verdicts" :key="state" :class="{ 'has-count': counts[state] }">{{ counts[state] ?? '–' }}</td>
      </tr>
    </tbody>
  </table>
</template>
