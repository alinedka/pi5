import json

from game_simulator import build_payload, make_board_random_levels, place_all_professors_random, validate_turn
from backend.ia import escolher_jogada


def main():
    board = make_board_random_levels()
    place_all_professors_random(board)

    payload = build_payload(
        board=board,
        team_id=1,
        turn_number=1,
        turn_phase="player_turn",
    )

    move = escolher_jogada(payload)
    error = validate_turn(payload["board"], payload["your_team"], move)

    print("=== PAYLOAD ENVIADO PARA O ALGORITMO ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    print("=== RESPOSTA DO ALGORITMO ===")
    print(json.dumps(move, indent=2, ensure_ascii=False))
    print()

    if error:
        print(f"STATUS: INVALIDO ({error})")
    else:
        print("STATUS: VALIDO")


if __name__ == "__main__":
    main()
