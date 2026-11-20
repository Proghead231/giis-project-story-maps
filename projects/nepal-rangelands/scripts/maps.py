import folium
import leafmap.foliumap as leafmap
from branca.element import Element, MacroElement
from jinja2 import Template
import geopandas as gpd
import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv()


rangeland_color_map = ["#38ff1e", "#38ff1e"]
STADIA_API_KEY = os.getenv("STADIA_API_KEY")
provinces = gpd.read_file(r"data/province_bounds_json.geojson")
karnali = provinces[provinces['name_eng'] == 'Karnali'] #already in WGS84
field_sites = gpd.read_file(r"data\eco_survey_sites_json.geojson")

# 5. Scroll-aware resize & fitBounds macro (prevents gray tiles when revealed on scroll) (has no effect so commented)
# class FitBoundsOnReveal(MacroElement):
#     def __init__(self, bounds):
#         super().__init__()
#         self._template = Template(f"""
#             {{% macro script(this, kwargs) %}}
#             function adjustMap() {{
#                 var map = {{{{ this._parent.get_name() }}}};
#                 map.invalidateSize();
#                 map.fitBounds({bounds}, {{padding: [25, 25]}});
#             }}
#             window.addEventListener("load", function() {{
#                 setTimeout(adjustMap, 300);
#             }});
#             var container = document.getElementById("{{{{ this._parent.get_name() }}}}");
#             if (container && typeof ResizeObserver !== "undefined") {{
#                 var ro = new ResizeObserver(function() {{
#                     adjustMap();
#                 }});
#                 ro.observe(container);
#             }}
#             {{% endmacro %}}
#         """)

class RecenterMap(MacroElement):
    def __init__(self, lat, lon, zoom):
        super().__init__()
        self._template = Template(f"""
            {{% macro script(this, kwargs) %}}
            window.addEventListener("load", function() {{
                setTimeout(function() {{
                    var map = {{{{ this._parent.get_name() }}}};
                    map.invalidateSize();
                    map.setView([{lat}, {lon}], {zoom});
                }}, 300);
            }});
            {{% endmacro %}}
        """)

def make_national_map():
    m_nat = leafmap.Map(
        # center=[center_lat, center_lon],
        # zoom=5,
        # height=1000,
        tiles = None
    )
    m_nat.add_basemap("Stadia.StamenTerrain", api_key=STADIA_API_KEY)

    m_nat.add_raster(
        r"data/nepal_rangeland_image.tif",
        layer_name="Nepal Rangelands",
        vmin=1,
        vmax=1,
        nodata=0,
        colormap=rangeland_color_map,
        opacity=1.0,
        zoom_to_layer=False,
    )

    m_nat.add_gdf(
        provinces,
        layer_name="Provinces",
        style={
            "color": "#ffffff",
            "weight": 2.5,
            "fillOpacity": 0.0,
            "dashArray": "5, 5",
            
        },
        zoom_to_layer=False,
        info_mode=None
    )
    for _, row in provinces.iterrows():
        pt = row.geometry.representative_point()
        label_text = str(row["name_eng"])

        folium.Marker(
            location=[pt.y, pt.x],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, -22),  # Positive Y moves the label UP (increase for more gap)
                html=f"""
                    <div style="
                        transform: translate(-50%, -100%);
                        display: inline-block;
                        font-size: 12pt;
                        font-weight: normal;
                        color: #000000;
                        text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                        white-space: nowrap;
                        text-align: center;
                    ">{label_text}</div>
                """,
            ),
        ).add_to(m_nat)

    m_nat.add_child(RecenterMap(28.165295, 84.470657, 7))
    
    # 4. Inject Multiply blend mode for the 2nd layer (your raster)
    blend_css = Element("""
    <style>
    .leaflet-tile-pane .leaflet-layer:nth-child(2) {
        mix-blend-mode: multiply;
    }
    </style>
    """)
    m_nat.get_root().html.add_child(blend_css)
    m_nat.add_image(
        image="images/rangeland_barplot.png",
        position=(0, 0),
    )
    # 5. Render the map as the final expression in the cell
    return m_nat

