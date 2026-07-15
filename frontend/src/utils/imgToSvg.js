export const escapeXml = (s) => String(s).replace(/[<>&"']/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]))

export const clamp = (v, a, b) => Math.max(a, Math.min(b, v))

export const rgbHex = (r, g, b) => '#' + [r, g, b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('')

export const fmtBytes = (bytes) => bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(2)} MB`

export const roundCoord = (value) => Math.round(Number(value) * 10) / 10

export function safeFileName(value, fallback = '气泡') {
  const cleaned = String(value || '').trim().replace(/[\\/:*?"<>|\u0000-\u001f]/g, '_').replace(/[. ]+$/g, '')
  return cleaned || fallback
}

export function dataUrlByteSize(dataUrl) {
  const comma = dataUrl.indexOf(',')
  if (comma < 0) return dataUrl.length
  const payload = dataUrl.slice(comma + 1)
  if (/;base64/i.test(dataUrl.slice(0, comma))) {
    const padding = payload.endsWith('==') ? 2 : payload.endsWith('=') ? 1 : 0
    return Math.max(0, Math.floor(payload.length * 3 / 4) - padding)
  }
  return new TextEncoder().encode(decodeURIComponent(payload)).length
}

export function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'))
    reader.onabort = () => reject(new Error('文件读取已取消'))
    reader.readAsDataURL(file)
  })
}

export function fileToArrayBuffer(file) {
  if (file.arrayBuffer) return file.arrayBuffer()
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error || new Error('GIF 数据读取失败'))
    reader.readAsArrayBuffer(file)
  })
}

export function loadHtmlImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.decoding = 'async'
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('浏览器无法解码该图片'))
    img.src = src
  })
}

export async function normalizeWithImageBitmap(file) {
  if (typeof createImageBitmap !== 'function') throw new Error('当前浏览器不支持备用解码')
  const bitmap = await createImageBitmap(file)
  try {
    const canvas = document.createElement('canvas')
    canvas.width = bitmap.width
    canvas.height = bitmap.height
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('无法创建画布')
    ctx.drawImage(bitmap, 0, 0)
    const dataUrl = canvas.toDataURL('image/png')
    return { dataUrl, image: await loadHtmlImage(dataUrl) }
  } finally {
    if (bitmap.close) bitmap.close()
  }
}

export function lzwDecodeGif(minCodeSize, data, expectedSize) {
  const clearCode = 1 << minCodeSize
  const endCode = clearCode + 1
  const prefix = new Uint16Array(4096)
  const suffix = new Uint8Array(4096)
  const stack = new Uint8Array(4097)
  const output = new Uint8Array(expectedSize)
  for (let i = 0; i < clearCode; i++) suffix[i] = i
  let codeSize = minCodeSize + 1
  let codeMask = (1 << codeSize) - 1
  let available = clearCode + 2
  let oldCode = -1
  let first = 0
  let datum = 0
  let bits = 0
  let dataPos = 0
  let top = 0
  let outPos = 0
  while (outPos < expectedSize) {
    if (top === 0) {
      while (bits < codeSize) {
        if (dataPos >= data.length) return output
        datum |= data[dataPos++] << bits
        bits += 8
      }
      let code = datum & codeMask
      datum >>>= codeSize
      bits -= codeSize
      if (code === clearCode) {
        codeSize = minCodeSize + 1
        codeMask = (1 << codeSize) - 1
        available = clearCode + 2
        oldCode = -1
        continue
      }
      if (code === endCode) break
      if (oldCode === -1) {
        output[outPos++] = suffix[code]
        first = code
        oldCode = code
        continue
      }
      const inCode = code
      if (code === available) {
        stack[top++] = first
        code = oldCode
      } else if (code > available) {
        break
      }
      while (code >= clearCode) {
        if (code >= 4096 || top >= stack.length) break
        stack[top++] = suffix[code]
        code = prefix[code]
      }
      first = suffix[code]
      stack[top++] = first
      if (available < 4096) {
        prefix[available] = oldCode
        suffix[available] = first
        available++
        if ((available & codeMask) === 0 && available < 4096) {
          codeSize++
          codeMask = (1 << codeSize) - 1
        }
      }
      oldCode = inCode
    }
    if (top > 0) output[outPos++] = stack[--top]
  }
  return output
}

export function deinterlaceGif(source, width, height) {
  const output = new Uint8Array(source.length)
  let fromRow = 0
  const passes = [[0, 8], [4, 8], [2, 4], [1, 2]]
  for (const [start, step] of passes) {
    for (let y = start; y < height; y += step) {
      const from = fromRow * width
      output.set(source.subarray(from, from + width), y * width)
      fromRow++
    }
  }
  return output
}

export function parseGif(buffer) {
  const bytes = new Uint8Array(buffer)
  let pos = 0
  const need = (count) => { if (pos + count > bytes.length) throw new Error('GIF 文件数据不完整') }
  const byte = () => { need(1); return bytes[pos++] }
  const u16 = () => { need(2); const value = bytes[pos] | (bytes[pos + 1] << 8); pos += 2; return value }
  const ascii = (count) => { need(count); let value = ''; for (let i = 0; i < count; i++) value += String.fromCharCode(bytes[pos++]); return value }
  const colorTable = (size) => { const table = new Array(size); for (let i = 0; i < size; i++) table[i] = [byte(), byte(), byte()]; return table }
  const subBlocks = () => {
    const chunks = []
    let length = 0
    while (true) {
      const size = byte()
      if (!size) break
      need(size)
      const chunk = bytes.slice(pos, pos + size)
      pos += size
      chunks.push(chunk)
      length += size
    }
    const joined = new Uint8Array(length)
    let offset = 0
    for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.length }
    return joined
  }
  const signature = ascii(6)
  if (signature !== 'GIF87a' && signature !== 'GIF89a') throw new Error('文件不是有效的 GIF')
  const width = u16()
  const height = u16()
  if (!width || !height) throw new Error('GIF 尺寸无效')
  const packed = byte()
  const hasGlobalTable = Boolean(packed & 0x80)
  const globalTableSize = 1 << ((packed & 0x07) + 1)
  const backgroundIndex = byte()
  byte()
  const globalPalette = hasGlobalTable ? colorTable(globalTableSize) : null
  const background = globalPalette && globalPalette[backgroundIndex] ? globalPalette[backgroundIndex] : [0, 0, 0]
  const frames = []
  let loopCount = null
  let gce = { disposal: 0, delay: 100, transparentIndex: null }
  while (pos < bytes.length) {
    const marker = byte()
    if (marker === 0x3b) break
    if (marker === 0x21) {
      const label = byte()
      if (label === 0xf9) {
        const size = byte()
        need(size)
        const block = bytes.slice(pos, pos + size)
        pos += size
        if (pos < bytes.length && bytes[pos] === 0) pos++
        if (block.length >= 4) {
          const gcePacked = block[0]
          const delayCs = block[1] | (block[2] << 8)
          gce = {
            disposal: (gcePacked >> 2) & 0x07,
            delay: Math.max(20, delayCs ? delayCs * 10 : 100),
            transparentIndex: (gcePacked & 0x01) ? block[3] : null
          }
        }
      } else if (label === 0xff) {
        const size = byte()
        const application = ascii(size)
        const appData = subBlocks()
        if (/NETSCAPE2\.0|ANIMEXTS1\.0/.test(application) && appData.length >= 3 && appData[0] === 1) {
          loopCount = appData[1] | (appData[2] << 8)
        }
      } else if (label === 0x01) {
        const size = byte()
        need(size)
        pos += size
        subBlocks()
      } else {
        subBlocks()
      }
      continue
    }
    if (marker !== 0x2c) throw new Error(`GIF 中存在未知数据块 0x${marker.toString(16)}`)
    const left = u16()
    const top = u16()
    const frameWidth = u16()
    const frameHeight = u16()
    const imagePacked = byte()
    const hasLocalTable = Boolean(imagePacked & 0x80)
    const interlaced = Boolean(imagePacked & 0x40)
    const localTableSize = 1 << ((imagePacked & 0x07) + 1)
    const palette = hasLocalTable ? colorTable(localTableSize) : globalPalette
    if (!palette) throw new Error('GIF 帧缺少颜色表')
    const minCodeSize = byte()
    const compressed = subBlocks()
    let indices = lzwDecodeGif(minCodeSize, compressed, frameWidth * frameHeight)
    if (interlaced) indices = deinterlaceGif(indices, frameWidth, frameHeight)
    frames.push({
      left, top, width: frameWidth, height: frameHeight, palette, indices,
      delay: gce.delay, disposal: gce.disposal, transparentIndex: gce.transparentIndex
    })
    gce = { disposal: 0, delay: 100, transparentIndex: null }
  }
  if (!frames.length) throw new Error('GIF 中没有可用动画帧')
  return {
    width, height, background, loopCount, frames,
    duration: frames.reduce((sum, frame) => sum + frame.delay, 0)
  }
}

export function collectSamples(data, alphaThreshold, removeWhite, whiteTolerance) {
  const samples = []
  const step = Math.max(1, Math.floor((data.length / 4) / 12000))
  for (let i = 0, px = 0; i < data.length; i += 4, px++) {
    if (px % step) continue
    const a = data[i + 3]
    if (a <= alphaThreshold) continue
    const r = data[i], g = data[i + 1], b = data[i + 2]
    if (removeWhite && 255 - r <= whiteTolerance && 255 - g <= whiteTolerance && 255 - b <= whiteTolerance) continue
    samples.push([r, g, b])
  }
  return samples
}

export function kMeans(samples, k) {
  if (!samples.length) return [[0, 0, 0]]
  k = Math.min(k, samples.length)
  const sorted = samples.slice().sort((a, b) => (a[0] + a[1] + a[2]) - (b[0] + b[1] + b[2]))
  let centers = Array.from({ length: k }, (_, i) => sorted[Math.floor((i + .5) * sorted.length / k)].slice())
  for (let iter = 0; iter < 9; iter++) {
    const sums = Array.from({ length: k }, () => [0, 0, 0, 0])
    for (const p of samples) {
      let best = 0, bestD = Infinity
      for (let j = 0; j < k; j++) {
        const c = centers[j]
        const dr = p[0] - c[0], dg = p[1] - c[1], db = p[2] - c[2]
        const d = dr * dr + dg * dg + db * db
        if (d < bestD) { bestD = d; best = j }
      }
      sums[best][0] += p[0]; sums[best][1] += p[1]; sums[best][2] += p[2]; sums[best][3]++
    }
    centers = centers.map((c, j) => sums[j][3] ? [sums[j][0] / sums[j][3], sums[j][1] / sums[j][3], sums[j][2] / sums[j][3]] : c)
  }
  return centers
}

export function nearestColor(r, g, b, palette) {
  let best = 0, bestD = Infinity
  for (let j = 0; j < palette.length; j++) {
    const c = palette[j]
    const dr = r - c[0], dg = g - c[1], db = b - c[2]
    const d = dr * dr + dg * dg + db * db
    if (d < bestD) { bestD = d; best = j }
  }
  return best
}

export function quantize(data, w, h, palette, opts) {
  const out = new Int16Array(w * h)
  out.fill(-1)
  const work = new Float32Array(data.length)
  for (let i = 0; i < data.length; i++) work[i] = data[i]
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4
      const a = work[idx + 3]
      let r = clamp(work[idx], 0, 255), g = clamp(work[idx + 1], 0, 255), b = clamp(work[idx + 2], 0, 255)
      if (a <= opts.alphaThreshold) continue
      if (opts.removeWhite && 255 - r <= opts.whiteTolerance && 255 - g <= opts.whiteTolerance && 255 - b <= opts.whiteTolerance) continue
      const pi = nearestColor(r, g, b, palette)
      out[y * w + x] = pi
      if (opts.dither) {
        const c = palette[pi], er = r - c[0], eg = g - c[1], eb = b - c[2]
        const spread = (nx, ny, f) => {
          if (nx < 0 || nx >= w || ny < 0 || ny >= h) return
          const ni = (ny * w + nx) * 4
          work[ni] += er * f; work[ni + 1] += eg * f; work[ni + 2] += eb * f
        }
        spread(x + 1, y, 7 / 16); spread(x - 1, y + 1, 3 / 16); spread(x, y + 1, 5 / 16); spread(x + 1, y + 1, 1 / 16)
      }
    }
  }
  return out
}

export function mergeRuns(map, w, h) {
  const rects = []
  let active = new Map()
  for (let y = 0; y < h; y++) {
    const current = new Map()
    let x = 0
    while (x < w) {
      const c = map[y * w + x]
      if (c < 0) { x++; continue }
      const start = x
      while (x + 1 < w && map[y * w + x + 1] === c) x++
      const end = x
      const key = `${c}:${start}:${end}`
      if (active.has(key)) {
        const rect = active.get(key); rect.h++
        current.set(key, rect)
      } else {
        const rect = { c, x: start, y, w: end - start + 1, h: 1 }
        current.set(key, rect)
      }
      x++
    }
    for (const [key, rect] of active) if (!current.has(key)) rects.push(rect)
    active = current
  }
  for (const rect of active.values()) rects.push(rect)
  return rects
}

export function buildPathSvg(rects, palette, w, h, sourceW, sourceH) {
  const grouped = Array.from({ length: palette.length }, () => [])
  rects.forEach(r => grouped[r.c].push(`M${r.x} ${r.y}h${r.w}v${r.h}h-${r.w}Z`))
  const paths = grouped.map((commands, i) => commands.length ? `<path fill="${rgbHex(...palette[i])}" d="${commands.join('')}"/>` : '').join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${sourceW}" height="${sourceH}" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges" role="img" aria-label="Vectorized image">${paths}</svg>`
}

export function getSvgGeometry(svgText) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(svgText, 'image/svg+xml')
  const svg = doc.documentElement
  if (!svg || svg.nodeName.toLowerCase() !== 'svg') return { minX: 0, minY: 0, width: 1024, height: 864 }
  const viewBox = (svg.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(Number)
  if (viewBox.length === 4 && viewBox.every(Number.isFinite) && viewBox[2] > 0 && viewBox[3] > 0) {
    return { minX: viewBox[0], minY: viewBox[1], width: viewBox[2], height: viewBox[3] }
  }
  const width = parseFloat(svg.getAttribute('width')) || 1024
  const height = parseFloat(svg.getAttribute('height')) || 864
  return { minX: 0, minY: 0, width, height }
}

export function dynamicTextTag(textX, textY, fontSize, fontFamily, fontWeight, textAnchor, text, color) {
  const x = Number.isFinite(Number(textX)) ? Number(textX) : 0
  const y = Number.isFinite(Number(textY)) ? Number(textY) : 0
  const size = Math.max(1, Number(fontSize) || 1)
  const family = escapeXml(String(fontFamily).trim() || 'Arial,sans-serif')
  const weight = /^\d+$/.test(String(fontWeight)) ? fontWeight : '900'
  const anchor = ['start', 'middle', 'end'].includes(textAnchor) ? textAnchor : 'middle'
  const txt = escapeXml(String(text) || '88')
  const clr = String(color) || '#030000'
  return `  <text x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${clr}" text-anchor="${anchor}">${txt}</text>`
}

export function composeSvgTemplate(baseSvg, textX, textY, fontSize, fontFamily, fontWeight, textAnchor, text, color) {
  let body = String(baseSvg || '').trim()
  body = body.replace(/^\s*<\?xml[^>]*\?>\s*/i, '').replace(/^\s*<!DOCTYPE[\s\S]*?>\s*/i, '')
  if (!/<\/svg>\s*$/i.test(body)) throw new Error('基础 SVG 缺少结束标签')
  return body.replace(/\s*<\/svg>\s*$/i, '\n' + dynamicTextTag(textX, textY, fontSize, fontFamily, fontWeight, textAnchor, text, color) + '\n</svg>')
}

export function previewSvgText(svgText, previewNumber, previewColor) {
  const num = escapeXml(String(previewNumber) || '88')
  return svgText.split('${color}').join(String(previewColor) || '#030000').split('${num}').join(num)
}

export function adaptTextToNewGeometry(oldSvg, newSvg, textX, textY, fontSize, textAutoPosition) {
  if (!oldSvg || textAutoPosition) return null
  const oldBox = getSvgGeometry(oldSvg)
  const newBox = getSvgGeometry(newSvg)
  if (!oldBox.width || !oldBox.height || !newBox.width || !newBox.height) return null
  const oldX = Number(textX)
  const oldY = Number(textY)
  const oldSize = Number(fontSize)
  const relX = (oldX - oldBox.minX) / oldBox.width
  const relY = (oldY - oldBox.minY) / oldBox.height
  return {
    textX: roundCoord(newBox.minX + relX * newBox.width),
    textY: roundCoord(newBox.minY + relY * newBox.height),
    fontSize: Math.max(1, roundCoord(oldSize * (newBox.height / oldBox.height)))
  }
}

export function canvasToBlob(canvas, mime, quality) {
  return new Promise((resolve, reject) => {
    if (!canvas.toBlob) {
      try {
        const dataUrl = canvas.toDataURL(mime, quality)
        const [header, base64] = dataUrl.split(',')
        const actualMime = (header.match(/^data:([^;]+)/) || [, 'image/png'])[1]
        const bytes = atob(base64)
        const arr = new Uint8Array(bytes.length)
        for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
        resolve(new Blob([arr], { type: actualMime }))
      } catch (err) { reject(err) }
      return
    }
    canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('图片压缩失败')), mime, quality)
  })
}

