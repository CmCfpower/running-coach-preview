param(
  [int]$Port = 4173,
  [string]$HostName = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$Root\..\.."
$NodeCandidates = @(@(
  "$ProjectRoot\.tools\node-v24.15.0-win-x64\node.exe",
  (Get-Command node -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
  "$env:LOCALAPPDATA\OpenAI\Codex\bin\node.exe"
) | Where-Object { $_ -and (Test-Path $_) })

if ($NodeCandidates.Count -gt 0) {
  $env:PORT = "$Port"
  $env:HOST = "$HostName"
  $NodePath = $NodeCandidates.Item(0)
  & $NodePath "$Root\server.mjs"
  exit $LASTEXITCODE
}

$Prefix = "http://$HostName`:$Port/"
$ContentTypes = @{
  ".html" = "text/html; charset=utf-8"
  ".css" = "text/css; charset=utf-8"
  ".js" = "text/javascript; charset=utf-8"
}

$Listener = [System.Net.HttpListener]::new()
$Listener.Prefixes.Add($Prefix)

try {
  $Listener.Start()
  Write-Host "Roadmap page: $Prefix"
  Write-Host "Press Ctrl+C to stop."

  while ($Listener.IsListening) {
    $Context = $Listener.GetContext()
    $RequestPath = [Uri]::UnescapeDataString($Context.Request.Url.AbsolutePath)
    if ($RequestPath -eq "/") {
      $RequestPath = "/index.html"
    }

    $RelativePath = $RequestPath.TrimStart("/") -replace "/", "\"
    $FilePath = [System.IO.Path]::GetFullPath((Join-Path $Root $RelativePath))

    if (-not $FilePath.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
      $Context.Response.StatusCode = 403
      $Context.Response.Close()
      continue
    }

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
      $Bytes = [System.Text.Encoding]::UTF8.GetBytes("Not found")
      $Context.Response.StatusCode = 404
      $Context.Response.ContentType = "text/plain; charset=utf-8"
      $Context.Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
      $Context.Response.Close()
      continue
    }

    $Extension = [System.IO.Path]::GetExtension($FilePath)
    $Context.Response.ContentType = $ContentTypes[$Extension]
    if (-not $Context.Response.ContentType) {
      $Context.Response.ContentType = "application/octet-stream"
    }

    $Bytes = [System.IO.File]::ReadAllBytes($FilePath)
    $Context.Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
    $Context.Response.Close()
  }
}
finally {
  if ($Listener.IsListening) {
    $Listener.Stop()
  }
  $Listener.Close()
}
