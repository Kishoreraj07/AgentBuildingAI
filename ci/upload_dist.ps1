$ErrorActionPreference = 'Stop'
$ver    = (Get-Content version.env) -replace 'VERSION=',''
$bucket = $env:BUCKET
$region = $env:REGION
$dst    = "s3://$bucket/aba/$ver/"

Write-Host "Uploading dist to $dst"
aws s3 cp dist $dst --recursive --region $region
