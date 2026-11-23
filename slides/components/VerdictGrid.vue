<script setup>
import summary from '../summary.json'

const cells = Object.entries(summary.verdicts).flatMap(([name, count]) => Array(count).fill(name))
</script>

<template>
  <div class="verdict-grid" aria-hidden="true">
    <span v-for="(name, index) in cells" :key="index" class="status-mark" :data-verdict="name" />
  </div>
</template>
