# Como usar a pasta pi5-aux

Este guia explica como editar e testar seu jogador inteligente localmente, sem precisar subir API web.

## 1) Arquivos importantes

- `pi5-aux/ia_template.py`: arquivo principal para voce implementar sua IA.
- `pi5-aux/rodar_jogada_unica.py`: gera um estado aleatorio e executa 1 jogada do seu algoritmo.
- `pi5-aux/simular_partida_local.py`: simula uma partida completa (DEV vs RANDOM).
- `pi5-aux/game_simulator.py`: utilitarios e regras da simulacao local.

## 2) Onde editar seu algoritmo

Edite somente a funcao `escolher_jogada(payload)` em `pi5-aux/ia_template.py`.

Ela recebe o mesmo formato de payload usado pela API real:

```json
{
  "game_id": "uuid-ou-id-local",
  "turn_number": 7,
  "turn_phase": "player_turn",
  "your_team": 1,
  "board": [[{ "level": 0, "professor": null }]],
  "professor_to_place": null
}
```

Retorno esperado:

- `setup_placement`: `{ "row": int, "col": int }`
- `player_turn`:

```json
{
  "professor": "CLARO",
  "move_to": { "row": 1, "col": 2 },
  "mentor_at": { "row": 0, "col": 2 }
}
```

Observacao: ao mover para nivel 3 (vitoria), `mentor_at` pode ser omitido.

## 3) Teste rapido: jogada unica

Comando:

```bash
python pi5-aux/rodar_jogada_unica.py
```

Esse script:

1. Cria tabuleiro aleatorio com professores posicionados.
2. Monta o payload.
3. Chama `escolher_jogada(payload)`.
4. Valida se a resposta e uma jogada valida.

Exemplo de saida:

```text
=== PAYLOAD ENVIADO PARA O ALGORITMO ===
{ ... }

=== RESPOSTA DO ALGORITMO ===
{ ... }

STATUS: VALIDO
```

## 4) Teste completo: simulacao de partida

Comando:

```bash
python pi5-aux/simular_partida_local.py
```

Regras da simulacao:

- Time 1: seu algoritmo (`escolher_jogada`).
- Time 2: bot aleatorio.
- Executa setup (`setup_placement`) e depois turnos (`player_turn`).
- Encerra por vitoria, jogada invalida ou limite de turnos.

Exemplo de saida:

```text
setup#1 team=1 source=DEV professor=CLARO move={'row': 2, 'col': 2}
...
turn=035 team=1 source=DEV move={"professor": "CLARO", "move_to": {"row": 0, "col": 2}}

=== RESULTADO FINAL ===
winner_team: 1
loser_team: 2
turn_number: 35
reason: Vitoria por chegar ao nivel 3
```

## 5) Fluxo recomendado para dev

1. Implemente uma versao simples em `escolher_jogada(payload)`.
2. Rode `rodar_jogada_unica.py` até ter resposta sempre válida.
3. Rode `simular_partida_local.py` várias vezes para medir consistência.
4. Melhore heurísticas (vitória imediata, bloqueio, posicionamento).
5. Reaproveite a mesma função no endpoint `POST /move` da sua IA real.

## 6) Dicas de depuração

- Se aparecer `STATUS: INVALIDO`, confira campos `professor`, `move_to` e `mentor_at`.
- Garanta que `row` e `col` são inteiros entre `0` e `4`.
- Não mova para célula ocupada, nível 4, ou nível acima de `nivel_atual + 1`.
- Se não for jogada vencedora, sempre informe `mentor_at` válido.
