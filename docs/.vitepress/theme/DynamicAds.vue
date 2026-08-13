<!-- Optional sidebar promo slot — disabled for MediaCrawler Pro (no third-party ads). -->

<script setup>
import { ref } from 'vue'
const ads = ref([])
</script>

<template>
  <div v-if="ads.length > 0" class="vp-ad-carousel" />
</template>
