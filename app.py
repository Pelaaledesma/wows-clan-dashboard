import streamlit as st
import pandas as pd
import json
import gzip
import os
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="World of Warships - Clan Dashboard", layout="wide")
st.title("🚢 Dashboard de Estadísticas del Clan - World of Warships")

SESSION_FILE = "session_data.json"

def guardar_sesion(data):
    try:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception as e:
        st.warning(f"Error al guardar la sesión: {e}")

def cargar_sesion():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Error al cargar la sesión previa: {e}")
    return []

# --- Función para leer un archivo .wowsreplay y extraer datos básicos ---
def parse_replay(file):
    try:
        # Verificar si es gzip
        start = file.read(2)
        file.seek(0)
        is_gzip = start == b'\x1f\x8b'

        if is_gzip:
            with gzip.open(file, 'rb') as f:
                data = f.read()
        else:
            data = file.read()

        json_start = data.find(b'{')
        if isinstance(json_start, int):
            json_data = data[json_start:].decode('utf-8', errors='ignore')
        else:
            raise ValueError("No se encontró el inicio de un objeto JSON")

        # Buscar el primer objeto JSON válido
        decoder = json.JSONDecoder()
        replay, _ = decoder.raw_decode(json_data)

        players = replay.get('players', [])
        match_time = replay.get('dateTime', None)
        try:
            match_time = int(match_time)
        except (TypeError, ValueError):
            match_time = None

        battle_time = datetime.fromtimestamp(match_time) if match_time else None
        map_name = replay.get('mapDisplayName', 'Desconocido')

        results = []
        for p in players:
            results.append({
                'Jugador': p.get('name', 'Desconocido'),
                'Barco': p.get('shipName', 'Desconocido'),
                'Tipo de Barco': p.get('shipType', 'Desconocido'),
                'Daño': p.get('damageDealt', 0),
                'XP': p.get('xp', 0),
                'Kills': p.get('frags', 0),
                'Incendios': p.get('fires', 0),
                'Inundaciones': p.get('floodings', 0),
                'Spotting': p.get('spottedShips', 0),
                'Asistencias': p.get('damageAssisted', 0),
                'Capturas': p.get('capturePoints', 0),
                'Daño Recibido': p.get('damageReceived', 0),
                'Fecha': battle_time.isoformat() if battle_time else None,
                'Mapa': map_name
            })
        return results
    except Exception as e:
        st.error(f"Error al procesar replay: {e}")
        return []

# --- Cargar datos guardados previamente ---
session_data = cargar_sesion()
all_data = session_data.copy()

# --- Subida de archivos ---
uploaded_files = st.file_uploader("Sube uno o varios archivos .wowsreplay:", type=["wowsreplay"], accept_multiple_files=True)

# --- Miembros del clan ---
st.sidebar.header("🎖️ Miembros del Clan")
clan_input = st.sidebar.text_area("Nombres de los miembros (uno por línea):", "Miembro1\nMiembro2")
clan_miembros = [x.strip() for x in clan_input.splitlines() if x.strip()]

if uploaded_files:
    nuevos_datos = []
    for file in uploaded_files:
        with st.spinner(f"Procesando {file.name}..."):
            file_data = BytesIO(file.read())
            parsed = parse_replay(file_data)
            nuevos_datos.extend(parsed)

    if nuevos_datos:
        all_data.extend(nuevos_datos)
        guardar_sesion(all_data)

if all_data:
    df = pd.DataFrame(all_data)
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    # Identificar miembros del clan
    df["Es del Clan"] = df["Jugador"].isin(clan_miembros)
    df_clan = df[df["Es del Clan"] == True]

    # Filtros dinámicos
    st.sidebar.header("🔍 Filtros")
    jugador_sel = st.sidebar.multiselect("Filtrar por jugador:", options=df_clan["Jugador"].unique())
    barco_sel = st.sidebar.multiselect("Filtrar por tipo de barco:", options=df_clan["Tipo de Barco"].unique())
    mapa_sel = st.sidebar.multiselect("Filtrar por mapa:", options=df_clan["Mapa"].unique())

    if jugador_sel:
        df_clan = df_clan[df_clan["Jugador"].isin(jugador_sel)]
    if barco_sel:
        df_clan = df_clan[df_clan["Tipo de Barco"].isin(barco_sel)]
    if mapa_sel:
        df_clan = df_clan[df_clan["Mapa"].isin(mapa_sel)]

    st.subheader("📊 Estadísticas del Clan")
    st.dataframe(df_clan)

    resumen = df_clan.groupby("Jugador").agg({
        "Daño": "sum",
        "XP": "sum",
        "Kills": "sum",
        "Incendios": "sum",
        "Inundaciones": "sum",
        "Spotting": "sum",
        "Asistencias": "sum",
        "Capturas": "sum",
        "Daño Recibido": "sum",
        "Barco": "count"
    }).rename(columns={"Barco": "Batallas"}).reset_index()

    st.subheader("🏅 Ranking de jugadores por daño total")
    st.bar_chart(resumen.set_index("Jugador")["Daño"])

    st.subheader("📄 Tabla resumida")
    st.dataframe(resumen)

    # Exportar
    st.subheader("⬇️ Exportar datos")
    csv = df_clan.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV", data=csv, file_name="estadisticas_clan.csv", mime="text/csv")

    excel = BytesIO()
    with pd.ExcelWriter(excel, engine='xlsxwriter') as writer:
        df_clan.to_excel(writer, sheet_name='Datos', index=False)
        resumen.to_excel(writer, sheet_name='Resumen', index=False)
    st.download_button("Descargar Excel", data=excel.getvalue(), file_name="estadisticas_clan.xlsx")

else:
    st.info("Por favor, sube archivos .wowsreplay para comenzar o carga sesiones guardadas.")