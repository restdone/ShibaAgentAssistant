const currentPath = __CURRENT_PATH__;
let editor = null;
let editingFilePath = null;
let promptAction = null;
let promptExtra = null;

// ── Drag and drop ──────────────────────────────────────────────────────────
const dropzone = document.getElementById('dropzone');
if (dropzone) {
  dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    uploadFiles(e.dataTransfer.files);
  });
}

function uploadFiles(files) {
  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  fd.append('path', currentPath);
  fetch('/upload', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => { if (d.ok) location.reload(); else alert(d.error); });
}

// ── Editor ─────────────────────────────────────────────────────────────────
function modeFor(name) {
  const ext = name.split('.').pop().toLowerCase();
  return {
    py: 'python', js: 'javascript', html: 'htmlmixed', htm: 'htmlmixed',
    css: 'css', sh: 'shell', bash: 'shell', md: 'markdown',
    json: 'javascript', xml: 'xml'
  }[ext] || 'null';
}

function openEditor(filePath, fileName) {
  editingFilePath = filePath;
  document.getElementById('editorTitle').textContent = fileName;
  fetch('/read?path=' + encodeURIComponent(filePath))
    .then(r => r.json())
    .then(d => {
      if (d.error) { alert(d.error); return; }
      document.getElementById('editorModal').classList.add('active');
      if (!editor) {
        editor = CodeMirror.fromTextArea(document.getElementById('editorArea'), {
          theme: 'dracula', lineNumbers: true, indentUnit: 4,
          lineWrapping: true, autofocus: true
        });
      }
      editor.setOption('mode', modeFor(fileName));
      editor.setValue(d.content);
      editor.clearHistory();
    });
}

function closeEditor() {
  document.getElementById('editorModal').classList.remove('active');
}

function saveFile() {
  const content = editor.getValue();
  fetch('/write', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: editingFilePath, content })
  }).then(r => r.json()).then(d => {
    if (d.ok) { closeEditor(); location.reload(); }
    else alert(d.error);
  });
}

// ── Prompt modal ───────────────────────────────────────────────────────────
function openNewFolder() {
  promptAction = 'mkdir';
  document.getElementById('promptTitle').textContent = 'New folder name';
  document.getElementById('promptInput').value = '';
  document.getElementById('promptModal').classList.add('active');
  document.getElementById('promptInput').focus();
}

function openNewFile() {
  promptAction = 'newfile';
  document.getElementById('promptTitle').textContent = 'New file name';
  document.getElementById('promptInput').value = '';
  document.getElementById('promptModal').classList.add('active');
  document.getElementById('promptInput').focus();
}

function openRename(filePath, oldName) {
  promptAction = 'rename';
  promptExtra = filePath;
  document.getElementById('promptTitle').textContent = 'Rename: ' + oldName;
  document.getElementById('promptInput').value = oldName;
  document.getElementById('promptModal').classList.add('active');
  document.getElementById('promptInput').focus();
}

function closePrompt() {
  document.getElementById('promptModal').classList.remove('active');
  promptAction = null;
  promptExtra = null;
}

function promptOk() {
  const val = document.getElementById('promptInput').value.trim();
  if (!val) return;
  closePrompt();
  if (promptAction === 'mkdir') {
    fetch('/mkdir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: currentPath, name: val })
    }).then(r => r.json()).then(d => { if (d.ok) location.reload(); else alert(d.error); });
  } else if (promptAction === 'newfile') {
    fetch('/write', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: currentPath + '/' + val, content: '' })
    }).then(r => r.json()).then(d => { if (d.ok) location.reload(); else alert(d.error); });
  } else if (promptAction === 'rename') {
    fetch('/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: promptExtra, new_name: val })
    }).then(r => r.json()).then(d => { if (d.ok) location.reload(); else alert(d.error); });
  }
}

function deleteItem(filePath, name) {
  if (!confirm('Delete "' + name + '"? This cannot be undone.')) return;
  fetch('/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  }).then(r => r.json()).then(d => { if (d.ok) location.reload(); else alert(d.error); });
}

// ── Mobile Action Bottom Sheet ──────────────────────────────────────────────
let _sheetPath = null;
let _sheetName = null;
let _sheetIsDir = false;
let _sheetCanEdit = false;

function openActionSheet(filePath, fileName, isDir, canEdit) {
  _sheetPath = filePath;
  _sheetName = fileName;
  _sheetIsDir = isDir;
  _sheetCanEdit = canEdit;

  document.getElementById('sheetTitle').textContent = fileName;
  const actions = document.getElementById('sheetActions');
  actions.innerHTML = '';

  if (!isDir) {
    const dl = document.createElement('a');
    dl.className = 'btn btn-primary';
    dl.href = '/download?path=' + encodeURIComponent(filePath);
    dl.textContent = '⬇ Download';
    actions.appendChild(dl);
  }
  if (canEdit) {
    const ed = document.createElement('button');
    ed.className = 'btn btn-warn';
    ed.textContent = '✎ Edit';
    ed.onclick = () => { closeSheet(); openEditor(filePath, fileName); };
    actions.appendChild(ed);
  }
  const rn = document.createElement('button');
  rn.className = 'btn';
  rn.style.cssText = 'background:#cba6f7;color:#1e1e2e';
  rn.textContent = '✎ Rename';
  rn.onclick = () => { closeSheet(); openRename(filePath, fileName); };
  actions.appendChild(rn);

  const del = document.createElement('button');
  del.className = 'btn btn-danger';
  del.textContent = '🗑 Delete';
  del.onclick = () => { closeSheet(); deleteItem(filePath, fileName); };
  actions.appendChild(del);

  document.getElementById('sheetOverlay').classList.add('active');
}

function closeSheet() {
  document.getElementById('sheetOverlay').classList.remove('active');
}

// Close sheet when tapping the dark overlay background
document.getElementById('sheetOverlay').addEventListener('click', function(e) {
  if (e.target === this) closeSheet();
});
