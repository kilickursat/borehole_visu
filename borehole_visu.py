import streamlit as st
import folium
from folium import plugins
from streamlit_folium import folium_static
from pyproj import Transformer, CRS
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np

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
def plot_tunnel_cross_section(borehole_data, tunnel_coords):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Calculate distances between boreholes
    distances = []
    for i in range(len(borehole_data)):
        if i == 0:
            distances.append(0)
        else:
            dx = borehole_data.iloc[i]['X'] - borehole_data.iloc[0]['X']
            dy = borehole_data.iloc[i]['Y'] - borehole_data.iloc[0]['Y']
            distances.append(np.sqrt(dx**2 + dy**2))
    
    # Add lithology data for each borehole
    colors = {
        'CLAY': 'brown',
        'SAND': 'yellow',
        'ROCK': 'gray',
        'SOIL': 'darkgreen'
    }
    
    for i, distance in enumerate(distances):
        bh = borehole_data.iloc[i]
        
        # Example lithology data - replace with actual data input
        lithologies = [
            {'depth': 0, 'type': 'SOIL', 'thickness': 2},
            {'depth': 2, 'type': 'CLAY', 'thickness': 5},
            {'depth': 7, 'type': 'SAND', 'thickness': 3},
            {'depth': 10, 'type': 'ROCK', 'thickness': 5}
        ]
        
        for layer in lithologies:
            fig.add_trace(
                go.Bar(
                    name=layer['type'],
                    x=[[distance, distance]],
                    y=[[layer['depth'], layer['depth'] + layer['thickness']]],
                    orientation='h',
                    marker=dict(color=colors[layer['type']]),
                    showlegend=i==0,
                    width=5
                )
            )
    
    # Add tunnel alignment
    tunnel_distances = []
    tunnel_elevations = []
    for i in range(len(tunnel_coords)):
        if i == 0:
            tunnel_distances.append(0)
        else:
            dx = tunnel_coords[i][0] - tunnel_coords[0][0]
            dy = tunnel_coords[i][1] - tunnel_coords[0][1]
            tunnel_distances.append(np.sqrt(dx**2 + dy**2))
        # Example tunnel elevation - replace with actual data
        tunnel_elevations.append(-8)  
    
    fig.add_trace(
        go.Scatter(
            x=tunnel_distances,
            y=tunnel_elevations,
            mode='lines',
            name='Tunnel Alignment',
            line=dict(color='red', width=3)
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Tunnel Cross Section with Lithology',
        xaxis_title='Distance (m)',
        yaxis_title='Depth (m)',
        barmode='overlay',
        showlegend=True
    )
    
    # Invert y-axis to show depth increasing downwards
    fig.update_yaxes(autorange="reversed")
    
    return fig
def main():
    st.title("Tunnel and Borehole Visualization App")

    # Project type selection
    project_type = st.radio("Select Project Type", ['Tunnel Project', 'Offshore Drilling Project'])

    # Extended coordinate system selection
    coordinate_systems = {
        # Original European systems
        "ETRS89 / UTM zone 32N": "epsg:25832",
        "WGS 84 / UTM zone 32N": "epsg:32632",
        "ETRS89 / UTM zone 33N": "epsg:25833",
        "WGS 84 / UTM zone 33N": "epsg:32633",
        
        # Indonesian Coordinate Systems (DGN95/ED50)
        "DGN95 / UTM zone 46N": "epsg:23846",
        "DGN95 / UTM zone 47N": "epsg:23847",
        "DGN95 / UTM zone 48N": "epsg:23848",
        "DGN95 / UTM zone 49N": "epsg:23849",
        "DGN95 / UTM zone 50N": "epsg:23850",
        "DGN95 / UTM zone 51N": "epsg:23851",
        "DGN95 / UTM zone 52N": "epsg:23852",
        "DGN95 / UTM zone 53N": "epsg:23853",
        "DGN95 / UTM zone 54N": "epsg:23854",
        
        # ID74 / UTM zones (Indonesian Datum 1974)
        "ID74 / UTM zone 46N": "epsg:23866",
        "ID74 / UTM zone 47N": "epsg:23867",
        "ID74 / UTM zone 48N": "epsg:23868",
        "ID74 / UTM zone 49N": "epsg:23869",
        "ID74 / UTM zone 50N": "epsg:23870",
        "ID74 / UTM zone 51N": "epsg:23871",
        "ID74 / UTM zone 52N": "epsg:23872",
        "ID74 / UTM zone 53N": "epsg:23873",
        "ID74 / UTM zone 54N": "epsg:23874",
        
        # ITRF Systems
        "ITRF2014 / UTM zone 30N": "epsg:7912",
        "ITRF2014 / UTM zone 31N": "epsg:7913",
        "ITRF2014 / UTM zone 32N": "epsg:7914",
        "ITRF2014 / UTM zone 33N": "epsg:7915",
        "ITRF2014 / UTM zone 34N": "epsg:7916",
        "ITRF2014 / UTM zone 35N": "epsg:7917",
        
        # ITRF2008 Systems
        "ITRF2008 / UTM zone 30N": "epsg:5330",
        "ITRF2008 / UTM zone 31N": "epsg:5331",
        "ITRF2008 / UTM zone 32N": "epsg:5332",
        "ITRF2008 / UTM zone 33N": "epsg:5333",
        "ITRF2008 / UTM zone 34N": "epsg:5334",
        "ITRF2008 / UTM zone 35N": "epsg:5335",
        
        # Additional ED50 Systems (European Datum 1950)
        "ED50 / UTM zone 28N": "epsg:23028",
        "ED50 / UTM zone 29N": "epsg:23029",
        "ED50 / UTM zone 30N": "epsg:23030",
        "ED50 / UTM zone 31N": "epsg:23031",
        "ED50 / UTM zone 32N": "epsg:23032",
        "ED50 / UTM zone 33N": "epsg:23033",
        "ED50 / UTM zone 34N": "epsg:23034",
        "ED50 / UTM zone 35N": "epsg:23035",
        "ED50 / UTM zone 36N": "epsg:23036",
        "ED50 / UTM zone 37N": "epsg:23037",
        "ED50 / UTM zone 38N": "epsg:23038"
    }

    # Group coordinate systems by category for better organization
    coordinate_system_groups = {
        "European Systems": [k for k in coordinate_systems.keys() if k.startswith(("ETRS89", "WGS 84"))],
        "Indonesian Systems (DGN95)": [k for k in coordinate_systems.keys() if k.startswith("DGN95")],
        "Indonesian Systems (ID74)": [k for k in coordinate_systems.keys() if k.startswith("ID74")],
        "ITRF Systems": [k for k in coordinate_systems.keys() if k.startswith("ITRF")],
        "ED50 Systems": [k for k in coordinate_systems.keys() if k.startswith("ED50")]
    }

    # Create a two-step selection process
    selected_group = st.selectbox("Select Coordinate System Group", list(coordinate_system_groups.keys()))
    selected_crs = st.selectbox(
        "Select Specific Coordinate System", 
        coordinate_system_groups[selected_group]
    )
    from_crs = coordinate_systems[selected_crs]

    # Rest of the main() function remains the same
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
        tunnel_coords = []

    # Borehole input section remains the same
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

    # Cross-sectional map:
    if st.button("Generate Cross Section"):
        cross_section = plot_tunnel_cross_section(borehole_df, tunnel_coords)
        st.plotly_chart(cross_section)

if __name__ == "__main__":
    main()
