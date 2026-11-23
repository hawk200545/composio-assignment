<script setup>
import { useNav } from '@slidev/client'

const { currentSlideNo, hasNext, hasPrev, next, prev, total } = useNav()
</script>

<template>
  <nav class="deck-footer" aria-label="Slide navigation" @keydown.left.prevent="prev" @keydown.right.prevent="next">
    <div class="footer-index"><span>{{ String(currentSlideNo).padStart(2, '0') }}</span><span> / {{ String(total).padStart(2, '0') }}</span></div>
    <div class="footer-controls">
      <a v-if="currentSlideNo !== total" href="/7">App matrix</a>
      <a v-else href="/1">Back to start</a>
      <button type="button" aria-label="Previous slide" :disabled="!hasPrev" @click="prev">←</button>
      <button type="button" aria-label="Next slide" :disabled="!hasNext" @click="next">→</button>
    </div>
  </nav>
</template>
