@echo off
cd /d "%~dp0"
if not exist web\dist\index.html (
  pushd web
  call npm install
  call npm run build
  popd
)
start "" pyw -3.12 -m lumen.desktop
