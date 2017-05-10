import os
import uuid
import json
from .app import DamInventory as app


def add_new_dam(name, owner, river, date_built):
    """
    Persist new dam.
    """
    # Serialize data to json
    new_dam_id = uuid.uuid4()
    dam_dict = {
        'id': str(new_dam_id),
        'name': name,
        'owner': owner,
        'river': river,
        'date_built': date_built
    }

    dam_json = json.dumps(dam_dict)

    # Write to file in app_workspace/dams/{{uuid}}.json
    # Make dams dir if it doesn't exist
    user_workspace = app.get_app_workspace()
    dams_dir = os.path.join(user_workspace.path, 'dams')
    if not os.path.exists(dams_dir):
        os.mkdir(dams_dir)

    # Name of the file is its id
    file_name = str(new_dam_id) + '.json'
    file_path = os.path.join(dams_dir, file_name)

    # Write json
    with open(file_path, 'w') as f:
        f.write(dam_json)


def get_all_dams():
    """
    Get all persisted dams.
    """
    # Write to file in app_workspace/dams/{{uuid}}.json
    # Make dams dir if it doesn't exist
    user_workspace = app.get_app_workspace()
    dams_dir = os.path.join(user_workspace.path, 'dams')
    if not os.path.exists(dams_dir):
        os.mkdir(dams_dir)

    dams = []

    # Open each file and convert contents to python objects
    for dam_json in os.listdir(dams_dir):
        dam_json_path = os.path.join(dams_dir, dam_json)
        with open(dam_json_path, 'r') as f:
            dam_dict = json.loads(f.readlines()[0])
            dams.append(dam_dict)

    return dams




