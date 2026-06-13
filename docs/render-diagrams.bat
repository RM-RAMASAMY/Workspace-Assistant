@echo off
setlocal
cd /d "%~dp0.."
set MMDC=npx --yes @mermaid-js/mermaid-cli@11.4.0

for %%f in (docs\diagrams\*.mmd) do (
  echo Rendering %%~nf...
  call %MMDC% -i "%%f" -o "docs\images\%%~nf.png" -b white -w 1600 -H 1200 2>nul
  if errorlevel 1 (
    echo Retry without size flags for %%~nf
    call %MMDC% -i "%%f" -o "docs\images\%%~nf.png" -b white
  )
)
echo Done.
