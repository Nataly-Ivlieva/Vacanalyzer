""" ==========================================================
 IT-Stellenanzeigen-Analyse in Deutschland
 Web-Anwendung mit Dash für die Visualisierung und Analyse
 von Jobanzeigen im IT-Bereich
 =========================================================="""

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as px
from functions.data_loader import load_jobs
from functions.figures import (
    line_vacancies, bar_chart, pie_chart_last_date,
    scatter_bokeh, histogram_bokeh, folium_map
)

""" ----------------------------------------------------------
 Daten laden
 ----------------------------------------------------------
 Die Funktion `load_jobs()` lädt die vorverarbeiteten Jobdaten
 aus den Quelldateien (CSV oder Datenbank). Diese Daten bilden
 die Grundlage für alle Visualisierungen und Filterungen."""
df = load_jobs()

# ----------------------------------------------------------
# Initialisierung der Dash-App
# ----------------------------------------------------------
# Bootstrap wird für ein konsistentes Layout und Styling verwendet.
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

""" ----------------------------------------------------------
 Layout der Anwendung
 ----------------------------------------------------------
 Die App besteht aus Tabs, die jeweils unterschiedliche Diagramme darstellen:
 - Liniendiagramm (Zeitverlauf der Stellenanzeigen)
 - Balkendiagramm (Häufigkeit bestimmter Technologien im Zeitverlauf)
 - Kreisdiagramm (Verteilung nach Technologien oder Städten zum letzten Datum)
 - Scatterplot (Zusammenhänge zwischen Variablen)
 - Histogramm (Verteilungen von Variablen)
 - Karte (räumliche Verteilung der Jobs)"""
app.layout = dbc.Container([
    html.H1("IT-Stellenanzeigen-Analyse in Deutschland"),
    dbc.Tabs(id="tabs", active_tab="tab_line", children=[
        dbc.Tab(label="Liniendiagramm", tab_id="tab_line"),
        dbc.Tab(label="Balkendiagramm", tab_id="tab_bar"),
        dbc.Tab(label="Kreisdiagramm", tab_id="tab_pie"),
        dbc.Tab(label="Scatterplot", tab_id="tab_scatter"),
        dbc.Tab(label="Histogram", tab_id="tab_histogram"),
        dbc.Tab(label="Karte", tab_id="tab_map"),
    ]),
    html.Div(id="tab_content", className="mt-4")
])

""" ----------------------------------------------------------
 Hilfsfunktion zum Filtern der Daten
 ----------------------------------------------------------
 Diese Funktion ermöglicht es, die Daten nach Städten, Technologien
 und Zeitintervallen zu filtern. Für das Kreisdiagramm wird ein
 spezifisches Datum ausgewählt."""
def filter_df(tab, cities=None, techs=None, start=None, end=None, date=None):
    filtered = df.copy()
    if cities:
        filtered = filtered[filtered['city'].isin(cities)]
    if techs:
        filtered = filtered[filtered['tech'].isin(techs)]
    if start and end:
        filtered = filtered[(filtered['date'] >= start) & (filtered['date'] <= end)]
    if date:
        filtered = filtered[filtered['date'] == date]
    return filtered

""" ----------------------------------------------------------
 Dynamisches Rendering von Tabs
 ----------------------------------------------------------
 Abhängig vom ausgewählten Tab werden verschiedene Filter
 (Dropdowns, DatePicker) eingeblendet und das passende Diagramm angezeigt."""
@app.callback(Output("tab_content", "children"), Input("tabs", "active_tab"))
def render_tab(tab):
    filters = []

    # Filter nach Stadt
    if tab in ["tab_line", "tab_scatter", "tab_histogram"]:
        filters.append(dbc.Col([
            html.Label("Nach Stadt filtern:", className="filter-label"),
            dcc.Dropdown(
                options=[{'label': c, 'value': c} for c in sorted(df['city'].unique())],
                id=f'{tab}-city-filter',
                multi=True,
                className="dash-dropdown filter-input"
            )
        ], width=4, className="filter-col"))

    # Filter nach Technologie
    if tab in ["tab_line", "tab_scatter", "tab_histogram", "tab_map"]:
        filters.append(dbc.Col([
            html.Label("Nach Technologie filtern:", className="filter-label"),
            dcc.Dropdown(
                options=[{'label': t, 'value': t} for t in sorted(df['tech'].unique()) if t != "Other"],
                id=f'{tab}-tech-filter',
                multi=True,
                className="dash-dropdown filter-input"
            )
        ], width=4, className="filter-col"))

    # Filter nach Zeitraum (Start- und Enddatum)
    if tab in ["tab_line", "tab_bar", "tab_scatter", "tab_histogram"]:
        filters.append(dbc.Col([
            html.Label("Nach Datum filtern:", className="filter-label"),
            html.Div(dcc.DatePickerRange(
                id=f'{tab}-date-filter',
                min_date_allowed=df['date'].min(),
                max_date_allowed=df['date'].max(),
                start_date=df['date'].min(),
                end_date=df['date'].max(),
                className="dash-date-picker filter-input"
            ), className="date-filter-wrapper")
        ], width=4, className="filter-col"))

    # Auswahl eines spezifischen Datums für Kreisdiagramm
    if tab == "tab_pie":
        filters.append(dbc.Col([
            html.Label("Datum auswählen:", className="filter-label"),
            dcc.DatePickerSingle(
                id=f'{tab}-date-filter',
                min_date_allowed=df['date'].min(),
                max_date_allowed=df['date'].max(),
                date=df['date'].max(),
                className="dash-date-picker filter-input"
            )
        ], width=4, className="filter-col"))

    filter_row = dbc.Row(filters, className="filter-row", align="center")

    # Darstellung: Plotly-Diagramme oder Bokeh/Folium in Iframe
    graph = html.Iframe(id=f'{tab}-graph', width="100%", height="600") \
        if tab in ["tab_scatter", "tab_histogram", "tab_map"] else dcc.Graph(id=f'{tab}-graph')

    return dbc.Container([filter_row, graph])

