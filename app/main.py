# app/main.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

# Configurazione pagina
st.set_page_config(layout="wide", page_title="Dashboard Elezioni Regionali 2024", page_icon="🗳️")

st.title("🗳️ Dashboard Elezioni Regionali 2024 - Genova")

# Funzioni di utilità incorporate direttamente
def formatta_percentuale(valore):
    """Formatta un valore numerico come percentuale con 1 decimale"""
    if pd.isna(valore):
        return "N/A"
    return f"{valore:.1f}%"

def crea_mappa_plotly(gdf, colonna_id, colore, opacita, df_voti=None, join_col=None, partiti_cols=None):
    """
    Crea una mappa Plotly con i dati GeoJSON e informazioni sui voti.
    """
    try:
        # Converti a WGS84 se necessario
        if gdf.crs and str(gdf.crs) != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        
        # Unisci i dati di voto se disponibili
        if df_voti is not None and join_col is not None:
            # Crea una copia per evitare di modificare l'originale
            gdf_copy = gdf.copy()
            
            # Preparazione dei dati per il join
            if join_col not in df_voti.columns:
                print(f"Colonna di join '{join_col}' non trovata in df_voti")
                gdf_copy['id'] = range(len(gdf_copy))
                hover_data = {colonna_id: True}
                color_col = None
            else:
                # Converte la colonna di join in string per entrambi i dataframe
                gdf_copy[colonna_id] = gdf_copy[colonna_id].astype(str)
                df_voti[join_col] = df_voti[join_col].astype(str)
                
                try:
                    # Assicurati che tutte le colonne percentuali siano numeriche
                    numeric_df = df_voti.copy()
                    for col in numeric_df.columns:
                        if "%" in col:
                            numeric_df[col] = pd.to_numeric(numeric_df[col], errors='coerce')
                    
                    # Calcola percentuali CSX e CDX se non presenti
                    if 'CSX %' not in numeric_df.columns and partiti_cols:
                        csx_cols = [col for col in partiti_cols if any(p in col for p in ["PD", "M5S", "AVS", "Orlando"])]
                        numeric_df['CSX %'] = numeric_df[csx_cols].sum(axis=1)
                    
                    if 'CDX %' not in numeric_df.columns and partiti_cols:
                        cdx_cols = [col for col in partiti_cols if any(p in col for p in ["Bucci", "Lega", "FI", "FdI"])]
                        numeric_df['CDX %'] = numeric_df[cdx_cols].sum(axis=1)
                    
                    # Raggruppa i dati per la colonna di join - solo colonne numeriche
                    numeric_cols = numeric_df.select_dtypes(include=['number']).columns
                    grouped_df = numeric_df.groupby(join_col)[numeric_cols].mean().reset_index()
                    
                    # Unisci con i dati geografici
                    gdf_copy = gdf_copy.merge(grouped_df, how='left', left_on=colonna_id, right_on=join_col)
                    
                    # Crea la differenza per la colorazione
                    if 'CSX %' in gdf_copy.columns and 'CDX %' in gdf_copy.columns:
                        gdf_copy['Diff'] = gdf_copy['CSX %'] - gdf_copy['CDX %']
                        print(f"Range Diff: min={gdf_copy['Diff'].min()}, max={gdf_copy['Diff'].max()}")
                        color_col = 'Diff'
                    else:
                        color_col = None
                    
                    # Crea dati per hover più leggibili
                    hover_data = {}
                    
                    # Aggiungi le colonne di percentuali se disponibili
                    for col in ['CSX %', 'CDX %', 'Diff']:
                        if col in gdf_copy.columns:
                            hover_data[col] = ':.1f'
                    
                    # Aggiungi solo le colonne principali dei partiti per non sovraccaricare il tooltip
                    partiti_principali = [
                        "PD %", "M5S %", "FdI %", "Lega %", "FI %"
                    ]
                    for col in partiti_principali:
                        if col in gdf_copy.columns:
                            hover_data[col] = ':.1f'
                    
                except Exception as e:
                    print(f"Errore nel join dei dati: {str(e)}")
                    gdf_copy['id'] = range(len(gdf_copy))
                    hover_data = {colonna_id: True}
                    color_col = None
        else:
            # Se non ci sono dati di voto, usa il GeoDataFrame originale
            gdf_copy = gdf.copy()
            gdf_copy['id'] = range(len(gdf_copy))
            hover_data = {colonna_id: True}
            color_col = None
        
        # Crea una mappa con Plotly
        if color_col and 'Diff' in gdf_copy.columns:
            # Mappa colorata in base alla differenza CSX-CDX
            # Verifica che ci siano effettivamente differenze da visualizzare
            if gdf_copy['Diff'].notna().any():
                # Usa una scala di colori migliorata e range adattato ai dati
                max_abs_diff = max(
                    abs(gdf_copy['Diff'].min() if not pd.isna(gdf_copy['Diff'].min()) else 0), 
                    abs(gdf_copy['Diff'].max() if not pd.isna(gdf_copy['Diff'].max()) else 0)
                )
                range_color = [-max_abs_diff, max_abs_diff]  # Scala simmetrica
                
                fig = px.choropleth_mapbox(
                    gdf_copy,
                    geojson=gdf_copy.__geo_interface__,
                    locations='id',
                    color='Diff',
                    color_continuous_scale=[
                        [0, "rgb(0, 0, 255)"],       # Blu forte per CDX molto avanti
                        [0.4, "rgb(180, 180, 255)"], # Blu chiaro per CDX poco avanti
                        [0.5, "rgb(255, 255, 255)"], # Bianco per parità
                        [0.6, "rgb(255, 180, 180)"], # Rosso chiaro per CSX poco avanti
                        [1, "rgb(255, 0, 0)"]        # Rosso forte per CSX molto avanti
                    ],
                    range_color=range_color,
                    hover_name=gdf_copy[colonna_id],
                    hover_data=hover_data,
                    mapbox_style="carto-positron",
                    center={"lat": gdf_copy.geometry.centroid.y.mean(), "lon": gdf_copy.geometry.centroid.x.mean()},
                    zoom=10,
                    opacity=opacita
                )
                
                # Aggiungi una title per la colorbar
                fig.update_layout(
                    coloraxis_colorbar=dict(
                        title="Differenza % CSX-CDX",
                        tickvals=[-20, -10, 0, 10, 20],
                        ticktext=["-20%", "-10%", "0%", "+10%", "+20%"]
                    )
                )
            else:
                # Se non ci sono differenze valide, usa il colore predefinito
                fig = px.choropleth_mapbox(
                    gdf_copy,
                    geojson=gdf_copy.__geo_interface__,
                    locations='id',
                    hover_name=gdf_copy[colonna_id],
                    hover_data=hover_data,
                    mapbox_style="carto-positron",
                    center={"lat": gdf_copy.geometry.centroid.y.mean(), "lon": gdf_copy.geometry.centroid.x.mean()},
                    zoom=10,
                    opacity=opacita,
                    color_discrete_sequence=[colore]
                )
        else:
            # Mappa con colore fisso
            fig = px.choropleth_mapbox(
                gdf_copy,
                geojson=gdf_copy.__geo_interface__,
                locations='id',
                hover_name=gdf_copy[colonna_id],
                hover_data=hover_data,
                mapbox_style="carto-positron",
                center={"lat": gdf_copy.geometry.centroid.y.mean(), "lon": gdf_copy.geometry.centroid.x.mean()},
                zoom=10,
                opacity=opacita,
                color_discrete_sequence=[colore]
            )
        
        # Aumenta le dimensioni della mappa
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=600  # Altezza aumentata
        )
        
        return fig
    except Exception as e:
        print(f"Errore nella creazione della mappa Plotly: {str(e)}")
        fig = go.Figure()
        fig.update_layout(title=f"Errore: {str(e)}")
        return fig

