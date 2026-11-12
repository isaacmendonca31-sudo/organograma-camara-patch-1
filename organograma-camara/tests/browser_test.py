"""Testes de navegador (Chromium headless).

Uso:  python3 tests/browser_test.py [--shots]

Mede no DOM REAL (e não em simulação): sobreposição de cards, conectores que
atravessam cards, rolagem horizontal, cards fora do palco e texto cortado, em
várias larguras e estados. Também exercita os recursos de interação:
"Expandir próximo nível", acordeão (celular), validação dos dados, teclado,
movimento reduzido, interface simplificada (sem tipos ou contagem nos cartões e sem
busca ou legenda), tema por dimensão e macrounidade, cabeçalho/link do PDF e
incorporação em <iframe>.

Há UMA página (index.html) responsiva: os argumentos "desktop"/"mobile" dos
cenários só escolhem o aparelho simulado (largura, toque); o perfil de layout
é escolhido pela própria página (celular até 640px).

Regra transversal: nenhum cenário pode emitir `console.error` (exceto os de
validação, que PROVOCAM o erro de propósito e conferem que ele aparece).
"""
import os
import shutil
import sys
import tempfile

from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINA = 'file://' + os.path.join(RAIZ, 'index.html')
EXEMPLO = 'file://' + os.path.join(RAIZ, 'exemplo-no-site.html')
URL = {'desktop': PAGINA, 'mobile': PAGINA, 'index': PAGINA}
SHOTS = '--shots' in sys.argv
PASTA_SHOTS = os.path.join(RAIZ, 'tests', 'screens')
if SHOTS:
    os.makedirs(PASTA_SHOTS, exist_ok=True)

# Script executado DENTRO da página: coleta as métricas de layout de uma vez
# (uma única ida ao navegador por verificação, bem mais rápido que várias).
CHECAR = """() => {
  const palco = document.getElementById('organograma');
  const pr = palco.getBoundingClientRect();
  const cards = [...palco.querySelectorAll('.card:not(.saindo)')];
  const R = cards.map(c => { const r = c.getBoundingClientRect(); return {id: c.dataset.id, x: r.left, y: r.top, w: r.width, h: r.height}; });
  const out = {cards: R.length, sobrepostos: [], foraDoPalco: [], cortados: [], conectores: [], rolagemH: false, linhasNivel: {}};
  // Dois cards se sobrepõem se seus retângulos (com folga de 4px) se cruzam.
  for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) {
    const a = R[i], b = R[j];
    if (a.x < b.x + b.w + 4 && b.x < a.x + a.w + 4 && a.y < b.y + b.h + 4 && b.y < a.y + a.h + 4) out.sobrepostos.push([a.id, b.id]);
  }
  R.forEach(r => { if (r.x < pr.left - 0.5 || r.x + r.w > pr.right + 0.5) out.foraDoPalco.push(r.id); });
  // Texto cortado: o conteúdo é maior que a caixa do card.
  cards.forEach(c => { if (c.scrollHeight > c.clientHeight + 1) out.cortados.push(c.dataset.id); });
  const doc = document.documentElement;
  out.rolagemH = doc.scrollWidth > doc.clientWidth + 0.5;
  // Percorre cada conector ponto a ponto (de 3 em 3px) e verifica se entra num card.
  document.querySelectorAll('#organograma path.aresta').forEach(p => {
    const len = p.getTotalLength();
    for (let s = 0; s <= len; s += 3) {
      const pt = p.getPointAtLength(s);
      const x = pt.x + pr.left, y = pt.y + pr.top;
      const hit = R.find(r => x > r.x + 1 && x < r.x + r.w - 1 && y > r.y + 1 && y < r.y + r.h - 1);
      if (hit) { out.conectores.push(hit.id); break; }
    }
  });
  const ys = new Set(R.map(r => Math.round(r.y)));
  out.linhasDistintas = ys.size;
  out.largura = Math.round(pr.width);
  out.altura = Math.round(pr.height);
  return out;
}"""

falhas = []
total = 0


def registrar(nome, ok, detalhe=''):
    """Conta uma verificação e imprime o resultado."""
    global total
    total += 1
    if ok:
        print(f'  ok    {nome}')
    else:
        falhas.append((nome, detalhe))
        print(f'  FALHA {nome} {detalhe}')


def verificar(nome, resultado, esperado_cards=None):
    """Confere as métricas de layout de CHECAR (e, opcionalmente, a quantidade de cards)."""
    global total
    total += 1
    problemas = []
    if resultado['sobrepostos']:
        problemas.append(f"sobreposição {resultado['sobrepostos'][:3]}")
    if resultado['conectores']:
        problemas.append(f"conector atravessa card {sorted(set(resultado['conectores']))[:3]}")
    if resultado['rolagemH']:
        problemas.append('rolagem horizontal')
    if resultado['foraDoPalco']:
        problemas.append(f"card fora do palco {resultado['foraDoPalco'][:3]}")
    if resultado['cortados']:
        problemas.append(f"texto cortado {resultado['cortados'][:3]}")
    if esperado_cards is not None and resultado['cards'] != esperado_cards:
        problemas.append(f"esperava {esperado_cards} cards, há {resultado['cards']}")
    if problemas:
        falhas.append((nome, problemas))
        print('  FALHA', nome, problemas)
    else:
        print(f"  ok    {nome} ({resultado['cards']} cards, {resultado['largura']}x{resultado['altura']}px)")


def card(page, nome):
    """Localiza o card visível cujo nome contém `nome`."""
    return page.locator('#organograma .card:not(.saindo)', has=page.locator('.card-nome', has_text=nome)).first


def clicar(page, nome):
    """Clica no card e espera a animação (380ms) terminar."""
    c = card(page, nome)
    c.scroll_into_view_if_needed()
    c.click()
    page.wait_for_timeout(650)


