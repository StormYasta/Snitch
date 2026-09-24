import axios from 'axios';
import type {
  PageResponse,
  DeputadoSimple,
  DeputadoDetail,
  DeputadoAtividade,
  DeputadoIndicadores,
  AtividadeTemporalItem,
  DistribuicaoVotosItem,
  DeputadoVotoItem,
  DeputadoHistoricoItem,
  ProposicaoSimple,
  ProposicaoDetail,
  TramitacaoItem,
  VotacaoResumoItem,
  VotacaoDetail,
  VotoDeputadoItem,
  StatsResponse,
  GlobalSearchResult,
  DeputadoTrajetoria,
  LegislaturaItem,
  InstituicaoSimple,
  InstituicaoDetail,
  EstruturaGovernoGraph
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// Stats & Search
export async function getStats(): Promise<StatsResponse> {
  const { data } = await api.get<StatsResponse>('/stats');
  return data;
}

export async function searchGlobal(q: string): Promise<GlobalSearchResult> {
  const { data } = await api.get<GlobalSearchResult>('/busca', { params: { q } });
  return data;
}

// Deputados
export async function getDeputados(params: {
  busca?: string;
  partido?: string;
  uf?: string;
  situacao?: string;
  legislatura?: number;
  ordenar_por?: string;
  ordem?: string;
  page?: number;
  page_size?: number;
}): Promise<PageResponse<DeputadoSimple>> {
  const { data } = await api.get<PageResponse<DeputadoSimple>>('/deputados', { params });
  return data;
}

export async function getDeputado(id: number): Promise<DeputadoDetail> {
  const { data } = await api.get<DeputadoDetail>(`/deputados/${id}`);
  return data;
}

export async function getDeputadoAtividade(id: number): Promise<DeputadoAtividade> {
  const { data } = await api.get<DeputadoAtividade>(`/deputados/${id}/atividade`);
  return data;
}

export async function getDeputadoIndicadores(id: number): Promise<DeputadoIndicadores> {
  const { data } = await api.get<DeputadoIndicadores>(`/deputados/${id}/indicadores`);
  return data;
}

export async function getDeputadoTemporal(
  id: number,
  agrupamento: 'mes' | 'ano' = 'mes',
  legislatura?: number,
  ano?: number
): Promise<AtividadeTemporalItem[]> {
  const { data } = await api.get<AtividadeTemporalItem[]>(`/deputados/${id}/temporal`, {
    params: { agrupamento, legislatura, ano }
  });
  return data;
}

export async function getDeputadoDistribuicao(id: number): Promise<DistribuicaoVotosItem[]> {
  const { data } = await api.get<DistribuicaoVotosItem[]>(`/deputados/${id}/distribuicao_votos`);
  return data;
}

export async function getDeputadoVotos(id: number, params: {
  tipo_voto?: string;
  tipo_proposicao?: string;
  ano?: number;
  page?: number;
  page_size?: number;
}): Promise<PageResponse<DeputadoVotoItem>> {
  const { data } = await api.get<PageResponse<DeputadoVotoItem>>(`/deputados/${id}/votos`, { params });
  return data;
}

export async function getDeputadoProposicoes(id: number, relacao: 'autoria' | 'votacao', page: number = 1): Promise<PageResponse<ProposicaoSimple>> {
  const { data } = await api.get<PageResponse<ProposicaoSimple>>(`/deputados/${id}/proposicoes`, {
    params: { relacao, page, page_size: 10 }
  });
  return data;
}

export async function getDeputadoEventos(id: number): Promise<any[]> {
  const { data } = await api.get<any[]>(`/deputados/${id}/eventos`);
  return data;
}

export async function getDeputadoHistorico(id: number): Promise<DeputadoHistoricoItem[]> {
  const { data } = await api.get<DeputadoHistoricoItem[]>(`/deputados/${id}/historico`);
  return data;
}

export async function getDeputadoTrajetoria(id: number): Promise<DeputadoTrajetoria> {
  const { data } = await api.get<DeputadoTrajetoria>(`/deputados/${id}/trajetoria`);
  return data;
}

export async function getLegislaturas(): Promise<LegislaturaItem[]> {
  const { data } = await api.get<LegislaturaItem[]>('/legislaturas');
  return data;
}

// Proposições
export async function getProposicoes(params: {
  busca?: string;
  tipo?: string;
  ano?: number;
  situacao?: string;
  tema?: string;
  autor?: string;
  page?: number;
  page_size?: number;
}): Promise<PageResponse<ProposicaoSimple>> {
  const { data } = await api.get<PageResponse<ProposicaoSimple>>('/proposicoes', { params });
  return data;
}

export async function getProposicao(id: number): Promise<ProposicaoDetail> {
  const { data } = await api.get<ProposicaoDetail>(`/proposicoes/${id}`);
  return data;
}

export async function getProposicaoTramitacoes(id: number): Promise<TramitacaoItem[]> {
  const { data } = await api.get<TramitacaoItem[]>(`/proposicoes/${id}/tramitacoes`);
  return data;
}

export async function getProposicaoVotacoes(id: number): Promise<VotacaoResumoItem[]> {
  const { data } = await api.get<VotacaoResumoItem[]>(`/proposicoes/${id}/votacoes`);
  return data;
}

// Votações
export async function getVotacao(id: number): Promise<VotacaoDetail> {
  const { data } = await api.get<VotacaoDetail>(`/votacoes/${id}`);
  return data;
}

export async function getVotacaoVotos(id: number, params: {
  voto?: string;
  partido?: string;
  uf?: string;
  busca?: string;
  page?: number;
  page_size?: number;
}): Promise<PageResponse<VotoDeputadoItem>> {
  const { data } = await api.get<PageResponse<VotoDeputadoItem>>(`/votacoes/${id}/votos`, { params });
  return data;
}


// Entenda o Governo
export async function getEstruturaGoverno(): Promise<EstruturaGovernoGraph> {
  const { data } = await api.get<EstruturaGovernoGraph>('/governo/estrutura');
  return data;
}

export async function getInstituicoes(params: {
  esfera?: string;
  poder?: string;
  tipo?: string;
  nivel_federativo?: string;
  busca?: string;
  page?: number;
  page_size?: number;
}): Promise<PageResponse<InstituicaoSimple>> {
  const { data } = await api.get<PageResponse<InstituicaoSimple>>('/governo/instituicoes', { params });
  return data;
}

export async function searchInstituicoes(q: string): Promise<InstituicaoSimple[]> {
  const { data } = await api.get<InstituicaoSimple[]>('/governo/busca', { params: { q } });
  return data;
}

export async function getInstituicao(id: number): Promise<InstituicaoDetail> {
  const { data } = await api.get<InstituicaoDetail>(`/governo/instituicoes/${id}`);
  return data;
}
