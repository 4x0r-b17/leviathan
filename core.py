import argparse
import json
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator

from modules.banner import print_banner

from modules.bruteforce import generate_subdomain_urls, generate_directory_urls
from modules.crtsh import fetch_crtsh
from modules.status_check import probe
from modules.enrichment import enrich, EnrichedResult


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fuzzer",
        description="Subdomain and directory fuzzer with enrichment",
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "-d", "--directories",
        metavar="URL",
        help="Target URL for directory fuzzing (e.g. https://example.com)",
    )
    target_group.add_argument(
        "-s", "--subdomains",
        metavar="DOMAIN",
        help="Target domain for subdomain enumeration (e.g. example.com)",
    )

    parser.add_argument(
        "-w", "--wordlist",
        metavar="PATH",
        help="Path to wordlist file (required unless --crtsh-only)",
    )
    parser.add_argument(
        "--crtsh",
        action="store_true",
        help="Also query crt.sh Certificate Transparency logs (subdomains only)",
    )
    parser.add_argument(
        "--crtsh-only",
        action="store_true",
        help="Only use crt.sh, skip wordlist bruteforce (subdomains only)",
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=10,
        metavar="N",
        help="Number of concurrent probe threads (default: 10)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save results to file (.json or .csv)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        metavar="SEC",
        help="HTTP probe timeout in seconds (default: 5)",
    )

    args = parser.parse_args()

    # Validation
    if args.directories and args.crtsh:
        parser.error("--crtsh is only valid with --subdomains")
    if args.directories and args.crtsh_only:
        parser.error("--crtsh-only is only valid with --subdomains")
    if not args.wordlist and not args.crtsh_only:
        parser.error("--wordlist is required unless --crtsh-only is set")

    return args


# ── Discovery ─────────────────────────────────────────────────────────────────

def collect_urls(args: argparse.Namespace) -> Generator[str, None, None]:
    """
    Yields candidate URLs from all enabled discovery sources.
    No HTTP requests are made here.
    """
    if args.directories:
        yield from generate_directory_urls(args.directories, args.wordlist)
        return

    # Subdomain mode
    if not args.crtsh_only:
        yield from generate_subdomain_urls(args.subdomains, args.wordlist)

    if args.crtsh or args.crtsh_only:
        try:
            yield from fetch_crtsh(args.subdomains)
        except Exception as e:
            print(f"[!] crt.sh failed: {e}", file=sys.stderr)


# ── Probe + Enrich ────────────────────────────────────────────────────────────

def _probe_and_enrich(url: str, timeout: int) -> EnrichedResult | None:
    """Probes a single URL and returns an EnrichedResult, or None if not interesting."""
    response = probe(url, timeout=timeout)
    if response is None:
        return None
    return enrich(url, response)


def run_pipeline(args: argparse.Namespace) -> list[EnrichedResult]:
    """
    Runs discovery → probe → enrich across all candidate URLs.
    Uses a thread pool for concurrent probing.
    """
    results: list[EnrichedResult] = []
    urls = list(collect_urls(args))

    print(f"[*] {len(urls)} candidates — probing with {args.threads} threads...")

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(_probe_and_enrich, url, args.timeout): url
            for url in urls
        }
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    _print_result(result)
            except Exception as e:
                print(f"[!] Error probing {url}: {e}", file=sys.stderr)

    return results


# ── Output ────────────────────────────────────────────────────────────────────

_PRIORITY_COLOR = {
    "critical": "\033[95m",  # magenta
    "high":     "\033[91m",  # red
    "medium":   "\033[93m",  # yellow
    "low":      "\033[92m",  # green
    "unknown":  "\033[90m",  # grey
}
_RESET = "\033[0m"


def _print_result(r: EnrichedResult) -> None:
    color = _PRIORITY_COLOR.get(r["priority"], _RESET)
    geo = f"{r['country']}/{r['region']}" if r["country"] else "unknown"
    asn = r["asn_name"] or r["asn_number"] or "unknown"
    print(
        f"{color}[{r['priority'].upper():8}] {r['status_code']} "
        f"{r['url']:<60} {r['ip']:<16} {geo} — {asn}{_RESET}"
    )


def save_results(results: list[EnrichedResult], path: str) -> None:
    if path.endswith(".json"):
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"[+] Saved {len(results)} results to {path}")

    elif path.endswith(".csv"):
        if not results:
            print("[!] No results to save.", file=sys.stderr)
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"[+] Saved {len(results)} results to {path}")

    else:
        # Plain text fallback
        with open(path, "w") as f:
            for r in results:
                f.write(f"[{r['priority'].upper()}] {r['status_code']} {r['url']} {r['ip']}\n")
        print(f"[+] Saved {len(results)} results to {path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print_banner()
    args = parse_args()
    results = run_pipeline(args)

    print(f"\n[*] Done. {len(results)} live results found.")

    if args.output:
        save_results(results, args.output)


if __name__ == "__main__":
    main()
