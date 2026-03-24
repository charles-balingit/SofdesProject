// =======================================
// USER SIMULATION
// =======================================

const locations = [
    { name:"Quezon City", lat:14.6760, lng:121.0437 },
    { name:"Makati", lat:14.5547, lng:121.0244 },
    { name:"Pasig", lat:14.5764, lng:121.0851 }
];

const user = locations[Math.floor(Math.random()*locations.length)];
const battery = Math.floor(Math.random()*26)+5; // 5-30%

document.getElementById("location").textContent = user.name;
document.getElementById("battery").textContent = battery;


// =======================================
// DESTINATION (SCENARIO)
// =======================================

const destination = {
    name:"NAIA Airport",
    lat:14.5086,
    lng:121.0198
};


// =======================================
// EV MODEL
// =======================================

const MAX_RANGE = 50; // km full charge
const availableRange = (battery/100)*MAX_RANGE;


// =======================================
// MAP SETUP
// =======================================

const map = L.map('map').setView([14.5995,120.9842], 11);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);


// ICONS
const redIcon = new L.Icon({
    iconUrl:'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
    iconSize:[32,32]
});

const greenIcon = new L.Icon({
    iconUrl:'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
    iconSize:[32,32]
});

const blueIcon = new L.Icon({
    iconUrl:'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
    iconSize:[32,32]
});


// USER MARKER
L.marker([user.lat,user.lng],{icon:redIcon})
.addTo(map)
.bindPopup("Your Location")
.openPopup();


// DESTINATION MARKER
L.marker([destination.lat,destination.lng],{icon:blueIcon})
.addTo(map)
.bindPopup("Destination");


// =======================================
// NCR CHARGING STATIONS
// =======================================

const stations = [

{ name:"SM North EDSA Charger", lat:14.6567, lng:121.0281 },
{ name:"Trinoma EV Station", lat:14.6537, lng:121.0336 },
{ name:"Vertis North Charging", lat:14.6590, lng:121.0390 },
{ name:"BGC Charging Hub", lat:14.5520, lng:121.0487 },
{ name:"Market Market Charger", lat:14.5508, lng:121.0560 },
{ name:"SM Aura EV Station", lat:14.5453, lng:121.0535 },
{ name:"Ortigas EV Station", lat:14.5869, lng:121.0614 },
{ name:"Robinsons Galleria Charger", lat:14.5896, lng:121.0596 },
{ name:"SM Megamall Charging", lat:14.5850, lng:121.0565 },
{ name:"MOA EV Charging", lat:14.5350, lng:120.9822 },
{ name:"Newport Mall Charger", lat:14.5176, lng:121.0180 },
{ name:"Greenbelt Charging", lat:14.5523, lng:121.0222 }
];


// ADD STATION MARKERS
stations.forEach(s=>{
    L.marker([s.lat,s.lng],{icon:greenIcon})
        .addTo(map)
        .bindPopup(s.name);
});


// =======================================
// ROUTING FUNCTIONS
// =======================================

let routeLine;

async function getRouteData(a,b){

    const url =
`https://router.project-osrm.org/route/v1/driving/
${a.lng},${a.lat};
${b.lng},${b.lat}?overview=full&geometries=geojson`;

    const res = await fetch(url);
    return await res.json();
}


async function drawRoute(a,b){

    if(routeLine){
        map.removeLayer(routeLine);
    }

    const data = await getRouteData(a,b);

    const coords =
        data.routes[0].geometry.coordinates
        .map(c=>[c[1],c[0]]);

    routeLine = L.polyline(coords,{
        weight:6
    }).addTo(map);

    map.fitBounds(routeLine.getBounds());

    return data.routes[0];
}


// =======================================
// INTELLIGENT SMART ROUTING
// =======================================

async function smartRouting(){

    const routeToDest = await drawRoute(user,destination);

    const destDistance = routeToDest.distance/1000;

    // CAN REACH DESTINATION?
    if(availableRange >= destDistance){

        document.getElementById("routeInfo").innerHTML=`
            ✅ Destination reachable without charging
            <br>Distance: ${destDistance.toFixed(1)} km
            <br>Available Range: ${availableRange.toFixed(1)} km
        `;

        return;
    }

    // NEED CHARGING
    let bestStation=null;
    let bestDistance=Infinity;

    for(const station of stations){

        const data = await getRouteData(user,station);
        const distance=data.routes[0].distance/1000;

        if(distance <= availableRange && distance<bestDistance){
            bestDistance=distance;
            bestStation=station;
        }
    }

    if(bestStation){

        await drawRoute(user,bestStation);

        document.getElementById("routeInfo").innerHTML=`
            ⚠ Battery insufficient!
            <br><strong>Recommended Charging Station:</strong>
            ${bestStation.name}
            <br>Reachable Distance: ${bestDistance.toFixed(1)} km
            <br>Available Range: ${availableRange.toFixed(1)} km
        `;
    }
}


// RUN SYSTEM
smartRouting();