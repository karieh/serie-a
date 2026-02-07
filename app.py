"""
Serie A Tournament - Streamlit App
All UI in one file. Uses db.py for data, engine.py for pairings.
"""

import streamlit as st
import db
import engine

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NUM_COURTS = 5
MAX_PLAYERS = 40
TOTAL_ROUNDS = 12

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Serie A", layout="wide", page_icon="🏐")

db.init_db()

# If database is empty (fresh start or after reset), prompt for new tournament
if not db.get_all_players():
    st.session_state.show_new_tournament = True
    st.session_state.edit_mode = False

# Tournament settings in session state
if "num_courts" not in st.session_state:
    st.session_state.num_courts = NUM_COURTS
if "total_rounds" not in st.session_state:
    st.session_state.total_rounds = TOTAL_ROUNDS


# ---------------------------------------------------------------------------
# New Tournament Dialog
# ---------------------------------------------------------------------------
@st.dialog("🆕 Ny turnering", width="large")
def render_new_tournament_dialog():
    is_edit = st.session_state.get("edit_mode", False)

    if is_edit:
        st.info("Rediger spillerlistene før første runde trekkes. Endringene erstatter alle nåværende spillere.")
    else:
        st.warning("⚠️ Dette sletter alle spillere, runder og resultater fra nåværende turnering.")

    # Pre-fill with existing players if editing
    existing_males = ""
    existing_females = ""
    if is_edit:
        all_players = db.get_all_players()
        existing_males = "\n".join(p["name"] for p in all_players if p["gender"] == "M")
        existing_females = "\n".join(p["name"] for p in all_players if p["gender"] == "F")

    col_f, col_m = st.columns(2)
    with col_f:
        females_text = st.text_area(
            "🟢 Damer (ett navn per linje)",
            value=existing_females,
            height=300,
            placeholder="Kari Nordmann\nLisa Olsen\n...",
            key="new_females",
        )
    with col_m:
        males_text = st.text_area(
            "🔵 Herrer (ett navn per linje)",
            value=existing_males,
            height=300,
            placeholder="Ola Nordmann\nPer Hansen\n...",
            key="new_males",
        )

    # Preview counts
    male_names = [n.strip() for n in males_text.strip().splitlines() if n.strip() and not n.strip().startswith("#")]
    female_names = [n.strip() for n in females_text.strip().splitlines() if n.strip() and not n.strip().startswith("#")]
    st.caption(f"{len(female_names)} damer, {len(male_names)} herrer — {len(male_names) + len(female_names)} totalt")

    button_label = "💾 Oppdater spillere" if is_edit else "🚀 Start ny turnering"

    col1, col2 = st.columns(2)
    with col1:
        if st.button(button_label, type="primary", use_container_width=True):
            if len(male_names) + len(female_names) < 4:
                st.error("Legg til minst 4 spillere")
            else:
                db.reset_tournament()
                for name in male_names:
                    db.add_player(name, "M")
                for name in female_names:
                    db.add_player(name, "F")
                st.session_state.show_new_tournament = False
                st.session_state.edit_mode = False
                st.rerun()
    with col2:
        if st.button("Avbryt", use_container_width=True):
            st.session_state.show_new_tournament = False
            st.session_state.edit_mode = False
            st.rerun()


