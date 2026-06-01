# PI5 Aux

Arquivos auxiliares para desenvolvimento local do jogador inteligente.

## 1) Onde colocar seu algoritmo

Edite `pi5-aux/ia_template.py`, funcao `escolher_jogada(payload)`.

## 2) Rodar uma jogada unica com estado aleatorio

```bash
python rodar_jogada_unica.py
```

Esse script gera um tabuleiro aleatorio, chama seu algoritmo e valida se a resposta e uma jogada valida.

## 3) Simular partida completa (DEV vs RANDOM)

```bash
python simular_partida_local.py
```

- Time 1: algoritmo do dev (`escolher_jogada`)
- Time 2: jogador aleatorio

O script executa setup + turnos ate vitoria, erro de jogada ou limite de turnos.
