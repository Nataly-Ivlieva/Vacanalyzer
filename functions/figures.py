"""
Import der benötigten Bibliotheken für Datenvisualisierung:
- Plotly für interaktive Diagramme
- Folium für Karten
- Bokeh für Scatterplots und Histogramme
- Matplotlib (für Backend-Konfiguration)
"""
import plotly.express as px
import folium
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
import matplotlib
matplotlib.use('Agg')
from bokeh.transform import factor_cmap
from bokeh.palettes import Category10

# ------------------ Plotly Charts ------------------

def line_vacancies(df):
    """
    Erzeugt ein Liniendiagramm, das die Anzahl der Stellenanzeigen
    im Zeitverlauf nach Technologien darstellt.
    """
    df_count = df.groupby(['date', 'tech']).size().reset_index(name='Stellenanzeigen')
    fig = px.line(
        df_count, x='date', y='Stellenanzeigen', color='tech',
        template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Set2,
        hover_data={'Stellenanzeigen': True, 'tech': True, 'date': True}
    )
    fig.update_traces(mode='lines+markers',
                      customdata=df_count[['date', 'tech']].values,
                      hovertemplate='%{y} Stellenanzeigen für %{fullData.name} am %{x}')
    fig.update_layout(title="Stellenanzeigen im Zeitverlauf",
                      xaxis_title="Datum", yaxis_title="Anzahl der Stellenanzeigen",
                      plot_bgcolor='#1f2c56', paper_bgcolor='#1f2c56', font=dict(color='white'))
    return fig

