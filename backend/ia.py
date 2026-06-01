import time

TEAM_PROFESSORS = {1: ["CLARO", "REY"], 2: ["KARIN", "BEATRIZ"]}
INF = float("inf")
WIN_SCORE = 100_000

_SETUP_PRIORITY = [
    (2, 2),
    (1, 2), (2, 1), (2, 3), (3, 2),
    (1, 1), (1, 3), (3, 1), (3, 3),
    (0, 2), (2, 0), (2, 4), (4, 2),
    (0, 1), (1, 0), (0, 3), (3, 0), (1, 4), (4, 1), (3, 4), (4, 3),
    (0, 0), (0, 4), (4, 0), (4, 4),
]

_TT: dict = {}
_start_time: float = 0.0
_TIME_LIMIT: float = 3.0



#Interface pública


def escolher_jogada(payload):
    board = payload["board"]
    turn_phase = payload["turn_phase"]
    team_id = payload["your_team"]

    if turn_phase == "setup_placement":
        return _smart_setup(board)
    return _smart_turn(board, team_id)



#Setup


def _smart_setup(board):
    for r, c in _SETUP_PRIORITY:
        if board[r][c]["professor"] is None and board[r][c]["level"] == 0:
            return {"row": r, "col": c}
    for r in range(5):
        for c in range(5):
            if board[r][c]["professor"] is None and board[r][c]["level"] == 0:
                return {"row": r, "col": c}



#Turno principal


def _smart_turn(board, team_id):
    global _start_time, _TT
    _start_time = time.time()
    _TT = {}
    opponent_id = 3 - team_id

    #vitória imediata: não precisa de minimax
    for professor in TEAM_PROFESSORS[team_id]:
        pos = _find_professor(board, professor)
        if pos is None:
            continue
        cur_r, cur_c = pos
        if board[cur_r][cur_c]["level"] < 2:
            continue
        for dst_r, dst_c in _adjacent_cells(cur_r, cur_c):
            if board[dst_r][dst_c]["professor"] is None and board[dst_r][dst_c]["level"] == 3:
                return {"professor": professor, "move_to": {"row": dst_r, "col": dst_c}}

    moves = _generate_moves(board, team_id)
    if not moves:
        return _any_valid_move(board, team_id)

    #iterative deepening: começa em profundidade 2, sobe enquanto tiver tempo
    best_move = _order_moves(board, moves, team_id, opponent_id)[0]
    for depth in range(2, 5):
        if _elapsed() > _TIME_LIMIT * 0.6:
            break
        result = _root_search(board, moves, depth, team_id, opponent_id)
        if result is not None:
            best_move = result
        if _elapsed() > _TIME_LIMIT * 0.75:
            break

    return best_move


def _root_search(board, moves, depth, team_id, opponent_id):
    ordered = _order_moves(board, moves, team_id, opponent_id)
    best_score = -INF
    best_move = None
    alpha = -INF

    for move in ordered:
        if _elapsed() > _TIME_LIMIT * 0.8:
            break
        undo_info = _make_move(board, move)
        if undo_info[7]:  
            _undo_move(board, *undo_info)
            return move
        score = _minimax(board, depth - 1, alpha, INF, False, team_id, opponent_id)
        _undo_move(board, *undo_info)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)

    return best_move



#Minimax + Alpha-Beta 


def _minimax(board, depth, alpha, beta, maximizing, team_id, opponent_id):
    if _elapsed() > _TIME_LIMIT * 0.85:
        return _evaluate(board, team_id, opponent_id)

    key = (_board_hash(board), depth, maximizing)
    if key in _TT:
        return _TT[key]

    if depth == 0:
        val = _evaluate(board, team_id, opponent_id)
        _TT[key] = val
        return val

    current = team_id if maximizing else opponent_id
    other = opponent_id if maximizing else team_id
    moves = _generate_moves(board, current)

    if not moves:
        #time sem jogadas perde
        val = -WIN_SCORE if maximizing else WIN_SCORE
        _TT[key] = val
        return val

    ordered = _order_moves(board, moves, current, other)

    if maximizing:
        value = -INF
        for move in ordered:
            undo_info = _make_move(board, move)
            if undo_info[7]:  #won — vitória para o maximizador
                _undo_move(board, *undo_info)
                _TT[key] = WIN_SCORE
                return WIN_SCORE
            value = max(value, _minimax(board, depth - 1, alpha, beta, False, team_id, opponent_id))
            _undo_move(board, *undo_info)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = INF
        for move in ordered:
            undo_info = _make_move(board, move)
            if undo_info[7]:  #won — vitória para o minimizador (derrota nossa)
                _undo_move(board, *undo_info)
                _TT[key] = -WIN_SCORE
                return -WIN_SCORE
            value = min(value, _minimax(board, depth - 1, alpha, beta, True, team_id, opponent_id))
            _undo_move(board, *undo_info)
            beta = min(beta, value)
            if alpha >= beta:
                break

    _TT[key] = value
    return value



