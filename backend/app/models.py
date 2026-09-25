from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

# ==================== LEGISLATURAS ====================

class Legislatura(Base):
    __tablename__ = "legislaturas"

    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(Integer, unique=True, index=True, nullable=False)
    numero = Column(Integer, unique=True, index=True, nullable=False)
    data_inicio = Column(String(50), nullable=True)
    data_fim = Column(String(50), nullable=True)
    ano_inicio = Column(Integer, nullable=True)
    ano_fim = Column(Integer, nullable=True)

    mandatos = relationship("Mandato", back_populates="legislatura_rel")


# ==================== PESSOAS POLÍTICAS / DEPUTADOS ====================

class Deputado(Base):
    """Representa a entidade de Pessoa Política / Parlamentar.
    Preserva a identidade única da pessoa através de mandatos e legislaturas.
    """
    __tablename__ = "deputados"

    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(Integer, unique=True, index=True, nullable=False)
    nome_parlamentar = Column(String(255), index=True, nullable=False)
    nome_civil = Column(String(255), nullable=True)
    sigla_partido = Column(String(50), index=True, nullable=True)
    uf = Column(String(10), index=True, nullable=True)
    url_foto = Column(String(500), nullable=True)
    situacao = Column(String(100), index=True, nullable=True)
    condicao_eleitoral = Column(String(100), nullable=True)
    descricao_status = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    legislatura = Column(Integer, index=True, nullable=True)
    gabinete_predio = Column(String(50), nullable=True)
    gabinete_sala = Column(String(50), nullable=True)
    gabinete_andar = Column(String(50), nullable=True)
    gabinete_telefone = Column(String(50), nullable=True)
    data_nascimento = Column(String(50), nullable=True)
    municipio_nascimento = Column(String(100), nullable=True)
    uf_nascimento = Column(String(10), nullable=True)
    escolaridade = Column(String(100), nullable=True)
    rede_social = Column(JSON, nullable=True)
    url_website = Column(String(500), nullable=True)
    uri = Column(String(500), nullable=True)
    dados_raw = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    mandatos = relationship("Mandato", back_populates="deputado", cascade="all, delete-orphan", order_by="desc(Mandato.legislatura_numero)")
    filiacoes = relationship("FiliacaoPartidaria", back_populates="deputado", cascade="all, delete-orphan")
    historicos = relationship("DeputadoHistorico", back_populates="deputado", cascade="all, delete-orphan")
    votos = relationship("Voto", back_populates="deputado", cascade="all, delete-orphan")
    autorias = relationship("ProposicaoAutor", back_populates="deputado")
    eventos = relationship("EventoDeputado", back_populates="deputado", cascade="all, delete-orphan")


# Alias conceitual para evolução futura
PessoaPolitica = Deputado


class Mandato(Base):
    """Representa um mandato parlamentar específico exercido pela pessoa em uma legislatura."""
    __tablename__ = "mandatos"

    id = Column(Integer, primary_key=True, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)
    legislatura_id = Column(Integer, ForeignKey("legislaturas.id", ondelete="SET NULL"), nullable=True, index=True)
    legislatura_numero = Column(Integer, index=True, nullable=True)
    cargo = Column(String(100), default="Deputado Federal")
    sigla_partido = Column(String(50), index=True, nullable=True)
    uf = Column(String(10), index=True, nullable=True)
    situacao = Column(String(100), index=True, nullable=True)  # "Em exercício", "Mandato encerrado", "Suplente", etc.
    condicao_eleitoral = Column(String(100), nullable=True)    # "Titular", "Suplente"
    data_inicio = Column(String(50), nullable=True)
    data_fim = Column(String(50), nullable=True)
    dados_raw = Column(JSON, nullable=True)

    deputado = relationship("Deputado", back_populates="mandatos")
    legislatura_rel = relationship("Legislatura", back_populates="mandatos")


class FiliacaoPartidaria(Base):
    """Registra o histórico de filiações partidárias do parlamentar com períodos precisos."""
    __tablename__ = "filiacoes_partidarias"

    id = Column(Integer, primary_key=True, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)
    sigla_partido = Column(String(50), index=True, nullable=False)
    nome_partido = Column(String(150), nullable=True)
    data_inicio = Column(String(50), nullable=True)
    data_fim = Column(String(50), nullable=True)
    fonte = Column(String(100), default="Câmara dos Deputados")

    deputado = relationship("Deputado", back_populates="filiacoes")


