# Serie A — Turneringsprogram

Turneringsprogram for Serie A, en sosial mix-turnering i sandvolleyball arrangert av [Oslo Sandvolleyballklubb](https://osvb.no).

## Kom i gang

### 0. Installer Python

Hvis du ikke har Python installert, last ned fra [python.org](https://www.python.org/downloads/) (versjon 3.10 eller nyere). Under installasjonen, huk av for **"Add Python to PATH"**.

Verifiser at det fungerer:

```bash
python --version
```

### 1. Klon prosjektet

```bash
git clone <repo-url>
cd serie_a
```

### 2. Installer avhengigheter

```bash
pip install streamlit
```

### 3. Start programmet

```bash
streamlit run app.py
```

Programmet åpnes automatisk i nettleseren på `http://localhost:8501`.

### 4. Opprett turnering

Ved første oppstart får du opp en dialog for å opprette en ny turnering. Lim inn spillerlistene (ett navn per linje) — damer i venstre felt, herrer i høyre — og trykk **Start ny turnering**.

## Bruk

- **Sidebar**: Administrer spillere (aktiver/deaktiver, legg til, rediger, slett)
- **Trekk ny runde**: Genererer lag basert på kjønn, tidligere partnere og motstandere
- **Registrer resultat**: Klikk på vinnerlaget per bane
- **Ledertavle**: Oppdateres automatisk, viser seiere per spiller

## Filer

| Fil | Beskrivelse |
|---|---|
| `app.py` | Streamlit-app, all UI |
| `db.py` | SQLite database-operasjoner |
| `engine.py` | Trekkalgoritme for lagsammensetning |
| `tournament.db` | Database (opprettes automatisk) |
| `osvb_logo.png` | OSVB-logo |