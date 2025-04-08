# utils/map_utils.py

import folium
import plotly.express as px
import pandas as pd

def formatta_percentuale(valore):
    """Formatta un valore numerico come percentuale con 1 decimale"""
    if pd.isna(valore):
        return "N/A"
    return f"{valore:.1f}%"

def crea_mappa_folium(gdf, colonna_id, colore, opacita, df_voti=None, join_col=None, partiti_cols=None):
    """
    Crea una mappa Folium con i dati GeoJSON e tooltip con percentuali.
    """
    # Verifica che la colonna esista
    if colonna_id not in gdf.columns:
        print(f"Errore in crea_mappa_folium: La colonna '{colonna_id}' non è presente nei dati.")
        print(f"Colonne disponibili: {gdf.columns.tolist()}")
        # Usa la prima colonna che non è 'geometry'
        for col in gdf.columns:
            if col != 'geometry' and col != '_umap_options':
                colonna_id = col
                print(f"Usando la colonna '{colonna_id}' come alternativa.")
                break
        else:
            return folium.Map(location=[44.4056, 8.9463], zoom_start=12)  # Mappa vuota centrata su Genova
    
    # Unisci i dati di voto se disponibili
    if df_voti is not None and join_col is not None:
        # Crea una copia per evitare di modificare l'originale
        gdf_copy = gdf.copy()
        
        # Preparazione dei dati per il join
        if join_col not in df_voti.columns:
            print(f"Colonna di join '{join_col}' non trovata in df_voti")
        else:
            # Converte la colonna di join in string per entrambi i dataframe
            gdf_copy[colonna_id] = gdf_copy[colonna_id].astype(str)
            df_voti[join_col] = df_voti[join_col].astype(str)
            
            try:
                # Calcola percentuali CSX e CDX se non presenti
                if 'CSX %' not in df_voti.columns and partiti_cols:
                    csx_cols = [col for col in partiti_cols if any(p in col for p in ["PD", "M5S", "AVS", "Orlando"])]
                    df_voti['CSX %'] = df_voti[csx_cols].sum(axis=1)
                
                if 'CDX %' not in df_voti.columns and partiti_cols:
                    cdx_cols = [col for col in partiti_cols if any(p in col for p in ["Bucci", "Lega", "FI", "FdI"])]
                    df_voti['CDX %'] = df_voti[cdx_cols].sum(axis=1)
                
                # Raggruppa i dati per la colonna di join se necessario
                grouped_df = df_voti.groupby(join_col).mean().reset_index()
                
                # Unisci con i dati geografici
                gdf_copy = gdf_copy.merge(grouped_df, how='left', left_on=colonna_id, right_on=join_col)
                
                # Crea la lista di campi per il tooltip
                tooltip_fields = [colonna_id]
                tooltip_labels = [colonna_id]
                
                # Aggiungi le colonne di percentuali se disponibili
                for col in ['CSX %', 'CDX %']:
                    if col in gdf_copy.columns:
                        tooltip_fields.append(col)
                        tooltip_labels.append(col)
                
                # Aggiungi le colonne dei partiti se disponibili
                if partiti_cols:
                    for col in partiti_cols:
                        if col in gdf_copy.columns:
                            tooltip_fields.append(col)
                            tooltip_labels.append(col)
                
                # Colora la mappa in base alla differenza tra CSX e CDX
                if 'CSX %' in gdf_copy.columns and 'CDX %' in gdf_copy.columns:
                    gdf_copy['Diff'] = gdf_copy['CSX %'] - gdf_copy['CDX %']
                    
                    # Funzione per determinare il colore in base alla differenza
                    def get_color(feature):
                        diff = feature['properties'].get('Diff', 0)
                        if pd.isna(diff):
                            return {'fillColor': '#CCCCCC', 'color': 'black', 'weight': 1, 'fillOpacity': opacita}
                        
                        # Blu per CDX, Rosso per CSX
                        if diff > 0:  # CSX avanti
                            intensity = min(abs(diff) / 20, 1)  # Normalizza la differenza
                            return {
                                'fillColor': f'rgb({255*intensity}, 0, 0)',  # Rosso con intensità variabile
                                'color': 'black',
                                'weight': 1,
                                'fillOpacity': opacita
                            }
                        else:  # CDX avanti
                            intensity = min(abs(diff) / 20, 1)  # Normalizza la differenza
                            return {
                                'fillColor': f'rgb(0, 0, {255*intensity})',  # Blu con intensità variabile
                                'color': 'black',
                                'weight': 1,
                                'fillOpacity': opacita
                            }
                else:
                    # Se non ci sono dati di voto, usa il colore predefinito
                    def get_color(feature):
                        return {'fillColor': colore, 'color': 'black', 'weight': 1, 'fillOpacity': opacita}
            
            except Exception as e:
                print(f"Errore nel join dei dati: {str(e)}")
                # Usa il GeoDataFrame originale
                gdf_copy = gdf
                tooltip_fields = [colonna_id]
                tooltip_labels = [colonna_id]
                
                # Funzione colore predefinito
                def get_color(feature):
                    return {'fillColor': colore, 'color': 'black', 'weight': 1, 'fillOpacity': opacita}
        
    else:
        # Se non ci sono dati di voto, usa il GeoDataFrame originale
        gdf_copy = gdf
        tooltip_fields = [colonna_id]
        tooltip_labels = [colonna_id]
        
        # Funzione colore predefinito
        def get_color(feature):
            return {'fillColor': colore, 'color': 'black', 'weight': 1, 'fillOpacity': opacita}
    
    try:
        # Crea una mappa centrata sui dati
        m = folium.Map(location=[gdf_copy.geometry.centroid.y.mean(), gdf_copy.geometry.centroid.x.mean()], 
                      zoom_start=11)  # Zoom modificato per una vista più ampia
        
        # Aggiungi i dati GeoJSON alla mappa
        folium.GeoJson(
            gdf_copy,
            name=colonna_id,
            style_function=get_color,
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                labels=tooltip_labels,
                localize=True,
                sticky=True
            )
        ).add_to(m)
        
        # Rendi la mappa a schermo intero
        m.get_root().html.add_child(folium.Element("""
        <style>
        .folium-map {
            width: 100%;
            height: 600px !important;  /* Altezza aumentata */
        }
        </style>
        """))
        
        return m
    except Exception as e:
        print(f"Errore nella creazione della mappa Folium: {str(e)}")
        return folium.Map(location=[44.4056, 8.9463], zoom_start=12)

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
                    # Calcola percentuali CSX e CDX se non presenti
                    if 'CSX %' not in df_voti.columns and partiti_cols:
                        csx_cols = [col for col in partiti_cols if any(p in col for p in ["PD", "M5S", "AVS", "Orlando"])]
                        df_voti['CSX %'] = df_voti[csx_cols].sum(axis=1)
                    
                    if 'CDX %' not in df_voti.columns and partiti_cols:
                        cdx_cols = [col for col in partiti_cols if any(p in col for p in ["Bucci", "Lega", "FI", "FdI"])]
                        df_voti['CDX %'] = df_voti[cdx_cols].sum(axis=1)
                    
                    # Raggruppa i dati per la colonna di join se necessario
                    grouped_df = df_voti.groupby(join_col).mean().reset_index()
                    
                    # Unisci con i dati geografici
                    gdf_copy = gdf_copy.merge(grouped_df, how='left', left_on=colonna_id, right_on=join_col)
                    
                    # Crea la differenza per la colorazione
                    if 'CSX %' in gdf_copy.columns and 'CDX %' in gdf_copy.columns:
                        gdf_copy['Diff'] = gdf_copy['CSX %'] - gdf_copy['CDX %']
                        color_col = 'Diff'
                    else:
                        color_col = None
                    
                    # Crea dati per hover
                    hover_data = {colonna_id: True}
                    
                    # Aggiungi le colonne di percentuali se disponibili
                    for col in ['CSX %', 'CDX %']:
                        if col in gdf_copy.columns:
                            hover_data[col] = ':.1f'
                    
                    # Aggiungi le colonne dei partiti se disponibili
                    if partiti_cols:
                        for col in partiti_cols:
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
        if color_col:
            # Mappa colorata in base alla differenza CSX-CDX
            fig = px.choropleth_mapbox(
                gdf_copy,
                geojson=gdf_copy.__geo_interface__,
                locations='id',
                color=color_col,
                color_continuous_scale=[[0, 'blue'], [0.5, 'white'], [1, 'red']],
                range_color=[-30, 30],  # Scala da -30% a +30%
                hover_name=gdf_copy[colonna_id],
                hover_data=hover_data,
                mapbox_style="carto-positron",
                center={"lat": gdf_copy.geometry.centroid.y.mean(), "lon": gdf_copy.geometry.centroid.x.mean()},
                zoom=10,
                opacity=opacita
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
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(title=f"Errore: {str(e)}")
        return fig
