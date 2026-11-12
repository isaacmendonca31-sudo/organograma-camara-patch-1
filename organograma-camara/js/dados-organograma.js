(() => {
  let nextNodeId = 0;

  const SIGLAS_OFICIAIS = Object.freeze({
    'Plenário': 'CMG',
    'Comissões Legislativas': 'COMS',
    'Gabinetes Parlamentares': 'GABS',
    'Mesa Diretora': 'MESA',
    'Vice-presidências e secretarias': 'VPCS',
    '1ª Vice-Presidência': '1VPR',
    '2ª Vice-Presidência': '2VPR',
    '3ª Vice-Presidência': '3VPR',
    '4ª Vice-Presidência': '4VPR',
    '1ª Secretaria': '1SEC',
    '2ª Secretaria': '2SEC',
    '3ª Secretaria': '3SEC',
    '4ª Secretaria': '4SEC',
    '5ª Secretaria': '5SEC',
    '1ª Vice-Presidência Corregedoria': '1VPC',
    '2ª Vice-Presidência Corregedoria': '2VPC',
    'Diretoria Financeira': 'DFIN',
    'Coordenadoria de Gestão Financeira': 'CFIN',
    'Gerência da Tesouraria': 'GTES',
    'Gerência de Contabilidade': 'GCTB',
    'Chefia do Núcleo de Gestão das Obrigações Acessórias': 'NOBA',
    'Coordenadoria de Planejamento Orçamentário e Financeiro': 'CPOF',
    'Gerência de Gestão Orçamentária': 'GGOR',
    'Diretoria Legislativa': 'DLEG',
    'Chefia do Núcleo de Apoio Parlamentar': 'NPAR',
    'Coordenadoria de Expediente e Protocolo': 'CEXP',
    'Gerência de Expediente e Registro': 'GERE',
    'Chefia do Núcleo de Protocolo': 'NPRO',
    'Coordenadoria Legislativa de Plenário': 'CLPL',
    'Gerência de Apoio Legislativo': 'GLEG',
    'Gerência de Documentação': 'GDOC',
    'Gerência de Processamento e Controle': 'GPCO',
    'Gerência de Taquigrafia': 'GTAQ',
    'Chefia do Núcleo de Taquigrafia e Gravação': 'NTAG',
    'Gerência de Redação de Atas': 'GREA',
    'Núcleo de Serviços Especiais da Taquigrafia': 'NSET',
    'Núcleo de Serviços Especiais do Plenário': 'NSEP',
    'Núcleo de Serviços Especiais da Revisão da Taquigrafia': 'NSER',
    'Assessoria de Promoção à Participação Comunitária e Popular': 'APCP',
    'Diretoria Executiva Parlamentar': 'DPAR',
    'Coordenadoria Executiva Parlamentar': 'CPAR',
    'Assessoria de Execução e Fiscalização de Emendas Individuais': 'AEFE',
    'Diretoria Geral': 'DGER',
    'Chefia do Núcleo de Assistência Administrativa': 'NUAD',
    'Coordenadoria de Contratos': 'CCTT',
    'Assessoria de Gestão de Contratos': 'ACTT',
    'Gerência de Contratos': 'GCTT',
    'Chefia do Núcleo de Assistência à Gerência de Contratos': 'NCTT',
    'Coordenação de Manutenção e Serviços Gerais': 'CMSG',
    'Diretoria de Administração': 'DADM',
    'Coordenadoria de Engenharia': 'CENG',
    'Chefia do Núcleo de Apoio à Engenharia': 'NENG',
    'Coordenadoria de Contrato de Estágio e Jovem Aprendiz': 'CEJA',
    'Chefia do Núcleo de Estágio': 'NEST',
    'Coordenadoria de Controle da CEAP': 'CCAP',
    'Gerência de Controle da CEAP': 'GCAP',
    'Assessoria de Controle da CEAP': 'ACAP',
    'Diretoria de Compras e Licitações': 'DCLI',
    'Agente de Contratação': 'AGNT',
    'Coordenadoria de Compras': 'CCOM',
    'Gerência de Cotação de Preços': 'GCOT',
    'Diretoria de Comunicação': 'DCOM',
    'Coordenadoria de Imprensa e Comunicação': 'CIMC',
    'Assessoria de Comunicação': 'ACOM',
    'Assessoria de Imprensa Interna': 'AIMI',
    'Assessoria de Mídias Digitais': 'AMID',
    'Assessoria de Relações Públicas': 'ARPU',
    'Assessoria de Radialismo e Televisão': 'ARTV',
    'Assessor de Website': 'AWEB',
    'Coordenadoria da TV Câmara': 'CTVC',
    'Gerência de Gravação e Som': 'GSOM',
    'Chefia do Núcleo de Gravação e Som': 'NSOM',
    'Chefia do Núcleo de Áudio e Vídeo': 'NAUV',
    'Gerência de Fotojornalismo': 'GFOT',
    'Coordenadoria de Áudio e Projeção': 'CAPR',
    'Chefia do Núcleo de Áudio e Projeção': 'NAPR',
    'Diretoria de Recursos Humanos': 'DRHU',
    'Coordenadoria de Pessoal': 'COPE',
    'Chefia do Núcleo de Processos Administrativos': 'NPAD',
    'Gerência de Arquivo e Documentação': 'GARD',
    'Coordenadoria de Folha de Pagamento': 'CFOP',
    'Gerência de Processamento da Folha': 'GPFO',
    'Chefia do Núcleo de Cálculo da Folha': 'NCAF',
    'Diretoria do SESMT': 'DSMT',
    'Coordenadoria do SESMT': 'CSMT',
    'Assessoria de Apoio ao SESMT': 'ASMT',
    'Gerência Especializada em Segurança e Medicina do Trabalho': 'GSMT',
    'Diretoria de Transporte e Abastecimento': 'DTAB',
    'Coordenadoria de Transporte': 'CTRA',
    'Chefia do Núcleo de Abastecimento': 'NUAB',
    'Diretoria de Tecnologia da Informação': 'DTIN',
    'Coordenadoria de Informática': 'CINF',
    'Gerência de Hardware': 'GHAR',
    'Gerência de Suporte de Informática': 'GSIN',
    'Gerência de Software': 'GSOF',
    'Diretoria de Segurança e Inteligência': 'DSIN',
    'Serviço de Segurança da Presidência': 'SSIN',
    'Assessoria de Apoio de Segurança': 'ASIN',
    'Coordenação de Segurança e Inteligência': 'CSIN',
    'Diretoria Executiva do Cerimonial': 'DCER',
    'Assessoria de Apoio ao Cerimonial': 'ACER',
    'Núcleo de Serviços Especiais do Cerimonial': 'NCER',
    'Diretoria de Integração Social e Cidadania': 'DISC',
    'Coordenação de Integração Social e Cidadania': 'CISC',
    'Assessoria de Apoio à Integração Social e Cidadania': 'AISC',
    'Diretoria de Patrimônio e Almoxarifado': 'DPAA',
    'Coordenadoria de Patrimônio': 'CPAT',
    'Assessoria de Apoio ao Patrimônio': 'APAT',
    'Gerência de Patrimônio': 'GPAT',
    'Chefia do Núcleo de Patrimônio': 'NPAT',
    'Coordenadoria de Almoxarifado': 'CALM',
    'Assessoria de Apoio ao Almoxarifado': 'AALM',
    'Gerência de Almoxarifado': 'GALM',
    'Chefia do Núcleo de Almoxarifado': 'NALM',
    'Diretoria de Promoção de Atividades de Cultura e Ensino': 'DCEN',
    'Coordenadoria do Parlamento Jovem': 'CPAJ',
    'Assessoria do Parlamento Jovem': 'APAJ',
    'Chefia do Núcleo de Apoio ao Parlamento Jovem': 'NPAJ',
    'Coordenadoria da Escola do Legislativo': 'CELE',
    'Chefia do Núcleo de Coordenação da Escola do Legislativo': 'NCEL',
    'Assessoria Administrativa da Escola do Legislativo': 'ADEL',
    'Assessoria Acadêmica da Escola do Legislativo': 'ACEL',
    'Coordenadoria de Atividades Culturais e Comunitárias': 'CCUC',
    'Assessoria de Apoio às Atividades Culturais e Comunitárias': 'ACUC',
    'Chefia do Núcleo de Apoio às Atividades Culturais e Comunitárias': 'NCUC',
    'Diretoria das Ouvidorias': 'DOUV',
    'Coordenadoria do Canal Cidadania': 'CCID',
    'Assessoria de Apoio ao Canal Cidadania': 'ACID',
    'Chefia do Núcleo de Apoio ao Canal Cidadania': 'NCID',
    'Coordenadoria da Ouvidoria da Mulher': 'COUM',
    'Assessoria de Apoio da Ouvidoria da Mulher': 'AOUM',
    'Chefia do Núcleo de Apoio à Ouvidoria da Mulher': 'NOUM',
    'Coordenadoria da Ouvidoria Especial de Combate a Crimes Raciais': 'COCR',
    'Assessoria de Apoio da Ouvidoria Especial de Combate a Crimes Raciais': 'AOCR',
    'Chefia do Núcleo de Apoio da Ouvidoria Especial de Combate a Crimes Raciais': 'NOCR',
    'Diretoria de Transparência e Proteção de Dados': 'DTPD',
    'Coordenadoria do Portal da Transparência': 'CPTR',
    'Assessoria de Apoio ao Portal da Transparência': 'APTR',
    'Encarregado pelo Tratamento de Dados Pessoais': 'ENCD',
    'Gabinete da Presidência': 'PRES',
    'Assessoria de Articulação Política da Região Metropolitana': 'ASRM',
    'Assessoria de Apoio à Articulação Política da Região Metropolitana': 'APRM',
    'Assessoria Executiva de Assuntos Institucionais': 'AEAI',
    'Coordenadoria da Liderança de Governo': 'CLIG',
    'Assessoria de Apoio à Liderança de Governo': 'ALIG',
    'Assessoria Executiva de Imprensa da Presidência': 'AEIM',
    'Assessoria de Imprensa da Presidência': 'AIMP',
    'Controladoria Geral': 'CNTR',
    'Chefia do Núcleo de Apoio ao Controle Interno': 'NCIN',
    'Gerência de Pareceres Técnicos': 'GPTE',
    'Coordenadoria de Auditoria e Exame de Contas': 'CAEC',
    'Chefia do Núcleo de Controle Interno e Auditoria': 'NCIA',
    'Coordenadoria de Análise de Despesa de Pessoal e Contábil': 'CDPC',
    'Gerência de Folha de Pagamento e Gestão de Pessoal': 'CFOP',
    'Gerência de Análise de Pagamentos': 'GAPA',
    'Chefia de Gabinete': 'GABP',
    'Gerência de Expediente da Presidência': 'GEXP',
    'Gerência de Governança': 'GGOV',
    'Gerência de Apoio Administrativo': 'GADM',
    'Assessoria Jurídica da Presidência': 'AJUP',
    'Gerência Jurídica da Presidência': 'GJUP',
    'Assessoria Especial da Presidência I': 'AEP1',
    'Assessoria Especial da Presidência II': 'AEP2',
    'Procuradoria Geral': 'PROC',
    'Gerência de Apoio à Procuradoria': 'GPRO',
    'Secretaria Geral da Procuradoria': 'SPRO',
    'Subprocuradoria-Geral': 'SUBP',
    'Chefia do Núcleo de Assuntos Administrativos': 'NADM',
    'Chefia do Núcleo de Assuntos Extrajudiciais e Judiciais': 'NJUD',
    'Chefia do Núcleo de Assuntos Legislativos': 'NLEG',
    'Ouvidoria Especial de Combate a Crimes Raciais': 'OECCR',
    'Ouvidoria Especial da Mulher': 'OEM'
  });

  /*
   * GUIA RÁPIDO PARA EDITAR O ORGANOGRAMA
   *
   * Cada card é criado com node(nome, tipo, filhos, metadata):
   *   node('Nova Diretoria', 'diretoria', [
   *     coordenadoria('Nova Coordenadoria', [
   *       gerencia('Nova Gerência')
   *     ])
   *   ])
   *
   * O terceiro argumento é uma lista de filhos; sem filhos, omita-o. Cada item
   * dessa lista fica subordinado ao nó que a contém. `node` monta os campos
   * id, nome, tipo, cargo e filhos; `metadata` acrescenta campos opcionais.
   * Use, por exemplo, { sigla: 'TI' } para exibir/pesquisar uma sigla ou
   * { targetId: outroCard.id } para criar um atalho para um card existente.
   * O `id` identifica o card para o navegador, o estado salvo e os atalhos;
   * ele é interno e não precisa ser escrito manualmente.
   * Para adicionar um setor inteiro, crie a variável aqui junto das demais estruturas
   * e inclua-a no array "filhos" do pai correto, mais abaixo em "Árvore institucional".
   *
   * Os auxiliares commission/chefia/assessoria/coordenadoria/gerencia/diretoria
   * são atalhos para criar tipos recorrentes com menos repetição; use node()
   * diretamente quando o tipo não tiver um auxiliar próprio.
   *
   * Cor e apresentação do card vêm de dois campos (o tipo NÃO é mais exibido):
   *   dimensao: 'legislativa' | 'administrativa' (padrão: administrativa; use { ...LEG });
   *   macro:    true para macrounidades (Presidência/Gabinete, diretorias, Procuradoria,
   *             Controladoria); diretoria() já marca macro: true.
   *
   * IDs são gerados automaticamente por node() em cada carregamento; não os edite.
   * O campo `tipo` é interno (não aparece na tela nem define cor); se informado,
   * precisa existir em ROTULOS_TIPO (js/organograma-core.js).
   */
  const node = (nome, tipo, filhos = [], metadata = {}) => ({
    id: `cmg-${++nextNodeId}`,
    nome,
    sigla: SIGLAS_OFICIAIS[nome],
    tipo,
    cargo: tipo,
    // Dimensão do card (define a cor): 'administrativa' (padrão) ou 'legislativa'.
    dimensao: 'administrativa',
    // Macrounidade (apresentação de destaque): Presidência/Gabinete, diretorias,
    // Procuradoria e Controladoria. Padrão: não é.
    macro: false,
    filhos,
    ...metadata
  });

  // Atalho das entidades legislativas: Plenário, Mesa Diretora, comissões,
  // vice-presidências e secretarias, ouvidorias e Conselho de Ética.
  const LEG = { dimensao: 'legislativa' };

  const commission = (nome, sigla) => node(nome, 'comissao', [], { sigla, ...LEG });
  const chefia = (nome, filhos = []) => node(nome, 'chefia', filhos);
  const assessoria = (nome, filhos = []) => node(nome, 'assessoria', filhos);
  const coordenadoria = (nome, filhos = []) => node(nome, 'coordenadoria', filhos);
  const gerencia = (nome, filhos = []) => node(nome, 'gerencia', filhos);
  // Toda diretoria é macrounidade; para exceção, passe { macro: false } no 3º argumento.
  const diretoria = (nome, filhos = [], metadata = {}) => node(nome, 'diretoria', filhos, { macro: true, ...metadata });

  // Hierarquia do organograma oficial: as unidades de apoio da Chefia de Gabinete
  // ficam sob ela; Procuradoria e Controladoria ficam no nível do Gabinete.
  const gabinetePresidencia = node('Gabinete da Presidência', 'gabinete', [
    assessoria('Assessoria de Articulação Política da Região Metropolitana', [
      assessoria('Assessoria de Apoio à Articulação Política da Região Metropolitana')
    ]),
    assessoria('Assessoria Executiva de Assuntos Institucionais', [
      coordenadoria('Coordenadoria da Liderança de Governo', [
        assessoria('Assessoria de Apoio à Liderança de Governo')
      ])
    ]),
    assessoria('Assessoria Executiva de Imprensa da Presidência', [
      assessoria('Assessoria de Imprensa da Presidência')
    ]),
    diretoria('Controladoria Geral', [
      chefia('Chefia do Núcleo de Apoio ao Controle Interno'),
      gerencia('Gerência de Pareceres Técnicos'),
      coordenadoria('Coordenadoria de Auditoria e Exame de Contas', [
        chefia('Chefia do Núcleo de Controle Interno e Auditoria')
      ]),
      coordenadoria('Coordenadoria de Análise de Despesa de Pessoal e Contábil', [
        gerencia('Gerência de Folha de Pagamento e Gestão de Pessoal'),
        gerencia('Gerência de Análise de Pagamentos')
      ])
    ]),
    chefia('Chefia de Gabinete', [
      gerencia('Gerência de Expediente da Presidência'),
      gerencia('Gerência de Governança'),
      gerencia('Gerência de Apoio Administrativo'),
      assessoria('Assessoria Jurídica da Presidência', [
        gerencia('Gerência Jurídica da Presidência')
      ]),
      assessoria('Assessoria Especial da Presidência I'),
      assessoria('Assessoria Especial da Presidência II')
    ]),
    diretoria('Procuradoria Geral', [
      gerencia('Gerência de Apoio à Procuradoria'),
      node('Secretaria Geral da Procuradoria', 'unidade'),
      diretoria('Subprocuradoria-Geral', [
        chefia('Chefia do Núcleo de Assuntos Administrativos'),
        chefia('Chefia do Núcleo de Assuntos Extrajudiciais e Judiciais'),
        chefia('Chefia do Núcleo de Assuntos Legislativos')
      ], { macro: false })
    ])
  ], { macro: true });

  // Diretorias funcionais e suas unidades subordinadas.
  const diretoriaFinanceira = diretoria('Diretoria Financeira', [
    coordenadoria('Coordenadoria de Gestão Financeira', [
      gerencia('Gerência da Tesouraria'),
      gerencia('Gerência de Contabilidade'),
      chefia('Chefia do Núcleo de Gestão das Obrigações Acessórias')
    ]),
    coordenadoria('Coordenadoria de Planejamento Orçamentário e Financeiro', [
      gerencia('Gerência de Gestão Orçamentária')
    ])
  ]);

  const diretoriaLegislativa = diretoria('Diretoria Legislativa', [
    chefia('Chefia do Núcleo de Apoio Parlamentar'),
    coordenadoria('Coordenadoria de Expediente e Protocolo', [
      gerencia('Gerência de Expediente e Registro', [
        chefia('Chefia do Núcleo de Protocolo')
      ])
    ]),
    coordenadoria('Coordenadoria Legislativa de Plenário', [
      gerencia('Gerência de Apoio Legislativo'),
      gerencia('Gerência de Documentação'),
      gerencia('Gerência de Processamento e Controle'),
      gerencia('Gerência de Taquigrafia', [
        chefia('Chefia do Núcleo de Taquigrafia e Gravação')
      ]),
      gerencia('Gerência de Redação de Atas'),
      node('Núcleo de Serviços Especiais da Taquigrafia', 'unidade'),
      node('Núcleo de Serviços Especiais do Plenário', 'unidade'),
      node('Núcleo de Serviços Especiais da Revisão da Taquigrafia', 'unidade'),
      assessoria('Assessoria de Promoção à Participação Comunitária e Popular')
    ]),
    diretoria('Diretoria Executiva Parlamentar', [
      coordenadoria('Coordenadoria Executiva Parlamentar', [
        assessoria('Assessoria de Execução e Fiscalização de Emendas Individuais')
      ])
    ])
  ]);

  // Estrutura administrativa geral da Câmara Municipal.
  const diretoriaGeral = diretoria('Diretoria Geral', [
    chefia('Chefia do Núcleo de Assistência Administrativa'),
    coordenadoria('Coordenadoria de Contratos', [
      assessoria('Assessoria de Gestão de Contratos'),
      gerencia('Gerência de Contratos', [
        chefia('Chefia do Núcleo de Assistência à Gerência de Contratos')
      ])
    ]),
    coordenadoria('Coordenação de Manutenção e Serviços Gerais'),
    diretoria('Diretoria de Administração', [
      coordenadoria('Coordenadoria de Engenharia', [
        chefia('Chefia do Núcleo de Apoio à Engenharia')
      ]),
      coordenadoria('Coordenadoria de Contrato de Estágio e Jovem Aprendiz', [
        chefia('Chefia do Núcleo de Estágio')
      ]),
      coordenadoria('Coordenadoria de Controle da CEAP', [
        gerencia('Gerência de Controle da CEAP'),
        assessoria('Assessoria de Controle da CEAP')
      ])
    ]),
    diretoria('Diretoria de Compras e Licitações', [
      node('Agente de Contratação', 'cargo'),
      coordenadoria('Coordenadoria de Compras', [
        gerencia('Gerência de Cotação de Preços')
      ])
    ]),
    diretoria('Diretoria de Comunicação', [
      coordenadoria('Coordenadoria de Imprensa e Comunicação', [
        assessoria('Assessoria de Comunicação'),
        assessoria('Assessoria de Imprensa Interna'),
        assessoria('Assessoria de Mídias Digitais'),
        assessoria('Assessoria de Relações Públicas'),
        assessoria('Assessoria de Radialismo e Televisão'),
        assessoria('Assessor de Website')
      ]),
      coordenadoria('Coordenadoria da TV Câmara', [
        gerencia('Gerência de Gravação e Som', [
          chefia('Chefia do Núcleo de Gravação e Som'),
          chefia('Chefia do Núcleo de Áudio e Vídeo')
        ]),
        gerencia('Gerência de Fotojornalismo')
      ]),
      coordenadoria('Coordenadoria de Áudio e Projeção', [
        chefia('Chefia do Núcleo de Áudio e Projeção')
      ])
    ]),
    diretoria('Diretoria de Recursos Humanos', [
      coordenadoria('Coordenadoria de Pessoal', [
        chefia('Chefia do Núcleo de Processos Administrativos'),
        gerencia('Gerência de Arquivo e Documentação')
      ]),
      coordenadoria('Coordenadoria de Folha de Pagamento', [
        gerencia('Gerência de Processamento da Folha', [
          chefia('Chefia do Núcleo de Cálculo da Folha')
        ])
      ])
    ]),
    diretoria('Diretoria do SESMT', [
      coordenadoria('Coordenadoria do SESMT'),
      assessoria('Assessoria de Apoio ao SESMT', [
        gerencia('Gerência Especializada em Segurança e Medicina do Trabalho')
      ])
    ]),
    diretoria('Diretoria de Transporte e Abastecimento', [
      coordenadoria('Coordenadoria de Transporte', [
        chefia('Chefia do Núcleo de Abastecimento')
      ])
    ]),
    diretoria('Diretoria de Tecnologia da Informação', [
      coordenadoria('Coordenadoria de Informática', [
        gerencia('Gerência de Hardware'),
        gerencia('Gerência de Suporte de Informática'),
        gerencia('Gerência de Software')
      ])
    ]),
    diretoria('Diretoria de Segurança e Inteligência', [
      node('Serviço de Segurança da Presidência', 'unidade'),
      assessoria('Assessoria de Apoio de Segurança'),
      coordenadoria('Coordenação de Segurança e Inteligência')
    ]),
    diretoria('Diretoria Executiva do Cerimonial', [
      assessoria('Assessoria de Apoio ao Cerimonial'),
      node('Núcleo de Serviços Especiais do Cerimonial', 'unidade')
    ]),
    diretoria('Diretoria de Integração Social e Cidadania', [
      coordenadoria('Coordenação de Integração Social e Cidadania', [
        assessoria('Assessoria de Apoio à Integração Social e Cidadania')
      ])
    ]),
    diretoria('Diretoria de Patrimônio e Almoxarifado', [
      coordenadoria('Coordenadoria de Patrimônio'),
      assessoria('Assessoria de Apoio ao Patrimônio'),
      gerencia('Gerência de Patrimônio', [
        chefia('Chefia do Núcleo de Patrimônio')
      ]),
      coordenadoria('Coordenadoria de Almoxarifado'),
      assessoria('Assessoria de Apoio ao Almoxarifado', [
        gerencia('Gerência de Almoxarifado', [
          chefia('Chefia do Núcleo de Almoxarifado')
        ])
      ])
    ]),
    diretoria('Diretoria de Promoção de Atividades de Cultura e Ensino', [
      coordenadoria('Coordenadoria do Parlamento Jovem', [
        assessoria('Assessoria do Parlamento Jovem'),
        chefia('Chefia do Núcleo de Apoio ao Parlamento Jovem')
      ]),
      coordenadoria('Coordenadoria da Escola do Legislativo', [
        chefia('Chefia do Núcleo de Coordenação da Escola do Legislativo', [
          assessoria('Assessoria Administrativa da Escola do Legislativo', [
            assessoria('Assessoria Acadêmica da Escola do Legislativo')
          ])
        ])
      ]),
      coordenadoria('Coordenadoria de Atividades Culturais e Comunitárias', [
        assessoria('Assessoria de Apoio às Atividades Culturais e Comunitárias', [
          chefia('Chefia do Núcleo de Apoio às Atividades Culturais e Comunitárias')
        ])
      ])
    ]),
    diretoria('Diretoria das Ouvidorias', [
      coordenadoria('Coordenadoria do Canal Cidadania', [
        assessoria('Assessoria de Apoio ao Canal Cidadania', [
          chefia('Chefia do Núcleo de Apoio ao Canal Cidadania')
        ])
      ]),
      coordenadoria('Coordenadoria da Ouvidoria da Mulher', [
        assessoria('Assessoria de Apoio da Ouvidoria da Mulher', [
          chefia('Chefia do Núcleo de Apoio à Ouvidoria da Mulher')
        ])
      ]),
      coordenadoria('Coordenadoria da Ouvidoria Especial de Combate a Crimes Raciais', [
        assessoria('Assessoria de Apoio da Ouvidoria Especial de Combate a Crimes Raciais', [
          chefia('Chefia do Núcleo de Apoio da Ouvidoria Especial de Combate a Crimes Raciais')
        ])
      ])
    ]),
    diretoria('Diretoria de Transparência e Proteção de Dados', [
      coordenadoria('Coordenadoria do Portal da Transparência', [
        assessoria('Assessoria de Apoio ao Portal da Transparência')
      ]),
      node('Encarregado pelo Tratamento de Dados Pessoais', 'cargo')
    ])
  ]);

  const gabinetesParlamentares = node('Gabinetes Parlamentares', 'unidade');

  // Comissões e ouvidorias especiais seguem a hierarquia publicada pela Câmara.
  const comissoesLegislativas = node('Comissões Legislativas', 'comissao', [
    commission('Comissão de Cultura', 'CC'),
    commission('Comissão de Constituição, Justiça e Redação', 'CCJR'),
    commission('Comissão de Direitos do Consumidor', 'CDC'),
    commission('Comissão de Direitos da Criança e Adolescente', 'CDCA'),
    commission('Comissão da Defesa e dos Direitos da Mulher', 'CDDM'),
    commission('Comissão de Direitos Humanos e Cidadania', 'CDHC'),
    commission('Comissão de Direitos dos Idosos', 'CDI'),
    commission('Comissão de Educação, Ciência e Tecnologia', 'CECT'),
    commission('Comissão de Empreendedorismo, Cooperativismo, Desenvolvimento Econômico e Social', 'CEDES'),
    commission('Conselho de Ética e Decoro Parlamentar', 'CEDP'),
    commission('Comissão de Finanças, Orçamento e Economia', 'CFOE'),
    commission('Comissão de Fiscalização do Transporte Público Coletivo', 'CFTPC'),
    commission('Comissão de Habitação, Urbanismo e Ordenamento Urbano', 'CHUOU'),
    commission('Comissão de Lazer, Esporte e Turismo', 'CLET'),
    commission('Comissão de Legislação Participativa', 'CLP'),
    commission('Comissão Mista', 'CM'),
    commission('Comissão do Meio Ambiente', 'CMA'),
    commission('Comissão de Obras e Patrimônio', 'COP'),
    commission('Comissão de Proteção, Direitos e Defesa dos Animais', 'CPDDA'),
    commission('Comissão das Pessoas Portadoras de Deficiência e/ou Necessidades Especiais', 'CPPDNE'),
    commission('Comissão de Saúde e Assistência Social', 'CSAS'),
    commission('Comissão de Segurança Pública e Patrimonial', 'CSPP'),
    commission('Comissão do Trabalho e Servidores Públicos', 'CTSP'),
    node('Ouvidoria Especial de Combate a Crimes Raciais', 'ouvidoria', [], { ...LEG }),
    node('Ouvidoria Especial da Mulher', 'ouvidoria', [], { ...LEG })
  ], LEG);

  const vicePresidenciasSecretarias = node('Vice-presidências e secretarias', 'unidade', [
    ...[1, 2, 3, 4].map((numero) => node(`${numero}ª Vice-Presidência`, 'cargo', [], LEG)),
    ...[1, 2, 3, 4, 5].map((numero) => node(`${numero}ª Secretaria`, 'cargo', [], LEG)),
    ...[1, 2].map((numero) => node(`${numero}ª Vice-Presidência Corregedoria`, 'cargo', [], LEG))
  ], LEG);

  // A Mesa tem cinco ramos diretos, como no organograma interativo oficial.
  const mesaDiretora = node('Mesa Diretora', 'orgao', [
    diretoriaFinanceira,
    diretoriaGeral,
    diretoriaLegislativa,
    gabinetePresidencia,
    vicePresidenciasSecretarias
  ], LEG);

  // Ponto de entrada e três ramos do organograma oficial.
  const dados = node('Plenário', 'instituicao', [
    comissoesLegislativas,
    gabinetesParlamentares,
    mesaDiretora
  ], { sigla: 'CMG', ...LEG });

  window.organogramaDados = dados;
})();
