## Páginas HTML

- `index.html` — a página do organograma, única e responsiva (celular e desktop). Define a interface: cabeçalho de identificação com retorno ao site, barra de ações, link do PDF, área do diagrama e região de avisos para leitores de tela. Carrega os scripts na ordem necessária.
- `exemplo-no-site.html` — simulação do organograma dentro de uma página do site, por meio de um `<iframe>` que ajusta a própria altura. Serve de modelo do trecho a colar no portal (ver `INCORPORACAO.md`).

## Estilos CSS

- `organograma.css` — todos os estilos: paleta CMG informada (azuis, verdes e amarelos; fonte Calibri), cabeçalho, cards (cor por dimensão legislativa/administrativa e apresentação própria das macrounidades), conectores, estados de foco e animação, e os ajustes por largura (celular até 640 px) e para o modo incorporado.

## JavaScript

- `dados-organograma.js` — contém a árvore de unidades. Cada nó representa um card, e a lista `filhos` determina a subordinação. Os campos `dimensao` e `macro` definem a cor e a apresentação. É o principal arquivo para alterar os dados do organograma.
- `organograma-layout.js` — calcula as posições e dimensões dos cards e o percurso dos conectores. É um algoritmo independente do navegador e do DOM, o que permite testá-lo separadamente.
- `organograma-core.js` — coordena a aplicação: valida os dados, cria e posiciona os cards, desenha os conectores, anima as mudanças e implementa as interações, como teclado, expansão e acessibilidade.
- `organograma-busca.js` — módulo de busca preservado no projeto, mas não carregado pela página atual.
- `organograma-perfil.js` — define as medidas de layout do celular e do desktop, escolhe o perfil pela largura da janela (ou do quadro, quando incorporado) e ativa o acordeão nas unidades subordinadas à raiz no celular.
- `organograma-incorporado.js` — liga o modo incorporado quando a página está dentro de um `<iframe>` e avisa a altura do conteúdo à página-mãe.
- `d3.min.js` — biblioteca D3 usada pelo projeto para trabalhar com a hierarquia e desenhar elementos. É um arquivo de terceiros minificado, então normalmente não deve ser editado.

## Testes

- `layout.test.js` — testa a geometria do algoritmo sem abrir o navegador. Usa os dados do projeto, perfis de celular e desktop e cenários sintéticos; verifica se todos os cards foram posicionados, se não há sobreposição ou estouro de largura e se os conectores não atravessam cards. A aleatoriedade usa uma semente fixa para que os cenários sejam reproduzíveis.
- `browser_test.py` — testa a aplicação num navegador real. Confere layout e interações, como teclado, expansão, acordeão, ausência da busca e da legenda, cores por dimensão, cabeçalho e link do PDF, limite de 640 px, incorporação em `<iframe>` e movimento reduzido.
- `cores_test.py` — verifica as cores definidas no CSS, incluindo contraste, uso da paleta CMG informada e distinção entre as dimensões sob simulações de daltonismo.

## Documentação

- `LEIAME.md` — guia principal: apresenta a estrutura, a navegação, o tema, como o layout funciona, como manter o projeto e como executar os testes.
- `INCORPORACAO.md` — avalia e explica como disponibilizar o organograma dentro do site, sem abrir nova aba, e a navegação oferecida.
- `INTEGRACAO.md` — registro histórico dos recursos integrados na primeira fase e das decisões tomadas.

## Como as partes se conectam

O fluxo principal é:

**`index.html` → dados → layout → núcleo → perfil**

A página carrega os dados e os módulos. O núcleo valida os dados, mede os cards, solicita as posições ao algoritmo de layout e desenha o resultado. Os controles da interface acionam funções do núcleo; o CSS define a aparência. Os testes verificam partes diferentes desse fluxo: o algoritmo isolado, o comportamento no navegador e a acessibilidade das cores.
