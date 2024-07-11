import streamlit as st
import folium
from folium import plugins
from pyproj import Transformer, CRS
from shapely.geometry import Point, LineString

# Function to create a transformer for coordinate conversion
def create_transformer(from_crs, to_crs):
    return Transformer.from_crs(from_crs, to_crs, always_xy=True)

# Function to convert coordinates
def convert_coordinates(x, y, transformer):
    lon, lat = transformer.transform(x, y)
    return lat, lon

# Function to calculate distance between point and tunnel line
def calculate_distance_to_tunnel(point, tunnel_line):
    return point.distance(tunnel_line)

# Function to plot tunnel and boreholes on the map
def plot_tunnel_and_boreholes(tunnel_start, tunnel_end, borehole_coords, transformer):
    start_lat, start_lon = convert_coordinates(*tunnel_start, transformer)
    end_lat, end_lon = convert_coordinates(*tunnel_end, transformer)

    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    plugins.MeasureControl(position='bottomleft', primary_length_unit='meters').add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite Imagery',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    folium.LayerControl().add_to(m)

    tunnel_line = LineString([tunnel_start, tunnel_end])

    folium.PolyLine(
        locations=[(start_lat, start_lon), (end_lat, end_lon)],
        color="blue",
        weight=3,
        opacity=0.8,
        popup="Tunnel Alignment"
    ).add_to(m)

    folium.Marker(
        [start_lat, start_lon],
        popup='Tunnel Start',
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)
    folium.Marker(
        [end_lat, end_lon],
        popup='Tunnel End',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    for i, (x, y) in enumerate(borehole_coords, 1):
        lat, lon = convert_coordinates(x, y, transformer)
        borehole_point = Point(x, y)
        distance_to_tunnel = calculate_distance_to_tunnel(borehole_point, tunnel_line)

        popup_content = f"""
        <b>Borehole {i}</b><br>
        UTM Coordinates:<br>
        X: {x:.2f}<br>
        Y: {y:.2f}<br>
        Lat/Lon Coordinates:<br>
        Lat: {lat:.6f}<br>
        Lon: {lon:.6f}<br>
        Distance to Tunnel: {distance_to_tunnel:.2f} m
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color='purple',
            fill=True,
            fillColor='purple',
            fillOpacity=0.8,
            popup=folium.Popup(popup_content, max_width=300)
        ).add_to(m)

        nearest_point = tunnel_line.interpolate(tunnel_line.project(borehole_point))
        nearest_lat, nearest_lon = convert_coordinates(nearest_point.x, nearest_point.y, transformer)
        folium.PolyLine(
            locations=[[lat, lon], [nearest_lat, nearest_lon]],
            color="red",
            weight=2,
            opacity=0.6,
            dash_array="5, 5",
            popup=f"Distance: {distance_to_tunnel:.2f} m"
        ).add_to(m)

    m.add_child(folium.LatLngPopup())
    return m

st.title("Tunnel and Borehole Visualization")

# Define coordinate systems
crs_options  = {
        "ETRS89 / UTM zone 32N": "epsg:25832",
        "WGS 84 / UTM zone 32N": "epsg:32632",
        "ETRS89 / UTM zone 33N": "epsg:25833",
        "WGS 84 / UTM zone 33N": "epsg:32633",
    }


# User input for coordinate systems
from_crs = st.selectbox("Select input coordinate system", list(crs_options.keys()))
to_crs = st.selectbox("Select output coordinate system", list(crs_options.keys()))

# Create the transformer
transformer = create_transformer(crs_options[from_crs], crs_options[to_crs])

# User input for tunnel coordinates
st.subheader("Tunnel Coordinates (UTM)")
tunnel_start_x = st.number_input("Tunnel Start X", value=506354.60)
tunnel_start_y = st.number_input("Tunnel Start Y", value=5883817.71)
tunnel_end_x = st.number_input("Tunnel End X", value=506475.24)
tunnel_end_y = st.number_input("Tunnel End Y", value=5885294.25)
tunnel_start = (tunnel_start_x, tunnel_start_y)
tunnel_end = (tunnel_end_x, tunnel_end_y)

# User input for borehole coordinates
st.subheader("Borehole Coordinates (UTM)")
num_boreholes = st.number_input("Number of boreholes", min_value=1, value=14)
borehole_coords = []
for i in range(num_boreholes):
    x = st.number_input(f"Borehole {i+1} X", value=506480.60 if i == 0 else 0.0)
    y = st.number_input(f"Borehole {i+1} Y", value=5885291.28 if i == 0 else 0.0)
    borehole_coords.append((x, y))

if st.button("Plot Map"):
    map = plot_tunnel_and_boreholes(tunnel_start, tunnel_end, borehole_coords, transformer)
    folium_static(map)
