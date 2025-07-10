document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('orderForm');
  if (!form) return;

  const customerPhoneInput = document.getElementById('customerPhone');
  if (customerPhoneInput) {
    customerPhoneInput.addEventListener('click', () => {
      const customerModal = document.getElementById('customerModal');
      if (customerModal) {
        customerModal.style.display = 'flex';
      }
    });
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const customerId = document.getElementById('customer_id').value;
    const customerName = document.getElementById('custName').textContent;
    const customerPhone = document.getElementById('custPhone').textContent.replace(/\D/g, '');
    const customerGST = document.getElementById('custGST').textContent;
    const gstInput = document.getElementById('gst_number').value;
    const branchId = document.getElementById('branchSelect').value;

    const total = parseFloat(document.getElementById('grandTotal').value) || 0;
    const paid = parseFloat(document.getElementById('amountPaid').value) || 0;

    const rows = document.querySelectorAll('.item-row');
    const items = [];

    rows.forEach(row => {
      const productId = row.querySelector('select.product-select')?.value;
      const qty = parseInt(row.querySelector('input.qty-input')?.value);
      if (productId && qty > 0) {
        items.push({ product_id: productId, quantity: qty });
      }
    });

    if (!items.length) {
      alert("⚠️ Please add at least one item.");
      return;
    }

    const payload = {
      branch_id: branchId,
      customer_id: customerId || null,
      customer_name: customerName,
      customer_phone: customerPhone,
      customer_gst: customerGST !== '—' ? customerGST : '',
      total,
      paid,
      gst_input: gstInput,
      items
    };

    try {
      const editingSaleId = document.getElementById('editing-sale-id')?.value;
      const url = editingSaleId
        ? `/orders/edit/${editingSaleId}/save/`
        : '/orders/new/';

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      if (result.sale_id) {
  // Optional: still show receipt preview
  showReceiptPreview(customerName, customerPhone, customerGST, items, total, paid);

  // Auto-open print-optimized receipt for thermal
  const url = `/orders/thermal-receipt/${result.sale_id}/`;
  const win = window.open(url, '_blank', 'width=400,height=600');

  // Optional WhatsApp send
  sendWhatsAppReceipt(customerPhone, customerName, total, paid);
}else {
        alert(result.error || "❌ Something went wrong!");
      }
    } catch (err) {
      console.error("Order failed:", err);
      alert("❌ Failed to submit order. Try again.");
    }
  });

  function getCSRFToken() {
    const name = 'csrftoken';
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
  }

  // 🧾 Show Receipt Modal
  window.showReceiptPreview = function (name, phone, gst, items, total, paid) {
    const rows = document.querySelectorAll('.item-row');
    const rItems = document.getElementById('rItems');
    rItems.innerHTML = "";

    rows.forEach(row => {
      const select = row.querySelector('.product-select');
      const qty = parseInt(row.querySelector('.qty-input').value) || 0;
      const price = parseFloat(select.selectedOptions[0]?.dataset.price || 0);
      const itemName = select.selectedOptions[0]?.textContent;
      const lineTotal = qty * price;

      const itemLine = document.createElement('p');
      itemLine.textContent = `${itemName} — ${qty} × ₹${price.toFixed(2)} = ₹${lineTotal.toFixed(2)}`;
      rItems.appendChild(itemLine);
    });

    document.getElementById("rGrand").textContent = total.toFixed(2);
    document.getElementById("rPaid").textContent = paid.toFixed(2);
    document.getElementById("rName").textContent = name || "—";
    document.getElementById("rPhone").textContent = phone || "—";
    document.getElementById("rGST").textContent = gst || "—";
    document.getElementById("rDate").textContent = new Date().toLocaleString();

    document.getElementById("receiptModal").style.display = "flex";
  };

window.printReceipt = function (saleId) {
  const printWindow = window.open(`/orders/thermal-receipt/${saleId}`, '_blank', 'width=400,height=600');

  if (!printWindow) {
    alert("❌ Popup was blocked! Please allow popups for this site.");
    return;
  }

  // ✅ Let the thermal receipt template do the printing itself
};



  // 📱 WhatsApp Receipt
  function sendWhatsAppReceipt(phone, name, total, paid) {
    if (!phone || phone.length < 10) return;

    const now = new Date().toLocaleString();
    const msg = `Hello ${name}, thank you for shopping at UNIQUE STORE!\nDate: ${now}\nTotal: ₹${total}\nPaid: ₹${paid}\nVisit again!`;
    const encoded = encodeURIComponent(msg);
    const url = `https://wa.me/91${phone}?text=${encoded}`;
    window.open(url, '_blank');
  }
});
