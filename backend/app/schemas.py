from typing import Optional, Generic, TypeVar, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# ==================== DEPUTADOS ====================

class DeputadoSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: int
    nome_parlamentar: str
    nome_civil: Optional[str] = None
    sigla_partido: Optional[str] = None
    uf: Optional[str] = None
    url_foto: Optional[str] = None
    situacao: Optional[str] = None
    legislatura: Optional[int] = None
    email: Optional[str] = None
    total_votos: int = 0
    total_eventos: int = 0
    total_proposicoes: int = 0

class DeputadoGabinete(BaseModel):
    predio: Optional[str] = None
    sala: Optional[str] = None
    andar: Optional[str] = None
    telefone: Optional[str] = None

class DeputadoDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: int
    nome_parlamentar: str
    nome_civil: Optional[str] = None
    sigla_partido: Optional[str] = None
    uf: Optional[str] = None
    url_foto: Optional[str] = None
    situacao: Optional[str] = None
    condicao_eleitoral: Optional[str] = None
    descricao_status: Optional[str] = None
    email: Optional[str] = None
    legislatura: Optional[int] = None
    gabinete: DeputadoGabinete
    data_nascimento: Optional[str] = None
    municipio_nascimento: Optional[str] = None
    uf_nascimento: Optional[str] = None
    escolaridade: Optional[str] = None
    rede_social: Optional[list[str]] = None
    url_website: Optional[str] = None
    uri: Optional[str] = None
    updated_at: Optional[datetime] = None

class DeputadoAtividade(BaseModel):
    votos_registrados: int
    votacoes_distintas: int
    dias_com_atividade: int
    presencas_eventos: int
    proposicoes_autoria: int
    nota_metodologica: str = (
        "Este indicador considera atividades registradas nas bases públicas da Câmara, como "
        "votações e participação em eventos. Ele não representa a totalidade da atividade "
        "profissional do parlamentar."
    )

class FonteIndicador(BaseModel):
    status: str
    fonte: str
    consultado_em: Optional[datetime] = None
    expira_em: Optional[datetime] = None


class DeputadoIndicadores(BaseModel):
    ano_referencia: int
    mes_referencia: int
    presencas_plenario: Optional[int] = None
    faltas_plenario: Optional[int] = None
    faltas_justificadas: Optional[int] = None
    faltas_nao_justificadas: Optional[int] = None
    percentual_presenca: Optional[float] = None
    pls_apresentados: int = 0
    pls_aprovados: int = 0
    percentual_pls_aprovados: float = 0.0
    uso_cota_mes: Optional[float] = None
    votacoes_nominais: int = 0
    fontes: dict[str, FonteIndicador] = {}

class AtividadeTemporalItem(BaseModel):
    periodo: str  # "2024-01" or "2024"
    votos: int
    eventos: int
    proposicoes: int

class DistribuicaoVotosItem(BaseModel):
    tipo_voto: str
    quantidade: int
    percentual: float

class DeputadoHistoricoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_hora: Optional[str] = None
    sigla_partido: Optional[str] = None
    situacao: Optional[str] = None
    condicao_eleitoral: Optional[str] = None
    descricao_status: Optional[str] = None
    legislatura: Optional[int] = None

class DeputadoVotoItem(BaseModel):
    id: int
    votacao_id: int
    votacao_camara_id: str
    data_hora: Optional[str] = None
    descricao_votacao: str
    tipo_voto: str
    sigla_partido_momento: Optional[str] = None
    uf_momento: Optional[str] = None
    proposicao_id: Optional[int] = None
    proposicao_sigla: Optional[str] = None
    proposicao_numero: Optional[int] = None
    proposicao_ano: Optional[int] = None
    proposicao_ementa: Optional[str] = None


# ==================== COMPARATIVO DE DEPUTADOS ====================

class ComparativoParlamentar(BaseModel):
    id: int
    nome_parlamentar: str
    sigla_partido: Optional[str] = None
    uf: Optional[str] = None
    url_foto: Optional[str] = None
    dados_demonstrativos: bool = False

class ComparativoAtividade(BaseModel):
    votos_registrados: int
    votacoes_distintas: int
    dias_com_atividade: int
    presencas_eventos: int
    proposicoes_autoria: int

class ComparativoVotos(BaseModel):
    sim: int = 0
    nao: int = 0
    abstencao: int = 0
    obstrucao: int = 0
    outros: int = 0

class ComparativoTema(BaseModel):
    id: int
    nome: str
    sim: int = 0
    nao: int = 0
    abstencao: int = 0
    obstrucao: int = 0
    outros: int = 0
    total_registrado: int = 0
    total_sim_nao: int = 0
    percentual_sim: Optional[float] = None
    percentual_nao: Optional[float] = None

