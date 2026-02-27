import van from 'vanjs-core'

const { button, div, h3, li, nav, section, span, textarea, ul } = van.tags

const state = van.state({
  tree: [],
  path: '',
  content: '',
  status: 'ready'
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

function loadTree() {
  return fetchJson('/api/tree').then((data) => {
    state.val = { ...state.val, tree: data.items || [] }
  }).catch((e) => setStatus(e.message))
}

function openFile(path) {
  return fetchJson(`/api/file?path=${encodeURIComponent(path)}`).then((data) => {
    state.val = { ...state.val, path, content: data.content, status: `opened ${path}` }
  }).catch((e) => setStatus(e.message))
}

function saveFile() {
  const body = JSON.stringify({ path: state.val.path, content: state.val.content })
  return fetchJson('/api/file', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body })
    .then(() => setStatus(`saved ${state.val.path}`))
    .catch((e) => setStatus(e.message))
}

function treeNode(node) {
  if (node.type === 'file') {
    return li(button({ class: 'file', onclick: () => openFile(node.path) }, node.name))
  }
  return li(
    span(node.name),
    ul(node.children.map(treeNode))
  )
}

const app = div(
  nav(
    h3('Files'),
    () => ul(state.val.tree.map(treeNode))
  ),
  section(
    div({ class: 'top' },
      span(() => state.val.path || 'no file selected'),
      button({ id: 'save', onclick: saveFile, disabled: () => !state.val.path }, 'Save')
    ),
    textarea({
      id: 'editor',
      value: () => state.val.content,
      oninput: (e) => { state.val = { ...state.val, content: e.target.value } },
      placeholder: 'Select a markdown file'
    }),
    div({ class: 'status', id: 'status' }, () => state.val.status)
  )
)

van.add(document.getElementById('app'), app)
loadTree()
