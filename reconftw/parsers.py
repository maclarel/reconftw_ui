"""
Parsers for ReconFTW output files.

All functions accept a domain_path (str or Path) and return plain dicts/lists.
Files are read fresh on every call - no caching - so live updates from external
ReconFTW runs are reflected on the next page load.
"""

import json
import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _read_lines(filepath):
    """Return non-empty stripped lines from filepath, or [] if missing."""
    try:
        with open(filepath, encoding="utf-8", errors="replace") as fh:
            return [ln.rstrip("\n") for ln in fh if ln.strip()]
    except (FileNotFoundError, PermissionError, OSError):
        return []


def _read_text(filepath):
    """Return full file contents as a string, or '' if missing."""
    try:
        with open(filepath, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (FileNotFoundError, PermissionError, OSError):
        return ""


def _parse_json_file(filepath):
    """
    Robustly parse a file that may contain:
      - NDJSON  (one compact JSON object per line)
      - A JSON array
      - A single JSON object
      - Multiple concatenated / pretty-printed JSON objects
    Returns a list of dicts.
    """
    try:
        with open(filepath, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except (FileNotFoundError, PermissionError, OSError):
        return []

    if not content.strip():
        return []

    # Strategy 1 – NDJSON: every non-blank line that starts with { is JSON
    ndjson = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                ndjson.append(json.loads(stripped))
            except json.JSONDecodeError:
                pass
    if ndjson:
        return ndjson

    # Strategy 2 – JSON array or single object
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except json.JSONDecodeError:
        pass

    # Strategy 3 – concatenated objects (possibly multi-line / pretty-printed)
    results = []
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(content):
        while pos < len(content) and content[pos] in " \t\n\r":
            pos += 1
        if pos >= len(content):
            break
        try:
            obj, end_pos = decoder.raw_decode(content, pos)
            results.append(obj)
            pos = end_pos
        except json.JSONDecodeError:
            pos += 1
    return results


# ---------------------------------------------------------------------------
# Per-section parsers
# ---------------------------------------------------------------------------

def get_overview(domain_path):
    """Aggregate stats for the domain overview / dashboard."""
    base = Path(domain_path)

    subdomains = _read_lines(base / "subdomains" / "subdomains.txt")
    webs = _read_lines(base / "webs" / "webs.txt")
    ips = _read_lines(base / "hosts" / "ips.txt")
    screenshots = _get_screenshot_list(base / "screenshots")

    # GF vulnerability pattern counts
    gf_types = ["xss", "sqli", "ssrf", "ssti", "lfi", "redirect"]
    gf_counts = {}
    for vt in gf_types:
        gf_counts[vt] = len(_read_lines(base / "gf" / f"{vt}.txt"))

    # Hotlist  (format: "COUNT HOST")
    hotlist = []
    for line in _read_lines(base / "hotlist.txt"):
        parts = line.split(" ", 1)
        if len(parts) == 2:
            hotlist.append({"count": parts[0], "host": parts[1]})

    # Last scan timestamp from .log directory
    last_scan = None
    log_dir = base / ".log"
    try:
        logs = sorted(os.listdir(log_dir))
        if logs:
            last_scan = logs[-1].replace(".txt", "").replace("_", " ", 1)
    except (FileNotFoundError, PermissionError, OSError):
        pass

    # Cloud assets count
    cloud_assets = _read_lines(base / "subdomains" / "cloud_assets.txt")

    return {
        "subdomain_count": len(subdomains),
        "web_count": len(webs),
        "ip_count": len(ips),
        "screenshot_count": len(screenshots),
        "cloud_count": len(cloud_assets),
        "gf_counts": gf_counts,
        "total_vulns": sum(gf_counts.values()),
        "hotlist": hotlist,
        "last_scan": last_scan,
    }


def get_subdomains(domain_path):
    """Parse all subdomain-related data."""
    base = Path(domain_path)

    subdomain_list = _read_lines(base / "subdomains" / "subdomains.txt")
    dns_records = _parse_json_file(base / "subdomains" / "subdomains_dnsregs.json")
    sub_ips = _read_lines(base / "subdomains" / "subdomains_ips.txt")
    cloud_assets = _read_lines(base / "subdomains" / "cloud_assets.txt")
    cloud_extra = _read_lines(base / "subdomains" / "cloud_extra.txt")
    open_buckets = _read_lines(base / "subdomains" / "cloudhunter_open_buckets.txt")
    zonetransfer = _read_lines(base / "subdomains" / "zonetransfer.txt")

    # Build a lookup: host -> dns record
    dns_by_host = {r["host"]: r for r in dns_records if isinstance(r, dict) and "host" in r}

    enriched = []
    for host in subdomain_list:
        if not host:
            continue
        rec = dns_by_host.get(host, {})
        enriched.append({
            "host": host,
            "ips": rec.get("a", []),
            "cname": rec.get("cname", []),
            "txt": rec.get("txt", []),
            "ns": rec.get("ns", []),
            "status": rec.get("status_code", ""),
            "ttl": rec.get("ttl", ""),
        })

    return {
        "subdomains": enriched,
        "sub_ips": sub_ips,
        "cloud_assets": cloud_assets,
        "cloud_extra": cloud_extra,
        "open_buckets": open_buckets,
        "zonetransfer": zonetransfer,
        "count": len(subdomain_list),
    }


def get_webs(domain_path):
    """Parse web-asset data."""
    base = Path(domain_path)

    webs = _read_lines(base / "webs" / "webs.txt")
    web_full_info = _parse_json_file(base / "webs" / "web_full_info.txt")
    urls_by_ext = _read_lines(base / "webs" / "urls_by_ext.txt")
    url_extract = _read_lines(base / "webs" / "url_extract_nodupes.txt")

    # WAF info – format: "url;full_url (waf);waf_name"
    waf_data = []
    for line in _read_lines(base / "webs" / "webs_wafs.txt"):
        parts = line.split(";")
        if len(parts) >= 2:
            waf_data.append({
                "url": parts[0].strip(),
                "waf": parts[-1].strip(),
            })

    # Build a lookup from web_full_info by URL
    info_by_url = {}
    for item in web_full_info:
        if isinstance(item, dict) and "url" in item:
            info_by_url[item["url"]] = item

    return {
        "webs": webs,
        "web_full_info": web_full_info,
        "info_by_url": info_by_url,
        "wafs": waf_data,
        "urls_by_ext": urls_by_ext,
        "url_extract": url_extract,
        "count": len(webs),
    }


def get_hosts(domain_path):
    """Parse host / IP data."""
    base = Path(domain_path)

    ips = _read_lines(base / "hosts" / "ips.txt")
    cdn_providers = _read_lines(base / "hosts" / "cdn_providers.txt")

    # ipinfo.txt – one JSON object per IP (may be wrapped in {"input":…,"data":{…}})
    raw_ipinfo = _parse_json_file(base / "hosts" / "ipinfo.txt")
    ipinfo = []
    for entry in raw_ipinfo:
        if isinstance(entry, dict):
            data = entry.get("data", entry)
            if isinstance(data, dict) and "ip" in data:
                ipinfo.append(data)

    # portscan_shodan.txt – JSON array of host objects
    shodan_raw = _parse_json_file(base / "hosts" / "portscan_shodan.txt")
    # Flatten if it came back as a list-of-lists
    shodan = []
    for item in shodan_raw:
        if isinstance(item, list):
            shodan.extend(item)
        elif isinstance(item, dict) and "ip" in item:
            shodan.append(item)

    return {
        "ips": ips,
        "cdn_providers": cdn_providers,
        "ipinfo": ipinfo,
        "shodan": shodan,
        "count": len(ips),
    }


def get_osint(domain_path):
    """Parse OSINT data."""
    base = Path(domain_path) / "osint"

    domain_info = _read_text(base / "domain_info_general.txt")
    dorks = _read_lines(base / "dorks.txt")
    azure_domains = _read_lines(base / "azure_tenant_domains.txt")
    postman = _read_lines(base / "postman_leaks.txt")
    scopify = _read_lines(base / "scopify.txt")

    # Parse 3rdparts_misconfigurations.txt into structured blocks
    misconfigs_raw = _read_text(base / "3rdparts_misconfigurations.txt")
    misconfigs = _parse_misconfig_blocks(misconfigs_raw)

    return {
        "domain_info": domain_info,
        "dorks": dorks,
        "misconfigs": misconfigs,
        "azure_domains": azure_domains,
        "postman": postman,
        "scopify": scopify,
    }


def _parse_misconfig_blocks(text):
    """Parse the structured misconfig output into a list of dicts."""
    results = []
    if not text:
        return results
    separator = "-" * 80
    blocks = text.split(separator)
    for block in blocks:
        block = block.strip()
        if "Vulnerable result found" not in block and "URL:" not in block:
            continue
        url_m = re.search(r"URL:\s*(.+)", block)
        svc_m = re.search(r"Service:\s*(.+)", block)
        desc_m = re.search(r"Description:\s*(.+)", block)
        refs = re.findall(r"https?://\S+", block)
        results.append({
            "url": url_m.group(1).strip() if url_m else "",
            "service": svc_m.group(1).strip() if svc_m else "",
            "description": desc_m.group(1).strip() if desc_m else "",
            "references": refs,
        })
    return results


def get_vulnerabilities(domain_path):
    """Parse GF-pattern findings (potential vulnerability indicators)."""
    base = Path(domain_path) / "gf"

    vuln_types = ["xss", "sqli", "ssrf", "ssti", "lfi", "redirect", "endpoints"]
    findings = {}
    for vt in vuln_types:
        findings[vt] = [u for u in _read_lines(base / f"{vt}.txt") if u]

    return {
        "findings": findings,
        "total": sum(len(v) for v in findings.values()),
    }


def get_fuzzing(domain_path):
    """Parse directory fuzzing results."""
    base = Path(domain_path) / "fuzzing"

    files = {}
    full_results = []

    try:
        entries = sorted(os.listdir(base))
    except (FileNotFoundError, PermissionError, OSError):
        return {"files": {}, "full": [], "total": 0}

    for name in entries:
        if not name.endswith(".txt"):
            continue
        filepath = base / name
        parsed = _parse_fuzzing_file(filepath)
        if name == "fuzzing_full.txt":
            full_results = parsed
        else:
            host = name[: -len(".txt")]
            files[host] = parsed

    return {
        "files": files,
        "full": full_results,
        "total": sum(len(v) for v in files.values()),
    }


def _parse_fuzzing_file(filepath):
    """Parse ffuf/feroxbuster output. Format: STATUS LENGTH URL"""
    results = []
    for line in _read_lines(filepath):
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0].isdigit():
            results.append({"status": parts[0], "length": parts[1], "url": parts[2]})
        elif line.strip():
            results.append({"status": "", "length": "", "url": line.strip()})
    return results


def get_screenshots(domain_path):
    """Return list of screenshot metadata dicts."""
    base = Path(domain_path) / "screenshots"
    return _get_screenshot_list(base)


def _get_screenshot_list(screenshots_dir):
    results = []
    try:
        for name in sorted(os.listdir(screenshots_dir)):
            if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            url = _decode_screenshot_name(name)
            results.append({"filename": name, "url": url})
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return results


def _decode_screenshot_name(filename):
    """
    ReconFTW names screenshots like: https:__hostname.com.png
    Decode to https://hostname.com
    """
    stem = filename.rsplit(".", 1)[0]  # strip extension
    # Replace first :__ with ://
    url = re.sub(r"^(https?:)__", r"\1//", stem)
    # Any remaining __ become /
    url = url.replace("__", "/")
    return url


def get_js_analysis(domain_path):
    """Parse JS URL extraction results."""
    base = Path(domain_path) / "js"
    urls = _read_lines(base / "url_extract_js.txt")
    return {"urls": urls, "count": len(urls)}


def get_assets(domain_path):
    """Parse assets.jsonl (mixed web/cloud assets tracked by ReconFTW)."""
    base = Path(domain_path)
    all_assets = _parse_json_file(base / "assets.jsonl")

    web = [a for a in all_assets if isinstance(a, dict) and a.get("type") == "web"]
    cloud = [a for a in all_assets if isinstance(a, dict) and a.get("type") == "cloud"]

    return {"all": all_assets, "web": web, "cloud": cloud}
