/**
 * @file Modo incorporado: a página dentro de um <iframe> de outra página (o site da Câmara).
 *
 * Carregado no <head>, ANTES da pintura, para a página já nascer no modo certo
 * (sem piscar o cabeçalho que depois some).
 *
 * Quando o modo liga:
 *   - automaticamente, se a página está dentro de um <iframe>;
 *   - à força com `?incorporado` na URL (para testar fora de um quadro);
 *   - nunca com `?incorporado=0`.
 *
 * O que muda no modo incorporado (CSS: seção 8 de organograma.css):
 *   o cabeçalho azul de identificação e o "Voltar ao site" saem da vista (o site já tem
 *   os seus) e a barra deixa de ser fixa.
 *
 * Altura do quadro: um <iframe> não cresce sozinho com o conteúdo. Por isso a página
 * avisa a página-mãe da sua altura sempre que ela muda (expandir, recolher, redimensionar):
 *
 *   window.parent.postMessage({ tipo: 'organograma-cmg:altura', altura: 1234 }, '*')
 *
 * A página-mãe ouve a mensagem e ajusta a altura do <iframe> (exemplo pronto em
 * exemplo-no-site.html e em INCORPORACAO.md). Sem esse ouvinte nada quebra: o quadro
 * fica com a altura que tiver e o organograma rola dentro dele.
 */
(function (global) {
  'use strict';

  const consulta = global.location.search;
  const desligado = /[?&]incorporado=0(&|$)/.test(consulta);
  const forcado = /[?&]incorporado(=|&|$)/.test(consulta);

  let emQuadro;
  try {
    emQuadro = global.self !== global.top;
  } catch (erro) {
    emQuadro = true; // acesso ao topo bloqueado entre origens = estamos num quadro
  }

  if (desligado || !(emQuadro || forcado)) return;

  document.documentElement.classList.add('incorporado');

  // A mensagem só faz sentido dentro de um quadro (fora dele, window.parent é a própria janela).
  if (!emQuadro) return;

  let agendado = false;

  function avisarAltura() {
    agendado = false;
    // body.offsetHeight (e não a altura da janela): o quadro precisa poder encolher.
    global.parent.postMessage({ tipo: 'organograma-cmg:altura', altura: document.body.offsetHeight }, '*');
  }

  /** Agrupa várias mudanças do mesmo quadro de animação numa única mensagem. */
  function agendar() {
    if (agendado) return;
    agendado = true;
    global.requestAnimationFrame(avisarAltura);
  }

  document.addEventListener('DOMContentLoaded', () => {
    if ('ResizeObserver' in global) new global.ResizeObserver(agendar).observe(document.body);
    else global.addEventListener('resize', agendar);
    agendar();
  });
}(window));
