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
    try:
        # Ottieni il percorso assoluto della directory corrente
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Vai alla directory principale del progetto
        project_dir = os.path.abspath(os.path.join(current_dir, ".."))
        # Percorso alla directory data
        data_dir = os.path.join(project_dir, "data")
        
        # Debug info nella sidebar
        st.sidebar.markdown("### 📁 Percorsi")
        if st.sidebar.checkbox("Mostra percorsi file"):
            st.sidebar.write("Directory corrente:", current_dir)
            st.sidebar.write("Directory progetto:", project_dir)
            st.sidebar.write("Directory dati:", data_dir)
            st.sidebar.write("File Excel:", os.path.join(data_dir, "voti_rielaborati.xlsx"))
            st.sidebar.write("File esiste:", os.path.exists(os.path.join(data_dir, "voti_rielaborati.xlsx")))
        
        # Carica i file con percorsi assoluti
        municipi = gpd.read_file(os.path.join(data_dir, "municipi.geojson"))
        sezioni = gpd.read_file(os.path.join(data_dir, "sezioni.geojson"))
        uu = gpd.read_file(os.path.join(data_dir, "unita_urbanistiche.geojson"))
        voti = pd.read_excel(os.path.join(data_dir, "voti_rielaborati.xlsx"))
        
        return municipi, sezioni, uu, voti
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati: {str(e)}")
        if "No such file or directory" in str(e):
            st.error("File non trovato. Verifica che i file dati siano nella directory 'data'.")
        st.stop()

# Carica i dati
municipi, sezioni, uu, voti = carica_dati()

# Determina automaticamente quali colonne usare
def determine_columns():
    # Per i municipi
    municipio_col = None
    for col in ["MUNICIPIO", "Municipio", "municipio", "NOME_MUNIC", "NOME_MUNICIPIO"]:
        if col in municipi.columns:
            municipio_col = col
            break
    if not municipio_col:
        # Se non troviamo una colonna con nome specifico, cerchiamo una colonna che contiene "MUNI" o "NOME"
        for col in municipi.columns:
            if "MUNI" in col.upper() or "NOME" in col.upper():
                municipio_col = col
                break
        if not municipio_col:
            # Usa la prima colonna che non è 'geometry' o '_umap_options'
            for col in municipi.columns:
                if col not in ['geometry', '_umap_options']:
                    municipio_col = col
                    break

    # Per le sezioni
    sezione_col = None
    for col in ["SEZIONE", "Sezione", "sezione", "SEZ", "NUM_SEZIONE"]:
        if col in sezioni.columns:
            sezione_col = col
            break
    if not sezione_col:
        for col in sezioni.columns:
            if "SEZ" in col.upper() or "NUM" in col.upper():
                sezione_col = col
                break
        if not sezione_col:
            for col in sezioni.columns:
                if col not in ['geometry', '_umap_options']:
                    sezione_col = col
                    break

    # Per le unità urbanistiche
    uu_col = None
    for col in ["UNITA_URBANISTICA", "Unita_Urbanistica", "NOME_UU"]:
        if col in uu.columns:
            uu_col = col
            break
    if not uu_col:
        for col in uu.columns:
            if "UNIT" in col.upper() or "NOME" in col.upper() or "UU" in col.upper():
                uu_col = col
                break
        if not uu_col:
            for col in uu.columns:
                if col not in ['geometry', '_umap_options']:
                    uu_col = col
                    break
    
    return municipio_col, sezione_col, uu_col

# Ottieni i nomi delle colonne
municipio_col, sezione_col, uu_col = determine_columns()

# Debug delle colonne trovate
st.sidebar.markdown("### 🔍 Colonne trovate")
st.sidebar.write(f"Colonna municipio: {municipio_col}")
st.sidebar.write(f"Colonna sezione: {sezione_col}")
st.sidebar.write(f"Colonna unità urbanistica: {uu_col}")

