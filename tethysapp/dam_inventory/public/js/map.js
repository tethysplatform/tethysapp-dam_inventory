$(function() {
    var popup = new ol.Overlay({
        element: document.getElementById('popup')
    });

    var map = TETHYS_MAP_VIEW.getMap();

    // Get the Select Interaction
    var select_interaction = TETHYS_MAP_VIEW.getSelectInteraction();

    // Add Overlay to map
    map.addOverlay(popup);

    // When selected, call function to display properties
    select_interaction.getFeatures().on('change:length', function(e) {
        var popup_element = popup.getElement();

        if (e.target.getArray().length > 0) {
            // this means there is at least 1 feature selected
            var selected_feature = e.target.item(0); // 1st feature in Collection
            var coordinate = selected_feature.getGeometry().getCoordinates();

            // Clean up last popup and reinitialize
            $(popup_element).popover('destroy');
            popup.setPosition(coordinate);

            $(popup_element).popover({
              'placement': 'top',
              'animation': false,
              'html': true,
              'content': '<p>Foo bar:</p>'
            });
            $(popup_element).popover('show');


            console.log(selected_feature);
            console.log(selected_feature.get('name'));
            console.log(selected_feature.get('owner'));
            console.log(selected_feature.get('river'));
            console.log(selected_feature.get('date_built'));

        } else {
            // remove pop up.
            $(popup_element).popover('destroy');
        }
    });
});