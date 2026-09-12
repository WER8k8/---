/** AI 爬虫访问时注入 llms 语义块 — Nuxt render:html 传入对象为 bodyAppend */
export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('render:html', (html, { event }) => {
    if (!event?.context?.isAiCrawler) return
    const text = event.context.aiSemanticText
    if (!text || typeof text !== 'string') return

    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')

    const block = [
      '<article id="ai-semantic-payload" data-youding-geo="1" aria-hidden="true"',
      ' style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">',
      `<pre>${escaped}</pre></article>`,
    ].join('')

    if (html && typeof html === 'object' && html !== null) {
      const ctx = html as { bodyAppend?: string | string[]; body?: string }
      if (typeof ctx.bodyAppend === 'string') {
        ctx.bodyAppend += block
      } else if (Array.isArray(ctx.bodyAppend)) {
        ctx.bodyAppend.push(block)
      } else {
        ctx.bodyAppend = block
      }
      return
    }

    if (typeof html === 'string' && html.includes('</body>')) {
      return html.replace('</body>', `${block}\n</body>`)
    }
  })
})
