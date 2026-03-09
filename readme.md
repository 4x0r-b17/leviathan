# leviathan

![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/version-1.0.0-cyan?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)

Subdomain and directory fuzzer with automatic enrichment. Built for reconnaissance phases in penetration testing and bug bounty hunting.

---

## What it does

Leviathan discovers attack surface by combining two discovery methods — wordlist bruteforce and Certificate Transparency log scraping — then probes each candidate and enriches live results with network metadata.

**Discovery**
- Wordlist bruteforce generates candidate subdomains or directories
- crt.sh queries Certificate Transparency logs for historically issued certificates, surfacing subdomains that wordlists would miss

**Probing**
- Each candidate URL is probed concurrently over HTTPS, with automatic fallback to HTTP
- Only responses with interesting status codes are kept (200, 301, 302, 401, 403, 500, etc.)

**Enrichment**
- Every live result is enriched with: resolved IP, ASN number and name, country, region
- Each status code carries a priority label (critical / high / medium / low) and a short note on what to investigate next

---

## Install

```bash
git clone https://github.com/your-handle/leviathan
cd leviathan
```

**Linux**
```bash
sudo bash setup.sh
```

**Windows** — open PowerShell as Administrator
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Both installers create an isolated virtual environment, install dependencies, and register `leviathan` as a system-wide command.

---

## Usage

```bash
# Subdomain enumeration with wordlist
leviathan -s example.com -w wordlist.txt

# Subdomain enumeration using crt.sh only (no wordlist needed)
leviathan -s example.com --crtsh-only

# Subdomain enumeration combining both sources
leviathan -s example.com -w wordlist.txt --crtsh

# Directory fuzzing
leviathan -d https://example.com -w wordlist.txt

# Save output
leviathan -s example.com -w wordlist.txt -o results.json
leviathan -s example.com -w wordlist.txt -o results.csv
```

**Options**

| Flag | Description |
|---|---|
| `-s DOMAIN` | Target domain for subdomain enumeration |
| `-d URL` | Target URL for directory fuzzing |
| `-w PATH` | Path to wordlist file |
| `--crtsh` | Add crt.sh results on top of wordlist |
| `--crtsh-only` | Use crt.sh exclusively, skip wordlist |
| `-t N` | Number of concurrent threads (default: 10) |
| `--timeout SEC` | Request timeout in seconds (default: 5) |
| `-o FILE` | Output file (`.json` or `.csv`) |

---

## Use cases

**Bug bounty recon** — run `--crtsh-only` on a target domain to quickly map subdomains that have been publicly certified. Combine with `-w` to catch internal names that were never submitted to a CA.

**Penetration testing** — directory fuzzing against a known host surfaces hidden admin panels, API endpoints, and legacy paths. Enrichment metadata (ASN, geolocation) helps confirm whether a subdomain is in-scope and where it resolves.

**Subdomain takeover detection** — 404 responses on subdomains with dangling CNAMEs are flagged as `critical`. Cross-reference the resolved IP against known claimable services (GitHub Pages, Heroku, Netlify, S3).

**Infrastructure mapping** — ASN and geolocation data helps identify whether subdomains resolve to the target's own infrastructure or to third-party providers, which changes the attack surface.

---

## Requirements

- Python 3.10+
- See `requirements.txt`

---

## Disclaimer

For authorized testing only. Do not run against targets you do not have explicit permission to test.