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
from reportlab.pdfgen import canvas as rl_canvas

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                HRFlowable, Table, TableStyle,
                                Image as RLImage, KeepTogether, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# set_page_config precisa ser o primeiro comando Streamlit executado — antes
# de qualquer acesso a st.secrets, senão o aviso de "secrets não encontrados"
# quebra a regra de "primeiro comando" e a página derruba com StreamlitAPIException.
st.set_page_config(
    page_title="Rota Contigo – Contrato",
    page_icon="🚌",
    layout="centered",
)

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


class _PaginaCanvas(rl_canvas.Canvas):
    """Canvas com duas passagens para exibir 'Página X de Y'."""
    def __init__(self, *args, **kwargs):
        rl_canvas.Canvas.__init__(self, *args, **kwargs)
        self._estados = []

    def showPage(self):
        self._estados.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._estados)
        for estado in self._estados:
            self.__dict__.update(estado)
            self._desenhar_numero(total)
            rl_canvas.Canvas.showPage(self)
        rl_canvas.Canvas.save(self)

    def _desenhar_numero(self, total):
        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#555555"))
        texto = f"Página {self._pageNumber} de {total}"
        self.drawRightString(A4[0] - 2.5*cm, 1.1*cm, texto)
        self.restoreState()


def _cabecalho() -> list:
    """Monta o cabeçalho (logo + dados da agência + badge CADASTUR), comum a todos os documentos."""
    elementos = []
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
    elementos.append(cab_t)
    elementos.append(sp(3))
    elementos.append(hr(VERDE, 2))
    elementos.append(sp(2))

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
    elementos.append(badge_t)
    elementos.append(sp(3))
    return elementos


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
    story.extend(_cabecalho())

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
    story.append(KeepTogether([
        Paragraph("OBRIGAÇÕES DA CONTRATADA", SECAO),
        hr(colors.HexColor("#aaaaaa"), 0.5),
        Paragraph("Cláusula 2ª – DOS SERVIÇOS", CL_TIT),
        Paragraph(
            "A CONTRATADA compromete-se a prestar seus serviços com qualidade, segurança e "
            "pontualidade, em conformidade com o Código de Defesa do Consumidor "
            "(Lei nº 8.078/1990), a Lei Geral do Turismo (Lei nº 11.771/2008) e demais "
            "normas aplicáveis.", CORPO),
    ]))

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
        Paragraph("POLÍTICA DE CANCELAMENTO DO CONTRATANTE", SECAO),
        hr(colors.HexColor("#aaaaaa"), 0.5),
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

    # ── Autorização de Imagem ──────────────────────────────────────────────
    story.append(Paragraph("DA AUTORIZAÇÃO DE USO DE IMAGEM E TRATAMENTO DE DADOS PESSOAIS (LGPD)", SECAO))
    story.append(hr(colors.HexColor("#aaaaaa"), 0.5))

    story.append(Paragraph("Cláusula 17ª – DA AUTORIZAÇÃO DE USO DE IMAGEM", CL_TIT))
    story.append(Paragraph(
        "O(A) CONTRATANTE autoriza, de forma livre, expressa, inequívoca e informada, a empresa "
        "<b>ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA</b>, inscrita no CNPJ sob nº "
        "<b>65.050.169/0001-00</b>, a realizar a captação de fotografias, vídeos, áudios e "
        "demais registros audiovisuais contendo sua imagem, voz e nome durante a participação "
        "em viagens, eventos, excursões ou quaisquer atividades promovidas pela CONTRATADA.",
        CORPO))
    story.append(Paragraph(
        "<b>§1º</b> – A autorização prevista nesta cláusula compreende o direito de utilizar, "
        "reproduzir, editar, publicar, divulgar e veicular as imagens e gravações captadas, "
        "para fins institucionais, promocionais, publicitários e comerciais, em quaisquer meios "
        "de comunicação, físicos ou digitais, incluindo, mas não se limitando a redes sociais, "
        "websites, anúncios, campanhas publicitárias, materiais impressos e plataformas "
        "eletrônicas.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – O(A) CONTRATANTE declara estar ciente de que o tratamento de seus dados "
        "pessoais e de imagem será realizado em conformidade com a Lei nº 13.709/2018 – "
        "Lei Geral de Proteção de Dados Pessoais (LGPD), observando-se os princípios da "
        "finalidade, necessidade, adequação e segurança das informações.", CORPO))
    story.append(Paragraph(
        "<b>§3º</b> – A presente autorização é concedida em caráter gratuito, sem qualquer "
        "ônus para a CONTRATADA, não cabendo ao(à) CONTRATANTE qualquer tipo de remuneração, "
        "indenização ou compensação futura pelo uso das imagens e conteúdos captados.", CORPO))
    story.append(Paragraph(
        "<b>§4º</b> – A autorização prevista nesta cláusula vigorará por prazo indeterminado, "
        "podendo ser revogada pelo(a) CONTRATANTE mediante solicitação formal e expressa, por "
        "escrito, ficando resguardadas as utilizações e divulgações realizadas anteriormente à "
        "data do recebimento da revogação.", CORPO))

    # ── Disposições Gerais ─────────────────────────────────────────────────
    story.append(KeepTogether([
        Paragraph("DISPOSIÇÕES GERAIS E VIGÊNCIA", SECAO),
        hr(colors.HexColor("#aaaaaa"), 0.5),
        Paragraph("Cláusula 18ª – DA VIGÊNCIA", CL_TIT),
        Paragraph(
            "Este contrato entra em vigor na data da assinatura ou confirmação do pagamento "
            "(o que ocorrer primeiro), e tem vigência até a conclusão dos serviços contratados.",
            CORPO),
    ]))

    story.append(KeepTogether([
        Paragraph("Cláusula 19ª – DO FORO", CL_TIT),
        Paragraph(
            "Fica eleito o foro da Comarca de <b>Curitiba – PR</b> para dirimir quaisquer "
            "controvérsias oriundas deste contrato, com renúncia a qualquer outro, por mais "
            "privilegiado que seja (art. 63 do CPC).", CORPO),
    ]))

    story.append(Paragraph("Cláusula 20ª – DA VALIDADE DIGITAL", CL_TIT))
    story.append(Paragraph(
        "Este contrato tem plena validade jurídica em formato digital, nos termos da MP "
        "nº 2.200-2/2001, da Lei nº 14.063/2020 (assinaturas eletrônicas em interações "
        "com entes públicos e entre particulares), do Marco Civil da Internet (Lei nº "
        "12.965/2014) e do CDC. Sua aceitação ocorre mediante confirmação de pagamento "
        "ou assinatura eletrônica.",
        CORPO))

    story.append(Paragraph("Cláusula 21ª – DA LEGISLAÇÃO APLICÁVEL", CL_TIT))
    story.append(Paragraph(
        "Este contrato é regido pelas seguintes normas: Código Civil (Lei 10.406/2002), "
        "Código de Defesa do Consumidor (Lei 8.078/1990), Lei Geral do Turismo "
        "(Lei 11.771/2008), art. 49 do CDC, art. 413 do CC e LGPD (Lei 13.709/2018).",
        CORPO))

    # ── Assinaturas ────────────────────────────────────────────────────────
    # PageBreak garante que as assinaturas SEMPRE ficam na mesma posição
    # (y≈28% do topo), independente da quantidade de acompanhantes.
    story.append(PageBreak())
    story.append(sp(136))   # espaço calibrado para posicionar a assinatura em y≈24%
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

    doc.build(story, canvasmaker=_PaginaCanvas)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO DO PDF — TERMO DE INTERMEDIAÇÃO DE PASSAGEM AÉREA
