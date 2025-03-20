document.addEventListener('DOMContentLoaded', function() {
    // 1. 获取后端传过来的数据
    const analyticsData = document.getElementById('analytics-data');
    
    // 用 JSON.parse() 将字符串转换为 JavaScript 对象/数组
    const incomeTrendDates = JSON.parse(analyticsData.dataset.incomeTrendDates);
    const incomeTrendValues = JSON.parse(analyticsData.dataset.incomeTrendValues);
    const expenseTrendValues = JSON.parse(analyticsData.dataset.expenseTrendValues);
    const categoryDistribution = JSON.parse(analyticsData.dataset.categoryDistribution);
    const accountData = JSON.parse(analyticsData.dataset.accountData);
  
    // 2. 收支趋势图（折线图）
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    const trendChart = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: incomeTrendDates,  // 日期列表
        datasets: [
          {
            label: 'Income',
            data: incomeTrendValues,
            borderColor: 'green',
            fill: false
          },
          {
            label: 'Expense',
            data: expenseTrendValues,
            borderColor: 'red',
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  
    // 3. 类别占比（饼图）
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    const categoryLabels = Object.keys(categoryDistribution);
    const categoryValues = Object.values(categoryDistribution);
    const categoryChart = new Chart(categoryCtx, {
      type: 'pie',
      data: {
        labels: categoryLabels,
        datasets: [{
          data: categoryValues,
          backgroundColor: [
            '#007bff', '#28a745', '#ffc107', '#dc3545',
            '#17a2b8', '#6f42c1', '#fd7e14', '#20c997', '#343a40'
          ],
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  
    // 4. 各账户余额变化（折线图）
    const accountCtx = document.getElementById('accountChart').getContext('2d');
    const accountLabels = Object.keys(accountData);
    
    // 将初始余额和当前余额转成数组
    // 这里可以根据你的数据结构做相应调整
    const accountChart = new Chart(accountCtx, {
      type: 'line',
      data: {
        labels: ['30 Days Ago', 'Now'],
        datasets: accountLabels.map(name => ({
          label: name,
          data: [
            accountData[name].initial,
            accountData[name].current
          ],
          // 为每条线随机生成颜色
          borderColor: '#' + Math.floor(Math.random()*16777215).toString(16),
          fill: false
        }))
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: false }
        }
      }
    });
  });
  