import streamlit as st
import folium
from folium import plugins
from streamlit_folium import folium_static
from pyproj import Transformer, CRS
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

def utm_to_latlon(x, y, from_crs):
    transformer = Transformer.from_crs(from_crs, "epsg:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon
def create_custom_geological_profile(layers):
    """Create a geological profile visualization with custom colors and patterns"""
    fig = go.Figure()
    
    # Add layers from bottom to top
    bottom = 0
    
    for layer in reversed(layers):
        thickness = layer['thickness']
        custom_description = layer['description']
        color = layer['color']  # User-defined color
        
        # Add layer rectangle
        fig.add_trace(go.Scatter(
            x=[0, 1, 1, 0, 0],
            y=[bottom, bottom, bottom + thickness, bottom + thickness, bottom],
            fill="toself",
            fillcolor=color,
            line=dict(color='black'),
            name=custom_description,
            hoverinfo='text',
            text=f"Layer Description: {custom_description}<br>Thickness: {thickness}m"
        ))
        
        # Add text annotation for detailed description
        fig.add_annotation(
            x=0.5,
            y=bottom + thickness/2,
            text=custom_description,
            showarrow=False,
            font=dict(size=10),
            xanchor='center'
        )
        
        bottom += thickness
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        xaxis_title="Width",
        yaxis_title="Depth (m)",
        yaxis_autorange='reversed',
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig
    
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
    
    # Add measurement control and layers (previous code remains the same)
    
    # Plot boreholes with custom geological information
    for _, borehole in borehole_data.iterrows():
        lat, lon = utm_to_latlon(borehole['X'], borehole['Y'], from_crs)
        
        # Create detailed popup content with custom geological information
        popup_content = f"""
        <b>{borehole['Name']}</b><br>
        <b>Location:</b><br>
        Northing: {borehole['X']:.2f}<br>
        Easting: {borehole['Y']:.2f}<br>
        Lat/Lon: {lat:.6f}, {lon:.6f}<br>
        <b>Geological Profile:</b><br>
        """
        
        # Add custom geological layers information
        if 'layers' in borehole:
            for i, layer in enumerate(borehole['layers'], 1):
                popup_content += f"""
                Layer {i}:<br>
                - Description: {layer['description']}<br>
                - Thickness: {layer['thickness']}m<br>
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
    
    return m

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

    selected_crs = st.selectbox("Select Input Coordinate System", list(coordinate_systems.keys()))
    from_crs = coordinate_systems[selected_crs]

    # Add a section for custom legend creation
    st.subheader("Custom Geological Legend")
    st.markdown("Define your custom geological descriptions and colors")
    
    # Initialize session state for legend items if not exists
    if 'legend_items' not in st.session_state:
        st.session_state.legend_items = []

    # Add new legend item
    with st.expander("Add New Legend Item"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_description = st.text_input("Description", key="new_legend_desc")
        with col2:
            new_color = st.color_picker("Color", key="new_legend_color")
        with col3:
            if st.button("Add to Legend"):
                st.session_state.legend_items.append({
                    'description': new_description,
                    'color': new_color
                })

    # Display and edit existing legend items
    if st.session_state.legend_items:
        st.markdown("### Current Legend Items")
        for idx, item in enumerate(st.session_state.legend_items):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.text(item['description'])
            with col2:
                st.color_picker("", item['color'], key=f"color_{idx}", disabled=True)
            with col3:
                if st.button("Remove", key=f"remove_{idx}"):
                    st.session_state.legend_items.pop(idx)
                    st.experimental_rerun()

    # Tunnel coordinates section
    tunnel_coords = []
    if project_type == 'Tunnel Project':
        st.subheader("Tunnel Coordinates")
        num_tunnel_points = st.number_input("Number of Tunnel Points", min_value=2, value=2, step=1)
        
        for i in range(num_tunnel_points):
            col1, col2 = st.columns(2)
            with col1:
                x = st.number_input(f"Tunnel Point {i+1} Northing", value=506354.60 + i*100)
            with col2:
                y = st.number_input(f"Tunnel Point {i+1} Easting", value=5883817.71 + i*1000)
            tunnel_coords.append((x, y))

    # Borehole data section
    st.subheader("Borehole Data")
    num_boreholes = st.number_input("Number of Boreholes", min_value=1, value=3, step=1)
    
    borehole_data = []
    for i in range(num_boreholes):
        st.markdown(f"### Borehole {i+1}")
        
        # Basic borehole information
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input(f"Borehole Name", value=f"BH{i+1}", key=f"name_{i}")
        with col2:
            x = st.number_input(f"Northing", value=506400.0 + i*10, key=f"x_{i}")
        with col3:
            y = st.number_input(f"Easting", value=5884000.0 + i*100, key=f"y_{i}")
        
        # Custom geological layers input
        st.markdown(f"#### Geological Layers for {name}")
        num_layers = st.number_input(f"Number of Layers", min_value=1, value=3, key=f"layers_{i}")
        
        layers = []
        for j in range(num_layers):
            st.markdown(f"##### Layer {j+1}")
            col1, col2 = st.columns(2)
            
            with col1:
                # Free-form text input for layer description
                description = st.text_area(
                    "Layer Description",
                    value="Enter detailed geological description",
                    key=f"desc_{i}_{j}",
                    height=100
                )
                
                # Option to use legend item or custom color
                use_legend = st.checkbox("Use Legend Item", key=f"use_legend_{i}_{j}")
                if use_legend and st.session_state.legend_items:
                    legend_desc = [item['description'] for item in st.session_state.legend_items]
                    selected_idx = st.selectbox(
                        "Select Legend Item",
                        range(len(legend_desc)),
                        format_func=lambda x: legend_desc[x],
                        key=f"legend_select_{i}_{j}"
                    )
                    color = st.session_state.legend_items[selected_idx]['color']
                else:
                    color = st.color_picker("Layer Color", key=f"color_{i}_{j}")
            
            with col2:
                thickness = st.number_input(
                    "Layer Thickness (m)",
                    min_value=0.1,
                    value=1.0,
                    key=f"thickness_{i}_{j}"
                )
                
                # Additional geological parameters
                water_content = st.number_input(
                    "Water Content (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    key=f"water_{i}_{j}"
                )
                
                density = st.number_input(
                    "Density (g/cm³)",
                    min_value=0.1,
                    value=1.8,
                    key=f"density_{i}_{j}"
                )
                
                sample_quality = st.selectbox(
                    "Sample Quality",
                    ["Undisturbed", "Partially Disturbed", "Disturbed", "No Sample"],
                    key=f"quality_{i}_{j}"
                )
                
                additional_notes = st.text_area(
                    "Additional Notes",
                    value="",
                    key=f"notes_{i}_{j}",
                    height=50
                )
            
            layers.append({
                'description': description,
                'thickness': thickness,
                'color': color,
                'water_content': water_content,
                'density': density,
                'sample_quality': sample_quality,
                'additional_notes': additional_notes
            })
        
        # Create and display geological profile for this borehole
        st.markdown(f"#### Geological Profile for {name}")
        profile_fig = create_custom_geological_profile(layers)
        st.plotly_chart(profile_fig, use_container_width=True)
        
        borehole_data.append({
            'Name': name,
            'X': x,
            'Y': y,
            'layers': layers
        })
    
    borehole_df = pd.DataFrame(borehole_data)

    # Map generation and data export
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Map"):
            m = plot_tunnel_and_boreholes(tunnel_coords, borehole_df, from_crs, project_type)
            folium_static(m)
    
    with col2:
        if st.button("Export Geological Data"):
            export_data = {
                'project_type': project_type,
                'coordinate_system': selected_crs,
                'legend': st.session_state.legend_items,
                'tunnel_coordinates': tunnel_coords if project_type == 'Tunnel Project' else None,
                'boreholes': borehole_data
            }
            st.download_button(
                "Download Geological Data",
                data=json.dumps(export_data, indent=2),
                file_name="geological_data.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
