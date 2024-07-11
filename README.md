# Tunnel Visualization Streamlit App

## Overview

This Streamlit app provides an interactive visualization tool for tunnel alignments and borehole locations. It allows users to input tunnel coordinates and borehole data, select different coordinate systems, and generate a map showing the tunnel alignment and borehole positions.

## Features

- **Customizable Tunnel Alignment**: Input multiple points to define complex tunnel paths.
- **Borehole Visualization**: Add multiple boreholes with custom names and coordinates.
- **Coordinate System Selection**: Choose from various UTM coordinate systems.
- **Interactive Map**: 
  - Toggle between satellite imagery and OpenStreetMap views.
  - Measure distances and areas.
  - Click to view lat/lon coordinates.
- **Popup Information**: Hover over boreholes to see detailed coordinate information.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/tunnel-visualization-app.git
   cd tunnel-visualization-app
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run tunnel_visualization_app.py
   ```

2. Open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).

3. Use the app interface to:
   - Select the input coordinate system.
   - Input tunnel coordinates (multiple points).
   - Add borehole data (name, X, and Y coordinates).
   - Click "Generate Map" to visualize the data.

4. Interact with the generated map:
   - Switch between satellite and street map views.
   - Use the measurement tool for distances and areas.
   - Click on the map to see lat/lon coordinates.
   - Hover over borehole markers for detailed information.

## Requirements

- Python 3.7+
- Streamlit
- Folium
- Streamlit-Folium
- PyProj
- Pandas

See `requirements.txt` for specific version information.

## Contributing

Contributions to improve the app are welcome. Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the web app framework.
- [Folium](https://python-visualization.github.io/folium/) for map visualizations.
- [PyProj](https://pyproj4.github.io/pyproj/) for coordinate transformations.
