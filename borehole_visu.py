import streamlit as st
import folium
from folium import plugins
from streamlit_folium import folium_static
from pyproj import Transformer, CRS
import pandas as pd

def utm_to_latlon(x, y, from_crs):
    transformer = Transformer.from_crs(from_crs, "epsg:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon

def plot_tunnel_and_boreholes(tunnel_coords, borehole_data, from_crs, project_type):
    # Convert tunnel coordinates to lat/lon if tunnel project is selected
    tunnel_latlon = [utm_to_latlon(x, y, from_crs) for x, y in tunnel_coords] if project_type == 'Tunnel Project' else []
    
    # Center map based on either tunnel or boreholes
    if tunnel_latlon:
        center_lat = sum(lat for lat, _ in tunnel_latlon) / len(tunnel_latlon)
        center_lon = sum(lon for _, lon in tunnel_latlon) / len(tunnel_latlon)
    else:
        borehole_latlon = [utm_to_latlon(row['X'], row['Y'], from_crs) for _, row in borehole_data.iterrows()]
        center_lat = sum(lat for lat, _ in borehole_latlon) / len(borehole_latlon)
        center_lon = sum(lon for _, lon in borehole_latlon) / len(borehole_latlon)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # Add MeasureControl for scale and distance measurement
    plugins.MeasureControl(position='bottomleft', primary_length_unit='meters').add_to(m)
    
    # Add satellite imagery layer
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite Imagery',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add OpenStreetMap layer for landmarks
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Plot tunnel alignment if it's a tunnel project
    if project_type == 'Tunnel Project':
        folium.PolyLine(
            locations=tunnel_latlon,
            color="blue",
            weight=3,
            opacity=0.8,
            popup="Tunnel Alignment"
        ).add_to(m)

        # Add tunnel start and end markers
        folium.Marker(
            tunnel_latlon[0],
            popup='Tunnel Start',
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
        folium.Marker(
            tunnel_latlon[-1],
            popup='Tunnel End',
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    # Plot boreholes
    for _, borehole in borehole_data.iterrows():
        lat, lon = utm_to_latlon(borehole['X'], borehole['Y'], from_crs)
        popup_content = f"""
        <b>{borehole['Name']}</b><br>
        Input Coordinates:<br>
        Northing: {borehole['X']:.2f}<br>
        Easting: {borehole['Y']:.2f}<br>
        Lat/Lon Coordinates:<br>
        Lat: {lat:.6f}<br>
        Lon: {lon:.6f}
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

    # Add click event to show coordinates
    m.add_child(folium.LatLngPopup())

    return m

def main():
    st.title("Tunnel and Borehole Visualization App")

    # Project type selection
    project_type = st.radio("Select Project Type", ['Tunnel Project', 'Offshore Drilling Project'])

    # Coordinate system selection
    coordinate_systems = {
        "ETRS89 / UTM zone 32N": "epsg:25832",
        "WGS 84 / UTM zone 32N": "epsg:32632",
        "ETRS89 / UTM zone 33N": "epsg:25833",
        "WGS 84 / UTM zone 33N": "epsg:32633",
        "ITRF2014 / UTM zone 30N": "epsg:7912"  # Added new coordinate system
    }
    selected_crs = st.selectbox("Select Input Coordinate System", list(coordinate_systems.keys()))
    from_crs = coordinate_systems[selected_crs]

    # Tunnel coordinates (only relevant for Tunnel Projects)
    if project_type == 'Tunnel Project':
        st.subheader("Tunnel Coordinates")
        num_tunnel_points = st.number_input("Number of Tunnel Points", min_value=2, value=2, step=1)
        tunnel_coords = []
        for i in range(num_tunnel_points):
            col1, col2 = st.columns(2)
            with col1:
                x = st.number_input(f"Tunnel Point {i+1} Northing", value=506354.60 + i*100)
            with col2:
                y = st.number_input(f"Tunnel Point {i+1} Easting", value=5883817.71 + i*1000)
            tunnel_coords.append((x, y))
    else:
        tunnel_coords = []  # No tunnel coordinates for offshore projects

    # Borehole input
    st.subheader("Borehole Data")
    borehole_data = []
    num_boreholes = st.number_input("Number of Boreholes", min_value=1, value=3, step=1)
    
    for i in range(num_boreholes):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input(f"Borehole {i+1} Name", value=f"BH{i+1}")
        with col2:
            x = st.number_input(f"Borehole {i+1} Northing", value=506400.0 + i*10)
        with col3:
            y = st.number_input(f"Borehole {i+1} Easting", value=5884000.0 + i*100)
        borehole_data.append({'Name': name, 'X': x, 'Y': y})
    
    borehole_df = pd.DataFrame(borehole_data)

    # Create map
    if st.button("Generate Map"):
        m = plot_tunnel_and_boreholes(tunnel_coords, borehole_df, from_crs, project_type)
        folium_static(m)

if __name__ == "__main__":
    main()
