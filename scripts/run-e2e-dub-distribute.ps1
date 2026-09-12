# MS-F：英文配音出海 + 租户官网分发 E2E（需 dev 栈 + edge-tts + ffmpeg）
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$WingetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
if (Test-Path $WingetLinks) { $env:Path = "$WingetLinks;$env:Path" }
try {
  $ff = & where.exe ffmpeg 2>$null | Select-Object -First 1
  if ($ff) {
    $ff = $ff.Trim()
    $item = Get-Item -LiteralPath $ff -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType -eq 'SymbolicLink' -and $item.Target) {
      $env:FFMPEG_PATH = ($item.Target | Select-Object -First 1)
    } else {
      $env:FFMPEG_PATH = $ff
    }
  }
} catch {}
Set-Location (Join-Path $Root 'backend')
& (Join-Path $Root 'backend\.venv\Scripts\python.exe') (Join-Path $Root 'scripts\e2e_cross_border_dub_distribute.py')
exit $LASTEXITCODE
