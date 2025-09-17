# app.py
import streamlit as st
from gtts import gTTS
import speech_recognition as sr
import sqlite3
import os
import io
import time
import folium
from streamlit_folium import st_folium
from database import init_db, add_sos_event, list_sos_events, update_user_status

DB_PATH = "wristbridge.db"
init_db(DB_PATH)

st.set_page_config(page_title="WristBridge Prototype", layout="wide")

# --- Sidebar navigation ---
st.sidebar.title("WristBridge")
page = st.sidebar.radio("Go to", ["User Interface", "Caregiver Dashboard", "Smartwatch Simulator", "About"])

# --- Common helpers ---
def save_tts(text, filename="tts_output.mp3", lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename

def transcribe_wav(file_bytes):
    r = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(file_bytes)) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "[Could not understand audio]"
    except sr.RequestError as e:
        return f"[STT request error: {e}]"

# --- Page: User Interface (Care recipient / demo) ---
if page == "User Interface":
    st.title("WristBridge — User Interface (Prototype)")
    st.markdown("Simulated Tapface: choose mode quickly using large buttons.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Tapface (Mode Selection)")
        mode = st.radio("Select mode:", ["Speech-to-Text", "Text-to-Speech", "Visual Alert", "SOS"], index=0)

        st.markdown("---")
        if mode == "Speech-to-Text":
            st.write("Upload a WAV file (record on your phone/PC and upload) to transcribe.")
            uploaded = st.file_uploader("Upload WAV file", type=["wav"], key="stt_uploader")
            if uploaded is not None:
                bytes_data = uploaded.read()
                with st.spinner("Transcribing..."):
                    text = transcribe_wav(bytes_data)
                    st.success("Transcription:")
                    st.text_area("Transcribed text", value=text, height=150)
                    # Also store last status
                    update_user_status(DB_PATH, "last_message", text)
        elif mode == "Text-to-Speech":
            st.write("Type text and play or download the speech audio.")
            txt = st.text_area("Enter text", value="Hello! This is WristBridge speaking.")
            tts_lang = st.selectbox("TTS language", ["en", "hi", "es", "fr"], index=0)
            if st.button("Generate & Play"):
                fn = save_tts(txt, filename="output_tts.mp3", lang=tts_lang)
                audio_file = open(fn, "rb")
                st.audio(audio_file.read(), format="audio/mp3")
                audio_file.close()
                update_user_status(DB_PATH, "last_tts", txt)
            if st.button("Download TTS"):
                fn = save_tts(txt, filename="output_tts.mp3", lang=tts_lang)
                with open(fn, "rb") as f:
                    st.download_button("Download MP3", f, file_name="wristbridge_tts.mp3", mime="audio/mp3")
        elif mode == "Visual Alert":
            st.write("Trigger a visual alert (on-watch visual notification simulated here).")
            message = st.text_input("Alert message", value="Please pay attention.")
            if st.button("Show Visual Alert"):
                st.warning(f"🔔 VISUAL ALERT: {message}")
                update_user_status(DB_PATH, "last_alert", message)
        elif mode == "SOS":
            st.write("Send an emergency SOS. Provide (or simulate) location.")
            lat = st.number_input("Latitude", value=28.6139, format="%.6f")
            lon = st.number_input("Longitude", value=77.2090, format="%.6f")
            note = st.text_input("Short note (optional)", value="Need help")
            if st.button("Send SOS"):
                ts = int(time.time())
                add_sos_event(DB_PATH, ts, lat, lon, note)
                st.error("🚨 SOS sent! Caregiver notified (simulated).")
                update_user_status(DB_PATH, "last_sos", f"{ts}:{lat},{lon}:{note}")

    with col2:
        st.subheader("Status & Location")
        st.info("This panel simulates the smartwatch display & current state.")
        # Show last statuses stored in DB
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT key, value, updated_at FROM user_status")
        rows = cur.fetchall()
        conn.close()
        if rows:
            for k, v, updated_at in rows:
                st.write(f"**{k}** — {v}  (updated {updated_at})")
        else:
            st.write("No status yet.")

        st.markdown("---")
        st.subheader("Map (Simulated GPS)")
        m = folium.Map(location=[28.6139, 77.2090], zoom_start=6)
        # show last SOS pins
        sos_list = list_sos_events(DB_PATH, limit=10)
        for event in sos_list:
            _, ts, lat, lon, note = event
            popup = f"SOS at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}<br/>{note}"
            folium.Marker([lat, lon], popup=popup, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
        st_folium(m, width=700, height=400)

# --- Page: Caregiver Dashboard ---
elif page == "Caregiver Dashboard":
    st.title("WristBridge — Caregiver Dashboard")
    st.markdown("Monitor SOS events, get last messages, and acknowledge events.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Recent SOS Events")
        sos_list = list_sos_events(DB_PATH, limit=50)
        if sos_list:
            for row in sos_list[::-1]:
                id_, ts, lat, lon, note = row
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
                with st.expander(f"SOS #{id_} — {time_str}"):
                    st.write(f"Location: {lat}, {lon}")
                    st.write("Note:", note)
                    if st.button(f"Mark resolved #{id_}", key=f"resolve_{id_}"):
                        # simplistic removal
                        conn = sqlite3.connect(DB_PATH)
                        cur = conn.cursor()
                        cur.execute("DELETE FROM sos WHERE id = ?", (id_,))
                        conn.commit()
                        conn.close()
                        st.success("Marked resolved.")
                        st.experimental_rerun()
        else:
            st.info("No SOS events.")

    with col2:
        st.subheader("Quick Map View")
        m = folium.Map(location=[28.6139, 77.2090], zoom_start=5)
        for event in sos_list:
            _, ts, lat, lon, note = event
            popup = f"SOS at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}<br/>{note}"
            folium.Marker([lat, lon], popup=popup).add_to(m)
        st_folium(m, width=400, height=400)

    st.markdown("---")
    st.subheader("Manual Actions")
    if st.button("Simulate SOS (Test)"):
        ts = int(time.time())
        add_sos_event(DB_PATH, ts, 12.9716, 77.5946, "Simulated test from caregiver")
        st.success("Simulated SOS created.")

# --- Page: Smartwatch Simulator ---
elif page == "Smartwatch Simulator":
    st.title("Smartwatch Simulator")
    st.markdown("A quick simulated wearable UI that would live on the watch. This is just a prototype.")

    st.markdown("## Watch Face")
    st.write("Tap icons to switch modes (simulated).")

    cols = st.columns(4)
    if cols[0].button("STT"):
        st.info("Mode: Speech-to-Text (on-watch). Upload WAV in the User Interface to transcribe.")
    if cols[1].button("TTS"):
        st.info("Mode: Text-to-Speech. Use the User Interface to send TTS.")
    if cols[2].button("Alert"):
        st.warning("Visual Alert (simulated).")
    if cols[3].button("SOS"):
        lat = 28.7041
        lon = 77.1025
        add_sos_event(DB_PATH, int(time.time()), lat, lon, "SOS from watch-sim")
        st.error("SOS sent from watch simulator!")

    st.markdown("---")
    st.subheader("Recent Watch Notifications")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, key, value, updated_at FROM log ORDER BY id DESC LIMIT 10")
    logs = cur.fetchall()
    conn.close()
    if logs:
        for l in logs:
            st.write(f"{l[1]} — {l[2]} (at {l[3]})")
    else:
        st.write("No log entries.")

# --- Page: About ---
else:
    st.title("About WristBridge Prototype")
    st.markdown("""
    **WristBridge** — Prototype web app (Streamlit) for a dual-smartwatch assistive system.

    This repository contains a simulation of core functions:
    - Tapface-like quick mode switching
    - Text-to-Speech (gTTS)
    - Speech-to-Text (upload WAV -> Google STT)
    - SOS and GPS simulation (Folium map)
    - Simple caregiver dashboard using SQLite

    **Notes & limitations**
    - STT works best with WAV files. MP3 uploads may fail unless converted to WAV.
    - This prototype simulates the smartwatch; integrating real Wear OS watches requires companion apps/APIs.
    - For real deployments use secure cloud DB (e.g., Firebase), authentication, HTTPS endpoints, and proper user consent for location sharing.
    """)
