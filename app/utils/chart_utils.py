# utils/chart_utils.py

import pandas as pd
import plotly.express as px

# Funzione per mostrare un grafico a torta del voto CSX

def grafico_torta_csx(df: pd.DataFrame, livello: str, valore: str):
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

# Funzione per grafico a barre comparativo partiti

def grafico_barre_partiti(df: pd.DataFrame, livello: str, valore: str):
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
