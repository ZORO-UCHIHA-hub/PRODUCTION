document.addEventListener("DOMContentLoaded", function () {
  // Add Item Row
window.addItemRow = function () {
  const itemList = document.getElementById("itemList");

  const row = document.createElement("div");
  row.className = "item-row";
  row.style.display = "flex";
  row.style.gap = "1rem";
  row.style.marginBottom = "1rem";

  const productSelect = document.createElement("select");
  productSelect.className = "product-select";
  productSelect.required = true;
  productSelect.style.flex = "2";

  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = "-- Select Product --";
  productSelect.appendChild(blank);

  PRODUCTS.forEach(prod => {
    const priceWithGST = prod.price * (1 + prod.gst_percent / 100);
    const option = document.createElement("option");
    option.value = prod.id;
    option.textContent = `${prod.name} (₹${priceWithGST.toFixed(2)})`;
    option.dataset.price = priceWithGST.toFixed(2);
    option.dataset.base = prod.price;
    option.dataset.gst = prod.gst_percent;
    productSelect.appendChild(option);
  });

  const qtyInput = document.createElement("input");
  qtyInput.type = "number";
  qtyInput.min = 1;
  qtyInput.value = 1;
  qtyInput.className = "qty-input";
  qtyInput.style.flex = "1";

  const priceDisplay = document.createElement("span");
  priceDisplay.className = "price-display";
  priceDisplay.style.flex = "1";
  priceDisplay.textContent = "₹0.00";

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.textContent = "✖";
  removeBtn.onclick = () => {
    row.remove();
    updateTotal();
  };

  row.append(productSelect, qtyInput, priceDisplay, removeBtn);
  itemList.appendChild(row);

  $(productSelect).select2({
    placeholder: "-- Select Product --",
    width: "100%"
  });

  productSelect.addEventListener("change", () => {
    const selected = productSelect.selectedOptions[0];
    priceDisplay.textContent = selected ? `₹${selected.dataset.price}` : "₹0.00";
    updateTotal();
    syncLatestRow();
  });

  qtyInput.addEventListener("input", () => {
    updateTotal();
    syncLatestRow();
  });

  // ✅ Trigger change immediately to show price
  productSelect.dispatchEvent(new Event("change"));
};



  // Sync inputs
  window.syncLatestRow = function () {
    const rows = document.querySelectorAll(".item-row");
    if (!rows.length) return;

    const lastRow = rows[rows.length - 1];
    const qtyInput = lastRow.querySelector(".qty-input");
    const select = lastRow.querySelector(".product-select");

    const price = parseFloat(select.selectedOptions[0]?.dataset.price || 0);
    const qty = parseInt(qtyInput.value || 1);

    const total = price * qty;

    document.getElementById("itemPrice").value = price.toFixed(2);
    document.getElementById("itemQty").value = qty;
    document.getElementById("totalAmount").value = total.toFixed(2);

    document.getElementById("itemQty").oninput = () => {
      qtyInput.value = document.getElementById("itemQty").value;
      updateTotal();
    };
  };

  // Calculate totals
window.updateTotal = function () {
  const rows = document.querySelectorAll(".item-row");
  let subTotal = 0;
  let totalGST = 0;

  rows.forEach(row => {
    const select = row.querySelector(".product-select");
    const qty = parseInt(row.querySelector(".qty-input")?.value || 0);
    const product = PRODUCTS.find(p => p.id == select.value);
    if (!product) return;

    const basePrice = parseFloat(product.price);
    const gst = parseFloat(product.gst_percent);
    const lineTotal = basePrice * qty;
    const gstAmount = (basePrice * gst / 100) * qty;

    subTotal += lineTotal;
    totalGST += gstAmount;
  });

  const totalWithGST = subTotal + totalGST;

  // Update calculated values
  document.getElementById("grandTotal").value = subTotal.toFixed(2);

  const totalWithGSTField = document.getElementById("totalWithGST");

  if (!totalWithGSTField.matches(":focus")) {
    totalWithGSTField.value = totalWithGST.toFixed(2); // If not manually edited, update
  }

  syncLatestRow();
};


  // Handle form submit
  const form = document.getElementById("orderForm");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const customerId = document.getElementById('customer_id').value;
    const customerName = document.getElementById('custName').textContent;
    const customerPhone = document.getElementById('custPhone').textContent.replace(/\D/g, '');
    const customerGST = document.getElementById('custGST').textContent;
    const gstInput = document.getElementById('gst_number').value;
    const branchId = document.getElementById('branchSelect').value;
    const total = parseFloat(document.getElementById('totalWithGST').value) || 0;
    const paymentMethod = document.getElementById('paymentMethod').value;
    const paid = parseFloat(document.getElementById('amountPaid').value) || 0;

    const items = [];
    document.querySelectorAll('.item-row').forEach(row => {
      const productId = row.querySelector('.product-select')?.value;
      const qty = parseInt(row.querySelector('.qty-input')?.value || "0");
      if (productId && qty > 0) {
        items.push({ product_id: productId, quantity: qty });
      }
    });

    if (!items.length) return alert("⚠️ Please add at least one item.");

    const payload = {
      branch_id: branchId,
      customer_id: customerId || null,
      customer_name: customerName,
      customer_phone: customerPhone,
      customer_gst: customerGST !== '—' ? customerGST : '',
      total,
      paid,
      gst_input: gstInput,
      items,
      payment_method: paymentMethod
    };

    try {
      const editingSaleId = document.getElementById('editing-sale-id')?.value;
      const url = editingSaleId
        ? `/orders/${editingSaleId}/update/`
        : '/orders/new/';

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(payload)
      });

      const result = await res.json();
      if (result.sale_id) {
        window.open(`/orders/thermal-receipt/${result.sale_id}/`, '_blank');
      } else {
        alert(result.error || "❌ Something went wrong!");
      }
    } catch (err) {
      console.error(err);
      alert("❌ Order failed. Try again.");
    }
  });

  // CSRF
  function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
  }

  // ✅ Recalculate subtotal when user manually edits totalWithGST
document.getElementById("totalWithGST").addEventListener("input", () => {
  const rows = document.querySelectorAll(".item-row");

  let estimatedGST = 0;

  rows.forEach(row => {
    const select = row.querySelector(".product-select");
    const qty = parseInt(row.querySelector(".qty-input")?.value || 0);
    const product = PRODUCTS.find(p => p.id == select.value);
    if (!product || qty <= 0) return;

    const base = parseFloat(product.price);
    const gstPercent = parseFloat(product.gst_percent || 0);
    estimatedGST += (base * gstPercent / 100) * qty;
  });

  const editedTotal = parseFloat(document.getElementById("totalWithGST").value || 0);
  const newSubtotal = editedTotal - estimatedGST;

  if (!isNaN(newSubtotal) && newSubtotal >= 0) {
    document.getElementById("grandTotal").value = newSubtotal.toFixed(2);
  }
});


});
