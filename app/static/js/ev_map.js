// ===============================
// RANDOM USER DATA
// ===============================
const locations = [
    { name: "Quezon City", lat: 14.6760, lng: 121.0437 },
    { name: "Makati", lat: 14.5547, lng: 121.0244 },
    { name: "Pasig", lat: 14.5764, lng: 121.0851 }
];

const user = locations[Math.floor(Math.random() * locations.length)];
const battery = Math.floor(Math.random() * 50) + 50;

document.getElementById("location").textContent = user.name;
document.getElementById("battery").textContent = battery;


// ===============================
// CUSTOM MAP ICONS
// ===============================
const redIcon = L.icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

const greenIcon = L.icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/green-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});


// ===============================
// MAP 1 — STATIONS OVERVIEW
// ===============================
const map = L.map('map').setView([user.lat, user.lng], 12);

L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);

// USER MARKER (RED)
const userMarker = L.marker(
    [user.lat, user.lng],
    { icon: redIcon }
)
.addTo(map)
.bindPopup("📍 Your Location")
.openPopup();


// ===============================
// CHARGING STATIONS (PH)
// ===============================
const stations = [
    { name:"SM North EDSA Charger", lat:14.6567, lng:121.0281 },
    { name:"BGC Charging Hub", lat:14.5520, lng:121.0487 },
    { name:"Ortigas EV Station", lat:14.5869, lng:121.0614 },
    { name:"Ayala Malls Circuit Makati EV", lat:14.5636, lng:121.0152 },
    { name:"Robinsons Galleria Charger", lat:14.5896, lng:121.0596 },
    { name:"SM Aura EV Station", lat:14.5451, lng:121.0537 },
    { name:"UP Town Center Charging", lat:14.6495, lng:121.0754 },
    { name:"NAIA Terminal 3 EV Chargers", lat:14.5169, lng:121.0146 }
];

// GREEN STATION MARKERS
stations.forEach(s => {
    L.marker([s.lat, s.lng], { icon: greenIcon })
        .addTo(map)
        .bindPopup("⚡ " + s.name);
});


// ===============================
// MAP 2 — ROUTE VISUALIZATION
// ===============================
const routeMap = L.map('routeMap')
.setView([user.lat, user.lng], 13);

L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(routeMap);


// ===============================
// CREATE CLICKABLE STATION TABS
// ===============================
const tabsContainer = document.getElementById("stationTabs");

stations.forEach((station) => {

    const btn = document.createElement("button");
    btn.className = "station-btn";
    btn.innerText = station.name;

    btn.onclick = () => showRoute(station);

    tabsContainer.appendChild(btn);
});


// ===============================
// ROUTING FUNCTION
// ===============================
let routeLine;

async function showRoute(station) {

    // Remove previous route
    if (routeLine) {
        routeMap.removeLayer(routeLine);
    }

    // Remove old markers
    routeMap.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            routeMap.removeLayer(layer);
        }
    });

    // Add user + destination markers
    L.marker([user.lat, user.lng], { icon: redIcon })
        .addTo(routeMap)
        .bindPopup("Your Location");

    L.marker([station.lat, station.lng], { icon: greenIcon })
        .addTo(routeMap)
        .bindPopup(station.name);


    // OSRM ROUTE API
    const url =
`https://router.project-osrm.org/route/v1/driving/
${user.lng},${user.lat};
${station.lng},${station.lat}?overview=full&geometries=geojson`;

    const res = await fetch(url);
    const data = await res.json();

    const coords = data.routes[0].geometry.coordinates
        .map(c => [c[1], c[0]]);

    // RED ROUTE LINE
    routeLine = L.polyline(coords, {
        weight: 6,
        color: "red"
    }).addTo(routeMap);

    routeMap.fitBounds(routeLine.getBounds());

    // ROUTE DATA
    const distance =
        (data.routes[0].distance / 1000).toFixed(1);

    const eta =
        (data.routes[0].duration / 60).toFixed(0);

    const consumption =
        (distance * 0.18).toFixed(1);

    // DISPLAY INFO
    document.getElementById("routeInfo").innerHTML = `
        <div class="route-card">
            <strong>${station.name}</strong><br>
            Distance: ${distance} km<br>
            ETA: ${eta} mins<br>
            Estimated Battery Use: ${consumption}%<br>
            Remaining Battery: ${(battery - consumption).toFixed(1)}%
        </div>
    `;
}