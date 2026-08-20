import { readFileSync, writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const dist = resolve(__dirname, '..', 'dist')

const html = readFileSync(resolve(dist, 'index.html'), 'utf-8')

let clean = html
  .replace(/<title data-rh="true">.*?<\/title>/, '')
  .replace(/<meta data-rh="true"[^>]*>/g, '')

const bodyStart = clean.indexOf('<body>') + 6
const bodyEnd = clean.lastIndexOf('</body>')
clean = clean.substring(0, bodyStart) + '\n  <div id="root"></div>\n' + clean.substring(bodyEnd)

writeFileSync(resolve(dist, 'shell.html'), clean, 'utf-8')
console.log(`[postbuild] shell.html (${clean.length} B)`)

const SITE = 'https://www.naxely.com'
const FEED_URL = `${SITE}/rss.xml`
const DEFAULT_IMAGE_URL = `${SITE}/og-image.png`

const posts = JSON.parse(readFileSync(resolve(__dirname, '..', 'src', 'data', 'blog-posts.json'), 'utf-8'))

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function toRfc822(dateStr) {
  const parsed = new Date(dateStr)
  return Number.isNaN(parsed.getTime()) ? null : parsed.toUTCString()
}

const items = posts
  .map((post) => {
    const link = `${SITE}${post.routePrefix || '/blog/'}${post.slug}`
    const pubDate = post.date ? toRfc822(post.date) : null
    const imageUrl = `${SITE}${post.image || '/og-image.png'}`
    const imageSize = post.image ? ' width="1000" height="1500"' : ' width="1200" height="630"'
    return `    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <description>${escapeXml(post.excerpt)}</description>
      ${pubDate ? `<pubDate>${pubDate}</pubDate>` : ''}
      <enclosure url="${imageUrl}" type="image/png"${imageSize} />
      <media:content url="${imageUrl}" type="image/png"${imageSize} />
    </item>`
  })
  .join('\n')

const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Naxely Blog — AI Client Report Generator</title>
    <link>${SITE}/blog</link>
    <description>Product updates, guides, and thoughts on AI-powered client reporting for freelancers and agencies.</description>
    <language>en-us</language>
    <atom:link href="${FEED_URL}" rel="self" type="application/rss+xml" />
    <image>
      <url>${DEFAULT_IMAGE_URL}</url>
      <title>Naxely Blog</title>
      <link>${SITE}/blog</link>
    </image>
${items}
  </channel>
</rss>
`

writeFileSync(resolve(dist, 'rss.xml'), rss, 'utf-8')
console.log(`[postbuild] rss.xml (${rss.length} B, ${posts.length} items)`)
