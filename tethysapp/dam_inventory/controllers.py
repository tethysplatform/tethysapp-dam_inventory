from tethys_sdk.gizmos import Button
from tethys_sdk.layouts import MapLayout
from tethys_sdk.routing import controller
from .app import App


@controller(name="home")
class HomeMap(MapLayout):
    app = App
    base_template = f'{App.package}/base.html'
    map_title = 'Dam Inventory'
    map_subtitle = 'Tutorial'
    basemaps = ['OpenStreetMap', 'ESRI']


@controller(url='dams/add')
def add_dam(request):
    """
    Controller for the Add Dam page.
    """
    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='plus-square',
        style='success'
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=App.reverse('home')
    )

    context = {
        'add_button': add_button,
        'cancel_button': cancel_button,
    }

    return App.render(request, 'add_dam.html', context)