# ---------------------------------------------------------------------------
# Sidebar: Player Management
# ---------------------------------------------------------------------------
def render_sidebar():
    st.sidebar.image("osvb_logo.png", width=200)

    # --- Tournament settings ---
    with st.sidebar.expander("⚙️ Innstillinger"):
        st.session_state.num_courts = st.number_input(
            "Antall baner", min_value=1, max_value=10,
            value=st.session_state.num_courts
        )
        st.session_state.total_rounds = st.number_input(
            "Antall runder", min_value=1, max_value=50,
            value=st.session_state.total_rounds
        )

    # --- New tournament / Edit lists ---
    has_players = len(db.get_all_players()) > 0
    has_rounds = db.get_round_count() > 0

    if not has_players or has_rounds:
        if st.sidebar.button("🆕 Ny turnering", use_container_width=True):
            close_edit_form()
            st.session_state.edit_mode = False
            st.session_state.show_new_tournament = True
    else:
        if st.sidebar.button("📋 Rediger spillerlister", use_container_width=True):
            close_edit_form()
            st.session_state.edit_mode = True
            st.session_state.show_new_tournament = True

    if st.session_state.get("show_new_tournament", False):
        render_new_tournament_dialog()

    # --- Add new player ---
    with st.sidebar.expander("➕ Legg til spiller"):
        with st.form("add_player", clear_on_submit=True):
            new_name = st.text_input("Navn")
            new_gender = st.selectbox(
                "Klasse",
                ["Velg klasse", "F", "M"],
                format_func=lambda x: {"Velg klasse": "Velg klasse", "F": "Dame", "M": "Herre"}[x]
            )
            if st.form_submit_button("Legg til"):
                if not new_name.strip():
                    st.error("Skriv inn et navn")
                elif new_gender == "Velg klasse":
                    st.error("Velg klasse")
                else:
                    db.add_player(new_name, new_gender)
                    st.rerun()

    st.sidebar.markdown("---")

    # --- Player list with activation toggles ---
    st.sidebar.subheader("👥 Spillere")

    all_players = db.get_all_players()
    active_count = sum(1 for p in all_players if p["active"])
    st.sidebar.caption(f"{active_count} aktive av {len(all_players)} spillere")

    # Quick actions
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("✓ Alle på", use_container_width=True):
            db.set_all_players_active(True)
            st.rerun()
    with col2:
        if st.button("✗ Alle av", use_container_width=True):
            db.set_all_players_active(False)
            st.rerun()

    # Search
    search = st.sidebar.text_input("🔍 Søk", key="player_search", placeholder="Skriv og trykk Enter")

    # Player toggles grouped by gender
    males = [p for p in all_players if p["gender"] == "M"]
    females = [p for p in all_players if p["gender"] == "F"]

    for label, group in [("🟢 Damer", females), ("🔵 Herrer", males)]:
        filtered = [p for p in group if search.lower() in p["name"].lower()] if search else group
        if not filtered:
            continue
        active_in_group = sum(1 for p in filtered if p["active"])
        with st.sidebar.expander(f"{label} ({active_in_group}/{len(filtered)})", expanded=True):
            for p in filtered:
                col_check, col_edit = st.columns([5, 1])
                with col_check:
                    active = st.checkbox(
                        p["name"], value=bool(p["active"]),
                        key=f"player_{p['id']}"
                    )
                    if active != bool(p["active"]):
                        db.set_player_active(p["id"], active)
                        st.rerun()
                with col_edit:
                    if st.button("✏️", key=f"edit_{p['id']}", help="Rediger"):
                        if st.session_state.get("editing_player_id") == p["id"]:
                            st.session_state.editing_player_id = None
                        else:
                            st.session_state.editing_player_id = p["id"]
                        st.session_state.pop("confirm_delete", None)
                        st.rerun()

                # Inline edit form
                if st.session_state.get("editing_player_id") == p["id"]:
                    with st.form(f"edit_form_{p['id']}"):
                        edit_name = st.text_input("Navn", value=p["name"], key=f"ename_{p['id']}")
                        edit_gender = st.selectbox(
                            "Klasse", ["F", "M"],
                            index=0 if p["gender"] == "F" else 1,
                            format_func=lambda x: "Dame" if x == "F" else "Herre",
                            key=f"egender_{p['id']}"
                        )
                        # Row 1: Save and Cancel
                        r1c1, r1c2 = st.columns(2)
                        with r1c1:
                            if st.form_submit_button("Lagre", use_container_width=True):
                                db.update_player(p["id"], name=edit_name, gender=edit_gender)
                                st.session_state.editing_player_id = None
                                st.session_state.pop("confirm_delete", None)
                                st.rerun()
                        with r1c2:
                            if st.form_submit_button("Avbryt", use_container_width=True):
                                st.session_state.editing_player_id = None
                                st.session_state.pop("confirm_delete", None)
                                st.rerun()
                        # Row 2: Pause/Activate and Delete
                        r2c1, r2c2 = st.columns(2)
                        with r2c1:
                            pause_label = "Sett aktiv" if not p["active"] else "Sett på pause"
                            if st.form_submit_button(pause_label, use_container_width=True):
                                db.set_player_active(p["id"], not p["active"])
                                st.session_state.editing_player_id = None
                                st.session_state.pop("confirm_delete", None)
                                st.rerun()
                        with r2c2:
                            if not st.session_state.get("confirm_delete", False):
                                if st.form_submit_button("🗑️ Slett", use_container_width=True):
                                    st.session_state.confirm_delete = True
                                    st.rerun()
                            else:
                                if st.form_submit_button("⚠️ Er du sikker?", use_container_width=True):
                                    db.soft_delete_player(p["id"])
                                    st.session_state.editing_player_id = None
                                    st.session_state.pop("confirm_delete", None)
                                    st.rerun()


# ---------------------------------------------------------------------------
# Main: Round Controls
# ---------------------------------------------------------------------------
def close_edit_form():
    """Close any open player edit form."""
    st.session_state.pop("editing_player_id", None)
    st.session_state.pop("confirm_delete", None)

