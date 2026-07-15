<template>
  <div class="pb-4" style="padding-top: calc(5rem + env(safe-area-inset-top, 0px))">
    <div class="max-w-[1440px] mx-auto px-4 sm:px-6">
      <div class="mb-6 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight">图片转 SVG</h1>
        <p class="text-sm text-muted mt-1">浏览器本地转换 · 不上传图片</p>
      </div>

      <!-- Mobile tabs -->
      <div class="lg:hidden flex border-b border-border mb-4">
        <button class="flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors -mb-[1px]"
          :class="mobileTab === 'controls' ? 'text-accent border-accent' : 'text-muted border-transparent hover:text-ink'"
          @click="mobileTab = 'controls'">工具栏</button>
        <button class="flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors -mb-[1px]"
          :class="mobileTab === 'preview' ? 'text-accent border-accent' : 'text-muted border-transparent hover:text-ink'"
          @click="mobileTab = 'preview'">预览</button>
      </div>

      <div class="lg:grid lg:grid-cols-[380px_minmax(0,1fr)] gap-4">
        <!-- ===== 控制面板 ===== -->
        <aside :class="[
          'bg-surface/80 backdrop-blur-md border border-border rounded-xl shadow-sm p-3 space-y-2 lg:sticky lg:top-24 lg:self-start lg:max-h-[calc(100vh-16rem)] lg:min-h-[350px] lg:overflow-y-auto',
          mobileTab === 'controls' ? '' : 'max-lg:hidden'
        ]">
          <!-- 拖拽上传 -->
          <div
            class="min-h-[110px] p-3 rounded-xl border-2 border-dashed border-border grid place-items-center text-center cursor-pointer transition-all duration-200 hover:border-accent/50"
            :class="dragging ? 'border-accent bg-accent/5' : ''"
            @click="fileInputRef?.click()"
            @drop.prevent="onDrop"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @dragend.prevent="dragging = false"
            role="button"
            tabindex="0"
            @keydown.enter="fileInputRef?.click()"
            @keydown.space.prevent="fileInputRef?.click()"
          >
            <div>
              <svg class="w-8 h-8 mx-auto text-muted mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"/>
              </svg>
              <strong class="block text-sm text-ink">拖入图片或点击选择</strong>
              <span class="block mt-1.5 text-xs text-muted">也可以直接 Ctrl / ⌘ + V 粘贴截图</span>
            </div>
          </div>
          <input ref="fileInputRef" type="file" accept=".png,.jpg,.jpeg,.webp,.gif,.bmp,.svg,.avif,.ico,image/png,image/jpeg,image/webp,image/gif,image/bmp,image/svg+xml,image/avif,image/x-icon" class="hidden" @change="onFileChange" />

          <!-- 进度条 -->
          <div class="h-1 bg-border rounded-full overflow-hidden" v-show="busy">
            <div class="h-full w-1/3 rounded-full bg-gradient-to-r from-accent to-accent/60 animate-load"></div>
          </div>

          <!-- 转换模式 -->
          <section class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">转换模式</h3>
            <div>
              <select v-model="mode" @change="scheduleRender()" class="w-full px-3 py-2.5 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors">
                <option value="color">彩色块矢量</option>
                <option value="embed">保真嵌入（非描摹）</option>
                <option value="gif">GIF 动态 SVG（CSS 逐帧）</option>
              </select>
            </div>
          </section>

          <!-- 矢量化设置 -->
          <section v-if="isColor" class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">矢量化设置</h3>
            <div class="space-y-2">
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>采样精度</span><span class="text-ink font-mono tabular-nums">{{ detail }} px</span></label>
                <NumStepper v-model="detail" @update:model-value="scheduleRender()" :min="24" :max="240" />
              </div>
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>颜色数量</span><span class="text-ink font-mono tabular-nums">{{ colors }}</span></label>
                <NumStepper v-model="colors" @update:model-value="scheduleRender()" :min="2" :max="16" />
              </div>
              <div class="flex items-center justify-between text-xs text-muted">
                <span>抖动混色</span>
                <label class="relative inline-block w-10 h-5 cursor-pointer">
                  <input type="checkbox" class="opacity-0 w-0 h-0" :checked="dither" @change="dither = $event.target.checked; scheduleRender()" />
                  <span class="absolute inset-0 rounded-full bg-border transition-colors" :class="dither ? 'bg-accent' : ''"></span>
                  <span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm" :class="dither ? 'translate-x-5' : ''"></span>
                </label>
              </div>
            </div>
          </section>

          <!-- 保真嵌入压缩 -->
          <section v-if="isEmbed" class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">保真嵌入压缩</h3>
            <div class="space-y-2">
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>输出最长边</span><span class="text-ink font-mono tabular-nums">{{ embedMaxSideLabel }}</span></label>
                <NumStepper v-model="embedMaxSide" @update:model-value="scheduleRender()" :min="32" :max="2048" :step="16" />
              </div>
              <div>
                <label class="text-xs text-muted mb-1.5 block">嵌入格式</label>
                <select v-model="embedFormat" @change="scheduleRender()" class="w-full px-3 py-2.5 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors">
                  <option value="image/webp">WebP（体积最小，推荐）</option>
                  <option value="image/jpeg">JPEG（适合照片）</option>
                  <option value="image/png">PNG（保留透明背景）</option>
                </select>
              </div>
              <div v-if="embedFormat !== 'image/png'">
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>压缩质量</span><span class="text-ink font-mono tabular-nums">{{ embedQuality }}%</span></label>
                <NumStepper v-model="embedQuality" @update:model-value="scheduleRender()" :min="10" :max="100" />
              </div>
              <div class="flex items-center justify-between text-xs text-muted">
                <span>不放大小尺寸原图</span>
                <label class="relative inline-block w-10 h-5 cursor-pointer">
                  <input type="checkbox" class="opacity-0 w-0 h-0" :checked="embedNoUpscale" @change="embedNoUpscale = $event.target.checked; scheduleRender()" />
                  <span class="absolute inset-0 rounded-full bg-border transition-colors" :class="embedNoUpscale ? 'bg-accent' : ''"></span>
                  <span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm" :class="embedNoUpscale ? 'translate-x-5' : ''"></span>
                </label>
              </div>
              <p class="text-xs text-muted leading-relaxed">{{ embedHint }}</p>
            </div>
          </section>

          <!-- GIF 动态 SVG -->
          <section v-if="isGif" class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">GIF 动态 SVG</h3>
            <div class="space-y-2">
              <div class="p-2 rounded-xl border border-dashed border-accent/30 bg-accent/5 text-xs text-accent/80 leading-relaxed">新版只使用 CSS 逐帧动画：每帧作为独立图层，由 SVG 内部 CSS 切换显示。</div>
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>输出最长边</span><span class="text-ink font-mono tabular-nums">{{ gifMaxSideLabel }}</span></label>
                <NumStepper v-model="gifMaxSide" @update:model-value="scheduleRender()" :min="24" :max="768" :step="8" />
              </div>
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>抽帧间隔</span><span class="text-ink font-mono tabular-nums">{{ gifFrameStepLabel }}</span></label>
                <NumStepper v-model="gifFrameStep" @update:model-value="scheduleRender()" :min="1" :max="20" />
              </div>
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>最多输出帧数</span><span class="text-ink font-mono tabular-nums">{{ gifMaxFrames }} 帧</span></label>
                <NumStepper v-model="gifMaxFrames" @update:model-value="scheduleRender()" :min="2" :max="120" />
              </div>
              <div>
                <label class="text-xs text-muted mb-1.5 block">帧图片格式</label>
                <select v-model="gifFormat" @change="scheduleRender()" class="w-full px-3 py-2.5 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors">
                  <option value="image/webp">WebP（推荐，支持透明）</option>
                  <option value="image/png">PNG（清晰但较大）</option>
                  <option value="image/jpeg">JPEG（适合无透明背景）</option>
                </select>
              </div>
              <div v-if="gifFormat !== 'image/png'">
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>帧压缩质量</span><span class="text-ink font-mono tabular-nums">{{ gifQuality }}%</span></label>
                <NumStepper v-model="gifQuality" @update:model-value="scheduleRender()" :min="10" :max="100" />
              </div>
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>播放速度</span><span class="text-ink font-mono tabular-nums">{{ gifSpeed }}%</span></label>
                <NumStepper v-model="gifSpeed" @update:model-value="scheduleRender()" :min="25" :max="300" :step="5" />
              </div>
              <div class="flex items-center justify-between text-xs text-muted">
                <span>无限循环</span>
                <label class="relative inline-block w-10 h-5 cursor-pointer">
                  <input type="checkbox" class="opacity-0 w-0 h-0" :checked="gifInfinite" @change="gifInfinite = $event.target.checked; scheduleRender()" />
                  <span class="absolute inset-0 rounded-full bg-border transition-colors" :class="gifInfinite ? 'bg-accent' : ''"></span>
                  <span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm" :class="gifInfinite ? 'translate-x-5' : ''"></span>
                </label>
              </div>
              <p class="text-xs text-muted leading-relaxed">{{ gifInfoText }}</p>
            </div>
          </section>

          <!-- 背景与清理 -->
          <section v-if="isColor" class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">背景与清理</h3>
            <div class="space-y-2">
              <div class="flex items-center justify-between text-xs text-muted">
                <span>移除接近白色背景</span>
                <label class="relative inline-block w-10 h-5 cursor-pointer">
                  <input type="checkbox" class="opacity-0 w-0 h-0" :checked="removeWhite" @change="removeWhite = $event.target.checked; scheduleRender()" />
                  <span class="absolute inset-0 rounded-full bg-border transition-colors" :class="removeWhite ? 'bg-accent' : ''"></span>
                  <span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm" :class="removeWhite ? 'translate-x-5' : ''"></span>
                </label>
              </div>
              <div v-if="removeWhite">
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>白色容差</span><span class="text-ink font-mono tabular-nums">{{ whiteTolerance }}</span></label>
                <NumStepper v-model="whiteTolerance" @update:model-value="scheduleRender()" :min="2" :max="90" />
              </div>
              <div>
                <label class="flex justify-between text-xs text-muted mb-1.5"><span>透明度阈值</span><span class="text-ink font-mono tabular-nums">{{ alphaThreshold }}</span></label>
                <NumStepper v-model="alphaThreshold" @update:model-value="scheduleRender()" :min="0" :max="254" />
              </div>
            </div>
          </section>

          <!-- 动态文字 -->
          <section class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">动态文字</h3>
            <div class="p-2 rounded-xl border border-dashed border-accent/30 bg-accent/5 text-xs text-accent/80 leading-relaxed mb-2">在右侧 SVG 结果中直接按住文字拖动。文字和颜色使用当前预览值写入 SVG。</div>
            <div class="space-y-2">
              <div class="grid grid-cols-2 gap-1.5">
                <div><label class="text-xs text-muted mb-1 block">预览文字</label><input v-model="previewText" type="text" maxlength="12" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" @input="refreshTextPreview()" /></div>
                <div><label class="text-xs text-muted mb-1 block">预览颜色</label><input v-model="previewColor" type="color" class="w-full h-9 px-1 py-1 bg-canvas border border-border rounded-xl cursor-pointer" @input="refreshTextPreview()" /></div>
              </div>
              <div class="grid grid-cols-3 gap-1.5">
                <div><label class="text-xs text-muted mb-1 block">X</label><input v-model.number="textX" type="number" step="0.1" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" @input="onTextChange()" /></div>
                <div><label class="text-xs text-muted mb-1 block">Y</label><input v-model.number="textY" type="number" step="0.1" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" @input="onTextChange()" /></div>
                <div><label class="text-xs text-muted mb-1 block">字号</label><input v-model.number="fontSize" type="number" min="1" step="1" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" @input="onTextChange()" /></div>
              </div>
              <div class="grid grid-cols-2 gap-1.5">
                <div><label class="text-xs text-muted mb-1 block">字体</label><input v-model="fontFamily" type="text" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" @input="onTextChange()" /></div>
                <div><label class="text-xs text-muted mb-1 block">字重</label><select v-model="fontWeight" @change="onTextChange()" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors"><option value="400">400</option><option value="600">600</option><option value="700">700</option><option value="800">800</option><option value="900" selected>900</option></select></div>
              </div>
              <div class="grid grid-cols-2 gap-1.5">
                <div><label class="text-xs text-muted mb-1 block">文字锚点</label><select v-model="textAnchor" @change="onTextChange()" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors"><option value="start">左侧</option><option value="middle" selected>居中</option><option value="end">右侧</option></select></div>
                <div class="flex items-end"><button class="w-full px-3 py-2 rounded-xl border border-border text-sm text-muted hover:text-ink hover:bg-canvas transition-colors" @click="resetTextPosition">恢复示例位置</button></div>
              </div>
            </div>
          </section>

          <!-- 气泡压缩包 -->
          <section class="pt-2 border-t border-border">
            <h3 class="text-xs font-medium text-muted uppercase tracking-wider mb-2">气泡压缩包</h3>
            <div class="space-y-2">
              <div class="grid grid-cols-2 gap-1.5">
                <div><label class="text-xs text-muted mb-1 block">名称</label><input v-model="bubbleName" type="text" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" /></div>
                <div><label class="text-xs text-muted mb-1 block">sizeScale</label><input v-model.number="sizeScale" type="number" min="0.01" step="0.05" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" /></div>
              </div>
              <div><label class="text-xs text-muted mb-1 block">压缩包内目录名</label><input v-model="dirName" type="text" class="w-full px-3 py-2 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors" /></div>
              
            </div>
          </section>

          <!-- 颜色调色板 -->
          <div v-if="palette.length" class="flex flex-wrap gap-1.5">
            <span v-for="(c, i) in palette" :key="i" class="w-6 h-6 rounded-lg border border-border/50" :style="{ background: rgbHex(...c) }" :title="rgbHex(...c)"></span>
          </div>

          <!-- 操作按钮 -->
          <div class="grid grid-cols-2 gap-2 pt-2">
            <button :disabled="!currentSvg || busy" class="px-3 py-2 rounded-xl border border-border text-sm font-medium text-muted hover:text-ink hover:bg-canvas transition-colors disabled:opacity-40 disabled:cursor-not-allowed" @click="onCopy">复制 SVG 模板</button>
            <button :disabled="!currentSvg || busy" class="px-3 py-2 rounded-xl text-sm font-medium text-white bg-accent hover:bg-accent/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed" @click="onDownload">下载 SVG</button>
            <button :disabled="!currentSvg || busy" class="col-span-2 px-3 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-cyan-700 to-violet-600 hover:from-cyan-600 hover:to-violet-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed" @click="createBubbleFromTool">→ 创建气泡</button>
          </div>

          <!-- 下载结果 -->
          <div v-if="downloadResult" class="p-3 rounded-xl border border-accent/30 bg-accent/5 text-xs leading-relaxed">
            <strong class="block text-accent/90 mb-1">{{ downloadResult.label }}</strong>
            <p class="text-muted mb-2">若没有自动出现下载，请点击下面的按钮。手机上也可以长按按钮后选择下载或打开。</p>
            <a :href="downloadResult.url" :download="downloadResult.filename" class="block w-full text-center py-2 rounded-xl bg-cyan-200 text-cyan-900 font-bold text-sm hover:brightness-105 transition-all">{{ '手动保存 ' + downloadResult.filename }}</a>
          </div>
        </aside>

        <!-- ===== 预览面板 ===== -->
        <section :class="[
          'bg-surface/80 backdrop-blur-md border border-border rounded-xl shadow-sm p-4 lg:max-h-[calc(100vh-16rem)] lg:min-h-[350px] lg:flex lg:flex-col',
          mobileTab === 'preview' ? '' : 'max-lg:hidden'
        ]">
          <div class="flex items-center justify-between gap-3 mb-3 flex-wrap">
            <h2 class="text-sm font-medium text-ink">预览</h2>
            <div class="flex flex-wrap gap-1.5">
              <span class="px-2.5 py-1 rounded-full border border-border bg-canvas/50 text-xs text-muted">{{ sizeStat }}</span>
              <span class="px-2.5 py-1 rounded-full border border-border bg-canvas/50 text-xs text-muted">{{ vectorStat }}</span>
              <span v-if="embedStat" class="px-2.5 py-1 rounded-full border border-border bg-canvas/50 text-xs text-muted">{{ embedStat }}</span>
              <span v-if="gifStat" class="px-2.5 py-1 rounded-full border border-border bg-canvas/50 text-xs text-muted">{{ gifStat }}</span>
              <span class="px-2.5 py-1 rounded-full border border-border bg-canvas/50 text-xs text-muted">{{ fileStat }}</span>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 min-h-0 flex-1">
            <!-- 原图 -->
            <div class="rounded-xl border border-border overflow-hidden flex flex-col bg-canvas checkerboard">
              <div class="flex items-center justify-between px-3 py-2 bg-surface/50 border-b border-border/50">
                <b class="text-xs text-ink">原图</b>
                <span class="text-xs text-muted">{{ originalMeta }}</span>
              </div>
              <div class="flex-1 grid place-items-center p-3 overflow-auto min-h-0">
                <img v-if="sourceIsGif && sourceDataUrl" :src="sourceDataUrl" class="max-w-full max-h-[520px] object-contain drop-shadow-lg" />
                <canvas v-else-if="sourceImage" ref="originalCanvasRef" class="max-w-full max-h-[520px] object-contain drop-shadow-lg"></canvas>
                <div v-else class="text-xs text-muted text-center leading-relaxed">选择图片后将在这里显示原图</div>
              </div>
            </div>

            <!-- SVG 结果 -->
            <div class="rounded-xl border border-border overflow-hidden flex flex-col bg-canvas checkerboard">
              <div class="flex items-center justify-between px-3 py-2 bg-surface/50 border-b border-border/50">
                <b class="text-xs text-ink">SVG 结果</b>
                <span class="text-xs text-muted">{{ resultMeta }}</span>
              </div>
              <div ref="resultStageRef" class="flex-1 grid place-items-center p-3 overflow-auto min-h-0">
                <div v-if="currentSvgPreview" v-html="currentSvgPreview" class="[&_svg]:max-w-full [&_svg]:max-h-[520px] [&_svg]:object-contain [&_svg]:drop-shadow-lg [&_svg]:w-full [&_svg]:h-auto"></div>
                <div v-else class="text-xs text-muted text-center leading-relaxed">调整参数后会自动生成矢量预览</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import {
  fileToDataUrl, fileToArrayBuffer, loadHtmlImage, normalizeWithImageBitmap,
  parseGif, fmtBytes, escapeXml, rgbHex, roundCoord, safeFileName,
  collectSamples, kMeans, quantize, mergeRuns, buildPathSvg,
  buildEmbedSvgJob, buildGifFrameSvgJob,
  getSvgGeometry, adaptTextToNewGeometry,
  composeSvgTemplate,
  buildBubbleJson, makeSingleFileZipStored, makeSingleFileZip, triggerDownload,
  dataUrlByteSize, canvasToBlob, blobToDataUrl
} from '@/utils/imgToSvg'

