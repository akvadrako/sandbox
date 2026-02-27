import van from 'vanjs-core'

const { button, div, h3, li, nav, section, span, textarea, ul } = van.tags

const state = van.state({
  mode: 'md',
  tree: [],
  path: '',
  content: '',
  status: 'ready',
  logOffset: 0
})

let logTimer = null

function setStatus(msg) {
  state.val = { ...state.val, status: msg }
}

function fetchJson(path, options) {
  return fetch(path, options).then((r) => {
    if (!r.ok) return r.json().then((x) => Promise.reject(new Error(x.error || 'request failed')))
    return r.json()
  })
}

function clearLogTimer() {
  if (logTimer) {
    clearInterval(logTimer)
    logTimer = null
  }
}

function loadTree() {
  const endpoint = state.val.mode === 'md' ? '/api/tree' : '/api/logs/tree'
  return fetchJson(endpoint).then((data) => {
    state.val = { ...state.val, tree: data.items || [], path: '', content: '', logOffset: 0, status: 'ready' }
  }).catch((e) => setStatus(e.message))
}

function openFile(path) {
  if (state.val.mode === 'md') {
    return fetchJson(`/api/file?path=${encodeURIComponent(path)}`).then((data) => {
      state.val = { ...state.val, path, content: data.content, status: `opened ${path}` }
    }).catch((e) => setStatus(e.message))
  }
  clearLogTimer()
  return fetchJson(`/api/log?path=${encodeURIComponent(path)}&offset=0&limit=65536`).then((data) => {
    state.val = { ...state.val, path, content: data.content, logOffset: data.next_offset, status: `opened ${path}` }
    logTimer = setInterval(() => tailLog(), 1500)
  }).catch((e) => setStatus(e.message))
}

function tailLog() {
  if (state.val.mode !== 'log' || !state.val.path) return
  return fetchJson(`/api/log?path=${encodeURIComponent(state.val.path)}&offset=${state.val.logOffset}&limit=65536`).then((data) => {
    if (!data.content) return
    state.val = { ...state.val, content: state.val.content + data.content, logOffset: data.next_offset, status: `tailed ${state.val.path}` }
  }).catch((e) => setStatus(e.message))
}

function saveFile() {
  const body = JSON.stringify({ path: state.val.path, content: state.val.content })
  return fetchJson('/api/file', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body })
    .then(() => setStatus(`saved ${state.val.path}`))
    .catch((e) => setStatus(e.message))
}

function switchMode(mode) {
  clearLogTimer()
  state.val = { ...state.val, mode }
  loadTree()
}

function treeNode(node) {
  if (node.type === 'file') {
    return li(button({ class: 'file', onclick: () => openFile(node.path) }, node.name))
  }
  return li(span(node.name), ul(node.children.map(treeNode)))
}

const app = div(
  nav(
    div({ class: 'top' },
      button({ id: 'mode-md', onclick: () => switchMode('md') }, 'Markdown'),
      button({ id: 'mode-log', onclick: () => switchMode('log') }, 'Logs')
    ),
    h3(() => state.val.mode === 'md' ? 'Markdown files' : 'Log files'),
    () => ul(state.val.tree.map(treeNode))
  ),
  section(
    div({ class: 'top' },
      span(() => state.val.path || 'no file selected'),
      button({ id: 'save', onclick: saveFile, disabled: () => !state.val.path || state.val.mode !== 'md' }, 'Save')
    ),
    textarea({
      id: 'editor',
      value: () => state.val.content,
      readonly: () => state.val.mode === 'log',
      oninput: (e) => { state.val = { ...state.val, content: e.target.value } },
      placeholder: 'Select a file'
    }),
    div({ class: 'status', id: 'status' }, () => state.val.status)
  )
)

van.add(document.getElementById('app'), app)
loadTree()