def shot(page, nome, completo=False):
    """Salva uma captura de tela somente quando o script recebe `--shots`."""
    if SHOTS:
        page.screenshot(path=os.path.join(PASTA_SHOTS, nome + '.png'), full_page=completo)


def nova_pagina(browser, modo, largura, altura, url=None, **opcoes_contexto):
    """Abre um contexto NOVO (sessionStorage vazio) e devolve (contexto, página, erros_de_console).

    Cada cenário usa um contexto próprio para que o estado salvo (cards abertos)
    de um não vaze para o seguinte."""
    ctx = browser.new_context(viewport={'width': largura, 'height': altura}, device_scale_factor=1,
                              has_touch=(modo == 'mobile'), is_mobile=(modo == 'mobile'), **opcoes_contexto)
    page = ctx.new_page()
    erros = []
    page.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: erros.append(str(e)))
    page.goto(url or URL[modo])
    return ctx, page, erros


def sem_erros(nome, erros):
    """Transforma erros JavaScript do navegador em uma verificação visível no relatório."""
    registrar(f'{nome}: zero console.error', not erros, erros[:3])


def aguardar_organograma(page):
    """Espera a primeira renderização e a curta estabilização inicial do layout."""
    page.wait_for_selector('#organograma .card')
    page.wait_for_timeout(300)


# ---------------------------------------------------------------------------
# Cenário geral: layout, expandir/recolher, atalho, teclado, redimensionamento
# ---------------------------------------------------------------------------

def cenario(browser, modo, largura, altura, redimensionar_para=None):
    print(f"\n[{modo} {largura}x{altura}]")
    ctx, page, erros = nova_pagina(browser, modo, largura, altura)
    page.wait_for_selector('#organograma .card')
    page.wait_for_timeout(300)
    tag = f'{modo}{largura}'

    # Raiz com 3 filhos diretos
    verificar(f'{tag} inicial', page.evaluate(CHECAR), 4)
    shot(page, f'{tag}-1-inicial')

    # Comissões (23 comissões + 2 ouvidorias especiais)
    clicar(page, 'Comissões Legislativas')
    r = page.evaluate(CHECAR)
    verificar(f'{tag} comissões expandidas (25 filhos)', r, 4 + 25)
    print(f"        linhas verticais distintas: {r['linhasDistintas']}")
    shot(page, f'{tag}-2-comissoes')
    shot(page, f'{tag}-2-comissoes-pagina', True)

    # Recolhimento
    clicar(page, 'Comissões Legislativas')
    verificar(f'{tag} comissões recolhidas', page.evaluate(CHECAR), 4)

    # Poucos filhos e vários níveis
    clicar(page, 'Mesa Diretora')
    verificar(f'{tag} mesa diretora (5 filhos)', page.evaluate(CHECAR), 4 + 5)
    clicar(page, 'Diretoria Financeira')
    verificar(f'{tag} diretoria financeira (2 filhos)', page.evaluate(CHECAR), 4 + 5 + 2)
    clicar(page, 'Coordenadoria de Gestão Financeira')
    verificar(f'{tag} 4 níveis abaixo da Mesa', page.evaluate(CHECAR), 4 + 5 + 2 + 3)
    clicar(page, 'Diretoria Geral')
    verificar(f'{tag} diretoria geral (17 filhos)', page.evaluate(CHECAR), 4 + 5 + 2 + 3 + 17)
    shot(page, f'{tag}-3-niveis')
    shot(page, f'{tag}-3-niveis-pagina', True)

    # No ramo da Mesa, Vice-presidências e secretarias expande seus próprios cargos.
    clicar(page, 'Vice-presidências e secretarias')
    verificar(f'{tag} vice-presidências e secretarias (11 filhos)',
              page.evaluate(CHECAR), 4 + 5 + 2 + 3 + 17 + 11)
    vpcs = card(page, 'Vice-presidências e secretarias')
    vpcs.focus()
    page.keyboard.press('ArrowLeft')
    recolhido = vpcs.get_attribute('aria-expanded')
    page.keyboard.press('ArrowRight')
    expandido = vpcs.get_attribute('aria-expanded')
    registrar(f'{tag} teclado: setas expandem/recolhem e atualizam aria-expanded',
              (recolhido, expandido) == ('false', 'true'), f'{recolhido}/{expandido}')

    # Expandir tudo (195 cards)
    page.click('[data-acao="expandir-tudo"]')
    page.wait_for_timeout(900)
    verificar(f'{tag} expandir tudo', page.evaluate(CHECAR), 195)
    shot(page, f'{tag}-4-tudo-pagina', True)

    # Redimensionamento com tudo aberto
    if redimensionar_para:
        w2, h2 = redimensionar_para
        page.set_viewport_size({'width': w2, 'height': h2})
        page.wait_for_timeout(700)
        verificar(f'{tag} redimensionado para {w2}', page.evaluate(CHECAR), 195)
        page.click('[data-acao="recolher-tudo"]')
        page.wait_for_timeout(700)
        verificar(f'{tag} recolher tudo após redimensionar', page.evaluate(CHECAR), 4)
        clicar(page, 'Comissões Legislativas')
        verificar(f'{tag} comissões em {w2}px', page.evaluate(CHECAR), 4 + 25)
        shot(page, f'{tag}-5-redimensionado')
    else:
        page.click('[data-acao="recolher-tudo"]')
        page.wait_for_timeout(700)
        verificar(f'{tag} recolher tudo', page.evaluate(CHECAR), 4)

    sem_erros(tag, erros)
    ctx.close()