const btnCls = 'w-7 h-7 flex items-center justify-center rounded-lg border border-border text-muted hover:text-ink hover:bg-canvas transition-colors text-sm shrink-0'
const inputCls = 'w-full px-2 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink text-center font-mono tabular-nums focus:outline-none focus:border-accent transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'

const NumStepper = defineComponent({
  name: 'NumStepper',
  props: {
    modelValue: { type: Number, required: true },
    min: { type: Number, required: true },
    max: { type: Number, required: true },
    step: { type: Number, default: 1 }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => {
      const inc = () => emit('update:modelValue', Math.min(props.max, (props.modelValue || 0) + props.step))
      const dec = () => emit('update:modelValue', Math.max(props.min, (props.modelValue || 0) - props.step))
      const onInput = (e) => {
        let v = parseFloat(e.target.value)
        if (isNaN(v)) v = props.min
        emit('update:modelValue', Math.max(props.min, Math.min(props.max, v)))
      }
      return h('div', { class: 'flex items-center gap-1' }, [
        h('button', { type: 'button', class: btnCls, onClick: dec, disabled: props.modelValue <= props.min }, '−'),
        h('input', { type: 'number', class: inputCls, value: props.modelValue, onInput, min: props.min, max: props.max, step: props.step }),
        h('button', { type: 'button', class: btnCls, onClick: inc, disabled: props.modelValue >= props.max }, '+'),
      ])
    }
  }
})

