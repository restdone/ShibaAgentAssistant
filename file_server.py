import os
import shutil
from pathlib import Path
from flask import Flask, request, redirect, url_for, send_file, abort, jsonify
from werkzeug.utils import secure_filename

PORT = 1990
BASE_DIR = Path(os.path.expanduser("~/Shiba/server_files"))
BASE_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>File Manager — {current_path}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/dracula.min.css">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #1e1e2e; color: #cdd6f4; min-height: 100vh; }}
  a {{ color: #89b4fa; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* Top bar */
  .topbar {{ background: #181825; padding: 12px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #313244; }}
  .topbar h1 {{ font-size: 1.1rem; color: #cba6f7; font-weight: 600; flex-shrink: 0; }}
  .breadcrumb {{ display: flex; align-items: center; gap: 4px; flex-wrap: wrap; font-size: 0.9rem; }}
  .breadcrumb span {{ color: #6c7086; }}

  /* Toolbar */
  .toolbar {{ background: #181825; padding: 8px 24px; display: flex; gap: 8px; flex-wrap: wrap; border-bottom: 1px solid #313244; }}
  .btn {{ padding: 6px 14px; border-radius: 6px; border: none; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: opacity .15s; }}
  .btn:hover {{ opacity: 0.85; }}
  .btn-primary {{ background: #89b4fa; color: #1e1e2e; }}
  .btn-success {{ background: #a6e3a1; color: #1e1e2e; }}
  .btn-danger  {{ background: #f38ba8; color: #1e1e2e; }}
  .btn-warn    {{ background: #fab387; color: #1e1e2e; }}
  .btn-sm {{ padding: 4px 10px; font-size: 0.78rem; }}

  /* File table */
  .container {{ padding: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  thead th {{ text-align: left; padding: 8px 12px; color: #a6adc8; border-bottom: 1px solid #313244; font-weight: 500; }}
  tbody tr {{ border-bottom: 1px solid #313244; transition: background .1s; }}
  tbody tr:hover {{ background: #313244; }}
  td {{ padding: 8px 12px; }}
  .icon {{ font-size: 1.1rem; margin-right: 6px; }}
  .actions {{ display: flex; gap: 6px; }}
  .size-col {{ color: #a6adc8; width: 100px; }}
  .type-col {{ color: #a6adc8; width: 120px; }}

  /* Upload zone */
  .upload-zone {{ border: 2px dashed #45475a; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 20px; color: #a6adc8; cursor: pointer; transition: border-color .2s; }}
  .upload-zone.drag-over {{ border-color: #89b4fa; color: #89b4fa; }}
  .upload-zone input {{ display: none; }}

  /* Modal */
  .modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,.6); z-index: 100; align-items: center; justify-content: center; }}
  .modal-overlay.active {{ display: flex; }}
  .modal {{ background: #1e1e2e; border: 1px solid #45475a; border-radius: 12px; width: 90vw; max-width: 900px; max-height: 90vh; display: flex; flex-direction: column; }}
  .modal-header {{ padding: 14px 18px; border-bottom: 1px solid #45475a; display: flex; align-items: center; gap: 10px; }}
  .modal-header h2 {{ font-size: 1rem; flex: 1; color: #cba6f7; word-break: break-all; }}
  .modal-body {{ flex: 1; overflow: auto; }}
  .modal-footer {{ padding: 12px 18px; border-top: 1px solid #45475a; display: flex; gap: 8px; justify-content: flex-end; }}
  .CodeMirror {{ height: 60vh !important; font-size: 0.9rem; }}

  /* Prompt modal */
  .prompt-modal {{ background: #1e1e2e; border: 1px solid #45475a; border-radius: 12px; padding: 24px; width: 360px; }}
  .prompt-modal h2 {{ margin-bottom: 14px; font-size: 1rem; color: #cba6f7; }}
  .prompt-modal input {{ width: 100%; padding: 8px 12px; border-radius: 6px; border: 1px solid #45475a; background: #181825; color: #cdd6f4; font-size: 0.9rem; margin-bottom: 14px; }}
  .prompt-modal .row {{ display: flex; gap: 8px; justify-content: flex-end; }}

  .flash {{ padding: 10px 18px; border-radius: 8px; margin-bottom: 16px; font-size: 0.9rem; }}
  .flash-success {{ background: #a6e3a122; border: 1px solid #a6e3a1; color: #a6e3a1; }}
  .flash-error   {{ background: #f38ba822; border: 1px solid #f38ba8; color: #f38ba8; }}
</style>
</head>
<body>

<div class="topbar">
  <h1>&#128193; File Manager</h1>
  <nav class="breadcrumb">
    <a href="/browse/">Root</a>
    {breadcrumbs}
  </nav>
</div>

<div class="toolbar">
  <button class="btn btn-success" onclick="openNewFolder()">+ New Folder</button>
  <button class="btn btn-primary" onclick="openNewFile()">+ New File</button>
  <label class="btn btn-warn" style="cursor:pointer;">
    &#8679; Upload
    <input type="file" multiple onchange="uploadFiles(this.files)" style="display:none">
  </label>
</div>

<div class="container">
  {flash}

  <div class="upload-zone" id="dropzone" onclick="document.getElementById('dropInput').click()">
    Drop files here or click to upload
    <input type="file" id="dropInput" multiple onchange="uploadFiles(this.files)">
  </div>

  <table>
    <thead><tr>
      <th>Name</th>
      <th class="type-col">Type</th>
      <th class="size-col">Size</th>
      <th>Actions</th>
    </tr></thead>
    <tbody>
      {parent_row}
      {rows}
    </tbody>
  </table>
</div>

<!-- Editor Modal -->
<div class="modal-overlay" id="editorModal">
  <div class="modal">
    <div class="modal-header">
      <h2 id="editorTitle">Edit File</h2>
      <button class="btn btn-danger btn-sm" onclick="closeEditor()">✕ Close</button>
    </div>
    <div class="modal-body">
      <textarea id="editorArea"></textarea>
    </div>
    <div class="modal-footer">
      <button class="btn btn-primary" onclick="saveFile()">&#128190; Save</button>
    </div>
  </div>
</div>

<!-- Prompt Modal (new folder / new file / rename) -->
<div class="modal-overlay" id="promptModal">
  <div class="prompt-modal">
    <h2 id="promptTitle">Enter name</h2>
    <input type="text" id="promptInput" onkeydown="if(event.key==='Enter')promptOk()">
    <div class="row">
      <button class="btn btn-danger btn-sm" onclick="closePrompt()">Cancel</button>
      <button class="btn btn-primary btn-sm" onclick="promptOk()">OK</button>
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/python/python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/javascript/javascript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/xml/xml.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/htmlmixed/htmlmixed.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/css/css.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/shell/shell.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/markdown/markdown.min.js"></script>
<script>
const currentPath = {current_path_js};
let editor = null;
let editingFilePath = null;
let promptAction = null;
let promptExtra = null;

// ── Drag and drop ──────────────────────────────────────────
const dropzone = document.getElementById('dropzone');
dropzone.addEventListener('dragover', e => {{ e.preventDefault(); dropzone.classList.add('drag-over'); }});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {{
  e.preventDefault(); dropzone.classList.remove('drag-over');
  uploadFiles(e.dataTransfer.files);
}});

function uploadFiles(files) {{
  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  fd.append('path', currentPath);
  fetch('/upload', {{ method: 'POST', body: fd }})
    .then(r => r.json()).then(d => {{ if(d.ok) location.reload(); else alert(d.error); }});
}}

// ── Editor ─────────────────────────────────────────────────
function modeFor(name) {{
  const ext = name.split('.').pop().toLowerCase();
  return {{py:'python',js:'javascript',html:'htmlmixed',htm:'htmlmixed',
           css:'css',sh:'shell',bash:'shell',md:'markdown',
           json:'javascript',xml:'xml'}}[ext] || 'null';
}}

function openEditor(filePath, fileName) {{
  editingFilePath = filePath;
  document.getElementById('editorTitle').textContent = fileName;
  fetch('/read?path=' + encodeURIComponent(filePath))
    .then(r => r.json()).then(d => {{
      if (d.error) {{ alert(d.error); return; }}
      document.getElementById('editorModal').classList.add('active');
      if (!editor) {{
        editor = CodeMirror.fromTextArea(document.getElementById('editorArea'), {{
          theme: 'dracula', lineNumbers: true, indentUnit: 4,
          lineWrapping: true, autofocus: true
        }});
      }}
      editor.setOption('mode', modeFor(fileName));
      editor.setValue(d.content);
      editor.clearHistory();
    }});
}}

function closeEditor() {{
  document.getElementById('editorModal').classList.remove('active');
}}

function saveFile() {{
  const content = editor.getValue();
  fetch('/write', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{ path: editingFilePath, content }})
  }}).then(r => r.json()).then(d => {{
    if (d.ok) {{ closeEditor(); location.reload(); }}
    else alert(d.error);
  }});
}}

// ── Prompt modal ───────────────────────────────────────────
function openNewFolder() {{
  promptAction = 'mkdir';
  document.getElementById('promptTitle').textContent = 'New folder name';
  document.getElementById('promptInput').value = '';
  document.getElementById('promptModal').classList.add('active');
  document.getElementById('promptInput').focus();
}}

function openNewFile() {{
  promptAction = 'newfile';
  document.getElementById('promptTitle').textContent = 'New file name';
  document.getElementById('promptInput').value = '';
  document.getElementById('promptModal').classList.add('active');
  document.getElementById('promptInput').focus();
}}

function openRename(filePath, oldName) {{
  promptAction = 'rename';
  promptExtra = filePath;
  document.getElementById('promptTitle').textContent = 'Rename: ' + oldName;
  document.getElementById('promptInput').value = oldName;
  document.getElementById('promptModal').classList.add('active');
  document.getElementById('promptInput').focus();
}}

function closePrompt() {{
  document.getElementById('promptModal').classList.remove('active');
  promptAction = null; promptExtra = null;
}}

function promptOk() {{
  const val = document.getElementById('promptInput').value.trim();
  if (!val) return;
  closePrompt();
  if (promptAction === 'mkdir') {{
    fetch('/mkdir', {{ method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{ path: currentPath, name: val }}) }})
      .then(r=>r.json()).then(d=>{{ if(d.ok) location.reload(); else alert(d.error); }});
  }} else if (promptAction === 'newfile') {{
    fetch('/write', {{ method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{ path: currentPath + '/' + val, content: '' }}) }})
      .then(r=>r.json()).then(d=>{{
        if(d.ok) {{ location.reload(); }} else alert(d.error);
      }});
  }} else if (promptAction === 'rename') {{
    fetch('/rename', {{ method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{ path: promptExtra, new_name: val }}) }})
      .then(r=>r.json()).then(d=>{{ if(d.ok) location.reload(); else alert(d.error); }});
  }}
}}

function deleteItem(filePath, name) {{
  if (!confirm('Delete "' + name + '"? This cannot be undone.')) return;
  fetch('/delete', {{ method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{ path: filePath }}) }})
    .then(r=>r.json()).then(d=>{{ if(d.ok) location.reload(); else alert(d.error); }});
}}
</script>
</body>
</html>
"""

def safe_path(rel: str) -> Path:
    """Resolve a relative path safely under BASE_DIR."""
    target = (BASE_DIR / rel).resolve()
    if not str(target).startswith(str(BASE_DIR)):
        abort(403)
    return target

def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def build_breadcrumbs(rel: str) -> str:
    parts = [p for p in rel.split("/") if p]
    html = ""
    for i, part in enumerate(parts):
        so_far = "/".join(parts[:i+1])
        html += f' <span>/</span> <a href="/browse/{so_far}">{part}</a>'
    return html

def build_rows(rel: str, path: Path) -> tuple[str, str]:
    parent_row = ""
    if rel:
        parent = "/".join(rel.rstrip("/").split("/")[:-1])
        parent_row = f'<tr><td colspan="4"><a href="/browse/{parent}">&#128281; ..</a></td></tr>'

    rows = []
    entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    for entry in entries:
        entry_rel = (rel.rstrip("/") + "/" + entry.name).lstrip("/")
        is_dir = entry.is_dir()
        icon = "&#128193;" if is_dir else "&#128196;"
        if is_dir:
            name_html = f'<a href="/browse/{entry_rel}">{icon} {entry.name}</a>'
            size_str = "—"
            type_str = "Folder"
        else:
            name_html = f'{icon} {entry.name}'
            try:
                size_str = human_size(entry.stat().st_size)
            except Exception:
                size_str = "?"
            suffix = entry.suffix.lstrip(".").upper() or "File"
            type_str = f"{suffix} File"

        text_exts = {".txt",".py",".js",".ts",".html",".htm",".css",".md",
                     ".json",".yaml",".yml",".toml",".sh",".bash",".xml",
                     ".csv",".ini",".cfg",".env",".rs",".go",".c",".cpp",
                     ".h",".java",".rb",".php",".sql",".log"}
        can_edit = not is_dir and entry.suffix.lower() in text_exts

        actions = []
        if not is_dir:
            actions.append(f'<a class="btn btn-primary btn-sm" href="/download?path={entry_rel}">&#8681; Download</a>')
        if can_edit:
            actions.append(f'<button class="btn btn-warn btn-sm" onclick="openEditor({repr(entry_rel)}, {repr(entry.name)})">&#9998; Edit</button>')
        actions.append(f'<button class="btn btn-sm" style="background:#cba6f7;color:#1e1e2e" onclick="openRename({repr(entry_rel)}, {repr(entry.name)})">&#9998; Rename</button>')
        actions.append(f'<button class="btn btn-danger btn-sm" onclick="deleteItem({repr(entry_rel)}, {repr(entry.name)})">&#128465; Delete</button>')

        action_html = '<div class="actions">' + "".join(actions) + "</div>"
        rows.append(f"<tr><td>{name_html}</td><td class='type-col'>{type_str}</td><td class='size-col'>{size_str}</td><td>{action_html}</td></tr>")

    return parent_row, "\n".join(rows)


@app.route("/")
def index():
    return redirect(url_for("browse", rel_path=""))

@app.route("/browse/", defaults={"rel_path": ""})
@app.route("/browse/<path:rel_path>")
def browse(rel_path):
    path = safe_path(rel_path)
    if not path.exists():
        abort(404)
    if path.is_file():
        return redirect(url_for("download", path=rel_path))

    flash = request.args.get("flash", "")
    flash_type = request.args.get("ft", "success")
    flash_html = ""
    if flash:
        flash_html = f'<div class="flash flash-{flash_type}">{flash}</div>'

    parent_row, rows = build_rows(rel_path, path)
    breadcrumbs = build_breadcrumbs(rel_path)
    import json
    html = HTML_TEMPLATE.format(
        current_path=rel_path or "Root",
        current_path_js=json.dumps(rel_path),
        breadcrumbs=breadcrumbs,
        parent_row=parent_row,
        rows=rows,
        flash=flash_html,
    )
    return html

@app.route("/download")
def download():
    rel = request.args.get("path", "")
    path = safe_path(rel)
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True)

@app.route("/upload", methods=["POST"])
def upload():
    rel = request.form.get("path", "")
    dest = safe_path(rel)
    if not dest.is_dir():
        return jsonify({"ok": False, "error": "Not a directory"})
    files = request.files.getlist("files")
    for f in files:
        fname = secure_filename(f.filename)
        if fname:
            f.save(dest / fname)
    return jsonify({"ok": True})

@app.route("/mkdir", methods=["POST"])
def mkdir():
    data = request.get_json()
    parent = safe_path(data.get("path", ""))
    name = secure_filename(data.get("name", ""))
    if not name:
        return jsonify({"ok": False, "error": "Invalid name"})
    new_dir = parent / name
    new_dir.mkdir(exist_ok=True)
    return jsonify({"ok": True})

@app.route("/read")
def read():
    rel = request.args.get("path", "")
    path = safe_path(rel)
    if not path.is_file():
        return jsonify({"error": "Not a file"})
    try:
        content = path.read_text(errors="replace")
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/write", methods=["POST"])
def write():
    data = request.get_json()
    rel = data.get("path", "")
    content = data.get("content", "")
    path = safe_path(rel)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/rename", methods=["POST"])
def rename():
    data = request.get_json()
    rel = data.get("path", "")
    new_name = secure_filename(data.get("new_name", ""))
    path = safe_path(rel)
    if not new_name:
        return jsonify({"ok": False, "error": "Invalid name"})
    new_path = path.parent / new_name
    try:
        path.rename(new_path)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json()
    rel = data.get("path", "")
    path = safe_path(rel)
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    print(f"Serving files from: {BASE_DIR}")
    print(f"Access at: http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
