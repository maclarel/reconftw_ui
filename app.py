"""
ReconFTW UI – Flask application entry point.

Usage:
    cp .env.example .env          # edit DATA_DIR as needed
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    flask run                     # or: python app.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    render_template,
    request,
    send_from_directory,
)

from reconftw import parsers

load_dotenv()


def _resolve_data_dir():
    raw = os.environ.get("DATA_DIR", "./sampledata")
    return Path(raw).expanduser().resolve()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    DATA_DIR = _resolve_data_dir()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def list_domains():
        """Return sorted list of domain directory names inside DATA_DIR."""
        try:
            return sorted(
                d
                for d in os.listdir(DATA_DIR)
                if (DATA_DIR / d).is_dir() and not d.startswith(".")
            )
        except (FileNotFoundError, PermissionError, OSError):
            return []

    def domain_path(domain: str):
        """
        Validate and return the absolute path for a domain.
        Returns None if the domain contains traversal characters or
        does not correspond to an existing directory.
        """
        if not domain or ".." in domain or "/" in domain or "\\" in domain:
            return None
        path = DATA_DIR / domain
        if not path.is_dir():
            return None
        # Extra safety: confirm the resolved path is still under DATA_DIR
        try:
            path.resolve().relative_to(DATA_DIR.resolve())
        except ValueError:
            return None
        return path

    # ------------------------------------------------------------------
    # Domain sub-navigation items (label, endpoint, icon)
    # ------------------------------------------------------------------
    NAV_ITEMS = [
        ("Overview", "domain_overview", "bi-speedometer2"),
        ("Subdomains", "domain_subdomains", "bi-diagram-3"),
        ("Web Assets", "domain_webs", "bi-globe"),
        ("Screenshots", "domain_screenshots", "bi-camera"),
        ("Hosts & IPs", "domain_hosts", "bi-hdd-network"),
        ("OSINT", "domain_osint", "bi-search"),
        ("Vulnerabilities", "domain_vulnerabilities", "bi-shield-exclamation"),
        ("Fuzzing", "domain_fuzzing", "bi-braces"),
        ("JS Analysis", "domain_js", "bi-filetype-js"),
    ]

    app.jinja_env.globals["NAV_ITEMS"] = NAV_ITEMS

    # ------------------------------------------------------------------
    # Routes – root
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        domains = list_domains()
        summaries = []
        for d in domains:
            p = domain_path(d)
            if p:
                summaries.append({"name": d, "overview": parsers.get_overview(p)})
        return render_template("index.html", domains=summaries)

    # ------------------------------------------------------------------
    # Routes – domain sections
    # ------------------------------------------------------------------

    @app.route("/domain/<domain>/")
    @app.route("/domain/<domain>/overview")
    def domain_overview(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_overview(p)
        return render_template("domain/overview.html", domain=domain, data=data, active="domain_overview")

    @app.route("/domain/<domain>/subdomains")
    def domain_subdomains(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_subdomains(p)
        return render_template("domain/subdomains.html", domain=domain, data=data, active="domain_subdomains")

    @app.route("/domain/<domain>/webs")
    def domain_webs(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_webs(p)
        return render_template("domain/webs.html", domain=domain, data=data, active="domain_webs")

    @app.route("/domain/<domain>/hosts")
    def domain_hosts(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_hosts(p)
        return render_template("domain/hosts.html", domain=domain, data=data, active="domain_hosts")

    @app.route("/domain/<domain>/osint")
    def domain_osint(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_osint(p)
        return render_template("domain/osint.html", domain=domain, data=data, active="domain_osint")

    @app.route("/domain/<domain>/vulnerabilities")
    def domain_vulnerabilities(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_vulnerabilities(p)
        return render_template("domain/vulnerabilities.html", domain=domain, data=data, active="domain_vulnerabilities")

    @app.route("/domain/<domain>/fuzzing")
    def domain_fuzzing(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        status_filter = request.args.get("status", "")
        active_tab = request.args.get("tab", "")
        data = parsers.get_fuzzing(p, status_filter)
        return render_template("domain/fuzzing.html", domain=domain, data=data, active="domain_fuzzing", active_tab=active_tab)

    @app.route("/domain/<domain>/screenshots")
    def domain_screenshots(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_screenshots(p)
        return render_template("domain/screenshots.html", domain=domain, data=data, active="domain_screenshots")

    @app.route("/domain/<domain>/js")
    def domain_js(domain):
        p = domain_path(domain)
        if not p:
            abort(404)
        data = parsers.get_js_analysis(p)
        return render_template("domain/js.html", domain=domain, data=data, active="domain_js")

    # ------------------------------------------------------------------
    # Static file serving – screenshots
    # ------------------------------------------------------------------

    @app.route("/domain/<domain>/screenshot/<path:filename>")
    def serve_screenshot(domain, filename):
        p = domain_path(domain)
        if not p:
            abort(404)
        # Reject any path-traversal attempts in the filename itself
        if ".." in filename or filename.startswith("/"):
            abort(403)
        screenshot_dir = p / "screenshots"
        return send_from_directory(screenshot_dir, filename)

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app


# Allow running directly: python app.py
if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    create_app().run(debug=debug, host=host, port=port)
