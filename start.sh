#!/bin/bash
echo "=========================================="
echo "  Serie A - Turneringsprogram"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "FEIL: Python er ikke installert!"
    echo "Last ned fra: https://www.python.org/downloads/"
    read -p "Trykk Enter for å lukke"
    exit 1
fi

echo "Sjekker Python..."
python3 --version

# Check/install Streamlit
echo ""
echo "Sjekker Streamlit..."
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "Installerer Streamlit..."
    pip3 install streamlit
fi

echo ""
echo "Starter Serie A..."
echo "Nettleseren skal åpne automatisk."
echo "Hold dette vinduet åpent mens du bruker programmet."
echo ""

python3 -m streamlit run app.py --client.toolbarMode minimal --server.fileWatcherType none --browser.gatherUsageStats false