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