def navegacao_e_documentos(browser):
    """Cabeçalho de identificação, retorno ao site e links de documentos."""
    print('\n[navegação e documentos]')
    for modo, larg, alt in (('desktop', 1280, 800), ('mobile', 390, 844)):
        tag = f'nav-{modo}{larg}'
        ctx, page, erros = nova_pagina(browser, modo, larg, alt)
        aguardar_organograma(page)
        registrar(f'{tag} identificação no topo (Câmara + título)',
                  'Câmara Municipal de Goiânia' in page.text_content('.topo-orgao')
                  and page.text_content('.topo h1') == 'Organograma interativo')
        voltar = page.locator('a.topo-voltar')
        registrar(f'{tag} "Voltar ao site" aponta para o site e sai de quadros (_top)',
                  voltar.get_attribute('href') == 'https://www.goiania.go.leg.br/' and voltar.get_attribute('target') == '_top',
                  (voltar.get_attribute('href'), voltar.get_attribute('target')))
        pdf = page.locator('nav.barra-links a', has_text='Organograma em PDF')
        registrar(f'{tag} link do PDF', pdf.count() == 1 and pdf.get_attribute('href').endswith('CMG_organograma.pdf'))
        registrar(f'{tag} sem link da lei, campo de busca ou legenda',
                  page.locator('#link-lei, #busca-campo, #busca-lista, .chave').count() == 0)
        registrar(f'{tag} sem botão de trocar de versão e sem iframe',
                  page.locator('text=Ver versão').count() == 0 and page.locator('iframe').count() == 0)
        registrar(f'{tag} topo visível e identificação acima da barra',
                  page.evaluate("document.querySelector('.topo').getBoundingClientRect().bottom <= document.querySelector('.barra').getBoundingClientRect().top + 1"))
        sem_erros(tag, erros)
        ctx.close()


def proximo_nivel(browser, modo, largura, altura):
    print(f'\n[expandir próximo nível {modo} {largura}x{altura}]')
    tag = f'nivel-{modo}{largura}'
    ctx, page, erros = nova_pagina(browser, modo, largura, altura)
    aguardar_organograma(page)

    # Primeiro clique pelo TECLADO (Enter no botão) - critério de acessibilidade
    page.focus('[data-acao="expandir-nivel"]')
    page.keyboard.press('Enter')
    page.wait_for_timeout(700)
    r = page.evaluate(CHECAR)
    # raiz(1) + 3 filhos diretos(3) abertos: 25 comissões/ouvidorias + 5 ramos da Mesa
    verificar(f'{tag} 1º clique (teclado) abre o nível 1', r, 4 + 25 + 5)
    anuncio = page.text_content('#anuncio')
    registrar(f'{tag} anuncia quantos cards novos', '30 novos cards' in anuncio, anuncio)

    anteriores = [r['cards']]
    mensagem = ''
    for _ in range(12):
        page.click('[data-acao="expandir-nivel"]')
        page.wait_for_timeout(650)
        mensagem = page.text_content('#anuncio')
        if 'já estão expandidos' in mensagem:
            break
        anteriores.append(page.evaluate(CHECAR)['cards'])
    crescente = all(b > a for a, b in zip(anteriores, anteriores[1:]))
    registrar(f'{tag} cada clique aumenta a contagem de cards', crescente, anteriores)
    verificar(f'{tag} ao final todos os 195 cards', page.evaluate(CHECAR), 195)
    registrar(f'{tag} avisa quando não há mais níveis', 'Todos os níveis já estão expandidos' in mensagem, mensagem)
    sem_erros(tag, erros)
    ctx.close()


def simplificacao(browser, modo, largura, altura):
    """Interface limpa: sem tipo, busca, legenda ou contagem nos cartões."""
    print(f'\n[interface simplificada {modo} {largura}x{altura}]')
    tag = f'simples-{modo}{largura}'
    ctx, page, erros = nova_pagina(browser, modo, largura, altura)
    aguardar_organograma(page)
    page.click('[data-acao="expandir-tudo"]')
    page.wait_for_timeout(900)
    r = page.evaluate("""() => {
      const cards = [...document.querySelectorAll('#organograma .card')];
      const tipos = ['Instituição', 'Órgão', 'Gabinete', 'Diretoria', 'Coordenadoria', 'Gerência', 'Chefia', 'Assessoria', 'Unidade', 'Cargo', 'Comissão', 'Ouvidoria'];
      return {
        cards: cards.length,
        comTipo: document.querySelectorAll('.card-tipo').length,
        // o card só pode ter nome e sigla de texto; nenhum span extra com o tipo escrito
        extras: cards.filter(c => [...c.querySelectorAll('span')].some(s => !s.classList.contains('card-nome') && !s.classList.contains('card-sigla') && !s.classList.contains('card-acao') && !s.classList.contains('seta'))).length,
        acoesComTexto: cards.filter(c => { const a = c.querySelector('.card-acao:not(.card-atalho)'); return a && a.textContent.trim() !== ''; }).length,
        busca: document.querySelectorAll('#busca-campo, #busca-lista, .busca-rotulo').length,
        legenda: document.querySelectorAll('.chave').length,
        tiposEmCartaoSemNome: cards.filter(c => { const resto = [...c.children].filter(x => !x.classList.contains('card-nome') && !x.classList.contains('card-atalho')).map(x => x.textContent).join(' '); return tipos.some(x => resto.includes(x)); }).length
      };
    }""")
    registrar(f'{tag} nenhum cartão exibe o tipo da unidade', r['comTipo'] == 0 and r['tiposEmCartaoSemNome'] == 0, r)
    registrar(f'{tag} cartão só tem nome, sigla e seta', r['extras'] == 0, r['extras'])
    registrar(f'{tag} nenhum número de subunidades nos cartões', r['acoesComTexto'] == 0, r['acoesComTexto'])
    registrar(f'{tag} sem busca ou legenda', r['busca'] == 0 and r['legenda'] == 0, r)
    # rótulo acessível: dimensão dita por texto (a cor não é a única pista) e sem contagem visual
    rotulo = card(page, 'Comissão de Cultura').get_attribute('aria-label')
    registrar(f'{tag} aria-label diz a dimensão legislativa', 'unidade legislativa' in rotulo, rotulo)
    rotulo = card(page, 'Diretoria Financeira').get_attribute('aria-label')
    registrar(f'{tag} aria-label diz dimensão administrativa e macrounidade',
              'unidade administrativa' in rotulo and 'macrounidade' in rotulo, rotulo)
    aria_com_contagem = page.evaluate("() => [...document.querySelectorAll('#organograma .card')].some(c => /subunidades?/i.test(c.getAttribute('aria-label') || ''))")
    registrar(f'{tag} rótulos acessíveis não informam quantidade de subordinadas', not aria_com_contagem)
    sem_erros(tag, erros)
    ctx.close()