def render_round_controls():
    current_round = db.get_current_round()
    round_count = db.get_round_count()
    total = st.session_state.total_rounds
    active_players = db.get_active_players()

    # Header row
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col2:
        st.metric("Runde", f"{round_count} / {total}")
    with col3:
        st.metric("Aktive", len(active_players))
    with col4:
        males = sum(1 for p in active_players if p["gender"] == "M")
        females = sum(1 for p in active_players if p["gender"] == "F")
        st.metric("M / F", f"{males} / {females}")

    with col1:
        # Determine button state
        can_draw = True
        button_label = "🎲 Trekk ny runde"
        help_text = None

        if round_count >= total:
            button_label = "🎲 Trekk ekstra runde"
            help_text = f"Planlagte {total} runder er fullført"

        if len(active_players) < 4:
            can_draw = False
            help_text = "Minst 4 aktive spillere trengs"

        if current_round and not db.round_is_complete(current_round["id"]):
            matches = db.get_matches_for_round(current_round["id"])
            missing = sum(1 for m in matches if m["winner"] is None)
            can_draw = False
            help_text = f"{missing} kamper mangler resultat"

        if st.button(button_label, type="primary", use_container_width=True,
                     disabled=not can_draw, help=help_text):
            close_edit_form()
            draw_new_round()

    # Undo / Redraw controls
    if current_round:
        has_results = db.round_has_any_results(current_round["id"])
        col_undo, col_redraw, _ = st.columns([1, 1, 4])

        with col_undo:
            if st.button("↩️ Angre runde", disabled=has_results,
                         help="Slett siste runde (kun før resultater)" if not has_results else "Kan ikke angre etter resultater er registrert",
                         use_container_width=True):
                close_edit_form()
                db.delete_round(current_round["id"])
                st.rerun()

        with col_redraw:
            if st.button("🔄 Trekk på nytt", disabled=has_results,
                         help="Generer nye lag for denne runden" if not has_results else "Kan ikke trekke på nytt etter resultater er registrert",
                         use_container_width=True):
                # Get the players from the current round BEFORE deleting
                close_edit_form()
                matches = db.get_matches_for_round(current_round["id"])
                playing_ids = set()
                for m in matches:
                    playing_ids.update([m["team1_p1"], m["team1_p2"], m["team2_p1"], m["team2_p2"]])
                db.delete_round(current_round["id"])
                draw_new_round(locked_player_ids=playing_ids)


def draw_new_round(locked_player_ids: set[int] = None):
    """Generate a new round using the engine and save to database.
    
    Args:
        locked_player_ids: If provided (redraw), only these players are used.
                          The engine skips player selection and just re-pairs them.
    """
    active_players = db.get_active_players()
    past_partnerships = db.get_all_past_partnerships()
    past_opponents = db.get_all_past_opponents()
    games_played = db.get_games_played_counts()
    wins_counts = db.get_wins_counts()

    if locked_player_ids:
        # Redraw: use the same players, just re-pair them
        players_for_engine = [p for p in active_players if p["id"] in locked_player_ids]
    else:
        players_for_engine = active_players

    matches = engine.generate_round(
        players=players_for_engine,
        num_courts=st.session_state.num_courts,
        past_partnerships=past_partnerships,
        past_opponents=past_opponents,
        games_played=games_played,
        wins=wins_counts,
        skip_selection=locked_player_ids is not None,
    )

    if not matches:
        st.error("Kunne ikke generere runde. For få spillere?")
        return

    round_id = db.create_round()
    for match in matches:
        db.create_match(
            round_id=round_id,
            court_number=match["court"],
            team1_p1=match["team1"][0]["id"],
            team1_p2=match["team1"][1]["id"],
            team2_p1=match["team2"][0]["id"],
            team2_p2=match["team2"][1]["id"],
        )
    st.rerun()


# ---------------------------------------------------------------------------
# Main: Court Display
# ---------------------------------------------------------------------------
def render_courts():
    current_round = db.get_current_round()
    if not current_round:
        st.info("👆 Klikk 'Trekk ny runde' for å starte turneringen!")
        return

    matches = db.get_matches_for_round(current_round["id"])
    if not matches:
        return

    # Display courts in a grid
    num_cols = min(3, len(matches))
    rows = (len(matches) + num_cols - 1) // num_cols

    for row in range(rows):
        cols = st.columns(num_cols)
        for col_idx in range(num_cols):
            match_idx = row * num_cols + col_idx
            if match_idx >= len(matches):
                continue
            with cols[col_idx]:
                render_single_court(matches[match_idx])

    # Show who's sitting out
    playing_ids = set()
    for m in matches:
        playing_ids.update([m["team1_p1"], m["team1_p2"], m["team2_p1"], m["team2_p2"]])

    active_players = db.get_active_players()
    sitting_out = [p for p in active_players if p["id"] not in playing_ids]

    if sitting_out:
        with st.expander(f"📋 Pause denne runden ({len(sitting_out)} spillere)"):
            names = ", ".join(p["name"] for p in sitting_out)
            st.write(names)