# ══════════════════════════════════════════════════════════════════════════════

def gerar_pdf_passagem(d: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []
    story.append(sp(2))

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    story.extend(_cabecalho())

    story.append(Paragraph("TERMO DE INTERMEDIAÇÃO PARA EMISSÃO DE PASSAGEM AÉREA", SECAO))
    story.append(hr(VERDE, 0.5))

    story.append(Paragraph("Cláusula 1ª – DO OBJETO E DAS PARTES", CL_TIT))
    story.append(Paragraph(
        "O presente termo tem como objeto a intermediação, pela <b>ROTA CONTIGO AGENCIA "
        "DE VIAGENS E TURISMO LTDA</b>, inscrita no CNPJ/CADASTUR sob nº "
        "<b>65.050.169/0001-00</b>, com sede em Curitiba – PR, operando exclusivamente "
        "de forma digital, e-mail: rotacontigoturismo@gmail.com, telefone: "
        "(41) 99819-5099, doravante denominada <b>CONTRATADA</b>, para emissão de "
        "passagem(ns) aérea(s) junto à(s) companhia(s) aérea(s) e/ou consolidadora(s) de "
        "viagens, em nome e por conta do(a) <b>CONTRATANTE/PASSAGEIRO</b> identificado(a) "
        "abaixo:", CORPO))

    story.append(sp(2))
    story.append(Paragraph("<b>DADOS DO(A) CONTRATANTE / PASSAGEIRO:</b>", CAMPO))
    story.append(Paragraph(f"Nome completo: <b>{d['nome']}</b>", CAMPO))
    story.append(Paragraph(f"Data de Nascimento: <b>{fmt_data(d['nascimento'])}</b>", CAMPO))
    story.append(Paragraph(f"CPF: <b>{d['cpf']}</b>    RG: <b>{d['rg']}</b>", CAMPO))
    story.append(Paragraph(f"Celular/WhatsApp: <b>{d['celular']}</b>", CAMPO))
    story.append(Paragraph(f"E-mail: <b>{d['email']}</b>", CAMPO))
    story.append(Paragraph(f"Em caso de emergência avisar: <b>{d['emergencia']}</b>", CAMPO))
    story.append(sp(3))

    # ── Dados da Viagem ──────────────────────────────────────────────────
    viagem_rows = [["Trecho", "Data de Ida", "Data de Volta", "Companhia"]]
    viagem_rows.append([
        f"{d['origem']} → {d['destino']}",
        fmt_data(d['data_ida']),
        fmt_data(d['data_volta']) if d.get('ida_e_volta') and d.get('data_volta') else "Somente ida",
        d['companhia'],
    ])
    t_viagem = Table(viagem_rows, colWidths=[5.5*cm, 3.3*cm, 3.3*cm, 3.9*cm])
    t_viagem.setStyle(TableStyle([
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
    ]))
    story.append(KeepTogether([
        Paragraph("<b>DADOS DA VIAGEM:</b>", CAMPO),
        sp(2),
        t_viagem,
    ]))
    if d.get('localizador', '').strip():
        story.append(sp(2))
        story.append(Paragraph(f"Localizador da reserva: <b>{d['localizador']}</b>", CAMPO))
    story.append(sp(3))

    story.append(Paragraph("Cláusula 2ª – DA NATUREZA DA INTERMEDIAÇÃO", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA atua exclusivamente como <b>intermediária</b> entre o CONTRATANTE "
        "e a(s) companhia(s) aérea(s) e/ou consolidadora(s) de viagens, não se "
        "confundindo com o transportador aéreo. O contrato de transporte é celebrado "
        "diretamente entre o CONTRATANTE e a companhia aérea responsável pelo voo, sendo "
        "esta a única responsável pela execução do serviço de transporte, incluindo "
        "horários, itinerário, bagagem, atrasos, cancelamentos e overbooking, nos termos "
        "da Convenção de Montreal (Decreto nº 5.910/2006) e da Resolução ANAC nº "
        "400/2016.",
        CORPO))
    story.append(Paragraph(
        "<b>Parágrafo único</b> – Este termo aplica-se exclusivamente à intermediação de "
        "emissão de <b>passagem aérea avulsa</b>. Caso a contratação inclua hospedagem, "
        "pacote turístico ou outros serviços combinados, aplicam-se as disposições do "
        "Contrato de Prestação de Serviços Turísticos da CONTRATADA, uma vez que a "
        "limitação de responsabilidade aqui prevista está condicionada à venda isolada do "
        "bilhete, nos termos do entendimento do Superior Tribunal de Justiça (STJ, REsp "
        "2.123.720): \"Quando o serviço prestado pela agência/empresa de turismo for "
        "exclusivamente a venda de passagem aérea, fica afastada sua responsabilidade\" "
        "pelo cumprimento do contrato de transporte, por não deter a CONTRATADA "
        "ingerência sobre a sua execução.", CORPO))

    story.append(Paragraph("Cláusula 3ª – DA RESPONSABILIDADE DA CONTRATADA", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA responde, nos termos dos arts. 14 e 15 do Código de Defesa do "
        "Consumidor, exclusivamente pelos serviços que presta diretamente: a correta "
        "emissão da passagem conforme os dados fornecidos pelo CONTRATANTE, a informação "
        "clara sobre tarifas, regras e taxas antes da emissão, e o repasse de "
        "comunicações relevantes recebidas da companhia aérea. A CONTRATADA <b>não "
        "responde</b> por fatos de responsabilidade exclusiva da companhia aérea ou de "
        "terceiros (atraso, cancelamento, overbooking, extravio de bagagem, alteração de "
        "malha aérea, greve, entre outros), devendo o CONTRATANTE, nesses casos, buscar "
        "diretamente a companhia aérea, sem prejuízo do apoio da CONTRATADA na "
        "intermediação do contato.", CORPO))

    story.append(Paragraph("Cláusula 4ª – DOS DADOS FORNECIDOS E DA DOCUMENTAÇÃO", CL_TIT))
    story.append(Paragraph(
        "<b>§1º</b> – A emissão da passagem é feita com base exclusivamente nos dados "
        "(nome completo, documento, datas, trechos) fornecidos pelo CONTRATANTE. Erros "
        "de digitação ou informação incorreta identificados após a emissão poderão gerar "
        "custos de alteração cobrados pela companhia aérea/consolidadora, que serão "
        "integralmente repassados ao CONTRATANTE.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – É de responsabilidade exclusiva do CONTRATANTE possuir documento "
        "de identificação válido e, quando aplicável, passaporte, visto e demais "
        "documentos exigidos para embarque e entrada no destino, isentando a CONTRATADA "
        "de qualquer responsabilidade por impedimento de embarque ou de entrada "
        "decorrente de documentação irregular (art. 14, §3º, II do CDC).", CORPO))

    # ── Valores ──────────────────────────────────────────────────────────
    valores_rows = [
        ["Tarifa aérea",       f"R$ {d['valor_tarifa_fmt']}"],
        ["Taxa de serviço",    f"R$ {d['valor_taxa_fmt']}"],
        ["Valor total",        f"R$ {d['valor_total_fmt']}"],
    ]
    t_valores = Table(valores_rows, colWidths=[10*cm, 6*cm])
    t_valores.setStyle(TableStyle([
        ("FONTSIZE",      (0,0), (-1,-1), 9.5),
        ("ALIGN",         (1,0), (1,-1), "RIGHT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, colors.white, VCLARO]),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(KeepTogether([
        Paragraph("Cláusula 5ª – DO PREÇO E DA TAXA DE SERVIÇO", CL_TIT),
        Paragraph(
            f"O valor total pago pelo CONTRATANTE é de <b>R$ {d['valor_total_fmt']} "
            f"({d['valor_extenso']})</b>, composto pela tarifa aérea (repassada à "
            "companhia aérea/consolidadora) somada à taxa de serviço da CONTRATADA, "
            "remuneração pela intermediação, conforme discriminado abaixo:", CORPO),
        sp(2),
        t_valores,
    ]))
    story.append(sp(2))
    story.append(Paragraph(
        "<b>§1º</b> – Tarifas aéreas estão sujeitas a variação de disponibilidade e "
        "câmbio até a confirmação do pagamento e efetiva emissão do bilhete. Caso a "
        "tarifa informada não esteja mais disponível no momento da emissão, a "
        "CONTRATADA comunicará o novo valor ao CONTRATANTE, que poderá aceitar a "
        "diferença ou desistir da compra com devolução integral dos valores ainda não "
        "repassados à companhia aérea.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – A taxa de serviço remunera o trabalho de pesquisa, cotação, "
        "emissão e suporte da CONTRATADA e <b>não é reembolsável após a emissão do "
        "bilhete</b>, ainda que o CONTRATANTE opte por cancelar a viagem, salvo erro "
        "comprovado da CONTRATADA na emissão.", CORPO))

    story.append(Paragraph("Cláusula 6ª – DO CANCELAMENTO, ALTERAÇÃO E REEMBOLSO", CL_TIT))
    story.append(Paragraph(
        "<b>§1º</b> – As regras de cancelamento, alteração e reembolso da passagem "
        "aérea (incluindo prazos, multas e valores) são definidas pela companhia aérea "
        "e/ou consolidadora, conforme a tarifa escolhida, e serão informadas ao "
        "CONTRATANTE antes da confirmação da compra.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – Tarifas promocionais podem ser não reembolsáveis ou sujeitas a "
        "multa de alteração/cancelamento definida pela companhia aérea, conforme "
        "informado no ato da cotação.", CORPO))
    story.append(Paragraph(
        "<b>§3º</b> – Solicitado o cancelamento ou alteração pelo CONTRATANTE, a "
        "CONTRATADA repassará o pedido à companhia aérea/consolidadora e devolverá ao "
        "CONTRATANTE os valores efetivamente reembolsados por estas, descontada a taxa "
        "de serviço já prestada (Cláusula 5ª, §2º) e eventuais taxas de "
        "cancelamento/alteração cobradas pela companhia aérea.", CORPO))
    story.append(Paragraph(
        "<b>§4º</b> – Reembolsos em cartão de crédito seguem o cronograma de estorno da "
        "operadora do cartão, não controlado pela CONTRATADA.", CORPO))

    story.append(Paragraph("Cláusula 7ª – DA FORMA DE PAGAMENTO", CL_TIT))
    story.append(Paragraph(
        f"Forma de pagamento escolhida: <b>{d['forma_pagamento']}</b>. Em caso de "
        "recusa, estorno indevido ou chargeback do pagamento após a emissão da "
        "passagem, o CONTRATANTE será responsável pelo ressarcimento integral do valor "
        "à CONTRATADA, sem prejuízo das medidas legais cabíveis.", CORPO))

    # ── LGPD ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Cláusula 8ª – DA PROTEÇÃO DE DADOS PESSOAIS – LGPD", CL_TIT))
    story.append(Paragraph(
        "Em conformidade com a Lei nº 13.709/2018 (LGPD), a CONTRATADA compromete-se a "
        "coletar apenas os dados estritamente necessários à emissão da passagem, "
        "utilizá-los exclusivamente para essa finalidade, não compartilhá-los com "
        "terceiros sem consentimento expresso (salvo obrigação legal ou repasse "
        "necessário à companhia aérea/consolidadora para a emissão) e garantir a "
        "segurança das informações com medidas técnicas e administrativas adequadas.",
        CORPO))

    story.append(Paragraph("Cláusula 9ª – DO FORO", CL_TIT))
    story.append(Paragraph(
        "Fica eleito o foro da Comarca de <b>Curitiba – PR</b> para dirimir quaisquer "
        "controvérsias oriundas deste termo, com renúncia a qualquer outro, por mais "
        "privilegiado que seja (art. 63 do CPC).", CORPO))

    story.append(Paragraph("Cláusula 10ª – DA VALIDADE DIGITAL", CL_TIT))
    story.append(Paragraph(
        "Este termo tem plena validade jurídica em formato digital, nos termos da MP "
        "nº 2.200-2/2001, da Lei nº 14.063/2020, do Marco Civil da Internet (Lei nº "
        "12.965/2014) e do CDC. Sua aceitação ocorre mediante confirmação de pagamento "
        "ou assinatura eletrônica.", CORPO))

    # ── Assinaturas ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(sp(136))
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

    doc.build(story, canvasmaker=_PaginaCanvas)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO DO PDF — TERMO DE INTERMEDIAÇÃO CORPORATIVO (CONDIÇÕES GERAIS)
# ══════════════════════════════════════════════════════════════════════════════
# Assinado UMA VEZ por empresa cliente. Cobre a relação continuada; cada
# emissão de passagem específica é registrada depois via "Pedido de Emissão"
# (gerar_pdf_pedido_emissao), sem precisar de nova assinatura formal a cada voo.

def gerar_pdf_corporativo_geral(d: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []
    story.append(sp(2))

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    story.extend(_cabecalho())

    story.append(Paragraph("TERMO DE INTERMEDIAÇÃO CORPORATIVO – CONDIÇÕES GERAIS", SECAO))
    story.append(hr(VERDE, 0.5))

    story.append(Paragraph("Cláusula 1ª – DO OBJETO E DAS PARTES", CL_TIT))
    story.append(Paragraph(
        "O presente termo estabelece as condições gerais que regerão a intermediação, "
        "pela <b>ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA</b>, inscrita no "
        "CNPJ/CADASTUR sob nº <b>65.050.169/0001-00</b>, com sede em Curitiba – PR, "
        "operando exclusivamente de forma digital, e-mail: rotacontigoturismo@gmail.com, "
        "telefone: (41) 99819-5099, doravante denominada <b>CONTRATADA</b>, para "
        "emissão de passagens aéreas solicitadas ao longo do tempo pela pessoa jurídica "
        "identificada abaixo, doravante denominada <b>CONTRATANTE</b>:", CORPO))

    story.append(sp(2))
    story.append(Paragraph("<b>DADOS DA EMPRESA CONTRATANTE:</b>", CAMPO))
    story.append(Paragraph(f"Razão social: <b>{d['razao_social']}</b>", CAMPO))
    story.append(Paragraph(f"CNPJ: <b>{d['cnpj_empresa']}</b>", CAMPO))
    story.append(Paragraph(f"Endereço: <b>{d['endereco_empresa']}</b>", CAMPO))
    story.append(sp(2))
    story.append(Paragraph("<b>RESPONSÁVEL/SOLICITANTE AUTORIZADO:</b>", CAMPO))
    story.append(Paragraph(f"Nome: <b>{d['responsavel_nome']}</b>    Cargo: <b>{d['responsavel_cargo']}</b>", CAMPO))
    story.append(Paragraph(f"E-mail: <b>{d['responsavel_email']}</b>    Telefone: <b>{d['responsavel_telefone']}</b>", CAMPO))
    story.append(sp(3))

    story.append(Paragraph("Cláusula 2ª – DA NATUREZA DA INTERMEDIAÇÃO", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA atua exclusivamente como <b>intermediária</b> entre a CONTRATANTE "
        "e a(s) companhia(s) aérea(s) e/ou consolidadora(s) de viagens, não se "
        "confundindo com o transportador aéreo. O contrato de transporte é celebrado "
        "diretamente entre o passageiro e a companhia aérea responsável pelo voo, sendo "
        "esta a única responsável pela execução do serviço de transporte, incluindo "
        "horários, itinerário, bagagem, atrasos, cancelamentos e overbooking, nos termos "
        "da Convenção de Montreal (Decreto nº 5.910/2006) e da Resolução ANAC nº "
        "400/2016.",
        CORPO))
    story.append(Paragraph(
        "<b>Parágrafo único</b> – Este termo aplica-se exclusivamente à intermediação de "
        "emissão de <b>passagem aérea avulsa</b>. Caso alguma solicitação inclua "
        "hospedagem, pacote turístico ou outros serviços combinados, aplicam-se as "
        "disposições do Contrato de Prestação de Serviços Turísticos da CONTRATADA para "
        "aquela solicitação específica, uma vez que a limitação de responsabilidade aqui "
        "prevista está condicionada à venda isolada do bilhete, nos termos do "
        "entendimento do Superior Tribunal de Justiça (STJ, REsp 2.123.720): \"Quando o "
        "serviço prestado pela agência/empresa de turismo for exclusivamente a venda de "
        "passagem aérea, fica afastada sua responsabilidade\" pelo cumprimento do "
        "contrato de transporte, por não deter a CONTRATADA ingerência sobre a sua "
        "execução.", CORPO))

    story.append(Paragraph("Cláusula 3ª – DA RESPONSABILIDADE DA CONTRATADA E DA NATUREZA DA RELAÇÃO", CL_TIT))
    story.append(Paragraph(
        "A CONTRATADA responde exclusivamente pelos serviços que presta diretamente: a "
        "correta emissão da passagem conforme os dados fornecidos pela CONTRATANTE, a "
        "informação clara sobre tarifas, regras e taxas antes de cada emissão, e o "
        "repasse de comunicações relevantes recebidas da companhia aérea. A CONTRATADA "
        "<b>não responde</b> por fatos de responsabilidade exclusiva da companhia aérea "
        "ou de terceiros (atraso, cancelamento, overbooking, extravio de bagagem, "
        "alteração de malha aérea, greve, entre outros), devendo a CONTRATANTE, nesses "
        "casos, buscar diretamente a companhia aérea, sem prejuízo do apoio da "
        "CONTRATADA na intermediação do contato.", CORPO))
    story.append(Paragraph(
        "<b>Parágrafo único</b> – A aplicabilidade do Código de Defesa do Consumidor a "
        "esta relação depende da caracterização da CONTRATANTE como destinatária final "
        "dos serviços contratados, nos termos da teoria finalista adotada pela "
        "jurisprudência majoritária do STJ. Subsidiária e cumulativamente, aplicam-se as "
        "disposições do Código Civil (Lei nº 10.406/2002) relativas aos contratos em "
        "geral.", CORPO))

    story.append(Paragraph("Cláusula 4ª – DOS PEDIDOS DE EMISSÃO", CL_TIT))
    story.append(Paragraph(
        "<b>§1º</b> – Cada emissão de passagem aérea solicitada pela CONTRATANTE ao "
        "longo da vigência deste termo será registrada em um <b>Pedido de Emissão</b> "
        "específico, contendo os dados do passageiro, do trecho, das datas e dos "
        "valores daquela operação, o qual passa a integrar este termo como seu anexo, "
        "sem necessidade de nova assinatura formal a cada solicitação.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – A emissão de cada passagem é feita com base exclusivamente nos "
        "dados fornecidos pela CONTRATANTE por meio de seu responsável/solicitante "
        "autorizado. Erros de digitação ou informação incorreta identificados após a "
        "emissão poderão gerar custos de alteração cobrados pela companhia "
        "aérea/consolidadora, que serão integralmente repassados à CONTRATANTE.", CORPO))
    story.append(Paragraph(
        "<b>§3º</b> – É de responsabilidade exclusiva da CONTRATANTE e de cada "
        "passageiro possuir documento de identificação válido e, quando aplicável, "
        "passaporte, visto e demais documentos exigidos para embarque e entrada no "
        "destino, isentando a CONTRATADA de qualquer responsabilidade por impedimento de "
        "embarque ou de entrada decorrente de documentação irregular.", CORPO))

    story.append(Paragraph("Cláusula 5ª – DA TAXA DE SERVIÇO E DO PREÇO", CL_TIT))
    story.append(Paragraph(
        "O valor de cada emissão é composto pela tarifa aérea (repassada à companhia "
        "aérea/consolidadora) somada à taxa de serviço da CONTRATADA, remuneração pela "
        "intermediação, ambas informadas em cada Pedido de Emissão. Tarifas aéreas estão "
        "sujeitas a variação de disponibilidade e câmbio até a confirmação e efetiva "
        "emissão do bilhete. A taxa de serviço remunera o trabalho de pesquisa, cotação, "
        "emissão e suporte da CONTRATADA e <b>não é reembolsável após a emissão do "
        "bilhete</b>, salvo erro comprovado da CONTRATADA.", CORPO))

    story.append(Paragraph("Cláusula 6ª – DO CANCELAMENTO, ALTERAÇÃO E REEMBOLSO", CL_TIT))
    story.append(Paragraph(
        "As regras de cancelamento, alteração e reembolso de cada passagem (incluindo "
        "prazos, multas e valores) são definidas pela companhia aérea e/ou "
        "consolidadora, conforme a tarifa escolhida, e serão informadas à CONTRATANTE "
        "antes da confirmação de cada compra. Solicitado o cancelamento ou alteração, a "
        "CONTRATADA repassará o pedido à companhia aérea/consolidadora e devolverá à "
        "CONTRATANTE os valores efetivamente reembolsados por estas, descontada a taxa "
        "de serviço já prestada e eventuais taxas cobradas pela companhia aérea.", CORPO))

    story.append(Paragraph("Cláusula 7ª – DA FORMA DE PAGAMENTO", CL_TIT))
    story.append(Paragraph(
        f"Pagamento na modalidade <b>faturado</b>, com fechamento a cada "
        f"<b>{d['periodicidade_faturamento']} dias</b> e vencimento em "
        f"<b>{d['prazo_faturamento']} dias</b> corridos após a emissão da respectiva "
        "nota fiscal/fatura pela CONTRATADA, consolidando as emissões realizadas no "
        "período.", CORPO))
    story.append(Paragraph(
        "<b>§1º</b> – Em caso de recusa, estorno indevido ou chargeback de qualquer "
        "pagamento, a CONTRATANTE será responsável pelo ressarcimento integral do valor "
        "à CONTRATADA, sem prejuízo das medidas legais cabíveis.", CORPO))
    story.append(Paragraph(
        "<b>§2º</b> – O não pagamento no prazo faturado sujeitará a CONTRATANTE a "
        "multa de 2% (dois por cento) sobre o valor em atraso, juros de mora de 1% "
        "(um por cento) ao mês, e correção monetária pelo IGP-M/FGV (ou índice que vier "
        "a substituí-lo) desde o vencimento até a data do efetivo pagamento.", CORPO))

    story.append(Paragraph("Cláusula 8ª – DA CONFIDENCIALIDADE", CL_TIT))
    story.append(Paragraph(
        "As partes comprometem-se a manter sigilo sobre quaisquer informações "
        "comerciais, financeiras ou operacionais trocadas em razão deste termo, não as "
        "divulgando a terceiros sem consentimento prévio e expresso da outra parte, "
        "salvo por determinação legal ou judicial.", CORPO))

    # ── LGPD ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Cláusula 9ª – DA PROTEÇÃO DE DADOS PESSOAIS – LGPD", CL_TIT))
    story.append(Paragraph(
        "Em conformidade com a Lei nº 13.709/2018 (LGPD), a CONTRATADA compromete-se a "
        "coletar apenas os dados dos passageiros/funcionários estritamente necessários a "
        "cada emissão, indicados pela CONTRATANTE por meio de seu responsável "
        "autorizado, utilizá-los exclusivamente para essa finalidade, não compartilhá-los "
        "com terceiros sem consentimento expresso (salvo obrigação legal ou repasse "
        "necessário à companhia aérea/consolidadora) e garantir a segurança das "
        "informações com medidas técnicas e administrativas adequadas. A CONTRATANTE "
        "declara possuir base legal e legitimidade para compartilhar com a CONTRATADA os "
        "dados pessoais de seus funcionários/prepostos indicados como passageiros.",
        CORPO))

    story.append(Paragraph("Cláusula 10ª – DA VIGÊNCIA E RESCISÃO", CL_TIT))
    story.append(Paragraph(
        "Este termo vigora por prazo indeterminado a partir da data de assinatura, "
        "podendo ser rescindido por qualquer das partes mediante aviso prévio por "
        "escrito de 30 (trinta) dias, sem prejuízo da conclusão de Pedidos de Emissão já "
        "confirmados e do pagamento de valores em aberto.", CORPO))

    story.append(Paragraph("Cláusula 11ª – DO FORO", CL_TIT))
    story.append(Paragraph(
        "Fica eleito o foro da Comarca de <b>Curitiba – PR</b> para dirimir quaisquer "
        "controvérsias oriundas deste termo, com renúncia a qualquer outro, por mais "
        "privilegiado que seja (art. 63 do CPC).", CORPO))

    story.append(Paragraph("Cláusula 12ª – DA VALIDADE DIGITAL", CL_TIT))
    story.append(Paragraph(
        "Este termo tem plena validade jurídica em formato digital, nos termos da MP "
        "nº 2.200-2/2001, da Lei nº 14.063/2020, do Marco Civil da Internet (Lei nº "
        "12.965/2014) e da legislação civil aplicável. Sua aceitação ocorre mediante "
        "assinatura eletrônica.", CORPO))

    # ── Assinaturas ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(sp(136))
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
        f"<b>{d['razao_social']}</b><br/>"
        f"CNPJ: {d['cnpj_empresa']}<br/>"
        f"{d['responsavel_nome']} – {d['responsavel_cargo']}", ass_st)

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

    doc.build(story, canvasmaker=_PaginaCanvas)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO DO PDF — PEDIDO DE EMISSÃO (VINCULADO AO TERMO CORPORATIVO GERAL)
# ══════════════════════════════════════════════════════════════════════════════
# Documento leve, um por passagem, sem repetir as cláusulas gerais — apenas
# referencia o Termo de Intermediação Corporativo já assinado.

def gerar_pdf_pedido_emissao(d: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []
    story.append(sp(2))

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    story.extend(_cabecalho())

    story.append(Paragraph("PEDIDO DE EMISSÃO – PASSAGEM AÉREA CORPORATIVA", SECAO))
    story.append(hr(VERDE, 0.5))

    story.append(Paragraph(
        f"O presente Pedido de Emissão é regido pelo <b>Termo de Intermediação "
        f"Corporativo – Condições Gerais</b> firmado entre a "
        f"<b>ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA</b> (CNPJ "
        f"65.050.169/0001-00) e a CONTRATANTE abaixo identificada em "
        f"<b>{fmt_data(d['data_termo_geral'])}</b>, cujas cláusulas gerais "
        "permanecem integralmente aplicáveis a esta emissão, sendo este documento "
        "apenas o registro específico da presente operação.", CORPO))
    story.append(sp(3))

    story.append(Paragraph("<b>EMPRESA CONTRATANTE:</b>", CAMPO))
    story.append(Paragraph(f"Razão social: <b>{d['razao_social']}</b>    CNPJ: <b>{d['cnpj_empresa']}</b>", CAMPO))
    story.append(sp(2))
    story.append(Paragraph("<b>DADOS DO(A) PASSAGEIRO(A):</b>", CAMPO))
    story.append(Paragraph(f"Nome completo: <b>{d['passageiro_nome']}</b>    CPF: <b>{d['passageiro_cpf']}</b>", CAMPO))
    story.append(sp(3))

    # ── Dados da Viagem ──────────────────────────────────────────────────
    viagem_rows = [["Trecho", "Data de Ida", "Data de Volta", "Companhia"]]
    viagem_rows.append([
        f"{d['origem']} → {d['destino']}",
        fmt_data(d['data_ida']),
        fmt_data(d['data_volta']) if d.get('ida_e_volta') and d.get('data_volta') else "Somente ida",
        d['companhia'],
    ])
    t_viagem = Table(viagem_rows, colWidths=[5.5*cm, 3.3*cm, 3.3*cm, 3.9*cm])
    t_viagem.setStyle(TableStyle([
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
    ]))
    story.append(KeepTogether([
        Paragraph("<b>DADOS DA VIAGEM:</b>", CAMPO),
        sp(2),
        t_viagem,
    ]))
    if d.get('localizador', '').strip():
        story.append(sp(2))
        story.append(Paragraph(f"Localizador da reserva: <b>{d['localizador']}</b>", CAMPO))
    story.append(sp(3))

    # ── Valores ──────────────────────────────────────────────────────────
    valores_rows = [
        ["Tarifa aérea",       f"R$ {d['valor_tarifa_fmt']}"],
        ["Taxa de serviço",    f"R$ {d['valor_taxa_fmt']}"],
        ["Valor total",        f"R$ {d['valor_total_fmt']}"],
    ]
    t_valores = Table(valores_rows, colWidths=[10*cm, 6*cm])
    t_valores.setStyle(TableStyle([
        ("FONTSIZE",      (0,0), (-1,-1), 9.5),
        ("ALIGN",         (1,0), (1,-1), "RIGHT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, colors.white, VCLARO]),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(KeepTogether([
        Paragraph("<b>VALORES DESTA EMISSÃO:</b>", CAMPO),
        sp(2),
        t_valores,
        sp(2),
        Paragraph(
            f"Valor total por extenso: <b>{d['valor_extenso']}</b>. A cobrança deste "
            "valor será incluída na fatura consolidada do período, conforme a "
            "periodicidade e o prazo de vencimento definidos no Termo de Intermediação "
            "Corporativo – Condições Gerais.", CORPO),
    ]))
    story.append(sp(3))

    story.append(Paragraph(
        "Aplicam-se integralmente a esta emissão as cláusulas de natureza da "
        "intermediação, responsabilidade, documentação, preço e taxa de serviço, "
        "cancelamento/alteração/reembolso, forma de pagamento, confidencialidade e LGPD "
        "previstas no Termo de Intermediação Corporativo – Condições Gerais "
        "mencionado acima, inclusive quanto à não reembolsabilidade da taxa de serviço "
        "após a emissão do bilhete.", CORPO))

    # ── Confirmação ────────────────────────────────────────────────────────
    story.append(sp(10))
    story.append(hr(VERDE, 0.5))
    story.append(sp(6))
    story.append(Paragraph(
        f"Curitiba – PR, {data_extenso(d['data_pedido'])}.",
        E("data", fontSize=9.5, alignment=TA_CENTER)))
    story.append(sp(6))
    story.append(Paragraph(
        "ROTA CONTIGO AGENCIA DE VIAGENS E TURISMO LTDA  |  CNPJ: 65.050.169/0001-00  |  "
        "CADASTUR Regular – Válido até 10/02/2028  |  rotacontigoturismo@gmail.com  |  "
        "(41) 99819-5099", RODAPE))

    doc.build(story, canvasmaker=_PaginaCanvas)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO AUTENTIQUE
# ══════════════════════════════════════════════════════════════════════════════

def _contar_paginas(pdf_bytes: bytes) -> int:
    """Conta o número de páginas do PDF."""
    try:
        from pypdf import PdfReader
        return len(PdfReader(io.BytesIO(pdf_bytes)).pages)
    except Exception:
        return 2  # fallback seguro


def _pos(x: float, y: float, pagina: int, elemento: str = "SIGNATURE") -> str:
    """Formata um objeto de posição para o Autentique."""
    return f'{{"x":"{x}","y":"{y}","z":{pagina},"element":"{elemento}"}}'


def enviar_autentique(pdf_bytes: bytes, nome_cliente: str, email_cliente: str,
                      telefone_cliente: str, nome_arquivo: str, api_token: str,
                      via_whatsapp: bool, via_email: bool = True,
                      sandbox: bool = False,
                      mensagem_intro: str = "Segue o contrato da sua excursão com a Rota Contigo.") -> dict:
    """Envia o PDF para o Autentique e retorna link de assinatura."""

    # Detecta última página (onde ficam as linhas de assinatura)
    ultima_pag = _contar_paginas(pdf_bytes)

    # Posições das assinaturas na última página:
    # Layout do PDF: coluna ESQUERDA (x=15) = ROTA CONTIGO, coluna DIREITA (x=65) = CLIENTE
    # y=20 = sobre as linhas horizontais de assinatura (topo da última página)
    pos_rota    = f'[{_pos(15, 24, ultima_pag)}]'   # ESQUERDA = Rota Contigo
    pos_cliente = f'[{_pos(65, 24, ultima_pag)}]'   # DIREITA  = Cliente

    # Normaliza telefone
    tel = ""
    if telefone_cliente:
        tel = "".join(filter(str.isdigit, telefone_cliente))
        if not tel.startswith("55"):
            tel = "55" + tel
        tel = "+" + tel

    # Monta signatário do cliente
    # IMPORTANTE: a API Autentique aceita SOMENTE email OU phone, nunca ambos
    if via_whatsapp and tel:
        # WhatsApp: envia só o telefone (sem email)
        signer_input = (
            f'{{"name":"{nome_cliente}",'
            f'"phone":"{tel}","delivery_method":"DELIVERY_METHOD_WHATSAPP",'
            f'"positions":{pos_cliente},"action":"SIGN"}}'
        )
    else:
        # E-mail: envia só o email (sem telefone)
        signer_input = (
            f'{{"name":"{nome_cliente}","email":"{email_cliente}",'
            f'"positions":{pos_cliente},"action":"SIGN"}}'
        )

    # Signatário da Rota Contigo
    # IMPORTANTE: usar o email da conta vinculada ao token da API
    # para que signDocument possa assinar automaticamente
    signer_rota = (
        f'{{"name":"David Cortés – Rota Contigo",'
        f'"email":"davidcorteshernandez945@gmail.com",'
        f'"positions":{pos_rota},"action":"SIGN"}}'
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
        '"message":"Olá ' + nome_cliente.split()[0] + '! ' + mensagem_intro + ' Por favor, assine digitalmente clicando no botão abaixo."},'
        '"signers":[' + signer_input + ',' + signer_rota + '],'
        '"file":null}}'
    )

    payload = {
        "operations": operations,
        "map": '{"file": ["variables.file"]}',
    }
    files = [("file", (nome_arquivo, pdf_bytes, "application/pdf"))]
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1️⃣ Cria o documento
    resp = requests.post(
        "https://api.autentique.com.br/v2/graphql",
        headers=headers,
        data=payload,
        files=files,
        timeout=30,
    )
    resultado = resp.json()

    # 2️⃣ Assina automaticamente como Rota Contigo (usando ID do documento)
    # signDocument assina com a conta vinculada ao token (davidnobrasil01@gmail.com)
    # e retorna Boolean — sem sub-seleção
    try:
        doc_id = resultado["data"]["createDocument"]["id"]
        if doc_id:
            requests.post(
                "https://api.autentique.com.br/v2/graphql",
                headers={**headers, "Content-Type": "application/json"},
                json={"query": f'mutation {{ signDocument(id: "{doc_id}") }}'},
                timeout=15,
            )
    except Exception:
        pass  # Não bloqueia o fluxo se a auto-assinatura falhar

    return resultado


# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════

# ── Proteção por senha ────────────────────────────────────────────────────────
def _checar_senha() -> bool:
    """Retorna True se o usuário já está autenticado."""
    try:
        senha_correta = st.secrets["APP_PASSWORD"]
    except Exception:
        return True  # sem secret configurado → acesso livre (dev local)

    if st.session_state.get("autenticado"):
        return True

    st.markdown(
        "<div style='text-align:center;padding:2rem 0'>"
        "<img src='https://raw.githubusercontent.com/davidnobrasil01-star/"
        "rota-contigo-app/main/logo.png' width='160'><br><br>"
        "<h3 style='color:#1a5c38'>🔒 Acesso Restrito</h3>"
        "<p style='color:#555'>Rota Contigo – Gerador de Contratos</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        senha = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso")
        entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")

    if entrar:
        if senha == senha_correta:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta. Tente novamente.")

    return False

if not _checar_senha():
    st.stop()

# ── App principal (só chega aqui quem passou pela senha) ──────────────────────
st.markdown(
    "<h2 style='color:#1a5c38;text-align:center'>🚌 Rota Contigo</h2>"
    "<p style='text-align:center;color:#777;margin-top:-10px'>"
    "Gerador de Contrato de Serviços Turísticos</p>",
    unsafe_allow_html=True,
)
st.divider()

TIPO_EXCURSAO     = "Contrato de Excursão"
TIPO_PASSAGEM_PF  = "Termo de Intermediação – Passagem Aérea (Pessoa Física)"
TIPO_PJ_GERAL     = "Termo de Intermediação Corporativo – Condições Gerais (assinar 1x)"
TIPO_PJ_PEDIDO    = "Pedido de Emissão Corporativo (uma passagem)"

tipo_documento = st.radio(
    "Tipo de documento",
    [TIPO_EXCURSAO, TIPO_PASSAGEM_PF, TIPO_PJ_GERAL, TIPO_PJ_PEDIDO],
    horizontal=True,
)
if tipo_documento == TIPO_PJ_PEDIDO:
    st.caption("A empresa precisa ter o Termo de Intermediação Corporativo – Condições Gerais assinado antes do primeiro pedido.")
st.divider()

with st.form("contrato_form"):

    if tipo_documento == TIPO_PJ_GERAL:
        # ── Dados da Empresa Contratante ────────────────────────────────────
        st.markdown("### 🏢 Dados da Empresa Contratante")

        col1, col2 = st.columns(2)
        with col1:
            razao_social = st.text_input("Razão social *")
        with col2:
            cnpj_empresa = st.text_input("CNPJ *", placeholder="00.000.000/0000-00")

        endereco_empresa = st.text_input("Endereço completo *", placeholder="Rua, número, bairro, cidade – UF, CEP")

        col1, col2 = st.columns(2)
        with col1:
            responsavel_nome  = st.text_input("Nome do responsável/solicitante *")
            responsavel_email = st.text_input("E-mail do responsável *")
        with col2:
            responsavel_cargo     = st.text_input("Cargo do responsável *")
            responsavel_telefone  = st.text_input("Telefone/WhatsApp do responsável *", placeholder="(41) 99999-9999")

    elif tipo_documento == TIPO_PJ_PEDIDO:
        # ── Empresa e referência ao Termo Geral ─────────────────────────────
        st.markdown("### 🏢 Empresa e Termo Geral já assinado")
        col1, col2 = st.columns(2)
        with col1:
            razao_social = st.text_input("Razão social *")
        with col2:
            cnpj_empresa = st.text_input("CNPJ *", placeholder="00.000.000/0000-00")
        data_termo_geral = st.date_input(
            "Data em que o Termo de Intermediação Corporativo – Condições Gerais foi assinado *",
            max_value=date.today())

        col1, col2 = st.columns(2)
        with col1:
            responsavel_nome  = st.text_input("Nome do responsável/solicitante *")
            responsavel_email = st.text_input("E-mail do responsável *")
        with col2:
            responsavel_telefone = st.text_input("Telefone/WhatsApp do responsável *", placeholder="(41) 99999-9999")

        st.divider()
        st.markdown("### 🧍 Dados do Passageiro")
        col1, col2 = st.columns(2)
        with col1:
            passageiro_nome = st.text_input("Nome completo do passageiro *")
        with col2:
            passageiro_cpf = st.text_input("CPF do passageiro *", placeholder="000.000.000-00")

    else:
        # ── Dados do Contratante ──────────────────────────────────────────
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

    if tipo_documento == TIPO_EXCURSAO:
        # ── Participantes adicionais ──────────────────────────────────────
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

        # ── Dados da Excursão ───────────────────────────────────────────────
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

        # ── Serviços Inclusos ───────────────────────────────────────────────
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

    elif tipo_documento == TIPO_PJ_GERAL:
        # ── Forma de Pagamento (faturado, definida uma vez) ─────────────────
        st.markdown("### 💳 Forma de Pagamento")
        st.caption("Todos os Pedidos de Emissão feitos sob este Termo serão cobrados por fatura, nesta periodicidade.")

        col1, col2 = st.columns(2)
        with col1:
            periodicidade_faturamento = st.selectbox(
                "Periodicidade de faturamento *", ["15", "30"], index=1)
        with col2:
            prazo_faturamento = st.number_input(
                "Prazo de vencimento da fatura (dias) *", min_value=1, max_value=90, value=15, step=1)

    else:
        # ── Dados da Passagem Aérea ─────────────────────────────────────────
        st.markdown("### ✈️ Dados da Passagem Aérea")

        col1, col2 = st.columns(2)
        with col1:
            origem = st.text_input("Origem *", placeholder="ex: Curitiba (CWB)")
        with col2:
            destino_pass = st.text_input("Destino *", placeholder="ex: Maceió (MCZ)")

        ida_volta = st.checkbox("Ida e volta", value=True)
        col1, col2 = st.columns(2)
        with col1:
            data_ida = st.date_input("Data de ida *", min_value=date.today())
        with col2:
            data_volta = st.date_input(
                "Data de volta *", min_value=date.today()) if ida_volta else None

        col1, col2 = st.columns(2)
        with col1:
            companhia = st.text_input("Companhia aérea *", placeholder="ex: Azul, LATAM, GOL")
        with col2:
            localizador = st.text_input("Localizador (se já emitido)", placeholder="opcional")

        st.markdown("**Valores**")
        col1, col2 = st.columns(2)
        with col1:
            valor_tarifa = st.number_input(
                "Valor da tarifa aérea (R$) *", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            valor_taxa = st.number_input(
                "Taxa de serviço (R$) *", min_value=0.0, step=0.01, format="%.2f")

        valor_extenso_pass = st.text_input(
            "Valor total por extenso *",
            placeholder="ex: dois mil quatrocentos e setenta e sete reais")

        if tipo_documento == TIPO_PASSAGEM_PF:
            forma_pagamento = st.selectbox(
                "Forma de pagamento *",
                ["Pix", "Transferência bancária", "Cartão de crédito", "Cartão de débito"])
        # TIPO_PJ_PEDIDO não pergunta forma de pagamento aqui — já está
        # definida no Termo de Intermediação Corporativo – Condições Gerais.

    st.divider()

    # ── Data do Contrato ──────────────────────────────────────────────────
    st.markdown("### 📅 Data do Contrato")
    data_contrato = st.date_input("Data de assinatura *", value=date.today())

    st.divider()

    # ── Envio Autentique (opcional) ───────────────────────────────────────
    api_token    = ""
    via_whatsapp = False
    modo_sandbox = True  # ← SANDBOX ATIVO: troque para False quando quiser cobrar

    st.markdown("### ✍️ Assinatura Digital")
    usar_autentique = st.checkbox(
        "📲 Enviar para o cliente assinar pelo WhatsApp/e-mail (Autentique)",
        value=True
    )

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


    st.divider()

    _labels_botao = {
        TIPO_EXCURSAO:    "📄 Gerar Contrato PDF",
        TIPO_PASSAGEM_PF: "📄 Gerar Termo PDF",
        TIPO_PJ_GERAL:    "📄 Gerar Termo Geral PDF",
        TIPO_PJ_PEDIDO:   "📄 Gerar Pedido de Emissão PDF",
    }
    submitted = st.form_submit_button(
        _labels_botao[tipo_documento],
        type="primary",
        use_container_width=True,
    )

# ── Validação e Geração ───────────────────────────────────────────────────────
if submitted:
    pdf_bytes     = None
    nome_arquivo  = None
    _labels_doc = {
        TIPO_EXCURSAO:    "Contrato",
        TIPO_PASSAGEM_PF: "Termo",
        TIPO_PJ_GERAL:    "Termo Geral",
        TIPO_PJ_PEDIDO:   "Pedido de Emissão",
    }
    label_doc     = _labels_doc[tipo_documento]
    mensagem_intro = "Segue o contrato da sua excursão com a Rota Contigo."

    if tipo_documento == TIPO_EXCURSAO:
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

            nome_arquivo = (
                f"Contrato_RotaContigo"
                f"_{nome.split()[0]}"
                f"_{destino.replace(' ', '_').replace('–','-')}"
                f"_{fmt_data(data_viagem).replace('/','')}.pdf"
            )
            mensagem_intro = "Segue o contrato da sua excursão com a Rota Contigo."
            nome_cliente_aut     = nome.strip()
            email_cliente_aut    = email.strip()
            telefone_cliente_aut = celular.strip()

    elif tipo_documento == TIPO_PASSAGEM_PF:
        erros = []
        if not nome.strip():               erros.append("Nome completo")
        if not cpf.strip():                erros.append("CPF")
        if not rg.strip():                 erros.append("RG")
        if not celular.strip():            erros.append("Celular/WhatsApp")
        if not email.strip():              erros.append("E-mail")
        if not emergencia.strip():         erros.append("Contato de emergência")
        if not origem.strip():             erros.append("Origem")
        if not destino_pass.strip():       erros.append("Destino")
        if not companhia.strip():          erros.append("Companhia aérea")
        if valor_tarifa <= 0:              erros.append("Valor da tarifa aérea")
        if not valor_extenso_pass.strip(): erros.append("Valor total por extenso")
        if ida_volta and data_volta is None: erros.append("Data de volta")

        if erros:
            st.error("⚠️ Preencha os campos obrigatórios: " + ", ".join(erros))
        else:
            with st.spinner("Gerando termo, aguarde..."):
                valor_total = valor_tarifa + valor_taxa
                dados = {
                    "nome":          nome.strip(),
                    "nascimento":    nascimento,
                    "cpf":           cpf.strip(),
                    "rg":            rg.strip(),
                    "celular":       celular.strip(),
                    "email":         email.strip(),
                    "emergencia":    emergencia.strip(),
                    "origem":        origem.strip(),
                    "destino":       destino_pass.strip(),
                    "data_ida":      data_ida,
                    "ida_e_volta":   ida_volta,
                    "data_volta":    data_volta,
                    "companhia":     companhia.strip(),
                    "localizador":   localizador.strip(),
                    "valor_tarifa_fmt": fmt_valor(valor_tarifa),
                    "valor_taxa_fmt":   fmt_valor(valor_taxa),
                    "valor_total_fmt":  fmt_valor(valor_total),
                    "valor_extenso":    valor_extenso_pass.strip(),
                    "forma_pagamento":  forma_pagamento,
                    "data_contrato":    data_contrato,
                }
                pdf_bytes = gerar_pdf_passagem(dados)

            nome_arquivo = (
                f"Termo_Intermediacao_RotaContigo"
                f"_{nome.split()[0]}"
                f"_{destino_pass.replace(' ', '_').replace('–','-')}"
                f"_{fmt_data(data_ida).replace('/','')}.pdf"
            )
            mensagem_intro = "Segue o termo de intermediação da sua passagem aérea com a Rota Contigo."
            nome_cliente_aut     = nome.strip()
            email_cliente_aut    = email.strip()
            telefone_cliente_aut = celular.strip()

    elif tipo_documento == TIPO_PJ_GERAL:
        erros = []
        if not razao_social.strip():         erros.append("Razão social")
        if not cnpj_empresa.strip():         erros.append("CNPJ")
        if not endereco_empresa.strip():     erros.append("Endereço da empresa")
        if not responsavel_nome.strip():     erros.append("Nome do responsável")
        if not responsavel_cargo.strip():    erros.append("Cargo do responsável")
        if not responsavel_email.strip():    erros.append("E-mail do responsável")
        if not responsavel_telefone.strip(): erros.append("Telefone do responsável")

        if erros:
            st.error("⚠️ Preencha os campos obrigatórios: " + ", ".join(erros))
        else:
            with st.spinner("Gerando termo geral, aguarde..."):
                dados = {
                    "razao_social":         razao_social.strip(),
                    "cnpj_empresa":         cnpj_empresa.strip(),
                    "endereco_empresa":     endereco_empresa.strip(),
                    "responsavel_nome":     responsavel_nome.strip(),
                    "responsavel_cargo":    responsavel_cargo.strip(),
                    "responsavel_email":    responsavel_email.strip(),
                    "responsavel_telefone": responsavel_telefone.strip(),
                    "periodicidade_faturamento": periodicidade_faturamento,
                    "prazo_faturamento":         prazo_faturamento,
                    "data_contrato":             data_contrato,
                }
                pdf_bytes = gerar_pdf_corporativo_geral(dados)

            nome_arquivo = (
                f"Termo_Corporativo_Geral_RotaContigo"
                f"_{razao_social.split()[0]}"
                f"_{fmt_data(data_contrato).replace('/','')}.pdf"
            )
            mensagem_intro = (
                f"Segue o Termo de Intermediação Corporativo – Condições Gerais da "
                f"{razao_social.strip()} com a Rota Contigo."
            )
            nome_cliente_aut     = responsavel_nome.strip()
            email_cliente_aut    = responsavel_email.strip()
            telefone_cliente_aut = responsavel_telefone.strip()

    else:  # TIPO_PJ_PEDIDO
        erros = []
        if not razao_social.strip():         erros.append("Razão social")
        if not cnpj_empresa.strip():         erros.append("CNPJ")
        if not responsavel_nome.strip():     erros.append("Nome do responsável")
        if not responsavel_email.strip():    erros.append("E-mail do responsável")
        if not responsavel_telefone.strip(): erros.append("Telefone do responsável")
        if not passageiro_nome.strip():      erros.append("Nome do passageiro")
        if not passageiro_cpf.strip():       erros.append("CPF do passageiro")
        if not origem.strip():               erros.append("Origem")
        if not destino_pass.strip():         erros.append("Destino")
        if not companhia.strip():            erros.append("Companhia aérea")
        if valor_tarifa <= 0:                erros.append("Valor da tarifa aérea")
        if not valor_extenso_pass.strip():   erros.append("Valor total por extenso")
        if ida_volta and data_volta is None: erros.append("Data de volta")

        if erros:
            st.error("⚠️ Preencha os campos obrigatórios: " + ", ".join(erros))
        else:
            with st.spinner("Gerando pedido de emissão, aguarde..."):
                valor_total = valor_tarifa + valor_taxa
                dados = {
                    "data_termo_geral": data_termo_geral,
                    "razao_social":     razao_social.strip(),
                    "cnpj_empresa":     cnpj_empresa.strip(),
                    "passageiro_nome":  passageiro_nome.strip(),
                    "passageiro_cpf":   passageiro_cpf.strip(),
                    "origem":        origem.strip(),
                    "destino":       destino_pass.strip(),
                    "data_ida":      data_ida,
                    "ida_e_volta":   ida_volta,
                    "data_volta":    data_volta,
                    "companhia":     companhia.strip(),
                    "localizador":   localizador.strip(),
                    "valor_tarifa_fmt": fmt_valor(valor_tarifa),
                    "valor_taxa_fmt":   fmt_valor(valor_taxa),
                    "valor_total_fmt":  fmt_valor(valor_total),
                    "valor_extenso":    valor_extenso_pass.strip(),
                    "data_pedido":      data_contrato,
                }
                pdf_bytes = gerar_pdf_pedido_emissao(dados)

            nome_arquivo = (
                f"Pedido_Emissao_RotaContigo"
                f"_{razao_social.split()[0]}"
                f"_{passageiro_nome.split()[0]}"
                f"_{fmt_data(data_ida).replace('/','')}.pdf"
            )
            mensagem_intro = (
                f"Segue o pedido de emissão da passagem aérea de "
                f"{passageiro_nome.strip()} para a {razao_social.strip()} com a Rota Contigo."
            )
            nome_cliente_aut     = responsavel_nome.strip()
            email_cliente_aut    = responsavel_email.strip()
            telefone_cliente_aut = responsavel_telefone.strip()

    if pdf_bytes:
        st.success(f"✅ {label_doc} gerado com sucesso!")

        st.download_button(
            label=f"⬇️ Baixar {label_doc} PDF",
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
                            nome_cliente     = nome_cliente_aut,
                            email_cliente    = email_cliente_aut,
                            telefone_cliente = telefone_cliente_aut,
                            nome_arquivo     = nome_arquivo,
                            api_token        = api_token.strip(),
                            via_whatsapp     = enviar_whatsapp,
                            via_email        = enviar_email,
                            sandbox          = modo_sandbox,
                            mensagem_intro   = mensagem_intro,
                        )

                        if "errors" in resultado:
                            st.error(f"❌ Erro Autentique: {resultado['errors'][0]['message']}")
                        else:
                            doc_id = resultado["data"]["createDocument"]["id"]
                            sigs   = resultado["data"]["createDocument"]["signatures"]

                            st.success(f"✅ {label_doc} enviado para assinatura!")
                            st.markdown("---")
                            st.markdown("**📋 Links de assinatura:**")

                            for s in sigs:
                                link_obj = s.get("link") or {}
                                link = link_obj.get("short_link", "")
                                if link:
                                    eh_cliente = s.get("email", "") == email_cliente_aut
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