def acordeao(browser, modo, largura, altura):
    print(f'\n[acordeão nas raízes {modo} {largura}x{altura}]')
    tag = f'acordeao-{modo}{largura}'
    ctx, page, erros = nova_pagina(browser, modo, largura, altura)
    aguardar_organograma(page)
    clicar(page, 'Comissões Legislativas')
    clicar(page, 'Mesa Diretora')
    if modo == 'mobile':
        # Abrir Mesa fecha Comissões (acordeão ativo)
        verificar(f'{tag} abrir Mesa fecha Comissões', page.evaluate(CHECAR), 4 + 5)
        registrar(f'{tag} Comissões ficou recolhida',
                  card(page, 'Comissões Legislativas').get_attribute('aria-expanded') == 'false')
    else:
        # No desktop os dois permanecem abertos
        verificar(f'{tag} desktop mantém vários ramos abertos', page.evaluate(CHECAR), 4 + 25 + 5)
    sem_erros(tag, erros)
    ctx.close()


def teclado_novos_elementos(browser, modo, largura, altura):
    print(f'\n[ordem de Tab {modo} {largura}x{altura}]')
    tag = f'tab-{modo}{largura}'
    ctx, page, erros = nova_pagina(browser, modo, largura, altura)
    aguardar_organograma(page)
    ordem = []
    page.evaluate('document.body.focus()')
    for _ in range(5):
        page.keyboard.press('Tab')
        ordem.append(page.evaluate(
            "document.activeElement.dataset.acao || document.activeElement.id || document.activeElement.className"))
    esperado = ['topo-voltar', 'expandir-nivel', 'expandir-tudo', 'recolher-tudo', 'botao']
    registrar(f'{tag} Tab percorre retorno ao site, ações e PDF', ordem == esperado, ordem)
    page.keyboard.press('Tab')
    registrar(f'{tag} próximo Tab chega ao primeiro card',
              page.locator('#organograma .card:focus').count() == 1)
    foco_visivel = page.evaluate("getComputedStyle(document.activeElement).outlineStyle !== 'none'")
    registrar(f'{tag} foco visível no primeiro card', foco_visivel)
    sem_erros(tag, erros)
    ctx.close()


def movimento_reduzido(browser):
    print('\n[prefers-reduced-motion]')
    for reduzido, rotulo in ((True, 'reduce'), (False, 'no-preference')):
        ctx, page, erros = nova_pagina(browser, 'desktop', 1280, 800, reduced_motion=('reduce' if reduzido else 'no-preference'))
        aguardar_organograma(page)
        card(page, 'Comissões Legislativas').click()
        page.wait_for_timeout(60)
        animando = page.locator('#organograma').evaluate("e => e.classList.contains('animando')")
        registrar(f'{rotulo}: expansão {"sem" if reduzido else "com"} animação',
                  animando == (not reduzido), animando)
        page.wait_for_timeout(500)
        registrar(f'{rotulo}: transição termina', not page.locator('#organograma').evaluate(
            "e => e.classList.contains('animando')"))
        sem_erros(f'motion-{rotulo}', erros)
        ctx.close()


