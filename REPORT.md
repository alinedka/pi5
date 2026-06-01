# REPORT — Backend

O backend é uma API REST em FastAPI (Python) com duas responsabilidades: expor o endpoint que o servidor do professor chama a cada turno, e executar a lógica do jogador inteligente que decide a jogada.

---

## Estrutura da Aplicação

```
backend/
├── __init__.py   #Torna o diretório um módulo Python
├── main.py       #Aplicação FastAPI: endpoints /health e /move
└── ia.py         #Toda a lógica do jogador inteligente
requirements.txt  #Dependências: fastapi, uvicorn
Procfile          #Comando de inicialização para Railway
```

### `main.py`

Toda a configuração do servidor está aqui, com dois endpoints:

- `GET /health` — retorna `{"status": "ok"}`, usado pelo Railway para saber se o container está rodando. Se não responder, ele reinicia a instância.
- `POST /move` — recebe o payload do servidor do professor com o estado atual do tabuleiro e repassa para `escolher_jogada()` em `ia.py`.


---

## Jogador Inteligente - Estratégia

### O Jogo

The Last Graduation é um jogo de tabuleiro 5×5. Dois times (Turing e Lovelace) colocam dois professores cada e se alternam em turnos. Em cada turno o jogador move um professor para uma célula adjacente e depois constrói em uma célula adjacente à nova posição, elevando-a um nível. Quem chegar com um professor no nível 3 primeiro vence. Nível 4 é cúpula — bloqueia a célula permanentemente.

### Como chegamos na estratégia atual

Começamos com uma abordagem puramente heurística: a IA olhava apenas para o estado atual do tabuleiro e escolhia a jogada com melhor pontuação imediata, sem simular respostas do adversário. Fomos ajustando os pesos e adicionando penalidades (mobilidade restrita, construção que dá vantagem ao adversário), mas chegou num ponto onde aumentar os pesos não melhorava mais — a IA simplesmente não enxergava longe o suficiente para evitar armadilhas.

O problema ficou claro quando testamos localmente: a heurística estava vencendo ~65% das partidas contra uma IA aleatória, mas perdia facilmente para qualquer adversário que pensasse 2-3 turnos à frente. Isso nos levou a implementar o Minimax.

### Algoritmo: Minimax com Alpha-Beta Pruning e Iterative Deepening

O Minimax constrói uma árvore de busca onde alternamos entre o nosso time (tentando maximizar a pontuação) e o adversário (tentando minimizá-la). Em vez de escolher a melhor jogada imediata, o algoritmo considera todas as respostas possíveis do adversário e escolhe a jogada que leva ao melhor resultado assumindo que o outro lado também joga bem.

**Alpha-Beta Pruning** é uma otimização em cima do Minimax: durante a busca, mantemos dois limites — o melhor que já garantimos para nós (alpha) e o melhor que o adversário já garantiu para ele (beta). Quando um ramo claramente não pode melhorar nenhum dos dois, ele é descartado sem explorar. Isso permite quase dobrar a profundidade alcançável no mesmo tempo.

**Iterative Deepening** surgiu de um problema prático: não sabemos quanto tempo cada nível vai demorar antes de buscar. A solução foi buscar na profundidade 2, depois 3, depois 4, parando quando o tempo se esgotar. Assim sempre temos uma jogada pronta, mesmo se o tempo acabar no meio de uma busca mais profunda.

Também investimos em ordenação de jogadas: vitórias imediatas são avaliadas primeiro, depois jogadas que criam ameaças, depois por nível do destino. Isso faz o Alpha-Beta encontrar os melhores cortes mais cedo e na prática acelera bastante a busca.

Uma decisão de implementação importante foi usar make/undo em vez de copiar o tabuleiro inteiro a cada jogada. O `copy.deepcopy` estava consumindo tempo demais; com make/undo, mutamos o tabuleiro e depois desfazemos manualmente, o que é muito mais rápido.

### Função de Avaliação

Quando a busca chega na profundidade máxima, avaliamos o tabuleiro com a função `_evaluate`:

- +100.000 / −100.000: vitória ou derrota já detectada
- Altura dos professores: nível atual × 12 (subir é fundamental)
- Caminhos de vitória: +50 por célula de nível 3 acessível a partir do nível 2
- Acesso a nível 2: +12 por célula de nível 2 adjacente alcançável
- Mobilidade própria: penalidade se restrita (−60 com 1 saída, −150 sem nenhuma)
- Mobilidade do adversário: bônus por restringir o adversário (+60 com 1 saída, +150 se preso)
- Centro: pequena preferência pelo centro do tabuleiro

Os pesos vieram de tentativa e erro nos testes locais — nenhuma fórmula exata, só ajuste até as partidas simuladas melhorarem.

### Testes e Validação

Usamos o `game_simulator.py` para simular partidas completas localmente. Testamos alternando qual time cada versão controlava (Turing/Lovelace) para não favorecer nenhum lado por acidente.

Um problema que apareceu só em produção: o Railway é significativamente mais lento que nossa máquina local. Com o limite de tempo em 8 segundos, o servidor do professor estava recebendo timeout antes da nossa resposta. Tivemos que reduzir o `TIME_LIMIT` para 3 segundos e a profundidade máxima de 6 para 4. 

Em 16 partidas simuladas localmente contra a versão heurística anterior, o Minimax venceu todas. A diferença principal não foi a função de avaliação em si — foi a profundidade. A heurística via 1-2 jogadas à frente; o Minimax vê sequências completas de 4 turnos e consegue detectar ameaças duplas que a versão anterior simplesmente ignorava.
