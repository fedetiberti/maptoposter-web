"""
Poster generation wrapper that integrates with the original maptoposter script.
"""
import os
import sys
import json
import ssl
import certifi
import urllib3
import requests
from datetime import datetime
from typing import Optional, Tuple

# Check if SSL verification should be disabled (for development with corporate proxies)
DISABLE_SSL_VERIFY = os.getenv("DISABLE_SSL_VERIFY", "false").lower() == "true"

if DISABLE_SSL_VERIFY:
    # Disable SSL verification warnings for development (corporate proxy issue)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Monkey-patch requests to disable SSL verification globally (development only)
    # This is needed because corporate proxy intercepts HTTPS with self-signed cert
    _original_request = requests.Session.request
    def _patched_request(self, *args, **kwargs):
        kwargs['verify'] = False
        return _original_request(self, *args, **kwargs)
    requests.Session.request = _patched_request

from core.config import settings
from core.jobs import Job, JobStatus, update_job

# Add the core directory to path so we can import the original script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the original maptoposter script
import osmnx as ox
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
import geopy.geocoders
import time
from shapely.geometry import Point

# SSL context configuration
if DISABLE_SSL_VERIFY:
    # Create unverified SSL context for development (corporate proxy with self-signed cert)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # Configure geopy to skip SSL verification
    geopy.geocoders.options.default_ssl_context = ssl_context
    # Configure OSMnx to skip SSL verification
    ox.settings.requests_kwargs = {"verify": False}
else:
    # Production: use proper SSL verification with certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    geopy.geocoders.options.default_ssl_context = ssl_context


def load_theme(theme_name: str) -> dict:
    """Load a theme from the themes directory."""
    theme_file = os.path.join(settings.themes_dir, f"{theme_name}.json")

    if not os.path.exists(theme_file):
        # Fallback to default theme
        return {
            "name": "Feature-Based Shading",
            "bg": "#FFFFFF",
            "text": "#000000",
            "gradient_color": "#FFFFFF",
            "water": "#C0C0C0",
            "parks": "#F0F0F0",
            "road_motorway": "#0A0A0A",
            "road_primary": "#1A1A1A",
            "road_secondary": "#2A2A2A",
            "road_tertiary": "#3A3A3A",
            "road_residential": "#4A4A4A",
            "road_default": "#3A3A3A"
        }

    with open(theme_file, 'r') as f:
        return json.load(f)


def get_all_themes() -> list:
    """Get all available themes with their metadata."""
    themes = []

    if not os.path.exists(settings.themes_dir):
        return themes

    for filename in sorted(os.listdir(settings.themes_dir)):
        if filename.endswith('.json'):
            theme_id = filename[:-5]
            theme_path = os.path.join(settings.themes_dir, filename)

            try:
                with open(theme_path, 'r') as f:
                    theme_data = json.load(f)
                    themes.append({
                        "id": theme_id,
                        "name": theme_data.get("name", theme_id),
                        "description": theme_data.get("description", ""),
                        "colors": {
                            "bg": theme_data.get("bg", "#FFFFFF"),
                            "text": theme_data.get("text", "#000000"),
                            "road_primary": theme_data.get("road_primary", "#1A1A1A"),
                            "water": theme_data.get("water", "#C0C0C0"),
                            "parks": theme_data.get("parks", "#F0F0F0"),
                        }
                    })
            except (json.JSONDecodeError, IOError):
                continue

    return themes


def get_coordinates(city: str, country: str) -> Tuple[float, float]:
    """Get coordinates for a city using Nominatim geocoding."""
    # Pass SSL context directly to Nominatim to bypass corporate proxy SSL issues
    geolocator = Nominatim(
        user_agent="maptoposter-web",
        timeout=10,
        ssl_context=ssl_context
    )
    time.sleep(1)  # Rate limiting

    location = geolocator.geocode(f"{city}, {country}")

    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")


def load_fonts() -> Optional[dict]:
    """Load Roboto fonts if available."""
    fonts = {
        'bold': os.path.join(settings.fonts_dir, 'Roboto-Bold.ttf'),
        'regular': os.path.join(settings.fonts_dir, 'Roboto-Regular.ttf'),
        'light': os.path.join(settings.fonts_dir, 'Roboto-Light.ttf')
    }

    for weight, path in fonts.items():
        if not os.path.exists(path):
            return None

    return fonts