def validacao_dos_dados(browser):
    """Copia o projeto para uma pasta temporária, estraga os dados de propósito e
    confere que a página mostra um aviso claro, registra o erro e não desenha nada."""
    print('\n[validação dos dados]')
    tmp = tempfile.mkdtemp(prefix='organograma-')
    copia = os.path.join(tmp, 'p')
    shutil.copytree(RAIZ, copia, ignore=shutil.ignore_patterns('screens', '__pycache__'))
    casos = [
        ('id duplicado', "{id:'a',nome:'A',tipo:'instituicao',filhos:[{id:'a',nome:'B',tipo:'orgao',filhos:[]}]}", 'Id duplicado'),
        ('tipo desconhecido', "{id:'a',nome:'A',tipo:'instituicao',filhos:[{id:'b',nome:'B',tipo:'inexistente',filhos:[]}]}", 'Tipo desconhecido'),
        ('atalho órfão', "{id:'a',nome:'A',tipo:'instituicao',filhos:[{id:'b',nome:'B',tipo:'orgao',targetId:'zzz',filhos:[]}]}", 'não existe'),
        ('nó sem nome', "{id:'a',nome:'A',tipo:'instituicao',filhos:[{id:'b',tipo:'orgao',filhos:[]}]}", 'sem nome'),
        ('id vazio', "{id:'a',nome:'A',tipo:'instituicao',filhos:[{id:'',nome:'B',tipo:'orgao',filhos:[]}]}", 'sem id válido'),
        ('dimensão desconhecida', "{id:'a',nome:'A',filhos:[{id:'b',nome:'B',dimensao:'mista',filhos:[]}]}", 'Dimensão desconhecida'),
    ]
    try:
        for nome, dados, trecho in casos:
            with open(os.path.join(copia, 'js', 'dados-organograma.js'), 'w', encoding='utf-8') as f:
                f.write(f'window.organogramaDados = {dados};')
            ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = ctx.new_page()
            erros = []
            page.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
            page.goto('file://' + os.path.join(copia, 'index.html'))
            page.wait_for_selector('[role=alert]')
            texto = page.text_content('[role=alert]')
            registrar(f'dados com {nome}: mostra aviso com "{trecho}"', trecho in texto, texto)
            registrar(f'dados com {nome}: não desenha cards', page.locator('.card').count() == 0)
            registrar(f'dados com {nome}: registra console.error específico',
                      any('[organograma] dados inválidos' in e for e in erros), erros[:2])
            ctx.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def hierarquia_oficial(browser):
    """Confere os ramos e siglas que definem a árvore publicada pela Câmara."""
    print('\n[hierarquia e siglas oficiais]')
    ctx, page, erros = nova_pagina(browser, 'desktop', 1280, 800)
    aguardar_organograma(page)
    estrutura = page.evaluate("""() => {
      const raiz = window.organogramaDados;
      const porSigla = new Map();
      const visitar = n => { if (n.sigla) porSigla.set(n.sigla, n); n.filhos.forEach(visitar); };
      visitar(raiz);
      const filhos = sigla => (porSigla.get(sigla)?.filhos || []).map(n => n.sigla);
      const total = [];
      (function contar(n) { total.push(n); n.filhos.forEach(contar); })(raiz);
      return {
        total: total.length,
        semSigla: total.filter(n => !n.sigla).map(n => n.nome),
        raiz: raiz.filhos.map(n => n.sigla),
        comissoes: filhos('COMS'),
        gabinetes: filhos('GABS'),
        mesa: filhos('MESA'),
        vpcs: filhos('VPCS'),
        presidencia: filhos('PRES'),
        chefiaPresidencia: filhos('GABP'),
        dger: filhos('DGER'),
        administracao: filhos('DADM'),
        patrimonio: filhos('DPAA')
      };
    }""")
    registrar('organograma tem 195 unidades e sigla em todas', estrutura['total'] == 195 and not estrutura['semSigla'], estrutura)
    registrar('raiz oficial: COMS, GABS e MESA', estrutura['raiz'] == ['COMS', 'GABS', 'MESA'], estrutura['raiz'])
    registrar('comissões incluem 23 comissões e as duas ouvidorias especiais',
              len(estrutura['comissoes']) == 25 and all(s in estrutura['comissoes'] for s in ('OECCR', 'OEM')),
              estrutura['comissoes'])
    registrar('gabinetes parlamentares permanecem como ramo próprio', estrutura['gabinetes'] == [], estrutura['gabinetes'])
    registrar('Mesa contém cinco ramos oficiais',
              estrutura['mesa'] == ['DFIN', 'DGER', 'DLEG', 'PRES', 'VPCS'], estrutura['mesa'])
    registrar('vice-presidências e secretarias subordinadas a VPCS',
              len(estrutura['vpcs']) == 11 and 'VPCS' not in estrutura['gabinetes'], estrutura['vpcs'])
    registrar('Gabinete da Presidência tem seus seis ramos oficiais',
              estrutura['presidencia'] == ['ASRM', 'AEAI', 'AEIM', 'CNTR', 'GABP', 'PROC'], estrutura['presidencia'])
    registrar('Chefia de Gabinete contém as unidades de apoio',
              estrutura['chefiaPresidencia'] == ['GEXP', 'GGOV', 'GADM', 'AJUP', 'AEP1', 'AEP2'],
              estrutura['chefiaPresidencia'])
    registrar('Diretoria Geral contém os três setores administrativos diretos e 14 diretorias',
              len(estrutura['dger']) == 17 and all(s in estrutura['dger'] for s in ('NUAD', 'CCTT', 'CMSG', 'DADM')),
              estrutura['dger'])
    registrar('Diretoria de Administração e Patrimônio seguem os pais publicados',
              estrutura['administracao'] == ['CENG', 'CEJA', 'CCAP']
              and estrutura['patrimonio'] == ['CPAT', 'APAT', 'GPAT', 'CALM', 'AALM'],
              (estrutura['administracao'], estrutura['patrimonio']))
    sem_erros('hierarquia oficial', erros)
    ctx.close()


def responsivo_e_incorporado(browser):
    """Uma página só: o perfil muda no limite de 640px; no modo incorporado o topo some."""
    print('\n[página única responsiva e modo incorporado]')
    # Limite do celular: 640px = acordeão e barra estática; 641px = desktop.
    for largura, celular in ((640, True), (641, False)):
        ctx, page, erros = nova_pagina(browser, 'desktop', largura, 800)
        aguardar_organograma(page)
        clicar(page, 'Comissões Legislativas')
        clicar(page, 'Mesa Diretora')
        esperado = 4 + 5 if celular else 4 + 25 + 5
        verificar(f'responsivo {largura}px usa o perfil {"celular (acordeão)" if celular else "desktop"}',
                  page.evaluate(CHECAR), esperado)
        posicao = page.evaluate("getComputedStyle(document.querySelector('.barra')).position")
        registrar(f'responsivo {largura}px: barra {"estática" if celular else "fixa"}',
                  posicao == ('static' if celular else 'sticky'), posicao)
        sem_erros(f'responsivo {largura}', erros)
        ctx.close()

    # Cruzar o limite com a página aberta refaz o layout sem erros nem sobreposição.
    ctx, page, erros = nova_pagina(browser, 'desktop', 1000, 800)
    aguardar_organograma(page)
    page.click('[data-acao="expandir-tudo"]')
    page.wait_for_timeout(900)
    for larg in (600, 1000, 420):
        page.set_viewport_size({'width': larg, 'height': 800})
        page.wait_for_timeout(700)
        verificar(f'cruzando o limite: {larg}px com tudo aberto', page.evaluate(CHECAR), 195)
    sem_erros('cruzando o limite', erros)
    ctx.close()

    # Sem JavaScript: aviso e o PDF continuam acessíveis.
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(PAGINA)
    registrar('sem JavaScript: aviso do <noscript> e link do PDF presentes',
              'precisa de JavaScript' in page.text_content('noscript') and page.locator('a[href$="CMG_organograma.pdf"]').count() == 1)
    ctx.close()

    # Modo incorporado forçado: topo só para leitores de tela, barra estática, página encolhe ao recolher.
    ctx, page, erros = nova_pagina(browser, 'desktop', 1000, 800, url=PAGINA + '?incorporado')
    aguardar_organograma(page)
    caixa = page.evaluate("(() => { const r = document.querySelector('.topo').getBoundingClientRect(); return [r.width, r.height]; })()")
    registrar('incorporado: cabeçalho de identificação fora da vista', caixa[0] <= 1 and caixa[1] <= 1, caixa)
    registrar('incorporado: h1 continua no DOM para leitores de tela', page.locator('.topo h1').count() == 1)
    registrar('incorporado: barra não é fixa', page.evaluate("getComputedStyle(document.querySelector('.barra')).position") == 'static')
    sem_erros('incorporado forçado', erros)
    ctx.close()

    ctx, page, erros = nova_pagina(browser, 'desktop', 1000, 800, url=PAGINA + '?incorporado=0')
    aguardar_organograma(page)
    registrar('?incorporado=0 mantém o cabeçalho', page.evaluate("document.querySelector('.topo').getBoundingClientRect().height") > 20)
    ctx.close()