const router = useRouter()
const { show: toast } = useToast()

function createBubbleFromTool() {
  if (!currentSvg.value) return
  try {
    sessionStorage.setItem('img_to_svg_svg', currentSvg.value)
    sessionStorage.setItem('img_to_svg_params', JSON.stringify({
      previewText: previewText.value,
      previewColor: previewColor.value,
      fontSize: fontSize.value,
      fontFamily: fontFamily.value,
      fontWeight: fontWeight.value,
      textAnchor: textAnchor.value,
    }))
    router.push({ path: '/', query: { 'create-from-tool': '1' } })
  } catch (e) {
    toast('跳转失败：' + (e.message || '未知错误'), 'error')
  }
}

// ---- Image state ----
const sourceImage = ref(null)
const sourceDataUrl = ref('')
const sourceName = ref('image')
const sourceFileSize = ref(0)
const sourceFileBuffer = ref(null)
const sourceIsGif = ref(false)
const gifData = ref(null)

// ---- SVG state ----
const currentSvg = ref('')
const currentBaseSvg = ref('')
const currentSvgPreview = ref('')
const palette = ref([])

// ---- UI state ----
const mode = ref('color')
const busy = ref(false)
const renderToken = ref(0)
const textAutoPosition = ref(true)
const previewAnimTimer = ref(0)
const dragging = ref(false)
const mobileTab = ref('controls')

