$(document).ready(function() {
    $(".transaction-row").click(function() {
        const txId = $(this).data("id"); // 获取 data-id
        $.get(`/transaction/detail/${txId}/`, function(html) { // 发送 AJAX GET 请求
            $("#transactionModalBody").html(html); // 更新模态框 HTML
            $("#transactionModal").modal("show"); // 显示 Bootstrap 模态框
        });
    });
});



// ======================================== //
const hiddenAccountField = document.getElementById('hiddenAccountField');
const hiddenCategoryField = document.getElementById('hiddenCategoryField');
const hiddenAmountField = document.getElementById('hiddenAmountField');
const hiddenDateField = document.getElementById('hiddenDateField');

// ==================== 1. Category Icons ==================== //
document.querySelectorAll('.icon-item').forEach(icon => {
    icon.addEventListener('click', function(){
        document.querySelectorAll('.icon-item').forEach(i => i.classList.remove('selected'));
        this.classList.add('selected');
        hiddenCategoryField.value = this.dataset.cat;
    });
});

// ==================== 2. Account Drop Down Menu  ==================== //
const visibleAccountSelect = document.getElementById('visibleAccountSelect');
visibleAccountSelect.addEventListener('change', function(){
    hiddenAccountField.value = this.value; 
});
hiddenAccountField.value = visibleAccountSelect.value;

// ==================== 3. Number Keypad ==================== //
const keypad = document.getElementById('keypad');
const amountDisplay = document.getElementById('amountDisplay');
keypad.addEventListener('click', function(e){
    if(!e.target.classList.contains('key')) return;
    let action = e.target.getAttribute('data-action');
    let cur = amountDisplay.textContent;
    if(!action){
        if(cur === '0') cur = '';
        amountDisplay.textContent = cur + e.target.textContent;
    } else if(action === 'dot'){
        if(!cur.includes('.')){
            amountDisplay.textContent = cur + '.';
        }
    } else if(action === 'clear'){
        amountDisplay.textContent = '0';
    }
    hiddenAmountField.value = amountDisplay.textContent;
});
hiddenAmountField.value = amountDisplay.textContent;

// ==================== 4. Custom Calendar ==================== //
const calendar = document.getElementById('calendar');
function renderCalendar(year, month){
    const date = new Date(year, month, 1);
    const firstDay = date.getDay();
    const lastDate = new Date(year, month+1, 0).getDate();
    let html = `<div class="cal-header d-flex justify-content-between align-items-center">
                    <span>${date.toLocaleString('default', {month:'long'})} ${year}</span>
                    <div>
                        <button class="btn btn-sm btn-light" id="prevMonthBtn">&laquo;</button>
                        <button class="btn btn-sm btn-light" id="nextMonthBtn">&raquo;</button>
                    </div>
                </div>`;
    html += `<div class="cal-grid">`;
    const daysOfWeek = ['Su','Mo','Tu','We','Th','Fr','Sa'];
    daysOfWeek.forEach(d => html += `<div class="cal-day-header">${d}</div>`);
    for(let i=0; i<firstDay; i++){
        html += `<div class="cal-cell empty"></div>`;
    }
    for(let d=1; d<=lastDate; d++){
        html += `<div class="cal-cell day" data-date="${year}-${('0'+(month+1)).slice(-2)}-${('0'+d).slice(-2)}">${d}</div>`;
    }
    html += `</div>`;
    calendar.innerHTML = html;

    calendar.querySelectorAll('.day').forEach(cell => {
        cell.addEventListener('click', function(){
            calendar.querySelectorAll('.day').forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            hiddenDateField.value = this.dataset.date;
        });
    });

    document.getElementById('prevMonthBtn').addEventListener('click', () => {
        let newMonth = month===0 ? 11 : month-1;
        let newYear = month===0 ? year-1 : year;
        renderCalendar(newYear, newMonth);
    });
    document.getElementById('nextMonthBtn').addEventListener('click', () => {
        let newMonth = month===11 ? 0 : month+1;
        let newYear = month===11 ? year+1 : year;
        renderCalendar(newYear, newMonth);
    });
}

let today = new Date();
renderCalendar(today.getFullYear(), today.getMonth());

document.getElementById('saveBtn').addEventListener('click', function(){
    document.getElementById('hiddenForm').submit();
});

