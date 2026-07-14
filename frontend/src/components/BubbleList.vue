<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-medium text-ink">{{ title }}</h2>
        <span v-if="total != null" class="text-xs text-muted">共 {{ total }}</span>
      </div>
      <button
        v-if="sortable"
        class="text-xs font-medium text-muted hover:text-accent transition-colors flex items-center gap-1"
        @click="$emit('toggle-sort')"
      >
        排序：<span class="text-accent">{{ sortBy === 'hot' ? '人气最高' : '最新上传' }}</span>
        <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"></polyline>
          <polyline points="6 15 12 9 18 15"></polyline>
        </svg>
      </button>
    </div>

    <div v-if="!styles.length && !loading" class="py-12 text-center text-sm text-muted">
      暂无气泡
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <BubbleCard
        v-for="(style, idx) in styles"
        :key="style.id"
        :bubble="style"
        :current-id="currentId"
        class="scroll-animate"
        :style="{ animationDelay: `${Math.min(idx, 11) * 40}ms` }"
        @select="handleSelect"
        @edit="handleEdit"
        @delete="handleDelete"
        @share="handleShare"
        @copy-share="handleCopyShare"
        @toggle-public="handleTogglePublic"
        @toggle-favorite="handleToggleFavorite"
        @remove-import="handleRemoveImport"
      />
    </div>

    <div ref="sentinel" class="py-6 text-center text-xs text-muted">
      <span v-if="loadingMore">加载中…</span>
      <span v-else-if="!hasMore && styles.length">没有更多了</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import BubbleCard from './BubbleCard.vue'

const props = defineProps({
  styles: { type: Array, required: true },
  currentId: { type: Number, default: 0 },
  title: { type: String, default: '' },
  total: { type: Number, default: null },
  sortable: { type: Boolean, default: false },
  sortBy: { type: String, default: 'new' },
  loading: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: false },
})

const emit = defineEmits([
  'select', 'edit', 'delete', 'share', 'copyShare',
  'togglePublic', 'toggleFavorite', 'removeImport',
  'load-more', 'toggle-sort',
])

const sentinel = ref(null)
let observer = null

const setupObserver = () => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
  if (!sentinel.value) return
  observer = new IntersectionObserver((entries) => {
    const hit = entries.some(e => e.isIntersecting)
    if (hit && props.hasMore && !props.loadingMore && !props.loading) {
      emit('load-more')
    }
  }, { root: null, rootMargin: '200px', threshold: 0 })
  observer.observe(sentinel.value)
}

onMounted(() => {
  setupObserver()
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})

watch(() => [props.hasMore, props.loadingMore, props.styles.length], () => {
  // re-bind after list changes
  requestAnimationFrame(setupObserver)
})

const handleSelect = (id) => emit('select', id)
const handleEdit = (style) => emit('edit', style)
const handleDelete = (style) => emit('delete', style)
const handleShare = (style) => emit('share', style)
const handleCopyShare = (code) => emit('copyShare', code)
const handleTogglePublic = (id, isPublic) => emit('togglePublic', id, isPublic)
const handleToggleFavorite = (id, favorite) => emit('toggleFavorite', id, favorite)
const handleRemoveImport = (style) => emit('removeImport', style)
</script>
