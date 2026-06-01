import random


def escolher_jogada(payload):
    """
    TEMPLATE PARA O DEV.

    Edite apenas esta funcao com seu algoritmo.

    Entrada (payload):
      {
        "game_id": 96,
        "turn_number": int,
        "turn_phase": "setup_placement" | "player_turn",
        "your_team": 1 | 2,
        "board": [[{"level": int, "professor": str|None}, ...], ...],
        "professor_to_place": str|None
      }

    Saida esperada:
      - setup_placement: {"row": int, "col": int}
      - player_turn: {
          "professor": str,
          "move_to": {"row": int, "col": int},
          "mentor_at": {"row": int, "col": int}
        }
        (se mover para nivel 3, mentor_at pode ser omitido)
    """
    board = payload["board"]
    turn_phase = payload["turn_phase"]
    team_id = payload["your_team"]

    if turn_phase == "setup_placement":
        candidates = []
        for r in range(5):
            for c in range(5):
                cell = board[r][c]
                if cell["level"] == 0 and cell["professor"] is None:
                    candidates.append((r, c))
        row, col = random.choice(candidates)
        return {"row": row, "col": col}

    return _random_valid_player_turn(board, team_id)


def _adjacent_cells(row, col):
    cells = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr = row + dr
            nc = col + dc
            if 0 <= nr < 5 and 0 <= nc < 5:
                cells.append((nr, nc))
    return cells


def _find_professor(board, professor_name):
    for r in range(5):
        for c in range(5):
            if board[r][c]["professor"] == professor_name:
                return (r, c)
    return None


def _random_valid_player_turn(board, team_id):
    team_professors = {1: ["CLARO", "REY"], 2: ["KARIN", "BEATRIZ"]}
    winning_moves = []
    candidate_moves = []

    for professor in team_professors[team_id]:
        pos = _find_professor(board, professor)
        if pos is None:
            continue

        cur_row, cur_col = pos
        cur_level = board[cur_row][cur_col]["level"]

        for dst_row, dst_col in _adjacent_cells(cur_row, cur_col):
            dst_cell = board[dst_row][dst_col]
            if dst_cell["professor"] is not None:
                continue
            if dst_cell["level"] == 4:
                continue
            if dst_cell["level"] > cur_level + 1:
                continue

            if dst_cell["level"] == 3:
                winning_moves.append(
                    {
                        "professor": professor,
                        "move_to": {"row": dst_row, "col": dst_col},
                    }
                )
                continue

            for men_row, men_col in _adjacent_cells(dst_row, dst_col):
                men_cell = board[men_row][men_col]
                mentoring_source_cell = (men_row, men_col) == (cur_row, cur_col)
                if (men_cell["professor"] is None or mentoring_source_cell) and men_cell["level"] < 4:
                    candidate_moves.append(
                        {
                            "professor": professor,
                            "move_to": {"row": dst_row, "col": dst_col},
                            "mentor_at": {"row": men_row, "col": men_col},
                        }
                    )

    if winning_moves:
        return random.choice(winning_moves)
    if candidate_moves:
        return random.choice(candidate_moves)
    raise RuntimeError("Nenhuma jogada valida encontrada para o time")