def create_gradient_fade(ax, color, location='bottom', zorder=10):
    """Creates a fade effect at the top or bottom of the map."""
    vals = np.linspace(0, 1, 256).reshape(-1, 1)
    gradient = np.hstack((vals, vals))

    rgb = mcolors.to_rgb(color)
    my_colors = np.zeros((256, 4))
    my_colors[:, 0] = rgb[0]
    my_colors[:, 1] = rgb[1]
    my_colors[:, 2] = rgb[2]

    if location == 'bottom':
        my_colors[:, 3] = np.linspace(1, 0, 256)
        extent_y_start = 0
        extent_y_end = 0.25
    else:
        my_colors[:, 3] = np.linspace(0, 1, 256)
        extent_y_start = 0.75
        extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(my_colors)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end

    ax.imshow(gradient, extent=[xlim[0], xlim[1], y_bottom, y_top],
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')


def get_edge_colors_by_type(G, theme):
    """Assigns colors to edges based on road type hierarchy."""
    edge_colors = []

    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        if highway in ['motorway', 'motorway_link']:
            color = theme['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = theme['road_primary']
        elif highway in ['secondary', 'secondary_link']:
            color = theme['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']:
            color = theme['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = theme['road_residential']
        else:
            color = theme['road_default']

        edge_colors.append(color)

    return edge_colors


def get_edge_widths_by_type(G):
    """Assigns line widths to edges based on road type."""
    edge_widths = []

    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        if highway in ['motorway', 'motorway_link']:
            width = 1.2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            width = 1.0
        elif highway in ['secondary', 'secondary_link']:
            width = 0.8
        elif highway in ['tertiary', 'tertiary_link']:
            width = 0.6
        else:
            width = 0.4

        edge_widths.append(width)

    return edge_widths


def get_crop_limits(G_proj, center_lat_lon, fig, dist):
    """Crop inward to preserve aspect ratio."""
    lat, lon = center_lat_lon

    center = (
        ox.projection.project_geometry(
            Point(lon, lat),
            crs="EPSG:4326",
            to_crs=G_proj.graph["crs"]
        )[0]
    )
    center_x, center_y = center.x, center.y

    fig_width, fig_height = fig.get_size_inches()
    aspect = fig_width / fig_height

    half_x = dist
    half_y = dist

    if aspect > 1:
        half_y = half_x / aspect
    else:
        half_x = half_y * aspect

    return (
        (center_x - half_x, center_x + half_x),
        (center_y - half_y, center_y + half_y),
    )


def generate_poster(
    job: Job,
    city: str,
    country: str,
    theme_name: str,
    distance: int = 15000,
    width: float = 12,
    height: float = 16,
    output_format: str = "png",
    city_label: Optional[str] = None,
    country_label: Optional[str] = None,
    is_preview: bool = False,
) -> str:
    """
    Generate a map poster and return the output file path.

    For preview mode, uses smaller dimensions and lower DPI.
    """
    try:
        # Update job status
        update_job(job.id, status=JobStatus.PROCESSING, progress=10)

        # Load theme
        theme = load_theme(theme_name)

        # Preview settings: smaller dimensions, lower DPI
        if is_preview:
            width = 3.6
            height = 4.8
            dpi = 72
        else:
            dpi = 300

        # Get coordinates
        update_job(job.id, progress=20)
        point = get_coordinates(city, country)
        lat, lon = point

        # Fetch street network
        update_job(job.id, progress=30)
        compensated_dist = distance * (max(height, width) / min(height, width)) / 4

        try:
            G = ox.graph_from_point(point, dist=compensated_dist, dist_type='bbox',
                                    network_type='all', truncate_by_edge=True)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch street network: {e}")

        # Fetch water features
        update_job(job.id, progress=50)
        try:
            water = ox.features_from_point(point, tags={'natural': 'water', 'waterway': 'riverbank'},
                                           dist=compensated_dist)
        except:
            water = None

        # Fetch parks
        update_job(job.id, progress=60)
        try:
            parks = ox.features_from_point(point, tags={'leisure': 'park', 'landuse': 'grass'},
                                           dist=compensated_dist)
        except:
            parks = None

        # Setup plot
        update_job(job.id, progress=70)
        fig, ax = plt.subplots(figsize=(width, height), facecolor=theme['bg'])
        ax.set_facecolor(theme['bg'])
        ax.set_position((0.0, 0.0, 1.0, 1.0))

        # Project graph
        G_proj = ox.project_graph(G)

        # Plot water
        if water is not None and not water.empty:
            water_polys = water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            if not water_polys.empty:
                try:
                    water_polys = ox.projection.project_gdf(water_polys)
                except:
                    water_polys = water_polys.to_crs(G_proj.graph['crs'])
                water_polys.plot(ax=ax, facecolor=theme['water'], edgecolor='none', zorder=1)

        # Plot parks
        if parks is not None and not parks.empty:
            parks_polys = parks[parks.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            if not parks_polys.empty:
                try:
                    parks_polys = ox.projection.project_gdf(parks_polys)
                except:
                    parks_polys = parks_polys.to_crs(G_proj.graph['crs'])
                parks_polys.plot(ax=ax, facecolor=theme['parks'], edgecolor='none', zorder=2)

        # Plot roads
        update_job(job.id, progress=80)
        edge_colors = get_edge_colors_by_type(G_proj, theme)
        edge_widths = get_edge_widths_by_type(G_proj)

        crop_xlim, crop_ylim = get_crop_limits(G_proj, point, fig, compensated_dist)

        ox.plot_graph(
            G_proj, ax=ax, bgcolor=theme['bg'],
            node_size=0,
            edge_color=edge_colors,
            edge_linewidth=edge_widths,
            show=False, close=False
        )
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(crop_xlim)
        ax.set_ylim(crop_ylim)

        # Add gradient fades
        create_gradient_fade(ax, theme['gradient_color'], location='bottom', zorder=10)
        create_gradient_fade(ax, theme['gradient_color'], location='top', zorder=10)

        # Typography
        update_job(job.id, progress=90)
        fonts = load_fonts()
        scale_factor = width / 12.0

        BASE_MAIN = 60
        BASE_SUB = 22
        BASE_COORDS = 14
        BASE_ATTR = 8

        if fonts:
            font_main = FontProperties(fname=fonts['bold'], size=BASE_MAIN * scale_factor)
            font_sub = FontProperties(fname=fonts['light'], size=BASE_SUB * scale_factor)
            font_coords = FontProperties(fname=fonts['regular'], size=BASE_COORDS * scale_factor)
            font_attr = FontProperties(fname=fonts['light'], size=BASE_ATTR * scale_factor)
        else:
            font_main = FontProperties(family='monospace', weight='bold', size=BASE_MAIN * scale_factor)
            font_sub = FontProperties(family='monospace', weight='normal', size=BASE_SUB * scale_factor)
            font_coords = FontProperties(family='monospace', size=BASE_COORDS * scale_factor)
            font_attr = FontProperties(family='monospace', size=BASE_ATTR * scale_factor)

        display_city = city_label if city_label else city
        display_country = country_label if country_label else country

        spaced_city = "  ".join(list(display_city.upper()))

        # Adjust font size for long city names
        city_char_count = len(display_city)
        if city_char_count > 10:
            length_factor = 10 / city_char_count
            adjusted_font_size = max(BASE_MAIN * scale_factor * length_factor, 10 * scale_factor)
            if fonts:
                font_main = FontProperties(fname=fonts['bold'], size=adjusted_font_size)
            else:
                font_main = FontProperties(family='monospace', weight='bold', size=adjusted_font_size)

        # Add text
        ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
                color=theme['text'], ha='center', fontproperties=font_main, zorder=11)

        ax.text(0.5, 0.10, display_country.upper(), transform=ax.transAxes,
                color=theme['text'], ha='center', fontproperties=font_sub, zorder=11)

        coords_text = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
        if lon < 0:
            coords_text = coords_text.replace("E", "W")

        ax.text(0.5, 0.07, coords_text, transform=ax.transAxes,
                color=theme['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)

        ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes,
                color=theme['text'], linewidth=1 * scale_factor, zorder=11)

        ax.text(0.98, 0.02, "© OpenStreetMap contributors", transform=ax.transAxes,
                color=theme['text'], alpha=0.5, ha='right', va='bottom',
                fontproperties=font_attr, zorder=11)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        city_slug = city.lower().replace(' ', '_')
        preview_suffix = "_preview" if is_preview else ""
        filename = f"{city_slug}_{theme_name}{preview_suffix}_{timestamp}.{output_format}"
        output_path = os.path.join(settings.output_dir, filename)

        save_kwargs = dict(facecolor=theme["bg"], bbox_inches="tight", pad_inches=0.05)
        if output_format == "png":
            save_kwargs["dpi"] = dpi

        plt.savefig(output_path, format=output_format, **save_kwargs)
        plt.close()

        # Update job as complete
        update_job(job.id, status=JobStatus.COMPLETE, progress=100, result_path=output_path)

        return output_path

    except Exception as e:
        update_job(job.id, status=JobStatus.ERROR, error=str(e))
        raise