class DeputadoHistorico(Base):
    __tablename__ = "deputado_historico"

    id = Column(Integer, primary_key=True, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)
    data_hora = Column(String(50), nullable=True)
    sigla_partido = Column(String(50), nullable=True)
    situacao = Column(String(100), nullable=True)
    condicao_eleitoral = Column(String(100), nullable=True)
    descricao_status = Column(Text, nullable=True)
    legislatura = Column(Integer, nullable=True)

    deputado = relationship("Deputado", back_populates="historicos")


# ==================== PROPOSIÇÕES ====================

class Proposicao(Base):
    __tablename__ = "proposicoes"

    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(Integer, unique=True, index=True, nullable=False)
    sigla_tipo = Column(String(50), index=True, nullable=False)
    numero = Column(Integer, index=True, nullable=False)
    ano = Column(Integer, index=True, nullable=False)
    ementa = Column(Text, nullable=True)
    ementa_detalhada = Column(Text, nullable=True)
    data_apresentacao = Column(String(50), index=True, nullable=True)
    situacao = Column(String(150), index=True, nullable=True)
    descricao_situacao = Column(Text, nullable=True)
    regime = Column(String(100), nullable=True)
    despacho = Column(Text, nullable=True)
    orgao_atual = Column(String(100), nullable=True)
    url_inteiro_teor = Column(String(500), nullable=True)
    uri = Column(String(500), nullable=True)
    dados_raw = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    autores = relationship("ProposicaoAutor", back_populates="proposicao", cascade="all, delete-orphan")
    temas = relationship("ProposicaoTema", back_populates="proposicao", cascade="all, delete-orphan")
    tramitacoes = relationship("Tramitacao", back_populates="proposicao", cascade="all, delete-orphan", order_by="desc(Tramitacao.sequencia)")
    votacoes_relacionadas = relationship("VotacaoProposicao", back_populates="proposicao", cascade="all, delete-orphan")


class ProposicaoAutor(Base):
    __tablename__ = "proposicao_autores"

    id = Column(Integer, primary_key=True, index=True)
    proposicao_id = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados.id", ondelete="SET NULL"), nullable=True, index=True)
    nome_autor = Column(String(255), nullable=False)
    tipo_autor = Column(String(100), nullable=True)
    ordem_autoria = Column(Integer, default=1)
    proponente = Column(Boolean, default=False)
    uri_autor = Column(String(500), nullable=True)

    proposicao = relationship("Proposicao", back_populates="autores")
    deputado = relationship("Deputado", back_populates="autorias")


class Tema(Base):
    __tablename__ = "temas"

    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(Integer, unique=True, index=True, nullable=True)
    nome = Column(String(150), unique=True, index=True, nullable=False)

    proposicoes = relationship("ProposicaoTema", back_populates="tema")


class ProposicaoTema(Base):
    __tablename__ = "proposicao_temas"

    id = Column(Integer, primary_key=True, index=True)
    proposicao_id = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    tema_id = Column(Integer, ForeignKey("temas.id", ondelete="CASCADE"), nullable=False, index=True)
    relevancia = Column(Integer, default=0)

    proposicao = relationship("Proposicao", back_populates="temas")
    tema = relationship("Tema", back_populates="proposicoes")


class Tramitacao(Base):
    __tablename__ = "tramitacoes"

    id = Column(Integer, primary_key=True, index=True)
    proposicao_id = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    data_hora = Column(String(50), nullable=True)
    sequencia = Column(Integer, nullable=False, default=1)
    descricao_tramitacao = Column(String(255), nullable=True)
    despacho = Column(Text, nullable=True)
    orgao = Column(String(100), nullable=True)
    situacao = Column(String(150), nullable=True)
    regime = Column(String(100), nullable=True)
    url_documento = Column(String(500), nullable=True)

    proposicao = relationship("Proposicao", back_populates="tramitacoes")


# ==================== VOTAÇÕES ====================

