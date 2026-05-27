import datetime
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication  # Nueva importación para adjuntar archivos
import re
from io import BytesIO

import markdown
import pandas as pd
import streamlit as st
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# Importaciones para generar PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader

# ==========================================
# PATH RESOLUTION FOR LOGOS & ICONS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "Logos_icons", "logo_regtech2.png"))
ICON_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "Logos_icons", "regtech_icon2.ico"))

try:
    app_icon = Image.open(ICON_PATH)
except FileNotFoundError:
    app_icon = "🛡️"

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="RegTech AI Surveillance",
    page_icon=app_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN CSS AVANZADA PARA UI ---
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem !important; }
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.25rem;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE CONNECTION SETUP
# ==========================================
Base = declarative_base()

class RegulatoryReport(Base):
    __tablename__ = 'regulatory_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_date = Column(DateTime, default=datetime.datetime.utcnow)
    total_alerts_captured = Column(Integer, nullable=False)
    english_summary = Column(Text, nullable=False)
    spanish_summary = Column(Text, nullable=False)
    raw_llm_payload = Column(Text, nullable=True)

DB_PATH = 'sqlite:///BD/regtech_data.db'
engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)

def load_historical_reports():
    session = SessionLocal()
    try:
        return session.query(RegulatoryReport).order_by(RegulatoryReport.execution_date.desc()).all()
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return []
    finally:
        session.close()

# ==========================================
# FUNCIONES AUXILIARES (Email, Mailing, PDF)
# ==========================================
MAILING_LIST_FILE = "mailing_lists.json"

def load_mailing_lists():
    if not os.path.exists(MAILING_LIST_FILE):
        return {"Default QA Team": ["admin@regtech.com"]}
    with open(MAILING_LIST_FILE, "r") as f:
        return json.load(f)

