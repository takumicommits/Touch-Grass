# Optionally launch an app, then screenshot the primary screen as proof.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File proof-win.ps1 [-App "C:\path\App.exe"] [-Out ".claude\proof\x.png"]
# Prints the path of the saved screenshot.
param([string]$App = "", [string]$Out = "")

if (-not $Out) { $Out = Join-Path ".claude\proof" ((Get-Date -Format "yyyyMMdd-HHmmss") + ".png") }
$full = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Out))
New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($full)) | Out-Null

if ($App) {
  Start-Process -FilePath $App
  Start-Sleep -Seconds 3
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output $full
