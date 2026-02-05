# ci\build_exe.ps1

$ErrorActionPreference = 'Stop'

Set-StrictMode -Version Latest
 
# --- Inputs / defaults -------------------------------------------------------

$APP        = if ($env:APP) { $env:APP } else { 'ABA' }

$EntryFile  = 'login_page.py'   # your main script (repo root)

$IconFile   = 'icon_3.ico'      # icon file (repo root)

$ExtraDir   = 'Icon'            # folder to bundle, copied as "Icon" at runtime
 
# --- Paths -------------------------------------------------------------------

$repo     = Split-Path -Parent $PSScriptRoot

$py       = Join-Path $env:PY_ROOT 'python.exe'

$verFile  = Join-Path $repo 'version.env'

$entry    = Join-Path $repo $EntryFile

$iconAbs  = Join-Path $repo $IconFile

$extraAbs = Join-Path $repo $ExtraDir

$distDir  = Join-Path $repo 'dist'

$workDir  = Join-Path $repo 'build'
 
if (-not (Test-Path $verFile)) { throw "version.env not found at $verFile" }

if (-not (Test-Path $entry))   { throw "Entry script not found: $entry" }
 
$VERSION  = (Get-Content $verFile) -replace '^VERSION=',''

if (-not $VERSION) { throw "VERSION is empty in $verFile" }
 
$exeBase  = "$APP-$VERSION"

$exeName  = "$exeBase.exe"

$exePath  = Join-Path $distDir $exeName

$shaPath  = "$exePath.sha256"
 
# --- Prep output dirs --------------------------------------------------------

New-Item -ItemType Directory -Path $distDir -Force | Out-Null

New-Item -ItemType Directory -Path $workDir -Force | Out-Null
 
# --- Build with PyInstaller (don’t rely on PATH) -----------------------------

$piArgs = @(

  '-m','PyInstaller',

  '--noconfirm','--clean',

  '--onefile','--noconsole',

  '--name',    $exeBase,

  '--distpath',$distDir,

  '--workpath',$workDir,

  '--specpath',$workDir

)
 
if (Test-Path $iconAbs) {

  $piArgs += "--icon=$iconAbs"

} else {

  Write-Warning "Icon not found at $iconAbs; continuing without --icon"

}
 
# Windows uses ';' between src and dest for --add-data

if (Test-Path $extraAbs) {

  $piArgs += @('--add-data', "$extraAbs;Icon")

} else {

  Write-Host "Extra data folder '$ExtraDir' not found; skipping --add-data"

}
 
$piArgs += $entry
 
Write-Host "Running: $($py) $($piArgs -join ' ')"
& $py $piArgs

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

if (-not (Test-Path $exePath)) { throw "Expected output not found: $exePath" }
 
# --- SHA256 in Linux-friendly format (no BOM, trailing newline) --------------

$hash = (Get-FileHash -Path $exePath -Algorithm SHA256).Hash.ToLower()

$line = "$hash *$exeName`n"

[System.IO.File]::WriteAllText($shaPath, $line, (New-Object System.Text.UTF8Encoding($false)))
 
Write-Host "Built: $exePath"

Write-Host "SHA256: $shaPath"
 