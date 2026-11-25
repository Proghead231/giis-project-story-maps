import json
import os
import folium
import geopandas as gpd
import leafmap.foliumap as leafmap
from branca.element import Element, MacroElement
from dotenv import load_dotenv
from jinja2 import Template
import base64

load_dotenv()

rangeland_color_map = ["#38ff1e", "#38ff1e"]
STADIA_API_KEY = os.getenv("STADIA_API_KEY")
provinces = gpd.read_file("data/province_bounds_json.geojson")
districts = gpd.read_file("data/districts.geojson")
districts = districts[districts["DISTRICT"].isin(["JUMLA", "DOLPA"])]
field_sites = gpd.read_file("data/eco_survey_sites_json.geojson")

VIEWS = {
    "nat":     {"lat": 28.165295,  "lon": 84.470657, "zoom": 7},
    "karnali": {"lat": 29.049975,  "lon": 82.151980, "zoom": 8},
    "field":   {"lat": 29.169920000000047, "lon": 82.51973000000004, "zoom": 9},
    "restoration":   {"lat": 29.2975564, "lon": 82.2855706, "zoom": 10},
    "thuloguthi": {"lat": 29.20410000000004, "lon": 82.30480000000006, "zoom": 15},
    "patrasi": {"lat": 29.3300433, "lon": 82.3067474, "zoom": 11},
}


class ViewController(MacroElement):
    def __init__(self, views, groups, view_layers):
        super().__init__()
        self.views_json = json.dumps(views)
        self.groups = groups                      # {"provinces": group, "field": group}
        self.view_layers_json = json.dumps(view_layers)
        self._template = Template("""
            {% macro script(this, kwargs) %}
            (function () {
                var map = {{ this._parent.get_name() }};
                var VIEWS = {{ this.views_json }};
                var VIEW_LAYERS = {{ this.view_layers_json }};
                var GROUPS = {
                    {% for key, g in this.groups.items() %}
                    "{{ key }}": {{ g.get_name() }},
                    {% endfor %}
                };

                function applyLayers(name, addToo) {
                    var want = VIEW_LAYERS[name] || [];
                    Object.keys(GROUPS).forEach(function (k) {
                        var g = GROUPS[k], on = map.hasLayer(g);
                        if (want.indexOf(k) === -1) {
                            if (on) map.removeLayer(g);
                        } else if (addToo && !on) {
                            map.addLayer(g);
                        }
                    });
                }

                window.goToView = function (name, animate) {
                    var v = VIEWS[name];
                    if (!v) return;
                    window.__view = name;
                    map.invalidateSize();

                    applyLayers(name, animate === false);   // remove now; add now only if no animation

                    var same = map.getCenter().distanceTo([v.lat, v.lon]) < 50 && map.getZoom() === v.zoom;

                    if (animate === false || same) {
                        map.setView([v.lat, v.lon], v.zoom);
                        applyLayers(name, true);
                    } else {
                        map.once("moveend", function () {
                            if (window.__view === name) applyLayers(name, true);
                        });
                        map.flyTo([v.lat, v.lon], v.zoom, {duration: 1.6});
                    }
                };

                window.addEventListener("load", function () {
                    setTimeout(function () { window.goToView("nat", false); }, 300);
                });
            })();
            {% endmacro %}
        """)


def _label(text, cls, anchor_y, label_size, anchor_x=0, font_color="#000"):
        # big: 12pt,
        # medium: 10pt,
        # smal": 8pt,
    size_css = f"{label_size}px" if isinstance(label_size, (int, float)) else str(label_size)
    html = f"""
        <div style="
            transform: translate(-50%, -100%);
            display: inline-block;
            font-size: {size_css};
            color: {font_color};
            white-space: nowrap;
            text-align: center;
            text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff,
                         -1px 1px 0 #fff, 1px 1px 0 #fff;
        ">{text}</div>
    """

    return folium.DivIcon(
        icon_size=(0, 0),
        icon_anchor=(anchor_x, anchor_y),
        class_name=cls,
        html=html,
    )

def build_field_group(name, keep=None):
    triangle_svg = """
        <svg width="14" height="14" viewBox="0 0 14 14">
        <polygon points="7,1 13,12 1,12" fill="#fd0000" fill-opacity="0.85" stroke="#ffffff" stroke-width="1.5"/>
        </svg>
    """
    
    g = folium.FeatureGroup(name=name, show=False)
    sites = field_sites if keep is None else field_sites[field_sites["pasture"].isin(keep)]

    folium.GeoJson(
        sites[["pasture", "geometry"]].__geo_interface__,
        marker=folium.Marker(icon=folium.DivIcon(
            html=triangle_svg, icon_size=(14, 14), icon_anchor=(7, 7))),
    ).add_to(g)

    for _, row in sites.iterrows():
        pt = row.geometry.representative_point()
        folium.Marker([pt.y, pt.x],
                      icon=_label(row["pasture"], "lbl", 10, 12, 0, "#fd0000")).add_to(g)
    return g

