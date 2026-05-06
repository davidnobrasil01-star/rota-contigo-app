# ══════════════════════════════════════════════════════════════════════════════
# Rota Contigo — Gerador Interativo de Contrato
# Para rodar:  streamlit run gerar_contrato_app.py
# Acesso pelo celular (mesma rede Wi-Fi):  http://<IP-do-computador>:8501
# ══════════════════════════════════════════════════════════════════════════════

import io
import os
import requests
import streamlit as st
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                HRFlowable, Table, TableStyle,
                                Image as RLImage, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ── Token Autentique ──────────────────────────────────────────────────────────
# Prioridade: (1) .env local, (2) Streamlit Secrets (nuvem), (3) campo manual
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(_env_path, override=False)
except ImportError:
    pass  # python-dotenv não instalado

AUTENTIQUE_TOKEN_ENV = os.environ.get("AUTENTIQUE_TOKEN", "")

# Fallback: Streamlit Secrets (usado no Streamlit Cloud)
if not AUTENTIQUE_TOKEN_ENV:
    try:
        AUTENTIQUE_TOKEN_ENV = st.secrets.get("AUTENTIQUE_TOKEN", "")
    except Exception:
        pass

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

# ── Cores ──────────────────────────────────────────────────────────────────
VERDE  = colors.HexColor("#1a5c38")
VCLARO = colors.HexColor("#e8f5ee")
CINZA  = colors.HexColor("#555555")

_styles = getSampleStyleSheet()

def E(nome, **kw):
    base = kw.pop("parent", _styles["Normal"])
    return ParagraphStyle(nome, parent=base, **kw)

SECAO   = E("secao",   fontSize=11, textColor=VERDE,         alignment=TA_CENTER,  fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2)
CL_TIT  = E("cl_tit",  fontSize=10, textColor=VERDE,         alignment=TA_LEFT,    fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=1)
CORPO   = E("corpo",   fontSize=9.5, textColor=colors.black, alignment=TA_JUSTIFY, fontName="Helvetica",      leading=13, spaceBefore=1, spaceAfter=2)
CAMPO   = E("campo",   fontSize=9.5, textColor=colors.black, alignment=TA_LEFT,    fontName="Helvetica",      leading=13, spaceBefore=1, spaceAfter=1)
RODAPE  = E("rodape",  fontSize=7.5, textColor=CINZA,         alignment=TA_CENTER,  fontName="Helvetica-Oblique")
BADGE   = E("badge",   fontSize=8,   textColor=colors.white,  alignment=TA_CENTER,  fontName="Helvetica-Bold")
ATENCAO = E("atencao", fontSize=9.5, textColor=colors.HexColor("#7a0000"),
            alignment=TA_JUSTIFY, fontName="Helvetica-Bold", leading=14)

def hr(cor=VERDE, esp=1):
    return HRFlowable(width="100%", thickness=esp, color=cor, spaceAfter=3, spaceBefore=3)

def sp(h=4):
    return Spacer(1, h)

MESES_PT = ["janeiro","fevereiro","março","abril","maio","junho",
            "julho","agosto","setembro","outubro","novembro","dezembro"]

def fmt_data(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}/{d.year}"

def data_extenso(d: date) -> str:
    return f"{d.day} de {MESES_PT[d.month-1]} de {d.year}"

