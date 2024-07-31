from tethys_sdk.base import TethysAppBase


class App(TethysAppBase):
    """
    Tethys app class for Dam Inventory.
    """
    name = 'Dam Inventory'
    description = ''
    package = 'dam_inventory'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'dam-inventory'
    color = '#d35400'
    tags = ''
    enable_feedback = False
    feedback_emails = []