export function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('压缩结果读取失败'))
    reader.readAsDataURL(blob)
  })
}

export function clearGifRect(pixels, gif, frame) {
  const startX = Math.max(0, frame.left)
  const startY = Math.max(0, frame.top)
  const endX = Math.min(gif.width, frame.left + frame.width)
  const endY = Math.min(gif.height, frame.top + frame.height)
  for (let y = startY; y < endY; y++) {
    for (let x = startX; x < endX; x++) {
      const offset = (y * gif.width + x) * 4
      pixels[offset] = 0
      pixels[offset + 1] = 0
      pixels[offset + 2] = 0
      pixels[offset + 3] = 0
    }
  }
}

export function drawGifPatch(pixels, gif, frame) {
  for (let fy = 0; fy < frame.height; fy++) {
    const y = frame.top + fy
    if (y < 0 || y >= gif.height) continue
    for (let fx = 0; fx < frame.width; fx++) {
      const x = frame.left + fx
      if (x < 0 || x >= gif.width) continue
      const colorIndex = frame.indices[fy * frame.width + fx]
      if (frame.transparentIndex !== null && colorIndex === frame.transparentIndex) continue
      const color = frame.palette[colorIndex] || [0, 0, 0]
      const offset = (y * gif.width + x) * 4
      pixels[offset] = color[0]
      pixels[offset + 1] = color[1]
      pixels[offset + 2] = color[2]
      pixels[offset + 3] = 255
    }
  }
}

