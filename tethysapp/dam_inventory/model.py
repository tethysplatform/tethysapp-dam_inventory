import json
import os
import uuid
from pathlib import Path


def add_new_dam(db_directory: Path | str, location: str, name: str, owner: str, river: str, date_built: str):
    """
    Persist new dam.
    """
    # Convert GeoJSON to Python dictionary
    location_dict = json.loads(location)

    # Serialize data to json
    new_dam_id = uuid.uuid4()
    dam_dict = {
        'id': str(new_dam_id),
        'location': location_dict['geometries'][0],
        'name': name,
        'owner': owner,
        'river': river,
        'date_built': date_built
    }

    dam_json = json.dumps(dam_dict)

    # Write to file in {{db_directory}}/dams/{{uuid}}.json
    # Make dams dir if it doesn't exist
    dams_dir = Path(db_directory) / 'dams'
    if not dams_dir.exists():
        os.makedirs(dams_dir, exist_ok=True)

    # Name of the file is its id
    file_name = str(new_dam_id) + '.json'
    file_path = dams_dir / file_name

    # Write json
    with file_path.open('w') as f:
        f.write(dam_json)


def get_all_dams(db_directory: Path | str):
    """
    Get all persisted dams.
    """
    # Write to file in {{db_directory}}/dams/{{uuid}}.json
    # Make dams dir if it doesn't exist
    dams_dir = Path(db_directory) / 'dams'
    if not dams_dir.exists():
        os.makedirs(dams_dir, exist_ok=True)

    dams = []

    # Open each json file and convert contents to python dictionaries
    for dam_json in dams_dir.glob('*.json'):
        with dam_json.open('r') as f:
            dam_dict = json.loads(f.read())
            dams.append(dam_dict)

    return dams
