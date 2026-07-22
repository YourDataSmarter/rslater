param(
    [string]$ProjectRoot = $PSScriptRoot,
    [string]$OutputZip = "",
    [string]$PythonCmd = "python",
    [switch]$SkipDependencyInstall,
    [switch]$KeepBuildDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $OutputZip) {
    $OutputZip = Join-Path $ProjectRoot "dist\stage-lambda-function.zip"
}

$requirementsPath = Join-Path $ProjectRoot "requirements.txt"
$buildDir = Join-Path $ProjectRoot ".lambda_build"
$sourceFiles = @(
    "lambda_function.py",
    "stage_zarr_api.py"
)

Write-Host "Project root: $ProjectRoot"
Write-Host "Build folder: $buildDir"
Write-Host "Output zip:   $OutputZip"

foreach ($fileName in $sourceFiles) {
    $fullPath = Join-Path $ProjectRoot $fileName
    if (-not (Test-Path -LiteralPath $fullPath)) {
        throw "Required source file not found: $fullPath"
    }
}

if (-not (Test-Path -LiteralPath $requirementsPath)) {
    throw "requirements.txt not found at $requirementsPath"
}

if (Test-Path -LiteralPath $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Path $buildDir | Out-Null

if (-not $SkipDependencyInstall) {
    Write-Host "Installing dependencies from requirements.txt into build folder..."
    & $PythonCmd -m pip install --upgrade pip
    & $PythonCmd -m pip install -r $requirementsPath -t $buildDir --no-compile
} else {
    Write-Host "Skipping dependency installation as requested."
}

Write-Host "Copying Lambda source files..."
foreach ($fileName in $sourceFiles) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $fileName) -Destination $buildDir -Force
}

$zipParent = Split-Path -Parent $OutputZip
if (-not (Test-Path -LiteralPath $zipParent)) {
    New-Item -ItemType Directory -Path $zipParent | Out-Null
}

if (Test-Path -LiteralPath $OutputZip) {
    Remove-Item -LiteralPath $OutputZip -Force
}

Write-Host "Creating Lambda deployment zip..."
Compress-Archive -Path (Join-Path $buildDir "*") -DestinationPath $OutputZip -Force

if (-not $KeepBuildDirectory) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}

Write-Host "Done. Lambda package created: $OutputZip"
Write-Host "Lambda handler should be set to: lambda_function.lambda_handler"