// ---- Vector params ----
const detail = ref(112)
const colors = ref(8)
const dither = ref(false)

// ---- Embed params ----
const embedMaxSide = ref(512)
const embedFormat = ref('image/webp')
const embedQuality = ref(72)
const embedNoUpscale = ref(true)

// ---- GIF params ----
const gifMaxSide = ref(128)
const gifFrameStep = ref(1)
const gifMaxFrames = ref(40)
const gifFormat = ref('image/webp')
const gifQuality = ref(70)
const gifSpeed = ref(100)
const gifInfinite = ref(true)

// ---- Cleanup params ----
const removeWhite = ref(false)
const whiteTolerance = ref(24)
const alphaThreshold = ref(16)

// ---- Text params ----
const previewText = ref('88')
const previewColor = ref('#030000')
const textX = ref(0)
const textY = ref(0)
const fontSize = ref(100)
const fontFamily = ref('Arial,sans-serif')
const fontWeight = ref('900')
const textAnchor = ref('middle')

// ---- ZIP params ----
const bubbleName = ref('气泡')
const dirName = ref('自定义段评气泡_2')
const sizeScale = ref(0.5)
const dayEmphasisColor = ref('#030000')
const dayNormalColor = ref('#808080')
const nightEmphasisColor = ref('#140000')
const nightNormalColor = ref('#808080')