export function gifFrameSegments(gifData, frameStep, maxFrames, speed) {
  const frameCount = gifData.frames.length
  const effectiveStep = Math.max(Number(frameStep), Math.ceil(frameCount / Number(maxFrames)))
  const indices = []
  for (let i = 0; i < frameCount; i += effectiveStep) indices.push(i)
  const speedRatio = Math.max(0.25, Number(speed) / 100)
  const segments = indices.map((frameIndex, index) => {
    const endIndex = index + 1 < indices.length ? indices[index + 1] : frameCount
    let duration = 0
    for (let i = frameIndex; i < endIndex; i++) duration += gifData.frames[i].delay
    return { frameIndex, duration: Math.max(16, Math.round(duration / speedRatio)) }
  })
  return { effectiveStep, segments, totalDuration: segments.reduce((sum, item) => sum + item.duration, 0) }
}

export function gifCssIterationCount(gifData, infinite) {
  if (infinite) return 'infinite'
  if (!gifData || gifData.loopCount === null) return '1'
  if (gifData.loopCount === 0) return 'infinite'
  return String(Math.max(1, gifData.loopCount + 1))
}

export function cssFrameRule(index, start, end, totalDuration, iterationCount) {
  const startPct = Math.max(0, Math.min(100, start / totalDuration * 100))
  const endPct = Math.max(0, Math.min(100, end / totalDuration * 100))
  const epsilon = Math.min(0.01, Math.max(0.0001, 100 / Math.max(100000, totalDuration * 100)))
  const f = value => Number(value.toFixed(6))
  let keyframes
  if (startPct <= 0.000001 && endPct >= 99.999999) {
    keyframes = `0%,100%{opacity:1}`
  } else if (startPct <= 0.000001) {
    keyframes = `0%,${f(Math.max(0, endPct - epsilon))}%{opacity:1}${f(endPct)}%,100%{opacity:0}`
  } else if (endPct >= 99.999999) {
    keyframes = `0%,${f(Math.max(0, startPct - epsilon))}%{opacity:0}${f(startPct)}%,100%{opacity:1}`
  } else {
    keyframes = `0%,${f(Math.max(0, startPct - epsilon))}%{opacity:0}${f(startPct)}%,${f(Math.max(startPct, endPct - epsilon))}%{opacity:1}${f(endPct)}%,100%{opacity:0}`
  }
  return `@keyframes gifFrame${index}{${keyframes}}#gif-frame-${index}{animation:gifFrame${index} ${totalDuration}ms linear ${iterationCount};animation-fill-mode:both}`
}

