export async function hashUsername(username) {
  const msgBuffer = new TextEncoder().encode(username)
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16)
}

export function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[<>&"']/g, function(ch) {
    return ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;" })[ch]
  })
}

export function normalizePlaceholders(s) {
  return String(s || "")
    .split("${displayText}").join("{n}")
    .split("{{displayText}}").join("{n}")
    .split("$displayText").join("{n}")
    .split("{displayText}").join("{n}")
    .split("{{count}}").join("{n}")
    .split("{count}").join("{n}")
    .split("{{number}}").join("{n}")
    .split("{{n}}").join("{n}")
    .split("${qpyscolor}").join("{c}")
    .split("{{qpyscolor}}").join("{c}")
    .split("$qpyscolor").join("{c}")
    .split("{qpyscolor}").join("{c}")
    .split("{{bubbleColor}}").join("{c}")
    .split("{{c}}").join("{c}")
    .split("${qpwzcolor}").join("{t}")
    .split("{{qpwzcolor}}").join("{t}")
    .split("$qpwzcolor").join("{t}")
    .split("{qpwzcolor}").join("{t}")
    .split("{{textColor}}").join("{t}")
    .split("{{color}}").join("{t}")
    .split("{color}").join("{t}")
    .split("{{t}}").join("{t}")
}

export function fillSvg(tpl, c, t, n = 12) {
  return normalizePlaceholders(tpl)
    .split("{n}").join(n)
    .split("{c}").join(c || "#8a8f99")
    .split("{t}").join(t || "#8a8f99")
}

export function svgToImg(svg, cls, c, t) {
  const filled = fillSvg(svg, c, t)
  const trimmed = filled.trim()
  if (trimmed.startsWith('<svg')) {
    const tagEnd = trimmed.indexOf('>')
    const openTag = trimmed.slice(0, tagEnd + 1)
    if (/\bclass\s*=/.test(openTag)) {
      const merged = openTag.replace(/\bclass\s*=\s*(["'])([^"']*)\1/, (m, q, existing) => `class=${q}${existing} ${cls}${q}`)
      return merged + trimmed.slice(tagEnd + 1)
    }
    return `<svg class="${cls}"` + trimmed.slice(4)
  }
  return `<span class="${cls}">${filled}</span>`
}

export function extractColors(svg) {
  const re = /#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)/g
  const seen = {}
  const list = []
  let match
  
  while ((match = re.exec(svg))) {
    const color = match[0]
    const key = color.toLowerCase()
    if (!seen[key]) {
      seen[key] = 1
      list.push(color)
    }
  }
  
  return list
}

export function autoMapColors(svg) {
  const normalized = normalizePlaceholders(svg)
  
  if (normalized.indexOf("{c}") >= 0 || normalized.indexOf("{t}") >= 0) {
    return { svg: normalized, color: "", textColor: "" }
  }
  
  let result = normalized
  let color = ""
  let textColor = ""
  
  const textMatch = normalized.match(/<text\b[^>]*?\bfill\s*=\s*["']([^"']+)["']/i)
  const textColorVal = textMatch ? textMatch[1] : ""
  
  function isColor(v) {
    return /^#[0-9a-fA-F]{3,8}$/.test(v) || /^rgba?\(/i.test(v)
  }
  
  if (isColor(textColorVal)) {
    result = result.split(textColorVal).join("{t}")
    textColor = textColorVal
  }
  
  const re = /(?:fill|stroke)\s*=\s*["'](#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))["']/gi
  let m
  let bc = ""
  
  while ((m = re.exec(normalized))) {
    if (m[1] !== textColorVal) {
      bc = m[1]
      break
    }
  }
  
  if (bc) {
    result = result.split(bc).join("{c}")
    color = bc
  }
  
  return { svg: result, color, textColor }
}
