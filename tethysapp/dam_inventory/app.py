from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting


class DamInventory(TethysAppBase):
    """
    Tethys app class for Dam Inventory.
    """

    name = 'Dam Inventory'
    description = ''
    package = 'dam_inventory'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/dam_icon.png'
    root_url = 'dam-inventory'
    color = '#244C96'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def custom_settings(self):
        """
        Example custom_settings method.
        """
        custom_settings = (
            CustomSetting(
                name='max_dams',
                type=CustomSetting.TYPE_INTEGER,
                description='Maximum number of dams that can be created in the app.',
                required=False
            ),
        )
        return custom_settings
