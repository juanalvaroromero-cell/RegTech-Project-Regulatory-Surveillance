import datetime
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import markdown
import streamlit as st
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ==========================================
# PATH RESOLUTION FOR LOGOS & ICONS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Usamos abspath para limpiar los ".." y genere una ruta absoluta perfecta
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
        reports = session.query(RegulatoryReport).order_by(RegulatoryReport.execution_date.desc()).all()
        return reports
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return []
    finally:
        session.close()

# ==========================================
# MAILING LISTS (JSON CRUD)
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

# ==========================================
# EMAIL SENDING ENGINE
# ==========================================
def send_real_email(to_emails, language, report_date_str, report_content, logo_path):
    """
    Construye y envía un correo electrónico HTML maquetado con el logo incrustado.
    """
    #sender_email = "regtech.admin@gmail.com"
    sender_email = "juanalvaroromero@gmail.com"
    # IMPORTANTE: Reemplaza esto por tu Contraseña de Aplicación de 16 dígitos de Google
    sender_password = "eoivnindqzzosrcq" 

    msg = MIMEMultipart('related')
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')

    # Configuración de Asunto y Título según idioma
    if language == "Español":
        msg['Subject'] = f"RegTech - Informe de cambios EMA - Fecha {current_date}"
        title = f"INFORME DE CAMBIOS - Agencia Europea de Medicamentos - Fecha {report_date_str}"
    else:
        msg['Subject'] = f"RegTech - EMA Changes Report - Date {current_date}"
        title = f"CHANGES REPORT - European Medicines Agency - Date {report_date_str}"

    msg['From'] = sender_email
    msg['To'] = ", ".join(to_emails)

    # Convertir el texto de la IA (Markdown) a formato HTML
    html_report_content = markdown.markdown(report_content)

    # Construcción del cuerpo del correo en HTML con la maquetación solicitada
    html_body = f"""
    <html>
    <head></head>
    <body style="margin: 0; padding: 0; background-color: #ffffff;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="cid:logo_img" style="width: 180px; height: auto;">
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
    
    # Añadir el HTML al mensaje
    msg.attach(MIMEText(html_body, 'html'))

    # Incrustar el logo físicamente en el correo para que no dependa de enlaces externos
    try:
        with open(logo_path, 'rb') as f:
            img_data = f.read()
        image = MIMEImage(img_data, name=os.path.basename(logo_path))
        # El Content-ID relaciona la imagen adjunta con el <img src="cid:logo_img"> del HTML
        image.add_header('Content-ID', '<logo_img>')
        image.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
        msg.attach(image)
    except Exception as e:
        print(f"Advertencia: No se pudo cargar el logo para el correo: {e}")

    # Conexión al servidor SMTP de Gmail y envío
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
# HEADER
# ==========================================
st.title("RegTech Automated Surveillance System")
st.markdown("### Executive Regulatory Intelligence Dashboard")
st.markdown("---")

# ==========================================
# DATA INGESTION & SIDEBAR CONTROLS
# ==========================================
historical_reports = load_historical_reports()

with st.sidebar:
    try:
        logo_img = Image.open(LOGO_PATH)
        st.image(logo_img, use_container_width=True)
    except FileNotFoundError:
        pass 
        
    st.header("⚙️ Dashboard Controls")
    language = st.radio("Select Report Language / Idioma:", ("English", "Español"))
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
tab1, tab2 = st.tabs(["📊 Executive Dashboard", "📧 Mailing Lists Management"])

# --- TAB 1: DASHBOARD ---
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📑 AI Executive Summary ({language})")
        if current_report:
            st.info(f"Historical Report loaded from DB (Execution: {current_report.execution_date.strftime('%Y-%m-%d %H:%M:%S')})")
            
            if language == "English":
                st.markdown(current_report.english_summary)
            else:
                st.markdown(current_report.spanish_summary)
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
        
        if st.button("📨 Send Report via Email", type="primary", use_container_width=True):
            if selected_group_to_send and current_report:
                target_emails = mailing_data[selected_group_to_send]
                
                if not target_emails:
                    st.error(f"The group '{selected_group_to_send}' has no email addresses assigned.")
                else:
                    report_text = current_report.spanish_summary if language == "Español" else current_report.english_summary
                    report_date = current_report.execution_date.strftime('%Y-%m-%d %H:%M:%S')
                    
                    with st.spinner(f"Sending real email to {len(target_emails)} recipient(s)..."):
                        success, status_msg = send_real_email(
                            to_emails=target_emails, 
                            language=language, 
                            report_date_str=report_date, 
                            report_content=report_text, 
                            logo_path=LOGO_PATH
                        )
                        
                    if success:
                        st.toast(f"Report successfully delivered to {selected_group_to_send}!", icon="✅")
                        st.balloons() # Pequeño toque visual de celebración al enviar con éxito
                    else:
                        st.error(f"SMTP Server Error: {status_msg}. Please check your Gmail App Password settings.")
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

st.markdown("---")
st.caption("RegTech | Developed by Juan Alvaro Romero | Ironhack Big Data & Machine Learning MVP | © 2026")