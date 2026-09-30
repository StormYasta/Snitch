"""initial_schema

Revision ID: fe8661aa8f62
Revises:
Create Date: 2026-09-24 11:31:41.851145

Baseline do MVP legislativo. A revisão seguinte adiciona histórico parlamentar
e a dimensão institucional.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fe8661aa8f62"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deputados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camara_id", sa.Integer(), nullable=False),
        sa.Column("nome_parlamentar", sa.String(length=255), nullable=False),
        sa.Column("nome_civil", sa.String(length=255), nullable=True),
        sa.Column("sigla_partido", sa.String(length=50), nullable=True),
        sa.Column("uf", sa.String(length=10), nullable=True),
        sa.Column("url_foto", sa.String(length=500), nullable=True),
        sa.Column("situacao", sa.String(length=100), nullable=True),
        sa.Column("condicao_eleitoral", sa.String(length=100), nullable=True),
        sa.Column("descricao_status", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("legislatura", sa.Integer(), nullable=True),
        sa.Column("gabinete_predio", sa.String(length=50), nullable=True),
        sa.Column("gabinete_sala", sa.String(length=50), nullable=True),
        sa.Column("gabinete_andar", sa.String(length=50), nullable=True),
        sa.Column("gabinete_telefone", sa.String(length=50), nullable=True),
        sa.Column("data_nascimento", sa.String(length=50), nullable=True),
        sa.Column("municipio_nascimento", sa.String(length=100), nullable=True),
        sa.Column("uf_nascimento", sa.String(length=10), nullable=True),
        sa.Column("escolaridade", sa.String(length=100), nullable=True),
        sa.Column("rede_social", sa.JSON(), nullable=True),
        sa.Column("url_website", sa.String(length=500), nullable=True),
        sa.Column("uri", sa.String(length=500), nullable=True),
        sa.Column("dados_raw", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camara_id"),
    )
    op.create_index("ix_deputados_id", "deputados", ["id"])
    op.create_index("ix_deputados_camara_id", "deputados", ["camara_id"], unique=True)
    op.create_index("ix_deputados_nome_parlamentar", "deputados", ["nome_parlamentar"])
    op.create_index("ix_deputados_sigla_partido", "deputados", ["sigla_partido"])
    op.create_index("ix_deputados_uf", "deputados", ["uf"])
    op.create_index("ix_deputados_legislatura", "deputados", ["legislatura"])

    op.create_table(
        "proposicoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camara_id", sa.Integer(), nullable=False),
        sa.Column("sigla_tipo", sa.String(length=50), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("ementa", sa.Text(), nullable=True),
        sa.Column("ementa_detalhada", sa.Text(), nullable=True),
        sa.Column("data_apresentacao", sa.String(length=50), nullable=True),
        sa.Column("situacao", sa.String(length=150), nullable=True),
        sa.Column("descricao_situacao", sa.Text(), nullable=True),
        sa.Column("regime", sa.String(length=100), nullable=True),
        sa.Column("despacho", sa.Text(), nullable=True),
        sa.Column("orgao_atual", sa.String(length=100), nullable=True),
        sa.Column("url_inteiro_teor", sa.String(length=500), nullable=True),
        sa.Column("uri", sa.String(length=500), nullable=True),
        sa.Column("dados_raw", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camara_id"),
    )
    op.create_index("ix_proposicoes_id", "proposicoes", ["id"])
    op.create_index("ix_proposicoes_camara_id", "proposicoes", ["camara_id"], unique=True)
    op.create_index("ix_proposicoes_sigla_tipo", "proposicoes", ["sigla_tipo"])
    op.create_index("ix_proposicoes_numero", "proposicoes", ["numero"])
    op.create_index("ix_proposicoes_ano", "proposicoes", ["ano"])
    op.create_index("ix_proposicoes_data_apresentacao", "proposicoes", ["data_apresentacao"])
    op.create_index("ix_proposicoes_situacao", "proposicoes", ["situacao"])

    op.create_table(
        "temas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camara_id", sa.Integer(), nullable=True),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camara_id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index("ix_temas_id", "temas", ["id"])
    op.create_index("ix_temas_camara_id", "temas", ["camara_id"], unique=True)
    op.create_index("ix_temas_nome", "temas", ["nome"], unique=True)

    op.create_table(
        "votacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camara_id", sa.String(length=100), nullable=False),
        sa.Column("data_hora_registro", sa.String(length=50), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("resultado", sa.String(length=255), nullable=True),
        sa.Column("aprovada", sa.Boolean(), nullable=True),
        sa.Column("orgao", sa.String(length=100), nullable=True),
        sa.Column("evento_camara_id", sa.Integer(), nullable=True),
        sa.Column("placar_sim", sa.Integer(), nullable=True),
        sa.Column("placar_nao", sa.Integer(), nullable=True),
        sa.Column("placar_abstencao", sa.Integer(), nullable=True),
        sa.Column("placar_obstrucao", sa.Integer(), nullable=True),
        sa.Column("uri", sa.String(length=500), nullable=True),
        sa.Column("dados_raw", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camara_id"),
    )
    op.create_index("ix_votacoes_id", "votacoes", ["id"])
    op.create_index("ix_votacoes_camara_id", "votacoes", ["camara_id"], unique=True)
    op.create_index("ix_votacoes_data_hora_registro", "votacoes", ["data_hora_registro"])

    op.create_table(
        "eventos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("camara_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.String(length=50), nullable=True),
        sa.Column("data_fim", sa.String(length=50), nullable=True),
        sa.Column("tipo", sa.String(length=100), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("situacao", sa.String(length=100), nullable=True),
        sa.Column("local", sa.String(length=255), nullable=True),
        sa.Column("uri", sa.String(length=500), nullable=True),
        sa.Column("dados_raw", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camara_id"),
    )
    op.create_index("ix_eventos_id", "eventos", ["id"])
    op.create_index("ix_eventos_camara_id", "eventos", ["camara_id"], unique=True)
    op.create_index("ix_eventos_data_inicio", "eventos", ["data_inicio"])

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("registros_processados", sa.Integer(), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_runs_id", "sync_runs", ["id"])

    op.create_table(
        "deputado_historico",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deputado_id", sa.Integer(), nullable=False),
        sa.Column("data_hora", sa.String(length=50), nullable=True),
        sa.Column("sigla_partido", sa.String(length=50), nullable=True),
        sa.Column("situacao", sa.String(length=100), nullable=True),
        sa.Column("condicao_eleitoral", sa.String(length=100), nullable=True),
        sa.Column("descricao_status", sa.String(length=255), nullable=True),
        sa.Column("legislatura", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["deputado_id"], ["deputados.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deputado_historico_id", "deputado_historico", ["id"])

    op.create_table(
        "proposicao_autores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposicao_id", sa.Integer(), nullable=False),
        sa.Column("deputado_id", sa.Integer(), nullable=True),
        sa.Column("nome_autor", sa.String(length=255), nullable=False),
        sa.Column("tipo_autor", sa.String(length=100), nullable=True),
        sa.Column("ordem_autoria", sa.Integer(), nullable=True),
        sa.Column("proponente", sa.Boolean(), nullable=True),
        sa.Column("uri_autor", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["deputado_id"], ["deputados.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proposicao_id"], ["proposicoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposicao_autores_id", "proposicao_autores", ["id"])

    op.create_table(
        "proposicao_temas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposicao_id", sa.Integer(), nullable=False),
        sa.Column("tema_id", sa.Integer(), nullable=False),
        sa.Column("relevancia", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["proposicao_id"], ["proposicoes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tema_id"], ["temas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposicao_temas_id", "proposicao_temas", ["id"])

    op.create_table(
        "tramitacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposicao_id", sa.Integer(), nullable=False),
        sa.Column("data_hora", sa.String(length=50), nullable=True),
        sa.Column("sequencia", sa.Integer(), nullable=False),
        sa.Column("descricao_tramitacao", sa.String(length=255), nullable=True),
        sa.Column("despacho", sa.Text(), nullable=True),
        sa.Column("orgao", sa.String(length=100), nullable=True),
        sa.Column("situacao", sa.String(length=150), nullable=True),
        sa.Column("regime", sa.String(length=100), nullable=True),
        sa.Column("url_documento", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["proposicao_id"], ["proposicoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tramitacoes_id", "tramitacoes", ["id"])

    op.create_table(
        "votacao_proposicoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("votacao_id", sa.Integer(), nullable=False),
        sa.Column("proposicao_id", sa.Integer(), nullable=False),
        sa.Column("tipo_relacao", sa.String(length=100), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["proposicao_id"], ["proposicoes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["votacao_id"], ["votacoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_votacao_proposicoes_id", "votacao_proposicoes", ["id"])

    op.create_table(
        "votacao_orientacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("votacao_id", sa.Integer(), nullable=False),
        sa.Column("bancada", sa.String(length=100), nullable=False),
        sa.Column("orientacao_voto", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["votacao_id"], ["votacoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_votacao_orientacoes_id", "votacao_orientacoes", ["id"])

    op.create_table(
        "votos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("votacao_id", sa.Integer(), nullable=False),
        sa.Column("deputado_id", sa.Integer(), nullable=False),
        sa.Column("tipo_voto", sa.String(length=50), nullable=False),
        sa.Column("data_hora", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["deputado_id"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["votacao_id"], ["votacoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_votos_id", "votos", ["id"])
    op.create_index("ix_votos_tipo_voto", "votos", ["tipo_voto"])

    op.create_table(
        "evento_deputados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evento_id", sa.Integer(), nullable=False),
        sa.Column("deputado_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["deputado_id"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evento_deputados_id", "evento_deputados", ["id"])


def downgrade() -> None:
    op.drop_index("ix_evento_deputados_id", table_name="evento_deputados")
    op.drop_table("evento_deputados")
    op.drop_index("ix_votos_tipo_voto", table_name="votos")
    op.drop_index("ix_votos_id", table_name="votos")
    op.drop_table("votos")
    op.drop_index("ix_votacao_orientacoes_id", table_name="votacao_orientacoes")
    op.drop_table("votacao_orientacoes")
    op.drop_index("ix_votacao_proposicoes_id", table_name="votacao_proposicoes")
    op.drop_table("votacao_proposicoes")
    op.drop_index("ix_tramitacoes_id", table_name="tramitacoes")
    op.drop_table("tramitacoes")
    op.drop_index("ix_proposicao_temas_id", table_name="proposicao_temas")
    op.drop_table("proposicao_temas")
    op.drop_index("ix_proposicao_autores_id", table_name="proposicao_autores")
    op.drop_table("proposicao_autores")
    op.drop_index("ix_deputado_historico_id", table_name="deputado_historico")
    op.drop_table("deputado_historico")
    op.drop_index("ix_sync_runs_id", table_name="sync_runs")
    op.drop_table("sync_runs")
    op.drop_index("ix_eventos_data_inicio", table_name="eventos")
    op.drop_index("ix_eventos_camara_id", table_name="eventos")
    op.drop_index("ix_eventos_id", table_name="eventos")
    op.drop_table("eventos")
    op.drop_index("ix_votacoes_data_hora_registro", table_name="votacoes")
    op.drop_index("ix_votacoes_camara_id", table_name="votacoes")
    op.drop_index("ix_votacoes_id", table_name="votacoes")
    op.drop_table("votacoes")
    op.drop_index("ix_temas_nome", table_name="temas")
    op.drop_index("ix_temas_camara_id", table_name="temas")
    op.drop_index("ix_temas_id", table_name="temas")
    op.drop_table("temas")
    op.drop_index("ix_proposicoes_situacao", table_name="proposicoes")
    op.drop_index("ix_proposicoes_data_apresentacao", table_name="proposicoes")
    op.drop_index("ix_proposicoes_ano", table_name="proposicoes")
    op.drop_index("ix_proposicoes_numero", table_name="proposicoes")
    op.drop_index("ix_proposicoes_sigla_tipo", table_name="proposicoes")
    op.drop_index("ix_proposicoes_camara_id", table_name="proposicoes")
    op.drop_index("ix_proposicoes_id", table_name="proposicoes")
    op.drop_table("proposicoes")
    op.drop_index("ix_deputados_legislatura", table_name="deputados")
    op.drop_index("ix_deputados_uf", table_name="deputados")
    op.drop_index("ix_deputados_sigla_partido", table_name="deputados")
    op.drop_index("ix_deputados_nome_parlamentar", table_name="deputados")
    op.drop_index("ix_deputados_camara_id", table_name="deputados")
    op.drop_index("ix_deputados_id", table_name="deputados")
    op.drop_table("deputados")
