<template>
  <div>
    <div 
      v-for="(group, index) in groupedStyles" 
      :key="group.title"
      class="mb-8"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-medium text-ink">{{ group.title }}</h2>
          <span v-if="group.hint" class="text-xs text-muted">{{ group.hint }}</span>
        </div>
        <button 
          v-if="group.sortable"
          class="text-xs font-medium text-muted hover:text-accent transition-colors flex items-center gap-1"
          @click="toggleSort"
        >
          排序：<span class="text-accent">{{ sortBy === 'hot' ? '人气最高' : '最新上传' }}</span>
          <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
            <polyline points="6 15 12 9 18 15"></polyline>
          </svg>
        </button>
      </div>
      
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <BubbleCard 
          v-for="(style, idx) in group.styles" 
          :key="style.id"
          :bubble="style"
          :current-id="currentId"
          class="scroll-animate"
          :style="{ animationDelay: `${(index * 2 + idx) * 80}ms` }"
          @select="handleSelect"
          @edit="handleEdit"
          @delete="handleDelete"
          @share="handleShare"
          @copy-share="handleCopyShare"
          @toggle-public="handleTogglePublic"
          @toggle-favorite="handleToggleFavorite"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import BubbleCard from './BubbleCard.vue'

const props = defineProps({
  styles: {
    type: Array,
    required: true
  },
  currentId: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select', 'edit', 'delete', 'share', 'copyShare', 'togglePublic', 'toggleFavorite'])

const sortBy = ref('new')

const toggleSort = () => {
  sortBy.value = sortBy.value === 'new' ? 'hot' : 'new'
}

const groupedStyles = computed(() => {
  const mine = props.styles.filter(s => s.mine)
  const favorited = props.styles.filter(s => s.favorited && !s.mine)
  const favIds = new Set(favorited.map(s => s.id))
  const imported = props.styles.filter(s => s.imported && !favIds.has(s.id))
  let pub = props.styles.filter(s => s.public && !s.mine && !s.imported && !s.official && !favIds.has(s.id))
  const official = props.styles.filter(s => s.official && !favIds.has(s.id))

  if (sortBy.value === 'hot') {
    pub = [...pub].sort((a, b) => (b.uses || 0) - (a.uses || 0) || b.id - a.id)
  }

  const groups = []

  if (mine.length) {
    groups.push({ title: '我的气泡', hint: '我自己创建的', styles: mine })
  }
  if (favorited.length) {
    groups.push({ title: '我的收藏', hint: '收藏的气泡', styles: favorited })
  }
  if (imported.length) {
    groups.push({ title: '我导入的', hint: '凭分享码添加', styles: imported })
  }
  if (pub.length) {
    groups.push({ title: '大家公开的', hint: '其他用户公开分享', styles: pub, sortable: true })
  }
  if (official.length) {
    groups.push({ title: '官方样式', styles: official })
  }

  return groups
})

const handleSelect = (id) => emit('select', id)
const handleEdit = (style) => emit('edit', style)
const handleDelete = (style) => emit('delete', style)
const handleShare = (style) => emit('share', style)
const handleCopyShare = (code) => emit('copyShare', code)
const handleTogglePublic = (id, isPublic) => emit('togglePublic', id, isPublic)
const handleToggleFavorite = (id, favorite) => emit('toggleFavorite', id, favorite)
</script>
