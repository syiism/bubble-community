<template>
  <div class="fixed inset-0 z-50 bg-ink/20 backdrop-blur-sm flex items-end sm:items-center justify-center">
    <div class="bg-surface w-full sm:w-[90%] sm:max-w-2xl sm:rounded-2xl rounded-t-2xl max-h-[90vh] overflow-y-auto animate-slide-up">
      <div class="sticky top-0 bg-surface border-b border-border px-6 py-4 flex items-center justify-between">
        <h2 class="text-lg font-medium text-ink">{{ isEditing ? '编辑气泡' : '添加气泡' }}</h2>
        <button 
          class="text-sm text-muted hover:text-ink transition-colors"
          @click="$emit('close')"
        >
          取消
        </button>
      </div>
      
      <div class="p-6 space-y-6">
        <div>
          <label class="block text-sm font-medium text-ink mb-2">名称</label>
          <input 
            v-model="form.name"
            type="text" 
            placeholder="如 我的爱心"
            class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
          />
        </div>
        
        <div v-if="admin">
          <label class="block text-sm font-medium text-ink mb-2">作者（用户名）</label>
          <select v-model="form.userId"
                  class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink
                         focus:outline-none focus:border-accent transition-colors">
            <option :value="0">—</option>
            <option v-for="u in userList" :key="u.id" :value="u.id">{{ u.username }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-ink mb-2">描述（选填）</label>
          <input 
            v-model="form.desc"
            type="text" 
            placeholder="如 圆润可爱 · 适合轻松向"
            maxlength="60"
            class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-ink mb-2">SVG 模板</label>
          <div class="text-xs text-muted mb-2">
            数字用 {n}；颜色用 {c}/{t}，也兼容 ${displayText}、{{color}} 等；粘贴自带颜色的也可以，会自动变可调
          </div>
          <textarea 
            v-model="form.svg"
            rows="6"
            placeholder='<svg ...>...{n}...</svg>'
            @input="preview"
            @change="autoMap"
            class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm font-mono text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors resize-none"
          ></textarea>
        </div>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-ink mb-2">气泡颜色</label>
            <div class="flex items-center gap-2">
              <input 
                type="color" 
                :value="form.color || '#b8693d'"
                @input="updateColor('color', $event.target.value)"
                class="w-10 h-10 rounded-lg border border-border cursor-pointer"
              />
              <input 
                v-model="form.color"
                type="text" 
                placeholder="留空=默认"
                @input="updateColor('color', form.color)"
                class="flex-1 px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
              />
              <button 
                class="px-3 py-2 text-xs font-medium text-muted bg-surface border border-border rounded-lg hover:bg-canvas transition-colors"
                @click="clearColor('color')"
              >
                默认
              </button>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ink mb-2">文字颜色</label>
            <div class="flex items-center gap-2">
              <input 
                type="color" 
                :value="form.textColor || '#ffffff'"
                @input="updateColor('textColor', $event.target.value)"
                class="w-10 h-10 rounded-lg border border-border cursor-pointer"
              />
              <input 
                v-model="form.textColor"
                type="text" 
                placeholder="留空=默认"
                @input="updateColor('textColor', form.textColor)"
                class="flex-1 px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
              />
              <button 
                class="px-3 py-2 text-xs font-medium text-muted bg-surface border border-border rounded-lg hover:bg-canvas transition-colors"
                @click="clearColor('textColor')"
              >
                默认
              </button>
            </div>
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <button 
            class="px-4 py-2 text-sm font-medium text-ink bg-surface border border-border rounded-lg hover:bg-canvas transition-colors"
            @click="extractColors"
          >
            识别模板里的固定颜色
          </button>
          <span class="text-xs text-muted">把写死的颜色一键变成可调</span>
        </div>
        
        <div v-if="extractedColors.length">
          <div class="flex flex-wrap gap-2">
            <div 
              v-for="(color, idx) in extractedColors" 
              :key="idx"
              class="flex items-center gap-2 px-3 py-2 bg-canvas border border-border rounded-lg"
            >
              <div 
                class="w-4 h-4 rounded border border-border"
                :style="{ backgroundColor: color }"
              ></div>
              <code class="text-xs font-mono text-ink">{{ color }}</code>
              <button 
                class="px-2 py-0.5 text-xs font-medium text-paleText-blue bg-pale-blue rounded hover:bg-blue-50 transition-colors"
                @click="applyColor(color, 'c')"
              >
                →气泡色
              </button>
              <button 
                class="px-2 py-0.5 text-xs font-medium text-paleText-green bg-pale-green rounded hover:bg-green-50 transition-colors"
                @click="applyColor(color, 't')"
              >
                →文字色
              </button>
            </div>
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-ink mb-2">预览</label>
          <div class="bg-canvas rounded-xl p-6 flex items-center justify-center min-h-[80px]">
            <span v-html="previewHtml"></span>
          </div>
        </div>
        
        <div class="flex items-center gap-3">
          <input 
            type="checkbox" 
            v-model="form.public"
            class="w-4 h-4 rounded border-border text-accent focus:ring-accent"
          />
          <span class="text-sm text-ink">所有人共用（公开给全站用户）</span>
        </div>
        
        <p class="text-xs text-muted">
          {{ isEditing 
            ? (form.public 
              ? '保存修改后：所有使用此气泡的人（公开 + 凭分享码）下次读正文都会同步更新。'
              : '保存修改后：仅凭分享码使用此气泡的人会同步更新（未公开）。')
            : '保存后此气泡加入你的列表；勾选公开则全站可见。'
          }}
        </p>
        
        <button 
          :disabled="!form.svg.trim() || loading"
          :class="[
            'w-full py-3 rounded-xl text-sm font-medium transition-colors',
            form.svg.trim() && !loading
              ? 'bg-ink text-white hover:bg-charcoal'
              : 'bg-border text-muted cursor-not-allowed'
          ]"
          @click="submit"
        >
          {{ loading ? '保存中...' : (isEditing ? '保存修改' : '创建') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { svgToImg, normalizePlaceholders, autoMapColors, extractColors as extract } from '@/utils/svgHelper'

const props = defineProps({
  style: {
    type: Object,
    default: null
  },
  admin: {
    type: Boolean,
    default: false
  },
  userList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'submit'])

const isEditing = computed(() => !!props.style)

const form = ref({
  name: '',
  desc: '',
  svg: '',
  color: '',
  textColor: '',
  public: false,
  userId: 0
})

const loading = ref(false)
const extractedColors = ref([])

watch(() => props.style, (newStyle) => {
  if (newStyle) {
    form.value = {
      name: newStyle.name || '',
      desc: newStyle.desc || '',
      svg: newStyle.rawSvg || newStyle.svg || '',
      color: newStyle.color || '',
      textColor: newStyle.textColor || '',
      public: !!newStyle.public,
      userId: newStyle.userId || newStyle.user_id || 0
    }
    // admin 模式下根据 userId 预填署名
    if (props.admin && form.value.userId) {
      const u = props.userList.find(u => u.id === form.value.userId)
      if (u) form.value.authorName = u.authorName || u.username || ''
    }
  } else {
    form.value = {
      name: '',
      desc: '',
      svg: '',
      color: '',
      textColor: '',
      public: false,
      userId: 0
    }
  }
  extractedColors.value = []
}, { immediate: true })

// admin 模式下切换作者时自动填充署名
watch(() => form.value.userId, (uid) => {
  if (!props.admin || !uid) return
  const u = props.userList.find(u => u.id === uid)
  if (u) {
    form.value.authorName = u.authorName || u.username || ''
  }
})

const previewHtml = computed(() => {
  return svgToImg(form.value.svg, 'h-16 w-auto', form.value.color, form.value.textColor)
})

const updateColor = (field, value) => {
  form.value[field] = value
}

const clearColor = (field) => {
  form.value[field] = ''
}

const preview = () => {}

const autoMap = () => {
  const result = autoMapColors(form.value.svg)
  form.value.svg = result.svg
  if (result.color && !form.value.color) {
    form.value.color = result.color
  }
  if (result.textColor && !form.value.textColor) {
    form.value.textColor = result.textColor
  }
}

const extractColors = () => {
  extractedColors.value = extract(form.value.svg)
  if (!extractedColors.value.length) {
    emit('toast', '未发现固定颜色（已是占位符或无颜色）')
  }
}

const applyColor = (color, type) => {
  form.value.svg = form.value.svg.split(color).join(type === 'c' ? '{c}' : '{t}')
  if (type === 'c') {
    form.value.color = color
  } else {
    form.value.textColor = color
  }
  extractColors()
  emit('toast', `已改为可调的${type === 'c' ? '气泡色' : '文字色'}`)
}

const submit = () => {
  if (!form.value.svg.trim()) {
    emit('toast', '请填写 SVG')
    return
  }
  
  loading.value = true
  
  setTimeout(() => {
    emit('submit', {
      ...form.value,
      id: props.style?.id
    })
    loading.value = false
  }, 500)
}
</script>

<style scoped>
@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-slide-up {
  animation: slideUp 300ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
