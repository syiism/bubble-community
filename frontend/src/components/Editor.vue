<template>
  <el-dialog
    v-model="visible"
    :title="isEditing ? '编辑气泡' : '添加气泡'"
    width="720px"
    :close-on-click-modal="false"
    top="5vh"
    class="editor-dialog"
    @closed="$emit('close')"
  >
    <div class="space-y-6">
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
        <label class="block text-sm font-medium text-ink mb-2">分区</label>
        <select v-model="form.category"
                class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink
                       focus:outline-none focus:border-accent transition-colors">
          <option value="original">原创</option>
          <option value="anime">动漫</option>
          <option value="classical">古风</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-ink mb-2">SVG 模板</label>
        <div class="text-xs text-muted mb-2">
          数字用 {n}；颜色用 {c}/{t}，也兼容 ${displayText}、{{color}} 等；粘贴自带颜色的也可以，会自动变可调
        </div>
        <div class="relative">
          <textarea
            v-model="form.svg"
            rows="12"
            placeholder='<svg ...>...{n}...</svg>'
            @input="preview"
            @change="autoMap"
            class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm font-mono text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors resize-none"
          ></textarea>
          <button
            v-if="form.svg.trim()"
            class="absolute top-2 right-2 w-8 h-8 flex items-center justify-center rounded-lg bg-surface border border-border text-muted hover:text-ink hover:bg-canvas transition-colors"
            title="复制 SVG 内容"
            @click="copySvg"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          </button>
        </div>
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
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElNotification } from 'element-plus'
import { svgToImg, normalizePlaceholders, autoMapColors, extractColors as extract } from '@/utils/svgHelper'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
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

const emit = defineEmits(['update:modelValue', 'close', 'submit', 'toast'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEditing = computed(() => !!props.style)

const form = ref({
  name: '',
  desc: '',
  svg: '',
  color: '',
  textColor: '',
  public: false,
  category: 'original',
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
      category: newStyle.category || 'original',
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
      category: 'original',
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

const copySvg = async () => {
  const svg = form.value.svg
  if (!svg.trim()) return
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
    ElNotification({ title: '已复制', message: 'SVG 内容已复制到剪贴板', type: 'success', duration: 3000 })
  } catch {
    ElNotification({ title: '复制失败', message: '请手动选中 SVG 内容复制', type: 'error', duration: 3000 })
  }
}

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

<style>
/* Element Plus 弹窗适配深色/浅色主题 */
/* 使用非 scoped 样式，因为 el-dialog 通过 Teleport 渲染到 body */
.editor-dialog {
  border-radius: 16px;
  --el-dialog-bg-color: rgb(var(--color-surface));
}

.editor-dialog .el-dialog__header {
  border-bottom: 1px solid rgb(var(--color-border));
  padding: 16px 24px;
}

.editor-dialog .el-dialog__title {
  font-size: 18px;
  font-weight: 500;
  color: rgb(var(--color-ink));
}

.editor-dialog .el-dialog__headerbtn {
  top: 16px;
  right: 24px;
  font-size: 18px;
}

.editor-dialog .el-dialog__headerbtn .el-dialog__close {
  color: rgb(var(--color-muted));
}

.editor-dialog .el-dialog__headerbtn .el-dialog__close:hover {
  color: rgb(var(--color-ink));
}

.editor-dialog .el-dialog__body {
  padding: 24px;
}

.editor-dialog .el-dialog__footer {
  display: none;
}

/* 移动端底部弹出 */
@media (max-width: 640px) {
  .editor-dialog {
    border-radius: 12px 12px 0 0;
    margin-bottom: 0 !important;
    margin-top: auto !important;
    position: fixed !important;
    bottom: 0 !important;
    top: auto !important;
    left: 0 !important;
    width: 100% !important;
    max-height: 90vh;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
  }

  .editor-dialog.el-dialog {
    --el-dialog-width: 100%;
  }

  .editor-dialog .el-dialog__header {
    flex-shrink: 0;
  }

  .editor-dialog .el-dialog__body {
    flex: 1;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