def grafico_torta_csx(df, livello, valore):
    """
    Funzione per mostrare un grafico a torta del voto CSX.
    """
    col_pd = "PD %"
    col_m5s = "M5S %"
    col_avs = "AVS - Lista Sansa - Possibile %"
    col_orlando = "liste Orlando %"

    df_filtrato = df[df[livello] == valore]

    if df_filtrato.empty:
        return None

    media_pd = df_filtrato[col_pd].mean()
    media_m5s = df_filtrato[col_m5s].mean()
    media_avs = df_filtrato[col_avs].mean()
    media_orlando = df_filtrato[col_orlando].mean()

    dati = pd.DataFrame({
        "Partito": ["PD", "M5S", "AVS", "Liste Orlando"],
        "Percentuale": [media_pd, media_m5s, media_avs, media_orlando]
    })

    fig = px.pie(
        dati,
        names="Partito",
        values="Percentuale",
        title=f"Spaccato CSX - {livello}: {valore}",
        hole=0.3,
        color_discrete_sequence=["#235789", "#F1D302", "#C1292E", "#6a0dad"]
    )

    fig.update_traces(textinfo="label+percent", pull=[0.05] * 4)
    fig.update_layout(height=400, margin={"t": 50, "b": 0, "l": 0, "r": 0})

    return fig

