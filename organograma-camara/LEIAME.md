# Organograma institucional

HTML + CSS + JavaScript + D3.js (v7.9.0, licença ISC, incluído em `js/vendor/`). Sem build, sem npm, sem CDN: basta publicar a pasta ou abrir o `index.html` no navegador (funciona offline).

Uma **única página responsiva** (`index.html`) serve de página própria **ou** de conteúdo de um `<iframe>` no site da Câmara, sem abrir nova aba. Como incorporar: [`INCORPORACAO.md`](INCORPORACAO.md); simulação: `exemplo-no-site.html`.

## Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `index.html` | A página: cabeçalho de identificação, barra de ações e link do PDF do organograma. |
| `exemplo-no-site.html` | Simulação do organograma dentro de uma página do site (iframe + ajuste de altura). |
| `js/dados-organograma.js` | **Única fonte de dados.** É o único arquivo a editar para mudar a estrutura. |
| `js/organograma-layout.js` | Algoritmo de posicionamento puro (sem DOM): larguras, quebra em linhas, alturas, conectores. |
| `js/organograma-core.js` | Validação dos dados, `d3.hierarchy`, cards, SVG, animação, teclado/ARIA, botões. |
| `js/organograma-busca.js` | Módulo de busca preservado, mas não carregado pela página atual. |
| `js/organograma-perfil.js` | Números do layout para celular e desktop; escolhe o perfil pela largura (até 640 px = celular). |
| `js/organograma-incorporado.js` | Modo incorporado (dentro de `<iframe>`): esconde o topo e avisa a altura à página-mãe. |
| `css/organograma.css` | Todos os estilos: tema da CMG, cabeçalho, cards, conectores e ajustes por largura. |
| `tests/` | `layout.test.js` (algoritmo), `browser_test.py` (navegador) e `cores_test.py` (acessibilidade das cores). |

### Como percorrer o código

1. Abra `index.html`: ele define a interface e carrega os scripts na ordem necessária.
2. Para entender os setores e suas relações, leia `js/dados-organograma.js`. Cada chamada `node(...)` cria um card; a lista `filhos` define as ligações.
3. Para entender o posicionamento, leia `js/organograma-layout.js` e depois `js/organograma-core.js`: o primeiro calcula coordenadas sem DOM; o segundo mede e desenha os cards, anima conectores e trata interações.
4. Para mudar a aparência, veja `css/organograma.css` (seção 7 = cores e apresentação dos cards).

`js/vendor/d3.min.js` é uma dependência de terceiros minificada; normalmente não deve ser editada.

## O que cada card mostra

Cada card mostra **sigla** (quando existe), **nome** e uma **seta** que indica se abre ou fecha as unidades subordinadas. O **tipo** da unidade (instituição, órgão etc.) e a **quantidade** de subunidades não aparecem nem nos cartões nem nos seus rótulos acessíveis.

A cor e a apresentação vêm de dois campos dos dados:

| Campo | Valores | Efeito |
|---|---|---|
| `dimensao` | `'legislativa'` ou `'administrativa'` (padrão) | Azul (legislativa) ou verde (administrativa). |
| `macro` | `true` ou `false` (padrão) | Macrounidade: tom escuro, texto maior e faixa amarela no topo. |

