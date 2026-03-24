// ===============================
// MAP INITIALIZATION
// ===============================
const map = L.map('map').setView([14.5995,120.9842], 12);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);

let userMarker;
let destinationMarker;
let routeLine;
let stationMarkers = [];


// ===============================
// NCR CHARGING STATIONS
// ===============================
const stations = [
 {name:"SM North EDSA EV",lat:14.6567,lng:121.0281},
 {name:"Trinoma EV Station",lat:14.6535,lng:121.0336},
 {name:"BGC Stopover Charging",lat:14.5520,lng:121.0487},
 {name:"Makati Circuit EV",lat:14.5636,lng:121.0190},
 {name:"Ortigas EV Station",lat:14.5869,lng:121.0614},
 {name:"SM Megamall EV",lat:14.5849,lng:121.0567},
 {name:"MOA EV Charging",lat:14.5350,lng:120.9822},
 {name:"Robinsons Manila EV",lat:14.5764,lng:120.9880}
];


// ===============================
// GEOCODING (TEXT → COORDS)
// ===============================
async function geocode(place){

    const url =
`https://nominatim.openstreetmap.org/search?format=json&q=${place}`;

    const res = await fetch(url);
    const data = await res.json();

    if(!data.length){
        alert("Location not found: " + place);
        return null;
    }

    return {
        lat: parseFloat(data[0].lat),
        lng: parseFloat(data[0].lon)
    };
}


// ===============================
// ROUTE FETCH (OSRM)
// ===============================
async function getRoute(start,end){

    const url =
`https://router.project-osrm.org/route/v1/driving/
${start.lng},${start.lat};
${end.lng},${end.lat}?overview=full&geometries=geojson`;

    const res = await fetch(url);
    return await res.json();
}


// ===============================
// DRAW ROUTE
// ===============================
function drawRoute(coords){

    if(routeLine) map.removeLayer(routeLine);

    routeLine = L.polyline(coords,{
        weight:6
    }).addTo(map);

    map.fitBounds(routeLine.getBounds());
}


// ===============================
// SMART ROUTING SYSTEM
// ===============================
document.getElementById("routeBtn").onclick = async ()=>{

    const startText = document.getElementById("startInput").value;
    const destText = document.getElementById("destinationInput").value;
    const battery = Number(document.getElementById("batteryInput").value);

    if(!startText || !destText){
        alert("Enter locations");
        return;
    }

    const start = await geocode(startText);
    const destination = await geocode(destText);

    if(!start || !destination) return;

    // markers
    if(userMarker) map.removeLayer(userMarker);
    if(destinationMarker) map.removeLayer(destinationMarker);

    userMarker = L.marker([start.lat,start.lng])
        .addTo(map)
        .bindPopup("Start Location");

    destinationMarker = L.marker([destination.lat,destination.lng])
        .addTo(map)
        .bindPopup("Destination");

    // direct route
    const direct = await getRoute(start,destination);

    const distanceKm = direct.routes[0].distance/1000;
    const batteryNeeded = distanceKm * 0.18;

    // ===============================
    // DECISION SYSTEM
    // ===============================
    if(battery >= batteryNeeded){

        const coords = direct.routes[0].geometry.coordinates
            .map(c=>[c[1],c[0]]);

        drawRoute(coords);

        document.getElementById("routeInfo").innerHTML =
        `<div class="route-card">
            ✅ Battery sufficient.<br>
            Direct route selected.<br>
            Distance: ${distanceKm.toFixed(1)} km
        </div>`;

        return;
    }

    // NEED CHARGING → FIND BEST STATION
    let bestStation=null;
    let bestDistance=99999;

    for(const s of stations){

        const route = await getRoute(start,s);
        const d = route.routes[0].distance/1000;

        if(d < bestDistance){
            bestDistance = d;
            bestStation = s;
        }
    }

    // route start → station
    const toStation = await getRoute(start,bestStation);

    const coords = toStation.routes[0].geometry.coordinates
        .map(c=>[c[1],c[0]]);

    drawRoute(coords);

    // station marker (green)
    L.circleMarker(
        [bestStation.lat,bestStation.lng],
        {radius:8,color:"green"}
    ).addTo(map)
    .bindPopup(bestStation.name);

    document.getElementById("routeInfo").innerHTML =
    `<div class="route-card">
        ⚠ Battery insufficient.<br>
        Recommended Charging Station:<br>
        <strong>${bestStation.name}</strong><br>
        Distance to station: ${bestDistance.toFixed(1)} km
    </div>`;
};