# Mostra informazioni sulle colonne disponibili
st.sidebar.markdown("### 📊 Colonne nei dati")
if st.sidebar.checkbox("Mostra nomi colonne"):
    st.sidebar.write("Colonne in municipi:", municipi.columns.tolist())
    st.sidebar.write("Colonne in sezioni:", sezioni.columns.tolist())
    st.sidebar.write("Colonne in uu:", uu.columns.tolist())
    st.sidebar.write("Colonne in voti:", voti.columns.tolist())

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
        m = crea_mappa_folium(municipi, municipio_col, colore, opacita)
        folium_static(m)
    else:
        fig = crea_mappa_plotly(municipi, municipio_col, colore, opacita)
        st.plotly_chart(fig, use_container_width=True)

    # Verifica la colonna corretta nel DataFrame voti
    municipio_voti_col = "Municipio"  # Colonna predefinita
    if municipio_voti_col not in voti.columns:
        for col in voti.columns:
            if "MUNI" in col.upper() or "municipio" in col.lower():
                municipio_voti_col = col
                break
    
    if municipio_voti_col in voti.columns:
        municipio_scelto = st.selectbox("Seleziona un municipio", sorted(voti[municipio_voti_col].dropna().unique()))
        fig_torta = grafico_torta_csx(voti, municipio_voti_col, municipio_scelto)
        fig_barre = grafico_barre_partiti(voti, municipio_voti_col, municipio_scelto)
        if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
        if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)
    else:
        st.error(f"Colonna 'Municipio' non trovata nel file voti. Colonne disponibili: {voti.columns.tolist()}")

elif mappa_tipo == "Sezioni":
    st.subheader("🗺️ Mappa delle Sezioni")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(sezioni, sezione_col, colore, opacita)
        folium_static(m)
    else:
        fig = crea_mappa_plotly(sezioni, sezione_col, colore, opacita)
        st.plotly_chart(fig, use_container_width=True)

    # Verifica la colonna corretta nel DataFrame voti
    sezione_voti_col = "SEZIONE"  # Colonna predefinita
    if sezione_voti_col not in voti.columns:
        for col in voti.columns:
            if "SEZ" in col.upper() or "sezione" in col.lower():
                sezione_voti_col = col
                break
    
    if sezione_voti_col in voti.columns:
        sezione_scelta = st.selectbox("Seleziona una sezione", sorted(voti[sezione_voti_col].dropna().unique()))
        fig_torta = grafico_torta_csx(voti, sezione_voti_col, sezione_scelta)
        fig_barre = grafico_barre_partiti(voti, sezione_voti_col, sezione_scelta)
        if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
        if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)
    else:
        st.error(f"Colonna 'SEZIONE' non trovata nel file voti. Colonne disponibili: {voti.columns.tolist()}")

elif mappa_tipo == "Unità Urbanistiche":
    st.subheader("🗺️ Mappa delle Unità Urbanistiche")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(uu, uu_col, colore, opacita)
        folium_static(m)
    else:
        fig = crea_mappa_plotly(uu, uu_col, colore, opacita)
        st.plotly_chart(fig, use_container_width=True)

    # Verifica la colonna corretta nel DataFrame voti
    uu_voti_col = "UNITA_URBANISTICA"  # Colonna predefinita
    if uu_voti_col not in voti.columns:
        for col in voti.columns:
            if "UNIT" in col.upper() or "UU" in col.upper() or "urbanistica" in col.lower():
                uu_voti_col = col
                break
    
    if uu_voti_col in voti.columns:
        uu_scelta = st.selectbox("Seleziona un'unità urbanistica", sorted(voti[uu_voti_col].dropna().unique()))
        fig_torta = grafico_torta_csx(voti, uu_voti_col, uu_scelta)
        fig_barre = grafico_barre_partiti(voti, uu_voti_col, uu_scelta)
        if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
        if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)
    else:
        st.error(f"Colonna 'UNITA_URBANISTICA' non trovata nel file voti. Colonne disponibili: {voti.columns.tolist()}")

st.markdown("---")
st.markdown("Dashboard per AVS Genova 2025")
