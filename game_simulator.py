import copy
import random
import uuid

BOARD_SIZE = 5
TEAM_PROFESSORS = {
    1: ["CLARO", "REY"],
    2: ["KARIN", "BEATRIZ"],
}
SETUP_ORDER = [1, 2, 1, 2]


def make_board_random_levels():
    board = []
    for _ in range(BOARD_SIZE):
        row = []
        for _ in range(BOARD_SIZE):
            row.append({"level": random.randint(0, 2), "professor": None})
        board.append(row)
    return board


def make_board_empty():
    return [[{"level": 0, "professor": None} for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def adjacent_cells(row, col):
    result = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr = row + dr
            nc = col + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                result.append((nr, nc))
    return result


def find_professor(board, name):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c]["professor"] == name:
                return (r, c)
    return None


def random_empty_cell(board):
    candidates = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c]["professor"] is None:
                candidates.append((r, c))
    return random.choice(candidates)


def place_all_professors_random(board):
    for professor in TEAM_PROFESSORS[1] + TEAM_PROFESSORS[2]:
        r, c = random_empty_cell(board)
        board[r][c]["professor"] = professor


def random_valid_setup(board):
    candidates = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c]["level"] == 0 and board[r][c]["professor"] is None:
                candidates.append((r, c))
    if not candidates:
        raise RuntimeError("Sem celula valida para setup")
    return random.choice(candidates)


def random_valid_player_turn(board, team_id):
    winning_moves = []
    candidate_moves = []

    for professor in TEAM_PROFESSORS[team_id]:
        pos = find_professor(board, professor)
        if pos is None:
            continue
        cur_row, cur_col = pos
        cur_level = board[cur_row][cur_col]["level"]

        for dst_row, dst_col in adjacent_cells(cur_row, cur_col):
            dst = board[dst_row][dst_col]
            if dst["professor"] is not None:
                continue
            if dst["level"] == 4:
                continue
            if dst["level"] > cur_level + 1:
                continue

            if dst["level"] == 3:
                winning_moves.append(
                    {
                        "professor": professor,
                        "move_to": {"row": dst_row, "col": dst_col},
                    }
                )
                continue

            for men_row, men_col in adjacent_cells(dst_row, dst_col):
                men = board[men_row][men_col]
                source_cell = (men_row, men_col) == (cur_row, cur_col)
                if (men["professor"] is None or source_cell) and men["level"] < 4:
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
    raise RuntimeError("Sem jogada valida para o time")


def validate_setup(board, team_id, professor, move):
    if not isinstance(move, dict):
        return "Resposta do setup deve ser objeto"
    if "row" not in move or "col" not in move:
        return "Setup precisa de row e col"
    row, col = move["row"], move["col"]
    if not (isinstance(row, int) and isinstance(col, int)):
        return "row/col do setup devem ser int"
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return "Setup fora do tabuleiro"
    cell = board[row][col]
    if cell["level"] != 0:
        return "Setup deve ser em celula nivel 0"
    if cell["professor"] is not None:
        return "Celula ocupada"
    return None


def validate_turn(board, team_id, move):
    if not isinstance(move, dict):
        return "Resposta do turno deve ser objeto"
    professor = move.get("professor")
    if professor not in TEAM_PROFESSORS.get(team_id, []):
        return "Professor invalido para o time"

    pos = find_professor(board, professor)
    if pos is None:
        return "Professor nao esta no tabuleiro"
    cur_row, cur_col = pos
    cur_level = board[cur_row][cur_col]["level"]

    move_to = move.get("move_to")
    if not isinstance(move_to, dict):
        return "move_to ausente ou invalido"
    dst_row, dst_col = move_to.get("row"), move_to.get("col")
    if not (isinstance(dst_row, int) and isinstance(dst_col, int)):
        return "move_to.row/col devem ser int"
    if not (0 <= dst_row < BOARD_SIZE and 0 <= dst_col < BOARD_SIZE):
        return "Destino fora do tabuleiro"
    if (dst_row, dst_col) not in adjacent_cells(cur_row, cur_col):
        return "Destino nao adjacente"

    dst = board[dst_row][dst_col]
    if dst["professor"] is not None:
        return "Destino ocupado"
    if dst["level"] == 4:
        return "Destino nivel 4"
    if dst["level"] > cur_level + 1:
        return "Subida de nivel maior que 1"

    if dst["level"] == 3:
        return None

    mentor = move.get("mentor_at")
    if not isinstance(mentor, dict):
        return "mentor_at ausente ou invalido"
    men_row, men_col = mentor.get("row"), mentor.get("col")
    if not (isinstance(men_row, int) and isinstance(men_col, int)):
        return "mentor_at.row/col devem ser int"
    if not (0 <= men_row < BOARD_SIZE and 0 <= men_col < BOARD_SIZE):
        return "mentor_at fora do tabuleiro"
    if (men_row, men_col) not in adjacent_cells(dst_row, dst_col):
        return "mentor_at nao adjacente ao destino"
    men = board[men_row][men_col]
    source_cell = (men_row, men_col) == (cur_row, cur_col)
    if men["professor"] is not None and not source_cell:
        return "Nao pode mentorar celula ocupada"
    if men["level"] == 4:
        return "Nao pode mentorar nivel 4"
    return None


def apply_setup(board, professor, move):
    new_board = copy.deepcopy(board)
    new_board[move["row"]][move["col"]]["professor"] = professor
    return new_board


def apply_turn(board, move):
    new_board = copy.deepcopy(board)
    professor = move["professor"]
    cur_row, cur_col = find_professor(new_board, professor)
    dst_row = move["move_to"]["row"]
    dst_col = move["move_to"]["col"]
    won = new_board[dst_row][dst_col]["level"] == 3

    new_board[cur_row][cur_col]["professor"] = None
    new_board[dst_row][dst_col]["professor"] = professor

    if not won:
        men_row = move["mentor_at"]["row"]
        men_col = move["mentor_at"]["col"]
        new_board[men_row][men_col]["level"] = min(4, new_board[men_row][men_col]["level"] + 1)

    return new_board, won


def build_payload(board, team_id, turn_number, turn_phase, professor_to_place=None, game_id=None):
    return {
        "game_id": game_id or str(uuid.uuid4()),
        "turn_number": turn_number,
        "turn_phase": turn_phase,
        "your_team": team_id,
        "board": copy.deepcopy(board),
        "professor_to_place": professor_to_place,
    }
