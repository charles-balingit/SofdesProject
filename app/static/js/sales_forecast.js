let forecastChart = null;

/* ====================================
   BUTTON CLICK (NOW CALLS MODEL API)
==================================== */
async function generateForecast() {

    const vehicle =
        document.getElementById("vehicleSelect").value;

    const months =
        parseInt(document.getElementById("monthSelect").value);

    try {

        const response = await fetch("/api/forecast", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                vehicle: vehicle,
                horizon: months
            })
        });

        const result = await response.json();

        showForecast(vehicle, result.forecast);

    } catch (err) {
        console.error(err);
        alert("Forecast service unavailable.");
    }
}


/* ====================================
   DISPLAY RESULTS
==================================== */
function showForecast(vehicle, data) {

    document.getElementById("forecastResults").style.display = "block";

    document.getElementById("forecastTitle").innerText =
        `Sales Forecast — ${vehicle}`;

    const labels = data.map(d => d.date);
    const values = data.map(d => d.forecast);

    renderChart(labels, values);
    renderTable(data);
}


/* ====================================
   CHART RENDER
==================================== */
function renderChart(labels, values) {

    const ctx = document.getElementById("forecastChart");

    if (forecastChart) {
        forecastChart.destroy();
    }

    forecastChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Forecast",
                data: values,
                tension: 0.35,
                borderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}


/* ====================================
   TABLE RENDER
==================================== */
function renderTable(rows) {

    const tbody =
        document.querySelector("#forecastTable tbody");

    tbody.innerHTML = "";

    rows.forEach(r => {

        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${r.date}</td>
            <td>${r.forecast}</td>
        `;

        tbody.appendChild(tr);
    });
}