// ---- Download result ----
const downloadResult = ref(null)

// ---- DOM refs ----
const fileInputRef = ref(null)
const resultStageRef = ref(null)
const originalCanvasRef = ref(null)

// ---- Computed ----
const isColor = computed(() => mode.value === 'color')
const isEmbed = computed(() => mode.value === 'embed')
const isGif = computed(() => mode.value === 'gif')

const sizeStat = computed(() => {
  const img = sourceImage.value
  if (!img) return '尚未载入图片'
  let text = `${img.naturalWidth} × ${img.naturalHeight}`
  if (sourceFileSize.value) text += ` · 原图 ${fmtBytes(sourceFileSize.value)}`
  return text
})

const originalMeta = computed(() => {
  const img = sourceImage.value
  if (!img) return '—'
  let text = `${img.naturalWidth} × ${img.naturalHeight}`
  if (sourceIsGif.value && gifData.value) {
    text += ` · ${gifData.value.frames.length} 帧 · ${(gifData.value.duration / 1000).toFixed(2)}s`
  }
  return text
})

const resultMeta = computed(() => {
  if (!currentSvg.value) return '—'
  return `${detail.value}px 采样`
})

const vectorStat = computed(() => {
  if (!currentSvg.value) return '0 个矢量块'
  return '—'
})

const embedStat = computed(() => null)
const gifStat = computed(() => null)

const fileStat = computed(() => {
  if (!currentSvg.value) return 'SVG 0 KB'
  return `SVG ${fmtBytes(new Blob([currentSvg.value]).size)}`
})

const embedMaxSideLabel = computed(() => {
  const img = sourceImage.value
  if (!img) return `${embedMaxSide.value} px`
  const naturalMax = Math.max(img.naturalWidth, img.naturalHeight)
  const scale = embedNoUpscale.value ? Math.min(1, embedMaxSide.value / naturalMax) : embedMaxSide.value / naturalMax
  const outW = Math.max(1, Math.round(img.naturalWidth * scale))
  const outH = Math.max(1, Math.round(img.naturalHeight * scale))
  return `${Math.max(outW, outH)} px · ${outW}×${outH}`
})

const gifMaxSideLabel = computed(() => {
  const img = sourceImage.value
  if (!img) return `${gifMaxSide.value} px`
  const naturalMax = Math.max(img.naturalWidth, img.naturalHeight)
  const scale = Math.min(1, gifMaxSide.value / naturalMax)
  const w = Math.max(1, Math.round(img.naturalWidth * scale))
  const h = Math.max(1, Math.round(img.naturalHeight * scale))
  return `${Math.max(w, h)} px · ${w}×${h}`
})