class ComparativoDeputado(BaseModel):
    deputado: ComparativoParlamentar
    atividade: ComparativoAtividade
    votos: ComparativoVotos
    temas: list[ComparativoTema] = []

class ComparativoResponse(BaseModel):
    ano: int
    legislatura: Optional[int] = None
    ultima_sincronizacao: Optional[datetime] = None
    deputados: list[ComparativoDeputado]
    nota_metodologica: str

class VotacaoComparada(BaseModel):
    id: int
    camara_id: str
    data_hora: Optional[str] = None
    descricao: str
    uri: Optional[str] = None
    proposicao_id: Optional[int] = None
    proposicao_nome: Optional[str] = None
    votos: dict[str, str]

# ==================== PROPOSICOES ====================

class ProposicaoSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: int
    sigla_tipo: str
    numero: int
    ano: int
    ementa: Optional[str] = None
    data_apresentacao: Optional[str] = None
    situacao: Optional[str] = None
    descricao_situacao: Optional[str] = None
    orgao_atual: Optional[str] = None
    temas: list[str] = []
    autor_principal: Optional[str] = None
    autor_principal_deputado_id: Optional[int] = None

class AutorItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_autor: str
    tipo_autor: Optional[str] = None
    ordem_autoria: int
    proponente: bool
    deputado_id: Optional[int] = None
    sigla_partido: Optional[str] = None
    uf: Optional[str] = None
    url_foto: Optional[str] = None

class TramitacaoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_hora: Optional[str] = None
    sequencia: int
    descricao_tramitacao: Optional[str] = None
    despacho: Optional[str] = None
    orgao: Optional[str] = None
    situacao: Optional[str] = None
    regime: Optional[str] = None
    url_documento: Optional[str] = None

class VotacaoResumoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: str
    data_hora_registro: Optional[str] = None
    descricao: str
    resultado: Optional[str] = None
    aprovada: Optional[bool] = None
    orgao: Optional[str] = None
    placar_sim: int = 0
    placar_nao: int = 0
    placar_abstencao: int = 0
    placar_obstrucao: int = 0
    tipo_relacao: str = "Votação relacionada à proposição"

class ProposicaoDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: int
    sigla_tipo: str
    numero: int
    ano: int
    ementa: Optional[str] = None
    ementa_detalhada: Optional[str] = None
    data_apresentacao: Optional[str] = None
    situacao: Optional[str] = None
    descricao_situacao: Optional[str] = None
    regime: Optional[str] = None
    despacho: Optional[str] = None
    orgao_atual: Optional[str] = None
    url_inteiro_teor: Optional[str] = None
    uri: Optional[str] = None
    updated_at: Optional[datetime] = None
    temas: list[str] = []
    autores: list[AutorItem] = []
    tramitacoes: list[TramitacaoItem] = []
    votacoes: list[VotacaoResumoItem] = []

# ==================== VOTACOES ====================

class OrientacaoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bancada: str
    orientacao_voto: str

class VotoDeputadoItem(BaseModel):
    id: int
    deputado_id: int
    camara_id: int
    nome_parlamentar: str
    sigla_partido: Optional[str] = None
    sigla_partido_momento: Optional[str] = None
    sigla_partido_atual: Optional[str] = None
    uf: Optional[str] = None
    uf_momento: Optional[str] = None
    url_foto: Optional[str] = None
    tipo_voto: str
    data_hora: Optional[str] = None

class VotacaoDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: str
    data_hora_registro: Optional[str] = None
    descricao: str
    resultado: Optional[str] = None
    aprovada: Optional[bool] = None
    orgao: Optional[str] = None
    placar_sim: int = 0
    placar_nao: int = 0
    placar_abstencao: int = 0
    placar_obstrucao: int = 0
    uri: Optional[str] = None
    orientacoes: list[OrientacaoItem] = []
    proposicoes: list[ProposicaoSimple] = []
    total_votos: int = 0

# ==================== STATS & SEARCH ====================

class StatsResponse(BaseModel):
    total_deputados: int
    total_proposicoes: int
    total_votacoes: int
    total_votos: int
    ultima_sincronizacao: Optional[str] = None
    votacoes_recentes: list[VotacaoResumoItem]
    proposicoes_recentes: list[ProposicaoSimple]

class GlobalSearchResult(BaseModel):
    query: str
    deputados: list[DeputadoSimple]
    proposicoes: list[ProposicaoSimple]
    votacoes: list[VotacaoResumoItem]

