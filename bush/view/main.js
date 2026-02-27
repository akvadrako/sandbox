import van from 'vanjs-core'

const { button, div, h3, li, nav, pre, section, span, textarea, ul } = van.tags

const state = van.state({
  mode: 'md',
  tree: [],
  path: '',
  content: '',
  status: 'ready',
  logOffset: 0,
  logPollId: null
})

function setStatus(msg) {
  state.val = { ...state.val, status: msg }
}

function fetchJson(path, options) {
  return fetch(path, options).then((r) => {
    if (!r.ok) return r.json().then((x) => Promise.reject(new Error(x.error || 'request failed')))
    return r.json()
  })
}

function stopLogPolling() {
  if (state.val.logPollId) {
    clearInterval(state.val.logPollId)
    state.val = { ...state.val, logPollId: null }
  }
}

function loadTree() {
  const path = state.val.mode === 'md' ? '/api/tree' : '/api/logs/tree'
  return fetchJson(path)
    .then((data) => {
      state.val = { ...state.val, tree: data.items || [] }
    })
    .catch((e) => setStatus(e.message))
}

function openMarkdown(path) {
  stopLogPolling()
  return fetchJson(`/api/file?path=${encodeURIComponent(path)}`)
    .then((data) => {
      state.val = { ...state.val, path, content: data.content, status: `opened ${path}`, logOffset: 0 }
    })
    .catch((e) => setStatus(e.message))
}

function pollLog() {
  if (!state.val.path || state.val.mode !== 'log') return Promise.resolve()
  return fetchJson(`/api/log?path=${encodeURIComponent(state.val.path)}&offset=${state.val.logOffset}`)
    .then((data) => {
      const next = data.next_offset || 0
      const append = state.val.logOffset === data.offset ? data.content : ''
      state.val = { ...state.val, content: state.val.content + append, logOffset: next, status: `tailing ${state.val.path}` }
    })
    .catch((e) => setStatus(e.message))
}

function openLog(path) {
  stopLogPolling()
  state.val = { ...state.val, path, content: '', logOffset: 0, status: `opened ${path}` }
  pollLog()
  const id = setInterval(pollLog, 2000)
  state.val = { ...state.val, logPollId: id }
}

function openFile(path) {
  if (state.val.mode === 'md') return openMarkdown(path)
  openLog(path)
  return Promise.resolve()
}

function saveFile() {
  const body = JSON.stringify({ path: state.val.path, content: state.val.content })
  return fetchJson('/api/file', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body })
    .then(() => setStatus(`saved ${state.val.path}`))
    .catch((e) => setStatus(e.message))
}

function setMode(mode) {
  stopLogPolling()
  state.val = { ...state.val, mode, tree: [], path: '', content: '', status: mode === 'md' ? 'markdown mode' : 'log mode', logOffset: 0 }
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
    div(
      button({ class: () => state.val.mode === 'md' ? 'mode active' : 'mode', onclick: () => setMode('md') }, 'Markdown'),
      button({ class: () => state.val.mode === 'log' ? 'mode active' : 'mode', onclick: () => setMode('log') }, 'Logs')
    ),
    h3('Files'),
    () => ul(state.val.tree.map(treeNode))
  ),
  section(
    div({ class: 'top' },
      span(() => state.val.path || 'no file selected'),
      button({ id: 'save', onclick: saveFile, disabled: () => !state.val.path || state.val.mode !== 'md' }, 'Save')
    ),
    () => state.val.mode === 'md'
      ? textarea({
          id: 'editor',
          value: () => state.val.content,
          oninput: (e) => { state.val = { ...state.val, content: e.target.value } },
          placeholder: 'Select a markdown file'
        })
      : pre({ id: 'log' }, () => state.val.content || 'Select a log file'),
    div({ class: 'status', id: 'status' }, () => state.val.status)
  )
)

van.add(document.getElementById('app'), app)
loadTree()
window.addEventListener('beforeunload', stopLogPolling)
