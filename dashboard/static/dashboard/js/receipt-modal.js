function showReceipt() {
  const rows = document.querySelectorAll('.item-row');
  const rItems = document.getElementById('rItems');
  rItems.innerHTML = ""; // Clear previous content

  let subTotal = 0;
  let totalGST = 0;

  rows.forEach((row, index) => {
    const select = row.querySelector('.product-select');
    const qtyInput = row.querySelector('.qty-input');
    if (!select || !qtyInput) return;

    const selectedProduct = PRODUCTS.find(p => p.id == select.value);
    if (!selectedProduct) return;

    const price = parseFloat(selectedProduct.price);
    const gstPercent = parseFloat(selectedProduct.gst_percent || 0);
    const qty = parseInt(qtyInput.value || "1");

    const gstAmountPerItem = (price * gstPercent) / 100;
    const totalPriceWithoutGST = price * qty;
    const totalGSTForItem = gstAmountPerItem * qty;
    const totalPriceWithGST = totalPriceWithoutGST + totalGSTForItem;

    subTotal += totalPriceWithoutGST;
    totalGST += totalGSTForItem;

    const itemLine = document.createElement('p');
    itemLine.textContent = `${selectedProduct.name} — ${qty} × ₹${price.toFixed(2)} + GST = ₹${totalPriceWithGST.toFixed(2)}`;
    rItems.appendChild(itemLine);
  });

  const grandTotal = subTotal + totalGST;

  document.getElementById("rSubTotal").textContent = subTotal.toFixed(2);
  document.getElementById("rGSTAmount").textContent = totalGST.toFixed(2);
  document.getElementById("rGrand").textContent = grandTotal.toFixed(2);

  const paidInput = document.getElementById("amountPaid");
  document.getElementById("rPaid").textContent = paidInput ? parseFloat(paidInput.value || 0).toFixed(2) : "0.00";

  document.getElementById("rName").textContent = document.getElementById("custName")?.textContent || "—";
  document.getElementById("rPhone").textContent = document.getElementById("custPhone")?.textContent || "—";

  // GST fallback logic
  const customerGST = document.getElementById("customerGST")?.value?.trim();
  const managerGST = document.getElementById("gst_number")?.value?.trim();
  const fallbackGST = customerGST || managerGST || '—';

  document.getElementById("rGST").textContent = fallbackGST;

  document.getElementById("receiptModal").style.display = "flex";
}



function printReceipt() {
  const modalContent = document.querySelector("#receiptModal .customer-modal");

  const printWindow = window.open('', '_blank', 'width=800,height=600');
  printWindow.document.write(`
    <html>
      <head>
        <title>Receipt - UNIQUE STORE</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 20px;
            color: #000;
          }
          h3 {
            text-align: center;
            margin-bottom: 20px;
          }
          p {
            margin: 6px 0;
          }
          hr {
            margin: 12px 0;
          }
          .receipt-footer {
            text-align: center;
            margin-top: 30px;
            font-size: 0.85rem;
            color: #555;
          }
        </style>
      </head>
      <body>
        ${modalContent.innerHTML}
        <div class="receipt-footer">Thank you for shopping with UNIQUE STORE!</div>
      </body>
    </html>
  `);

  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  printWindow.close();
}
function closeReceiptModal() {
  const modal = document.getElementById("receiptModal");
  if (modal) {
    modal.style.display = "none";
  }
}

