import { test, expect } from '@playwright/test'
import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const viewDir = path.resolve(__dirname, '..')
const rootDir = path.resolve(viewDir, '..')
let api
let web

function waitFor(url, ms = 12000) {
  const end = Date.now() + ms
  return new Promise((resolve, reject) => {
    const ping = () => {
      fetch(url)
        .then((r) => {
          if (r.ok) resolve()
          else if (Date.now() > end) reject(new Error(`not ready: ${url}`))
          else setTimeout(ping, 200)
        })
        .catch(() => {
          if (Date.now() > end) reject(new Error(`not ready: ${url}`))
          else setTimeout(ping, 200)
        })
    }
    ping()
  })
}

test.beforeAll(async () => {
  api = spawn('python', ['app.py', '--root', '..', '--port', '8000'], { cwd: path.join(rootDir, 'back') })
  web = spawn('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173'], { cwd: viewDir })
  await waitFor('http://127.0.0.1:8000/api/tree')
  await waitFor('http://127.0.0.1:5173')
})

test.afterAll(() => {
  if (web) web.kill('SIGTERM')
  if (api) api.kill('SIGTERM')
})

test('opens and saves markdown file', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'welcome.md' }).click()
  await expect(page.locator('#editor')).toHaveValue(/hello bush/i)
  await page.locator('#editor').fill('# hello bush\n\nupdated from playwright')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.locator('#status')).toContainText('saved')
})

test('opens log mode and reads log file', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Logs' }).click()
  await page.getByRole('button', { name: 'runtime.log' }).click()
  await expect(page.locator('#editor')).toHaveValue(/boot/) 
  await expect(page.locator('#save')).toBeDisabled()
})
