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
from scipy.interpolate import griddata

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
    #Cross sectional profile
def create_geological_cross_section(borehole_data, tunnel_coords):
    import numpy as np
    from scipy.interpolate import griddata
    
    # Function to calculate distance along section
    def calculate_distance(x1, y1, x2, y2):
        return np.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    # Project boreholes onto section line
    def project_point_to_line(px, py, x1, y1, x2, y2):
        # Vector from line start to point
        ax = px - x1
        ay = py - y1
        # Vector from line start to line end
        bx = x2 - x1
        by = y2 - y1
        # Length of line
        b_len = np.sqrt(bx*bx + by*by)
        # Normalized line vector
        bx /= b_len
        by /= b_len
        # Projection length
        proj_len = ax*bx + ay*by
        # Projected point
        proj_x = x1 + bx*proj_len
        proj_y = y1 + by*proj_len
        # Distance along line
        distance = proj_len
        return distance, proj_x, proj_y

    # Create figure
    fig = go.Figure()
    
    # Get section line endpoints from tunnel coordinates
    start_x, start_y = tunnel_coords[0]
    end_x, end_y = tunnel_coords[-1]
    section_length = calculate_distance(start_x, start_y, end_x, end_y)
    
    # Project boreholes and create interpolation points
    distances = []
    depths = []
    soil_types = []
    
    for _, bh in borehole_data.iterrows():
        distance, _, _ = project_point_to_line(bh['X'], bh['Y'], start_x, start_y, end_x, end_y)
        
        # Add each layer from the borehole
        for layer in bh['layers']:  # You'll need to add layer data to your boreholes
            depths.append(layer['depth'])
            distances.append(distance)
            soil_types.append(layer['soil_type'])
    
    # Create interpolation grid
    xi = np.linspace(0, section_length, 100)
    yi = np.linspace(min(depths), max(depths), 100)
    xi, yi = np.meshgrid(xi, yi)
    
    # Interpolate soil types
    # Convert soil types to numerical values for interpolation
    unique_soils = list(set(soil_types))
    soil_values = [unique_soils.index(s) for s in soil_types]
    
    zi = griddata((distances, depths), soil_values, (xi, yi), method='linear')
    
    # Create color scale for soil types
    colors = {
        'CLAY': '#C4A484',
        'SAND': '#F4D03F',
        'ROCK': '#808080',
        'SOIL': '#8B4513',
        'SILT': '#D2B48C',
        'GRAVEL': '#A0522D'
    }
    
    # Plot interpolated geology
    for i, soil in enumerate(unique_soils):
        mask = (zi == i)
        if np.any(mask):
            fig.add_trace(go.Contour(
                x=xi[0],
                y=yi[:,0],
                z=mask*1.0,
                contours_coloring='fill',
                showscale=False,
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, colors.get(soil, '#000000')]],
                name=soil,
                showlegend=True
            ))
    
    # Add boreholes as vertical lines
    for _, bh in borehole_data.iterrows():
        distance, _, _ = project_point_to_line(bh['X'], bh['Y'], start_x, start_y, end_x, end_y)
        fig.add_trace(go.Scatter(
            x=[distance, distance],
            y=[0, max(depths)],
            mode='lines',
            line=dict(color='black', width=2),
            name=f'BH-{bh["Name"]}',
            showlegend=True
        ))
    
    # Add tunnel alignment
    tunnel_distances = []
    tunnel_elevations = []
    for x, y in tunnel_coords:
        distance, _, _ = project_point_to_line(x, y, start_x, start_y, end_x, end_y)
        tunnel_distances.append(distance)
        tunnel_elevations.append(-8)  # Replace with actual tunnel elevation
    
    fig.add_trace(go.Scatter(
        x=tunnel_distances,
        y=tunnel_elevations,
        mode='lines',
        line=dict(color='red', width=3),
        name='Tunnel Alignment'
    ))
    
    # Update layout
    fig.update_layout(
        title='Geological Cross Section',
        xaxis_title='Distance Along Section (m)',
        yaxis_title='Elevation (m)',
        yaxis_autorange='reversed',
        showlegend=True,
        height=600
    )
    
    return fig

# Add to main():
def add_layer_data():
    layers = []
    num_layers = st.number_input("Number of layers", min_value=1, value=3)
    for i in range(num_layers):
        col1, col2 = st.columns(2)
        with col1:
            depth = st.number_input(f"Layer {i+1} depth", value=i*5.0)
        with col2:
            soil_type = st.selectbox(f"Layer {i+1} soil type", 
                                   ['CLAY', 'SAND', 'ROCK', 'SOIL', 'SILT', 'GRAVEL'])
        layers.append({'depth': depth, 'soil_type': soil_type})
    return layers
    
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

    # Tunnel coordinates input
    if project_type == 'Tunnel Project':
        st.subheader("Tunnel Coordinates")
        num_points = st.number_input("Number of Tunnel Points", min_value=2, value=2)
        tunnel_coords = []
        for i in range(num_points):
            col1, col2 = st.columns(2)
            with col1:
                x = st.number_input(f"Point {i+1} Northing", value=float(506354.60 + i*100))
            with col2:
                y = st.number_input(f"Point {i+1} Easting", value=float(5883817.71 + i*100))
            tunnel_coords.append((x, y))
    else:
        tunnel_coords = []

    # Borehole data input
    st.subheader("Borehole Data")
    num_boreholes = st.number_input("Number of Boreholes", min_value=1, value=2)
    borehole_data = []
    
    for i in range(num_boreholes):
        st.markdown(f"### Borehole {i+1}")
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input(f"Name", value=f"BH{i+1}", key=f"bh_name_{i}")
        with col2:
            x = st.number_input(f"Northing", value=506400.0 + i*50, key=f"bh_x_{i}")
        with col3:
            y = st.number_input(f"Easting", value=5884000.0 + i*50, key=f"bh_y_{i}")
        
        # Lithology layers
        num_layers = st.number_input(f"Number of layers", min_value=1, value=3, key=f"num_layers_{i}")
        layers = []
        
        for j in range(num_layers):
            col1, col2, col3 = st.columns(3)
            with col1:
                soil_type = st.selectbox(
                    "Soil Type",
                    ['CLAY', 'SAND', 'ROCK', 'SOIL', 'SILT', 'GRAVEL'],
                    key=f"soil_{i}_{j}"
                )
            with col2:
                depth = st.number_input("Depth (m)", value=float(j*3), key=f"depth_{i}_{j}")
            with col3:
                thickness = st.number_input("Thickness (m)", value=3.0, key=f"thickness_{i}_{j}")
            
            layers.append({
                'soil_type': soil_type,
                'depth': depth,
                'thickness': thickness
            })
        
        borehole_data.append({
            'Name': name,
            'X': x,
            'Y': y,
            'layers': layers
        })

    borehole_df = pd.DataFrame(borehole_data)

    if st.button("Generate Cross Section"):
        fig = create_geological_cross_section(borehole_df, tunnel_coords)
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
