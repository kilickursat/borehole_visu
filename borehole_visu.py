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

def plot_project(project_type, tunnel_coords, borehole_data, from_crs):
    if project_type == "Tunnel Boring":
        # Convert tunnel coordinates to lat/lon
        tunnel_latlon = [utm_to_latlon(x, y, from_crs) for x, y in tunnel_coords]
        
        # Create a map centered around the midpoint of the tunnel
        center_lat = sum(lat for lat, _ in tunnel_latlon) / len(tunnel_latlon)
        center_lon = sum(lon for _, lon in tunnel_latlon) / len(tunnel_latlon)
    else:  # Offshore Project
        # Create a map centered around the first borehole
        center_lat, center_lon = utm_to_latlon(borehole_data.iloc[0]['X'], borehole_data.iloc[0]['Y'], from_crs)

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
    
    if project_type == "Tunnel Boring":
        # Plot tunnel alignment
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
        X: {borehole['X']:.2f}<br>
        Y: {borehole['Y']:.2f}<br>
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
    st.title("Project Visualization App")

    # Project type selection
    project_type = st.radio("Select Project Type", ["Tunnel Boring", "Offshore Project"])

    # Coordinate system selection
    coordinate_systems = {
        "ETRS89 / UTM zone 32N": "epsg:25832",
        "WGS 84 / UTM zone 32N": "epsg:32632",
        "ETRS89 / UTM zone 33N": "epsg:25833",
        "WGS 84 / UTM zone 33N": "epsg:32633",
        "ITRF2014 UTM Zone 30N": "epsg:7927",
    }
    selected_crs = st.selectbox("Select Input Coordinate System", list(coordinate_systems.keys()))
    from_crs = coordinate_systems[selected_crs]

    tunnel_coords = []
    if project_type == "Tunnel Boring":
        # Tunnel coordinates
        st.subheader("Tunnel Coordinates")
        num_tunnel_points = st.number_input("Number of Tunnel Points", min_value=2, value=2, step=1)
        for i in range(num_tunnel_points):
            col1, col2 = st.columns(2)
            with col1:
                x = st.number_input(f"Tunnel Point {i+1} X", value=506354.60 + i*100)
            with col2:
                y = st.number_input(f"Tunnel Point {i+1} Y", value=5883817.71 + i*1000)
            tunnel_coords.append((x, y))

    # Borehole input
    st.subheader("Borehole Data")
    borehole_data = []
    num_boreholes = st.number_input("Number of Boreholes", min_value=1, value=3, step=1)
    
    for i in range(num_boreholes):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input(f"Borehole {i+1} Name", value=f"BH{i+1}")
        with col2:
            x = st.number_input(f"Borehole {i+1} X", value=506400.0 + i*10)
        with col3:
            y = st.number_input(f"Borehole {i+1} Y", value=5884000.0 + i*100)
        borehole_data.append({'Name': name, 'X': x, 'Y': y})
    
    borehole_df = pd.DataFrame(borehole_data)

    # Create map
    if st.button("Generate Map"):
        m = plot_project(project_type, tunnel_coords, borehole_df, from_crs)
        folium_static(m)

if __name__ == "__main__":
    main()
