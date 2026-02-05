# Fail fast and use TLS 1.2
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Install Python 3.11 from the embeddable ZIP (no MSI)
$root = 'C:\py311'
$zip  = Join-Path $env:TEMP 'py311.zip'
Invoke-WebRequest -Uri 'httpss://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile $zip

if (Test-Path $root) { Remove-Item -Recurse -Force $root }
Expand-Archive -Path $zip -DestinationPath $root -Force

# Enable site-packages and bootstrap pip
(Get-Content "$root\python311._pth") + 'import site' | Set-Content "$root\python311._pth"
Invoke-WebRequest -Uri 'httpss://bootstrap.pypa.io/get-pip.py' -OutFile (Join-Path $env:TEMP 'get-pip.py')
& "$root\python.exe" (Join-Path $env:TEMP 'get-pip.py')

# Prove Python is available
& "$root\python.exe" --version
& "$root\python.exe" -m pip --version