const gifFrameStepLabel = computed(() => {
  return Number(gifFrameStep.value) === 1 ? '每帧' : `每 ${gifFrameStep.value} 帧取 1 帧`
})

const embedHint = computed(() => {
  const formatName = embedFormat.value === 'image/webp' ? 'WebP' : embedFormat.value === 'image/jpeg' ? 'JPEG' : 'PNG'
  if (formatName === 'PNG') return 'PNG 保留透明背景，但通常比 WebP/JPEG 大，且压缩质量滑块不生效。'
  return formatName === 'JPEG'
    ? '降低最长边和质量可显著减小文件；JPEG 会把透明区域填充为白色。'
    : 'WebP 通常体积最小并支持透明背景，适合小尺寸图片。'
})

const gifInfoText = computed(() => {
  if (!sourceIsGif.value) return '请先载入 GIF 图片。载入后会自动切换到 GIF 动态 SVG 模式。'
  if (!gifData.value) return '该 GIF 无法完成逐帧解析，请尝试重新导出为标准 GIF89a。'
  const effectiveStep = Math.max(Number(gifFrameStep.value), Math.ceil(gifData.value.frames.length / Number(gifMaxFrames.value)))
  const outputFrames = Math.ceil(gifData.value.frames.length / effectiveStep)
  return `原 GIF：${gifData.value.frames.length} 帧 · ${(gifData.value.duration / 1000).toFixed(2)} 秒；预计输出 ${outputFrames} 帧（有效间隔 ${effectiveStep}），导出使用 CSS 关键帧。`
})

// ---- Methods ----

function scheduleRender() {
  if (!sourceImage.value) return
  clearTimeout(scheduleRender._timer)
  scheduleRender._timer = setTimeout(renderSvg, mode.value === 'gif' ? 360 : 140)
}

async function loadFile(file) {
  if (!file) return
  const ext = (file.name || '').split('.').pop().toLowerCase()
  const commonImageExts = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg', 'avif', 'ico']
  const looksLikeImage = (file.type || '').startsWith('image/') || commonImageExts.includes(ext)
  if (!looksLikeImage) {
    toast('请选择 PNG、JPG、WebP、GIF、BMP、SVG 或 AVIF 图片')
    return
  }
  if (['heic', 'heif'].includes(ext) || /heic|heif/i.test(file.type || '')) {
    toast('当前浏览器通常无法读取 HEIC，请先转成 JPG 或 PNG', 'warning')
    return
  }

  busy.value = true
  sourceName.value = (file.name || 'image').replace(/\.[^.]+$/, '')
  sourceFileSize.value = Number(file.size) || 0
  sourceFileBuffer.value = null
  sourceIsGif.value = false
  gifData.value = null
  textAutoPosition.value = true
  bubbleName.value = sourceName.value || '气泡'

  try {
    const gifCandidate = ext === 'gif' || /image\/gif/i.test(file.type || '')
    if (gifCandidate) {
      sourceFileBuffer.value = await fileToArrayBuffer(file)
      const signature = String.fromCharCode(...new Uint8Array(sourceFileBuffer.value).slice(0, 6))
      sourceIsGif.value = signature === 'GIF87a' || signature === 'GIF89a'
      if (sourceIsGif.value) {
        try {
          gifData.value = parseGif(sourceFileBuffer.value)
        } catch (gifError) {
          console.warn('GIF 逐帧解析失败：', gifError)
          gifData.value = null
        }
        mode.value = 'gif'
      }
    }
    if (!sourceIsGif.value && mode.value === 'gif') mode.value = 'color'

    let img
    try {
      sourceDataUrl.value = await fileToDataUrl(file)
      if (!sourceDataUrl.value) throw new Error('读取结果为空')
      img = await loadHtmlImage(sourceDataUrl.value)
    } catch (primaryError) {
      if (sourceIsGif.value) throw primaryError
      console.warn('Data URL 解码失败，尝试 createImageBitmap：', primaryError)
      const normalized = await normalizeWithImageBitmap(file)
      sourceDataUrl.value = normalized.dataUrl
      img = normalized.image
    }

    if (!img.naturalWidth || !img.naturalHeight) throw new Error('图片尺寸无效')
    sourceImage.value = img

    await nextTick()
    showOriginalPreview()

    await renderSvg()
  } catch (err) {
    console.error('图片读取失败：', err)
    sourceImage.value = null
    sourceDataUrl.value = ''
    sourceFileSize.value = 0
    sourceFileBuffer.value = null
    sourceIsGif.value = false
    gifData.value = null
    currentSvg.value = ''
    currentBaseSvg.value = ''
    currentSvgPreview.value = ''
    toast(`图片读取失败：${err && err.message ? err.message : '未知错误'}`, 'error')
  } finally {
    busy.value = false
  }
}

