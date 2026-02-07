# Serie A — Turneringsprogram

Turneringsprogram for Serie A, en sosial mix-turnering i sandvolleyball arrangert av [Oslo Sandvolleyballklubb](https://osvb.no).

## Oppsett (gjøres én gang)

### 1. Installer Python

Last ned fra [python.org](https://www.python.org/downloads/) (versjon 3.10 eller nyere).

**Viktig:** Huk av for **"Add Python to PATH"** under installasjonen.

### 2. Last ned prosjektet

Last ned eller klon prosjektet og legg mappen et fast sted, f.eks. `C:\serie_a\`:

```bash
git clone https://github.com/karieh/serie-a
```

### 3. Installer Streamlit

Åpne en terminal i prosjektmappen og kjør:

```bash
pip install streamlit
```

### 4. Verifiser at det fungerer

Dobbeltklikk `Serie A.vbs` i prosjektmappen. En nettleser skal åpne seg med programmet.

### 5. Lag snarvei på skrivebordet

1. Høyreklikk `Serie A.vbs` → **Send til** → **Skrivebord (lag snarvei)**
2. Gi snarveien navnet **Serie A**

Turneringslederen dobbeltklikker snarveien på skrivebordet for å starte programmet.

## Første oppstart

Ved første oppstart får du opp en dialog for å opprette en ny turnering. Lim inn spillerlistene (ett navn per linje) — damer i venstre felt, herrer i høyre — og trykk **Start ny turnering**.

## Bruk

- **Sidebar**: Administrer spillere (aktiver/deaktiver, legg til, rediger, slett)
- **Trekk ny runde**: Genererer lag basert på klasse, tidligere partnere og motstandere
- **Registrer resultat**: Klikk på vinnerlaget per bane
- **Ledertavle**: Oppdateres automatisk, viser seiere per spiller

## Filer

| Fil | Beskrivelse |
|---|---|
| `app.py` | Streamlit-app (UI) |
| `db.py` | SQLite database-operasjoner |
| `engine.py` | Trekkalgoritme for lagsammensetning |
| `start.ps1` | PowerShell-script som starter programmet |
| `Serie A.vbs` | Snarvei-launcher (dobbeltklikk for å starte) |
| `tournament.db` | Database (opprettes automatisk) |
| `osvb_logo.png` | OSVB-logo |