#Make/Undo (sem deepcopy)


def _make_move(board, move):
    professor = move["professor"]
    cur_r, cur_c = _find_professor(board, professor)
    dst_r = move["move_to"]["row"]
    dst_c = move["move_to"]["col"]
    won = board[dst_r][dst_c]["level"] == 3

    board[cur_r][cur_c]["professor"] = None
    board[dst_r][dst_c]["professor"] = professor

    build_r = build_c = old_build_level = None
    if not won and "mentor_at" in move:
        build_r = move["mentor_at"]["row"]
        build_c = move["mentor_at"]["col"]
        old_build_level = board[build_r][build_c]["level"]
        board[build_r][build_c]["level"] += 1

    return cur_r, cur_c, dst_r, dst_c, build_r, build_c, old_build_level, won


def _undo_move(board, cur_r, cur_c, dst_r, dst_c, build_r, build_c, old_build_level, won):
    professor = board[dst_r][dst_c]["professor"]
    board[dst_r][dst_c]["professor"] = None
    board[cur_r][cur_c]["professor"] = professor
    if build_r is not None:
        board[build_r][build_c]["level"] = old_build_level



#Geração e ordenação de jogadas


def _generate_moves(board, team_id):
    moves = []
    for professor in TEAM_PROFESSORS[team_id]:
        pos = _find_professor(board, professor)
        if pos is None:
            continue
        cur_r, cur_c = pos
        cur_level = board[cur_r][cur_c]["level"]

        for dst_r, dst_c in _adjacent_cells(cur_r, cur_c):
            dst = board[dst_r][dst_c]
            if dst["professor"] is not None or dst["level"] == 4 or dst["level"] > cur_level + 1:
                continue

            if dst["level"] == 3:
                moves.append({"professor": professor, "move_to": {"row": dst_r, "col": dst_c}})
                continue

            for men_r, men_c in _adjacent_cells(dst_r, dst_c):
                men = board[men_r][men_c]
                is_source = (men_r, men_c) == (cur_r, cur_c)
                if (men["professor"] is None or is_source) and men["level"] < 4:
                    moves.append({
                        "professor": professor,
                        "move_to": {"row": dst_r, "col": dst_c},
                        "mentor_at": {"row": men_r, "col": men_c},
                    })
    return moves


def _order_moves(board, moves, team_id, opponent_id):
    opp_at_l2 = []
    for prof in TEAM_PROFESSORS[opponent_id]:
        pos = _find_professor(board, prof)
        if pos and board[pos[0]][pos[1]]["level"] >= 2:
            opp_at_l2.append(pos)

    def priority(move):
        dst_r = move["move_to"]["row"]
        dst_c = move["move_to"]["col"]
        dst_level = board[dst_r][dst_c]["level"]

        if dst_level == 3:
            return 10_000  #vitória imediata

        score = dst_level * 20

        if "mentor_at" in move:
            men_r = move["mentor_at"]["row"]
            men_c = move["mentor_at"]["col"]
            new_level = board[men_r][men_c]["level"] + 1
            score += new_level * 5
            if new_level == 3 and dst_level >= 2:
                score += 60  #cria caminho de vitória
            if new_level == 3 and any(
                (men_r, men_c) in _adjacent_cells(r, c) for r, c in opp_at_l2
            ):
                score -= 90  #da vitória ao adversário

        score -= (abs(dst_r - 2) + abs(dst_c - 2))
        return score

    return sorted(moves, key=priority, reverse=True)



#Função de avaliação