function showOriginalPreview() {
  const img = sourceImage.value
  if (!img) return
  if (sourceIsGif.value) return
  const canvas = originalCanvasRef.value
  if (!canvas) return
  const maxPreviewSide = 1800
  const scale = Math.min(1, maxPreviewSide / Math.max(img.naturalWidth, img.naturalHeight))
  const w = Math.max(1, Math.round(img.naturalWidth * scale))
  const h = Math.max(1, Math.round(img.naturalHeight * scale))
  canvas.width = w
  canvas.height = h
  canvas.setAttribute('aria-label', '原图预览')
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, w, h)
  ctx.drawImage(img, 0, 0, w, h)
}

async function renderSvg() {
  const img = sourceImage.value
  if (!img) return
  const token = ++renderToken.value
  busy.value = true
  await new Promise(r => setTimeout(r, 20))

  try {
    let svg = '', paletteColors = []
    if (mode.value === 'gif') {
      const opts = {
        maxSide: Number(gifMaxSide.value),
        frameStep: Number(gifFrameStep.value),
        maxFrames: Number(gifMaxFrames.value),
        format: gifFormat.value,
        quality: Number(gifQuality.value),
        speed: Number(gifSpeed.value),
        infinite: gifInfinite.value
      }
      const gifResult = await buildGifFrameSvgJob(gifData.value, () => renderToken.value === token ? true : null, opts)
      if (!gifResult) return
      svg = gifResult.svg
    } else if (mode.value === 'embed') {
      const opts = {
        maxSide: Number(embedMaxSide.value),
        noUpscale: embedNoUpscale.value,
        format: embedFormat.value,
        quality: Number(embedQuality.value)
      }
      const embedResult = await buildEmbedSvgJob(img, opts)
      svg = embedResult.svg
    } else {
      const maxSide = Number(detail.value)
      const scale = maxSide / Math.max(img.naturalWidth, img.naturalHeight)
      const w = Math.max(1, Math.round(img.naturalWidth * scale))
      const h = Math.max(1, Math.round(img.naturalHeight * scale))
      const canvas = document.createElement('canvas')
      canvas.width = w; canvas.height = h
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.clearRect(0, 0, w, h)
      ctx.drawImage(img, 0, 0, w, h)
      const imageData = ctx.getImageData(0, 0, w, h)
      const opts = {
        alphaThreshold: Number(alphaThreshold.value),
        removeWhite: removeWhite.value,
        whiteTolerance: Number(whiteTolerance.value),
        dither: dither.value
      }
      const samples = collectSamples(imageData.data, opts.alphaThreshold, opts.removeWhite, opts.whiteTolerance)
      paletteColors = kMeans(samples, Number(colors.value))
      const map = quantize(imageData.data, w, h, paletteColors, opts)
      const rects = mergeRuns(map, w, h)
      svg = buildPathSvg(rects, paletteColors, w, h, img.naturalWidth, img.naturalHeight)
    }

    palette.value = paletteColors

    const adapted = adaptTextToNewGeometry(currentBaseSvg.value, svg, textX.value, textY.value, fontSize.value, textAutoPosition.value)
    if (adapted) {
      textX.value = adapted.textX
      textY.value = adapted.textY
      fontSize.value = adapted.fontSize
    }
    currentBaseSvg.value = svg
    ensureTextPosition()
    refreshTextTemplate(true)
  } catch (err) {
    console.error(err)
    currentSvg.value = ''
    currentBaseSvg.value = ''
    currentSvgPreview.value = ''
    toast(`SVG 生成失败：${err && err.message ? err.message : '未知错误'}`, 'error')
  } finally {
    if (renderToken.value === token) busy.value = false
  }
}

function ensureTextPosition() {
  if (!textAutoPosition.value || !currentBaseSvg.value) return
  const box = getSvgGeometry(currentBaseSvg.value)
  textX.value = roundCoord(box.minX + box.width * (670 / 1024))
  textY.value = roundCoord(box.minY + box.height * (400 / 864))
  fontSize.value = Math.max(1, roundCoord(box.height * (250 / 864)))
  textAutoPosition.value = false
}

function resetTextPosition() {
  if (!currentBaseSvg.value) return
  const box = getSvgGeometry(currentBaseSvg.value)
  textX.value = roundCoord(box.minX + box.width * (670 / 1024))
  textY.value = roundCoord(box.minY + box.height * (400 / 864))
  fontSize.value = Math.max(1, roundCoord(box.height * (250 / 864)))
  textAutoPosition.value = false
  refreshTextTemplate(true)
}

function refreshTextTemplate(redraw = true) {
  if (!currentBaseSvg.value) return
  try {
    currentSvg.value = composeSvgTemplate(currentBaseSvg.value, textX.value, textY.value, fontSize.value, fontFamily.value, fontWeight.value, textAnchor.value, previewText.value, previewColor.value)
    if (redraw) refreshTextPreview()
  } catch (e) {
    console.error(e)
  }
}

function refreshTextPreview() {
  if (!currentSvg.value) return
  currentSvgPreview.value = currentSvg.value
  downloadResult.value = null
}

function onTextChange() {
  textAutoPosition.value = false
  refreshTextTemplate(true)
}

function stopPreviewAnimation() {
  if (previewAnimTimer.value) clearTimeout(previewAnimTimer.value)
  previewAnimTimer.value = 0
}

