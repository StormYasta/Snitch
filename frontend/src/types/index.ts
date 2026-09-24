export interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DeputadoSimple {
  id: number;
  camara_id: number;
  nome_parlamentar: string;
  nome_civil?: string;
  sigla_partido?: string;
  uf?: string;
  url_foto?: string;
  situacao?: string;
  legislatura?: number;
  email?: string;
  total_votos: number;
  total_eventos: number;
  total_proposicoes: number;
}

export interface DeputadoGabinete {
  predio?: string;
  sala?: string;
  andar?: string;
  telefone?: string;
}

export interface DeputadoDetail {
  id: number;
  camara_id: number;
  nome_parlamentar: string;
  nome_civil?: string;
  sigla_partido?: string;
  uf?: string;
  url_foto?: string;
  situacao?: string;
  condicao_eleitoral?: string;
  descricao_status?: string;
  email?: string;
  legislatura?: number;
  gabinete: DeputadoGabinete;
  data_nascimento?: string;
  municipio_nascimento?: string;
  uf_nascimento?: string;
  escolaridade?: string;
  rede_social?: string[];
  url_website?: string;
  uri?: string;
  updated_at?: string;
}

export interface DeputadoAtividade {
  votos_registrados: number;
  votacoes_distintas: number;
  dias_com_atividade: number;
  presencas_eventos: number;
  proposicoes_autoria: number;
  nota_metodologica: string;
}

export interface DeputadoIndicadores {
  ano_referencia: number;
  mes_referencia: number;
  presencas_plenario?: number | null;
  faltas_plenario?: number | null;
  faltas_justificadas?: number | null;
  faltas_nao_justificadas?: number | null;
  percentual_presenca?: number | null;
  pls_apresentados: number;
  pls_aprovados: number;
  percentual_pls_aprovados: number;
  uso_cota_mes?: number | null;
  votacoes_nominais: number;
}

export interface AtividadeTemporalItem {
  periodo: string;
  votos: number;
  eventos: number;
  proposicoes: number;
}

export interface DistribuicaoVotosItem {
  tipo_voto: string;
  quantidade: number;
  percentual: number;
}

export interface DeputadoVotoItem {
  id: number;
  votacao_id: number;
  votacao_camara_id: string;
  data_hora?: string;
  descricao_votacao: string;
  tipo_voto: string;
  sigla_partido_momento?: string;
  uf_momento?: string;
  proposicao_id?: number;
  proposicao_sigla?: string;
  proposicao_numero?: number;
  proposicao_ano?: number;
  proposicao_ementa?: string;
}

export interface DeputadoHistoricoItem {
  id: number;
  data_hora?: string;
  sigla_partido?: string;
  situacao?: string;
  condicao_eleitoral?: string;
  descricao_status?: string;
  legislatura?: number;
}

export interface ProposicaoSimple {
  id: number;
  camara_id: number;
  sigla_tipo: string;
  numero: number;
  ano: number;
  ementa?: string;
  data_apresentacao?: string;
  situacao?: string;
  descricao_situacao?: string;
  orgao_atual?: string;
  temas: string[];
  autor_principal?: string;
  autor_principal_deputado_id?: number;
}

export interface AutorItem {
  id: number;
  nome_autor: string;
  tipo_autor?: string;
  ordem_autoria: number;
  proponente: boolean;
  deputado_id?: number;
  sigla_partido?: string;
  uf?: string;
  url_foto?: string;
}

export interface TramitacaoItem {
  id: number;
  data_hora?: string;
  sequencia: number;
  descricao_tramitacao?: string;
  despacho?: string;
  orgao?: string;
  situacao?: string;
  regime?: string;
  url_documento?: string;
}

export interface VotacaoResumoItem {
  id: number;
  camara_id: string;
  data_hora_registro?: string;
  descricao: string;
  resultado?: string;
  aprovada?: boolean;
  orgao?: string;
  placar_sim: number;
  placar_nao: number;
  placar_abstencao: number;
  placar_obstrucao: number;
  tipo_relacao: string;
}

export interface ProposicaoDetail {
  id: number;
  camara_id: number;
  sigla_tipo: string;
  numero: number;
  ano: number;
  ementa?: string;
  ementa_detalhada?: string;
  data_apresentacao?: string;
  situacao?: string;
  descricao_situacao?: string;
  regime?: string;
  despacho?: string;
  orgao_atual?: string;
  url_inteiro_teor?: string;
  uri?: string;
  updated_at?: string;
  temas: string[];
  autores: AutorItem[];
  tramitacoes: TramitacaoItem[];
  votacoes: VotacaoResumoItem[];
}

