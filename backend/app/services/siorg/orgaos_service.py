import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models import Instituicao, RelacaoInstitucional, utc_now
from app.services.siorg.siorg_client import SiorgClient

logger = logging.getLogger(__name__)

# Mapeamento e destaque dos ministérios e entidades de alta relevância pública
MINISTERIOS_DESTAQUE = [
    {"sigla": "MF", "nome": "Ministério da Fazenda", "natureza": "Administração Direta Federal"},
    {"sigla": "MS", "nome": "Ministério da Saúde", "natureza": "Administração Direta Federal"},
    {"sigla": "MEC", "nome": "Ministério da Educação", "natureza": "Administração Direta Federal"},
    {"sigla": "MJSP", "nome": "Ministério da Justiça e Segurança Pública", "natureza": "Administração Direta Federal"},
    {"sigla": "MD", "nome": "Ministério da Defesa", "natureza": "Administração Direta Federal"},
    {"sigla": "MRE", "nome": "Ministério das Relações Exteriores", "natureza": "Administração Direta Federal"},
    {"sigla": "MMA", "nome": "Ministério do Meio Ambiente e Mudança do Clima", "natureza": "Administração Direta Federal"},
    {"sigla": "MME", "nome": "Ministério de Minas e Energia", "natureza": "Administração Direta Federal"},
    {"sigla": "MGI", "nome": "Ministério da Gestão e da Inovação em Serviços Públicos", "natureza": "Administração Direta Federal"},
    {"sigla": "MPO", "nome": "Ministério do Planejamento e Orçamento", "natureza": "Administração Direta Federal"},
    {"sigla": "MCTI", "nome": "Ministério da Ciência, Tecnologia e Inovação", "natureza": "Administração Direta Federal"},
    {"sigla": "MDIC", "nome": "Ministério do Desenvolvimento, Indústria, Comércio e Serviços", "natureza": "Administração Direta Federal"},
    {"sigla": "MDS", "nome": "Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome", "natureza": "Administração Direta Federal"},
    {"sigla": "MT", "nome": "Ministério dos Transportes", "natureza": "Administração Direta Federal"},
    {"sigla": "MAPA", "nome": "Ministério da Agricultura e Pecuária", "natureza": "Administração Direta Federal"},
    {"sigla": "MCID", "nome": "Ministério das Cidades", "natureza": "Administração Direta Federal"},
    {"sigla": "MTE", "nome": "Ministério do Trabalho e Emprego", "natureza": "Administração Direta Federal"},
    {"sigla": "MPOR", "nome": "Ministério de Portos e Aeroportos", "natureza": "Administração Direta Federal"},
    {"sigla": "MCOM", "nome": "Ministério das Comunicações", "natureza": "Administração Direta Federal"},
    {"sigla": "MDHC", "nome": "Ministério dos Direitos Humanos e da Cidadania", "natureza": "Administração Direta Federal"},
    {"sigla": "MIR", "nome": "Ministério da Igualdade Racial", "natureza": "Administração Direta Federal"},
    {"sigla": "MPI", "nome": "Ministério dos Povos Indígenas", "natureza": "Administração Direta Federal"},
    {"sigla": "MMULHERES", "nome": "Ministério das Mulheres", "natureza": "Administração Direta Federal"},
    {"sigla": "MINC", "nome": "Ministério da Cultura", "natureza": "Administração Direta Federal"},
    {"sigla": "MEPORTE", "nome": "Ministério do Esporte", "natureza": "Administração Direta Federal"},
    {"sigla": "MTUR", "nome": "Ministério do Turismo", "natureza": "Administração Direta Federal"},
    {"sigla": "MIDR", "nome": "Ministério da Integração e do Desenvolvimento Regional", "natureza": "Administração Direta Federal"},
    {"sigla": "MPA", "nome": "Ministério da Pesca e Aquicultura", "natureza": "Administração Direta Federal"},
    {"sigla": "MDA", "nome": "Ministério do Desenvolvimento Agrário e Agricultura Familiar", "natureza": "Administração Direta Federal"},
    {"sigla": "CGU", "nome": "Controladoria-Geral da União", "natureza": "Órgão Central de Controle Interno Federal"}
]