def save_mailing_lists(data):
    with open(MAILING_LIST_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_markdown_to_rl(text):
    text = text.replace('\n', '<br/>')
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return text

def generate_pdf_report(report, language, logo_path):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50,
        title="RegTech Official Report - EMA", 
        author="Juan Alvaro Romero | RegTech AI"
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="CustomTitle", parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=20)
    normal_style = ParagraphStyle(name="CustomNormal", parent=styles['Normal'], fontSize=11, leading=14)
    footer_style = ParagraphStyle(name="CustomFooter", parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)

    elements = []

    try:
        img_reader = ImageReader(logo_path)
        img_w, img_h = img_reader.getSize()
        aspect = img_h / float(img_w)
        rl_img = RLImage(logo_path, width=120, height=120 * aspect)
        elements.append(rl_img)
        elements.append(Spacer(1, 20))
    except Exception:
        pass

    date_str = report.execution_date.strftime('%Y-%m-%d %H:%M:%S')
    if language == "Español":
        doc_title = f"INFORME DE CAMBIOS - EMA<br/><font size='12'>Fecha: {date_str}</font>"
    elif language == "English":
        doc_title = f"CHANGES REPORT - EMA<br/><font size='12'>Date: {date_str}</font>"
    else:
        doc_title = f"INFORME DE CAMBIOS / CHANGES REPORT - EMA<br/><font size='12'>Date: {date_str}</font>"

    elements.append(Paragraph(doc_title, title_style))
    elements.append(Spacer(1, 20))

    if language == "Español":
        content = parse_markdown_to_rl(report.spanish_summary)
    elif language == "English":
        content = parse_markdown_to_rl(report.english_summary)
    else:
        content = "<b>🇬🇧 ENGLISH VERSION</b><br/><br/>" + parse_markdown_to_rl(report.english_summary) + "<br/><br/><hr/><br/><b>🇪🇸 VERSIÓN EN ESPAÑOL</b><br/><br/>" + parse_markdown_to_rl(report.spanish_summary)

    elements.append(Paragraph(content, normal_style))

    elements.append(Spacer(1, 40))
    pdf_footer_text = """
    <b>
    <font color="#D32F2F">Reg</font><font color="#F5B041">Tech</font>
    <font color="#27AE60"> | </font>
    <font color="#D32F2F">Developed</font>
    <font color="#F5B041">by</font>
    <font color="#27AE60">Juan</font>
    <font color="#D32F2F">Alvaro</font>
    <font color="#F5B041">Romero</font>
    <font color="#27AE60"> | </font>
    <font color="#D32F2F">Ironhack</font>
    <font color="#F5B041">Big</font>
    <font color="#27AE60">Data</font>
    <font color="#D32F2F">&amp;</font>
    <font color="#F5B041">Machine</font>
    <font color="#27AE60">Learning</font>
    <font color="#D32F2F">MVP</font>
    <font color="#F5B041"> | </font>
    <font color="#27AE60">&copy;</font>
    <font color="#D32F2F">2026</font>
    </b>
    """
    elements.append(Paragraph(pdf_footer_text, footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# Actualizada la firma de la función para admitir el adjunto opcional
def send_real_email(to_emails, language, report_date_str, report_content, logo_path, attach_pdf=False, pdf_data=None):
    sender_email = "regtech.admin@gmail.com"
    sender_password = "qjripfjgtkapmonn" 

    msg = MIMEMultipart('related')
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')

    if language == "Español":
        msg['Subject'] = f"RegTech - Informe de cambios EMA - Fecha {current_date}"
        title = f"INFORME DE CAMBIOS - Agencia Europea de Medicamentos - Fecha {report_date_str}"
    elif language == "English":
        msg['Subject'] = f"RegTech - EMA Changes Report - Date {current_date}"
        title = f"CHANGES REPORT - European Medicines Agency - Date {report_date_str}"
    else:
        msg['Subject'] = f"RegTech - Informe / Report EMA - {current_date}"
        title = f"INFORME DE CAMBIOS / CHANGES REPORT - EMA - {report_date_str}"

    msg['From'] = sender_email
    msg['To'] = ", ".join(to_emails)

    html_report_content = markdown.markdown(report_content)
    html_body = f"""
    <html>
    <head></head>
    <body style="margin: 0; padding: 0; background-color: #ffffff;">
        <div style="width: 95%; max-width: 1200px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="cid:logo_img" style="width: 150px; height: auto;">
            </div>
            <h1 style="font-family: Verdana, sans-serif; font-size: 20px; font-weight: bold; text-align: center; color: #1a1a1a; margin-bottom: 40px;">
                {title}
            </h1>
            <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333333; line-height: 1.6;">
                {html_report_content}
            </div>
            <br><br><br>
            <hr style="border: 0; border-top: 1px solid #e0e0e0; margin-bottom: 20px;">
            <p style="font-family: Verdana, sans-serif; font-size: 10px; text-align: center; color: #7f8c8d;">
                RegTech - Developed by Juan Alvaro Romero | Ironhack Big Data & Machine Learning MVP | &copy; 2026
            </p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with open(logo_path, 'rb') as f:
            img_data = f.read()
        image = MIMEImage(img_data, name=os.path.basename(logo_path))
        image.add_header('Content-ID', '<logo_img>')
        image.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
        msg.attach(image)
    except Exception:
        pass

    # --- LÓGICA DE ADJUNTADO DE ARCHIVOS REAL ---
    if attach_pdf and pdf_data:
        try:
            # Formateamos el nombre del archivo para quitar caracteres conflictivos
            safe_date = report_date_str.replace(":", "-").replace(" ", "_")
            pdf_filename = f"RegTech_Official_Report_{safe_date}.pdf"

            part = MIMEApplication(pdf_data, _subtype="pdf")
            part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
            msg.attach(part)
        except Exception as e:
            print(f"Error empaquetando el adjunto PDF: {e}")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado correctamente."
    except Exception as e:
        return False, str(e)

# ==========================================
# HEADER (Icono Personalizado Integrado)
# ==========================================
col_icon, col_title = st.columns([1, 15])
with col_icon:
    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
    try:
        header_icon = Image.open(ICON_PATH)
        st.image(header_icon, width=60)
    except Exception:
        st.write("🛡️")

with col_title:
    st.title("RegTech Automated Surveillance System")

st.markdown("---")

# ==========================================
# DATA INGESTION & SIDEBAR CONTROLS
# ==========================================
historical_reports = load_historical_reports()

with st.sidebar:
    try:
        logo_img = Image.open(LOGO_PATH)
        st.image(logo_img, width='stretch')
    except FileNotFoundError:
        pass 

    st.header("⚙️ Dashboard Controls")
    language = st.radio("Select Report Language / Idioma:", ("English", "Español", "English & Español"))
    st.markdown("---")

    current_report = None
    if not historical_reports:
        st.warning("No historical reports found in the database. Run the pipeline in Jupyter first.")
    else:
        report_options = {r.execution_date.strftime("%Y-%m-%d %H:%M:%S"): r for r in historical_reports}
        selected_date = st.selectbox("Select Historical Run / Historial:", list(report_options.keys()))
        current_report = report_options[selected_date]

        st.metric(label="Target Source", value="EMA Guidelines")
        st.metric(label="Critical Alerts Detected", value=current_report.total_alerts_captured)

# ==========================================
# MAIN NAVIGATION TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Executive Dashboard", "📧 Mailing Lists Management", "📈 Analytics Trends"])

# --- TAB 1: DASHBOARD ---
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📑 AI Executive Summary ({language})")
        if current_report:
            st.info(f"Historical Report loaded from DB (Execution: {current_report.execution_date.strftime('%Y-%m-%d %H:%M:%S')})")

            if language == "English":
                st.markdown(current_report.english_summary)
            elif language == "Español":
                st.markdown(current_report.spanish_summary)
            else:
                st.markdown("### 🇬🇧 ENGLISH VERSION")
                st.markdown(current_report.english_summary)
                st.markdown("---")
                st.markdown("### 🇪🇸 VERSIÓN EN ESPAÑOL")
                st.markdown(current_report.spanish_summary)

            st.markdown("---")
            pdf_data = generate_pdf_report(current_report, language, LOGO_PATH)
            st.download_button(
                label="📥 Download Official PDF Report",
                data=pdf_data,
                file_name=f"RegTech_Report_{current_report.execution_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.info("Awaiting pipeline execution...")

    with col2:
        st.subheader("📊 System Status")
        st.success("✅ Baseline Synchronized")
        st.success("✅ NLP Engine Online")
        st.success("✅ Database Committed")

        st.markdown("### Actions")
        mailing_data = load_mailing_lists()
        selected_group_to_send = st.selectbox("Send Alert To:", list(mailing_data.keys()) if mailing_data else ["No groups available"])

        # --- NUEVA OPCIÓN: Checkbox para adjuntar PDF ---
        attach_pdf_choice = st.checkbox("📎 Adjuntar informe oficial PDF / Attach PDF Document", value=False)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📨 Send Report via Email", type="primary", width='stretch'):
            if selected_group_to_send and current_report:
                target_emails = mailing_data[selected_group_to_send]
                if not target_emails:
                    st.error(f"The group '{selected_group_to_send}' has no email addresses assigned.")
                else:
                    if language == "Español":
                        report_text = current_report.spanish_summary
                    elif language == "English":
                        report_text = current_report.english_summary
                    else:
                        report_text = f"### 🇬🇧 ENGLISH VERSION\n{current_report.english_summary}\n\n---\n\n### 🇪🇸 VERSIÓN EN ESPAÑOL\n{current_report.spanish_summary}"

                    report_date = current_report.execution_date.strftime('%Y-%m-%d %H:%M:%S')

                    with st.spinner(f"Sending real email to {len(target_emails)} recipient(s)..."):
                        success, status_msg = send_real_email(
                            to_emails=target_emails, 
                            language=language, 
                            report_date_str=report_date, 
                            report_content=report_text, 
                            logo_path=LOGO_PATH,
                            attach_pdf=attach_pdf_choice, # Pasamos la elección del usuario
                            pdf_data=pdf_data             # Pasamos los bytes cargados
                        )

                    if success:
                        st.toast(f"Report successfully delivered to {selected_group_to_send}!", icon="✅")
                        pills_html = """
                        <style>
                        @keyframes floatUp { 0% { transform: translateY(100vh) rotate(0deg); opacity: 1; } 85% { opacity: 1; } 100% { transform: translateY(-120vh) rotate(720deg); opacity: 0; } }
                        .pill { position: fixed; bottom: -70px; width: 26px; height: 65px; border-radius: 35px; z-index: 999999; pointer-events: none; animation: floatUp 4s linear forwards; box-shadow: 0 5px 12px rgba(0,0,0,0.4); }
                        .p1  { left: 5%;  background: linear-gradient(to bottom, #D32F2F 50%, #F5B041 50%); animation-duration: 3.0s; animation-delay: 0.0s; }
                        .p2  { left: 11%; background: linear-gradient(to bottom, #2E86C1 50%, #EEEEEE 50%); animation-duration: 3.8s; animation-delay: 0.4s; }
                        .p3  { left: 18%; background: linear-gradient(to bottom, #27AE60 50%, #D32F2F 50%); animation-duration: 3.4s; animation-delay: 0.1s; }
                        .p4  { left: 24%; background: linear-gradient(to bottom, #E67E22 50%, #FFFFFF 50%); animation-duration: 4.2s; animation-delay: 0.6s; }
                        .p5  { left: 31%; background: linear-gradient(to bottom, #8E44AD 50%, #2ECC71 50%); animation-duration: 3.1s; animation-delay: 0.2s; }
                        .p6  { left: 37%; background: linear-gradient(to bottom, #F4D03F 50%, #17A589 50%); animation-duration: 4.5s; animation-delay: 0.8s; }
                        .p7  { left: 44%; background: linear-gradient(to bottom, #D32F2F 50%, #FFFFFF 50%); animation-duration: 3.3s; animation-delay: 0.3s; }
                        .p8  { left: 50%; background: linear-gradient(to bottom, #2E86C1 50%, #F5B041 50%); animation-duration: 3.9s; animation-delay: 0.7s; }
                        .p9  { left: 56%; background: linear-gradient(to bottom, #27AE60 50%, #FFFFFF 50%); animation-duration: 3.6s; animation-delay: 0.1s; }
                        .p10 { left: 63%; background: linear-gradient(to bottom, #E67E22 50%, #D32F2F 50%); animation-duration: 4.1s; animation-delay: 0.5s; }
                        .p11 { left: 69%; background: linear-gradient(to bottom, #8E44AD 50%, #F4D03F 50%); animation-duration: 3.2s; animation-delay: 0.9s; }
                        .p12 { left: 75%; background: linear-gradient(to bottom, #111111 50%, #EEEEEE 50%); animation-duration: 4.4s; animation-delay: 0.2s; }
                        .p13 { left: 81%; background: linear-gradient(to bottom, #D32F2F 50%, #2E86C1 50%); animation-duration: 3.5s; animation-delay: 0.6s; }
                        .p14 { left: 87%; background: linear-gradient(to bottom, #2ECC71 50%, #F5B041 50%); animation-duration: 4.0s; animation-delay: 0.3s; }
                        .p15 { left: 93%; background: linear-gradient(to bottom, #E67E22 50%, #17A589 50%); animation-duration: 3.7s; animation-delay: 0.7s; }
                        .p16 { left: 40%; background: linear-gradient(to bottom, #F4D03F 50%, #D32F2F 50%); animation-duration: 3.9s; animation-delay: 0.4s; }
                        </style>
                        <div class="pill p1"></div><div class="pill p2"></div><div class="pill p3"></div><div class="pill p4"></div>
                        <div class="pill p5"></div><div class="pill p6"></div><div class="pill p7"></div><div class="pill p8"></div>
                        <div class="pill p9"></div><div class="pill p10"></div><div class="pill p11"></div><div class="pill p12"></div>
                        <div class="pill p13"></div><div class="pill p14"></div><div class="pill p15"></div><div class="pill p16"></div>
                        """
                        st.markdown(pills_html, unsafe_allow_html=True)
                    else:
                        st.error(f"SMTP Server Error: {status_msg}")
            elif not current_report:
                st.error("No report available to send.")
            else:
                st.error("Please create a mailing group first.")

# --- TAB 2: MAILING LISTS ---
with tab2:
    st.subheader("Distribution Groups")
    mailing_lists = load_mailing_lists()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("#### Create New Group")
        with st.form("new_group_form", clear_on_submit=True):
            new_group_name = st.text_input("Group Name (e.g., Compliance Team)")
            submit_new_group = st.form_submit_button("Create Group")
            if submit_new_group and new_group_name:
                if new_group_name not in mailing_lists:
                    mailing_lists[new_group_name] = []
                    save_mailing_lists(mailing_lists)
                    st.success(f"Group '{new_group_name}' created.")
                    st.rerun()
                else:
                    st.error("Group already exists.")

    with col_right:
        st.markdown("#### Manage Existing Groups")
        if not mailing_lists:
            st.warning("No mailing groups found. Create one first.")
        else:
            selected_group = st.selectbox("Select a group to manage:", list(mailing_lists.keys()))

            if selected_group:
                with st.form("add_email_form", clear_on_submit=True):
                    new_email = st.text_input(f"Add email to '{selected_group}'")
                    submit_new_email = st.form_submit_button("Add Email")
                    if submit_new_email and new_email:
                        if new_email not in mailing_lists[selected_group]:
                            mailing_lists[selected_group].append(new_email)
                            save_mailing_lists(mailing_lists)
                            st.success(f"{new_email} added.")
                            st.rerun()
                        else:
                            st.warning("Email already in list.")

                st.markdown(f"**Current Emails in {selected_group}:**")
                if len(mailing_lists[selected_group]) == 0:
                    st.info("Empty list.")
                else:
                    for email in mailing_lists[selected_group]:
                        e_col1, e_col2 = st.columns([4, 1])
                        e_col1.write(f"📧 {email}")
                        if e_col2.button("🗑️", key=f"del_{selected_group}_{email}"):
                            mailing_lists[selected_group].remove(email)
                            save_mailing_lists(mailing_lists)
                            st.rerun()

                st.markdown("---")
                if st.button(f"🚨 Delete Group '{selected_group}'", type="secondary"):
                    del mailing_lists[selected_group]
                    save_mailing_lists(mailing_lists)
                    st.rerun()

# --- TAB 3: ANALYTICS TRENDS ---
with tab3:
    st.subheader("📊 Historical Analytics & Regulatory Trends")
    if historical_reports:
        chrono_reports = list(reversed(historical_reports))

        dates = [r.execution_date.strftime('%Y-%m-%d %H:%M') for r in chrono_reports]
        alerts = [r.total_alerts_captured for r in chrono_reports]

        if len(chrono_reports) == 1:
            initial_date = (chrono_reports[0].execution_date - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
            dates.insert(0, initial_date)
            alerts.insert(0, 0)

        df_trends = pd.DataFrame({
            "Execution Date": dates,
            "Critical Alerts Captured": alerts
        })

        st.markdown("### KPI Summary")
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        kpi_col1.metric("Total Executions", len(historical_reports))
        kpi_col2.metric("Total Alerts (All Time)", sum(r.total_alerts_captured for r in historical_reports))

        avg = round(sum(r.total_alerts_captured for r in historical_reports) / len(historical_reports), 1)
        kpi_col3.metric("Avg Alerts per Run", avg)

        st.markdown("---")
        st.markdown("### Alert Volume Over Time")
        st.line_chart(df_trends.set_index("Execution Date"))

    else:
        st.info("Not enough historical data to generate trends. Run the pipeline a few times!")

# ==========================================
# COLORFUL FOOTER
# ==========================================
st.markdown("---")
footer_html = """
<div style="font-size: 12px; font-weight: bold; text-align: center; margin-top: 10px; padding-bottom: 20px;">
    <span style="color: #D32F2F;">Reg</span><span style="color: #F5B041;">Tech</span>
    <span style="color: #27AE60;"> | </span>
    <span style="color: #D32F2F;">Developed</span>
    <span style="color: #F5B041;">by</span>
    <span style="color: #27AE60;">Juan</span>
    <span style="color: #D32F2F;">Alvaro</span>
    <span style="color: #F5B041;">Romero</span>
    <span style="color: #27AE60;"> | </span>
    <span style="color: #D32F2F;">Ironhack</span>
    <span style="color: #F5B041;">Big</span>
    <span style="color: #27AE60;">Data</span>
    <span style="color: #D32F2F;">&</span>
    <span style="color: #F5B041;">Machine</span>
    <span style="color: #27AE60;">Learning</span>
    <span style="color: #D32F2F;">MVP</span>
    <span style="color: #F5B041;"> | </span>
    <span style="color: #27AE60;">&copy;</span>
    <span style="color: #D32F2F;">2026</span>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
