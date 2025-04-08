# utils/map_utils.py

import folium
import plotly.express as px
import geopandas as gpd
from shapely.geometry import mapping

# Mappa interattiva con Folium
def crea_mappa_folium(gdf: gpd.GeoDataFrame, colonna_id: str, colore="#2563eb", opacita=0.6) -> folium.Map:
    centro = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    m = folium.Map(location=centro, zoom_start=12, tiles="CartoDB positron")

    for _, r in gdf.iterrows():
        geojson = mapping(r.geometry)
        tooltip = f"{colonna_id}: {r[colonna_id]}"
        style = {
            "fillColor": colore,
            "color": "black",
            "weight": 1,
            "fillOpacity": opacita,
        }
        folium.GeoJson(geojson, tooltip=tooltip, style_function=lambda x: style).add_to(m)

    return m

# Mappa statistica con Plotly

def crea_mappa_plotly(
    gdf: gpd.GeoDataFrame,
    colonna_id: str,
    colore="#2563eb",
    opacita=0.6,
    metrica: str = None,
    dati_statistici: gpd.GeoDataFrame = None
):
    if dati_statistici is not None and metrica is not None:
        df = gdf.merge(dati_statistici, left_on=colonna_id, right_on="ID", how="left")
        fig = px.choropleth_mapbox(
            df,
            geojson=df.geometry,
            locations=df.index,
            color=metrica,
            hover_name=colonna_id,
            mapbox_style="carto-positron",
            center={"lat": gdf.geometry.centroid.y.mean(), "lon": gdf.geometry.centroid.x.mean()},
            zoom=11,
            opacity=opacita,
            height=600
        )
    else:
        fig = px.choropleth_mapbox(
            gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            hover_name=colonna_id,
            mapbox_style="carto-positron",
            center={"lat": gdf.geometry.centroid.y.mean(), "lon": gdf.geometry.centroid.x.mean()},
            zoom=11,
            color_discrete_sequence=[colore],
            opacity=opacita,
            height=600
        )

    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    return fig