def _evaluate(board, team_id, opponent_id):
    score = 0.0

    for prof in TEAM_PROFESSORS[team_id]:
        pos = _find_professor(board, prof)
        if pos is None:
            continue
        r, c = pos
        level = board[r][c]["level"]

        score += level * 12

        #caminhos de vitória imediata
        if level >= 2:
            for adj_r, adj_c in _adjacent_cells(r, c):
                cell = board[adj_r][adj_c]
                if cell["level"] == 3 and cell["professor"] is None:
                    score += 50

        #acesso a nível 2 (recurso para vencer)
        if level >= 1:
            for adj_r, adj_c in _adjacent_cells(r, c):
                cell = board[adj_r][adj_c]
                if cell["level"] == 2 and cell["professor"] is None:
                    score += 12

        #mobilidade própria
        mobility = sum(
            1 for adj_r, adj_c in _adjacent_cells(r, c)
            if board[adj_r][adj_c]["professor"] is None
            and board[adj_r][adj_c]["level"] < 4
            and board[adj_r][adj_c]["level"] <= level + 1
        )
        if mobility == 0:
            score -= 150
        elif mobility == 1:
            score -= 60
        elif mobility == 2:
            score -= 25
        else:
            score += mobility * 3

        score -= (abs(r - 2) + abs(c - 2)) * 0.8

    for prof in TEAM_PROFESSORS[opponent_id]:
        pos = _find_professor(board, prof)
        if pos is None:
            continue
        r, c = pos
        level = board[r][c]["level"]

        score -= level * 12

        #caminhos de vitória do adversário
        if level >= 2:
            for adj_r, adj_c in _adjacent_cells(r, c):
                cell = board[adj_r][adj_c]
                if cell["level"] == 3 and cell["professor"] is None:
                    score -= 50

        #acesso a nível 2 do adversário
        if level >= 1:
            for adj_r, adj_c in _adjacent_cells(r, c):
                cell = board[adj_r][adj_c]
                if cell["level"] == 2 and cell["professor"] is None:
                    score -= 12

        #mobilidade do adversário, queremos restringi-la
        opp_mobility = sum(
            1 for adj_r, adj_c in _adjacent_cells(r, c)
            if board[adj_r][adj_c]["professor"] is None
            and board[adj_r][adj_c]["level"] < 4
            and board[adj_r][adj_c]["level"] <= level + 1
        )
        if opp_mobility == 0:
            score += 150  #adversário preso — quase ganhamos
        elif opp_mobility == 1:
            score += 60
        elif opp_mobility == 2:
            score += 25
        else:
            score -= opp_mobility * 3

        score += (abs(r - 2) + abs(c - 2)) * 0.5

    return score



#Fallback


def _any_valid_move(board, team_id):
    for professor in TEAM_PROFESSORS[team_id]:
        pos = _find_professor(board, professor)
        if pos is None:
            continue
        cur_r, cur_c = pos
        cur_level = board[cur_r][cur_c]["level"]
        for dst_r, dst_c in _adjacent_cells(cur_r, cur_c):
            dst = board[dst_r][dst_c]
            if dst["professor"] is None and dst["level"] == 3 and cur_level >= 2:
                return {"professor": professor, "move_to": {"row": dst_r, "col": dst_c}}
        for dst_r, dst_c in _adjacent_cells(cur_r, cur_c):
            dst = board[dst_r][dst_c]
            if dst["professor"] is not None or dst["level"] == 4 or dst["level"] > cur_level + 1:
                continue
            if dst["level"] == 3:
                continue
            for men_r, men_c in _adjacent_cells(dst_r, dst_c):
                men = board[men_r][men_c]
                is_source = (men_r, men_c) == (cur_r, cur_c)
                if (men["professor"] is None or is_source) and men["level"] < 4:
                    return {
                        "professor": professor,
                        "move_to": {"row": dst_r, "col": dst_c},
                        "mentor_at": {"row": men_r, "col": men_c},
                    }
    raise RuntimeError(f"Time {team_id} sem jogada válida")



#Helpers


def _adjacent_cells(row, col):
    cells = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < 5 and 0 <= nc < 5:
                cells.append((nr, nc))
    return cells


def _find_professor(board, professor_name):
    for r in range(5):
        for c in range(5):
            if board[r][c]["professor"] == professor_name:
                return (r, c)
    return None


def _board_hash(board):
    return tuple(
        (cell["level"], cell["professor"])
        for row in board for cell in row
    )


def _elapsed():
    return time.time() - _start_time