- **Estrutura oficial:** Plenário → Comissões Legislativas, Gabinetes Parlamentares e Mesa Diretora. A Mesa tem cinco ramos: DFIN, DGER, DLEG, PRES e Vice-presidências e secretarias (VPCS). A árvore e as siglas foram conferidas com a [página oficial do organograma interativo](https://www.goiania.go.leg.br/institucional/organograma/organograma-interativo) e a [Lei Municipal nº 11.351/2025](https://www.goiania.go.gov.br/html/gabinete_civil/sileg/dados/legis/2025/lo_20250320_000011351.html).
- **Legislativas:** Plenário, Mesa Diretora, comissões legislativas (incluindo o Conselho de Ética e Decoro Parlamentar), vice-presidências e secretarias e ouvidorias especiais.
- **Macrounidades:** Gabinete da Presidência, todas as diretorias, Procuradoria Geral e Controladoria Geral.
- `Gabinetes Parlamentares` é um ramo próprio do Plenário, sem descendentes na árvore publicada. Vice-presidências e secretarias são filhas de VPCS, diretamente sob a Mesa.

## Como o layout funciona

1. Cada card visível é medido no DOM (tamanho real, com o texto quebrado).
2. Os filhos de um nó ficam lado a lado enquanto couberem na largura disponível; se não couberem, quebram em linhas **balanceadas**, de acordo com o espaço disponível. Cards da mesma linha ficam com a mesma altura.
3. O pai é centralizado sobre a primeira linha de filhos. Linhas seguintes se ligam por um "tronco" no corredor esquerdo, por onde nenhum card passa.
4. Celular e desktop usam o mesmo algoritmo; muda só o orçamento de largura (`js/organograma-perfil.js`). Por isso o desktop cresce para os lados e o celular para baixo, sem `scale()` nem `overflow-x`.
5. Expandir/recolher recalcula tudo; cards e conectores são interpolados juntos a cada quadro, e o card clicado fica parado na tela.

## Navegação

### Cabeçalho e links
- **Identificação no topo:** faixa azul com "Câmara Municipal de Goiânia" e o título.
- **Voltar ao site:** link para `https://www.goiania.go.leg.br/` (`target="_top"`, sai do quadro quando incorporado).
- **Documento:** link visível para o [Organograma em PDF](https://www.goiania.go.leg.br/institucional/organograma/organograma/CMG_organograma.pdf).
- No modo incorporado o cabeçalho some da vista (o site já tem o seu), mas os botões de ações e documentos permanecem.

### Botões da barra
- **Expandir próximo nível:** abre um nível por clique. Quando não há mais o que abrir, avisa "Todos os níveis já estão expandidos".
- **Expandir tudo / Recolher tudo.**

### Acordeão (só celular)
No celular (até 640 px), abrir um dos filhos diretos da raiz fecha os outros, para a página não ficar gigante. Atalhos, "Expandir tudo" e "Expandir próximo nível" ignoram essa regra. No desktop não existe.

## Validação dos dados
Antes de desenhar, o núcleo confere os dados: `id` único e não vazio, `nome` presente, `tipo` (se informado) cadastrado em `ROTULOS_TIPO`, `dimensao` (se informada) igual a `legislativa` ou `administrativa`, e `targetId` apontando para um id existente. Se algo estiver errado, a página mostra um aviso (`role="alert"`) com a causa e o `console.error` registra o mesmo; nada é desenhado.

## Manutenção

- **Novo setor/comissão/funcionário:** adicione `node(...)` (ou os atalhos `diretoria(...)`, `gerencia(...)` etc.) no array `filhos` do pai, em `dados-organograma.js`. Nada no algoritmo muda.
- **Entidade legislativa:** passe `{ dimensao: 'legislativa' }` (no arquivo, `...LEG`) nos metadados. As comissões já são legislativas por padrão (`commission(...)`).
- **Macrounidade:** `diretoria(...)` já marca `macro: true`; para outros, use `{ macro: true }`. Para uma exceção a uma diretoria, `{ macro: false }`.
- **Sigla:** `{ sigla: 'XXX' }` nos metadados; aparece no card.
- **Espaçamento/tamanho:** `organograma-perfil.js` (só números).
- **Atalho entre cards:** `targetId` em um card faz o clique levar ao card alvo.
- **Padrão dos comentários:** cada função explica *o que faz* e *por que existe*; as constantes explicam de onde vem o valor. Mantenha isso ao alterar o código.

## Acessibilidade
Padrão ARIA *tree*: `↑`/`↓` percorrem os cards, `→` expande (ou entra no primeiro filho), `←` recolhe (ou sobe ao pai), `Enter`/`Espaço` alternam, `Home`/`End` vão ao primeiro/último. Cada card expõe `aria-expanded`, `aria-level` e um rótulo com nome, sigla, **dimensão** ("unidade legislativa" ou "unidade administrativa") e "macrounidade" quando aplicável. Assim a cor não é a única pista (WCAG 1.4.1), sem anunciar quantidades de subordinadas. Há foco visível em todos os controles e as animações respeitam `prefers-reduced-motion`.

## Tema: paleta CMG

As cores seguem a paleta informada para o projeto. Azul e verde distinguem as dimensões; os tons escuros destacam macrounidades; amarelos são usados em detalhes.

| Uso | Cor | Valor |
|---|---|---|
| Macrounidade legislativa / identidade da interface | Azul escuro | `#242F62` |
| Unidade legislativa | Azul | `#4C61BD` |
| Macrounidade administrativa | Verde escuro | `#1A5529` |
| Unidade administrativa | Verde | `#2F9D4C` |
| Conectores | Amarelo escuro | `#BA8727` |
| Faixa de macrounidade e filete do topo | Amarelo claro | `#DBAD57` |

Apresentação dos cards:

| Card | Fundo | Contorno | Texto |
|---|---|---|---|
| Legislativo comum | azul `#4C61BD` | azul escuro | branco |
| Administrativo comum | verde `#2F9D4C` | verde escuro | escuro |
| Macrounidade | azul `#242F62` ou verde `#1A5529` | mesma cor do fundo | branco, maior, com faixa `#DBAD57` de 6 px no topo |

O foco usa o azul escuro da paleta; o realce de hierarquia usa o azul `#4C61BD`, distinguindo-o dos conectores amarelos. Os cartões não usam amarelo como cor de dimensão.

**Tipografia:** o manual define **Calibri** para materiais institucionais. A pilha é `Calibri, Carlito, "Segoe UI", system-ui, ...` (`--fonte-texto`). Calibri não vem no projeto (licença da Microsoft) e costuma faltar em Linux e celulares, onde entra Carlito (mesmas métricas) ou a fonte do sistema. Os cards são medidos no DOM, então o layout não quebra com a troca. Para garantir a mesma fonte em todo aparelho, hospede o Carlito (licença livre) e declare-o com `@font-face`.

**Trocar uma cor:** edite o valor em `css/organograma.css` (tokens `--cmg-*` e seção 7) e rode `python3 tests/cores_test.py`; ele confere contraste WCAG, os seis valores da paleta e a distinção entre dimensões sob daltonismo. `--tabela` lista as distâncias.

O CSS também trata `forced-colors` (alto contraste do Windows): contornos e conectores continuam visíveis, e a macrounidade segue distinguível pela faixa grossa no topo.

## Nitidez
Em repouso, cada card é posicionado na grade de pixels físicos da tela (`alinhar` em `desenhar`), tem largura e altura inteiras e só ganha camada de GPU (`will-change`) enquanto anima. Isso evita o texto "embaçado", principalmente em telas com escala 125%/150%.

## Testes
- `node tests/layout.test.js`: 478 cenários do algoritmo, sem navegador (sobreposição, conectores atravessando cards, largura).
- `python3 tests/browser_test.py`: Chromium headless (precisa de `pip install playwright`); mede o DOM real em várias larguras e exercita próximo nível, acordeão, validação, teclado, movimento reduzido, ausência da busca e da legenda, cores renderizadas por dimensão e macrounidade, cabeçalho e link do PDF, limite de 640 px e incorporação em `<iframe>` (a altura do quadro acompanha o conteúdo). Exige zero `console.error`.
- `python3 tests/cores_test.py`: contraste WCAG, paleta CMG e distinção entre dimensões sob daltonismo, lendo as cores direto do CSS. Precisa de `pip install numpy scikit-image` (só para testes).

Os testes têm focos diferentes: `layout.test.js` valida a matemática isoladamente; `browser_test.py` verifica o resultado no navegador e o comportamento interativo; `cores_test.py` checa os tokens definidos no CSS. Ao explicar uma mudança, indique qual desses níveis cobre o comportamento alterado.
