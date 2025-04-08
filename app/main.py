# app/main.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import sys, os

# Assicura che le directory necessarie siano nel path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(current_dir)
sys.path.append(parent_dir)

# Importa le funzioni di utilità
try:
    from utils.map_utils import crea_mappa_folium, crea_mappa_plotly
    from utils.chart_utils import grafico_torta_csx, grafico_barre_partiti
    from streamlit_folium import folium_static
except ImportError:
    try:
        from app.utils.map_utils import crea_mappa_folium, crea_mappa_plotly
        from app.utils.chart_utils import grafico_torta_csx, grafico_barre_partiti
        from streamlit_folium import folium_static
    except ImportError:
        st.error("Impossibile importare i moduli utils. Verifica la struttura del progetto.")
        st.stop()

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

# Funzione per trovare le colonne dei partiti
def trova_colonne_partiti(df):
    partiti_cols = []
    for col in df.columns:
        if "%" in col and any(partito in col for partito in ["PD", "M5S", "AVS", "Orlando", "Bucci", "Lega", "FI", "FdI"]):
            partiti_cols.append(col)
    return partiti_cols

# Trova le colonne dei partiti
partiti_cols = trova_colonne_partiti(voti)

# Sidebar
st.sidebar.title("🧭 Filtri")
mappa_tipo = st.sidebar.selectbox("Scegli la mappa:", ["Municipi", "Sezioni Elettorali", "Unità Urbanistiche"])
tipo_visualizzazione = st.sidebar.radio("Visualizzazione:", ["Folium", "Plotly"])
colore = st.sidebar.color_picker("Colore poligoni", "#2563eb")
opacita = st.sidebar.slider("Opacità", 0.0, 1.0, 0.6)

# Mappa + grafici
if mappa_tipo == "Municipi":
    st.subheader("🗺️ Mappa dei Municipi")
    
    # Verifica la colonna corretta nel DataFrame voti
    municipio_voti_col = "Municipio"  # Colonna predefinita
    if municipio_voti_col not in voti.columns:
        for col in voti.columns:
            if "MUNI" in col.upper() or "municipio" in col.lower():
                municipio_voti_col = col
                break
    
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(
            municipi, 
            municipio_col, 
            colore, 
            opacita, 
            df_voti=voti, 
            join_col=municipio_voti_col,
            partiti_cols=partiti_cols
        )
        folium_static(m)
    else:
        fig = crea_mappa_plotly(
            municipi, 
            municipio_col, 
            colore, 
            opacita, 
            df_voti=voti, 
            join_col=municipio_voti_col,
            partiti_cols=partiti_cols
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Aggiungi legenda per la colorazione della mappa
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin: 20px 0;">
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: blue; margin-right: 5px;"></div>
            <span>CDX avanti</span>
        </div>
        <div style="margin: 0 15px; border-top: 1px solid #ccc; width: 50px;"></div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: white; border: 1px solid #ccc; margin-right: 5px;"></div>
            <span>Parità</span>
        </div>
        <div style="margin: 0 15px; border-top: 1px solid #ccc; width: 50px;"></div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: red; margin-right: 5px;"></div>
            <span>CSX avanti</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if municipio_voti_col in voti.columns:
        # Conversione da numeri a nomi letterali per i municipi
        municipi_map = {
            "1": "Centro Est",
            "2": "Centro Ovest",
            "3": "Bassa Val Bisagno",
            "4": "Media Val Bisagno",
            "5": "Valpolcevera",
            "6": "Medio Ponente",
            "7": "Ponente",
            "8": "Medio Levante",
            "9": "Levante"
        }
        
        # Ottieni valori unici e trasforma i numeri in nomi se possibile
        municipi_valori = sorted(voti[municipio_voti_col].dropna().unique())
        municipi_display = []
        
        for val in municipi_valori:
            # Prova a vedere se è un numero o una stringa che può essere convertita in numero
            try:
                # Se è già un nome letterale, usalo così com'è
                if str(val) in municipi_map.values():
                    municipi_display.append(str(val))
                # Altrimenti controlla se è una chiave nella mappa
                elif str(val) in municipi_map:
                    municipi_display.append(f"{val} - {municipi_map[str(val)]}")
                else:
                    municipi_display.append(str(val))
            except:
                municipi_display.append(str(val))
        
        municipio_scelto_display = st.selectbox("Seleziona un municipio", municipi_display)
        
        # Estrai il valore numerico se presente
        if " - " in municipio_scelto_display:
            municipio_scelto = municipio_scelto_display.split(" - ")[0]
        else:
            municipio_scelto = municipio_scelto_display
        
        fig_torta = grafico_torta_csx(voti, municipio_voti_col, municipio_scelto)
        fig_barre = grafico_barre_partiti(voti, municipio_voti_col, municipio_scelto)
        if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
        if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)
    else:
        st.error(f"Colonna 'Municipio' non trovata nel file voti. Colonne disponibili: {voti.columns.tolist()}")

