from django.contrib import messages
from tethys_sdk.gizmos import (
    MapView, MVDraw, MVView, Button, TextInput, DatePicker, SelectInput, DataTableView
)
from tethys_sdk.layouts import MapLayout
from tethys_sdk.routing import controller
from .app import App
from .model import add_new_dam, get_all_dams


@controller(name="home", app_workspace=True)
class HomeMap(MapLayout):
    app = App
    base_template = f'{App.package}/base.html'
    map_title = 'Dam Inventory'
    map_subtitle = 'Tutorial'
    basemaps = ['OpenStreetMap', 'ESRI']
    show_properties_popup = True

    def compose_layers(self, request, map_view, app_workspace, *args, **kwargs):
        # Get list of dams and create dams MVLayer:
        dams = get_all_dams(app_workspace.path)
        features = []

        # Define GeoJSON Features
        for dam in dams:
            dam_location = dam.get('location')
            dam_feature = {
                'type': 'Feature',
                'geometry': {
                    'type': dam_location['type'],
                    'coordinates': dam_location['coordinates'],
                },
                'properties': {
                    'id': dam['id'],
                    'name': dam['name'],
                    'owner': dam['owner'],
                    'river': dam['river'],
                    'date_built': dam['date_built']
                }
            }

            features.append(dam_feature)

        # Define GeoJSON FeatureCollection
        dams_feature_collection = {
            'type': 'FeatureCollection',
            'crs': {
                'type': 'name',
                'properties': {
                    'name': 'EPSG:4326'
                }
            },
            'features': features
        }

        # Compute zoom extent for the dams layer
        layer_extent = self.compute_dams_extent(dams)

        dam_layer = self.build_geojson_layer(
            geojson=dams_feature_collection,
            layer_name='dams',
            layer_title='Dams',
            layer_variable='dams',
            extent=layer_extent,
            visible=True,
            selectable=True,
            plottable=True,
        )

        layer_groups = [
            self.build_layer_group(
                id='all-layers',
                display_name='Layers',
                layer_control='checkbox',
                layers=[dam_layer]
            )
        ]

        # Update the map view with the new extent
        map_view.view = MVView(
            projection='EPSG:4326',
            extent=layer_extent,
            maxZoom=self.max_zoom,
            minZoom=self.min_zoom,
        )

        return layer_groups

    def build_map_extent_and_view(self, request, app_workspace, *args, **kwargs):
        """
        Builds the default MVView and BBOX extent for the map.

        Returns:
            MVView, 4-list<float>: default view and extent of the project.
        """
        dams = get_all_dams(app_workspace.path)
        extent = self.compute_dams_extent(dams)

        # Construct the default view
        view = MVView(
            projection="EPSG:4326",
            extent=extent,
            maxZoom=self.max_zoom,
            minZoom=self.min_zoom,
        )

        return view, extent

    def compute_dams_extent(self, dams):
        """Compute the extent/bbox of the given dams."""
        lat_list = []
        lng_list = []

        # Define GeoJSON Features
        for dam in dams:
            dam_location = dam.get('location')
            lat_list.append(dam_location['coordinates'][1])
            lng_list.append(dam_location['coordinates'][0])

        if len(lat_list) > 1:
            # Compute the bounding box of all the dams
            min_x = min(lng_list)
            min_y = min(lat_list)
            max_x = max(lng_list)
            max_y = max(lat_list)
            x_dist = max_x - min_x
            y_dist = max_y - min_y

            # Buffer the bounding box
            buffer_factor = 0.1
            x_buffer = x_dist * buffer_factor
            y_buffer = y_dist * buffer_factor
            min_xb = min_x - x_buffer
            min_yb = min_y - y_buffer
            max_xb = max_x + x_buffer
            max_yb = max_y + y_buffer

            # Bounding box for the view
            extent = [min_xb, min_yb, max_xb, max_yb]
        else:
            extent = [-125.771484, 24.527135, -66.005859, 49.667628]  # CONUS

        return extent


@controller(url='dams/add', app_workspace=True)
def add_dam(request, app_workspace):
    """
    Controller for the Add Dam page.
    """
    # Default Values
    name = ''
    owner = 'Reclamation'
    river = ''
    date_built = ''
    location = ''

    # Errors
    name_error = ''
    owner_error = ''
    river_error = ''
    date_error = ''
    location_error = ''

    # Handle form submission
    if request.POST and 'add-button' in request.POST:
        # Get values
        has_errors = False
        name = request.POST.get('name', None)
        owner = request.POST.get('owner', None)
        river = request.POST.get('river', None)
        date_built = request.POST.get('date-built', None)
        location = request.POST.get('geometry', None)

        # Validate
        if not name:
            has_errors = True
            name_error = 'Name is required.'

        if not owner:
            has_errors = True
            owner_error = 'Owner is required.'

        if not river:
            has_errors = True
            river_error = 'River is required.'

        if not date_built:
            has_errors = True
            date_error = 'Date Built is required.'

        if not location:
            has_errors = True
            location_error = 'Location is required.'

        if not has_errors:
            add_new_dam(
                db_directory=app_workspace.path,
                location=location,
                name=name,
                owner=owner,
                river=river,
                date_built=date_built
            )
            return App.redirect(App.reverse('home'))

        messages.error(request, "Please fix errors.")

    # Define form gizmos
    name_input = TextInput(
        display_text='Name',
        name='name',
        initial=name,
        error=name_error
    )

    owner_input = SelectInput(
        display_text='Owner',
        name='owner',
        multiple=False,
        options=[('Reclamation', 'Reclamation'), ('Army Corp', 'Army Corp'), ('Other', 'Other')],
        initial=owner,
        error=owner_error
    )

    river_input = TextInput(
        display_text='River',
        name='river',
        placeholder='e.g.: Mississippi River',
        initial=river,
        error=river_error
    )

    date_built = DatePicker(
        name='date-built',
        display_text='Date Built',
        autoclose=True,
        format='MM d, yyyy',
        start_view='decade',
        today_button=True,
        initial=date_built,
        error=date_error
    )

    initial_view = MVView(
        projection='EPSG:4326',
        center=[-98.6, 39.8],
        zoom=3.5
    )

    drawing_options = MVDraw(
        controls=['Modify', 'Delete', 'Move', 'Point'],
        initial='Point',
        output_format='GeoJSON',
        point_color='#FF0000'
    )

    location_input = MapView(
        height='300px',
        width='100%',
        basemap=['OpenStreetMap'],
        draw=drawing_options,
        view=initial_view
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='plus-square',
        style='success',
        attributes={'form': 'add-dam-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=App.reverse('home')
    )

    context = {
        'name_input': name_input,
        'owner_input': owner_input,
        'river_input': river_input,
        'date_built_input': date_built,
        'location_input': location_input,
        'location_error': location_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
    }

    return App.render(request, 'add_dam.html', context)


@controller(name='dams', url='dams', app_workspace=True)
def list_dams(request, app_workspace):
    """
    Show all dams in a table view.
    """
    dams = get_all_dams(app_workspace.path)
    table_rows = []

    for dam in dams:
        table_rows.append(
            (
                dam['name'], dam['owner'],
                dam['river'], dam['date_built']
            )
        )

    dams_table = DataTableView(
        column_names=('Name', 'Owner', 'River', 'Date Built'),
        rows=table_rows,
        searching=False,
        orderClasses=False,
        lengthMenu=[ [10, 25, 50, -1], [10, 25, 50, "All"] ],
    )

    context = {
        'dams_table': dams_table
    }

    return App.render(request, 'list_dams.html', context)
