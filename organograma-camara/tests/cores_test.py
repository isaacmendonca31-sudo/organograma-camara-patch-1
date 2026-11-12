"""Teste de acessibilidade das cores: python3 tests/cores_test.py [--tabela]

Lê as cores DIRETO de css/organograma.css (única fonte da verdade) e confere:

  1. Contraste WCAG 2.2: texto >= 4,5:1 (AA); bordas, linhas e anel de foco >= 3:1 (1.4.11),
     para as 4 apresentações de card (legislativa/administrativa x comum/macrounidade),
     para a interface (topo azul, botões, busca) e para os detalhes amarelos.
  2. Identidade: os seis tokens da paleta definida para o projeto são usados
     nas dimensões, macrounidades e detalhes.
  3. Daltonismo: a distância perceptual (CIEDE2000) entre as dimensões legislativa e
     administrativa (contorno das unidades comuns e preenchimento das macrounidades), medida
     sob visão normal, protanopia, deuteranopia e tritanopia, nunca fica abaixo de LIMITE_DE.
     O contraste visual das dimensões também é exposto em texto nos rótulos ARIA.

Dependências (apenas para desenvolvedores, o site em si não usa nada disso):
    pip install numpy scikit-image

Simulação de daltonismo: matrizes de Machado, Oliveira e Fernandes (2009), severidade 1,0,
aplicadas em RGB linear. Distância de cor: CIEDE2000 (a mais próxima da percepção humana).
"""
import os
import re
import sys

try:
    import numpy as np
    from skimage import color as sk
except ImportError:
    sys.exit('Instale as dependências do teste: pip install numpy scikit-image')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RAIZ, 'css', 'organograma.css')

# Limites do projeto (ver LEIAME.md, seção "Tema: paleta CMG").
CONTRASTE_TEXTO = 4.5      # WCAG AA para texto normal
CONTRASTE_TEXTO_ALTO = 7.0 # AAA, exigido do texto principal da página
CONTRASTE_NAO_TEXTO = 3.0  # WCAG 1.4.11 (bordas, linhas, anel de foco)
LIMITE_DE = 10.0           # CIEDE2000 mínimo entre as dimensões (acima de ~5 já é visível)

# Paleta informada para o projeto (azuis, verdes e amarelos).
PALETA = {
    'cmg-azul': '#242f62',
    'cmg-azul-claro': '#4c61bd',
    'cmg-verde': '#1a5529',
    'cmg-verde-claro': '#2f9d4c',
    'cmg-dourado': '#ba8727',
    'cmg-dourado-claro': '#dbad57',
}

# As 4 apresentações de card definidas na seção 7 do CSS.
APRESENTACOES = ['legislativa', 'administrativa', 'macro-legislativa', 'macro-administrativa']

