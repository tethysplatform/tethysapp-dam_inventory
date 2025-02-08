from .app import App
from .model import Hydrograph


def create_hydrograph(hydrograph_id):
    """
    Generates a plotly view of a hydrograph.
    """
    # Get objects from database
    Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    hydrograph = session.query(Hydrograph).get(int(hydrograph_id))
    dam = hydrograph.dam
    time = []
    flow = []
    for hydro_point in hydrograph.points:
        time.append(hydro_point.time)
        flow.append(hydro_point.flow)

    # Build up Plotly plot
    data =[
        dict(
            x=time,
            y=flow,
            name=f'Hydrograph for {dam.name}',
            line={'color': '#0080ff', 'width': 4, 'shape': 'spline'},
        )
    ]
    layout = {
        'title': f'Hydrograph for {dam.name}',
        'xaxis': {'title': 'Time (hr)'},
        'yaxis': {'title': 'Flow (cfs)'},
    }
    session.close()
    return data, layout
