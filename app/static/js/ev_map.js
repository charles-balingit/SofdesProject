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

// ===============================
// CHARGING STATION ICON
// ===============================
const chargingIcon = L.divIcon({
    className: "charging-icon",
    html: "⚡",
    iconSize: [28, 28],
    iconAnchor: [14, 14]
});

// ===============================
// NCR CHARGING STATIONS
// ===============================
const stations = [
    { name:"SM North EDSA EV Charging", lat:14.6569, lng:121.0296 },
    { name:"SM Aura Premier EV Charging", lat:14.5453, lng:121.0537 },
    { name:"SM Mall of Asia EV Charging", lat:14.5350, lng:120.9822 },
    { name:"SM Megamall EV Charging", lat:14.5849, lng:121.0567 },
    { name:"SM City Manila EV Charging", lat:14.5896, lng:120.9817 },
    { name:"SM City Fairview EV Charging", lat:14.7346, lng:121.0583 },
    { name:"SM City Bicutan EV Charging", lat:14.4876, lng:121.0447 },
    { name:"SM City Marikina EV Charging", lat:14.6255, lng:121.1012 },
    { name:"SM Southmall EV Charging", lat:14.4326, lng:120.9793 },
    { name:"Quezon City Hall EV Charging", lat:14.6511, lng:121.0495 },
    { name:"UP Diliman EV Charging Station", lat:14.6548, lng:121.0687 },
    { name:"Pasig City Hall EV Charging", lat:14.5764, lng:121.0851 },
    { name:"Nissan Mantrade Makati Charging", lat:14.5312, lng:121.0113 },
    { name:"Nissan Otis Manila Charging", lat:14.5790, lng:120.9972 },
    { name:"The Podium EV Charging Station", lat:14.5865, lng:121.0574 },
    { name:"Go Station Katipunan EV Charging", lat:14.6380, lng:121.0755 }
];

// ===============================
// SHOW ALL CHARGING STATIONS
// ===============================
const stationMarkers = [];

function loadChargingStations() {

    stations.forEach(station => {

        const marker = L.marker(
            [station.lat, station.lng],
            { icon: chargingIcon }
        )
        .addTo(map)
        .bindPopup(`
            <b>${station.name}</b><br>
            EV Charging Station ⚡
        `);

        stationMarkers.push(marker);
    });
}

// load immediately
loadChargingStations();

// ===============================
// GEOCODING
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
// ROUTE FETCH
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

    routeLine = L.polyline(coords,{ weight:6 }).addTo(map);

    map.fitBounds(routeLine.getBounds());
}


// ===============================
// SUMMARY PANEL UPDATE
// ===============================
function updateRouteSummary(distanceKm, batteryPercent){

    const MAX_RANGE = 300;
    const batteryDistance = (batteryPercent/100)*MAX_RANGE;

    // NEW LOGIC
    const difference = batteryDistance - distanceKm;

    document.getElementById("distanceValue").textContent =
        distanceKm.toFixed(1);

    document.getElementById("batteryRangeValue").textContent =
        batteryDistance.toFixed(1);

    const statusEl = document.getElementById("batteryStatus");

    statusEl.classList.remove(
        "status-safe",
        "status-warning",
        "status-danger"
    );

    if (difference > 20) {
        statusEl.textContent = "SAFE";
        statusEl.classList.add("status-safe");
    }
    else if (difference <= 20 && difference > 10) {
        statusEl.textContent = "WARNING";
        statusEl.classList.add("status-warning");
    }
    else {
        statusEl.textContent = "DANGER";
        statusEl.classList.add("status-danger");
    }

    return batteryDistance; // ⭐ return for reuse
}


// ===============================
// SMART ROUTING SYSTEM
// ===============================
document.getElementById("routeBtn").onclick = async ()=>{

    const startText =
        document.getElementById("startInput").value;

    const destText =
        document.getElementById("destinationInput").value;

    const battery =
        Number(document.getElementById("batteryInput").value);

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

    userMarker=L.marker([start.lat,start.lng])
        .addTo(map).bindPopup("Start Location");

    destinationMarker=L.marker([destination.lat,destination.lng])
        .addTo(map).bindPopup("Destination");


    // DIRECT ROUTE
    const direct = await getRoute(start,destination);

    if(!direct.routes.length){
        alert("Route not found");
        return;
    }

    const distanceKm =
        direct.routes[0].distance/1000;

    // ⭐ UPDATE SUMMARY
    const batteryDistance =
        updateRouteSummary(distanceKm,battery);


    // ===============================
    // BATTERY SUFFICIENT
    // ===============================
    if(distanceKm <= batteryDistance){

        const coords =
            direct.routes[0].geometry.coordinates
            .map(c=>[c[1],c[0]]);

        drawRoute(coords);

        document.getElementById("routeInfo").innerHTML=
        `<div class="route-card">
            ✅ Battery sufficient.<br>
            Direct route selected.<br>
            Distance: ${distanceKm.toFixed(1)} km
        </div>`;

        return;
    }


    // ===============================
    // NEED CHARGING
    // ===============================
    let bestStation=null;
    let bestDistance=Infinity;

    for(const s of stations){

        const route=await getRoute(start,s);
        if(!route.routes.length) continue;

        const stationDistance =
            route.routes[0].distance/1000;

        // ⭐ IMPORTANT RULE:
        // battery distance must NOT be less
        // than station distance
        if(stationDistance <= batteryDistance &&
           stationDistance < bestDistance){

            bestDistance = stationDistance;
            bestStation = s;
        }
    }

    // NO REACHABLE STATION
    if(!bestStation){

        document.getElementById("routeInfo").innerHTML =
        `<div class="route-card">
            🔴 DANGER<br>
            No reachable charging station with current battery.
        </div>`;

        return;
    }


    // ROUTE TO STATION
    const toStation=await getRoute(start,bestStation);

    const coords=
        toStation.routes[0].geometry.coordinates
        .map(c=>[c[1],c[0]]);

    drawRoute(coords);

    L.marker(
    [bestStation.lat, bestStation.lng],
    { icon: chargingIcon }
)
    .addTo(map)
    .bindPopup(`✅ Recommended Station<br><b>${bestStation.name}</b>`)
    .openPopup();

    document.getElementById("routeInfo").innerHTML=
    `<div class="route-card">
        ⚠ Battery insufficient.<br>
        Recommended Charging Station:<br>
        <strong>${bestStation.name}</strong><br>
        Distance to station: ${bestDistance.toFixed(1)} km
    </div>`;
};