def fmt_valor(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO DO PDF
# ══════════════════════════════════════════════════════════════════════════════

def gerar_pdf(d: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []
    story.append(sp(2))

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    try:
        logo = RLImage(LOGO_PATH, width=5*cm, height=2*cm)
    except Exception:
        logo = Paragraph("[ ROTA CONTIGO ]", BADGE)

    cab_st = E("cab", fontSize=13, textColor=VERDE, fontName="Helvetica-Bold",
               alignment=TA_LEFT, leading=13)
    cab_dados = Paragraph(
        "<b>ROTA CONTIGO</b><br/>"
        "<font size='8'>AGENCIA DE VIAGENS E TURISMO LTDA</font><br/>"
        "<font size='7.5' color='#555555'>CNPJ: 65.050.169/0001-00 | CADASTUR: 65.050.169/0001-00</font><br/>"
        "<font size='7.5' color='#555555'>Curitiba – PR | Atendimento exclusivamente digital</font><br/>"
        "<font size='7.5' color='#555555'>(41) 99819-5099 | rotacontigoturismo@gmail.com</font>",
        cab_st)

    cab_t = Table([[cab_dados, logo]], colWidths=[11.5*cm, 4.5*cm])
    cab_t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (1,0), (1,0),  "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(cab_t)
    story.append(sp(3))
    story.append(hr(VERDE, 2))
    story.append(sp(2))

    badge_t = Table(
        [["  CADASTUR REGULAR  |  Validade: 10/02/2026 a 10/02/2028  |  www.cadastur.turismo.gov.br"]],
        colWidths=[16*cm])
    badge_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), VERDE),
        ("TEXTCOLOR",     (0,0), (-1,-1), colors.white),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(badge_t)
    story.append(sp(3))

    story.append(Paragraph("CONTRATO DE PRESTAÇÃO DE SERVIÇOS TURÍSTICOS", SECAO))
    story.append(hr(VERDE, 0.5))

    # ── Condições Gerais ───────────────────────────────────────────────────
    story.append(Paragraph("CONDIÇÕES GERAIS", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))
    story.append(Paragraph(
        "<b>01 – NOSSO PACOTE:</b> A duração dos passeios e programações dependem do "
        "cronograma da viagem, entregue ao titular no ato da contratação.", CORPO))
    story.append(Paragraph(
        "<b>02 – ALIMENTAÇÃO:</b> A inclusão de refeições (café da manhã, almoço e/ou "
        "jantar) é definida individualmente por excursão e indicada na tabela "
        "<b>SERVIÇOS INCLUSOS</b> deste contrato. Despesas não incluídas no pacote são "
        "de inteira responsabilidade do CONTRATANTE.", CORPO))
    story.append(Paragraph(
        "<b>03 – O PREÇO NÃO INCLUI (salvo indicação contrária):</b> Refeições em paradas, "
        "diárias adicionais, telefonemas, bebidas, taxas em museus, ingressos não listados "
        "no pacote e quaisquer outras despesas de caráter pessoal.", CORPO))

    # ── Cláusula 1 ─────────────────────────────────────────────────────────
    story.append(Paragraph("Cláusula 1ª – DO OBJETO E DAS PARTES", CL_TIT))
    story.append(Paragraph(
        "O presente contrato tem como objeto a prestação de serviços turísticos pela "
        "<b>ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA</b>, inscrita no CNPJ/CADASTUR "
        "sob nº <b>65.050.169/0001-00</b>, com sede em Curitiba – PR, operando "
        "exclusivamente de forma digital, e-mail: rotacontigoturismo@gmail.com, "
        "telefone: (41) 99819-5099, doravante denominada <b>CONTRATADA</b>, "
        "ao(à) <b>CONTRATANTE</b> identificado(a) abaixo:", CORPO))

    story.append(sp(2))
    story.append(Paragraph("<b>DADOS DO(A) CONTRATANTE / TITULAR RESPONSÁVEL:</b>", CAMPO))
    story.append(Paragraph(f"Nome completo: <b>{d['nome']}</b>", CAMPO))
    story.append(Paragraph(f"Data de Nascimento: <b>{fmt_data(d['nascimento'])}</b>", CAMPO))
    story.append(Paragraph(f"CPF: <b>{d['cpf']}</b>    RG: <b>{d['rg']}</b>", CAMPO))
    story.append(Paragraph(f"Celular/WhatsApp: <b>{d['celular']}</b>", CAMPO))
    story.append(Paragraph(f"E-mail: <b>{d['email']}</b>", CAMPO))
    story.append(Paragraph(f"Em caso de emergência avisar: <b>{d['emergencia']}</b>", CAMPO))
    story.append(sp(3))

    # ── Tabela de participantes (se houver grupo/família) ──────────────────
    todos = [{"nome": d['nome'], "tipo": "Adulto", "idade": "-", "titular": True}]
    for p in d.get('participantes_extras', []):
        if p['nome'].strip():
            todos.append({"nome": p['nome'], "tipo": p['tipo'],
                          "idade": str(p['idade']), "titular": False})

    if len(todos) > 1:
        n_adultos = sum(1 for p in todos if p['tipo'] == "Adulto")
        n_menores = sum(1 for p in todos if p['tipo'] == "Menor")

        part_rows = [["#", "Nome do Participante", "Tipo", "Idade"]]
        for i, p in enumerate(todos, 1):
            titular_label = " (Titular)" if p['titular'] else ""
            part_rows.append([
                str(i),
                p['nome'] + titular_label,
                p['tipo'],
                p['idade'],
            ])
        part_rows.append([
            "", f"TOTAL: {len(todos)} pessoa(s)",
            f"{n_adultos} adulto(s)",
            f"{n_menores} menor(es)",
        ])

        t_part = Table(part_rows, colWidths=[1*cm, 9*cm, 3*cm, 2.5*cm])
        t_part.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("ALIGN",         (1,0), (1,-1), "LEFT"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0,1), (-1,-2), [VCLARO, colors.white]),
            ("BACKGROUND",    (0,-1), (-1,-1), colors.HexColor("#d4edda")),
            ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
            ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ]))

        story.append(KeepTogether([
            Paragraph("<b>PARTICIPANTES DA EXCURSÃO:</b>", CAMPO),
            sp(2),
            t_part,
            sp(2),
            Paragraph(
                "<b>Nota:</b> O CONTRATANTE/Titular assina em nome próprio e como "
                "responsável legal por todos os participantes menores de 18 anos "
                "listados acima, declarando ciência e aceite de todos os termos "
                "deste contrato em nome de todos.", CORPO),
        ]))
        story.append(sp(3))

    # ── Tabela de Serviços ─────────────────────────────────────────────────
    serv_rows = [["Serviço", "Incluso", "Não Incluso", "Observação"]]
    for nome_s, info in d['servicos'].items():
        inc   = "✓" if info['incluso'] else ""
        n_inc = "✗" if not info['incluso'] else ""
        serv_rows.append([nome_s, inc, n_inc, info.get('obs', '')])

    t_serv = Table(serv_rows, colWidths=[5.5*cm, 2.1*cm, 2.5*cm, 5.4*cm])
    t_serv.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), VERDE),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("ALIGN",         (0,1), (0,-1), "LEFT"),
        ("ALIGN",         (3,0), (3,-1), "LEFT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [VCLARO, colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("TEXTCOLOR",     (1,1), (1,-1), colors.HexColor("#1a5c38")),
        ("FONTNAME",      (1,1), (1,-1), "Helvetica-Bold"),
        ("TEXTCOLOR",     (2,1), (2,-1), colors.HexColor("#cc0000")),
        ("FONTNAME",      (2,1), (2,-1), "Helvetica-Bold"),
    ]))

    story.append(KeepTogether([
        Paragraph("<b>SERVIÇOS INCLUSOS NESTA EXCURSÃO:</b>", CAMPO),
        sp(2),
        t_serv,
        sp(3),
        Paragraph(
            "<b>⚠ OBSERVAÇÃO:</b> A falta de documento original com foto e/ou não "
            "comparecimento no local e horário de embarque será tratado como desistência, "
            "isentando a CONTRATADA de qualquer reembolso.", ATENCAO),
    ]))

    # ── Obrigações da Contratada ───────────────────────────────────────────
    story.append(Paragraph("OBRIGAÇÕES DA CONTRATADA", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))

    story.append(Paragraph("Cláusula 2ª – DOS SERVIÇOS", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA compromete-se a prestar seus serviços com qualidade, segurança e "
        "pontualidade, em conformidade com o Código de Defesa do Consumidor "
        "(Lei nº 8.078/1990), a Lei Geral do Turismo (Lei nº 11.771/2008) e demais "
        "normas aplicáveis.", CORPO))

    story.append(Paragraph("Cláusula 3ª – DOS VEÍCULOS E TRANSPORTE", CL_TIT))
    story.append(Paragraph(
        "O veículo adotado seguirá critério baseado no número de participantes confirmados:",
        CORPO))
    for item in [
        "a) A partir de 15 participantes: Van Executiva;",
        "b) A partir de 25 participantes: Micro-Ônibus Executivo;",
        "c) A partir de 38 participantes: Ônibus Executivo;",
        "d) Não atingido o mínimo: devolução total ou crédito para outra excursão, "
        "a critério do CONTRATANTE.",
    ]:
        story.append(Paragraph(item, CAMPO))

    story.append(Paragraph("Cláusula 4ª – DA RESPONSABILIDADE", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA é responsável pela organização e execução da excursão, bem como "
        "pela restituição de valores nos casos previstos neste contrato, nos termos do "
        "art. 14 do CDC.", CORPO))

    story.append(Paragraph("Cláusula 5ª – DOS EMBARQUES", CL_TIT))
    story.append(Paragraph(
        "Horários e locais de embarque serão comunicados ao CONTRATANTE via WhatsApp "
        "e/ou redes sociais da CONTRATADA na semana anterior ao evento.", CORPO))

    story.append(Paragraph("Cláusula 6ª – DA IMPOSSIBILIDADE DE REALIZAÇÃO", CL_TIT))
    story.append(Paragraph(
        "Em caso de cancelamento por força maior, decreto governamental, interdição do "
        "destino ou número insuficiente de participantes, a CONTRATADA poderá:", CORPO))
    for item in [
        "a) Remarcar a viagem para nova data acordada entre as partes;",
        "b) Disponibilizar crédito equivalente para outro destino;",
        "c) Restituir o valor pago:",
        "    – Pix / transferência: devolução integral;",
        "    – Cartão de crédito/débito: devolução conforme política de estorno da "
        "operadora do cartão, sem acréscimo adicional pela CONTRATADA.",
    ]:
        story.append(Paragraph(item, CAMPO))
    story.append(Paragraph(
        "A restituição ocorrerá em até <b>30 (trinta) dias corridos</b> após a confirmação "
        "do cancelamento, conforme art. 49 do CDC.", CORPO))

    story.append(Paragraph("Cláusula 7ª – DA CONDUTA DO PARTICIPANTE, EXCLUSÃO E PENALIDADES", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA zelará pelo bem-estar, segurança e harmonia de todos os integrantes "
        "da excursão. Poderão ser aplicadas penalidades ao CONTRATANTE que apresentar as "
        "seguintes condutas inadequadas:", CORPO))
    for item in [
        "a) Apresentar-se em estado de embriaguez ou sob efeito de substâncias psicoativas "
        "que comprometam sua conduta ou a segurança do grupo;",
        "b) Praticar atos de violência física ou verbal contra demais participantes, guias, "
        "motoristas ou prepostos da CONTRATADA;",
        "c) Desrespeitar as normas de segurança estabelecidas para o destino, transporte "
        "ou atrações;",
        "d) Causar danos ao patrimônio de terceiros, estabelecimentos, atrativos turísticos "
        "ou ao veículo utilizado pela CONTRATADA;",
        "e) Praticar atos que atentem contra a dignidade, a moral ou os bons costumes, "
        "prejudicando a experiência dos demais participantes.",
    ]:
        story.append(Paragraph(item, CAMPO))
    story.append(Paragraph(
        "<b>§1º – Gradação das penalidades:</b> As infrações serão apuradas e sancionadas "
        "de forma proporcional à sua gravidade:", CORPO))
    for item in [
        "I – Advertência verbal, com registro pelo responsável da excursão;",
        "II – Restrição de participação em atividades específicas do roteiro;",
        "III – Exclusão imediata da excursão, nos casos de reincidência ou infração grave.",
    ]:
        story.append(Paragraph(item, CAMPO))
    story.append(Paragraph(
        "<b>§2º</b> – Em caso de exclusão, esta ocorrerá por <b>culpa exclusiva do "
        "CONTRATANTE</b>, nos termos do art. 14, §3º, II do CDC, não cabendo indenização "
        "à CONTRATADA. A CONTRATADA poderá reter, dos valores pagos, o montante "
        "correspondente aos <b>custos efetivamente incorridos e devidamente comprovados</b> "
        "até o momento da exclusão, conforme art. 475 do Código Civil.", CORPO))
    story.append(Paragraph(
        "<b>§3º</b> – As despesas decorrentes do retorno do participante excluído ao ponto "
        "de origem (transporte, hospedagem e correlatas) serão integralmente arcadas pelo "
        "próprio CONTRATANTE.", CORPO))
    story.append(Paragraph(
        "<b>§4º</b> – Ao CONTRATANTE são assegurados o contraditório e a ampla defesa, "
        "sendo admitidos como meio de prova registros fotográficos, audiovisuais, relatos "
        "de testemunhas e demais documentos pertinentes.", CORPO))
    story.append(Paragraph(
        "<b>§5º</b> – Em caso de danos a bens de terceiros ou ao veículo da CONTRATADA "
        "causados pelo CONTRATANTE excluído, este responderá pelos prejuízos apurados, "
        "independentemente das sanções previstas nesta cláusula.", CORPO))

    story.append(Paragraph("Cláusula 8ª – DO ROTEIRO", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA envidará esforços para o cumprimento integral do roteiro, ressalvadas "
        "situações de caso fortuito e força maior (art. 393 do Código Civil). Alterações de "
        "ordem ou conteúdo poderão ocorrer por motivos climáticos ou operacionais.", CORPO))
    story.append(Paragraph(
        "<b>§1º</b> – Na hipótese de supressão definitiva de serviço já incluso e pago "
        "(ingresso, refeição, atração), a CONTRATADA restituirá ao CONTRATANTE o valor "
        "correspondente ao item suprimido, de forma proporcional ao total contratado.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – Passeios, caminhadas e trilhas são opcionais. O CONTRATANTE poderá "
        "seguir roteiro próprio, desde que esteja no local de embarque no retorno.", CORPO))

    story.append(Paragraph("Cláusula 9ª – DA BAGAGEM E PERTENCES", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA não se responsabiliza por perda, roubo, dano ou extravio de bagagens, "
        "documentos ou objetos de valor durante a excursão, salvo dolo ou culpa grave "
        "comprovada de seus prepostos. Recomenda-se seguro de viagem individual "
        "(art. 14, §3º, III do CDC).", CORPO))

    # ── Valor e Pagamento ──────────────────────────────────────────────────
    story.append(Paragraph("DO VALOR E PAGAMENTO", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))

    story.append(Paragraph("Cláusula 10ª – DO VALOR E FORMA DE PAGAMENTO", CL_TIT))

    # Monta descrição de participantes para a cláusula
    extras = [p for p in d.get('participantes_extras', []) if p['nome'].strip()]
    total_pessoas = 1 + len(extras)
    if total_pessoas > 1:
        n_adultos = 1 + sum(1 for p in extras if p['tipo'] == "Adulto")
        n_menores = sum(1 for p in extras if p['tipo'] == "Menor")
        desc_pessoas = (f"<b>{total_pessoas} pessoas</b> "
                        f"({n_adultos} adulto(s) e {n_menores} menor(es))")
    else:
        desc_pessoas = "<b>1 (uma) pessoa</b>"

    story.append(Paragraph(
        f"O CONTRATANTE pagará à CONTRATADA o valor total de <b>R$ {d['valor_fmt']} "
        f"({d['valor_extenso']})</b>, referente ao pacote para {desc_pessoas} "
        f"com destino a <b>{d['destino']}</b>, com data de viagem prevista para "
        f"<b>{fmt_data(d['data_viagem'])}</b>.", CORPO))
    story.append(Paragraph(
        "Formas aceitas: Pix, transferência bancária ou cartão. O comprovante deve ser "
        "enviado via WhatsApp ou e-mail <b>rotacontigoturismo@gmail.com</b>, com nome "
        "completo e CPF.", CORPO))

    story.append(Paragraph("Cláusula 11ª – DA INADIMPLÊNCIA", CL_TIT))
    story.append(Paragraph(
        "O não pagamento no prazo acordado facultará à CONTRATADA a rescisão do contrato, "
        "após notificação ao CONTRATANTE com prazo mínimo de <b>48 (quarenta e oito) "
        "horas</b> para regularização, aplicando-se as regras de cancelamento previstas "
        "na Cláusula 15ª.", CORPO))

    # ── Rescisão ───────────────────────────────────────────────────────────
    story.append(Paragraph("DA RESCISÃO", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))

    story.append(Paragraph("Cláusula 12ª", CL_TIT))
    story.append(Paragraph(
        "O contrato poderá ser rescindido por qualquer das partes mediante comunicação "
        "formal por escrito (WhatsApp ou e-mail), observados os prazos deste instrumento.",
        CORPO))

    story.append(Paragraph("Cláusula 13ª", CL_TIT))
    story.append(Paragraph(
        "Rescisão por iniciativa da CONTRATADA, por motivos além dos previstos na "
        "Cláusula 6ª, ensejará restituição integral ao CONTRATANTE em até 30 dias.", CORPO))

    story.append(Paragraph("Cláusula 14ª", CL_TIT))
    story.append(Paragraph(
        "Valores pagos a título de ingressos já adquiridos não são restituídos pela "
        "CONTRATADA. O CONTRATANTE deverá buscar ressarcimento junto ao organizador "
        "do evento.", CORPO))

    # ── Política de Cancelamento ───────────────────────────────────────────
    story.append(Paragraph("POLÍTICA DE CANCELAMENTO DO CONTRATANTE", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))

    reemb = [
        ["Antecedência da desistência",                "% Restituído"],
        ["Mais de 31 dias antes da viagem",             "90% do valor pago"],
        ["De 21 a 30 dias antes da viagem",             "80% do valor pago"],
        ["De 11 a 20 dias antes da viagem",             "40% do valor pago"],
        ["10 dias ou menos antes da viagem",            "0% (sem restituição)"],
        ["Indicação de substituto (mín. 5 dias antes)", "100% – sem taxa adicional"],
    ]
    t_reemb = Table(reemb, colWidths=[10*cm, 5.5*cm])
    t_reemb.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), VERDE),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [VCLARO, colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(KeepTogether([
        Paragraph("Cláusula 15ª", CL_TIT),
        Paragraph(
            "Em caso de desistência pelo CONTRATANTE, aplicam-se os percentuais abaixo, "
            "conforme art. 49 do CDC e art. 413 do Código Civil:", CORPO),
        sp(4),
        t_reemb,
    ]))

    # ── LGPD ──────────────────────────────────────────────────────────────
    story.append(Paragraph("DA PROTEÇÃO DE DADOS PESSOAIS – LGPD", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))
    story.append(Paragraph("Cláusula 16ª", CL_TIT))
    story.append(Paragraph(
        "Em conformidade com a Lei nº 13.709/2018 (LGPD), a CONTRATADA compromete-se a:",
        CORPO))
    for item in [
        "a) Coletar apenas os dados estritamente necessários à execução dos serviços;",
        "b) Utilizar as informações exclusivamente para fins turísticos;",
        "c) Não compartilhar dados com terceiros sem consentimento expresso, salvo "
        "obrigação legal;",
        "d) Garantir segurança das informações com medidas técnicas e administrativas "
        "adequadas.",
    ]:
        story.append(Paragraph(item, CAMPO))

    # ── Disposições Gerais ─────────────────────────────────────────────────
    story.append(Paragraph("DISPOSIÇÕES GERAIS E VIGÊNCIA", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))

    story.append(Paragraph("Cláusula 17ª – DA VIGÊNCIA", CL_TIT))
    story.append(Paragraph(
        "Este contrato entra em vigor na data da assinatura ou confirmação do pagamento "
        "(o que ocorrer primeiro), e tem vigência até a conclusão dos serviços contratados.",
        CORPO))

    story.append(Paragraph("Cláusula 18ª – DO FORO", CL_TIT))
    story.append(Paragraph(
        "Fica eleito o foro da Comarca de <b>Curitiba – PR</b> para dirimir quaisquer "
        "controvérsias oriundas deste contrato, com renúncia a qualquer outro, por mais "
        "privilegiado que seja (art. 63 do CPC).", CORPO))

    story.append(Paragraph("Cláusula 19ª – DA VALIDADE DIGITAL", CL_TIT))
    story.append(Paragraph(
        "Este contrato tem plena validade jurídica em formato digital, nos termos da MP "
        "nº 2.200-2/2001, do Marco Civil da Internet (Lei nº 12.965/2014) e do CDC. "
        "Sua aceitação ocorre mediante confirmação de pagamento ou assinatura eletrônica.",
        CORPO))

    story.append(Paragraph("Cláusula 20ª – DA LEGISLAÇÃO APLICÁVEL", CL_TIT))
    story.append(Paragraph(
        "Este contrato é regido pelas seguintes normas: Código Civil (Lei 10.406/2002), "
        "Código de Defesa do Consumidor (Lei 8.078/1990), Lei Geral do Turismo "
        "(Lei 11.771/2008), art. 49 do CDC, art. 413 do CC e LGPD (Lei 13.709/2018).",
        CORPO))

    # ── Assinaturas ────────────────────────────────────────────────────────
    story.append(sp(14))
    story.append(hr(VERDE, 1))
    story.append(sp(12))

    ass_st = E("ass", fontSize=9, alignment=TA_CENTER, fontName="Helvetica", leading=14)
    ass_l = Paragraph(
        "________________________________________<br/>"
        "<b>ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA</b><br/>"
        "CNPJ/CADASTUR: 65.050.169/0001-00<br/>"
        "David Cortés Hernández – Sócio-Administrador<br/>"
        "Curitiba – PR | Agência Digital", ass_st)
    ass_r = Paragraph(
        "________________________________________<br/>"
        f"<b>{d['nome']}</b><br/>"
        f"CPF: {d['cpf']}", ass_st)

    t_ass = Table([[ass_l, ass_r]], colWidths=[8*cm, 8*cm])
    t_ass.setStyle(TableStyle([
        ("ALIGN",  (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(t_ass)
    story.append(sp(8))
    story.append(Paragraph(
        f"Curitiba – PR, {data_extenso(d['data_contrato'])}.",
        E("data", fontSize=9.5, alignment=TA_CENTER)))
    story.append(sp(8))
    story.append(hr(VERDE, 0.5))
    story.append(Paragraph(
        "ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA  |  CNPJ: 65.050.169/0001-00  |  "
        "CADASTUR Regular – Válido até 10/02/2028  |  rotacontigoturismo@gmail.com  |  "
        "(41) 99819-5099", RODAPE))

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO AUTENTIQUE
# ══════════════════════════════════════════════════════════════════════════════

def enviar_autentique(pdf_bytes: bytes, nome_cliente: str, email_cliente: str,
                      telefone_cliente: str, nome_arquivo: str, api_token: str,
                      via_whatsapp: bool, via_email: bool = True,
                      sandbox: bool = False) -> dict:
    """Envia o PDF para o Autentique e retorna link de assinatura."""

    # Normaliza telefone
    tel = ""
    if telefone_cliente:
        tel = "".join(filter(str.isdigit, telefone_cliente))
        if not tel.startswith("55"):
            tel = "55" + tel
        tel = "+" + tel

    # Monta signatário(s) do cliente
    signers_cliente = []
    if via_whatsapp and tel:
        signers_cliente.append(
            f'{{"name":"{nome_cliente}","email":"{email_cliente}",'
            f'"phone":"{tel}","delivery_method":"DELIVERY_METHOD_WHATSAPP",'
            f'"action":"SIGN"}}'
        )
    if via_email:
        signers_cliente.append(
            f'{{"name":"{nome_cliente}","email":"{email_cliente}",'
            f'"action":"SIGN"}}'
        )
    # Garante ao menos um signatário (fallback e-mail)
    if not signers_cliente:
        signers_cliente.append(
            f'{{"name":"{nome_cliente}","email":"{email_cliente}",'
            f'"action":"SIGN"}}'
        )
    signer_input = ",".join(signers_cliente)

    # Signatário da Rota Contigo (você assina também)
    signer_rota = (
        '{"name":"David Cortés – Rota Contigo",'
        '"email":"rotacontigoturismo@gmail.com","action":"SIGN"}'
    )

    query = """
    mutation CreateDocumentMutation(
      $document: DocumentInput!,
      $signers: [SignerInput!]!,
      $file: Upload!
    ) {
      createDocument(document: $document, signers: $signers, file: $file) {
        id
        name
        signatures {
          public_id
          name
          email
          link { short_link }
        }
      }
    }
    """

    operations = (
        '{"query":"' + query.replace("\n", "\\n").replace('"', '\\"') + '",'
        '"variables":{'
        '"document":{"name":"' + nome_arquivo.replace(".pdf", "") + '",'
        '"message":"Olá ' + nome_cliente.split()[0] + '! Segue o contrato da sua excursão com a Rota Contigo. Por favor, assine digitalmente clicando no botão abaixo."},'
        '"signers":[' + signer_input + ',' + signer_rota + '],'
        '"file":null}}'
    )

    payload = {
        "operations": operations,
        "map": '{"file": ["variables.file"]}',
    }
    files = [("file", (nome_arquivo, pdf_bytes, "application/pdf"))]
    headers = {"Authorization": f"Bearer {api_token}"}

    resp = requests.post(
        "https://api.autentique.com.br/v2/graphql",
        headers=headers,
        data=payload,
        files=files,
        timeout=30,
    )
    return resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Rota Contigo – Contrato",
    page_icon="🚌",
    layout="centered",
)

st.markdown(
    "<h2 style='color:#1a5c38;text-align:center'>🚌 Rota Contigo</h2>"
    "<p style='text-align:center;color:#777;margin-top:-10px'>"
    "Gerador de Contrato de Serviços Turísticos</p>",
    unsafe_allow_html=True,
)
st.divider()

with st.form("contrato_form"):

    # ── Dados do Contratante ──────────────────────────────────────────────
    st.markdown("### 👤 Dados do Contratante")

    nome = st.text_input("Nome completo *")

    col1, col2 = st.columns(2)
    with col1:
        nascimento = st.date_input(
            "Data de Nascimento *",
            value=date(1990, 1, 1),
            min_value=date(1920, 1, 1),
            max_value=date.today(),
        )
        cpf = st.text_input("CPF *", placeholder="000.000.000-00")
    with col2:
        rg = st.text_input("RG *")
        celular = st.text_input("Celular/WhatsApp *", placeholder="(41) 99999-9999")

    email      = st.text_input("E-mail *")
    emergencia = st.text_input(
        "Em caso de emergência avisar *",
        placeholder="Nome e telefone do contato")

    st.divider()

    # ── Participantes adicionais ──────────────────────────────────────────
    st.markdown("### 👨‍👩‍👧‍👦 Participantes Adicionais")
    st.caption("Se for uma família ou grupo, liste os demais participantes abaixo. O titular acima já está incluído automaticamente.")

    num_extras = st.number_input(
        "Quantos participantes adicionais? (além do titular)",
        min_value=0, max_value=20, value=0, step=1)

    participantes_extras = []
    if num_extras > 0:
        st.markdown("**Preencha os dados de cada participante:**")
        for i in range(int(num_extras)):
            st.markdown(f"*Participante {i+2}*")
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                p_nome = st.text_input("Nome", key=f"p_nome_{i}", placeholder="Nome completo")
            with col2:
                p_tipo = st.selectbox("Tipo", ["Adulto", "Menor"], key=f"p_tipo_{i}")
            with col3:
                p_idade = st.number_input("Idade", min_value=0, max_value=99, value=0, key=f"p_idade_{i}")
            participantes_extras.append({
                "nome":  p_nome,
                "tipo":  p_tipo,
                "idade": p_idade,
            })

    st.divider()

    # ── Dados da Excursão ─────────────────────────────────────────────────
    st.markdown("### 🗺️ Dados da Excursão")

    destino     = st.text_input("Destino *", placeholder="ex: Bonito – MS")
    data_viagem = st.date_input("Data da viagem *", min_value=date.today())

    col1, col2 = st.columns(2)
    with col1:
        valor_num = st.number_input(
            "Valor do pacote (R$) *", min_value=0.0, step=0.01, format="%.2f")
    with col2:
        valor_extenso = st.text_input(
            "Valor por extenso *",
            placeholder="ex: quinhentos reais")

    st.divider()

    # ── Serviços Inclusos ─────────────────────────────────────────────────
    st.markdown("### ✅ Serviços Inclusos")
    st.caption("Marque o que está incluso e adicione observações se necessário.")

    servicos_lista = [
        "Transporte (ônibus/van)",
        "Café da manhã",
        "Almoço",
        "Jantar",
        "Ingressos / Entradas",
        "Guia turístico",
        "Seguro de viagem",
    ]

    servicos_data = {}
    for s in servicos_lista:
        col1, col2 = st.columns([1, 2])
        with col1:
            inc = st.checkbox(s, key=f"inc_{s}")
        with col2:
            obs = st.text_input(
                "Observação", key=f"obs_{s}",
                label_visibility="collapsed",
                placeholder=f"Observação sobre {s.lower()}")
        servicos_data[s] = {"incluso": inc, "obs": obs}

    st.divider()

    # ── Data do Contrato ──────────────────────────────────────────────────
    st.markdown("### 📅 Data do Contrato")
    data_contrato = st.date_input("Data de assinatura *", value=date.today())

    st.divider()

    # ── Envio Autentique (opcional) ───────────────────────────────────────
    st.markdown("### ✍️ Assinatura Digital")
    usar_autentique = st.checkbox(
        "📲 Enviar para o cliente assinar pelo WhatsApp/e-mail (Autentique)",
        value=True
    )

    api_token    = ""
    via_whatsapp = False
    modo_sandbox = True  # ← SANDBOX ATIVO: troque para False quando quiser cobrar
    if usar_autentique:
        if AUTENTIQUE_TOKEN_ENV:
            st.success("🔑 Token Autentique carregado automaticamente")
            api_token = AUTENTIQUE_TOKEN_ENV
        else:
            api_token = st.text_input(
                "Token da API Autentique *",
                type="password",
                placeholder="Cole aqui seu token do painel Autentique",
                help="Painel Autentique → Configurações → API → Gerar Token"
            )
        st.markdown("**Como notificar o cliente?**")
        col_e, col_w = st.columns(2)
        with col_e:
            enviar_email     = st.toggle("📧 E-mail (R$0,013)", value=True)
        with col_w:
            enviar_whatsapp  = st.toggle("📱 WhatsApp (R$0,12)", value=False)

        via_whatsapp = enviar_whatsapp  # usado na função de envio

        if enviar_email and enviar_whatsapp:
            st.info("📧📱 Cliente receberá por e-mail e WhatsApp.")
        elif enviar_whatsapp:
            st.info("📱 Cliente receberá pelo WhatsApp.")
        elif enviar_email:
            st.info("📧 Cliente receberá por e-mail.")
        else:
            st.warning("⚠️ Ative ao menos um canal de envio.")

        if modo_sandbox:
            st.warning("🧪 MODO TESTE ativo — documento não será cobrado (sandbox)")

    st.divider()

    submitted = st.form_submit_button(
        "📄 Gerar Contrato PDF",
        type="primary",
        use_container_width=True,
    )

# ── Validação e Geração ───────────────────────────────────────────────────────
if submitted:
    erros = []
    if not nome.strip():            erros.append("Nome completo")
    if not cpf.strip():             erros.append("CPF")
    if not rg.strip():              erros.append("RG")
    if not celular.strip():         erros.append("Celular/WhatsApp")
    if not email.strip():           erros.append("E-mail")
    if not emergencia.strip():      erros.append("Contato de emergência")
    if not destino.strip():         erros.append("Destino")
    if valor_num <= 0:              erros.append("Valor do pacote")
    if not valor_extenso.strip():   erros.append("Valor por extenso")

    if erros:
        st.error("⚠️ Preencha os campos obrigatórios: " + ", ".join(erros))
    else:
        with st.spinner("Gerando contrato, aguarde..."):
            dados = {
                "nome":          nome.strip(),
                "nascimento":    nascimento,
                "cpf":           cpf.strip(),
                "rg":            rg.strip(),
                "celular":       celular.strip(),
                "email":         email.strip(),
                "emergencia":    emergencia.strip(),
                "destino":       destino.strip(),
                "data_viagem":   data_viagem,
                "valor_fmt":     fmt_valor(valor_num),
                "valor_extenso": valor_extenso.strip(),
                "servicos":             servicos_data,
                "data_contrato":        data_contrato,
                "participantes_extras": participantes_extras,
            }
            pdf_bytes = gerar_pdf(dados)

        st.success("✅ Contrato gerado com sucesso!")

        nome_arquivo = (
            f"Contrato_RotaContigo"
            f"_{nome.split()[0]}"
            f"_{destino.replace(' ', '_').replace('–','-')}"
            f"_{fmt_data(data_viagem).replace('/','')}.pdf"
        )
        st.download_button(
            label="⬇️ Baixar Contrato PDF",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True,
        )

        # ── Envio Autentique ──────────────────────────────────────────────
        if usar_autentique:
            if not api_token.strip():
                st.warning("⚠️ Coloque o Token da API Autentique para enviar.")
            else:
                with st.spinner("📤 Enviando para o Autentique..."):
                    try:
                        resultado = enviar_autentique(
                            pdf_bytes        = pdf_bytes,
                            nome_cliente     = nome.strip(),
                            email_cliente    = email.strip(),
                            telefone_cliente = celular.strip(),
                            nome_arquivo     = nome_arquivo,
                            api_token        = api_token.strip(),
                            via_whatsapp     = enviar_whatsapp,
                            via_email        = enviar_email,
                            sandbox          = modo_sandbox,
                        )

                        if "errors" in resultado:
                            st.error(f"❌ Erro Autentique: {resultado['errors'][0]['message']}")
                        else:
                            doc_id = resultado["data"]["createDocument"]["id"]
                            sigs   = resultado["data"]["createDocument"]["signatures"]

                            st.success("✅ Contrato enviado para assinatura!")
                            st.markdown("---")
                            st.markdown("**📋 Links de assinatura:**")

                            for s in sigs:
                                link_obj = s.get("link") or {}
                                link = link_obj.get("short_link", "")
                                if link:
                                    eh_cliente = s.get("email", "") == email.strip()
                                    if eh_cliente and enviar_whatsapp:
                                        metodo = "📱 WhatsApp"
                                    elif eh_cliente:
                                        metodo = "📧 E-mail"
                                    else:
                                        metodo = "📧 E-mail (Rota Contigo)"
                                    st.markdown(
                                        f"- **{s['name']}** — {metodo} enviado "
                                        f"| [Abrir link de assinatura]({link})"
                                    )

                            st.info(
                                f"🔔 Você receberá uma notificação em "
                                f"rotacontigoturismo@gmail.com quando o cliente assinar."
                            )

                    except Exception as ex:
                        st.error(f"❌ Erro ao conectar com Autentique: {ex}")

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    "<hr><p style='text-align:center;color:#aaa;font-size:12px'>"
    "Rota Contigo Agencia de Viagens e Turismo Ltda · CNPJ 65.050.169/0001-00 · "
    "CADASTUR Regular até 10/02/2028</p>",
    unsafe_allow_html=True,
)
