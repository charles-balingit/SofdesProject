async function generateForecast() {

    const vehicle = document.getElementById("vehicleSelect").value;
    const months = document.getElementById("monthSelect").value;

    const res = await fetch("/generate-forecast", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            vehicle: vehicle,
            months: months
        })
    });

    const data = await res.json();

    const dates = data.map(d => d.date);
    const values = data.map(d => d.forecast);

    // Plotly chart
    Plotly.newPlot("forecastChart", [{
        x: dates,
        y: values,
        type: "scatter",
        mode: "lines+markers"
    }], {
        template: "plotly_dark",
        title: `Sales Forecast — ${vehicle}`
    });

    // Table
    const tbody = document.querySelector("#forecastTable tbody");
    tbody.innerHTML = "";

    data.forEach(row => {
        tbody.innerHTML += `
            <tr>
                <td>${row.date}</td>
                <td>${row.forecast.toFixed(4)}</td>
            </tr>`;
    });
}