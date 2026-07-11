<template>
  <div
    :class="[
      'bg-surface border-2 rounded-xl p-5 cursor-pointer transition-all duration-200 hover:shadow-subtle',
      bubble.id === currentId ? 'border-accent' : 'border-border'
    ]"
    @click="$emit('select', bubble.id)"
  >
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-base font-medium text-ink">{{ bubble.name }}</span>
          <span v-if="bubble.desc" class="text-xs text-muted">{{ bubble.desc }}</span>
          <span v-if="bubble.official" class="px-2 py-0.5 text-xs font-medium text-paleText-blue bg-pale-blue rounded-full uppercase tracking-wider">官方</span>
          <span v-else-if="bubble.mine" class="px-2 py-0.5 text-xs font-medium text-accent bg-pale-yellow rounded-full uppercase tracking-wider">我的</span>
          <span v-else-if="bubble.imported" class="px-2 py-0.5 text-xs font-medium text-paleText-blue bg-pale-blue rounded-full uppercase tracking-wider">导入</span>
          <span v-else-if="bubble.public" class="px-2 py-0.5 text-xs font-medium text-paleText-green bg-pale-green rounded-full uppercase tracking-wider">公开</span>
          <span v-if="bubble.favorited" class="px-2 py-0.5 text-xs font-medium text-paleText-red bg-pale-red rounded-full uppercase tracking-wider">已收藏</span>
        </div>
        <div v-if="bubble.uses > 0 || bubble.author" class="flex items-center gap-3 mt-2">
          <span v-if="!bubble.official && bubble.uses > 0" class="text-xs text-paleText-red bg-pale-red px-2 py-0.5 rounded-full">{{ bubble.uses }} 人在用</span>
          <span v-if="bubble.author" class="text-xs text-muted">by {{ bubble.author }}</span>
          <span v-else-if="bubble.public && !bubble.official" class="text-xs text-muted">by 匿名书友</span>
        </div>
      </div>
      <div
        :class="[
          'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1',
          bubble.id === currentId ? 'border-accent bg-accent' : 'border-border'
        ]"
      >
        <div v-if="bubble.id === currentId" class="w-2 h-2 rounded-full bg-surface"></div>
      </div>
    </div>

    <div class="relative bg-canvas rounded-lg p-4 flex items-center justify-center mb-4 min-h-[60px] bubble-preview">
      <span v-html="previewLarge"></span>
      <div class="absolute top-2 right-2 flex items-center gap-1.5">
        <button
          class="w-8 h-8 rounded-full flex items-center justify-center transition-colors text-muted bg-surface hover:bg-border/50"
          title="复制SVG代码"
          @click.stop="copySvg"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
        </button>
        <button
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center transition-colors',
            bubble.favorited ? 'text-paleText-red bg-pale-red' : 'text-muted bg-surface hover:bg-border/50'
          ]"
          :title="bubble.favorited ? '取消收藏' : '收藏'"
          @click.stop="$emit('toggleFavorite', bubble.id, !bubble.favorited)"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" :fill="bubble.favorited ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
          </svg>
        </button>
      </div>
    </div>
    
    <div class="text-xs text-muted mb-2">正文中的实际大小</div>
    <div class="bg-canvas rounded-lg p-3 text-sm text-ink leading-relaxed bubble-preview">
      他抬头望向天边的晚霞，久久没有说话<span v-html="previewSmall"></span>。
    </div>
    
    <div v-if="bubble.mine" class="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
      <button
        class="px-3 py-1.5 text-xs font-medium text-ink bg-surface border border-border rounded-lg hover:bg-canvas transition-colors"
        @click.stop="$emit('edit', bubble)"
      >
        编辑
      </button>
      <button
        class="px-3 py-1.5 text-xs font-medium text-ink bg-surface border border-border rounded-lg hover:bg-canvas transition-colors"
        @click.stop="$emit('share', bubble)"
      >
        生成分享码
      </button>
      <button
        class="px-3 py-1.5 text-xs font-medium text-paleText-red bg-pale-red border border-transparent rounded-lg hover:bg-red-50 transition-colors"
        @click.stop="$emit('delete', bubble)"
      >
        删除
      </button>
      <label class="flex items-center gap-2 text-xs text-muted cursor-pointer">
        <input
          type="checkbox"
          :checked="bubble.public"
          @change.stop="$emit('togglePublic', bubble.id, !bubble.public)"
          class="w-3.5 h-3.5 rounded border-border"
        />
        公开分享
      </label>
    </div>

    <div v-if="bubble.imported" class="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
      <button
        class="px-3 py-1.5 text-xs font-medium text-paleText-red bg-pale-red border border-transparent rounded-lg hover:bg-red-50 transition-colors"
        @click.stop="$emit('removeImport', bubble)"
      >
        移除
      </button>
    </div>

    <div v-if="bubble.shareCode" class="mt-4 pt-4 border-t border-border">
      <div class="flex gap-3 items-center">
        <code class="flex-1 bg-canvas rounded-lg px-3 py-2 text-sm font-mono font-semibold text-accent tracking-wider"
              @click.stop>{{ bubble.shareCode }}</code>
        <button 
          class="px-3 py-2 text-xs font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
          @click.stop="$emit('copyShare', bubble.shareCode)"
        >
          复制
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElNotification } from 'element-plus'
import { svgToImg } from '@/utils/svgHelper'

const props = defineProps({
  bubble: {
    type: Object,
    required: true
  },
  currentId: {
    type: Number,
    default: 0
  }
})

defineEmits(['select', 'edit', 'delete', 'share', 'copyShare', 'togglePublic', 'toggleFavorite', 'removeImport'])

const previewLarge = computed(() => {
  return svgToImg(props.bubble.svg, 'h-14 w-auto', props.bubble.color, props.bubble.textColor)
})

const previewSmall = computed(() => {
  return svgToImg(props.bubble.svg, 'h-5 w-auto inline-block align-middle ml-1', props.bubble.color, props.bubble.textColor)
})

const copySvg = async () => {
  const svg = props.bubble.rawSvg || props.bubble.svg
  if (!svg) {
    ElNotification({ title: '复制失败', message: 'SVG内容为空', type: 'error', duration: 3000 })
    return
  }
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(svg)
    } else {
      const ta = document.createElement('textarea')
      ta.value = svg
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    ElNotification({ title: '已复制', message: 'SVG代码已复制到剪贴板', type: 'success', duration: 3000 })
  } catch {
    ElNotification({ title: '复制失败', message: '请手动复制SVG代码', type: 'error', duration: 3000 })
  }
}
</script>
