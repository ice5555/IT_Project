document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.transaction-row').forEach(row => {
        row.addEventListener('click', function() {
            const txId = this.dataset.id;
            fetch(`/transaction/detail/${txId}/`)
              .then(response => response.text())
              .then(html => {
                  document.getElementById('transactionModalBody').innerHTML = html;
                  var myModal = new bootstrap.Modal(document.getElementById('transactionModal'));
                  myModal.show();
              });
        });
    });
});
