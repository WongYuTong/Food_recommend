let map;
let marker;
let autocomplete;
let placeId;

function initMap() {
    const defaultCenter = { lat: 23.97565, lng: 120.9738819 };
    map = new google.maps.Map(document.getElementById("map"), {
        center: defaultCenter,
        zoom: 7,
        mapTypeControl: false
    });
    const input = document.getElementById("location-search");
    autocomplete = new google.maps.places.Autocomplete(input, {
        fields: ["place_id", "geometry", "name", "formatted_address"],
        types: ["restaurant", "food"],
        strictBounds: false
    });
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) return;
        map.setCenter(place.geometry.location);
        map.setZoom(17);
        if (marker) {
            marker.position = place.geometry.location;
        } else {
            marker = new google.maps.marker.AdvancedMarkerElement({
                map: map,
                position: place.geometry.location,
                title: place.name
            });
        }
        document.getElementById("id_location_name").value = place.name;
        document.getElementById("id_location_address").value = place.formatted_address;
        document.getElementById("id_location_lat").value = place.geometry.location.lat();
        document.getElementById("id_location_lng").value = place.geometry.location.lng();
        document.getElementById("id_location_place_id").value = place.place_id;
    });
    map.addListener("click", (mapsMouseEvent) => {
        const clickLocation = mapsMouseEvent.latLng;
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ location: clickLocation }, (results, status) => {
            if (status === "OK") {
                if (results[0]) {
                    placeDetails(results[0].place_id);
                }
            }
        });
    });
    const latInput = document.getElementById('id_location_lat');
    const lngInput = document.getElementById('id_location_lng');
    const nameInput = document.getElementById('id_location_name');
    const addressInput = document.getElementById('id_location_address');
    const placeIdInput = document.getElementById('id_location_place_id');

    // 如果有已儲存的地點，初始化地圖標記
    if (latInput && lngInput && latInput.value && lngInput.value) {
        const position = {
            lat: parseFloat(latInput.value),
            lng: parseFloat(lngInput.value)
        };
        map.setCenter(position);
        map.setZoom(16);
        marker = new google.maps.marker.AdvancedMarkerElement({
            map: map,
            position: position,
            title: nameInput && nameInput.value ? nameInput.value : ""
        });
    }
}

function placeDetails(placeId) {
    const service = new google.maps.places.PlacesService(map);
    service.getDetails(
        { placeId: placeId, fields: ["name", "formatted_address", "geometry", "place_id"] },
        (place, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                if (marker) {
                    marker.position = place.geometry.location;
                } else {
                    marker = new google.maps.marker.AdvancedMarkerElement({
                        map: map,
                        position: place.geometry.location,
                        title: place.name
                    });
                }
                document.getElementById("id_location_name").value = place.name;
                document.getElementById("id_location_address").value = place.formatted_address;
                document.getElementById("id_location_lat").value = place.geometry.location.lat();
                document.getElementById("id_location_lng").value = place.geometry.location.lng();
                document.getElementById("id_location_place_id").value = place.place_id;
                document.getElementById("location-search").value = place.name;
            }
        }
    );
}