def make_map():
    m = leafmap.Map(tiles=None)
    # m.add_basemap("Stadia.StamenTerrain", api_key=STADIA_API_KEY)
    terrain = folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Terrain", show=True,
        max_native_zoom=13, max_zoom=20, z_index=1,
    ).add_to(m)
    satellite = folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics", name="Satellite", show=False,
        max_native_zoom=19, max_zoom=20, z_index=1,
    ).add_to(m)
    labels = folium.TileLayer(
        tiles=f"https://tiles.stadiamaps.com/tiles/stamen_terrain_labels/{{z}}/{{x}}/{{y}}{{r}}.png?api_key={STADIA_API_KEY}",
        attr='© Stadia Maps © Stamen Design © OpenMapTiles © OpenStreetMap contributors',
        name="Map Labels",
        overlay=True,
        control=True,
        show=True,
        max_zoom=20,
        z_index=3
    ).add_to(m)

    with open("data/nepal_rangeland.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    rangeland_overlay = folium.raster_layers.ImageOverlay(
        image=f"data:image/png;base64,{b64}",
        bounds=[[26.35, 80.05], [30.45, 88.20]],    # Nepal bounds
        opacity=1,
        name="Nepal Rangelands",
        interactive=False,
        zindex=10,
    ).add_to(m)
    
    province_group = folium.FeatureGroup(name="Province", show=False)

    folium.GeoJson(
        provinces[["name_eng", "geometry"]].__geo_interface__,
        style_function=lambda f: {"color": "#7c0c31", "weight": 2.5,
                                "fillOpacity": 0.0, "dashArray": "5, 5"},
    ).add_to(province_group)
    district_group = folium.FeatureGroup(name="District", show=False)
    folium.GeoJson(
        districts[["DISTRICT", "geometry"]].__geo_interface__,
        style_function=lambda f: {"color": "#ff0055", "weight": 2.5,
                                "fillOpacity": 0.0},
    ).add_to(district_group)

    field_group = build_field_group("Field Survey Sites")
    restoration_group = build_field_group("All restoration sites",
                                         keep=["Thulo Guthichaur", "Salimkot", "Dudhe Patan", "Bhaisi Goth"])
    thuloguthi_group = build_field_group("Thuli Guthichaur",
                                         keep=["Thulo Guthichaur"])
    patrasi_group = build_field_group("Patrasi",
                                         keep=["Salimkot", "Dudhe Patan", "Bhaisi Goth"]) 
    
    for _, row in provinces.iterrows():
        pt = row.geometry.representative_point()
        folium.Marker([pt.y, pt.x], icon=_label(row["name_eng"], "lbl lbl-prov", -22, 16)).add_to(province_group)
    for _, row in districts.iterrows():
        pt = row.geometry.representative_point()
        folium.Marker([pt.y, pt.x], icon=_label(row["DISTRICT"], "lbl lbl-site", -40, 14, 30)).add_to(district_group)
    for _, row in field_sites.iterrows():
        pt = row.geometry.representative_point()
        folium.Marker([pt.y, pt.x], icon=_label(row["pasture"], "lbl lbl-site", 10, 12, 0, "#fd0000")).add_to(field_group)
    
    province_group.add_to(m)
    district_group.add_to(m)
    field_group.add_to(m)
    restoration_group.add_to(m)
    thuloguthi_group.add_to(m)
    patrasi_group.add_to(m)

    GROUPS = {"provinces": province_group, "districts": district_group,
          "field": field_group, "restoration": restoration_group, "thuloguthi": thuloguthi_group, "patrasi":patrasi_group,
          "terrain": terrain, "satellite": satellite, "labels": labels, "rangeland":rangeland_overlay}
    # which layers are visible in each view
    VIEW_LAYERS = {
        "nat":         ["terrain", "labels", "rangeland",  "provinces"],
        "karnali":     ["terrain", "labels", "rangeland", "provinces", "districts"],
        "field":       ["terrain", "labels", "rangeland", "provinces", "districts", "field"],
        "restoration": ["satellite", "provinces", "districts", "restoration"],
        "thuloguthi": ["satellite", "provinces", "districts", "thuloguthi"],
        "patrasi": ["satellite", "provinces", "districts", "patrasi"]
    }

    m.add_child(ViewController(VIEWS, GROUPS, VIEW_LAYERS))
    m.get_root().html.add_child(Element("""
    <style>
        .leaflet-overlay-pane { mix-blend-mode: multiply; isolation: auto; }
        .leaflet-overlay-pane svg { mix-blend-mode: normal !important; }  /* keep boundaries crisp */
    </style>
    """))
    # m.add_image(image="images/rangeland_barplot.png", position=(0, 0))
    return m