class SyncStatusResponse(BaseModel):
    id: Optional[int] = None
    tipo: Optional[str] = None
    iniciado_em: Optional[datetime] = None
    finalizado_em: Optional[datetime] = None
    status: str
    registros_processados: int
    erro: Optional[str] = None


# ==================== EVOLUÇÃO: HISTÓRICO DE DEPUTADOS ====================

class MandatoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    legislatura_numero: Optional[int] = None
    cargo: str = "Deputado Federal"
    sigla_partido: Optional[str] = None
    uf: Optional[str] = None
    situacao: Optional[str] = None
    condicao_eleitoral: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None

class FiliacaoPartidariaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sigla_partido: str
    nome_partido: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    fonte: Optional[str] = None

class TrajetoriaMilestone(BaseModel):
    tipo: str  # "MANDATO", "FILIACAO", "HISTORICO"
    titulo: str
    subtitulo: Optional[str] = None
    data: Optional[str] = None
    ano: Optional[int] = None
    legislatura: Optional[int] = None
    partido: Optional[str] = None
    uf: Optional[str] = None
    detalhes: Optional[str] = None

class DeputadoTrajetoriaResponse(BaseModel):
    deputado_id: int
    nome_parlamentar: str
    sigla_partido_atual: Optional[str] = None
    uf_atual: Optional[str] = None
    mandatos: list[MandatoItem] = []
    filiacoes: list[FiliacaoPartidariaItem] = []
    timeline: list[TrajetoriaMilestone] = []

class LegislaturaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camara_id: int
    numero: int
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    ano_inicio: Optional[int] = None
    ano_fim: Optional[int] = None


# ==================== EVOLUÇÃO: ENTENDA O GOVERNO ====================

class InstituicaoSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    sigla: Optional[str] = None
    tipo: str
    poder: str
    esfera: str
    nivel_federativo: str
    codigo_externo: Optional[str] = None
    natureza_juridica: Optional[str] = None
    site_oficial: Optional[str] = None
    ativo: bool = True

class RelacaoInstitucionalItem(BaseModel):
    id: int
    origem_id: int
    origem_nome: str
    origem_sigla: Optional[str] = None
    origem_tipo: str
    destino_id: int
    destino_nome: str
    destino_sigla: Optional[str] = None
    destino_tipo: str
    tipo_relacao: str  # HIERARQUIA_ADMINISTRATIVA, VINCULACAO, COMPOSICAO, CONTROLE, FISCALIZACAO
    descricao: Optional[str] = None
    fonte: Optional[str] = None

class InstituicaoDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    sigla: Optional[str] = None
    tipo: str
    poder: str
    esfera: str
    nivel_federativo: str
    codigo_externo: Optional[str] = None
    natureza_juridica: Optional[str] = None
    descricao: Optional[str] = None
    site_oficial: Optional[str] = None
    fonte: str
    url_fonte: Optional[str] = None
    ativo: bool
    superiores: list[InstituicaoSimple] = []
    subordinados: list[InstituicaoSimple] = []
    vinculados: list[InstituicaoSimple] = []
    relacoes: list[RelacaoInstitucionalItem] = []
    integrado: bool = False
    estatisticas_camara: Optional[dict[str, Any]] = None

class EstruturaGovernoNode(BaseModel):
    id: int
    nome: str
    sigla: Optional[str] = None
    tipo: str
    poder: str
    esfera: str
    nivel_federativo: str
    codigo_externo: Optional[str] = None
    descricao: Optional[str] = None
    site_oficial: Optional[str] = None
    integrado: bool = False
    parentId: Optional[int] = None
    natureza_juridica: Optional[str] = None

class EstruturaGovernoEdge(BaseModel):
    id: str
    source: int
    target: int
    tipo_relacao: str  # HIERARQUIA_ADMINISTRATIVA, VINCULACAO, COMPOSICAO, CONTROLE, FISCALIZACAO
    descricao: Optional[str] = None

class EstruturaGovernoGraph(BaseModel):
    nodes: list[EstruturaGovernoNode]
    edges: list[EstruturaGovernoEdge]
    legenda: dict[str, str] = {
        "HIERARQUIA_ADMINISTRATIVA": "Linha contínua: Subordinação hierárquica e administrativa direta",
        "VINCULACAO": "Linha tracejada: Vinculação administrativa / supervisão ministerial (DL 200/1967)",
        "COMPOSICAO": "Linha sólida de estrutura: Ente componente ou câmara de poder",
        "CONTROLE": "Linha pontilhada: Controle externo ou fiscalização de legalidade e contas",
        "FISCALIZACAO": "Linha pontilhada: Fiscalização constitucional"
    }