def render_single_court(match: dict):
    """Render a single court with two teams and result buttons."""
    done = match["winner"] is not None

    with st.container(border=True):
        # Header
        status = " ✅" if done else ""
        st.markdown(f"**Bane {match['court_number']}{status}**")

        # Team display with net divider
        col_a, col_net, col_b = st.columns([5, 1, 5])

        with col_a:
            gender1 = "♂" if match["t1p1_gender"] == "M" else "♀"
            gender2 = "♂" if match["t1p2_gender"] == "M" else "♀"
            st.markdown(f"{gender1} {match['t1p1_name']}")
            st.markdown(f"{gender2} {match['t1p2_name']}")

        with col_net:
            st.markdown(
                '<div style="border-left: 2px dashed; height: 60px; margin: 0 auto; width: 0;"></div>',
                unsafe_allow_html=True,
            )

        with col_b:
            gender1 = "♂" if match["t2p1_gender"] == "M" else "♀"
            gender2 = "♂" if match["t2p2_gender"] == "M" else "♀"
            st.markdown(f"{gender1} {match['t2p1_name']}")
            st.markdown(f"{gender2} {match['t2p2_name']}")

        # Result buttons
        btn_a, btn_b = st.columns(2)

        with btn_a:
            if match["winner"] == 1:
                st.button("🏆 Lag 1", key=f"t1_{match['id']}", disabled=True, use_container_width=True)
            elif match["winner"] == 2:
                st.button("Lag 1", key=f"t1_{match['id']}", disabled=True, use_container_width=True)
            else:
                if st.button("Lag 1", key=f"t1_{match['id']}", use_container_width=True):
                    db.record_result(match["id"], 1)
                    st.rerun()

        with btn_b:
            if match["winner"] == 2:
                st.button("🏆 Lag 2", key=f"t2_{match['id']}", disabled=True, use_container_width=True)
            elif match["winner"] == 1:
                st.button("Lag 2", key=f"t2_{match['id']}", disabled=True, use_container_width=True)
            else:
                if st.button("Lag 2", key=f"t2_{match['id']}", use_container_width=True):
                    db.record_result(match["id"], 2)
                    st.rerun()

        # Allow changing result
        if done:
            if st.button("↩️ Endre resultat", key=f"undo_{match['id']}",
                         use_container_width=True):
                db.clear_result(match["id"])
                st.rerun()


# ---------------------------------------------------------------------------
# Main: Leaderboard
# ---------------------------------------------------------------------------
def render_leaderboard():
    leaderboard = db.get_leaderboard()
    if not leaderboard:
        return

    st.subheader("🏆 Ledertavle")

    # Check for ties at the top
    if len(leaderboard) >= 2 and leaderboard[0]["wins"] == leaderboard[1]["wins"]:
        tied = [p for p in leaderboard if p["wins"] == leaderboard[0]["wins"]]
        st.info(f"⚡ {len(tied)} spillere deler førsteplassen med {leaderboard[0]['wins']} seiere!")

    # Split into male and female leaderboards
    col_all, col_f, col_m = st.tabs(["Alle", "Damer 🟢", "Herrer 🔵"])

    with col_all:
        _render_leaderboard_table(leaderboard)
    with col_f:
        _render_leaderboard_table([p for p in leaderboard if p["gender"] == "F"])
    with col_m:
        _render_leaderboard_table([p for p in leaderboard if p["gender"] == "M"])


def _render_leaderboard_table(players: list[dict]):
    if not players:
        st.caption("Ingen resultater ennå")
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for idx, p in enumerate(players, 1):
        medal = medals.get(idx, f"{idx}.")
        col_rank, col_name, col_wins, col_games = st.columns([1, 4, 2, 2])
        with col_rank:
            st.write(medal)
        with col_name:
            gender = "♂" if p["gender"] == "M" else "♀"
            st.write(f"{gender} {p['name']}")
        with col_wins:
            st.write(f"**{p['wins']}** seiere")
        with col_games:
            st.write(f"{p['games_played']} kamper")


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
render_sidebar()

st.title("🏐 Serie A")
st.markdown("---")

render_round_controls()
st.markdown("---")
render_courts()
st.markdown("---")
render_leaderboard()