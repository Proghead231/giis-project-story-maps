import json
import os
import folium
import geopandas as gpd
import leafmap.foliumap as leafmap
from branca.element import Element, MacroElement
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()

rangeland_color_map = ["#38ff1e", "#38ff1e"]
STADIA_API_KEY = os.getenv("STADIA_API_KEY")
provinces = gpd.read_file("data/province_bounds_json.geojson")
field_sites = gpd.read_file("data/eco_survey_sites_json.geojson")

VIEWS = {
    "nat":     {"lat": 28.165295,  "lon": 84.470657, "zoom": 7},
    "karnali": {"lat": 29.049975,  "lon": 82.151980, "zoom": 8},
    "field":   {"lat": 29.0674303, "lon": 82.6130036, "zoom": 10},
}


class ViewController(MacroElement):
    """Exposes window.goToView(name) inside the map iframe and toggles label visibility by zoom."""
    def __init__(self, views):
        super().__init__()
        self.views_json = json.dumps(views)
        self._template = Template("""
            {% macro script(this, kwargs) %}
            (function () {
                var map = {{ this._parent.get_name() }};
                var VIEWS = {{ this.views_json }};
                var el = map.getContainer();

                function syncLabels() {
                    var z = map.getZoom();
                    el.classList.toggle("show-prov", z <= 8);
                    el.classList.toggle("show-sites", z >= 9);
                }
                map.on("zoomend", syncLabels);

                window.goToView = function (name, animate) {
                    var v = VIEWS[name];
                    if (!v) return;
                    map.invalidateSize();
                    if (animate === false) {
                        map.setView([v.lat, v.lon], v.zoom);
                    } else {
                        map.flyTo([v.lat, v.lon], v.zoom, {duration: 1.6});
                    }
                };

                window.addEventListener("load", function () {
                    setTimeout(function () {
                        window.goToView("nat", false);
                        syncLabels();
                    }, 300);
                });
            })();
            {% endmacro %}
        """)


def _label(text, cls, anchor_y):
    return folium.DivIcon(
        icon_size=(0, 0),
        icon_anchor=(0, anchor_y),
        class_name=cls,
        html=f"""
            <div style="transform: translate(-50%, -100%); display: inline-block;
                font-size: 12pt; color: #000; white-space: nowrap; text-align: center;
                text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">
                {text}</div>""",
    )


def make_map():
    m = leafmap.Map(tiles=None)
    m.add_basemap("Stadia.StamenTerrain", api_key=STADIA_API_KEY)

    m.add_raster(
        "data/nepal_rangeland_image.tif",
        layer_name="Nepal Rangelands",
        vmin=1, vmax=1, nodata=0,
        colormap=rangeland_color_map,
        opacity=1.0,
        zoom_to_layer=False,
    )

    m.add_gdf(
        provinces,
        layer_name="Provinces",
        style={"color": "#ffffff", "weight": 2.5, "fillOpacity": 0.0, "dashArray": "5, 5"},
        zoom_to_layer=False,
        info_mode=None,
    )
    m.add_gdf(
        field_sites,
        layer_name="Field Survey Sites",
        style={"color": "#fd0000", "weight": 2.5, "fillOpacity": 0.0, "dashArray": "5, 5"},
        zoom_to_layer=False,
        info_mode=None,
    )

    for _, row in provinces.iterrows():
        pt = row.geometry.representative_point()
        folium.Marker([pt.y, pt.x], icon=_label(row["name_eng"], "lbl lbl-prov", -22)).add_to(m)

    for _, row in field_sites.iterrows():
        pt = row.geometry.representative_point()
        folium.Marker([pt.y, pt.x], icon=_label(row["pasture"], "lbl lbl-site", 36)).add_to(m)

    m.add_child(ViewController(VIEWS))

    m.get_root().html.add_child(Element("""
    <style>
      .leaflet-tile-pane .leaflet-layer:nth-child(2) { mix-blend-mode: multiply; }
      .lbl { display: none; }
      .show-prov  .lbl-prov { display: block; }
      .show-sites .lbl-site { display: block; }
    </style>
    """))

    # m.add_image(image="images/rangeland_barplot.png", position=(0, 0))
    return m