function startPreviewAnimation(svg) {
  stopPreviewAnimation()
  const frames = Array.from(svg.querySelectorAll('[data-gif-frame]'))
  if (frames.length < 2) return
  frames.forEach(frame => {
    frame.style.animation = 'none'
    frame.style.opacity = '0'
  })
  let index = 0
  const tick = () => {
    if (!frames.length) return
    frames.forEach((frame, i) => frame.style.opacity = i === index ? '1' : '0')
    const duration = Math.max(16, Number(frames[index].getAttribute('data-frame-duration')) || 100)
    index = (index + 1) % frames.length
    previewAnimTimer.value = setTimeout(tick, duration)
  }
  tick()
}

function bindTextDrag(svg) {
  const texts = svg.querySelectorAll('text')
  const text = texts[texts.length - 1]
  if (!text) return
  text.style.cursor = 'grab'
  text.style.userSelect = 'none'
  text.style.touchAction = 'none'
  let dragging = false

  const move = (event) => {
    if (!dragging || !svg.getScreenCTM()) return
    const point = svg.createSVGPoint()
    point.x = event.clientX
    point.y = event.clientY
    const local = point.matrixTransform(svg.getScreenCTM().inverse())
    const x = roundCoord(local.x)
    const y = roundCoord(local.y)
    textX.value = x
    textY.value = y
    text.setAttribute('x', x)
    text.setAttribute('y', y)
    textAutoPosition.value = false
    refreshTextTemplate(false)
  }

  const stop = (event) => {
    if (!dragging) return
    dragging = false
    text.style.cursor = 'grab'
    if (svg.releasePointerCapture && svg.hasPointerCapture && svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId)
    refreshTextTemplate(false)
  }

  text.addEventListener('pointerdown', (event) => {
    dragging = true
    text.style.cursor = 'grabbing'
    if (svg.setPointerCapture) svg.setPointerCapture(event.pointerId)
    event.preventDefault()
    event.stopPropagation()
  })
  svg.addEventListener('pointermove', move)
  svg.addEventListener('pointerup', stop)
  svg.addEventListener('pointercancel', stop)
}

function getCopySvg() {
  let svg = currentSvg.value
  svg = svg.replace(/^\s*<\?xml[^>]*\?>\s*/i, '').replace(/^\s*<!DOCTYPE[\s\S]*?>\s*/i, '')
  return svg.trim()
}

async function onCopy() {
  if (!currentSvg.value) return
  const content = getCopySvg()
  try {
    await navigator.clipboard.writeText(content)
    toast('SVG 模板已复制')
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = content
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
      toast('SVG 模板已复制')
    } catch {
      toast('复制失败，请使用下载按钮', 'warning')
    }
  }
}

function onDownload() {
  if (!currentSvg.value) return
  const filename = `${safeFileName(sourceName.value, 'vectorized')}.svg`
  triggerDownload(new Blob([currentSvg.value], { type: 'image/svg+xml;charset=utf-8' }), filename, 'SVG')
  toast('SVG 已生成；若未自动下载，请点击下方手动保存')
}

function onPackage() {
  if (!currentSvg.value) return
  try {
    const opts = {
      dirName: dirName.value,
      bubbleName: bubbleName.value,
      sizeScale: sizeScale.value,
      dayEmphasisColor: dayEmphasisColor.value,
      dayNormalColor: dayNormalColor.value,
      nightEmphasisColor: nightEmphasisColor.value,
      nightNormalColor: nightNormalColor.value
    }
    const { dirName: dir, json } = buildBubbleJson(currentSvg.value, opts)
    const zip = makeSingleFileZipStored(`${dir}/bubble.json`, json)
    const filename = `${safeFileName(bubbleName.value || sourceName.value, '气泡')}.zip`
    const { url } = triggerDownload(zip, filename, 'ZIP 压缩包')
    downloadResult.value = { url, filename, label: `ZIP 已生成：${dir}/bubble.json` }
    toast(`ZIP 已生成：${dir}/bubble.json`)
  } catch (err) {
    console.error(err)
    toast(`ZIP 导出失败：${err && err.message ? err.message : '未知错误'}`, 'error')
  }
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (file) loadFile(file)
}

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) loadFile(file)
}

function onPaste(e) {
  const item = [...e.clipboardData.items].find(i => i.type.startsWith('image/'))
  if (item) loadFile(item.getAsFile())
}

// ---- Watch SVG result for drag binding ----
watch(currentSvgPreview, async () => {
  if (!currentSvgPreview.value) return
  await nextTick()
  const container = resultStageRef.value
  if (!container) return
  const svg = container.querySelector('svg')
  if (svg) {
    bindTextDrag(svg)
    startPreviewAnimation(svg)
  }
})

// ---- Keyboard paste ----
onMounted(() => {
  window.addEventListener('paste', onPaste)
})

onUnmounted(() => {
  window.removeEventListener('paste', onPaste)
  stopPreviewAnimation()
})
</script>

<style scoped>
@keyframes load {
  from { transform: translateX(-100%); }
  to { transform: translateX(320%); }
}
.animate-load {
  animation: load 1s infinite ease-in-out;
}
.checkerboard {
  background-image:
    repeating-conic-gradient(rgb(var(--color-border) / 0.15) 0% 25%, transparent 0% 50%);
  background-size: 20px 20px;
}
</style>
