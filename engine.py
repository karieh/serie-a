"""
Serie A Tournament - Pairing Engine
Pure logic: takes players + history, returns pairings.
No database or UI dependencies — just data in, pairings out.
"""

import random
from itertools import combinations


def generate_round(
    players: list[dict],
    num_courts: int,
    past_partnerships: set[tuple[int, int]],
    past_opponents: dict[tuple[int, int], int],
    games_played: dict[int, int],
    wins: dict[int, int],
    num_attempts: int = 200,
    skip_selection: bool = False,
) -> list[dict]:
    """
    Generate pairings for one round.

    Args:
        players: List of active player dicts with keys: id, name, gender.
        num_courts: Number of available courts.
        past_partnerships: Set of (id1, id2) tuples of past partners.
        past_opponents: Dict of {(id1, id2): count} for past opponents.
        games_played: Dict of {player_id: total_games_played}.
        wins: Dict of {player_id: total_wins}.
        num_attempts: How many random candidates to generate and score.
        skip_selection: If True, use all provided players (for redraw).

    Returns:
        List of match dicts, each with keys:
            court, team1 (list of 2 player dicts), team2 (list of 2 player dicts)
    """
    if len(players) < 4:
        return []

    max_matches = min(num_courts, len(players) // 4)
    if max_matches == 0:
        return []

    # Select which players play this round
    if skip_selection:
        playing = list(players)
    else:
        playing = _select_players(players, max_matches * 4, games_played)

    # Generate many candidate pairings, score them, pick the best
    best_matches = None
    best_score = float("-inf")

    for _ in range(num_attempts):
        candidate = _generate_candidate(playing, max_matches, past_partnerships)
        if candidate is None:
            continue

        score = _score_candidate(candidate, past_partnerships, past_opponents, wins)
        if score > best_score:
            best_score = score
            best_matches = candidate

    if best_matches is None:
        # Fallback: just do a random assignment ignoring constraints
        best_matches = _generate_fallback(playing, max_matches)

    return best_matches


def _select_players(
    players: list[dict], needed: int, games_played: dict[int, int]
) -> list[dict]:
    """
    Select which players will play this round.
    Prioritize players who have played fewer games.
    """
    if len(players) <= needed:
        return list(players)

    # Sort by games played (ascending), with random tiebreaker
    shuffled = list(players)
    random.shuffle(shuffled)
    shuffled.sort(key=lambda p: games_played.get(p["id"], 0))

    return shuffled[:needed]


def _generate_candidate(
    players: list[dict], num_matches: int, past_partnerships: set[tuple[int, int]]
) -> list[dict] | None:
    """
    Generate one candidate set of matches.
    Tries to form mixed-gender pairs, avoids past partnerships.
    Returns None if it fails to form valid pairs.
    """
    shuffled = list(players)
    random.shuffle(shuffled)

    males = [p for p in shuffled if p["gender"] == "M"]
    females = [p for p in shuffled if p["gender"] == "F"]

    pairs = _form_pairs(males, females, past_partnerships)

    if len(pairs) < num_matches * 2:
        return None

    # Shuffle pairs and assign to matches
    random.shuffle(pairs)
    matches = []
    for i in range(num_matches):
        team1 = pairs[i * 2]
        team2 = pairs[i * 2 + 1]
        matches.append(
            {"court": i + 1, "team1": list(team1), "team2": list(team2)}
        )

    return matches


def _form_pairs(
    males: list[dict],
    females: list[dict],
    past_partnerships: set[tuple[int, int]],
) -> list[tuple[dict, dict]]:
    """
    Form player pairs, preferring mixed gender (M+F).
    Falls back to same-gender pairs when numbers don't balance.
    Tries to avoid past partnerships.
    """
    pairs = []
    used_m = set()
    used_f = set()

    # First pass: form mixed pairs, avoiding past partnerships
    random.shuffle(males)
    random.shuffle(females)

    for m in males:
        for f in females:
            if f["id"] in used_f:
                continue
            pair_key = (min(m["id"], f["id"]), max(m["id"], f["id"]))
            if pair_key not in past_partnerships:
                pairs.append((m, f))
                used_m.add(m["id"])
                used_f.add(f["id"])
                break
        if m["id"] in used_m:
            continue

    # Second pass: pair remaining males with remaining females (allow past partnerships)
    remaining_m = [m for m in males if m["id"] not in used_m]
    remaining_f = [f for f in females if f["id"] not in used_f]

    for m in remaining_m:
        for f in remaining_f:
            if f["id"] in used_f:
                continue
            pairs.append((m, f))
            used_m.add(m["id"])
            used_f.add(f["id"])
            break

    # Third pass: same-gender pairs for any leftovers
    leftover = [m for m in males if m["id"] not in used_m] + [
        f for f in females if f["id"] not in used_f
    ]
    random.shuffle(leftover)

    while len(leftover) >= 2:
        p1 = leftover.pop()
        # Try to find a partner they haven't played with
        best_idx = 0
        for idx, p2 in enumerate(leftover):
            pair_key = (min(p1["id"], p2["id"]), max(p1["id"], p2["id"]))
            if pair_key not in past_partnerships:
                best_idx = idx
                break
        p2 = leftover.pop(best_idx)
        pairs.append((p1, p2))

    return pairs


def _score_candidate(
    matches: list[dict],
    past_partnerships: set[tuple[int, int]],
    past_opponents: dict[tuple[int, int], int],
    wins: dict[int, int],
) -> float:
    """
    Score a candidate set of matches. Higher is better.

    Criteria:
    - Heavy penalty for repeated partnerships (hard constraint)
    - Penalty for repeated opponent pairings
    - Bonus for mixed-gender pairs
    - Penalty for skill imbalance across courts
    """
    score = 0.0

    for match in matches:
        t1 = match["team1"]
        t2 = match["team2"]

        # --- Partnership penalties ---
        for team in [t1, t2]:
            pair_key = (min(team[0]["id"], team[1]["id"]), max(team[0]["id"], team[1]["id"]))
            if pair_key in past_partnerships:
                score -= 100  # Heavy penalty

        # --- Opponent penalties ---
        for p1 in t1:
            for p2 in t2:
                opp_key = (min(p1["id"], p2["id"]), max(p1["id"], p2["id"]))
                times_faced = past_opponents.get(opp_key, 0)
                score -= times_faced * 10  # Escalating penalty

        # --- Mixed gender bonus ---
        for team in [t1, t2]:
            genders = {team[0]["gender"], team[1]["gender"]}
            if len(genders) == 2:  # Mixed pair
                score += 15

        # --- Skill balance across the match ---
        t1_wins = sum(wins.get(p["id"], 0) for p in t1)
        t2_wins = sum(wins.get(p["id"], 0) for p in t2)
        win_diff = abs(t1_wins - t2_wins)
        score -= win_diff * 2  # Penalize imbalanced matches

    return score


def _generate_fallback(players: list[dict], num_matches: int) -> list[dict]:
    """
    Simple random assignment as fallback when the scoring approach
    can't find valid candidates (e.g., very few players).
    """
    shuffled = list(players)
    random.shuffle(shuffled)

    matches = []
    for i in range(num_matches):
        start = i * 4
        group = shuffled[start: start + 4]
        if len(group) < 4:
            break
        matches.append(
            {"court": i + 1, "team1": group[:2], "team2": group[2:4]}
        )

    return matches