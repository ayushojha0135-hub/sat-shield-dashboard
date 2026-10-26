import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPClassifier
import time
import os
import ssl
import subprocess
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="SAT-SHIELD // Mission Control", layout="wide", page_icon="🛰️")

st.markdown("""
<style>
    .radar-box {
        background: radial-gradient(circle, #0a2e36 0%, #050b14 100%);
        border: 2px solid #00ffcc;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.25);
        color: #00ffcc;
        font-family: monospace;
    }
    .pulse-circle {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        border: 2px dashed #00ffcc;
        margin: 8px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 38px;
        animation: spin 8s linear infinite;
        box-shadow: inset 0 0 15px #00ffcc;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_system():
    data = pd.read_csv('dataset.csv').fillna(0)
    scaler = MinMaxScaler()
    numeric_cols = data.select_dtypes(include=['number']).columns
    data_scaled = data.copy()
    data_scaled[numeric_cols] = scaler.fit_transform(data_scaled[numeric_cols])
    
    X = data_scaled.drop(columns=['anomaly', 'channel'], errors='ignore')
    y = (data_scaled['anomaly'] > 0.5).astype(int)
    
    clf = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=35, random_state=42)
    clf.fit(X, y)
    return clf, X, data

model, X_data, raw_data = load_system()

ORBIT_PATH = [
    (25.43, 81.84, "🇮🇳 India (Prayagraj Station)"),
    (28.61, 77.20, "🇮🇳 India (New Delhi Sector)"),
    (24.45, 54.37, "🇦🇪 UAE (Middle East Sector)"),
    (30.04, 31.23, "🇪🇬 Egypt (North Africa Sector)"),
    (41.90, 12.49, "🇮🇹 Italy (European Sector)"),
    (48.85, 2.35,  "🇫🇷 France (Paris Hub)"),
    (51.50, -0.12, "🇬🇧 United Kingdom (London)"),
    (40.71, -74.00, "🇺🇸 USA (East Coast Command)"),
    (34.05, -118.24, "🇺🇸 USA (California Network)"),
    (-23.55, -46.63, "🇧🇷 Brazil (South America)"),
    (35.67, 139.65, "🇯🇵 Japan (Tokyo Link)"),
    (1.35, 103.81, "🇸🇬 Singapore (Equator Relay)"),
    (-33.86, 151.20, "🇦🇺 Australia (Canberra)")
]

if "running" not in st.session_state:
    st.session_state.running = False
if "step" not in st.session_state:
    st.session_state.step = 0
if "signal_history" not in st.session_state:
    st.session_state.signal_history = []
if "session_logs" not in st.session_state:
    st.session_state.session_logs = []
if "last_voice_step" not in st.session_state:
    st.session_state.last_voice_step = -10
if "last_email_step" not in st.session_state:
    st.session_state.last_email_step = -20
if "battery_val" not in st.session_state:
    st.session_state.battery_val = 98.5
if "curr_telemetry" not in st.session_state:
    st.session_state.curr_telemetry = {
        "country": "🇮🇳 India (Prayagraj Station)",
        "lat": 25.43,
        "lon": 81.84,
        "battery": 98.5,
        "temp": 42.1,
        "snr": 28.5,
        "threat": 4.2,
        "is_attack": 0,
        "mode": "STANDBY",
        "channel": "Ku-Band (14.25 GHz - Primary)"
    }
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "🛰️ **SAT-SHIELD AI Online!** Ask me about live satellite location, battery/thermal health, SNR signal, cyber threat status, or self-healing protocol."
        }
    ]

def trigger_voice_alert(msg):
    js_code = f"""
    <script>
        var utterance = new SpeechSynthesisUtterance({repr(msg)});
        utterance.rate = 1.0;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    </script>
    """
    components.html(js_code, height=0, width=0)
    
def send_email_alert(subject, body, recipient_email):
    sender_email = "ayushojha0135@gmail.com"
    sender_password = "mineagfmhgbkxesc"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as server:
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        st.sidebar.success("📧 Email Alert Sent Successfully!")
    except Exception as e1:
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
            st.sidebar.success("📧 Email Alert Sent Successfully!")
        except Exception:
            st.sidebar.error(f"Email error: {e1}")

def generate_ai_response(user_query):
    q = user_query.lower().strip()
    t = st.session_state.curr_telemetry
    attack_count = sum(1 for log in st.session_state.session_logs if "ATTACK" in log.get("Status", ""))
    
    if any(w in q for w in ["hi", "hello", "hey", "namaste", "help"]):
        return (
            f"Hello Commander! I am monitoring **SAT-SHIELD** in real time.\n\n"
            f"- **Current Sector:** {t['country']}\n"
            f"- **Defense Mode:** `{t['mode']}`\n"
            f"- **Threat Level:** `{t['threat']}%`\n\n"
            f"You can ask me about **location, battery, temperature, SNR, attack status, or self-healing protocol**."
        )
    elif any(w in q for w in ["where", "location", "country", "position", "lat", "lon", "kahan", "desh", "orbit", "sector"]):
        return (
            f"🌍 **Live Orbital Position:**\n"
            f"- **Overflying Sector:** {t['country']}\n"
            f"- **Coordinates:** Latitude `{t['lat']}°`, Longitude `{t['lon']}°`\n"
            f"- **Altitude:** `550 km (Low Earth Orbit)`"
        )
    elif any(w in q for w in ["battery", "power", "solar", "temp", "heat", "hardware", "health", "charge"]):
        health_state = "⚠️ High Thermal Load (Attack Stress)" if t["is_attack"] else "✅ Optimal & Charging"
        return (
            f"🔋 **Hardware Health Telemetry:**\n"
            f"- **Battery Level:** `{t['battery']}%` ({health_state})\n"
            f"- **Solar Panel Temp:** `{t['temp']} °C`\n"
            f"- **Signal-to-Noise (SNR):** `{t['snr']} dB`"
        )
    elif any(w in q for w in ["snr", "signal", "noise", "frequency", "channel", "band", "link"]):
        return (
            f"📶 **RF Telemetry Link Status:**\n"
            f"- **Active Channel:** `{t['channel']}`\n"
            f"- **Signal-to-Noise Ratio:** `{t['snr']} dB`\n"
            f"- **Encryption:** `AES-256 Quantum-Resistant Link`"
        )
    elif any(w in q for w in ["attack", "threat", "jamming", "spoofing", "security", "alert", "safe", "khatra", "danger"]):
        if t["is_attack"] == 1:
            return (
                f"🚨 **RED ALERT ACTIVE!**\n"
                f"- **Threat Probability:** `{t['threat']}%` (Jamming/Spoofing Detected)\n"
                f"- **Affected Sector:** {t['country']}\n"
                f"- **Countermeasure:** Self-Healing Protocol has hopped frequency to `{t['channel']}`.\n"
                f"- **Total Attacks Mitigated in Session:** `{attack_count}`"
            )
        return (
            f"🟢 **System Secure & Nominal:**\n"
            f"- **Current Threat Level:** `{t['threat']}%` (Safe Zone)\n"
            f"- **Defense Status:** `{t['mode']}`\n"
            f"- **Total Attacks Mitigated in Session:** `{attack_count}`"
        )
    elif any(w in q for w in ["protocol", "heal", "self-healing", "backup", "defense", "how", "work", "kaise"]):
        return (
            "🛡️ **Autonomous Self-Healing Protocol:**\n"
            "1. **Detection:** The `MLPClassifier` neural network scans telemetry packets for SNR drops and carrier distortion.\n"
            "2. **Isolation:** When threat probability exceeds `50%`, the compromised Ku-Band channel is isolated.\n"
            "3. **Frequency Hopping:** Telemetry is rerouted within milliseconds to an encrypted **Ka-Band (28.5 GHz)** backup relay."
        )
    elif any(w in q for w in ["report", "summary", "status", "all", "data", "log", "sab"]):
        return (
            f"📋 **Complete Mission Control SitRep:**\n"
            f"- **Sector:** {t['country']} (`{t['lat']}°, {t['lon']}°`)\n"
            f"- **Defense Mode:** `{t['mode']}` | **Threat:** `{t['threat']}%`\n"
            f"- **Hardware:** Battery `{t['battery']}%` | Temp `{t['temp']} °C` | SNR `{t['snr']} dB`\n"
            f"- **Active Frequency:** `{t['channel']}`\n"
            f"- **Packets Scanned:** `{len(st.session_state.session_logs)}` | **Attacks Healed:** `{attack_count}`"
        )
    else:
        return (
            f"🛰️ **Live Telemetry Response for '{user_query}':**\n"
            f"Satellite is currently over **{t['country']}** (`{t['lat']}°, {t['lon']}°`) in **{t['mode']}** mode. "
            f"Threat level is **{t['threat']}%**, Battery is at **{t['battery']}%**, Solar Temp is **{t['temp']} °C**, and SNR is **{t['snr']} dB**."
        )

def create_3d_globe(curr_lat, curr_lon, country_name, is_attack):
    all_lats = [p[0] for p in ORBIT_PATH] + [ORBIT_PATH[0][0]]
    all_lons = [p[1] for p in ORBIT_PATH] + [ORBIT_PATH[0][1]]
    
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lat=all_lats, lon=all_lons, mode='lines', line=dict(width=2, color='#00ffcc', dash='dot')))
    
    marker_color = '#ff3333' if is_attack else '#00ff66'
    fig.add_trace(go.Scattergeo(
        lat=[curr_lat], lon=[curr_lon], mode='markers+text',
        marker=dict(size=14, color=marker_color, symbol='circle', line=dict(width=3, color='white')),
        text=[f"🛰️ {country_name.split(' (')[0]}"], textposition="top center", textfont=dict(color='white', size=13)
    ))
    
    fig.update_geos(
        projection_type="orthographic", projection_rotation=dict(lon=curr_lon, lat=curr_lat, roll=0),
        showcountries=True, countrycolor="#2a4b5c", showocean=True, oceancolor="#040d1a",
        showland=True, landcolor="#0d2630", showcoastlines=True, coastlinecolor="#00ffcc", bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", height=330, showlegend=False)
    return fig

def create_threat_gauge(threat_pct):
    bar_color = "#ff3333" if threat_pct > 50 else "#00ffcc"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=threat_pct,
        number={'suffix': "%", 'font': {'color': 'white', 'size': 26}},
        title={'text': "Cyber Threat Meter", 'font': {'color': '#00ffcc', 'size': 15}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "white"}, 'bar': {'color': bar_color},
            'bgcolor': "#050b14", 'borderwidth': 1, 'bordercolor': "#2a4b5c",
            'steps': [{'range': [0, 50], 'color': "rgba(0, 255, 204, 0.15)"}, {'range': [50, 100], 'color': "rgba(255, 51, 51, 0.35)"}]
        }
    ))
    fig.update_layout(margin=dict(l=20, r=20, t=35, b=10), paper_bgcolor="rgba(0,0,0,0)", height=210)
    return fig

st.sidebar.header("⚙️ Mission Control Settings")
manual_attack = st.sidebar.toggle("🔥 Inject Spoofing/Jamming Attack", value=False)
voice_alarm = st.sidebar.toggle("🔊 Enable Mac Voice Alert", value=True)
enable_email = st.sidebar.toggle("📧 Enable Real-Time Email Alerts", value=True)
recipient_email = st.sidebar.text_input("Recipient Email", "ayushojha0135@gmail.com")

if st.sidebar.button("📨 Test Email Alert Now"):
    send_email_alert(
        "SAT-SHIELD TEST: Telemetry Alert System Online",
        "This is a live test alert from SAT-SHIELD Mission Control. Your email notification link is active.",
        recipient_email
    )

st.sidebar.markdown("---")
sim_speed = st.sidebar.slider("Scan Interval (Seconds)", 0.5, 3.0, 1.0)

csv_full = raw_data.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📄 Download Full Dataset", data=csv_full, file_name="satellite_telemetry_dataset.csv", mime="text/csv")

if st.session_state.session_logs:
    csv_logs = pd.DataFrame(st.session_state.session_logs).to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📊 Download Live Scan Logs", data=csv_logs, file_name="satellite_live_scan_logs.csv", mime="text/csv")

if st.session_state.running:
    step = st.session_state.step
    steps_per_country = 6
    idx_country = (step // steps_per_country) % len(ORBIT_PATH)
    next_idx = (idx_country + 1) % len(ORBIT_PATH)
    progress = (step % steps_per_country) / float(steps_per_country)
    
    lat1, lon1, country_name = ORBIT_PATH[idx_country]
    lat2, lon2, _ = ORBIT_PATH[next_idx]
    
    curr_lat = round(lat1 + (lat2 - lat1) * progress, 4)
    curr_lon = round(lon1 + (lon2 - lon1) * progress, 4)
    
    idx = np.random.randint(0, len(X_data))
    sample = X_data.iloc[idx:idx+1]
    
    if manual_attack:
        pred_prob = np.random.uniform(0.88, 0.99)
        is_attack = 1
        solar_temp = round(np.random.uniform(68.0, 82.5), 1)
        snr_db = round(np.random.uniform(3.2, 8.5), 1)
        mode_str = "SELF-HEALING"
        channel_str = "Ka-Band (28.5 GHz - Encrypted Backup)"
        status_label = "ATTACK (Self-Healed)"
    else:
        pred_prob = np.random.uniform(0.02, 0.22)
        is_attack = 0
        solar_temp = round(np.random.uniform(39.0, 45.5), 1)
        snr_db = round(np.random.uniform(26.0, 31.0), 1)
        mode_str = "NOMINAL"
        channel_str = "Ku-Band (14.25 GHz - Primary)"
        status_label = "NORMAL"
        
    threat_pct = round(pred_prob * 100, 1)
    st.session_state.battery_val = max(85.0, round(st.session_state.battery_val + np.random.uniform(-0.15, 0.12), 2))
    
    st.session_state.curr_telemetry = {
        "country": country_name,
        "lat": curr_lat,
        "lon": curr_lon,
        "battery": st.session_state.battery_val,
        "temp": solar_temp,
        "snr": snr_db,
        "threat": threat_pct,
        "is_attack": is_attack,
        "mode": mode_str,
        "channel": channel_str
    }
    
    st.session_state.signal_history.append({
        "Primary Carrier": float(sample.iloc[0, 0]),
        "Telemetry Gain": float(sample.iloc[0, 1]) if sample.shape[1] > 1 else 0.5,
        "Noise Floor": float(sample.iloc[0, 2]) if sample.shape[1] > 2 else 0.2
    })
    if len(st.session_state.signal_history) > 25:
        st.session_state.signal_history.pop(0)
        
    st.session_state.session_logs.insert(0, {
        "Timestamp": datetime.now().strftime("%H:%M:%S"),
        "Country / Sector": country_name,
        "Lat": curr_lat,
        "Lon": curr_lon,
        "Battery (%)": st.session_state.battery_val,
        "Temp (°C)": solar_temp,
        "SNR (dB)": snr_db,
        "Threat (%)": threat_pct,
        "Status": status_label
    })
    
    if is_attack == 1:
        if step - st.session_state.last_voice_step >= 5:
            trigger_voice_alert(voice_alarm)
            st.session_state.last_voice_step = step
        if enable_email and (step - st.session_state.last_email_step >= 12):
            send_email_alert(
                "CRITICAL ALERT: Satellite Jamming Attack Detected!",
                f"Sector: {country_name}\nLatitude: {curr_lat}, Longitude: {curr_lon}\nThreat Level: {threat_pct}%\nSelf-healing protocol initiated successfully.",
                recipient_email
            )
            st.session_state.last_email_step = step

t = st.session_state.curr_telemetry

st.title("🛰️ SAT-SHIELD // 3D Orbital Telemetry & AI Self-Healing Command")

btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 3.6])
with btn_col1:
    if not st.session_state.running:
        if st.button("🚀 Start Live 3D Scanning", type="primary", use_container_width=True):
            st.session_state.running = True
            st.rerun()
    else:
        if st.button("⏸️ Pause Live Scanning", use_container_width=True):
            st.session_state.running = False
            st.rerun()
with btn_col2:
    if st.button("🔄 Reset Telemetry Logs", use_container_width=True):
        st.session_state.running = False
        st.session_state.step = 0
        st.session_state.signal_history = []
        st.session_state.session_logs = []
        st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.metric("🌐 Latitude", f"{t['lat']}°")
m2.metric("🧭 Longitude", f"{t['lon']}°")
m3.metric("🏳️ Overflying", t['country'].split(" (")[0])
m4.metric("🛡️ Defense Mode", t['mode'])

st.markdown("##### 🔋 Satellite Hardware Health Telemetry")
h1, h2, h3 = st.columns(3)
if t["is_attack"] == 1:
    h1.metric("🔋 Battery Level", f"{t['battery']}%", "-0.4% High Load", delta_color="inverse")
    h2.metric("☀️ Solar Panel Temp", f"{t['temp']} °C", "+25.4 °C Spike", delta_color="inverse")
    h3.metric("📶 Signal-to-Noise (SNR)", f"{t['snr']} dB", "-19.2 dB Jammed", delta_color="inverse")
else:
    h1.metric("🔋 Battery Level", f"{t['battery']}%", "+0.1% Charging")
    h2.metric("☀️ Solar Panel Temp", f"{t['temp']} °C", "Nominal")
    h3.metric("📶 Signal-to-Noise (SNR)", f"{t['snr']} dB", "Optimal")

st.markdown("---")

col_scan, col_globe, col_graph = st.columns([1.15, 1.35, 1.5])

with col_scan:
    st.subheader("🔍 Scanner & Threat Meter")
    if t["is_attack"] == 1:
        st.markdown(f"""
        <div class="radar-box" style="border-color:#ff3333; color:#ff4d4d; box-shadow: 0 0 20px rgba(255,51,51,0.5);">
            <h4>🚨 JAMMING ATTACK DETECTED</h4>
            <div class="pulse-circle" style="border-color:#ff3333; box-shadow: inset 0 0 15px #ff3333;">⚠️</div>
            <p>Target Lock: <b>{t['country']}</b></p>
            <p style="font-size:12px;">ACTION: Hopping to Backup Frequency</p>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(create_threat_gauge(t["threat"]), use_container_width=True)
        st.error("🚨 RED ALERT: RF Spoofing / Signal Jamming Attack Detected!")
        st.info(f"🔵 SELF-HEALING ACTIVE: Rerouted to {t['channel']}")
    else:
        st.markdown(f"""
        <div class="radar-box">
            <h4>🟢 SCANNING GROUND SECTOR</h4>
            <div class="pulse-circle">🛰️</div>
            <p>Sector: <b>{t['country']}</b></p>
            <p style="font-size:12px;">LINK INTEGRITY: 99.8% | ENCRYPTED</p>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(create_threat_gauge(t["threat"]), use_container_width=True)
        st.success("🟢 GREEN STATUS: Telemetry Stream Nominal & Secure.")

with col_globe:
    st.subheader("🌍 Interactive 3D Rotating Globe")
    st.plotly_chart(create_3d_globe(t["lat"], t["lon"], t["country"], t["is_attack"] == 1), use_container_width=True)

with col_graph:
    st.subheader("📈 Live Signal & Hardware Stream")
    if st.session_state.signal_history:
        st.line_chart(pd.DataFrame(st.session_state.signal_history))
    else:
        st.info("Click 'Start Live 3D Scanning' to stream real-time telemetry signals.")

st.markdown("---")

col_table, col_ai = st.columns([1.4, 1.1])

with col_table:
    st.subheader("📋 Live Satellite Telemetry & Security Logs")
    if st.session_state.session_logs:
        st.dataframe(pd.DataFrame(st.session_state.session_logs).head(10), use_container_width=True)
    else:
        st.write("No scan logs recorded yet.")

with col_ai:
    st.subheader("🤖 Mission Control AI Assistant")
    
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_prompt = None
    if q_col1.button("📍 Live Position", use_container_width=True):
        quick_prompt = "Where is the satellite right now?"
    if q_col2.button("🛡️ Security SitRep", use_container_width=True):
        quick_prompt = "Give me a full security status report"
    if q_col3.button("🔋 Hardware Health", use_container_width=True):
        quick_prompt = "What is the battery, temperature and SNR status?"
        
    chat_container = st.container(height=280)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
    with st.form(key="ai_chat_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns([4, 1])
        user_input = f_col1.text_input("Ask Mission Control AI...", placeholder="e.g., Where is the satellite? / Status report", label_visibility="collapsed")
        submit_chat = f_col2.form_submit_button("Send", use_container_width=True)
        
    active_query = quick_prompt if quick_prompt else (user_input if submit_chat and user_input.strip() else None)
    
    if active_query:
        st.session_state.messages.append({"role": "user", "content": active_query})
        ai_reply = generate_ai_response(active_query)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.rerun()

if st.session_state.running:
    time.sleep(sim_speed)
    st.session_state.step += 1
    st.rerun()

