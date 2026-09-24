import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Instituicao, RelacaoInstitucional, utc_now

logger = logging.getLogger(__name__)

# Definição canônica das instituições fundacionais do Estado brasileiro
# em estrita consonância com a Constituição Federal de 1988
ESTRUTURA_CANONICA = [
    # Topo: Brasil
    {
        "nome": "República Federativa do Brasil",
        "sigla": "Brasil",
        "tipo": "ESTADO",
        "poder": "Soberania Nacional",
        "esfera": "Nacional",
        "nivel_federativo": "Nacional",
        "natureza_juridica": "Pessoa Jurídica de Direito Público Externo/Interno",
        "descricao": "União indissolúvel dos Estados, Municípios e do Distrito Federal, constituída em Estado Democrático de Direito (Art. 1º da CF/88).",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "BRASIL",
        "relacoes": []
    },
    # Nível 1: Níveis Federativos
    {
        "nome": "União",
        "sigla": "União",
        "tipo": "ENTE_FEDERATIVO",
        "poder": "Governo Federal",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Pessoa Jurídica de Direito Público Interno",
        "descricao": "Pessoa jurídica de direito público interno autônoma, dotada de competências legislativas e executivas federais (Arts. 20 a 24 da CF/88).",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "UNIAO",
        "relacoes": [
            {"destino": "BRASIL", "tipo": "COMPOSICAO", "descricao": "Ente político autônomo que integra a República Federativa do Brasil"}
        ]
    },
    {
        "nome": "Estados da Federação",
        "sigla": "Estados",
        "tipo": "ENTE_FEDERATIVO",
        "poder": "Governos Estaduais",
        "esfera": "Estadual",
        "nivel_federativo": "Estados",
        "natureza_juridica": "Pessoas Jurídicas de Direito Público Interno",
        "descricao": "26 entes federativos dotados de auto-organização, autolegislação e autogoverno (Arts. 25 a 28 da CF/88).",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "ESTADOS",
        "relacoes": [
            {"destino": "BRASIL", "tipo": "COMPOSICAO", "descricao": "Entes federativos componentes do Estado brasileiro"}
        ]
    },
    {
        "nome": "Distrito Federal",
        "sigla": "DF",
        "tipo": "ENTE_FEDERATIVO",
        "poder": "Governo Distrital",
        "esfera": "Distrital",
        "nivel_federativo": "Distrito Federal",
        "natureza_juridica": "Pessoa Jurídica de Direito Público Interno com poderes híbridos estaduais e municipais",
        "descricao": "Unidade federativa autônoma com competências legislativas cumulativas estaduais e municipais, vedada sua divisão em Municípios (Art. 32 da CF/88).",
        "site_oficial": "https://www.df.gov.br",
        "codigo_externo": "DF",
        "relacoes": [
            {"destino": "BRASIL", "tipo": "COMPOSICAO", "descricao": "Ente federativo singular da República Federativa do Brasil"}
        ]
    },
    {
        "nome": "Municípios Brasileiros",
        "sigla": "Municípios",
        "tipo": "ENTE_FEDERATIVO",
        "poder": "Governos Municipais",
        "esfera": "Municipal",
        "nivel_federativo": "Municípios",
        "natureza_juridica": "Pessoas Jurídicas de Direito Público Interno",
        "descricao": "Mais de 5.500 municípios dotados de autonomia política, administrativa e financeira para assuntos de interesse local (Arts. 29 a 31 da CF/88).",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "MUNICIPIOS",
        "relacoes": [
            {"destino": "BRASIL", "tipo": "COMPOSICAO", "descricao": "Entes federativos de base territorial local"}
        ]
    },

    # ==================== UNIÃO: PODERES E ÓRGÃOS AUTÔNOMOS ====================
    {
        "nome": "Poder Legislativo da União",
        "sigla": "Legislativo Federal",
        "tipo": "PODER",
        "poder": "Legislativo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Poder da União",
        "descricao": "Exerce a função legislativa federal e a fiscalização contábil, financeira e orçamentária do Poder Executivo (Arts. 44 a 75 da CF/88).",
        "site_oficial": "https://www.congressonacional.leg.br",
        "codigo_externo": "PODER_LEG_FED",
        "relacoes": [
            {"destino": "UNIAO", "tipo": "COMPOSICAO", "descricao": "Poder constituído da União"}
        ]
    },
    {
        "nome": "Poder Executivo da União",
        "sigla": "Executivo Federal",
        "tipo": "PODER",
        "poder": "Executivo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Poder da União",
        "descricao": "Exercido pelo Presidente da República, auxiliado pelos Ministros de Estado, exercendo a administração e a chefia de Estado e de Governo (Arts. 76 a 91 da CF/88).",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "PODER_EXEC_FED",
        "relacoes": [
            {"destino": "UNIAO", "tipo": "COMPOSICAO", "descricao": "Poder constituído da União"}
        ]
    },
    {
        "nome": "Poder Judiciário da União",
        "sigla": "Judiciário Federal",
        "tipo": "PODER",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Poder da União",
        "descricao": "Tem por função precípua a jurisdição constitucional e a aplicação da lei federal, assegurando a ordem jurídica e os direitos fundamentais (Arts. 92 a 126 da CF/88).",
        "site_oficial": "https://www.stf.jus.br",
        "codigo_externo": "PODER_JUD_FED",
        "relacoes": [
            {"destino": "UNIAO", "tipo": "COMPOSICAO", "descricao": "Poder constituído da União"}
        ]
    },
    {
        "nome": "Funções Essenciais à Justiça e Órgãos de Controle da União",
        "sigla": "Órgãos Constitucionais Autônomos",
        "tipo": "PODER",
        "poder": "Instituição Autônoma / Controle",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Instituições Constitucionais Autônomas",
        "descricao": "Instituições permanentes com autonomia funcional, administrativa e financeira, independentes dos Três Poderes: Ministério Público da União, Defensoria Pública da União, Tribunal de Contas da União e Advocacia-Geral da União.",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "ORGAOS_AUTONOMOS_FED",
        "relacoes": [
            {"destino": "UNIAO", "tipo": "COMPOSICAO", "descricao": "Instituições autônomas e de controle vinculadas à ordem constitucional da União"}
        ]
    },

    # ==================== LEGISLATIVO FEDERAL ====================
    {
        "nome": "Congresso Nacional",
        "sigla": "CN",
        "tipo": "CASA_LEGISLATIVA",
        "poder": "Legislativo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgão Constitucional Bicameral",
        "descricao": "Órgão bicameral composto pela Câmara dos Deputados (representantes do povo) e pelo Senado Federal (representantes dos Estados e do DF).",
        "site_oficial": "https://www.congressonacional.leg.br",
        "codigo_externo": "CONGRESSO_NACIONAL",
        "relacoes": [
            {"destino": "PODER_LEG_FED", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Órgão máximo do Poder Legislativo da União"}
        ]
    },
    {
        "nome": "Câmara dos Deputados",
        "sigla": "CD",
        "tipo": "CASA_LEGISLATIVA",
        "poder": "Legislativo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Casa Parlamentar Popular",
        "descricao": "Composta por 513 deputados federais eleitos pelo sistema proporcional para mandatos de 4 anos. Fonte primária integrada nesta plataforma.",
        "site_oficial": "https://www.camara.leg.br",
        "codigo_externo": "CAMARA_DEPUTADOS",
        "relacoes": [
            {"destino": "CONGRESSO_NACIONAL", "tipo": "COMPOSICAO", "descricao": "Ramo popular do parlamento bicameral federal"}
        ]
    },
    {
        "nome": "Senado Federal",
        "sigla": "SF",
        "tipo": "CASA_LEGISLATIVA",
        "poder": "Legislativo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Casa Parlamentar Federativa",
        "descricao": "Composto por 81 senadores (3 por Estado e DF) eleitos pelo sistema majoritário para mandatos de 8 anos. (Integração de dados planejada para etapas futuras).",
        "site_oficial": "https://www.senado.leg.br",
        "codigo_externo": "SENADO_FEDERAL",
        "relacoes": [
            {"destino": "CONGRESSO_NACIONAL", "tipo": "COMPOSICAO", "descricao": "Ramo federativo do parlamento bicameral federal"}
        ]
    },

    # ==================== CONTROLE E FISCALIZAÇÃO DO LEGISLATIVO ====================
    {
        "nome": "Tribunal de Contas da União",
        "sigla": "TCU",
        "tipo": "ORGAO_CONTROLE",
        "poder": "Instituição Autônoma / Controle",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Tribunal Administrativo de Controle Externo",
        "descricao": "Auxilia o Congresso Nacional na fiscalização contábil, financeira, orçamentária, operacional e patrimonial da União e das entidades da administração direta e indireta (Art. 71 CF/88).",
        "site_oficial": "https://portal.tcu.gov.br",
        "codigo_externo": "TCU",
        "relacoes": [
            {"destino": "ORGAOS_AUTONOMOS_FED", "tipo": "COMPOSICAO", "descricao": "Órgão autônomo com garantia constitucional de independência"},
            {"destino": "CONGRESSO_NACIONAL", "tipo": "CONTROLE", "descricao": "Auxilia o Congresso Nacional no exercício do controle externo"},
            {"destino": "PODER_EXEC_FED", "tipo": "FISCALIZACAO", "descricao": "Fiscaliza as contas e contratos do Poder Executivo federal"}
        ]
    },

    # ==================== FUNÇÕES ESSENCIAIS À JUSTIÇA ====================
    {
        "nome": "Ministério Público da União",
        "sigla": "MPU",
        "tipo": "ORGAO_AUTONOMO",
        "poder": "Instituição Autônoma / Controle",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Instituição Constitucional Permanente",
        "descricao": "Instituição permanente essencial à função jurisdicional do Estado, incumbindo-lhe a defesa da ordem jurídica, do regime democrático e dos interesses sociais e individuais indisponíveis. Compreende o MPF, MPT, MPM e MPDFT.",
        "site_oficial": "https://www.mpu.mp.br",
        "codigo_externo": "MPU",
        "relacoes": [
            {"destino": "ORGAOS_AUTONOMOS_FED", "tipo": "COMPOSICAO", "descricao": "Instituição permanente e autônoma"}
        ]
    },
    {
        "nome": "Procuradoria-Geral da República / Ministério Público Federal",
        "sigla": "PGR / MPF",
        "tipo": "ORGAO_AUTONOMO",
        "poder": "Instituição Autônoma / Controle",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Chefia do Ministério Público da União",
        "descricao": "Chefiada pelo Procurador-Geral da República, nomeado pelo Presidente da República após aprovação do Senado Federal.",
        "site_oficial": "https://www.mpf.mp.br",
        "codigo_externo": "PGR_MPF",
        "relacoes": [
            {"destino": "MPU", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Ramo do MPU e órgão de cúpula"}
        ]
    },
    {
        "nome": "Advocacia-Geral da União",
        "sigla": "AGU",
        "tipo": "ORGAO_AUTONOMO",
        "poder": "Instituição Autônoma / Controle",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Instituição Representativa Judicial da União",
        "descricao": "Instituição que representa judicial e extrajudicialmente a União, prestando consultoria e assessoramento jurídico ao Poder Executivo (Art. 131 da CF/88).",
        "site_oficial": "https://www.gov.br/agu",
        "codigo_externo": "AGU",
        "relacoes": [
            {"destino": "ORGAOS_AUTONOMOS_FED", "tipo": "COMPOSICAO", "descricao": "Função essencial à Justiça em âmbito federal"}
        ]
    },
    {
        "nome": "Defensoria Pública da União",
        "sigla": "DPU",
        "tipo": "ORGAO_AUTONOMO",
        "poder": "Instituição Autônoma / Controle",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Instituição Constitucional Permanente",
        "descricao": "Instituição permanente dotada de autonomia funcional e administrativa, com a incumbência de prestar orientação jurídica e defesa integral e gratuita aos necessitados (Art. 134 CF/88).",
        "site_oficial": "https://www.dpu.def.br",
        "codigo_externo": "DPU",
        "relacoes": [
            {"destino": "ORGAOS_AUTONOMOS_FED", "tipo": "COMPOSICAO", "descricao": "Função essencial à Justiça em âmbito federal"}
        ]
    },

    # ==================== JUDICIÁRIO FEDERAL ====================
    {
        "nome": "Supremo Tribunal Federal",
        "sigla": "STF",
        "tipo": "TRIBUNAL",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Corte Constitucional de Cúpula",
        "descricao": "Órgão de cúpula do Poder Judiciário brasileiro, ao qual compete precipuamente a guarda da Constituição Federal (Art. 102 da CF/88). Composto por 11 ministros.",
        "site_oficial": "https://portal.stf.jus.br",
        "codigo_externo": "STF",
        "relacoes": [
            {"destino": "PODER_JUD_FED", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Instância máxima do Judiciário nacional"}
        ]
    },
    {
        "nome": "Conselho Nacional de Justiça",
        "sigla": "CNJ",
        "tipo": "ORGAO_CONTROLE",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgão de Controle Administrativo e Financeiro do Judiciário",
        "descricao": "Compete o controle da atuação administrativa e financeira do Poder Judiciário e do cumprimento dos deveres funcionais dos juízes (Art. 103-B da CF/88). Presidido pelo Presidente do STF.",
        "site_oficial": "https://www.cnj.jus.br",
        "codigo_externo": "CNJ",
        "relacoes": [
            {"destino": "PODER_JUD_FED", "tipo": "CONTROLE", "descricao": "Controle administrativo e disciplinar dos órgãos judiciários"}
        ]
    },
    {
        "nome": "Superior Tribunal de Justiça",
        "sigla": "STJ",
        "tipo": "TRIBUNAL",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Corte Superior de Uniformização Infraconstitucional",
        "descricao": "Corte responsável por uniformizar a interpretação da lei federal em todo o Brasil (Art. 105 da CF/88). Composto por 33 ministros.",
        "site_oficial": "https://www.stj.jus.br",
        "codigo_externo": "STJ",
        "relacoes": [
            {"destino": "PODER_JUD_FED", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Corte superior de justiça federal e estadual comum"}
        ]
    },
    {
        "nome": "Tribunais Regionais Federais",
        "sigla": "TRFs (1ª a 6ª Regiões)",
        "tipo": "TRIBUNAL",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgãos de 2ª Instância da Justiça Federal Comum",
        "descricao": "Responsáveis pelo julgamento de recursos e ações contra a União, autarquias federais e empresas públicas nas respectivas regiões territoriais.",
        "site_oficial": "https://www.cjf.jus.br",
        "codigo_externo": "TRFS",
        "relacoes": [
            {"destino": "STJ", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Subordinados jurisdicionalmente ao STJ em matéria federal"}
        ]
    },
    {
        "nome": "Tribunal Superior Eleitoral",
        "sigla": "TSE",
        "tipo": "TRIBUNAL",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgão Superior da Justiça Eleitoral",
        "descricao": "Instância jurídica máxima da Justiça Eleitoral brasileira, responsável pela organização, fiscalização e julgamento dos pleitos eleitorais.",
        "site_oficial": "https://www.tse.jus.br",
        "codigo_externo": "TSE",
        "relacoes": [
            {"destino": "PODER_JUD_FED", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Órgão de cúpula do ramo eleitoral especializado"}
        ]
    },
    {
        "nome": "Tribunal Superior do Trabalho",
        "sigla": "TST",
        "tipo": "TRIBUNAL",
        "poder": "Judiciário",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgão Superior da Justiça do Trabalho",
        "descricao": "Instância máxima da Justiça do Trabalho brasileira em matéria laboral e dissídios coletivos.",
        "site_oficial": "https://www.tst.jus.br",
        "codigo_externo": "TST",
        "relacoes": [
            {"destino": "PODER_JUD_FED", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Órgão de cúpula do ramo laboral especializado"}
        ]
    },

    # ==================== EXECUTIVO FEDERAL (BASE PRESIDENCIAL) ====================
    {
        "nome": "Presidência da República",
        "sigla": "PR",
        "tipo": "ORGAO",
        "poder": "Executivo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgão Superior da Administração Direta Federal",
        "descricao": "Órgão máximo do Poder Executivo federal, sob a chefia do Presidente da República, que acumula as funções de Chefe de Estado e Chefe de Governo.",
        "site_oficial": "https://www.gov.br/planalto",
        "codigo_externo": "PRESIDENCIA_REPUBLICA",
        "relacoes": [
            {"destino": "PODER_EXEC_FED", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Chefia suprema do Poder Executivo da União"}
        ]
    },
    {
        "nome": "Casa Civil da Presidência da República",
        "sigla": "CC-PR",
        "tipo": "MINISTERIO",
        "poder": "Executivo",
        "esfera": "Federal",
        "nivel_federativo": "União",
        "natureza_juridica": "Órgão Essencial da Presidência da República",
        "descricao": "Responsável pela coordenação e integração das ações governamentais, análise de propostas legislativas e gestão de políticas prioritárias.",
        "site_oficial": "https://www.gov.br/casacivil",
        "codigo_externo": "CASA_CIVIL",
        "relacoes": [
            {"destino": "PRESIDENCIA_REPUBLICA", "tipo": "HIERARQUIA_ADMINISTRATIVA", "descricao": "Órgão de assessoramento direto da Presidência"}
        ]
    },

    # ==================== ESTADOS DA FEDERAÇÃO ====================
    {
        "nome": "Poder Executivo Estadual",
        "sigla": "Governos Estaduais",
        "tipo": "PODER",
        "poder": "Executivo",
        "esfera": "Estadual",
        "nivel_federativo": "Estados",
        "natureza_juridica": "Poder Estadual",
        "descricao": "Exercido pelo Governador do Estado com auxílio dos Secretários de Estado. Responsável pela segurança pública estadual, saúde e educação de nível médio.",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "EXEC_ESTADUAL",
        "relacoes": [
            {"destino": "ESTADOS", "tipo": "COMPOSICAO", "descricao": "Poder constituído dos Estados"}
        ]
    },
    {
        "nome": "Poder Legislativo Estadual",
        "sigla": "Assembleias Legislativas",
        "tipo": "PODER",
        "poder": "Legislativo",
        "esfera": "Estadual",
        "nivel_federativo": "Estados",
        "natureza_juridica": "Casas Parlamentares Estaduais Unicamerais",
        "descricao": "Exercido pelas Assembleias Legislativas estaduais, integradas por Deputados Estaduais eleitos pelo sistema proporcional para 4 anos.",
        "site_oficial": "https://www.unale.org.br",
        "codigo_externo": "LEG_ESTADUAL",
        "relacoes": [
            {"destino": "ESTADOS", "tipo": "COMPOSICAO", "descricao": "Poder constituído dos Estados"}
        ]
    },
    {
        "nome": "Poder Judiciário Estadual",
        "sigla": "Tribunais de Justiça (TJs)",
        "tipo": "PODER",
        "poder": "Judiciário",
        "esfera": "Estadual",
        "nivel_federativo": "Estados",
        "natureza_juridica": "Órgãos de Justiça Comum Estadual",
        "descricao": "Composto pelos 26 Tribunais de Justiça e seus juízos de 1º grau, com competência residual ampla (cível, criminal, família etc.).",
        "site_oficial": "https://www.cnj.jus.br",
        "codigo_externo": "JUD_ESTADUAL",
        "relacoes": [
            {"destino": "ESTADOS", "tipo": "COMPOSICAO", "descricao": "Poder constituído dos Estados"}
        ]
    },

    # ==================== MUNICÍPIOS (ATENÇÃO: SEM JUDICIÁRIO MUNICIPAL) ====================
    {
        "nome": "Poder Executivo Municipal",
        "sigla": "Prefeituras Municipais",
        "tipo": "PODER",
        "poder": "Executivo",
        "esfera": "Municipal",
        "nivel_federativo": "Municípios",
        "natureza_juridica": "Administração Pública Municipal Direta",
        "descricao": "Chefiado pelo Prefeito Municipal, auxiliado pelos Secretários Municipais, responsável pela gestão dos serviços públicos locais (transporte, saneamento, educação infantil, atenção básica de saúde).",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "EXEC_MUNICIPAL",
        "relacoes": [
            {"destino": "MUNICIPIOS", "tipo": "COMPOSICAO", "descricao": "Poder constituído dos Municípios"}
        ]
    },
    {
        "nome": "Poder Legislativo Municipal",
        "sigla": "Câmaras de Vereadores",
        "tipo": "PODER",
        "poder": "Legislativo",
        "esfera": "Municipal",
        "nivel_federativo": "Municípios",
        "natureza_juridica": "Casas Parlamentares Municipais Unicamerais",
        "descricao": "Composto pelos Vereadores eleitos diretamente pelo povo, com competência para legislar sobre assuntos de interesse local e fiscalizar as contas do Prefeito.",
        "site_oficial": "https://www.gov.br",
        "codigo_externo": "LEG_MUNICIPAL",
        "relacoes": [
            {"destino": "MUNICIPIOS", "tipo": "COMPOSICAO", "descricao": "Poder constituído dos Municípios"}
        ]
    },
    {
        "nome": "Poder Judiciário Municipal (Inexistente no Ordenamento Brasileiro)",
        "sigla": "Não existe Judiciário Municipal",
        "tipo": "NOTA_CONSTITUCIONAL",
        "poder": "Esclarecimento Didático",
        "esfera": "Municipal",
        "nivel_federativo": "Municípios",
        "natureza_juridica": "Nota de Esclarecimento Constitucional",
        "descricao": "Conforme a Constituição da República de 1988 (Art. 92), NÃO EXISTE Poder Judiciário no âmbito municipal. A prestação jurisdicional nos municípios é realizada pelo Poder Judiciário Estadual (Justiça Estadual) ou pela Justiça Federal nas comarcas/subseções judiciárias correspondentes.",
        "site_oficial": "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
        "codigo_externo": "JUD_MUNICIPAL_NOTA",
        "relacoes": [
            {"destino": "MUNICIPIOS", "tipo": "COMPOSICAO", "descricao": "Nota explicativa: a jurisdição nos municípios é suprida pela Justiça Estadual ou Federal"}
        ]
    }
]


class EstruturaService:
    """Serviço responsável por gerar e sincronizar a estrutura canônica constitucional do Estado brasileiro."""

    def sync_estrutura_canonica(self, db: Session) -> int:
        """Sincroniza os nós estruturais canônicos e suas relações no banco de dados."""
        logger.info("Sincronizando estrutura institucional canônica...")
        instituicoes_map = {}

        # 1. Cria ou atualiza as instituições canônicas
        for item in ESTRUTURA_CANONICA:
            cod = item["codigo_externo"]
            inst = db.query(Instituicao).filter(Instituicao.codigo_externo == cod).first()
            if not inst:
                inst = Instituicao(
                    nome=item["nome"],
                    sigla=item.get("sigla"),
                    tipo=item["tipo"],
                    poder=item["poder"],
                    esfera=item["esfera"],
                    nivel_federativo=item["nivel_federativo"],
                    codigo_externo=cod,
                    natureza_juridica=item.get("natureza_juridica"),
                    descricao=item.get("descricao"),
                    site_oficial=item.get("site_oficial"),
                    fonte="Constituição Federal de 1988 / Estrutura Canônica",
                    url_fonte=item.get("site_oficial"),
                    ativo=True
                )
                db.add(inst)
            else:
                inst.nome = item["nome"]
                inst.sigla = item.get("sigla")
                inst.tipo = item["tipo"]
                inst.poder = item["poder"]
                inst.esfera = item["esfera"]
                inst.nivel_federativo = item["nivel_federativo"]
                inst.natureza_juridica = item.get("natureza_juridica")
                inst.descricao = item.get("descricao")
                inst.site_oficial = item.get("site_oficial")
                inst.updated_at = utc_now()

            db.flush()
            instituicoes_map[cod] = inst

        # 2. Cria as relações institucionais
        for item in ESTRUTURA_CANONICA:
            origem_inst = instituicoes_map.get(item["codigo_externo"])
            if not origem_inst:
                continue

            for rel_data in item.get("relacoes", []):
                destino_inst = instituicoes_map.get(rel_data["destino"])
                if not destino_inst:
                    continue

                tipo_rel = rel_data["tipo"]
                desc_rel = rel_data.get("descricao")

                rel = db.query(RelacaoInstitucional).filter(
                    RelacaoInstitucional.instituicao_origem_id == origem_inst.id,
                    RelacaoInstitucional.instituicao_destino_id == destino_inst.id,
                    RelacaoInstitucional.tipo_relacao == tipo_rel
                ).first()

                if not rel:
                    rel = RelacaoInstitucional(
                        instituicao_origem_id=origem_inst.id,
                        instituicao_destino_id=destino_inst.id,
                        tipo_relacao=tipo_rel,
                        descricao=desc_rel,
                        fonte="CF/88"
                    )
                    db.add(rel)

        db.commit()
        logger.info(f"{len(instituicoes_map)} instituições canônicas sincronizadas.")
        return len(instituicoes_map)