export interface OrientacaoItem {
  id: number;
  bancada: string;
  orientacao_voto: string;
}

export interface VotoDeputadoItem {
  id: number;
  deputado_id: number;
  camara_id: number;
  nome_parlamentar: string;
  sigla_partido?: string;
  uf?: string;
  url_foto?: string;
  tipo_voto: string;
  data_hora?: string;
}

export interface VotacaoDetail {
  id: number;
  camara_id: string;
  data_hora_registro?: string;
  descricao: string;
  resultado?: string;
  aprovada?: boolean;
  orgao?: string;
  placar_sim: number;
  placar_nao: number;
  placar_abstencao: number;
  placar_obstrucao: number;
  uri?: string;
  orientacoes: OrientacaoItem[];
  proposicoes: ProposicaoSimple[];
  total_votos: number;
}

export interface StatsResponse {
  total_deputados: number;
  total_proposicoes: number;
  total_votacoes: number;
  total_votos: number;
  ultima_sincronizacao?: string;
  votacoes_recentes: VotacaoResumoItem[];
  proposicoes_recentes: ProposicaoSimple[];
}

export interface GlobalSearchResult {
  query: string;
  deputados: DeputadoSimple[];
  proposicoes: ProposicaoSimple[];
  votacoes: VotacaoResumoItem[];
}


export interface MandatoItem {
  id: number;
  legislatura_numero?: number;
  cargo: string;
  sigla_partido?: string;
  uf?: string;
  situacao?: string;
  condicao_eleitoral?: string;
  data_inicio?: string;
  data_fim?: string;
}

export interface FiliacaoPartidariaItem {
  id: number;
  sigla_partido: string;
  nome_partido?: string;
  data_inicio?: string;
  data_fim?: string;
  fonte?: string;
}

export interface TrajetoriaMilestone {
  tipo: string;
  titulo: string;
  subtitulo?: string;
  data?: string;
  ano?: number;
  legislatura?: number;
  partido?: string;
  uf?: string;
  detalhes?: string;
}

export interface DeputadoTrajetoria {
  deputado_id: number;
  nome_parlamentar: string;
  sigla_partido_atual?: string;
  uf_atual?: string;
  mandatos: MandatoItem[];
  filiacoes: FiliacaoPartidariaItem[];
  timeline: TrajetoriaMilestone[];
}

export interface LegislaturaItem {
  id: number;
  camara_id: number;
  numero: number;
  data_inicio?: string;
  data_fim?: string;
  ano_inicio?: number;
  ano_fim?: number;
}

export interface InstituicaoSimple {
  id: number;
  nome: string;
  sigla?: string;
  tipo: string;
  poder: string;
  esfera: string;
  nivel_federativo: string;
  codigo_externo?: string;
  natureza_juridica?: string;
  site_oficial?: string;
  ativo: boolean;
}

export interface RelacaoInstitucionalItem {
  id: number;
  origem_id: number;
  origem_nome: string;
  origem_sigla?: string;
  origem_tipo: string;
  destino_id: number;
  destino_nome: string;
  destino_sigla?: string;
  destino_tipo: string;
  tipo_relacao: string;
  descricao?: string;
  fonte?: string;
}

export interface InstituicaoDetail extends InstituicaoSimple {
  descricao?: string;
  fonte: string;
  url_fonte?: string;
  superiores: InstituicaoSimple[];
  subordinados: InstituicaoSimple[];
  vinculados: InstituicaoSimple[];
  relacoes: RelacaoInstitucionalItem[];
  integrado: boolean;
  estatisticas_camara?: {
    total_deputados: number;
    total_proposicoes: number;
    total_votacoes: number;
    total_legislaturas: number;
    links: Array<{ label: string; url: string }>;
  };
}

export interface EstruturaGovernoNode extends InstituicaoSimple {
  descricao?: string;
  integrado: boolean;
  parentId?: number;
}

export interface EstruturaGovernoEdge {
  id: string;
  source: number;
  target: number;
  tipo_relacao: string;
  descricao?: string;
}

export interface EstruturaGovernoGraph {
  nodes: EstruturaGovernoNode[];
  edges: EstruturaGovernoEdge[];
  legenda: Record<string, string>;
}
