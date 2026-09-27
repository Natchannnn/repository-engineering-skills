# Acceptance test suite for Demo 1, Demo 2, and Evidence Template
# Executes native Test-Json schema gates (in pwsh) and Python test suite scripts/test_demos.py

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path

Write-Host "=== Running Acceptance Test Suite for Examples & Demos ===" -ForegroundColor Cyan
Write-Host "Repository: $repoRoot"

# 1. Native PowerShell 7 Schema Validation check if Test-Json cmdlet is available
if (Get-Command Test-Json -ErrorAction SilentlyContinue) {
    Write-Host "--> Checking evidence template against schema with native Test-Json..."
    $schemaPath = Join-Path $repoRoot "examples\template\evidence-record.schema.json"
    $templatePath = Join-Path $repoRoot "examples\template\run-template.json"

    $templateContent = Get-Content $templatePath -Raw
    $validInstance = $templateContent -replace "YYYY-MM-DDTHH:MM:SSZ", "2026-09-27T02:00:00Z"

    # Positive control: Test-Json must succeed on valid template instance
    $validResult = Test-Json -Json $validInstance -SchemaFile $schemaPath
    if (-not $validResult) {
        Write-Error "Test-Json failed on valid template instance!"
        exit 1
    }

    # Negative control 1: invented enum state must fail validation
    $badEnumInstance = $validInstance -replace '"independent_checks_passed":\s*"not_run"', '"independent_checks_passed": "invented-state"'
    $badEnumResult = $false
    try {
        $badEnumResult = Test-Json -Json $badEnumInstance -SchemaFile $schemaPath -ErrorAction Stop
    } catch {
        $badEnumResult = $false
    }
    if ($badEnumResult) {
        Write-Error "Test-Json accepted invented enum state in negative control!"
        exit 1
    }

    # Negative control 2: fixture = {} (missing required fields)
    $badFixtureInstance = $validInstance -replace '"fixture":\s*\{[^}]*\}', '"fixture": {}'
    $badFixtureResult = $false
    try {
        $badFixtureResult = Test-Json -Json $badFixtureInstance -SchemaFile $schemaPath -ErrorAction Stop
    } catch {
        $badFixtureResult = $false
    }
    if ($badFixtureResult) {
        Write-Error "Test-Json accepted empty fixture object in negative control!"
        exit 1
    }

    # Negative control 3: exit_code = "zero" (invalid integer type)
    $badExitInstance = $validInstance -replace '"commands_executed":\s*\[\]', '"commands_executed": [{"cmd": "test", "exit_code": "zero"}]'
    $badExitResult = $false
    try {
        $badExitResult = Test-Json -Json $badExitInstance -SchemaFile $schemaPath -ErrorAction Stop
    } catch {
        $badExitResult = $false
    }
    if ($badExitResult) {
        Write-Error "Test-Json accepted string exit_code in negative control!"
        exit 1
    }

    # Negative control 4: limitations = [] (minItems: 1 violated)
    $badLimitsInstance = $validInstance -replace '"limitations":\s*\[[^\]]*\]', '"limitations": []'
    $badLimitsResult = $false
    try {
        $badLimitsResult = Test-Json -Json $badLimitsInstance -SchemaFile $schemaPath -ErrorAction Stop
    } catch {
        $badLimitsResult = $false
    }
    if ($badLimitsResult) {
        Write-Error "Test-Json accepted empty limitations array in negative control!"
        exit 1
    }

    Write-Host "    [PASS] Native Test-Json confirmed: valid instance passed, 4 negative control probes rejected." -ForegroundColor Green
}

# 2. Comprehensive Python Acceptance Suite (23 tests: positive & negative controls)
$testScript = Join-Path $repoRoot "scripts\test_demos.py"
if (-not (Test-Path $testScript)) {
    Write-Error "Test runner script not found: $testScript"
    exit 1
}

# Verify required python dependency jsonschema before launching suite
& python -c "import jsonschema" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Required Python test dependency 'jsonschema' is missing. Run: python -m pip install jsonschema"
    exit 1
}

& python -B $testScript -v
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[PASS] All demo acceptance tests (positive & negative controls) passed cleanly." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[FAIL] Demo acceptance suite failed with exit code $exitCode." -ForegroundColor Red
    exit $exitCode
}
