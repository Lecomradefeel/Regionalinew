# app/main.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import sys, os

# Aggiungi il percorso corrente al PATH di Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Ora importa direttamente da utils (senza 'app.')
from utils.map_utils import crea_mappa_folium, crea_mappa_plotly
from utils.chart_utils import grafico_torta_csx, grafico_barre_partiti

from streamlit_folium import folium_static

# Configurazione pagina
st.set_page_config(layout="wide", page_title="Dashboard Elezioni Regionali 2024", page_icon="🗳️")

st.title("🗳️ Dashboard Elezioni Regionali 2024 - Genova")

# Caricamento dati
@st.cache_data
def carica_dati():
    municipi = gpd.read_file("data/municipi.geojson")
    sezioni = gpd.read_file("data/sezioni.geojson")
    uu = gpd.read_file("data/unita_urbanistiche.geojson")
    voti = pd.read_excel("data/voti_rielaborati.xlsx")
    return municipi, sezioni, uu, voti

municipi, sezioni, uu, voti = carica_dati()

# Aggiungi questa funzione dopo carica_dati()
def check_columns():
    """Verifica e correggi i nomi delle colonne nei dataframes"""
    # Stampa nomi delle colonne per debug
    st.sidebar.markdown("### 📊 Colonne nei dati")
    if st.sidebar.checkbox("Mostra nomi colonne"):
        st.sidebar.write("Colonne in municipi:", municipi.columns.tolist())
        st.sidebar.write("Colonne in sezioni:", sezioni.columns.tolist())
        st.sidebar.write("Colonne in uu:", uu.columns.tolist())
        st.sidebar.write("Colonne in voti:", voti.columns.tolist())
    
    # Restituisci i nomi corretti delle colonne
    municipio_col = None
    sezione_col = None
    uu_col = None
    
    # Cerca il nome corretto per la colonna del municipio
    possibili_nomi_municipio = ['MUNICIPIO', 'Municipio', 'municipio', 'NOME_MUNICIPIO', 'Nome_Municipio']
    for nome in possibili_nomi_municipio:
        if nome in municipi.columns:
            municipio_col = nome
            break
    
    # Cerca il nome corretto per la colonna della sezione
    possibili_nomi_sezione = ['SEZIONE', 'Sezione', 'sezione', 'SEZ', 'NUM_SEZIONE']
    for nome in possibili_nomi_sezione:
        if nome in sezioni.columns:
            sezione_col = nome
            break
    
    # Cerca il nome corretto per la colonna dell'unità urbanistica
    possibili_nomi_uu = ['UNITA_URBANISTICA', 'Unita_Urbanistica', 'unita_urbanistica', 'NOME_UU']
    for nome in possibili_nomi_uu:
        if nome in uu.columns:
            uu_col = nome
            break
    
    return municipio_col, sezione_col, uu_col

# Carica i dati
municipi, sezioni, uu, voti = carica_dati()

# Ottieni i nomi corretti delle colonne
municipio_col, sezione_col, uu_col = check_columns()

# Debug delle colonne trovate
st.sidebar.markdown("### 🔍 Colonne trovate")
st.sidebar.write(f"Colonna municipio: {municipio_col}")
st.sidebar.write(f"Colonna sezione: {sezione_col}")
st.sidebar.write(f"Colonna unità urbanistica: {uu_col}")

# Verifica che le colonne siano state trovate
if not municipio_col or not sezione_col or not uu_col:
    st.error("Non sono state trovate tutte le colonne necessarie nei dati. Verifica i nomi delle colonne nei file GeoJSON.")
    if not municipio_col:
        st.error(f"Colonna municipio non trovata. Colonne disponibili: {municipi.columns.tolist()}")
    if not sezione_col:
        st.error(f"Colonna sezione non trovata. Colonne disponibili: {sezioni.columns.tolist()}")
    if not uu_col:
        st.error(f"Colonna unità urbanistica non trovata. Colonne disponibili: {uu.columns.tolist()}")
    st.stop()

# Sidebar
st.sidebar.title("🧭 Filtri")
mappa_tipo = st.sidebar.selectbox("Scegli la mappa:", ["Municipi", "Sezioni", "Unità Urbanistiche"])
tipo_visualizzazione = st.sidebar.radio("Visualizzazione:", ["Folium", "Plotly"])
colore = st.sidebar.color_picker("Colore poligoni", "#2563eb")
opacita = st.sidebar.slider("Opacità", 0.0, 1.0, 0.6)

# Mappa + grafici
if mappa_tipo == "Municipi":
    st.subheader("🗺️ Mappa dei Municipi")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(municipi, municipio_col, colore, opacita)  # Usa la colonna corretta
        folium_static(m)
    else:
        fig = crea_mappa_plotly(municipi, municipio_col, colore, opacita)  # Usa la colonna corretta
        st.plotly_chart(fig, use_container_width=True)

    municipio_scelto = st.selectbox("Seleziona un municipio", sorted(voti["Municipio"].dropna().unique()))
    fig_torta = grafico_torta_csx(voti, "Municipio", municipio_scelto)
    fig_barre = grafico_barre_partiti(voti, "Municipio", municipio_scelto)
    if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
    if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)

elif mappa_tipo == "Sezioni":
    st.subheader("🗺️ Mappa delle Sezioni")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(sezioni, sezione_col, colore, opacita)  # Usa la colonna corretta
        folium_static(m)
    else:
        fig = crea_mappa_plotly(sezioni, sezione_col, colore, opacita)  # Usa la colonna corretta
        st.plotly_chart(fig, use_container_width=True)

    sezione_scelta = st.selectbox("Seleziona una sezione", sorted(voti["SEZIONE"].dropna().unique()))
    fig_torta = grafico_torta_csx(voti, "SEZIONE", sezione_scelta)
    fig_barre = grafico_barre_partiti(voti, "SEZIONE", sezione_scelta)
    if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
    if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)

elif mappa_tipo == "Unità Urbanistiche":
    st.subheader("🗺️ Mappa delle Unità Urbanistiche")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(uu, uu_col, colore, opacita)  # Usa la colonna corretta
        folium_static(m)
    else:
        fig = crea_mappa_plotly(uu, uu_col, colore, opacita)  # Usa la colonna corretta
        st.plotly_chart(fig, use_container_width=True)

    uu_scelta = st.selectbox("Seleziona un'unità urbanistica", sorted(voti["UNITA_URBANISTICA"].dropna().unique()))
    fig_torta = grafico_torta_csx(voti, "UNITA_URBANISTICA", uu_scelta)
    fig_barre = grafico_barre_partiti(voti, "UNITA_URBANISTICA", uu_scelta)
    if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
    if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)