def make_karnali_map():
    minx, miny, maxx, maxy = karnali.total_bounds
    karnali_bounds = [[miny, minx], [maxy, maxx]]
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    # 1. Increase map height to fill the viewport
    m_karnali = leafmap.Map(
        # center=[center_lat, center_lon],
        # zoom=8,
        # height=1000, 
        tiles = None
    )
    m_karnali.add_basemap("Stadia.StamenTerrain", api_key=STADIA_API_KEY)

    m_karnali.add_raster(
        r"data\nepal_rangeland_image.tif",
        layer_name="Nepal Rangelands",
        vmin=1,
        vmax=1,
        nodata=0,
        colormap=rangeland_color_map,
        opacity=1.0,
        zoom_to_layer=False,
    )

    m_karnali.add_gdf(
        karnali,
        layer_name="Karnali Province",
        style={
            "color": "#ffffff",
            "weight": 2.5,
            "fillOpacity": 0.0,
            "dashArray": "5, 5"
        },
        info_mode=None
    )

    for _, row in karnali.iterrows():
        pt = row.geometry.representative_point()
        label_text = str(row["name_eng"])

        folium.Marker(
            location=[pt.y, pt.x],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, -22),  # Positive Y moves the label UP (increase for more gap)
                html=f"""
                    <div style="
                        transform: translate(-50%, -100%);
                        display: inline-block;
                        font-size: 12pt;
                        font-weight: normal;
                        color: #000000;
                        text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                        white-space: nowrap;
                        text-align: center;
                    ">{label_text}</div>
                """,
            ),
        ).add_to(m_karnali)

    # m_karnali.add_child(FitBoundsOnReveal(karnali_bounds))
    m_karnali.add_child(RecenterMap(29.049975, 82.151980, 8))
    # 4. Inject Multiply blend mode for the 2nd layer (your raster)
    blend_css = Element("""
    <style>
    .leaflet-tile-pane .leaflet-layer:nth-child(2) {
        mix-blend-mode: multiply;
    }
    </style>
    """)
    m_karnali.get_root().html.add_child(blend_css)

    # 5. Render the map as the final expression in the cell
    return m_karnali

def make_field_map():
    # 1. Increase map height to fill the viewport
    m_field = leafmap.Map(
        # center=[center_lat, center_lon],
        # zoom=8,
        # height=1000, 
        tiles = None
    )
    m_field.add_basemap("Stadia.StamenTerrain", api_key=STADIA_API_KEY)

    m_field.add_raster(
        r"data\nepal_rangeland_image.tif",
        layer_name="Nepal Rangelands",
        vmin=1,
        vmax=1,
        nodata=0,
        colormap=rangeland_color_map,
        opacity=1.0,
        zoom_to_layer=False,
    )

    m_field.add_gdf(
        karnali,
        layer_name="Karnali Province",
        style={
            "color": "#ffffff",
            "weight": 2.5,
            "fillOpacity": 0.0,
            "dashArray": "5, 5"
        },
        info_mode=None
    )
    m_field.add_gdf(
        field_sites,
        layer_name="Field Survey Sites",
        style={
            "color": "#fd0000",
            "weight": 2.5,
            "fillOpacity": 0.0,
            "dashArray": "5, 5"
        },
        info_mode=None
    )

    for _, row in field_sites.iterrows():
        pt = row.geometry.representative_point()
        label_text = str(row["pasture"])

        folium.Marker(
            location=[pt.y, pt.x],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, 36),  # Positive Y moves the label UP (increase for more gap)
                html=f"""
                    <div style="
                        transform: translate(-50%, -100%);
                        display: inline-block;
                        font-size: 12pt;
                        font-weight: normal;
                        color: #000000;
                        text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                        white-space: nowrap;
                        text-align: center;
                    ">{label_text}</div>
                """,
            ),
        ).add_to(m_field)

    m_field.add_child(RecenterMap(29.0674303, 82.6130036, 10))
    # 4. Inject Multiply blend mode for the 2nd layer (your raster)
    blend_css = Element("""
    <style>
    .leaflet-tile-pane .leaflet-layer:nth-child(2) {
        mix-blend-mode: multiply;
    }
    </style>
    """)
    m_field.get_root().html.add_child(blend_css)

    # 5. Render the map as the final expression in the cell
    return m_field