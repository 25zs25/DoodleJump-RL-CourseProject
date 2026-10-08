param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $taskPython -and (Test-Path -LiteralPath 'D:/Anaconda/python.exe')) { $taskPython = 'D:/Anaconda/python.exe' }
if (-not $taskPython) { Write-Host 'Install Python 3, then run start_game.cmd. PyTorch is only needed for training.'; Read-Host 'Enter to exit'; exit 1 }
$taskPort = 8765
while ($taskPort -lt 8800) {
  $taskProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$taskPort)
  try { $taskProbe.Start(); $taskProbe.Stop(); break } catch { $taskPort++ }
}
$taskServer = Join-Path $taskRoot 'serve.py'
$taskProcess = Start-Process -FilePath $taskPython -ArgumentList @(('"' + $taskServer + '"'),'--port',"$taskPort") -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru
@{ pid = $taskProcess.Id; port = $taskPort; script = $taskServer } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'server-session.json') -Encoding UTF8
Start-Sleep -Milliseconds 700
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$taskPort/" }
Write-Host "Game opened at http://127.0.0.1:$taskPort/. Run stop_game.ps1 when finished."