export function gifOutputGeometry(gifData, sourceImage, maxSide) {
  const sourceW = gifData ? gifData.width : (sourceImage ? sourceImage.naturalWidth : 0)
  const sourceH = gifData ? gifData.height : (sourceImage ? sourceImage.naturalHeight : 0)
  const scale = Math.min(1, maxSide / Math.max(sourceW, sourceH))
  return {
    width: Math.max(1, Math.round(sourceW * scale)),
    height: Math.max(1, Math.round(sourceH * scale))
  }
}

export async function buildGifFrameSvgJob(gifData, token, opts) {
  if (!gifData) throw new Error('GIF 逐帧解析失败，请重新导出为标准 GIF89a')
  const geometry = gifOutputGeometry(gifData, null, opts.maxSide)
  const selection = gifFrameSegments(gifData, opts.frameStep, opts.maxFrames, opts.speed)
  const wanted = new Map(selection.segments.map((segment, index) => [segment.frameIndex, { ...segment, index }]))
  const sourceCanvas = document.createElement('canvas')
  sourceCanvas.width = gifData.width
  sourceCanvas.height = gifData.height
  const sourceCtx = sourceCanvas.getContext('2d')
  const outputCanvas = document.createElement('canvas')
  outputCanvas.width = geometry.width
  outputCanvas.height = geometry.height
  const outputCtx = outputCanvas.getContext('2d')
  if (!sourceCtx || !outputCtx) throw new Error('无法创建 GIF 帧处理画布')
  sourceCtx.imageSmoothingEnabled = true
  outputCtx.imageSmoothingEnabled = true
  outputCtx.imageSmoothingQuality = 'high'
  const composite = new Uint8ClampedArray(gifData.width * gifData.height * 4)
  let previous = null
  const encodedFrames = []
  let rasterBytes = 0
  let actualMime = opts.format
  const requestedMime = opts.format
  const quality = Number(opts.quality) / 100
  for (let frameIndex = 0; frameIndex < gifData.frames.length; frameIndex++) {
    if (token !== null && token !== undefined && frameIndex % 4 === 0) {
      const currentToken = typeof token === 'function' ? token() : token
      if (currentToken !== true && (currentToken === null || currentToken === false || currentToken === 0)) return null
    }
    if (previous) {
      if (previous.frame.disposal === 2) clearGifRect(composite, gifData, previous.frame)
      else if (previous.frame.disposal === 3 && previous.restore) composite.set(previous.restore)
    }
    const frame = gifData.frames[frameIndex]
    const restore = frame.disposal === 3 ? composite.slice() : null
    drawGifPatch(composite, gifData, frame)
    const segment = wanted.get(frameIndex)
    if (segment) {
      sourceCtx.putImageData(new ImageData(composite, gifData.width, gifData.height), 0, 0)
      if (requestedMime === 'image/jpeg') {
        outputCtx.fillStyle = '#ffffff'
        outputCtx.fillRect(0, 0, geometry.width, geometry.height)
      } else {
        outputCtx.clearRect(0, 0, geometry.width, geometry.height)
      }
      outputCtx.drawImage(sourceCanvas, 0, 0, geometry.width, geometry.height)
      let dataUrl = outputCanvas.toDataURL(requestedMime, quality)
      if (requestedMime === 'image/webp' && !dataUrl.startsWith('data:image/webp')) {
        dataUrl = outputCanvas.toDataURL('image/png')
        actualMime = 'image/png'
      } else if (requestedMime === 'image/jpeg' && !dataUrl.startsWith('data:image/jpeg')) {
        dataUrl = outputCanvas.toDataURL('image/png')
        actualMime = 'image/png'
      }
      rasterBytes += dataUrlByteSize(dataUrl)
      encodedFrames.push({ dataUrl, duration: segment.duration })
      if (encodedFrames.length % 4 === 0) await new Promise(resolve => setTimeout(resolve, 0))
    }
    previous = { frame, restore }
  }
  if (!encodedFrames.length) throw new Error('没有生成可用 GIF 帧')
  const iterationCount = gifCssIterationCount(gifData, opts.infinite)
  let elapsed = 0
  const cssRules = []
  const images = encodedFrames.map((frame, index) => {
    const start = elapsed
    const end = elapsed + frame.duration
    elapsed = end
    if (encodedFrames.length > 1) cssRules.push(cssFrameRule(index, start, end, selection.totalDuration, iterationCount))
    return `<image id="gif-frame-${index}" data-gif-frame="${index}" data-frame-duration="${frame.duration}" width="${geometry.width}" height="${geometry.height}" preserveAspectRatio="xMidYMid meet" opacity="${index === 0 ? 1 : 0}" href="${escapeXml(frame.dataUrl)}"/>`
  }).join('')
  const style = cssRules.length ? `<style type="text/css">${cssRules.join('')}</style>` : ''
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${geometry.width}" height="${geometry.height}" viewBox="0 0 ${geometry.width} ${geometry.height}" role="img" aria-label="Animated GIF CSS frame sequence" data-gif-frames="${encodedFrames.length}" data-gif-duration="${selection.totalDuration}" data-animation-engine="css-frames">${style}<g id="gif-animation">${images}</g></svg>`
  return {
    svg, width: geometry.width, height: geometry.height,
    frameCount: encodedFrames.length, duration: selection.totalDuration,
    rasterBytes, mime: actualMime, method: 'css', effectiveStep: selection.effectiveStep
  }
}

