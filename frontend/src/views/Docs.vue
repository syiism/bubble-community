<template>
  <div class="pb-32" style="padding-top: calc(5rem + env(safe-area-inset-top, 0px))">
    <div class="max-w-3xl mx-auto px-6">
      <div class="mb-8 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-2">API 文档</h1>
        <p class="text-sm text-muted">气泡 SVG 接口说明与使用示例</p>
      </div>

      <div class="space-y-6">
        <!-- 接口概览 -->
        <div class="bg-surface border border-border rounded-xl p-5 scroll-animate">
          <h2 class="text-base font-medium text-ink mb-3">GET /api/bubbles/get-bubble</h2>
          <p class="text-sm text-muted leading-relaxed mb-4">
            获取当前用户已选择的气泡 SVG 代码。返回的 SVG 中包含 <code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono text-accent">{n}</code>、<code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono text-accent">{c}</code>、<code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono text-accent">{t}</code> 占位符，下游可自行替换。
          </p>
          <div class="bg-canvas rounded-lg p-4 text-xs font-mono text-ink overflow-x-auto">
            <div class="text-muted mb-1">// 请求示例</div>
            <div>GET /bubble-community/api/bubbles/get-bubble</div>
            <div class="text-muted mt-2">// 响应 (Content-Type: image/svg+xml)</div>
            <div>&lt;svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 32"&gt;</div>
            <div>  &lt;rect width="100" height="32" rx="6" fill="{c}" /&gt;</div>
            <div>  &lt;text x="50" y="20" text-anchor="middle" fill="{t}"&gt;{n}&lt;/text&gt;</div>
            <div>&lt;/svg&gt;</div>
          </div>
        </div>

        <!-- 认证 -->
        <div class="bg-surface border border-border rounded-xl p-5 scroll-animate">
          <h2 class="text-base font-medium text-ink mb-3">认证方式</h2>
          <p class="text-sm text-muted leading-relaxed">
            接口通过 JWT Cookie <code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono text-accent">bubble_token</code> 进行身份认证。用户登录后浏览器自动携带此 Cookie，无需额外传参。未登录时返回 401。
          </p>
        </div>

        <!-- 占位符说明 -->
        <div class="bg-surface border border-border rounded-xl p-5 scroll-animate">
          <h2 class="text-base font-medium text-ink mb-3">占位符说明</h2>
          <p class="text-sm text-muted leading-relaxed mb-4">
            返回的 SVG 中包含以下占位符，下游根据需求替换为实际值：
          </p>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-muted text-xs border-b border-border">
                  <th class="pb-3 pr-4 font-medium">占位符</th>
                  <th class="pb-3 pr-4 font-medium">说明</th>
                  <th class="pb-3 font-medium">示例值</th>
                </tr>
              </thead>
              <tbody>
                <tr class="border-b border-border/50">
                  <td class="py-3 pr-4"><code class="px-1.5 py-0.5 bg-canvas rounded text-xs font-mono text-accent">{n}</code></td>
                  <td class="py-3 pr-4 text-sm text-ink">段号数字</td>
                  <td class="py-3 text-sm text-muted font-mono">12</td>
                </tr>
                <tr class="border-b border-border/50">
                  <td class="py-3 pr-4"><code class="px-1.5 py-0.5 bg-canvas rounded text-xs font-mono text-accent">{c}</code></td>
                  <td class="py-3 pr-4 text-sm text-ink">气泡背景色</td>
                  <td class="py-3 text-sm text-muted font-mono">#3B82F6</td>
                </tr>
                <tr>
                  <td class="py-3 pr-4"><code class="px-1.5 py-0.5 bg-canvas rounded text-xs font-mono text-accent">{t}</code></td>
                  <td class="py-3 pr-4 text-sm text-ink">文字颜色</td>
                  <td class="py-3 text-sm text-muted font-mono">#FFFFFF</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 使用示例 -->
        <div class="bg-surface border border-border rounded-xl p-5 scroll-animate">
          <h2 class="text-base font-medium text-ink mb-3">使用示例</h2>
          <div class="space-y-4">
            <div>
              <h3 class="text-xs font-medium text-muted mb-2">HTML &lt;img&gt;</h3>
              <div class="bg-canvas rounded-lg p-4 text-xs font-mono text-ink overflow-x-auto">
                <div>&lt;img src="/bubble-community/api/bubbles/get-bubble" /&gt;</div>
              </div>
            </div>
            <div>
              <h3 class="text-xs font-medium text-muted mb-2">JavaScript fetch</h3>
              <div class="bg-canvas rounded-lg p-4 text-xs font-mono text-ink overflow-x-auto">
                <div>const resp = await fetch('/bubble-community/api/bubbles/get-bubble')</div>
                <div>const svg = await resp.text()</div>
                <div class="text-muted">// 替换占位符后使用</div>
                <div>const filled = svg.replace(/\{n\}/g, count)</div>
                <div>               .replace(/\{c\}/g, bubbleColor)</div>
                <div>               .replace(/\{t\}/g, textColor)</div>
              </div>
            </div>
            <div>
              <h3 class="text-xs font-medium text-muted mb-2">curl</h3>
              <div class="bg-canvas rounded-lg p-4 text-xs font-mono text-ink overflow-x-auto">
                <div>curl -b 'bubble_token=&lt;你的token&gt;' \</div>
                <div>  https://你的域名/bubble-community/api/bubbles/get-bubble</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 注意事项 -->
        <div class="bg-surface border border-border rounded-xl p-5 scroll-animate">
          <h2 class="text-base font-medium text-ink mb-3">注意事项</h2>
          <ul class="text-sm text-muted leading-relaxed space-y-2 list-disc list-inside">
            <li>返回的 SVG 带有 <code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono">Cache-Control: no-store</code> 头，请勿长时间缓存。</li>
            <li>占位符除 <code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono">{n}</code>/<code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono">{c}</code>/<code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono">{t}</code> 外，系统会将 <code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono">{{count}}</code>、<code class="px-1 py-0.5 bg-canvas rounded text-xs font-mono">$displayText</code> 等变体统一归一化为标准占位符。</li>
            <li>如果用户未设置气泡，返回第一个官方气泡。</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