class Votacao(Base):
    __tablename__ = "votacoes"

    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(String(100), unique=True, index=True, nullable=False)
    data_hora_registro = Column(String(50), index=True, nullable=True)
    descricao = Column(Text, nullable=False)
    resultado = Column(String(255), nullable=True)
    aprovada = Column(Boolean, nullable=True)
    orgao = Column(String(100), nullable=True)
    evento_camara_id = Column(Integer, nullable=True)
    placar_sim = Column(Integer, default=0)
    placar_nao = Column(Integer, default=0)
    placar_abstencao = Column(Integer, default=0)
    placar_obstrucao = Column(Integer, default=0)
    uri = Column(String(500), nullable=True)
    dados_raw = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    votos = relationship("Voto", back_populates="votacao", cascade="all, delete-orphan")
    orientacoes = relationship("VotacaoOrientacao", back_populates="votacao", cascade="all, delete-orphan")
    proposicoes_relacionadas = relationship("VotacaoProposicao", back_populates="votacao", cascade="all, delete-orphan")


class VotacaoProposicao(Base):
    __tablename__ = "votacao_proposicoes"

    id = Column(Integer, primary_key=True, index=True)
    votacao_id = Column(Integer, ForeignKey("votacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    proposicao_id = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_relacao = Column(String(100), default="Votação relacionada à proposição")
    descricao = Column(Text, nullable=True)

    votacao = relationship("Votacao", back_populates="proposicoes_relacionadas")
    proposicao = relationship("Proposicao", back_populates="votacoes_relacionadas")


class VotacaoOrientacao(Base):
    __tablename__ = "votacao_orientacoes"

    id = Column(Integer, primary_key=True, index=True)
    votacao_id = Column(Integer, ForeignKey("votacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    bancada = Column(String(100), nullable=False)
    orientacao_voto = Column(String(50), nullable=False)

    votacao = relationship("Votacao", back_populates="orientacoes")


class Voto(Base):
    __tablename__ = "votos"

    id = Column(Integer, primary_key=True, index=True)
    votacao_id = Column(Integer, ForeignKey("votacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_voto = Column(String(50), index=True, nullable=False)
    data_hora = Column(String(50), nullable=True)
    sigla_partido_momento = Column(String(50), nullable=True)  # Partido do deputado no momento exato do voto
    uf_momento = Column(String(10), nullable=True)             # UF do deputado no momento do voto

    votacao = relationship("Votacao", back_populates="votos")
    deputado = relationship("Deputado", back_populates="votos")


# ==================== EVENTOS ====================

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(Integer, unique=True, index=True, nullable=False)
    data_inicio = Column(String(50), index=True, nullable=True)
    data_fim = Column(String(50), nullable=True)
    tipo = Column(String(100), nullable=True)
    descricao = Column(Text, nullable=True)
    situacao = Column(String(100), nullable=True)
    local = Column(String(255), nullable=True)
    uri = Column(String(500), nullable=True)
    dados_raw = Column(JSON, nullable=True)

    deputados = relationship("EventoDeputado", back_populates="evento", cascade="all, delete-orphan")


class EventoDeputado(Base):
    __tablename__ = "evento_deputados"

    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)

    evento = relationship("Evento", back_populates="deputados")
    deputado = relationship("Deputado", back_populates="eventos")


# ==================== DIMENSÃO INSTITUCIONAL: ENTENDA O GOVERNO ====================

class Instituicao(Base):
    """Representa qualquer instituição, poder, órgão, ministério ou tribunal do Estado brasileiro."""
    __tablename__ = "instituicoes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), index=True, nullable=False)
    sigla = Column(String(50), index=True, nullable=True)
    tipo = Column(String(50), index=True, nullable=False)  # PODER, ORGAO, MINISTERIO, SECRETARIA, DEPARTAMENTO, AUTARQUIA, FUNDACAO, CASA_LEGISLATIVA, TRIBUNAL, COMISSAO, OUTRO
    poder = Column(String(50), index=True, nullable=False)  # Executivo, Legislativo, Judiciário, Instituição Autônoma / Controle
    esfera = Column(String(50), index=True, nullable=False)  # Federal, Estadual, Distrital, Municipal
    nivel_federativo = Column(String(50), index=True, nullable=False)  # União, Estados, Distrito Federal, Municípios
    codigo_externo = Column(String(100), index=True, nullable=True)  # SIORG code, Camara code, etc.
    natureza_juridica = Column(String(150), nullable=True)
    descricao = Column(Text, nullable=True)
    site_oficial = Column(String(500), nullable=True)
    fonte = Column(String(150), nullable=False, default="SIORG / dados.gov.br")
    url_fonte = Column(String(500), nullable=True)
    ativo = Column(Boolean, default=True)
    dados_raw = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    relacoes_origem = relationship("RelacaoInstitucional", foreign_keys="RelacaoInstitucional.instituicao_origem_id", back_populates="instituicao_origem", cascade="all, delete-orphan")
    relacoes_destino = relationship("RelacaoInstitucional", foreign_keys="RelacaoInstitucional.instituicao_destino_id", back_populates="instituicao_destino", cascade="all, delete-orphan")
    cargos = relationship("Cargo", back_populates="instituicao", cascade="all, delete-orphan")


class RelacaoInstitucional(Base):
    """Representa relações institucionais reais entre órgãos (hierarquia, vinculação, composição, fiscalização etc.)."""
    __tablename__ = "relacoes_institucionais"

    id = Column(Integer, primary_key=True, index=True)
    instituicao_origem_id = Column(Integer, ForeignKey("instituicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    instituicao_destino_id = Column(Integer, ForeignKey("instituicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_relacao = Column(String(50), index=True, nullable=False)  # HIERARQUIA_ADMINISTRATIVA, VINCULACAO, COMPOSICAO, CONTROLE, FISCALIZACAO, INDICACAO, APROVACAO, OUTRA
    data_inicio = Column(String(50), nullable=True)
    data_fim = Column(String(50), nullable=True)
    descricao = Column(Text, nullable=True)
    fonte = Column(String(150), default="Estrutura Oficial")
    url_fonte = Column(String(500), nullable=True)
    dados_raw = Column(JSON, nullable=True)

    instituicao_origem = relationship("Instituicao", foreign_keys=[instituicao_origem_id], back_populates="relacoes_origem")
    instituicao_destino = relationship("Instituicao", foreign_keys=[instituicao_destino_id], back_populates="relacoes_destino")


class Cargo(Base):
    """Representa um cargo público permanente associado a uma instituição."""
    __tablename__ = "cargos"

    id = Column(Integer, primary_key=True, index=True)
    instituicao_id = Column(Integer, ForeignKey("instituicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String(150), nullable=False)
    tipo = Column(String(50), nullable=True)
    fonte = Column(String(100), default="Oficial")

    instituicao = relationship("Instituicao", back_populates="cargos")
    ocupacoes = relationship("OcupacaoCargo", back_populates="cargo", cascade="all, delete-orphan")


class OcupacaoCargo(Base):
    """Registra quem ocupou determinado cargo e em qual período, sem fundir pessoa e cargo."""
    __tablename__ = "ocupacoes_cargo"

    id = Column(Integer, primary_key=True, index=True)
    cargo_id = Column(Integer, ForeignKey("cargos.id", ondelete="CASCADE"), nullable=False, index=True)
    pessoa_id = Column(Integer, ForeignKey("deputados.id", ondelete="SET NULL"), nullable=True, index=True)
    nome_ocupante = Column(String(255), nullable=False)
    data_inicio = Column(String(50), nullable=True)
    data_fim = Column(String(50), nullable=True)
    fonte = Column(String(100), default="Oficial")

    cargo = relationship("Cargo", back_populates="ocupacoes")
    pessoa = relationship("Deputado")


# ==================== SINCRONIZAÇÃO E AUDITORIA ====================

class SyncRun(Base):
    __tablename__ = "sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)  # "all", "deputados", "proposicoes", "votacoes", "eventos", "seed", "siorg", "legislaturas", "estrutura_governo"
    iniciado_em = Column(DateTime(timezone=True), default=utc_now)
    finalizado_em = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="RUNNING")  # "SUCCESS", "FAILED", "RUNNING"
    registros_processados = Column(Integer, default=0)
    erro = Column(Text, nullable=True)


class OfficialCache(Base):
    """Agregados oficiais sob demanda, separados do histórico parlamentar."""
    __tablename__ = "official_cache"

    cache_key = Column(String(200), primary_key=True)
    source = Column(String(50), nullable=False, index=True)
    source_url = Column(String(500), nullable=False)
    payload = Column(JSON, nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