def pagina_de_exemplo_no_site(browser):
    """exemplo-no-site.html: o organograma dentro de um <iframe> que acompanha a altura do conteúdo."""
    print('\n[exemplo do organograma dentro do site (iframe)]')
    for larg, alt in ((1280, 800), (390, 844), (320, 640)):
        tag = f'iframe{larg}'
        ctx = browser.new_context(viewport={'width': larg, 'height': alt})
        page = ctx.new_page()
        erros = []
        page.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: erros.append(str(e)))
        page.goto(EXEMPLO)
        quadro = page.frame_locator('iframe#organograma-cmg')
        quadro.locator('.card').first.wait_for()
        page.wait_for_timeout(500)
        h0 = page.evaluate("document.getElementById('organograma-cmg').getBoundingClientRect().height")
        registrar(f'{tag} quadro cresceu até o conteúdo (altura {round(h0)}px)', h0 > 300, h0)
        registrar(f'{tag} identificação do quadro fica a cargo do site (sem topo azul dentro do quadro)',
                  quadro.locator('.topo').evaluate("e => e.getBoundingClientRect().height") <= 1)
        quadro.locator('[data-acao="expandir-tudo"]').click()
        page.wait_for_timeout(1200)
        h1 = page.evaluate("document.getElementById('organograma-cmg').getBoundingClientRect().height")
        registrar(f'{tag} expandir tudo aumenta o quadro ({round(h0)} -> {round(h1)}px)', h1 > h0 + 500, (h0, h1))
        largura_horizontal = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 0.5")
        quadro_horizontal = quadro.locator('html').evaluate("e => e.scrollWidth > e.clientWidth + 0.5")
        registrar(f'{tag} sem rolagem horizontal na página hospedeira', not largura_horizontal)
        registrar(f'{tag} sem rolagem horizontal dentro do organograma', not quadro_horizontal)
        rolagem_interna = quadro.locator('html').evaluate("e => e.scrollHeight > e.clientHeight + 2")
        registrar(f'{tag} sem rolagem interna no quadro (rola a página do site)', not rolagem_interna)
        quadro.locator('[data-acao="recolher-tudo"]').click()
        page.wait_for_timeout(1200)
        h2 = page.evaluate("document.getElementById('organograma-cmg').getBoundingClientRect().height")
        registrar(f'{tag} recolher tudo encolhe o quadro ({round(h1)} -> {round(h2)}px)', h2 < h1 - 500, (h1, h2))
        sem_erros(tag, erros)
        ctx.close()


