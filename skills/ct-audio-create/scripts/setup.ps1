# One-time setup of the voice readers (VieNeu-TTS v3 Turbo for Vietnamese, Kokoro-82M for English) on Windows 10 or 11, 64-bit. Safe to run again.
# Run it from PowerShell (the bypass applies to this one run only):
#   powershell -ExecutionPolicy Bypass -File .agents\skills\content-audio-create\scripts\setup.ps1
#
# Where things go (nothing goes into the repo, the system Python or your PATH setting; no account, token or admin rights):
#   %VIENEU_HOME% (default %USERPROFILE%\.vieneu-tts)  the Python 3.12 environment
#   %USERPROFILE%\.local\bin                           uv, the installer and Python manager (only when it is missing)
#   %HF_HOME% (default %USERPROFILE%\.cache\huggingface)  the Vietnamese voice model, about 540 MB
#   %VIENEU_HOME%\kokoro                              the English voice model (Kokoro v1.0 from GitHub), about 350 MB
# Total download about 1.5 GB, about 10 minutes. Delete the first folder to uninstall.
#
# NOTE: written for Windows but not yet run on a real Windows machine by the author. If a step fails, send the message to
# the person maintaining the skill; the Colab notebook (doc-bai-viet-vieneu.ipynb) is the fallback.
$ErrorActionPreference = "Stop"

$HomeDir = if ($env:VIENEU_HOME) { $env:VIENEU_HOME } else { Join-Path $env:USERPROFILE ".vieneu-tts" }
$Py = Join-Path $HomeDir ".venv\Scripts\python.exe"
$env:Path = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:Path"

function Run($exe, $argList) {
  & $exe @argList
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $exe $($argList -join ' ')" }
}
function TryRun($exe, $argList) {
  # Windows PowerShell 5.1 turns a native command's stderr into a terminating error under "Stop": relax it for this call.
  $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
  & $exe @argList *> $null
  $ok = ($LASTEXITCODE -eq 0)
  $ErrorActionPreference = $old
  return $ok
}

Write-Host "[0/6] checking this machine"
if (-not [Environment]::Is64BitOperatingSystem) { throw "A 64-bit Windows is needed." }
if (-not (Test-Path $Py)) {
  $drive = (Get-Item $env:USERPROFILE).PSDrive
  if ($drive.Free -lt 4GB) { throw "Need about 4 GB free on $($drive.Name): (found $([int]($drive.Free / 1MB)) MB)." }
}

Write-Host "[1/6] uv"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  $env:UV_NO_MODIFY_PATH = "1"   # keep the installer from changing the PATH setting
  Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
  if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv installed but not found; open a new PowerShell and run this script again." }
}

Write-Host "[2/6] Python 3.12 environment"
if (-not (Test-Path $Py)) { Run "uv" @("venv", "--python", "3.12", (Join-Path $HomeDir ".venv")) }

Write-Host "[3/6] vieneu 3.8.3 and ffmpeg (the version Sano pins)"
if (-not (TryRun $Py @("-c", "import vieneu, imageio_ffmpeg"))) {
  Run "uv" @("pip", "install", "--python", $Py, "vieneu==3.8.3", "imageio-ffmpeg")
}

Write-Host "[4/6] model download (about 540 MB, first time only; retries if the network drops)"
foreach ($try in 1..3) {
  if (TryRun $Py @("-c", "from vieneu import Vieneu; Vieneu()")) { break }
  Write-Host "  load attempt $try did not finish, trying again"
  Start-Sleep -Seconds 3
}

Write-Host "[5/6] turn the cache's symlinks into real files (onnxruntime refuses symlinked model files)"
$fix = @'
import glob, os, shutil
hf = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
n = 0
for snap in glob.glob(os.path.join(hf, "hub", "models--*", "snapshots", "*")):
    for root, _, files in os.walk(snap):
        for f in files:
            p = os.path.join(root, f)
            if os.path.islink(p):
                t = os.path.realpath(p); os.remove(p); shutil.copy2(t, p); n += 1
print("symlinks replaced:", n)
'@
$fix | & $Py -

Write-Host "[6/6] English voice: kokoro-onnx 0.6.1 and the Kokoro v1.0 model (about 350 MB, first time only)"
if (-not (TryRun $Py @("-c", "import kokoro_onnx"))) { Run "uv" @("pip", "install", "--python", $Py, "kokoro-onnx==0.6.1") }
$Kokoro = Join-Path $HomeDir "kokoro"
New-Item -ItemType Directory -Force $Kokoro | Out-Null
foreach ($f in @("kokoro-v1.0.onnx", "voices-v1.0.bin")) {
  $dest = Join-Path $Kokoro $f
  if (-not ((Test-Path $dest) -and (Get-Item $dest).Length -gt 0)) {
    $ProgressPreference = "SilentlyContinue"   # the progress bar makes Invoke-WebRequest many times slower
    Invoke-WebRequest "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f" -OutFile "$dest.part"
    Move-Item -Force "$dest.part" $dest
  }
}

if ((TryRun $Py @("-c", "from vieneu import Vieneu; Vieneu()")) -and (TryRun $Py @("-c", "import kokoro_onnx")) -and (Test-Path (Join-Path $Kokoro "voices-v1.0.bin"))) {
  Write-Host "READY: voice readers work (Vietnamese and English). Python: $Py"
} else {
  Write-Host "FAILED: the voice reader did not load. Check the network (Vietnamese model from huggingface.co, English from github.com) and run this script again."
  exit 1
}
