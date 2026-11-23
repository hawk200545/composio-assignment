<script setup>
import summary from '../summary.json'

const auditTitles = ['Original sample', 'Fresh sample']
const percent = ({ correct, total }) => (100 * correct / total).toFixed(1)
</script>

<template>
  <div class="audit-comparison">
    <section v-for="(series, index) in summary.audits" :key="index" :aria-label="auditTitles[index]">
      <div class="audit-group-heading"><h2>{{ auditTitles[index] }}</h2><span>{{ series[0].total }} scorable fields</span></div>
      <div v-for="(score, i) in series" :key="score.label" class="audit-row" :class="{ 'audit-last': i === series.length - 1 }">
        <span>{{ score.label }}</span>
        <div class="measure-track" aria-hidden="true"><div :style="{ width: `${percent(score)}%` }" /></div>
        <strong>{{ percent(score) }}%</strong><span class="audit-count">{{ score.correct }}/{{ score.total }}</span>
      </div>
    </section>
  </div>
</template>