export async function buildEmbedSvgJob(sourceImage, opts) {
  const maxSide = Number(opts.maxSide)
  const naturalMax = Math.max(sourceImage.naturalWidth, sourceImage.naturalHeight)
  const scale = opts.noUpscale ? Math.min(1, maxSide / naturalMax) : maxSide / naturalMax
  const w = Math.max(1, Math.round(sourceImage.naturalWidth * scale))
  const h = Math.max(1, Math.round(sourceImage.naturalHeight * scale))
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('无法创建压缩画布')
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  const requestedMime = opts.format
  if (requestedMime === 'image/jpeg') {
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, w, h)
  } else {
    ctx.clearRect(0, 0, w, h)
  }
  ctx.drawImage(sourceImage, 0, 0, w, h)
  const quality = Number(opts.quality) / 100
  let blob = await canvasToBlob(canvas, requestedMime, quality)
  let actualMime = blob.type || requestedMime
  if (requestedMime === 'image/webp' && actualMime !== 'image/webp') {
    blob = await canvasToBlob(canvas, 'image/png', quality)
    actualMime = blob.type || 'image/png'
  }
  const dataUrl = await blobToDataUrl(blob)
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="Compressed embedded image"><image width="${w}" height="${h}" preserveAspectRatio="xMidYMid meet" href="${escapeXml(dataUrl)}"/></svg>`
  return { svg, rasterBytes: blob.size, width: w, height: h, mime: actualMime }
}

export function buildBubbleJson(svgTemplate, opts) {
  const dirName = safeFileName(opts.dirName, '自定义段评气泡_2')
  const bubble = {
    dayEmphasisColor: opts.dayEmphasisColor,
    dayNormalColor: opts.dayNormalColor,
    dirName,
    name: String(opts.bubbleName || '').trim() || '气泡',
    nightEmphasisColor: opts.nightEmphasisColor,
    nightNormalColor: opts.nightNormalColor,
    sizeScale: Math.max(0.01, Number(opts.sizeScale) || 0.5),
    svgTemplate,
    updatedAt: Date.now()
  }
  return { dirName, json: JSON.stringify(bubble, null, 2) }
}

const crcTable = (() => {
  const table = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1)
    table[n] = c >>> 0
  }
  return table
})()

export function crc32(bytes) {
  let crc = 0xffffffff
  for (const byte of bytes) crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}

export function concatBytes(parts) {
  const length = parts.reduce((sum, part) => sum + part.length, 0)
  const out = new Uint8Array(length)
  let offset = 0
  for (const part of parts) { out.set(part, offset); offset += part.length }
  return out
}

export function makeHeader(length) {
  return new Uint8Array(length)
}

export function set16(view, offset, value) { view.setUint16(offset, value & 0xffff, true) }

export function set32(view, offset, value) { view.setUint32(offset, value >>> 0, true) }

export function dosStamp(date = new Date()) {
  const year = Math.max(1980, date.getFullYear())
  return {
    time: (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2),
    date: ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate()
  }
}

export async function maybeDeflateRaw(bytes) {
  if (typeof CompressionStream !== 'function') return { method: 0, bytes }
  try {
    const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'))
    const compressed = new Uint8Array(await new Response(stream).arrayBuffer())
    return compressed.length < bytes.length ? { method: 8, bytes: compressed } : { method: 0, bytes }
  } catch {
    return { method: 0, bytes }
  }
}

export async function makeSingleFileZip(path, content) {
  const encoder = new TextEncoder()
  const nameBytes = encoder.encode(path)
  const dataBytes = encoder.encode(content)
  const packed = await maybeDeflateRaw(dataBytes)
  const crc = crc32(dataBytes)
  const stamp = dosStamp()
  const flags = 0x0800
  const local = makeHeader(30)
  const lv = new DataView(local.buffer)
  set32(lv, 0, 0x04034b50); set16(lv, 4, 20); set16(lv, 6, flags); set16(lv, 8, packed.method)
  set16(lv, 10, stamp.time); set16(lv, 12, stamp.date); set32(lv, 14, crc)
  set32(lv, 18, packed.bytes.length); set32(lv, 22, dataBytes.length); set16(lv, 26, nameBytes.length); set16(lv, 28, 0)
  const localRecord = concatBytes([local, nameBytes, packed.bytes])
  const central = makeHeader(46)
  const cv = new DataView(central.buffer)
  set32(cv, 0, 0x02014b50); set16(cv, 4, 20); set16(cv, 6, 20); set16(cv, 8, flags); set16(cv, 10, packed.method)
  set16(cv, 12, stamp.time); set16(cv, 14, stamp.date); set32(cv, 16, crc)
  set32(cv, 20, packed.bytes.length); set32(cv, 24, dataBytes.length); set16(cv, 28, nameBytes.length)
  set16(cv, 30, 0); set16(cv, 32, 0); set16(cv, 34, 0); set16(cv, 36, 0); set32(cv, 38, 0); set32(cv, 42, 0)
  const centralRecord = concatBytes([central, nameBytes])
  const end = makeHeader(22)
  const ev = new DataView(end.buffer)
  set32(ev, 0, 0x06054b50); set16(ev, 4, 0); set16(ev, 6, 0); set16(ev, 8, 1); set16(ev, 10, 1)
  set32(ev, 12, centralRecord.length); set32(ev, 16, localRecord.length); set16(ev, 20, 0)
  return new Blob([localRecord, centralRecord, end], { type: 'application/zip' })
}

export function makeSingleFileZipStored(path, content) {
  const encoder = new TextEncoder()
  const nameBytes = encoder.encode(path)
  const dataBytes = encoder.encode(content)
  const crc = crc32(dataBytes)
  const stamp = dosStamp()
  const flags = 0x0800
  const method = 0
  const local = makeHeader(30)
  const lv = new DataView(local.buffer)
  set32(lv, 0, 0x04034b50); set16(lv, 4, 20); set16(lv, 6, flags); set16(lv, 8, method)
  set16(lv, 10, stamp.time); set16(lv, 12, stamp.date); set32(lv, 14, crc)
  set32(lv, 18, dataBytes.length); set32(lv, 22, dataBytes.length); set16(lv, 26, nameBytes.length); set16(lv, 28, 0)
  const localRecord = concatBytes([local, nameBytes, dataBytes])
  const central = makeHeader(46)
  const cv = new DataView(central.buffer)
  set32(cv, 0, 0x02014b50); set16(cv, 4, 20); set16(cv, 6, 20); set16(cv, 8, flags); set16(cv, 10, method)
  set16(cv, 12, stamp.time); set16(cv, 14, stamp.date); set32(cv, 16, crc)
  set32(cv, 20, dataBytes.length); set32(cv, 24, dataBytes.length); set16(cv, 28, nameBytes.length)
  set16(cv, 30, 0); set16(cv, 32, 0); set16(cv, 34, 0); set16(cv, 36, 0); set32(cv, 38, 0); set32(cv, 42, 0)
  const centralRecord = concatBytes([central, nameBytes])
  const end = makeHeader(22)
  const ev = new DataView(end.buffer)
  set32(ev, 0, 0x06054b50); set16(ev, 4, 0); set16(ev, 6, 0); set16(ev, 8, 1); set16(ev, 10, 1)
  set32(ev, 12, centralRecord.length); set32(ev, 16, localRecord.length); set16(ev, 20, 0)
  return new Blob([localRecord, centralRecord, end], { type: 'application/zip' })
}

export function prepareManualDownload(blob, filename, kindLabel) {
  const url = URL.createObjectURL(blob)
  return { url, filename, label: `${kindLabel}已生成：${filename}` }
}

export function clickDownloadUrl(url, filename) {
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.rel = 'noopener'
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  setTimeout(() => a.remove(), 0)
}

export function triggerDownload(blob, filename, kindLabel = '文件') {
  const url = URL.createObjectURL(blob)
  const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  if (isiOS && typeof File === 'function' && navigator.share) {
    try {
      const file = new File([blob], filename, { type: blob.type || 'application/octet-stream' })
      if (!navigator.canShare || navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: filename }).catch(() => {})
        URL.revokeObjectURL(url)
        return { url, manual: false }
      }
    } catch (err) { console.warn('系统分享不可用', err) }
  }
  clickDownloadUrl(url, filename)
  URL.revokeObjectURL(url)
  return { url, manual: false }
}
