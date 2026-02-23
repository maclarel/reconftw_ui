# ReconFTW UI

A web-based front-end for visualising reconnaissance data produced by [ReconFTW](https://github.com/six2dez/reconftw). Rather than manually reviewing dozens of text files, ReconFTW UI aggregates and presents all output in a structured, searchable, and navigable interface — one domain at a time.

> [!IMPORTANT]
> This is heavily vibe-coded project. Expect bugs, security issues, etc... Improvements may come over time, but use at your own risk.

---

## Goal

ReconFTW produces a rich set of output files (subdomains, web probes, port scans, vulnerability signals, screenshots, and more) organised under per-domain directories. Reading this data raw is time-consuming and error-prone. ReconFTW UI solves this by:

- **Automatically discovering** all domain directories under a configurable data path.
- **Parsing every supported file format** (plain text, NDJSON, JSON arrays, multi-line JSON, structured tool output) into clean, tabular views.
- **Reflecting live data** — files are read from disk on every page request, so ongoing ReconFTW scans are reflected without restarting the server.
- **Providing fast navigation** between data categories via a persistent per-domain sidebar.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Web framework | [Flask](https://flask.palletsprojects.com/) | 3.1.0 |
| Environment config | [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.0.1 |
| UI framework | [Bootstrap](https://getbootstrap.com/) | 5.3.3 |
| Icons | [Bootstrap Icons](https://icons.getbootstrap.com/) | 1.11.3 |
| Sortable tables | [DataTables](https://datatables.net/) | 2.0.8 |
| Runtime | Python 3.9+ | — |

Bootstrap, Bootstrap Icons, jQuery, and DataTables are loaded from CDN at pinned versions. No Node.js, no build step.

---

## Setup (local)

```bash
# 1. Clone the repository
git clone <repo-url>
cd reconftwUI

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the data directory
cp .env.example .env
# Edit .env and set DATA_DIR to the path containing your ReconFTW output folders.
# Each subdirectory should be named after the target domain, e.g.:
#   /your/data/
#     example.com/
# Defaults to ./sampledata if DATA_DIR is not set.

# 5. Start the server
flask --app app:create_app run

# Or run directly:
python app.py
```

The application will be available at `http://localhost:5000` by default.

---

## Docker

```bash
# Build the image
docker build -t reconftwui .

# Run, mounting your ReconFTW output directory
docker run -p 5000:5000 \
  -v /path/to/reconftw/output:/data \
  -e DATA_DIR=/data \
  -e FLASK_RUN_HOST=0.0.0.0 \
  reconftwui
```

`FLASK_RUN_HOST=0.0.0.0` is required when running inside a container so the server binds to all interfaces and is reachable from outside. The `.env` file is not included in the image, so pass environment variables via `-e` flags or `--env-file`.

---

## Setup (local)

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `./sampledata` | Path to the directory containing per-domain ReconFTW output folders |
| `SECRET_KEY` | `dev-secret-key` | Flask session secret — change this in any non-local deployment |
| `FLASK_RUN_HOST` | `127.0.0.1` | Address to bind to. Use `0.0.0.0` for all interfaces, or a specific IP to bind to one interface. Respected by both `flask run` and `python app.py` |
| `FLASK_RUN_PORT` | `5000` | Port to listen on |
| `FLASK_DEBUG` | `1` | Set to `0` to disable debug mode |

---

## Data Directory Layout

ReconFTW UI expects a directory structure matching ReconFTW's default output layout:

```
DATA_DIR/
└── <domain>/                         # one directory per target domain
    ├── assets.jsonl
    ├── hotlist.txt
    ├── subdomains/
    │   ├── subdomains.txt
    │   ├── subdomains_dnsregs.json
    │   ├── subdomains_ips.txt
    │   ├── cloud_assets.txt
    │   ├── cloud_extra.txt
    │   ├── cloudhunter_open_buckets.txt
    │   └── zonetransfer.txt
    ├── webs/
    │   ├── webs.txt
    │   ├── web_full_info.txt
    │   ├── webs_wafs.txt
    │   ├── url_extract_nodupes.txt
    │   └── urls_by_ext.txt
    ├── hosts/
    │   ├── ips.txt
    │   ├── ipinfo.txt
    │   ├── portscan_shodan.txt
    │   └── cdn_providers.txt
    ├── osint/
    │   ├── domain_info_general.txt
    │   ├── dorks.txt
    │   ├── 3rdparts_misconfigurations.txt
    │   ├── azure_tenant_domains.txt
    │   ├── postman_leaks.txt
    │   └── scopify.txt
    ├── gf/
    │   ├── xss.txt
    │   ├── sqli.txt
    │   ├── ssrf.txt
    │   ├── ssti.txt
    │   ├── lfi.txt
    │   ├── redirect.txt
    │   └── endpoints.txt
    ├── fuzzing/
    │   ├── <subdomain>.txt
    │   └── fuzzing_full.txt
    ├── screenshots/
    │   └── https:__<hostname>.png
    └── js/
        └── url_extract_js.txt
```

Missing files or directories are handled gracefully — sections simply render as empty rather than erroring.

---

## Functionality

### Domain List (`/`)

The landing page scans `DATA_DIR` and displays a card for every discovered domain directory. Each card shows a summary of key counts (subdomains, web assets, IPs, screenshots, cloud assets, vulnerability signals) and links directly to that domain's overview page.

---

### Per-Domain Sections

Each domain has a persistent sidebar providing one-click access to the following sections.

#### Overview (`/domain/<domain>/`)

A dashboard summarising all discovered data for the domain:

- **Stat cards** — subdomain count, web asset count, IP count, screenshot count, cloud asset count, total vulnerability signals.
- **Vulnerability signal breakdown** — a progress-bar chart showing counts per GF pattern type (XSS, SQLi, SSRF, SSTI, LFI, Open Redirect), colour-coded by severity.
- **Hotlist** — hosts flagged by ReconFTW's hotlist scoring, showing the count of findings per host.
- **Quick navigation** — buttons linking to every other section.
- **Last scan timestamp** — derived from the `.log` directory.

---

#### Subdomains (`/domain/<domain>/subdomains`)

| Tab | Content |
|---|---|
| All Subdomains | Sortable/searchable table enriched with DNS data: resolved IPs, CNAME records, TXT records, TTL, and DNS status (NOERROR / NXDOMAIN) |
| Cloud Assets | Subdomains identified as cloud-hosted assets |
| Open Buckets | Cloud storage buckets found to be publicly accessible (highlighted in red) |
| Zone Transfer | Raw zone transfer output (shown when present) |

---

#### Web Assets (`/domain/<domain>/webs`)

| Tab | Content |
|---|---|
| Full Probe Data | Table of all probed web endpoints with HTTP status code (colour-coded), page title, detected technologies, web server, CDN provider, and resolved IP |
| WAFs | Web endpoints where a WAF was detected, with the WAF name |
| URLs by Extension | Crawled URLs grouped/filtered by file extension |
| Extracted URLs | Full list of URLs extracted during crawling |

---

#### Screenshots (`/domain/<domain>/screenshots`)

- **Grid view** (default) — thumbnail gallery of all captured screenshots.
- **List view** — tabular view with inline thumbnails.
- **Lightbox** — clicking any thumbnail opens a full-size modal with the decoded URL and a link to open it in a new tab.
- View toggle buttons switch between grid and list modes.

---

#### Hosts & IPs (`/domain/<domain>/hosts`)

| Tab | Content |
|---|---|
| Shodan Data | IP addresses enriched with Shodan data: open ports, CPEs, tags, and CVEs (CVEs highlighted in red) |
| IP Geo Info | Geolocation data per IP: hostname, city, region, country, ASN, and timezone |
| IP List | Plain list of all unique IPs discovered |
| CDN Providers | CDN provider attribution data |

---

#### OSINT (`/domain/<domain>/osint`)

| Tab | Content |
|---|---|
| 3rd-Party Misconfigs | Structured cards per vulnerability found by misconfig-mapper: service name, affected URL, description, and reference links |
| WHOIS / Domain Info | Raw WHOIS output for the target domain |
| Google Dorks | Generated dorks with a direct "Search" button linking to Google |
| Azure Tenant | Azure tenant-associated domains |
| Postman Leaks | Postman workspace entries referencing the target domain |
| Scope | Scope entries from scopify |

---

#### Vulnerabilities (`/domain/<domain>/vulnerabilities`)

GF-pattern scan results, indicating URLs that match patterns commonly associated with specific vulnerability classes. These are **indicators for manual review**, not confirmed exploits.

| Pattern | Severity | Description |
|---|---|---|
| XSS | High | Cross-Site Scripting parameter patterns |
| SQLi | High | SQL Injection parameter patterns |
| SSRF | Medium | Server-Side Request Forgery parameter patterns |
| SSTI | Medium | Server-Side Template Injection patterns |
| LFI | Medium | Local File Inclusion path patterns |
| Open Redirect | Low | Open redirect parameter patterns |
| Endpoints | Info | Interesting endpoints discovered |

Each pattern type renders as a separate collapsible table with a **Copy All** button to export the URL list to the clipboard.

---

#### Fuzzing (`/domain/<domain>/fuzzing`)

Directory fuzzing results (from ffuf or feroxbuster output). Results are split into per-host tabs, with each row showing:

- **HTTP status code** (colour-coded: green for 2xx, blue for 3xx, orange for 4xx, red for 5xx)
- **Response content length**
- **Path / URL**

A "Full Scan" tab aggregates results across all targets when a `fuzzing_full.txt` file is present.

---

#### JS Analysis (`/domain/<domain>/js`)

A searchable table of all URLs extracted from JavaScript files during the ReconFTW scan, with direct external links and a **Copy All** button.

---

## Live Data Updates

All data is read directly from disk on each page request — there is no caching layer. This means:

- Any files written or updated by a running ReconFTW scan are reflected on the next page load.
- The **auto-refresh toggle** in the top navigation bar reloads the page every 30 seconds when enabled.
- No server restart is required to pick up new domains added to `DATA_DIR`.

---

## Project Structure

```
reconftwUI/
├── app.py                  # Flask application factory and all route definitions
├── requirements.txt        # Pinned Python dependencies
├── .env.example            # Environment variable template
├── reconftw/
│   ├── __init__.py
│   └── parsers.py          # All file parsing logic (stateless functions)
├── templates/
│   ├── base.html           # Base HTML layout (CDN imports, navbar)
│   ├── index.html          # Domain list / landing page
│   ├── errors/
│   │   └── 404.html
│   └── domain/
│       ├── layout.html     # Domain layout with sidebar (extends base.html)
│       ├── overview.html
│       ├── subdomains.html
│       ├── webs.html
│       ├── hosts.html
│       ├── osint.html
│       ├── vulnerabilities.html
│       ├── fuzzing.html
│       ├── screenshots.html
│       └── js.html
└── static/
    ├── css/
    │   └── main.css        # Custom dark-theme styles (CSS variables)
    └── js/
        └── main.js         # DataTables init helper, toast notifications, auto-refresh
```
