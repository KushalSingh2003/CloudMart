document.addEventListener("DOMContentLoaded", function () {

    /*
     * Data comes directly from Flask/Jinja.
     * Flask gets this data from RDS MySQL.
     */

    const revenueData = revenueTrend || [];
    const ordersData = ordersTrend || [];
    const statusData = orderStatus || [];
    const productsData = bestSelling || [];


    /* =====================================================
       COMMON CHART OPTIONS
       ===================================================== */

    Chart.defaults.font.family =
        "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

    Chart.defaults.color = "#8a909a";


    /* =====================================================
       REVENUE TREND
       ===================================================== */

    const revenueCanvas = document.getElementById("revenueChart");

    if (revenueCanvas && revenueData.length > 0) {

        new Chart(revenueCanvas, {

            type: "line",

            data: {
                labels: revenueData.map(item => item.order_date),

                datasets: [{
                    label: "Revenue",

                    data: revenueData.map(item =>
                        Number(item.revenue)
                    ),

                    borderColor: "#252a34",
                    backgroundColor: "rgba(37, 42, 52, 0.08)",

                    borderWidth: 2,

                    fill: true,

                    tension: 0.35,

                    pointRadius: 3,

                    pointHoverRadius: 5
                }]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                interaction: {
                    intersect: false,
                    mode: "index"
                },

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {
                        callbacks: {
                            label: function (context) {

                                return " ₹" +
                                    Number(context.raw)
                                        .toLocaleString("en-IN", {
                                            minimumFractionDigits: 2
                                        });
                            }
                        }
                    }
                },

                scales: {

                    x: {
                        grid: {
                            display: false
                        },

                        ticks: {
                            maxTicksLimit: 8
                        }
                    },

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: "#eef0f3"
                        },

                        ticks: {
                            callback: function (value) {
                                return "₹" +
                                    Number(value)
                                        .toLocaleString("en-IN");
                            }
                        }
                    }
                }
            }
        });

    }


    /* =====================================================
       ORDERS TREND
       ===================================================== */

    const ordersCanvas = document.getElementById("ordersChart");

    if (ordersCanvas && ordersData.length > 0) {

        new Chart(ordersCanvas, {

            type: "bar",

            data: {

                labels: ordersData.map(item =>
                    item.order_date
                ),

                datasets: [{

                    label: "Orders",

                    data: ordersData.map(item =>
                        Number(item.total_orders)
                    ),

                    backgroundColor: "#d9dde3",

                    borderRadius: 6,

                    borderSkipped: false
                }]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    x: {

                        grid: {
                            display: false
                        },

                        ticks: {
                            maxTicksLimit: 8
                        }
                    },

                    y: {

                        beginAtZero: true,

                        ticks: {
                            precision: 0
                        },

                        grid: {
                            color: "#eef0f3"
                        }
                    }
                }
            }
        });

    }


    /* =====================================================
       ORDER STATUS
       ===================================================== */

    const statusCanvas =
        document.getElementById("orderStatusChart");

    if (statusCanvas && statusData.length > 0) {

        new Chart(statusCanvas, {

            type: "doughnut",

            data: {

                labels: statusData.map(item =>
                    item.status
                ),

                datasets: [{

                    data: statusData.map(item =>
                        Number(item.total)
                    ),

                    backgroundColor: [
                        "#252a34",
                        "#8c939d",
                        "#c7a66a",
                        "#b86f6f",
                        "#bfc4cb"
                    ],

                    borderWidth: 0,

                    hoverOffset: 5
                }]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                cutout: "68%",

                plugins: {

                    legend: {

                        position: "bottom",

                        labels: {

                            usePointStyle: true,

                            pointStyle: "circle",

                            padding: 18,

                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });

    }


    /* =====================================================
       BEST-SELLING PRODUCTS
       ===================================================== */

    const productsCanvas =
        document.getElementById("bestSellingChart");

    if (productsCanvas && productsData.length > 0) {

        new Chart(productsCanvas, {

            type: "bar",

            data: {

                labels: productsData.map(item =>
                    item.product_name
                ),

                datasets: [{

                    label: "Units Sold",

                    data: productsData.map(item =>
                        Number(item.total_quantity)
                    ),

                    backgroundColor: "#252a34",

                    borderRadius: 6,

                    borderSkipped: false
                }]
            },

            options: {

                indexAxis: "y",

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }
                },

                scales: {

                    x: {

                        beginAtZero: true,

                        ticks: {
                            precision: 0
                        },

                        grid: {
                            color: "#eef0f3"
                        }
                    },

                    y: {

                        grid: {
                            display: false
                        },

                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });

    }


    /* =====================================================
       EMPTY CHART STATES
       ===================================================== */

    if (revenueCanvas && revenueData.length === 0) {
        showChartEmptyState(
            revenueCanvas,
            "No revenue data available yet."
        );
    }

    if (ordersCanvas && ordersData.length === 0) {
        showChartEmptyState(
            ordersCanvas,
            "No order data available yet."
        );
    }

    if (statusCanvas && statusData.length === 0) {
        showChartEmptyState(
            statusCanvas,
            "No order status data available."
        );
    }

    if (productsCanvas && productsData.length === 0) {
        showChartEmptyState(
            productsCanvas,
            "No product sales data available."
        );
    }


    function showChartEmptyState(canvas, message) {

        const container = canvas.parentElement;

        canvas.style.display = "none";

        const messageElement =
            document.createElement("div");

        messageElement.className =
            "chart-empty-state";

        messageElement.textContent = message;

        container.appendChild(messageElement);
    }

});