""" ----------------------------------------------------------
Callbacks zur Aktualisierung der Diagramme
----------------------------------------------------------
Für jeden Tab wird ein eigener Callback definiert,
der die Daten entsprechend filtert und das Diagramm rendert."""

# Liniendiagramm (Zeitreihe)
@app.callback(Output('tab_line-graph', 'figure'),
              Input('tab_line-city-filter', 'value'),
              Input('tab_line-tech-filter', 'value'),
              Input('tab_line-date-filter', 'start_date'),
              Input('tab_line-date-filter', 'end_date'))
def update_line(cities, techs, start, end):
    df_filtered = filter_df('tab_line', cities, techs, start, end)
    if df_filtered.empty:
        return px.line(title="Keine Daten für die ausgewählten Filter verfügbar")
    return line_vacancies(df_filtered)

# Balkendiagramm
@app.callback(Output('tab_bar-graph', 'figure'),
              Input('tab_bar-date-filter', 'start_date'),
              Input('tab_bar-date-filter', 'end_date'))
def update_bar(start, end):
    df_filtered = filter_df('tab_bar', start=start, end=end)
    if df_filtered.empty:
        return px.bar(title="Keine Daten für die ausgewählten Filter verfügbar")
    return bar_chart(df_filtered)

# Kreisdiagramm
@app.callback(Output('tab_pie-graph', 'figure'),
              Input('tab_pie-date-filter', 'date'))
def update_pie(date):
    df_filtered = filter_df('tab_pie', date=date)
    if df_filtered.empty:
        return px.pie(title="Keine Daten für das ausgewählte Datum verfügbar")
    return pie_chart_last_date(df_filtered)

# Scatterplot (Bokeh)
@app.callback(Output('tab_scatter-graph', 'srcDoc'),
              Input('tab_scatter-city-filter', 'value'),
              Input('tab_scatter-tech-filter', 'value'),
              Input('tab_scatter-date-filter', 'start_date'),
              Input('tab_scatter-date-filter', 'end_date'))
def update_scatter(cities, techs, start, end):
    df_filtered = filter_df('tab_scatter', cities=cities, techs=techs, start=start, end=end)
    return scatter_bokeh(df_filtered)

# Histogramm (Bokeh)
@app.callback(Output('tab_histogram-graph', 'srcDoc'),
              Input('tab_histogram-city-filter', 'value'),
              Input('tab_histogram-tech-filter', 'value'),
              Input('tab_histogram-date-filter', 'start_date'),
              Input('tab_histogram-date-filter', 'end_date'))
def update_histogram(cities, techs, start, end):
    df_filtered = filter_df('tab_histogram', cities=cities, techs=techs, start=start, end=end)
    return histogram_bokeh(df_filtered)

# Karte (Folium)
@app.callback(Output('tab_map-graph', 'srcDoc'),
              Input('tab_map-tech-filter', 'value'))
def update_map(techs):
    df_filtered = filter_df('tab_map', techs=techs)
    if not df_filtered.empty:
        last_date = df_filtered['date'].max()
        df_filtered = df_filtered[df_filtered['date'] == last_date]
    df_filtered = df_filtered.dropna(subset=['latitude', 'longitude'])

    if df_filtered.empty:
        return "<h3 style='color:red;'>Keine Standorte verfügbar</h3>"

    fmap = folium_map(df_filtered)
    return fmap._repr_html_()

# ----------------------------------------------------------
# Start der Anwendung
# ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)