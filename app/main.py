# app/main.py

import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import folium_static
from app.utils.map_utils import crea_mappa_folium, crea_mappa_plotly
from app.utils.chart_utils import grafico_torta_csx, grafico_barre_partiti

# Assicura che la cartella padre sia nel path
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
        m = crea_mappa_folium(municipi, "MUNICIPIO", colore, opacita)
        folium_static(m)
    else:
        fig = crea_mappa_plotly(municipi, "MUNICIPIO", colore, opacita)
        st.plotly_chart(fig, use_container_width=True)

    municipio_scelto = st.selectbox("Seleziona un municipio", sorted(voti["Municipio"].dropna().unique()))
    fig_torta = grafico_torta_csx(voti, "Municipio", municipio_scelto)
    fig_barre = grafico_barre_partiti(voti, "Municipio", municipio_scelto)
    if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
    if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)

elif mappa_tipo == "Sezioni":
    st.subheader("🗺️ Mappa delle Sezioni")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(sezioni, "SEZIONE", colore, opacita)
        folium_static(m)
    else:
        fig = crea_mappa_plotly(sezioni, "SEZIONE", colore, opacita)
        st.plotly_chart(fig, use_container_width=True)

    sezione_scelta = st.selectbox("Seleziona una sezione", sorted(voti["SEZIONE"].dropna().unique()))
    fig_torta = grafico_torta_csx(voti, "SEZIONE", sezione_scelta)
    fig_barre = grafico_barre_partiti(voti, "SEZIONE", sezione_scelta)
    if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
    if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)

elif mappa_tipo == "Unità Urbanistiche":
    st.subheader("🗺️ Mappa delle Unità Urbanistiche")
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(uu, "UNITA_URBANISTICA", colore, opacita)
        folium_static(m)
    else:
        fig = crea_mappa_plotly(uu, "UNITA_URBANISTICA", colore, opacita)
        st.plotly_chart(fig, use_container_width=True)

    uu_scelta = st.selectbox("Seleziona un'unità urbanistica", sorted(voti["UNITA_URBANISTICA"].dropna().unique()))
    fig_torta = grafico_torta_csx(voti, "UNITA_URBANISTICA", uu_scelta)
    fig_barre = grafico_barre_partiti(voti, "UNITA_URBANISTICA", uu_scelta)
    if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
    if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)

st.markdown("---")
st.markdown("Dashboard a cura del Comitato Elettorale Genova 2024")