CVD = {
    'normal': np.eye(3),
    'protanopia': np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    'deuteranopia': np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    'tritanopia': np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


# ---------------------------------------------------------------------------
# Matemática de cor
# ---------------------------------------------------------------------------

def hex_rgb(h):
    """Converte uma cor #RRGGBB em três canais RGB normalizados entre 0 e 1."""
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255


def para_linear(c):
    """Converte sRGB para luz linear, necessária para luminância e simulação CVD."""
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def de_linear(c):
    """Converte a simulação em luz linear de volta para valores sRGB exibíveis."""
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def luminancia(h):
    r, g, b = para_linear(hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    """Razão de contraste WCAG entre duas cores #RRGGBB."""
    la, lb = luminancia(a), luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def lab(h, visao='normal'):
    """Aplica a visão escolhida e representa a cor em CIELAB para comparação perceptual."""
    simulada = de_linear(CVD[visao] @ para_linear(hex_rgb(h)))
    return sk.rgb2lab(simulada.reshape(1, 1, 3))[0, 0]


def distancia(a, b):
    """Menor CIEDE2000 entre a e b considerando visão normal e os três tipos de daltonismo."""
    return min(float(sk.deltaE_ciede2000(lab(a, v), lab(b, v))) for v in CVD)


# ---------------------------------------------------------------------------
# Leitura do CSS
# ---------------------------------------------------------------------------

def ler_css():
    """Lê os tokens de :root e as variáveis de cor de cada apresentação de card."""
    css = open(CSS, encoding='utf-8').read()
    raiz = re.search(r':root\s*\{([^}]*)\}', css).group(1)
    ui = {m.group(1): m.group(2).lower() for m in re.finditer(r'--([a-z-]+):\s*(#[0-9a-fA-F]{6})', raiz)}
    # Tokens que apontam para outro (ex.: --acento: var(--cmg-azul)) herdam a cor dele.
    for m in re.finditer(r'--([a-z-]+):\s*var\(--([a-z-]+)\)', raiz):
        if m.group(2) in ui:
            ui[m.group(1)] = ui[m.group(2)]

    cards = {}
    for bloco in re.finditer(r'(?m)^(\.macro)?\.dim-([a-z]+)\s*\{([^}]*)\}', css):
        nome = ('macro-' if bloco.group(1) else '') + bloco.group(2)
        cores = {m.group(1): m.group(2).lower() for m in re.finditer(r'--([a-z-]+):\s*(#[0-9a-fA-F]{6})', bloco.group(3))}
        cards[nome] = cores
    return ui, cards


# ---------------------------------------------------------------------------
# Verificações
# ---------------------------------------------------------------------------

falhas = []
total = 0
resumo = {}


def exigir(nome, valor, minimo, formato='{:.1f}'):
    """Registra uma verificação `valor >= minimo`."""
    global total
    total += 1
    ok = valor >= minimo - 1e-9
    if not ok:
        falhas.append(f'{nome}: {formato.format(valor)} (mínimo {formato.format(minimo)})')
    return ok


def exigir_igual(nome, valor, esperado):
    """Registra uma verificação `valor == esperado`."""
    global total
    total += 1
    if valor != esperado:
        falhas.append(f'{nome}: {valor} (esperado {esperado})')


def main():
    ui, cards = ler_css()
    papel = ui['papel']

    faltando = [a for a in APRESENTACOES if a not in cards]
    if faltando:
        sys.exit(f'Apresentações sem cores em organograma.css: {faltando}')
    extras = [a for a in cards if a not in APRESENTACOES]
    if extras:
        sys.exit(f'Apresentações novas sem regra de teste (inclua em APRESENTACOES): {extras}')

    # 0) Paleta do projeto ---------------------------------------------------------
    for nome, valor in PALETA.items():
        exigir_igual(f'--{nome} usa a cor definida', ui.get(nome), valor)
    exigir_igual('unidade legislativa comum usa o azul claro', cards['legislativa']['fundo'], PALETA['cmg-azul-claro'])
    exigir_igual('unidade administrativa comum usa o verde claro', cards['administrativa']['fundo'], PALETA['cmg-verde-claro'])
    exigir_igual('macrounidade legislativa usa o azul escuro', cards['macro-legislativa']['fundo'], PALETA['cmg-azul'])
    exigir_igual('macrounidade administrativa usa o verde escuro', cards['macro-administrativa']['fundo'], PALETA['cmg-verde'])
    exigir_igual('conector usa o amarelo escuro', ui['linha'], PALETA['cmg-dourado'])
    exigir_igual('faixa de macrounidade usa o amarelo claro', ui['cmg-dourado-claro'], PALETA['cmg-dourado-claro'])
    resumo['Paleta'] = 'azuis #242F62/#4C61BD, verdes #1A5529/#2F9D4C, amarelos #BA8727/#DBAD57'

    # 1) Contraste dos cards ---------------------------------------------------
    menor_texto = menor_chip = menor_borda = 99
    for nome, c in cards.items():
        r = contraste(c['texto'], c['fundo'])
        menor_texto = min(menor_texto, r)
        exigir(f'texto do card {nome}', r, CONTRASTE_TEXTO)

        r = contraste(c['chip-texto'], c['chip-fundo'])
        menor_chip = min(menor_chip, r)
        exigir(f'selo da sigla de {nome}', r, CONTRASTE_TEXTO)

        r = contraste(c['borda'], papel)
        menor_borda = min(menor_borda, r)
        exigir(f'borda de {nome} contra o papel', r, CONTRASTE_NAO_TEXTO)

        # O selo da sigla precisa se destacar do fundo do próprio card.
        exigir(f'selo da sigla de {nome} contra o fundo do card', contraste(c['chip-fundo'], c['fundo']), CONTRASTE_NAO_TEXTO)
    resumo['Texto dos cards (mín.)'] = f'{menor_texto:.1f}:1 (exigido 4,5)'
    resumo['Selo da sigla (mín.)'] = f'{menor_chip:.1f}:1 (exigido 4,5)'
    resumo['Borda dos cards (mín.)'] = f'{menor_borda:.1f}:1 (exigido 3)'

    # 2) Contraste da interface ------------------------------------------------
    branco = '#ffffff'
    azul = ui['cmg-azul']
    interface = [
        ('texto principal', ui['tinta'], papel, CONTRASTE_TEXTO_ALTO),
        ('texto secundário', ui['tinta-suave'], papel, CONTRASTE_TEXTO),
        ('texto secundário sobre hover', ui['tinta-suave'], ui['hover'], CONTRASTE_TEXTO),
        ('título do topo (branco sobre azul)', branco, azul, CONTRASTE_TEXTO_ALTO),
        ('nome da Casa no topo', '#e3e7f6', azul, CONTRASTE_TEXTO),
        ('botão (texto)', ui['acento'], papel, CONTRASTE_TEXTO_ALTO),
        ('botão sobre hover', ui['acento'], ui['hover'], CONTRASTE_TEXTO),
        ('botão principal', branco, ui['acento'], CONTRASTE_TEXTO),
        ('botão principal em hover', branco, ui['acento-escuro'], CONTRASTE_TEXTO),
        ('texto de exemplo da busca', ui['placeholder'], branco, CONTRASTE_TEXTO),
        ('mensagem de erro', ui['erro-texto'], ui['erro-fundo'], CONTRASTE_TEXTO),
        ('borda do campo de busca', ui['campo-borda'], branco, CONTRASTE_NAO_TEXTO),
        ('conectores', ui['linha'], papel, CONTRASTE_NAO_TEXTO),
        ('conectores em destaque', ui['destaque'], papel, CONTRASTE_NAO_TEXTO),
        ('anel de foco', ui['foco'], papel, CONTRASTE_NAO_TEXTO),
        ('anel de foco do link do topo (branco sobre azul)', branco, azul, CONTRASTE_NAO_TEXTO),
        ('borda da mensagem de erro', ui['erro-borda'], papel, CONTRASTE_NAO_TEXTO),
        ('faixa amarela sobre o azul escuro', ui['cmg-dourado-claro'], PALETA['cmg-azul'], CONTRASTE_NAO_TEXTO),
        ('faixa amarela sobre o verde escuro', ui['cmg-dourado-claro'], PALETA['cmg-verde'], CONTRASTE_NAO_TEXTO),
    ]
    for nome, a, b, minimo in interface:
        exigir(nome, contraste(a, b), minimo)
    resumo['Interface'] = f'{len(interface)} pares verificados'

    # 3) Daltonismo: as dimensões precisam ser diferentes -------------------------
    distancias = {}
    pares = [
        ('contorno das unidades comuns', cards['legislativa']['borda'], cards['administrativa']['borda']),
        ('preenchimento das macrounidades', cards['macro-legislativa']['fundo'], cards['macro-administrativa']['fundo']),
        ('texto do selo das unidades comuns', cards['legislativa']['chip-texto'], cards['administrativa']['chip-texto']),
    ]
    menor = 999
    for rotulo, a, b in pares:
        d = distancia(a, b)
        distancias[rotulo] = d
        menor = min(menor, d)
        exigir(f'legislativa x administrativa: {rotulo} (CIEDE2000, pior visão)', d, LIMITE_DE)
    resumo['Daltonismo, legislativa x administrativa (mín.)'] = f'{menor:.1f} (exigido {LIMITE_DE:.0f})'

    d = distancia(ui['linha'], ui['destaque'])
    exigir('conector comum x conector em destaque', d, LIMITE_DE)
    resumo['Conector comum x destaque'] = f'{d:.1f} (exigido {LIMITE_DE:.0f})'

    # 4) Macrounidade: tom escuro x tom claro da mesma dimensão ----------------------
    for dim in ('legislativa', 'administrativa'):
        escuro = lab(cards['macro-' + dim]['fundo'])[0]
        claro = lab(cards[dim]['fundo'])[0]
        exigir(f'macro-{dim} é mais escura que a unidade comum (L*)', claro - escuro, 20.0)
    resumo['Macrounidade x comum'] = 'diferença de luminosidade L* >= 20'

    # Relatório ----------------------------------------------------------------
    if '--tabela' in sys.argv:
        print('Distância CIEDE2000 (pior visão) entre as dimensões:')
        for rotulo, d in sorted(distancias.items(), key=lambda kv: kv[1]):
            print(f'  {d:5.1f}  {rotulo}')
        print()
    print('Resumo da paleta')
    for k, v in resumo.items():
        print(f'  {k}: {v}')
    print()
    if falhas:
        print(f'{len(falhas)} falha(s) em {total} verificações:')
        for f in falhas:
            print(' -', f)
        sys.exit(1)
    print(f'Tudo certo: {total} verificações de cor sem falhas')


main()