def cores_no_dom(browser):
    """Confere as cores REALMENTE renderizadas (não só as escritas no CSS).

    Para cada combinação de dimensão x macrounidade: (1) o fundo calculado pelo
    navegador é o do token do CSS (a variável foi aplicada); (2) contraste texto/fundo
    e do selo da sigla >= 4,5:1 medido no DOM; (3) contorno >= 3:1 com o papel nas
    unidades comuns. Também confere que a macrounidade tem a faixa amarela da paleta
    e que as duas dimensões têm cores diferentes."""
    print('\n[cores renderizadas]')
    import re

    def para_rgb(texto):
        return tuple(int(v) for v in re.findall(r'\d+', texto)[:3])

    def luminancia(rgb):
        lin = [(c / 255) / 12.92 if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    def contraste_rgb(a, b):
        la, lb = luminancia(a), luminancia(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    css = open(os.path.join(RAIZ, 'css', 'organograma.css'), encoding='utf-8').read()
    tokens = {}
    for bloco in re.finditer(r'(?m)^(\.macro)?\.dim-([a-z]+)\s*\{([^}]*)\}', css):
        fundo = re.search(r'--fundo:\s*#([0-9a-fA-F]{6})', bloco.group(3))
        if fundo:
            h = fundo.group(1)
            chave = ('macro-' if bloco.group(1) else '') + bloco.group(2)
            tokens[chave] = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    registrar('CSS define as 4 combinações (2 dimensões x comum/macro)', len(tokens) == 4, sorted(tokens))
    papel = (0xff, 0xff, 0xff)

    ctx, page, erros = nova_pagina(browser, 'desktop', 1440, 900)
    aguardar_organograma(page)
    page.click('[data-acao="expandir-tudo"]')
    page.wait_for_timeout(900)
    medidas = page.evaluate("""() => {
      const out = {}, contagem = {};
      document.querySelectorAll('#organograma .card').forEach(c => {
        const dim = c.classList.contains('dim-legislativa') ? 'legislativa' : c.classList.contains('dim-administrativa') ? 'administrativa' : null;
        if (!dim) return;
        const chave = (c.classList.contains('macro') ? 'macro-' : '') + dim;
        contagem[chave] = (contagem[chave] || 0) + 1;
        if (out[chave] && !c.querySelector('.card-sigla')) return;
        if (out[chave] && out[chave].siglaFundo) return;
        const cs = getComputedStyle(c);
        const s = c.querySelector('.card-sigla');
        const ss = s ? getComputedStyle(s) : null;
        out[chave] = {fundo: cs.backgroundColor, texto: cs.color, borda: cs.borderTopColor, bordaLado: cs.borderLeftColor,
                      topo: cs.borderTopWidth, topoCor: cs.borderTopColor,
                      siglaFundo: ss && ss.backgroundColor, siglaTexto: ss && ss.color};
      });
      return {out, contagem};
    }""")
    # Hoje toda macrounidade é administrativa; o estilo macro-legislativa existe no CSS para quando houver uma.
    registrar('as 3 combinações usadas pelos dados aparecem na página expandida',
              sorted(medidas['out']) == ['administrativa', 'legislativa', 'macro-administrativa'], sorted(medidas['out']))
    registrar('contagem: 40 legislativos e 21 macrounidades',
              medidas['contagem'].get('legislativa', 0) + medidas['contagem'].get('macro-legislativa', 0) == 40
              and medidas['contagem'].get('macro-legislativa', 0) + medidas['contagem'].get('macro-administrativa', 0) == 21,
              medidas['contagem'])
    for chave, m in sorted(medidas['out'].items()):
        fundo, texto = para_rgb(m['fundo']), para_rgb(m['texto'])
        registrar(f'{chave}: fundo renderizado = token do CSS', fundo == tokens.get(chave), (fundo, tokens.get(chave)))
        registrar(f'{chave}: contraste do texto >= 4,5 no DOM', contraste_rgb(texto, fundo) >= 4.5, round(contraste_rgb(texto, fundo), 2))
        if m['siglaFundo']:
            c = contraste_rgb(para_rgb(m['siglaTexto']), para_rgb(m['siglaFundo']))
            registrar(f'{chave}: contraste do selo da sigla >= 4,5 no DOM', c >= 4.5, round(c, 2))
        borda_lado = para_rgb(m['bordaLado'])
        registrar(f'{chave}: contorno >= 3:1 com o papel', contraste_rgb(borda_lado, papel) >= 3, round(contraste_rgb(borda_lado, papel), 2))
        if chave.startswith('macro-'):
            registrar(f'{chave}: faixa amarela (#DBAD57) de 6px no topo',
                      m['topo'] == '6px' and para_rgb(m['topoCor']) == (0xdb, 0xad, 0x57), (m['topo'], m['topoCor']))
        else:
            registrar(f'{chave}: sem faixa amarela', m['topo'] == '2px', m['topo'])
    registrar('legislativo (azul) e administrativo (verde) têm cores diferentes',
              tokens.get('legislativa') != tokens.get('administrativa')
              and tokens.get('macro-legislativa') != tokens.get('macro-administrativa'))
    registrar('azul e verde escuros usam a paleta definida',
              tokens.get('macro-legislativa') == (0x24, 0x2f, 0x62) and tokens.get('macro-administrativa') == (0x1a, 0x55, 0x29),
              (tokens.get('macro-legislativa'), tokens.get('macro-administrativa')))
    # macrounidades certas
    nomes = page.evaluate("[...document.querySelectorAll('#organograma .card.macro .card-nome')].map(e => e.textContent)")
    esperado = ['Gabinete da Presidência', 'Procuradoria Geral', 'Controladoria Geral']
    registrar('macrounidades incluem Gabinete da Presidência, Procuradoria e Controladoria',
              all(n in nomes for n in esperado), nomes)
    registrar('toda diretoria é macrounidade', all(n in nomes for n in nomes if n.startswith('Diretoria')) and sum(n.startswith('Diretoria') for n in nomes) == 18,
              sum(n.startswith('Diretoria') for n in nomes))
    registrar('Subprocuradoria-Geral não é macrounidade', 'Subprocuradoria-Geral' not in nomes)
    leg = page.evaluate("[...document.querySelectorAll('#organograma .card.dim-legislativa .card-nome')].map(e => e.textContent)")
    registrar('Plenário, Mesa, Conselho de Ética, vice-presidências e ouvidorias especiais são legislativos',
              all(any(n.startswith(x) for n in leg) for x in ('Plenário', 'Mesa Diretora', 'Conselho de Ética', '1ª Vice-Presidência', '1ª Secretaria', 'Ouvidoria Especial')), len(leg))
    sem_erros('cores', erros)
    ctx.close()


def nitidez_e_padronizacao(browser):
    """Garante (1) texto NÍTIDO e (2) cards PADRONIZADOS.

    Nitidez: em repouso, cada card precisa estar alinhado à grade de pixels FÍSICOS
    (posição x densidade da tela = inteiro), ter largura/altura inteiras em px CSS e
    NÃO ter camada de GPU permanente (`will-change`). Testa densidades 1, 1.25 e 1.5
    (zoom/escala do Windows), onde o problema de texto embaçado aparecia.

    Padronização: as unidades comuns (das duas dimensões) têm o mesmo formato; as
    macrounidades têm um formato próprio (mesma largura, fonte maior, faixa amarela)."""
    print('\n[nitidez e padronização]')
    for dpr in (1, 1.25, 1.5):
        for modo, larg, alt in (('desktop', 1280, 800), ('mobile', 390, 844)):
            tag = f'nitidez-{modo}-dpr{dpr}'
            ctx = browser.new_context(viewport={'width': larg, 'height': alt}, device_scale_factor=dpr,
                                      has_touch=(modo == 'mobile'), is_mobile=(modo == 'mobile'))
            page = ctx.new_page()
            erros = []
            page.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
            page.on('pageerror', lambda e: erros.append(str(e)))
            page.goto(URL[modo])
            aguardar_organograma(page)
            page.click('[data-acao=expandir-tudo]')
            page.wait_for_timeout(900)
            # Rola até uma posição fracionária de propósito: não pode afetar o alinhamento.
            r = page.evaluate("""(dpr) => {
              const sx = window.scrollX, sy = window.scrollY;
              const ruins = []; let n = 0, willChange = 0;
              document.querySelectorAll('#organograma .card').forEach((el) => {
                const b = el.getBoundingClientRect();
                const px = (b.left + sx) * dpr, py = (b.top + sy) * dpr;
                const frac = (v) => Math.abs(v - Math.round(v));
                n++;
                if (frac(px) > 0.02 || frac(py) > 0.02 || frac(b.width) > 0.02 || frac(b.height) > 0.02) {
                  if (ruins.length < 3) ruins.push([el.querySelector('.card-nome').textContent, b.left + sx, b.top + sy, b.width, b.height]);
                }
                if (getComputedStyle(el).willChange !== 'auto') willChange++;
              });
              return { n, ruins, willChange, animando: document.querySelector('#organograma').classList.contains('animando') };
            }""", dpr)
            registrar(f'{tag}: {r["n"]} cards alinhados à grade de pixels', not r['ruins'], r['ruins'])
            registrar(f'{tag}: sem will-change permanente', r['willChange'] == 0, r['willChange'])
            registrar(f'{tag}: classe animando removida em repouso', not r['animando'])
            sem_erros(tag, erros)
            ctx.close()

    ctx, page, erros = nova_pagina(browser, 'desktop', 1280, 800)
    aguardar_organograma(page)
    page.click('[data-acao=expandir-tudo]')
    page.wait_for_timeout(900)
    por_grupo = page.evaluate("""() => {
      const m = {};
      document.querySelectorAll('#organograma .card').forEach((el) => {
        const grupo = el.classList.contains('macro') ? 'macro' : 'comum';
        const cs = getComputedStyle(el), nome = getComputedStyle(el.querySelector('.card-nome'));
        (m[grupo] = m[grupo] || new Set()).add(JSON.stringify({
          w: cs.width, bw: [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth],
          bs: cs.borderTopStyle, r: cs.borderTopLeftRadius, pad: cs.padding, fs: cs.fontSize, fw: cs.fontWeight,
          nfs: nome.fontSize, nfw: nome.fontWeight, fam: cs.fontFamily
        }));
      });
      return Object.fromEntries(Object.entries(m).map(([k, v]) => [k, [...v]]));
    }""")
    registrar('padronização: todas as unidades comuns (legislativas e administrativas) têm o mesmo formato',
              len(por_grupo['comum']) == 1, por_grupo['comum'][:2])
    registrar('padronização: todas as macrounidades têm o mesmo formato', len(por_grupo['macro']) == 1, por_grupo['macro'][:2])
    comum, macro = por_grupo['comum'][0], por_grupo['macro'][0]
    registrar('macrounidade tem apresentação diferente (texto maior e faixa superior)', comum != macro)
    import json
    c, mc = json.loads(comum), json.loads(macro)
    registrar('macrounidade: mesma largura dos demais cartões (o layout não muda)', c['w'] == mc['w'], (c['w'], mc['w']))
    registrar('macrounidade: fonte maior', float(mc['fs'][:-2]) > float(c['fs'][:-2]), (c['fs'], mc['fs']))
    fam = page.evaluate("getComputedStyle(document.querySelector('.card')).fontFamily")
    registrar('fonte: Calibri (manual da CMG) é a primeira da pilha', fam.lower().startswith('calibri'), fam)
    sem_serifa = page.evaluate("""() => {
      const bons = ['.topo h1', '.botao', '.card', '.card-nome']
      return bons.map((s) => [s, getComputedStyle(document.querySelector(s)).fontFamily]);
    }""")
    registrar('fonte: todo o conteúdo usa a mesma pilha sem serifa',
              len({f for _, f in sem_serifa}) == 1 and 'serif' in sem_serifa[0][1].split(',')[-1] and 'Georgia' not in sem_serifa[0][1],
              sem_serifa)
    sem_erros('padronização', erros)
    ctx.close()


# Ponto de entrada da suíte: agrupa cenários por comportamento e testa os dois perfis.
with sync_playwright() as p:
    navegador = p.chromium.launch()

    # Layout e interação básicos (cenários originais)
    cenario(navegador, 'desktop', 1440, 900, redimensionar_para=(1024, 768))
    cenario(navegador, 'desktop', 1920, 1080)
    cenario(navegador, 'desktop', 800, 900)
    cenario(navegador, 'mobile', 768, 1024)
    cenario(navegador, 'mobile', 430, 932, redimensionar_para=(360, 740))
    cenario(navegador, 'mobile', 390, 844)
    cenario(navegador, 'mobile', 320, 640)
    # Janela estreita (perfil celular escolhido pela própria página): sem rolagem horizontal
    cenario(navegador, 'desktop', 360, 740)
    navegacao_e_documentos(navegador)

    # Recursos de interação, tema e incorporação
    proximo_nivel(navegador, 'desktop', 1280, 800)
    proximo_nivel(navegador, 'mobile', 390, 844)
    simplificacao(navegador, 'desktop', 1280, 800)
    simplificacao(navegador, 'mobile', 390, 844)
    acordeao(navegador, 'mobile', 390, 844)
    acordeao(navegador, 'desktop', 1280, 800)
    teclado_novos_elementos(navegador, 'desktop', 1280, 800)
    teclado_novos_elementos(navegador, 'mobile', 390, 844)
    movimento_reduzido(navegador)
    validacao_dos_dados(navegador)
    hierarquia_oficial(navegador)
    responsivo_e_incorporado(navegador)
    pagina_de_exemplo_no_site(navegador)
    cores_no_dom(navegador)
    nitidez_e_padronizacao(navegador)
    navegador.close()

print()
if falhas:
    print(f'{len(falhas)} falha(s) em {total} verificações:')
    for nome, detalhe in falhas:
        print(' -', nome, detalhe)
    sys.exit(1)
print(f'Tudo certo: {total} verificações sem falhas')
