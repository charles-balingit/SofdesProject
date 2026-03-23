// ======================================
// RANDOM USER LOCATION
// ======================================
const locations = [
    { name: "Quezon City", lat: 14.6760, lng: 121.0437 },
    { name: "Makati", lat: 14.5547, lng: 121.0244 },
    { name: "Pasig", lat: 14.5764, lng: 121.0851 }
];

const user = locations[Math.floor(Math.random()*locations.length)];
const battery = Math.floor(Math.random()*50)+50;

document.getElementById("location").textContent = user.name;
document.getElementById("battery").textContent = battery;


// ======================================
// ICONS
// ======================================
const redIcon = L.icon({
    iconUrl:"https://maps.google.com/mapfiles/ms/icons/red-dot.png",
    iconSize:[32,32],
    iconAnchor:[16,32]
});

const greenIcon = L.icon({
    iconUrl:"https://maps.google.com/mapfiles/ms/icons/green-dot.png",
    iconSize:[32,32],
    iconAnchor:[16,32]
});


// ======================================
// SINGLE MAP
// ======================================
const map = L.map('map').setView([user.lat,user.lng],12);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);


// USER MARKER
L.marker([user.lat,user.lng],{icon:redIcon})
.addTo(map)
.bindPopup("📍 Your Location")
.openPopup();


// ======================================
// NCR CHARGING STATIONS (REAL LOCATIONS)
// ======================================
const stations = [

    // QUEZON CITY
    {name:"SM North EDSA EV",lat:14.6567,lng:121.0281},
    {name:"UP Town Center Charger",lat:14.6495,lng:121.0754},
    {name:"Trinoma EV Station",lat:14.6537,lng:121.0336},

    // MAKATI
    {name:"Circuit Makati EV",lat:14.5636,lng:121.0152},
    {name:"Greenbelt Charging Hub",lat:14.5523,lng:121.0235},
    {name:"Glorietta EV Chargers",lat:14.5510,lng:121.0248},

    // BGC / TAGUIG
    {name:"BGC Charging Hub",lat:14.5520,lng:121.0487},
    {name:"SM Aura EV Station",lat:14.5451,lng:121.0537},
    {name:"Market Market EV",lat:14.5495,lng:121.0563},

    // PASIG / ORTIGAS
    {name:"Ortigas EV Station",lat:14.5869,lng:121.0614},
    {name:"Robinsons Galleria EV",lat:14.5896,lng:121.0596},
    {name:"Estancia Mall Charger",lat:14.5808,lng:121.0606},

    // MANILA
    {name:"Robinsons Manila EV",lat:14.5755,lng:120.9830},
    {name:"SM Manila Charging",lat:14.5906,lng:120.9810},

    // AIRPORT AREA
    {name:"NAIA Terminal 3 EV",lat:14.5169,lng:121.0146}
];


// ======================================
// ADD STATIONS TO MAP
// ======================================
stations.forEach(station => {

    const marker = L.marker(
        [station.lat,station.lng],
        {icon:greenIcon}
    ).addTo(map);

    marker.bindPopup(`
        ⚡ <b>${station.name}</b><br>
        <button onclick="showRoute(${station.lat},${station.lng},'${station.name}')">
            Navigate Here
        </button>
    `);
});


// ======================================
// ROUTING
// ======================================
let routeLine;

async function showRoute(lat,lng,name){

    if(routeLine){
        map.removeLayer(routeLine);
    }

    const url =
`https://router.project-osrm.org/route/v1/driving/
${user.lng},${user.lat};
${lng},${lat}?overview=full&geometries=geojson`;

    const res = await fetch(url);
    const data = await res.json();

    const coords = data.routes[0].geometry.coordinates
        .map(c=>[c[1],c[0]]);

    routeLine = L.polyline(coords,{
        weight:6,
        color:"red"
    }).addTo(map);

    map.fitBounds(routeLine.getBounds());

    const distance=(data.routes[0].distance/1000).toFixed(1);
    const eta=(data.routes[0].duration/60).toFixed(0);
    const consumption=(distance*0.18).toFixed(1);

    document.getElementById("routeInfo").innerHTML=`
        <div class="route-card">
            <strong>${name}</strong><br>
            Distance: ${distance} km<br>
            ETA: ${eta} mins<br>
            Battery Use: ${consumption}%<br>
            Remaining Battery: ${(battery-consumption).toFixed(1)}%
        </div>
    `;
}