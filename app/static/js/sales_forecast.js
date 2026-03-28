let forecastChart = null;

/* ====================================
   BUTTON CLICK
==================================== */
function generateForecast() {

    const vehicle =
        document.getElementById("vehicleSelect").value;

    const months =
        parseInt(document.getElementById("monthSelect").value);

    const forecastData = createMockForecast(months);

    showForecast(vehicle, forecastData);
}


/* ====================================
   MOCK DATA GENERATOR
==================================== */
function createMockForecast(months) {

    const data = [];
    const startDate = new Date(2026, 0, 1);

    let baseValue = 470;

    for (let i = 0; i < months; i++) {

        baseValue += (Math.random() - 0.5) * 20;

        const d = new Date(startDate);
        d.setMonth(d.getMonth() + i);

        data.push({
            date: d.toISOString().slice(0,10),
            forecast: Number(baseValue.toFixed(2))
        });
    }

    return data;
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

    const tbody = document.getElementById("forecastTable");
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