# ── Leviathan Setup — Windows (PowerShell) ───────────────────────────────────
# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

$TOOL_NAME   = "leviathan"
$INSTALL_DIR = "C:\Program Files\$TOOL_NAME"
$BIN_DIR     = "C:\Windows\System32"
$WRAPPER     = "$BIN_DIR\$TOOL_NAME.cmd"

# ── Colors ────────────────────────────────────────────────────────────────────
function info    { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan    }
function success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green   }
function warning { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow  }
function err     { param($msg) Write-Host "[x] $msg" -ForegroundColor Red; exit 1 }

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host @"
`e[36m
 ██▓    ▓█████ ██▒   █▓ ██▓ ▄▄▄     ▄▄▄█████▓ ██░ ██  ▄▄▄       ███▄    █
▓██▒    ▓█   ▀▓██░   █▒▓██▒▒████▄   ▓  ██▒ ▓▒▓██░ ██▒▒████▄     ██ ▀█   █
▒██░    ▒███   ▓██  █▒░▒██▒▒██  ▀█▄ ▒ ▓██░ ▒░▒██▀▀██░▒██  ▀█▄  ▓██  ▀█ ██▒
▒██░    ▒▓█  ▄  ▒██ █░░░██░░██▄▄▄▄██░ ▓██▓ ░ ░▓█ ░██ ░██▄▄▄▄██ ▓██▒  ▐▌██▒
░██████▒░▒████▒  ▒▀█░  ░██░ ▓█   ▓██▒ ▒██▒ ░ ░▓█▒░██▓ ▓█   ▓██▒▒██░   ▓██░
░ ▒░▓  ░░░ ▒░ ░  ░ ▐░  ░▓   ▒▒   ▓▒█░ ▒ ░░    ▒ ░░▒░▒ ▒▒   ▓▒█░░ ▒░   ▒ ▒
░ ░ ▒  ░ ░ ░  ░  ░ ░░   ▒ ░  ▒   ▒▒ ░   ░     ▒ ░▒░ ░  ▒   ▒▒ ░░ ░░   ░ ▒░
  ░ ░      ░       ░░   ▒ ░  ░   ▒    ░       ░  ░░ ░  ░   ▒      ░   ░ ░
    ░  ░   ░  ░     ░   ░        ░  ░         ░  ░  ░      ░  ░         ░
                   ░
`e[0m
"@

# ── Admin check ───────────────────────────────────────────────────────────────
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    err "Run as Administrator: right-click PowerShell -> Run as Administrator"
}

# ── Python check ──────────────────────────────────────────────────────────────
info "Checking Python version..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    err "Python not found. Install from https://python.org (check 'Add to PATH')"
}

$pyVersion = python -c "import sys; print(sys.version_info.minor)"
if ([int]$pyVersion -lt 10) {
    err "Python 3.10+ required. Found 3.$pyVersion"
}
success "Python 3.$pyVersion found"

# ── Copy project ──────────────────────────────────────────────────────────────
info "Installing to $INSTALL_DIR ..."
if (Test-Path $INSTALL_DIR) {
    warning "Existing install found — overwriting"
    Remove-Item -Recurse -Force $INSTALL_DIR
}

Copy-Item -Recurse -Force $PSScriptRoot $INSTALL_DIR
success "Project copied to $INSTALL_DIR"

# ── Virtual environment ───────────────────────────────────────────────────────
info "Creating virtual environment..."
python -m venv "$INSTALL_DIR\venv"
success "Virtual environment created"

info "Installing dependencies..."
& "$INSTALL_DIR\venv\Scripts\pip.exe" install --quiet --upgrade pip
& "$INSTALL_DIR\venv\Scripts\pip.exe" install --quiet -r "$INSTALL_DIR\requirements.txt"
success "Dependencies installed"

# ── Wrapper .cmd ──────────────────────────────────────────────────────────────
info "Creating wrapper at $WRAPPER ..."

Set-Content -Path $WRAPPER -Value "@echo off`r`n`"$INSTALL_DIR\venv\Scripts\python.exe`" `"$INSTALL_DIR\core.py`" %*"

success "Wrapper created at $WRAPPER"

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
success "Leviathan installed successfully!"
Write-Host "    Usage: " -NoNewline; Write-Host "leviathan -s example.com --crtsh-only" -ForegroundColor Cyan
Write-Host "           " -NoNewline; Write-Host "leviathan -s example.com -w wordlist.txt --crtsh" -ForegroundColor Cyan
Write-Host "           " -NoNewline; Write-Host "leviathan -d https://example.com -w wordlist.txt" -ForegroundColor Cyan
Write-Host ""