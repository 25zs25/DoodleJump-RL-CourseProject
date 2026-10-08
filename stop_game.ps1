$taskSessionPath = Join-Path $PSScriptRoot 'server-session.json'
if (Test-Path -LiteralPath $taskSessionPath) {
  $taskSession = Get-Content -LiteralPath $taskSessionPath -Raw | ConvertFrom-Json
  $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskSession.pid)" -ErrorAction SilentlyContinue
  if ($taskProcess -and $taskProcess.CommandLine.Contains($taskSession.script)) { Stop-Process -Id $taskSession.pid }
}
