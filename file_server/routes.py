import json
from pathlib import Path
from flask import request, redirect, url_for, send_file, abort, jsonify
from werkzeug.utils import secure_filename

from .app import app, BASE_DIR
from .mime import get_mimetype
from .utils import safe_path, build_breadcrumbs, build_rows

# Load static template files once at startup
_TEMPLATE_DIR = Path(__file__).parent / "template"
_PAGE_HTML  = (_TEMPLATE_DIR / "page.html").read_text()
_STYLE_CSS  = (_TEMPLATE_DIR / "style.css").read_text()
_SCRIPT_JS  = (_TEMPLATE_DIR / "script.js").read_text()


def render_page(rel_path: str, flash_html: str = "") -> str:
    parent_row, rows = build_rows(rel_path, safe_path(rel_path))
    breadcrumbs = build_breadcrumbs(rel_path)

    # Inject currentPath into JS
    script = _SCRIPT_JS.replace("__CURRENT_PATH__", json.dumps(rel_path))

    # Use simple string replacement to avoid .format() choking on { } in CSS/JS
    html = _PAGE_HTML
    html = html.replace("{current_path}", rel_path or "Root")
    html = html.replace("{breadcrumbs}", breadcrumbs)
    html = html.replace("{parent_row}", parent_row)
    html = html.replace("{rows}", rows)
    html = html.replace("{flash}", flash_html)
    html = html.replace("{style_css}", _STYLE_CSS)
    html = html.replace("{script_js}", script)

    return html


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

    return render_page(rel_path, flash_html)


@app.route("/download")
def download():
    rel = request.args.get("path", "")
    path = safe_path(rel)
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, mimetype=get_mimetype(path))


@app.route("/upload", methods=["POST"])
def upload():
    rel = request.form.get("path", "")
    dest = safe_path(rel)
    if not dest.is_dir():
        return jsonify({"ok": False, "error": "Not a directory"})
    for f in request.files.getlist("files"):
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
    (parent / name).mkdir(exist_ok=True)
    return jsonify({"ok": True})


@app.route("/read")
def read():
    rel = request.args.get("path", "")
    path = safe_path(rel)
    if not path.is_file():
        return jsonify({"error": "Not a file"})
    try:
        return jsonify({"content": path.read_text(errors="replace")})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/write", methods=["POST"])
def write():
    data = request.get_json()
    path = safe_path(data.get("path", ""))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data.get("content", ""))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/rename", methods=["POST"])
def rename():
    data = request.get_json()
    path = safe_path(data.get("path", ""))
    new_name = secure_filename(data.get("new_name", ""))
    if not new_name:
        return jsonify({"ok": False, "error": "Invalid name"})
    try:
        path.rename(path.parent / new_name)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/delete", methods=["POST"])
def delete():
    import shutil
    data = request.get_json()
    path = safe_path(data.get("path", ""))
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
