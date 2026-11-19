/**
 * 演示截图脚本：用系统 Edge 跑一遍真实交互，产出 docs/shots/*.png
 * 用法：node docs/shot.js（需先启动后端 :8000 与前端 :5173）
 */
const path = require('node:path')
const fs = require('node:fs')
const { chromium } = require(
  'C:/Users/34908/.workbuddy/binaries/node/versions/22.22.2-6/node_modules/@playwright/cli/node_modules/playwright-core',
)

const BASE = 'http://127.0.0.1:5173'
const OUT = path.join(__dirname, 'shots')
fs.mkdirSync(OUT, { recursive: true })

const shot = async (page, name) => {
  await page.waitForTimeout(700)
  await page.screenshot({ path: path.join(OUT, `${name}.png`) })
  console.log('shot', name)
}

;(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 980 }, deviceScaleFactor: 1.5 })
  const page = await ctx.newPage()

  const errors = []
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(m.text())
  })
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))

  await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle' })
  await shot(page, '01-login')

  await page.click('button.submit')
  await page.waitForURL('**/#/dashboard', { timeout: 15000 })
  await page.waitForTimeout(1600)
  await shot(page, '02-dashboard')

  await page.click('a[href="#/shops"]')
  await page.waitForTimeout(900)
  await shot(page, '03-shops')

  await page.click('a[href="#/products"]')
  await page.waitForTimeout(1100)
  await shot(page, '04-products')

  await page.click('a[href="#/social"]')
  await page.waitForTimeout(900)
  await shot(page, '05-social')

  await page.click('a[href="#/collect"]')
  await page.waitForTimeout(900)
  await shot(page, '06-collect')

  await page.click('a[href="#/system"]')
  await page.waitForTimeout(900)
  await shot(page, '07-system')

  // 8 天维度切换，验证筛选联动
  await page.click('a[href="#/dashboard"]')
  await page.waitForTimeout(700)
  const seg = page.locator('.seg button', { hasText: '7 天' }).first()
  await seg.click()
  await page.waitForTimeout(1200)
  await shot(page, '08-dashboard-7d')

  // viewer 账号：验证权限码（侧边栏少一项 + 采集按钮被拦）
  await page.click('button.btn')
  await page.waitForTimeout(500)
  await page.fill('input[autocomplete="username"]', 'viewer')
  await page.fill('input[autocomplete="current-password"]', 'viewer123')
  await page.click('button.submit')
  await page.waitForURL('**/#/dashboard', { timeout: 15000 })
  await page.waitForTimeout(1200)
  const menus = await page.locator('nav.menu a').allInnerTexts()
  console.log('viewer 可见菜单:', menus.join(' | '))
  await shot(page, '09-viewer-menus')

  await page.goto(`${BASE}/#/collect`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(900)
  const disabled = await page.locator('tbody button.btn').first().isDisabled()
  console.log('viewer 采集按钮禁用状态:', disabled)
  await shot(page, '10-viewer-collect')

  await page.goto(`${BASE}/#/system`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(900)
  console.log('viewer 访问 /system 后落点:', page.url())

  console.log('console errors:', errors.length ? errors : 'none')
  await browser.close()
})().catch((e) => {
  console.error('FAILED:', e.message)
  process.exit(1)
})
