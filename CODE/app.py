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

# --- ADVANCED UI INJECTION (Tabs & Spacing) ---
st.markdown("""
    <style>
        /* Reduce page top padding */
        .block-container {
            padding-top: 1.5rem !important;
        }
        /* Style Streamlit Tabs headers */
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
    sender_email = "regtech.admin@gmail.com"
    # NOTA: Asegúrate de poner aquí tu clave de aplicación activa de 16 letras
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
    except Exception as e:
        print(f"Advertencia: No se pudo cargar el logo para el correo: {e}")

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
st.title("🛡️ RegTech Automated Surveillance System")
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
            elif language == "Español":
                st.markdown(current_report.spanish_summary)
            else:
                st.markdown("### 🇬🇧 ENGLISH VERSION")
                st.markdown(current_report.english_summary)
                st.markdown("---")
                st.markdown("### 🇪🇸 VERSIÓN EN ESPAÑOL")
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
                            logo_path=LOGO_PATH
                        )
                        
                    if success:
                        st.toast(f"Report successfully delivered to {selected_group_to_send}!", icon="✅")
                        
                        # ENHANCED CASCADE ANIMATION WITH 16 OPAQUE SOLID PILLS
                        pills_html = """
                        <style>
                        @keyframes floatUp {
                            0% { transform: translateY(100vh) rotate(0deg); opacity: 1; }
                            85% { opacity: 1; }
                            100% { transform: translateY(-120vh) rotate(720deg); opacity: 0; }
                        }
                        .pill {
                            position: fixed;
                            bottom: -70px;
                            width: 26px; height: 65px;
                            border-radius: 35px;
                            z-index: 999999;
                            pointer-events: none;
                            animation: floatUp 4s linear forwards;
                            box-shadow: 0 5px 12px rgba(0,0,0,0.4);
                        }
                        /* Opaque, vivid, non-transparent dual color combinations */
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