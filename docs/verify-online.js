/**
 * 线上验收：直接跑 Render 上的生产站点，验证构建产物 + 跨域 + 权限链路
 * 用法：node docs/verify-online.js
 */
const path = require('node:path')
const { chromium } = require(
  'C:/Users/34908/.workbuddy/binaries/node/versions/22.22.2-6/node_modules/@playwright/cli/node_modules/playwright-core',
)

const BASE = 'https://tk-shop-dashboard.onrender.com'
const OUT = path.join(__dirname, 'shots')

const shot = async (page, name) => {
  await page.screenshot({ path: path.join(OUT, `online-${name}.png`) })
  console.log('shot online-' + name)
}

;(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 980 }, deviceScaleFactor: 1.5 })
  const page = await ctx.newPage()

  const errors = []
  const failed = []
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()))
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  page.on('requestfailed', (r) => failed.push(r.url()))

  console.log('open', BASE)
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded', timeout: 120000 })
  await page.waitForSelector('button.submit', { timeout: 120000 })
  await page.waitForTimeout(1200)
  await shot(page, '01-login')

  await page.fill('input[autocomplete="username"]', 'admin')
  await page.fill('input[autocomplete="current-password"]', 'admin123')
  await page.click('button.submit')
  await page.waitForURL('**/#/dashboard', { timeout: 60000 })
  await page.waitForTimeout(3500)
  await shot(page, '02-dashboard')

  const cards = await page.locator('.card .value').allInnerTexts()
  console.log('指标卡:', cards.join(' | '))
  const noZero = cards.every((c) => c && !c.includes('$0.00'))
  console.log('数据正常(非零):', noZero)
  console.log('折线路径数:', await page.locator('svg path').count())

  await page.click('a[href="#/shops"]')
  await page.waitForTimeout(1500)
  await shot(page, '03-shops')
  console.log('店铺行数:', await page.locator('tbody tr').count())

  await page.click('a[href="#/collect"]')
  await page.waitForTimeout(1500)
  console.log('采集按钮可用:', !(await page.locator('tbody button.btn').first().isDisabled()))

  // viewer 只读账号
  await page.click('header button.btn')
  await page.waitForTimeout(800)
  await page.fill('input[autocomplete="username"]', 'viewer')
  await page.fill('input[autocomplete="current-password"]', 'viewer123')
  await page.click('button.submit')
  await page.waitForURL('**/#/dashboard', { timeout: 60000 })
  await page.waitForTimeout(2000)
  const menus = await page.locator('nav.menu a').allInnerTexts()
  console.log('viewer 菜单:', menus.join(' | '))

  await page.goto(`${BASE}/#/collect`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(2000)
  console.log('viewer 采集按钮禁用:', await page.locator('tbody button.btn').first().isDisabled())
  await shot(page, '04-viewer-collect')

  await page.goto(`${BASE}/#/system`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(2000)
  console.log('viewer 访问 /system 落点:', page.url())

  console.log('console errors:', errors.length ? errors.slice(0, 4) : 'none')
  console.log('failed requests:', failed.length ? failed.slice(0, 4) : 'none')
  await browser.close()
})().catch((e) => {
  console.error('FAILED:', e.message)
  process.exit(1)
})
