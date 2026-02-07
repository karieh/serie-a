Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "  Serie A - Turneringsprogram" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "Sjekker Python..."
try {
    python --version
} catch {
    Write-Host "FEIL: Python er ikke installert!" -ForegroundColor Red
    Write-Host "Last ned fra: https://www.python.org/downloads/"
    Write-Host 'Husk "Add Python to PATH"'
    Read-Host "Trykk Enter for aa lukke"
    exit 1
}

Write-Host ""
Write-Host "Sjekker Streamlit..."
$installed = pip show streamlit 2>$null
if (-not $installed) {
    Write-Host "Installerer Streamlit (dette tar et par minutter foerste gang)..."
    pip install streamlit
}

Write-Host ""
Write-Host "Starter Serie A..."
Write-Host "Nettleseren skal aapne automatisk."
Write-Host "Hold dette vinduet aapent mens du bruker programmet."
Write-Host ""

streamlit run app.py --client.toolbarMode minimal --server.fileWatcherType none --browser.gatherUsageStats false

Write-Host ""
Write-Host "Programmet har stoppet."
Read-Host "Trykk Enter for aa lukke"