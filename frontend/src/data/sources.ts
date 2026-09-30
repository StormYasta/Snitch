export type SourceCategory =
  | 'Dados legislativos'
  | 'Presença parlamentar'
  | 'Estrutura organizacional'
  | 'Base constitucional'
  | 'Referência institucional';

export interface OfficialSource {
  name: string;
  organization: string;
  url: string;
  category: SourceCategory;
  usage: string;
  accessedAt: string;
  endpoint?: string;
}

export const SOURCES_LAST_REVIEW = '24/09/2026';

export const officialSources: OfficialSource[] = [
  {
    name: 'Dados Abertos da Câmara dos Deputados — API v2',
    organization: 'Câmara dos Deputados',
    url: 'https://dadosabertos.camara.leg.br/swagger/api.html',
    endpoint: 'https://dadosabertos.camara.leg.br/api/v2',
    category: 'Dados legislativos',
    usage: 'Deputados, legislaturas, proposições, autores, tramitações, votações, votos, eventos e despesas parlamentares.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'ListarPresencasParlamentar',
    organization: 'Câmara dos Deputados',
    url: 'https://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo/webservices/sessoesreunioes-2/listarpresencasparlamentar',
    endpoint: 'https://www.camara.gov.br/SitCamaraWS/SessoesReunioes.asmx',
    category: 'Presença parlamentar',
    usage: 'Presenças e ausências de parlamentares em sessões do Plenário, dentro do período consultado.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'SIORG — Estruturas Organizacionais do Poder Executivo Federal',
    organization: 'Ministério da Gestão e da Inovação em Serviços Públicos',
    url: 'https://www.gov.br/conecta/catalogo/apis/estrutura-organizacional',
    endpoint: 'https://estruturaorganizacional.dados.gov.br',
    category: 'Estrutura organizacional',
    usage: 'Órgãos, entidades, unidades e relações da estrutura organizacional do Poder Executivo Federal.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Constituição da República Federativa do Brasil de 1988',
    organization: 'Presidência da República — Planalto',
    url: 'https://www4.planalto.gov.br/legislacao/legis-federal/constituicao',
    category: 'Base constitucional',
    usage: 'Referência para a organização político-administrativa, Poderes da União e instituições constitucionais representadas no mapa.',
    accessedAt: '24/09/2026',
  },

  {
    name: 'Portal do Governo Federal',
    organization: 'Governo Federal',
    url: 'https://www.gov.br',
    category: 'Referência institucional',
    usage: 'Referência institucional para a União e o Poder Executivo Federal.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Congresso Nacional',
    organization: 'Congresso Nacional',
    url: 'https://www.congressonacional.leg.br',
    category: 'Referência institucional',
    usage: 'Referência institucional da estrutura do Poder Legislativo da União.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Câmara dos Deputados',
    organization: 'Câmara dos Deputados',
    url: 'https://www.camara.leg.br',
    category: 'Referência institucional',
    usage: 'Referência institucional da Câmara dos Deputados.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Senado Federal',
    organization: 'Senado Federal',
    url: 'https://www.senado.leg.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Senado Federal.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Tribunal de Contas da União',
    organization: 'TCU',
    url: 'https://portal.tcu.gov.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Tribunal de Contas da União.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Ministério Público da União',
    organization: 'MPU',
    url: 'https://www.mpu.mp.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Ministério Público da União.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Ministério Público Federal',
    organization: 'MPF',
    url: 'https://www.mpf.mp.br',
    category: 'Referência institucional',
    usage: 'Referência institucional da Procuradoria-Geral da República e do Ministério Público Federal.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Advocacia-Geral da União',
    organization: 'AGU',
    url: 'https://www.gov.br/agu',
    category: 'Referência institucional',
    usage: 'Referência institucional da Advocacia-Geral da União.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Defensoria Pública da União',
    organization: 'DPU',
    url: 'https://www.dpu.def.br',
    category: 'Referência institucional',
    usage: 'Referência institucional da Defensoria Pública da União.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Supremo Tribunal Federal',
    organization: 'STF',
    url: 'https://portal.stf.jus.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Supremo Tribunal Federal.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Conselho Nacional de Justiça',
    organization: 'CNJ',
    url: 'https://www.cnj.jus.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Conselho Nacional de Justiça.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Superior Tribunal de Justiça',
    organization: 'STJ',
    url: 'https://www.stj.jus.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Superior Tribunal de Justiça.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Conselho da Justiça Federal',
    organization: 'CJF',
    url: 'https://www.cjf.jus.br',
    category: 'Referência institucional',
    usage: 'Referência institucional para a Justiça Federal e seus tribunais regionais.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Tribunal Superior Eleitoral',
    organization: 'TSE',
    url: 'https://www.tse.jus.br',
    category: 'Referência institucional',
    usage: 'Referência institucional da Justiça Eleitoral.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Tribunal Superior do Trabalho',
    organization: 'TST',
    url: 'https://www.tst.jus.br',
    category: 'Referência institucional',
    usage: 'Referência institucional da Justiça do Trabalho.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Casa Civil da Presidência da República',
    organization: 'Casa Civil',
    url: 'https://www.gov.br/casacivil',
    category: 'Referência institucional',
    usage: 'Referência institucional da Casa Civil no mapa do Executivo Federal.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'Governo do Distrito Federal',
    organization: 'GDF',
    url: 'https://www.df.gov.br',
    category: 'Referência institucional',
    usage: 'Referência institucional do Distrito Federal no nível federativo.',
    accessedAt: '24/09/2026',
  },
  {
    name: 'União Nacional dos Legisladores e Legislativos Estaduais',
    organization: 'UNALE',
    url: 'https://www.unale.org.br',
    category: 'Referência institucional',
    usage: 'Referência complementar para o nível legislativo estadual representado no mapa institucional.',
    accessedAt: '24/09/2026',
  },
];
