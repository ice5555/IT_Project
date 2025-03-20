document.addEventListener('DOMContentLoaded', function() {
    // 初始化类别饼图
    const ctx = document.getElementById('categoryChart').getContext('2d');
    window.categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(categoryDistribution),
            datasets: [{
                data: Object.values(categoryDistribution),
                backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545', '#17a2b8'],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, 

            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });

    // 绑定时间筛选按钮事件
    const timeFilterButtons = document.querySelectorAll(".btn-time");
    timeFilterButtons.forEach(btn => {
        btn.addEventListener("click", function() {
            timeFilterButtons.forEach(b => b.classList.remove("active"));
            this.classList.add("active");
            const range = this.textContent.replace(/\s/g, '_').toLowerCase();
            fetch(`/transactions/filter_ajax/?range=${range}`)
                .then(response => response.json())
                .then(data => {
                    console.log("Returned data:", data);
                    updateDashboard(data);
                })
                .catch(err => console.error("Error fetching data:", err));
        });
    });
});

// 更新仪表板数据
function updateDashboard(data) {
    document.getElementById("incomeValue").textContent = `£${parseFloat(data.total_income).toFixed(2)}`;
    document.getElementById("expenseValue").textContent = `£${parseFloat(data.total_expense).toFixed(2)}`;
    document.getElementById("balanceValue").textContent = `£${parseFloat(data.total_balance).toFixed(2)}`;
    document.getElementById("budgetRemainingValue").textContent = `£${parseFloat(data.budget_remaining).toFixed(2)}`;
    updatePieChart(data.category_distribution);
    
    // 更新最近交易表格
    const tbody = document.getElementById("lastTxTableBody");
    tbody.innerHTML = "";
    data.recent_transactions.forEach(tx => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${tx.category}</td>
          <td>${tx.account}</td>
          <td>${tx.date}</td>
          <td class="text-end">${tx.amount < 0 ? 
              '<span class="money-text negative">£' + parseFloat(tx.amount).toFixed(2) + '</span>' 
              : '<span class="money-text positive">£' + parseFloat(tx.amount).toFixed(2) + '</span>'}
          </td>`;
        tbody.appendChild(row);
    });
}

// 更新饼图数据
function updatePieChart(categoryDist) {
    const labels = Object.keys(categoryDist);
    const values = Object.values(categoryDist);
    window.categoryChart.data.labels = labels;
    window.categoryChart.data.datasets[0].data = values;
    window.categoryChart.update();
}