# Entidades vinculadas essenciais (Autarquias e Fundações)
ENTIDADES_VINCULADAS = [
    {
        "sigla": "INSS",
        "nome": "Instituto Nacional do Seguro Social",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MDS",
        "descricao": "Autarquia federal responsável pela operacionalização dos direitos dos segurados do Regime Geral de Previdência Social.",
        "natureza_juridica": "Autarquia Federal"
    },
    {
        "sigla": "RECEITA_FEDERAL",
        "nome": "Secretaria Especial da Receita Federal do Brasil",
        "tipo": "SECRETARIA",
        "ministerio_sigla": "MF",
        "descricao": "Órgão específico singular subordinado ao Ministério da Fazenda, responsável pela administração tributária federal e aduaneira.",
        "natureza_juridica": "Órgão Direto da Administração Federal"
    },
    {
        "sigla": "STN",
        "nome": "Secretaria do Tesouro Nacional",
        "tipo": "SECRETARIA",
        "ministerio_sigla": "MF",
        "descricao": "Órgão central do Sistema de Administração Financeira Federal, responsável pela gestão da dívida pública e das contas fiscais.",
        "natureza_juridica": "Órgão Direto da Administração Federal"
    },
    {
        "sigla": "ANVISA",
        "nome": "Agência Nacional de Vigilância Sanitária",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MS",
        "descricao": "Autarquia sob regime especial vinculada ao Ministério da Saúde, responsável pelo controle sanitário e regulação de produtos e serviços.",
        "natureza_juridica": "Autarquia Especial (Agência Reguladora)"
    },
    {
        "sigla": "FIOCRUZ",
        "nome": "Fundação Oswaldo Cruz",
        "tipo": "FUNDACAO",
        "ministerio_sigla": "MS",
        "descricao": "Fundação pública de pesquisa e desenvolvimento em ciências biológicas e saúde pública vinculada ao Ministério da Saúde.",
        "natureza_juridica": "Fundação Pública Federal"
    },
    {
        "sigla": "IBAMA",
        "nome": "Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renováveis",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MMA",
        "descricao": "Autarquia federal vinculada ao Ministério do Meio Ambiente responsável pelo poder de polícia ambiental e licenciamento federal.",
        "natureza_juridica": "Autarquia Federal"
    },
    {
        "sigla": "ICMBIO",
        "nome": "Instituto Chico Mendes de Conservação da Biodiversidade",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MMA",
        "descricao": "Autarquia responsável por propor, implantar, gerir, proteger e monitorar as Unidades de Conservação federais.",
        "natureza_juridica": "Autarquia Federal"
    },
    {
        "sigla": "IBGE",
        "nome": "Fundação Instituto Brasileiro de Geografia e Estatística",
        "tipo": "FUNDACAO",
        "ministerio_sigla": "MPO",
        "descricao": "Fundação pública federal responsável pelas informações estatísticas, geográficas, cartográficas e ambientais do Brasil.",
        "natureza_juridica": "Fundação Pública Federal"
    },
    {
        "sigla": "IPEA",
        "nome": "Instituto de Pesquisa Econômica Aplicada",
        "tipo": "FUNDACAO",
        "ministerio_sigla": "MPO",
        "descricao": "Fundação pública federal de pesquisa que presta apoio técnico e institucional às decisões governamentais.",
        "natureza_juridica": "Fundação Pública Federal"
    },
    {
        "sigla": "BCB",
        "nome": "Banco Central do Brasil",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MF",
        "descricao": "Autarquia de natureza especial dotada de autonomia técnica, operacional, administrativa e financeira (Lei Complementar 179/2021).",
        "natureza_juridica": "Autarquia Especial Autônoma"
    },
    {
        "sigla": "CNPQ",
        "nome": "Conselho Nacional de Desenvolvimento Científico e Tecnológico",
        "tipo": "FUNDACAO",
        "ministerio_sigla": "MCTI",
        "descricao": "Agência vinculada ao MCTI destinada ao fomento da pesquisa científica e tecnológica e qualificação de pesquisadores.",
        "natureza_juridica": "Fundação Pública Federal"
    },
    {
        "sigla": "ANATEL",
        "nome": "Agência Nacional de Telecomunicações",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MCOM",
        "descricao": "Agência reguladora autárquica vinculada ao Ministério das Comunicações para regular o setor de telecomunicações.",
        "natureza_juridica": "Autarquia Especial (Agência Reguladora)"
    },
    {
        "sigla": "ANEEL",
        "nome": "Agência Nacional de Energia Elétrica",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MME",
        "descricao": "Autarquia em regime especial vinculada ao Ministério de Minas e Energia para regular o setor elétrico brasileiro.",
        "natureza_juridica": "Autarquia Especial (Agência Reguladora)"
    },
    {
        "sigla": "ANP",
        "nome": "Agência Nacional do Petróleo, Gás Natural e Biocombustíveis",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MME",
        "descricao": "Órgão regulador das atividades integrantes das indústrias de petróleo, gás natural e biocombustíveis.",
        "natureza_juridica": "Autarquia Especial (Agência Reguladora)"
    },
    {
        "sigla": "FUNAI",
        "nome": "Fundação Nacional dos Povos Indígenas",
        "tipo": "FUNDACAO",
        "ministerio_sigla": "MPI",
        "descricao": "Órgão indigenista oficial do Estado brasileiro, vinculado ao Ministério dos Povos Indígenas.",
        "natureza_juridica": "Fundação Pública Federal"
    },
    {
        "sigla": "INCRA",
        "nome": "Instituto Nacional de Colonização e Reforma Agrária",
        "tipo": "AUTARQUIA",
        "ministerio_sigla": "MDA",
        "descricao": "Autarquia federal responsável pela execução da reforma agrária e pelo ordenamento fundiário nacional.",
        "natureza_juridica": "Autarquia Federal"
    }
]