def grafico_barre_partiti(df, livello, valore):
    """
    Funzione per grafico a barre comparativo partiti.
    """
    df_filtrato = df[df[livello] == valore]
    if df_filtrato.empty:
        return None

    partiti = [
        "PD %", "M5S %", "AVS - Lista Sansa - Possibile %",
        "liste Orlando %", "liste Bucci %", "Lega %", "FI %", "FdI %"
    ]

    medie = {partito: df_filtrato[partito].mean() for partito in partiti if partito in df_filtrato.columns}

    df_bar = pd.DataFrame({
        "Partito": list(medie.keys()),
        "Percentuale": list(medie.values())
    })

    fig = px.bar(
        df_bar,
        x="Partito",
        y="Percentuale",
        title=f"Confronto Partiti - {livello}: {valore}",
        text_auto=".1f"
    )

    fig.update_layout(height=400, margin={"t": 50, "b": 0, "l": 0, "r": 0})
    return fig

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

# Calcola le percentuali di CSX e CDX
def calcola_percentuali_coalizioni(df):
    """Calcola le percentuali di CSX e CDX e aggiunge le colonne al DataFrame"""
    # Identifica le colonne dei partiti di CSX e CDX
    csx_cols = []
    cdx_cols = []
    
    for col in df.columns:
        if "%" in col:
            if any(p in col for p in ["PD", "M5S", "AVS", "Orlando"]):
                csx_cols.append(col)
            elif any(p in col for p in ["Bucci", "Lega", "FI", "FdI"]):
                cdx_cols.append(col)
    
    # Calcola le percentuali totali
    if csx_cols:
        df['CSX %'] = df[csx_cols].sum(axis=1)
    if cdx_cols:
        df['CDX %'] = df[cdx_cols].sum(axis=1)
    
    return df, csx_cols, cdx_cols

# Carica i dati
municipi, sezioni, uu, voti = carica_dati()

# Aggiungi le percentuali delle coalizioni
voti, csx_cols, cdx_cols = calcola_percentuali_coalizioni(voti)

# Debug per differenze CSX-CDX
if st.sidebar.checkbox("Debug differenze CSX-CDX"):
    st.sidebar.write("Statistiche CSX-CDX:")
    if 'CSX %' in voti.columns and 'CDX %' in voti.columns:
        voti['Diff'] = voti['CSX %'] - voti['CDX %']
        st.sidebar.write(f"Min: {voti['Diff'].min():.1f}%")
        st.sidebar.write(f"Max: {voti['Diff'].max():.1f}%")
        st.sidebar.write(f"Media: {voti['Diff'].mean():.1f}%")
        st.sidebar.write("Top 5 CSX:")
        st.sidebar.write(voti.nlargest(5, 'Diff')[['Municipio', 'Diff']].reset_index(drop=True))
        st.sidebar.write("Top 5 CDX:")
        st.sidebar.write(voti.nsmallest(5, 'Diff')[['Municipio', 'Diff']].reset_index(drop=True))

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
colore = st.sidebar.color_picker("Colore poligoni (per aree senza dati)", "#2563eb")
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
