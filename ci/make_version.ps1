$ErrorActionPreference = 'Stop'
 
$t = $env:CODEBUILD_WEBHOOK_TRIGGER
if ($t -and $t.StartsWith('tag/')) {
  $v = $t.Substring(4)
} elseif ($env:CODEBUILD_BUILD_NUMBER) {
  $v = "build-$($env:CODEBUILD_BUILD_NUMBER)-$(Get-Date -Format 'yyyy.MM.dd-HHmm')"
} else {
  $v = "local-$(Get-Date -Format 'yyyy.MM.dd-HHmm')"
}
 
$line = "VERSION=$v"
 
# Write exactly this text, no CRLF and no BOM
Set-Content -Path "version.env" -Value $line -Encoding Ascii -NoNewline
# (Equivalent alternative)
# [IO.File]::WriteAllText("version.env", $line, (New-Object System.Text.UTF8Encoding($false)))
 
Write-Host $line