def bar_chart(df):
    """
    Erzeugt ein Balkendiagramm, das die Anzahl der Stellenanzeigen
    pro Technologie anzeigt.
    """
    df_count = df.groupby('tech').size().reset_index(name='Stellenanzeigen')
    fig = px.bar(df_count, x='tech', y='Stellenanzeigen', color='tech',
                 template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(hovertemplate='Insgesamt %{y} Stellenanzeigen für %{x}')
    fig.update_layout(title="Stellenanzeigen nach Technologien",
                      xaxis_title="Technologie", yaxis_title="Anzahl der Stellenanzeigen",
                      plot_bgcolor='#1f2c56', paper_bgcolor='#1f2c56', font=dict(color='white'))
    return fig

def pie_chart_last_date(df, min_pct=0.05):
    """
    Erzeugt ein Kreisdiagramm für das zuletzt vorhandene Datum.
    Kleine Werte (unterhalb eines definierten Schwellenwerts)
    werden unter 'Andere' zusammengefasst.
    """
    last_date = df['date'].max()
    df_last = df[df['date'] == last_date].groupby('tech').size().reset_index(name='Stellenanzeigen')
    total = df_last['Stellenanzeigen'].sum()
    df_last['pct'] = df_last['Stellenanzeigen'] / total
    df_last.loc[df_last['pct'] < min_pct, 'tech'] = 'Andere'
    df_last = df_last.groupby('tech')['Stellenanzeigen'].sum().reset_index()
    fig = px.pie(df_last, names='tech', values='Stellenanzeigen',
                 template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(textinfo='percent+label',
                      hovertemplate='%{label}: %{value} Stellenanzeigen (%{percent})')
    fig.update_layout(title=f"Technologien – Anteil an den Stellenanzeigen am {last_date.strftime('%d.%m.%Y')}")
    return fig

# ------------------ Folium Map ------------------

def folium_map(df):
    """
    Erzeugt eine interaktive Karte mit Markierungen der Stellenanzeigenstandorte.
    Jede Markierung enthält Informationen zur Technologie, zum Bezirk
    und einen Link zur Stellenausschreibung.
    """
    fmap = folium.Map(location=[51.1657, 10.4515], zoom_start=6)
    for _, row in df.iterrows():
        popup_html = f"""
        <b>Technologie:</b> {row['tech']}<br>
        <b>Bezirk:</b> {row['district']}<br>
        <a href="{row['redirect_url']}" target="_blank">Zur Stelle</a>
        """
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            popup=folium.Popup(popup_html, max_width=300),
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(fmap)
    return fmap

def bokeh_to_iframe(p):
    """
    Hilfsfunktion: Konvertiert ein Bokeh-Diagramm in eine HTML-Iframe-Darstellung.
    """
    script, div = components(p)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-3.8.0.min.css" type="text/css">
        <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.8.0.min.js"></script>
        {script}
    </head>
    <body style="margin:0; background-color:#1f2c56">{div}</body>
    </html>
    """
    return html.strip()   


# ------------------ Scatter ------------------
def scatter_bokeh(df):
    """
    Erzeugt einen Scatterplot mit den 20 Städten mit den meisten Anzeigen.
    Die Anzahl der Stellenanzeigen wird pro Technologie visualisiert,
    inklusive interaktivem Hover-Tooltip.
    """
    top_cities = (
        df.groupby("city")
        .size()
        .sort_values(ascending=False)
        .head(20)
        .index.tolist()
    )
    df_grouped = (
        df[df["city"].isin(top_cities)]
        .groupby(["city", "tech"])
        .size()
        .reset_index(name="Stellenanzeigen")
    )

    source = ColumnDataSource(df_grouped)

    cities = df_grouped["city"].unique().tolist()
    technologies = df_grouped["tech"].unique().tolist()

    p = figure(
        title="Scatterplot: Technologien pro Stadt (Top 20 Städte)",
        x_range=FactorRange(*cities),
        width=1200, height=600,
        background_fill_color="#1f2c56",
        border_fill_color="#1f2c56"
    )

    r=p.scatter(
        x="city",
        y="Stellenanzeigen",
        source=source,
        size=12,
        alpha=0.9,
        line_color="white",
        line_width=0.5,
        color=factor_cmap(
            "tech",
            palette=Category10[10] * (len(technologies) // 10 + 1),
            factors=technologies
        ),
        legend_field="tech"
    )

    hover = HoverTool(
    renderers=[r],
    tooltips=[
        ("Stadt", "@city"),
        ("Stellenanzeigen", "@Stellenanzeigen"),
        ("Technologie", "@tech")
    ]
)

    p.add_tools(hover)

    p.title.text_color = "white"
    p.xaxis.axis_label_text_color = "white"
    p.yaxis.axis_label_text_color = "white"
    p.xaxis.major_label_text_color = "white"
    p.yaxis.major_label_text_color = "white"
    p.xaxis.axis_label = "Stadt"
    p.yaxis.axis_label = "Anzahl Stellenanzeigen"

    p.xaxis.major_label_orientation = 0.8  
    p.xaxis.major_label_text_font_size = "8pt"


    p.add_layout(p.legend[0], 'right')
    p.legend[0].orientation = "vertical"
    p.legend[0].label_text_color = "white"
    p.legend[0].background_fill_color = "#2c3e50"
    p.legend[0].border_line_color = None
    p.min_border_right = 200

    p.min_border_bottom = 50
    p.min_border_left = 50

    return bokeh_to_iframe(p)

# ------------------ Histogram ------------------
def histogram_bokeh(df):
    def histogram_bokeh(df):
        """
        Erzeugt ein Histogramm, das die Gesamtanzahl der Stellenanzeigen pro Tag darstellt.
        Zusätzlich werden die Technologien angezeigt, die an den jeweiligen Tagen vorkommen.
        """
    df_grouped = df.groupby(["date", "tech"]).size().reset_index(name="count")

    df_count = df_grouped.groupby("date").agg({
        "count": "sum",
        "tech": lambda x: ", ".join(sorted(x.unique()))
    }).reset_index().rename(columns={"count": "Stellenanzeigen", "tech": "Technologien"})

    source = ColumnDataSource(df_count)

    p = figure(
        title="Histogramm: Anzahl Stellenanzeigen pro Tag",
        width=1200, height=500,
        x_axis_type="datetime",
        background_fill_color="#1f2c56",
        border_fill_color="#1f2c56",
        x_axis_label="Datum", y_axis_label="Anzahl Stellenanzeigen"
    )

    bars = p.vbar(
        x="date",
        top="Stellenanzeigen",        
        source=source,
        width=24 * 60 * 60 * 1000 * 0.8,
        fill_color="#FFA500",
        fill_alpha=0.8,
        line_color="white",
        line_width=1.2,
        name="bars"
    )

    hover = HoverTool(
        tooltips=[
            ("Datum", "@date{%F}"),
            ("Anzahl", "@Stellenanzeigen"),
            ("Technologien", "@Technologien")
        ],
        formatters={"@date": "datetime"},
        renderers=[bars],
        mode="mouse"
    )
    p.add_tools(hover)

    p.title.text_color = "white"
    p.xaxis.axis_label_text_color = "white"
    p.yaxis.axis_label_text_color = "white"
    p.xaxis.major_label_text_color = "white"
    p.yaxis.major_label_text_color = "white"

    return bokeh_to_iframe(p)