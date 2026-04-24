from .app import app, PORT
from . import routes  # noqa: F401 — registers all routes

if __name__ == "__main__":
    from .app import BASE_DIR
    print(f"Serving files from: {BASE_DIR}")
    print(f"Access at: http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