class OrgaosService:
    def __init__(self, client: Optional[SiorgClient] = None):
        self.client = client or SiorgClient()

    def sync_orgaos_executivo(self, db: Session, use_live_siorg: bool = True) -> int:
        """Sincroniza os Ministérios e órgãos federais com SIORG e dados canônicos."""
        logger.info("Sincronizando órgãos do Executivo Federal com dados do SIORG...")

        # 1. Obtém o nó da Presidência da República no banco
        presidencia = db.query(Instituicao).filter(Instituicao.codigo_externo == "PRESIDENCIA_REPUBLICA").first()
        if not presidencia:
            logger.warning("Presidência da República não encontrada no banco. Sincronize a estrutura canônica primeiro.")
            return 0

        # Tenta carregar dados do SIORG para enriquecer códigos e nomes oficiais
        siorg_unidades = []
        if use_live_siorg:
            try:
                siorg_unidades = self.client.fetch_unidades()
            except Exception as e:
                logger.warning(f"Não foi possível carregar dados online do SIORG: {e}")

        siorg_by_sigla = {}
        siorg_by_nome = {}
        for u in siorg_unidades:
            sig = (u.get("sigla") or "").strip().upper()
            nom = (u.get("nome") or "").strip().upper()
            if sig:
                siorg_by_sigla[sig] = u
            if nom:
                siorg_by_nome[nom] = u

        count = 0
        ministerios_db = {}

        # 2. Sincroniza Ministérios de Estado
        for min_data in MINISTERIOS_DESTAQUE:
            sigla = min_data["sigla"]
            nome = min_data["nome"]
            siorg_unit = siorg_by_sigla.get(sigla.upper()) or siorg_by_nome.get(nome.upper())

            cod_externo = siorg_unit.get("codigoUnidade") if siorg_unit else f"SIORG_MIN_{sigla}"

            inst = db.query(Instituicao).filter(Instituicao.sigla == sigla, Instituicao.esfera == "Federal").first()
            if not inst:
                inst = Instituicao(
                    nome=siorg_unit.get("nome", nome) if siorg_unit else nome,
                    sigla=sigla,
                    tipo="MINISTERIO",
                    poder="Executivo",
                    esfera="Federal",
                    nivel_federativo="União",
                    codigo_externo=cod_externo,
                    natureza_juridica=min_data.get("natureza", "Administração Direta Federal"),
                    descricao=f"Órgão de primeiro escalão do Poder Executivo federal, auxiliando o Presidente da República.",
                    site_oficial=f"https://www.gov.br/{sigla.lower()}",
                    fonte="SIORG / Ministério da Gestão e da Inovação",
                    ativo=True
                )
                db.add(inst)
            else:
                inst.nome = nome
                inst.tipo = "MINISTERIO"
                inst.poder = "Executivo"
                inst.esfera = "Federal"
                inst.nivel_federativo = "União"
                inst.codigo_externo = cod_externo
                inst.updated_at = utc_now()

            db.flush()
            ministerios_db[sigla] = inst
            count += 1

            # Relação com Presidência da República: HIERARQUIA_ADMINISTRATIVA
            rel_pr = db.query(RelacaoInstitucional).filter(
                RelacaoInstitucional.instituicao_origem_id == inst.id,
                RelacaoInstitucional.instituicao_destino_id == presidencia.id,
                RelacaoInstitucional.tipo_relacao == "HIERARQUIA_ADMINISTRATIVA"
            ).first()

            if not rel_pr:
                db.add(RelacaoInstitucional(
                    instituicao_origem_id=inst.id,
                    instituicao_destino_id=presidencia.id,
                    tipo_relacao="HIERARQUIA_ADMINISTRATIVA",
                    descricao="Subordinação hierárquica e administrativa direta à Chefia do Poder Executivo da União",
                    fonte="SIORG / CF/88 Art. 76"
                ))

        # 3. Sincroniza Entidades Vinculadas (Autarquias, Fundações) e Secretarias
        for ent in ENTIDADES_VINCULADAS:
            sigla = ent["sigla"]
            nome = ent["nome"]
            tipo = ent["tipo"]
            min_sigla = ent["ministerio_sigla"]
            ministerio_inst = ministerios_db.get(min_sigla)

            siorg_unit = siorg_by_sigla.get(sigla.upper()) or siorg_by_nome.get(nome.upper())
            cod_externo = siorg_unit.get("codigoUnidade") if siorg_unit else f"SIORG_ENT_{sigla}"

            inst = db.query(Instituicao).filter(Instituicao.sigla == sigla, Instituicao.esfera == "Federal").first()
            if not inst:
                inst = Instituicao(
                    nome=nome,
                    sigla=sigla,
                    tipo=tipo,
                    poder="Executivo",
                    esfera="Federal",
                    nivel_federativo="União",
                    codigo_externo=cod_externo,
                    natureza_juridica=ent.get("natureza_juridica"),
                    descricao=ent.get("descricao"),
                    site_oficial=f"https://www.gov.br/{sigla.lower()}",
                    fonte="SIORG / dados.gov.br",
                    ativo=True
                )
                db.add(inst)
            else:
                inst.nome = nome
                inst.sigla = sigla
                inst.tipo = tipo
                inst.descricao = ent.get("descricao")
                inst.natureza_juridica = ent.get("natureza_juridica")
                inst.updated_at = utc_now()

            db.flush()
            count += 1

            # Relação com o Ministério:
            # - Se Secretaria: HIERARQUIA_ADMINISTRATIVA
            # - Se Autarquia ou Fundação: VINCULACAO (Decreto-Lei 200/1967, art. 19: supervisão ministerial)
            if ministerio_inst:
                tipo_rel = "HIERARQUIA_ADMINISTRATIVA" if tipo == "SECRETARIA" else "VINCULACAO"
                desc_rel = (
                    "Subordinação hierárquica e administrativa interna ao Ministério"
                    if tipo == "SECRETARIA"
                    else f"Supervisão ministerial e vinculação administrativa (Art. 19 do DL 200/1967) ao {ministerio_inst.nome}"
                )

                rel_min = db.query(RelacaoInstitucional).filter(
                    RelacaoInstitucional.instituicao_origem_id == inst.id,
                    RelacaoInstitucional.instituicao_destino_id == ministerio_inst.id,
                    RelacaoInstitucional.tipo_relacao == tipo_rel
                ).first()

                if not rel_min:
                    db.add(RelacaoInstitucional(
                        instituicao_origem_id=inst.id,
                        instituicao_destino_id=ministerio_inst.id,
                        tipo_relacao=tipo_rel,
                        descricao=desc_rel,
                        fonte="SIORG / Decreto-Lei 200/1967"
                    ))

        db.commit()
        logger.info(f"{count} ministérios e entidades vinculadas sincronizados com sucesso.")
        return count
