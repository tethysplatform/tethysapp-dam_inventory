from django.contrib import messages
from django.utils.html import format_html
from tethys_sdk.gizmos import (
    MapView, MVDraw, MVView, Button, TextInput, DatePicker, SelectInput, DataTableView, PlotlyView
)
from tethys_sdk.layouts import MapLayout
from tethys_sdk.permissions import has_permission
from tethys_sdk.routing import controller
from .app import App
from .helpers import create_hydrograph
from .model import Dam, add_new_dam, get_all_dams, assign_hydrograph_to_dam, get_hydrograph


@controller(name="home")
class HomeMap(MapLayout):
    app = App
    base_template = f'{App.package}/base.html'
    map_title = 'Dam Inventory'
    map_subtitle = 'Tutorial'
    basemaps = ['OpenStreetMap', 'ESRI']
    show_properties_popup = True
    plot_slide_sheet = True

    def get_context(self, request, context, *args, **kwargs):
        # Add custom context variables
        context.update({
            'can_add_dams': has_permission(request, 'add_dams'),
        })

        # Call the MapLayout get_context method to initialize the map view
        context = super().get_context(request, context, *args, **kwargs)
        return context

    def compose_layers(self, request, map_view, *args, **kwargs):
        # Get list of dams and create dams MVLayer:
        dams = get_all_dams()
        features = []

        # Define GeoJSON Features
        for dam in dams:
            dam_feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [dam.longitude, dam.latitude],
                },
                'properties': {
                    'id': dam.id,
                    'name': dam.name,
                    'owner': dam.owner,
                    'river': dam.river,
                    'date_built': dam.date_built
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

    def build_map_extent_and_view(self, request, *args, **kwargs):
        """
        Builds the default MVView and BBOX extent for the map.

        Returns:
            MVView, 4-list<float>: default view and extent of the project.
        """
        dams = get_all_dams()
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
            lat_list.append(dam.latitude)
            lng_list.append(dam.longitude)

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

    def get_plot_for_layer_feature(self, request, layer_name, feature_id, layer_data, feature_props, *args, **kwargs):
        """
        Retrieves plot data for given feature on given layer.

        Args:
            layer_name (str): Name/id of layer.
            feature_id (str): ID of feature.
            layer_data (dict): The MVLayer.data dictionary.
            feature_props (dict): The properties of the selected feature.

        Returns:
            str, list<dict>, dict: plot title, data series, and layout options, respectively.
        """
        Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
        session = Session()
        dam = session.query(Dam).get(int(feature_id))

        if dam.hydrograph:
            data, layout = create_hydrograph(dam.hydrograph.id)
        else:
            data, layout = [], {}
        session.close()
        return f'Hydrograph for {dam.name}', data, layout


@controller(url='dams/add', permission_required='add_dams')
def add_dam(request):
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
            # Get value of max_dams custom setting
            max_dams = App.get_custom_setting('max_dams')

            # Query database for count of dams
            Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
            session = Session()
            num_dams = session.query(Dam).count()

            # Only add the dam if custom setting doesn't exist or we have not exceed max_dams
            if not max_dams or num_dams < max_dams:
                add_new_dam(
                    location=location,
                    name=name,
                    owner=owner,
                    river=river,
                    date_built=date_built
                )
            else:
                messages.warning(request, 'Unable to add dam "{0}", because the inventory is full.'.format(name))

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
        'can_add_dams': has_permission(request, 'add_dams')
    }

    return App.render(request, 'add_dam.html', context)


@controller(name='dams', url='dams')
def list_dams(request):
    """
    Show all dams in a table view.
    """
    dams = get_all_dams()
    table_rows = []

    for dam in dams:
        hydrograph_id = get_hydrograph(dam.id)
        if hydrograph_id:
            url = App.reverse('hydrograph', kwargs={'hydrograph_id': hydrograph_id})
            dam_hydrograph = format_html('<a class="btn btn-primary" href="{}">Hydrograph Plot</a>'.format(url))
        else:
            dam_hydrograph = format_html('<a class="btn btn-primary disabled" title="No hydrograph assigned" '
                                        'style="pointer-events: auto;">Hydrograph Plot</a>')

        table_rows.append(
            (
                dam.name, dam.owner,
                dam.river, dam.date_built,
                dam_hydrograph
            )
        )

    dams_table = DataTableView(
        column_names=('Name', 'Owner', 'River', 'Date Built', 'Hydrograph'),
        rows=table_rows,
        searching=False,
        orderClasses=False,
        lengthMenu=[ [10, 25, 50, -1], [10, 25, 50, "All"] ],
    )

    context = {
        'dams_table': dams_table,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    return App.render(request, 'list_dams.html', context)


@controller(url='hydrographs/assign')
def assign_hydrograph(request):
    """
    Controller for the Add Hydrograph page.
    """
    # Get dams from database
    Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    all_dams = session.query(Dam).all()

    # Defaults
    dam_select_options = [(dam.name, dam.id) for dam in all_dams]
    selected_dam = None
    hydrograph_file = None

    # Errors
    dam_select_errors = ''
    hydrograph_file_error = ''

    # Case where the form has been submitted
    if request.POST and 'add-button' in request.POST:
        # Get Values
        has_errors = False
        selected_dam = request.POST.get('dam-select', None)

        if not selected_dam:
            has_errors = True
            dam_select_errors = 'Dam is Required.'

        # Get File
        if request.FILES and 'hydrograph-file' in request.FILES:
            # Get a list of the files
            hydrograph_file = request.FILES.getlist('hydrograph-file')

        if not hydrograph_file and len(hydrograph_file) > 0:
            has_errors = True
            hydrograph_file_error = 'Hydrograph File is Required.'

        if not has_errors:
            # Process file here
            success = assign_hydrograph_to_dam(selected_dam, hydrograph_file[0])

            # Provide feedback to user
            if success:
                messages.info(request, 'Successfully assigned hydrograph.')
            else:
                messages.info(request, 'Unable to assign hydrograph. Please try again.')
            return App.redirect(App.reverse('home'))

        messages.error(request, "Please fix errors.")

    dam_select_input = SelectInput(
        display_text='Dam',
        name='dam-select',
        multiple=False,
        options=dam_select_options,
        initial=selected_dam,
        error=dam_select_errors
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='plus-square',
        style='success',
        attributes={'form': 'add-hydrograph-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=App.reverse('home')
    )

    context = {
        'dam_select_input': dam_select_input,
        'hydrograph_file_error': hydrograph_file_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    session.close()

    return App.render(request, 'assign_hydrograph.html', context)


@controller(url='hydrographs/{hydrograph_id}')
def hydrograph(request, hydrograph_id):
    """
    Controller for the Hydrograph Page.
    """
    data, layout = create_hydrograph(hydrograph_id)
    figure = {'data': data, 'layout': layout}
    hydrograph_plot = PlotlyView(figure, height="500px", width="100%")
    context = {
        'hydrograph_plot': hydrograph_plot,
        'can_add_dams': has_permission(request, 'add_dams')
    }
    return App.render(request, 'hydrograph.html', context)
