// =========================================================
// CURRENT DATE
// =========================================================

function displayCurrentDate() {

    const dateElement =
        document.getElementById("currentDate");

    const today = new Date();

    dateElement.textContent =
        today.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );
}


// =========================================================
// DASHBOARD DATA
// =========================================================

const dashboardData = {

    total_orders: 2,

    total_sales: 0,

    completed_orders: 0,

    pending_orders: 2,

    cancelled_orders: 0,

    best_selling_product: "No sales yet",

    best_selling_quantity: 0,

    orders: [

        {
            order_id: 1,
            customer_name: "Rahul Sharma",
            amount: 69993.00,
            status: "PENDING",
            created_at: "2026-09-15 12:00:00"
        },

        {
            order_id: 2,
            customer_name: "Rahul Sharma",
            amount: 669933.00,
            status: "PENDING",
            created_at: "2026-09-15 12:05:00"
        }

    ]

};


// =========================================================
// UPDATE STATISTICS
// =========================================================

function updateStatistics(data) {

    document.getElementById(
        "totalOrders"
    ).textContent = data.total_orders;


    document.getElementById(
        "totalSales"
    ).textContent =
        `₹${Number(data.total_sales).toFixed(2)}`;


    document.getElementById(
        "completedOrders"
    ).textContent = data.completed_orders;


    document.getElementById(
        "cancelledOrders"
    ).textContent = data.cancelled_orders;


    document.getElementById(
        "completedCount"
    ).textContent = data.completed_orders;


    document.getElementById(
        "pendingCount"
    ).textContent = data.pending_orders;


    document.getElementById(
        "cancelledCount"
    ).textContent = data.cancelled_orders;


    document.getElementById(
        "bestProduct"
    ).textContent =
        data.best_selling_product;


    document.getElementById(
        "bestProductQuantity"
    ).textContent =
        data.best_selling_quantity;
}


// =========================================================
// UPDATE ORDERS TABLE
// =========================================================

function updateOrdersTable(orders) {

    const table =
        document.getElementById("ordersTable");


    if (!orders || orders.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="5" class="loading">
                    No orders found today
                </td>
            </tr>
        `;

        return;
    }


    table.innerHTML = "";


    orders.forEach(order => {

        const row =
            document.createElement("tr");


        let statusClass = "";

        const status =
            order.status.toLowerCase();


        if (status === "completed") {

            statusClass =
                "status-completed";

        } else if (status === "pending") {

            statusClass =
                "status-pending";

        } else if (status === "cancelled") {

            statusClass =
                "status-cancelled";
        }


        row.innerHTML = `

            <td>
                #${order.order_id}
            </td>

            <td>
                ${order.customer_name}
            </td>

            <td>
                ₹${Number(order.amount).toFixed(2)}
            </td>

            <td>
                <span
                    class="status-badge ${statusClass}"
                >
                    ${order.status}
                </span>
            </td>

            <td>
                ${order.created_at}
            </td>

        `;


        table.appendChild(row);

    });
}


// =========================================================
// LOAD DASHBOARD
// =========================================================

function loadDashboard() {

    updateStatistics(
        dashboardData
    );


    updateOrdersTable(
        dashboardData.orders
    );


    document.getElementById(
        "lastUpdated"
    ).textContent =
        new Date().toLocaleTimeString(
            "en-IN"
        );
}


// =========================================================
// INITIALIZE
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        displayCurrentDate();

        loadDashboard();

    }
);