elif mappa_tipo == "Sezioni Elettorali":
    st.subheader("🗺️ Mappa delle Sezioni Elettorali")
    
    # Verifica la colonna corretta nel DataFrame voti
    sezione_voti_col = "SEZIONE"  # Colonna predefinita
    if sezione_voti_col not in voti.columns:
        for col in voti.columns:
            if "SEZ" in col.upper() or "sezione" in col.lower():
                sezione_voti_col = col
                break
    
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(
            sezioni, 
            sezione_col, 
            colore, 
            opacita, 
            df_voti=voti, 
            join_col=sezione_voti_col,
            partiti_cols=partiti_cols
        )
        folium_static(m)
    else:
        fig = crea_mappa_plotly(
            sezioni, 
            sezione_col, 
            colore, 
            opacita, 
            df_voti=voti, 
            join_col=sezione_voti_col,
            partiti_cols=partiti_cols
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Aggiungi legenda per la colorazione della mappa
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin: 20px 0;">
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: blue; margin-right: 5px;"></div>
            <span>CDX avanti</span>
        </div>
        <div style="margin: 0 15px; border-top: 1px solid #ccc; width: 50px;"></div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: white; border: 1px solid #ccc; margin-right: 5px;"></div>
            <span>Parità</span>
        </div>
        <div style="margin: 0 15px; border-top: 1px solid #ccc; width: 50px;"></div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: red; margin-right: 5px;"></div>
            <span>CSX avanti</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if sezione_voti_col in voti.columns:
        sezione_scelta = st.selectbox("Seleziona una sezione elettorale", sorted(voti[sezione_voti_col].dropna().unique()))
        fig_torta = grafico_torta_csx(voti, sezione_voti_col, sezione_scelta)
        fig_barre = grafico_barre_partiti(voti, sezione_voti_col, sezione_scelta)
        if fig_torta: st.plotly_chart(fig_torta, use_container_width=True)
        if fig_barre: st.plotly_chart(fig_barre, use_container_width=True)
    else:
        st.error(f"Colonna 'SEZIONE' non trovata nel file voti. Colonne disponibili: {voti.columns.tolist()}")

elif mappa_tipo == "Unità Urbanistiche":
    st.subheader("🗺️ Mappa delle Unità Urbanistiche")
    
    # Verifica la colonna corretta nel DataFrame voti
    uu_voti_col = "UNITA_URBANISTICA"  # Colonna predefinita
    if uu_voti_col not in voti.columns:
        for col in voti.columns:
            if "UNIT" in col.upper() or "UU" in col.upper() or "urbanistica" in col.lower():
                uu_voti_col = col
                break
    
    if tipo_visualizzazione == "Folium":
        m = crea_mappa_folium(
            uu, 
            uu_col, 
            colore, 
            opacita, 
            df_voti=voti, 
            join_col=uu_voti_col,
            partiti_cols=partiti_cols
        )
        folium_static(m)
    else:
        fig = crea_mappa_plotly(
            uu, 
            uu_col, 
            colore, 
            opacita, 
            df_voti=voti, 
            join_col=uu_voti_col,
            partiti_cols=partiti_cols
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Aggiungi legenda per la colorazione della mappa
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin: 20px 0;">
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: blue; margin-right: 5px;"></div>
            <span>CDX avanti</span>
        </div>
        <div style="margin: 0 15px; border-top: 1px solid #ccc; width: 50px;"></div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: white; border: 1px solid #ccc; margin-right: 5px;"></div>
            <span>Parità</span>
        </div>
        <div style="margin: 0 15px; border-top: 1px solid #ccc; width: 50px;"></div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: red; margin-right: 5px;"></div>
            <span>CSX avanti</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
