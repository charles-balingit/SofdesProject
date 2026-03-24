// =======================================
// RANDOM USER + DESTINATION
// =======================================

const locations = [
    { name:"Quezon City", lat:14.6760, lng:121.0437 },
    { name:"Makati", lat:14.5547, lng:121.0244 },
    { name:"Pasig", lat:14.5764, lng:121.0851 }
];

const destinations = [
    { name:"NAIA Airport", lat:14.5086, lng:121.0198 },
    { name:"UP Diliman", lat:14.6537, lng:121.0684 },
    { name:"MOA Complex", lat:14.5350, lng:120.9822 }
];

const user = locations[Math.floor(Math.random()*locations.length)];
const destination = destinations[Math.floor(Math.random()*destinations.length)];

// battery 5–30%
const battery = Math.floor(Math.random()*26)+5;

document.getElementById("location").textContent = user.name;
document.getElementById("destination").textContent = destination.name;
document.getElementById("battery").textContent = battery;


// =======================================
// MAP SETUP
// =======================================

const map = L.map('map').setView([user.lat,user.lng],12);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);


// =======================================
// CUSTOM ICONS
// =======================================

const userIcon = L.icon({
    iconUrl:"https://maps.google.com/mapfiles/ms/icons/red-dot.png",
    iconSize:[32,32]
});

const stationIcon = L.icon({
    iconUrl:"https://maps.google.com/mapfiles/ms/icons/green-dot.png",
    iconSize:[32,32]
});

const destIcon = L.icon({
    iconUrl:"https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
    iconSize:[32,32]
});


// markers
L.marker([user.lat,user.lng],{icon:userIcon})
.addTo(map).bindPopup("Your Location").openPopup();

L.marker([destination.lat,destination.lng],{icon:destIcon})
.addTo(map).bindPopup("Destination");


// =======================================
// NCR CHARGING STATIONS
// =======================================

const stations = [
 {name:"SM North EDSA",lat:14.6567,lng:121.0281},
 {name:"BGC Stopover",lat:14.5520,lng:121.0487},
 {name:"Ortigas Center",lat:14.5869,lng:121.0614},
 {name:"SM Megamall",lat:14.5849,lng:121.0567},
 {name:"Robinsons Galleria",lat:14.5896,lng:121.0607},
 {name:"Greenbelt Makati",lat:14.5510,lng:121.0220},
 {name:"MOA Charging Hub",lat:14.5350,lng:120.9822},
 {name:"UP Town Center",lat:14.6495,lng:121.0755}
];

stations.forEach(s=>{
    L.marker([s.lat,s.lng],{icon:stationIcon})
    .addTo(map)
    .bindPopup(s.name);
});


// =======================================
// ROUTING FUNCTION
// =======================================

let routeLine;

async function getRoute(start,end,color="blue"){

    const url =
`https://router.project-osrm.org/route/v1/driving/
${start.lng},${start.lat};
${end.lng},${end.lat}?overview=full&geometries=geojson`;

    const res = await fetch(url);
    const data = await res.json();

    const coords = data.routes[0].geometry.coordinates
        .map(c=>[c[1],c[0]]);

    const line = L.polyline(coords,{
        weight:6,
        color:color
    }).addTo(map);

    return {
        distance:data.routes[0].distance/1000,
        duration:data.routes[0].duration/60,
        line
    };
}


// =======================================
// SMART DECISION SYSTEM
// =======================================

async function smartRouting(){

    const decisionBox = document.getElementById("decisionBox");

    // route directly to destination
    const direct = await getRoute(user,destination,"blue");

    const neededBattery = direct.distance * 0.18;

    // enough battery
    if(battery > neededBattery){

        decisionBox.innerHTML = `
        ✅ Battery sufficient.<br>
        Direct route selected.<br>
        Distance: ${direct.distance.toFixed(1)} km
        `;

        return;
    }

    // remove direct line
    map.removeLayer(direct.line);

    decisionBox.innerHTML =
    "⚠ Battery insufficient. Searching optimal charging station...";

    // find nearest station
    let bestStation=null;
    let bestDistance=999;

    for(const s of stations){

        const d =
        Math.sqrt(
            (user.lat-s.lat)**2 +
            (user.lng-s.lng)**2
        );

        if(d < bestDistance){
            bestDistance=d;
            bestStation=s;
        }
    }

    // ROUTE 1: USER → STATION
    const leg1 = await getRoute(user,bestStation,"red");

    // simulate recharge
    const rechargeBattery = 90;

    // ROUTE 2: STATION → DESTINATION
    const leg2 = await getRoute(bestStation,destination,"green");

    decisionBox.innerHTML = `
        Intelligent Decision:<br><br>

        🔋 Battery (${battery}%) insufficient.<br>
        ⚡ Recommended Stop: <b>${bestStation.name}</b><br><br>

        Route Plan:<br>
        🚗 To Station: ${leg1.distance.toFixed(1)} km<br>
        🔌 Recharge → ${rechargeBattery}%<br>
        🏁 Continue: ${leg2.distance.toFixed(1)} km
    `;
}

smartRouting();