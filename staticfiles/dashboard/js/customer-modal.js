// Run this once DOM is ready
window.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("openCustomerBtn");
  if (openBtn) {
    openBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openCustomerModal();
    });
  }

  if (document.getElementById("modalCustomerSelect")) {
    populateCustomerOptions();

    const addBtn = document.querySelector('.add-customer-btn');
    if (addBtn) {
      addBtn.addEventListener('click', openCustomerModal);
    }
  }
});

function populateCustomerOptions() {
  const select = document.getElementById("modalCustomerSelect");
  if (!select || typeof CUSTOMERS === 'undefined') return;

  // 🧹 Clear previous options without breaking Select2
  while (select.options.length > 0) {
    select.remove(0);
  }

  // Add placeholder option
  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = '-- Choose a Customer --';
  select.appendChild(defaultOption);

  // Add each customer
  CUSTOMERS.forEach(c => {
    const option = document.createElement('option');
    option.value = c.id;
    option.textContent = c.name;
    option.dataset.phone = c.phone;
    option.dataset.gst = c.gst || '';
    select.appendChild(option);
  });

  // ✅ Trigger Select2 refresh (important after programmatically changing options)
  if ($(select).hasClass("select2-hidden-accessible")) {
    $(select).trigger('change.select2');
  }
}


function openCustomerModal() {
  const modal = document.getElementById("addCustomerModal");
  if (!modal) return;
  modal.style.display = "flex";
  modal.dataset.mode = "add";
  modal.dataset.customerId = "";
  clearCustomerForm();
}

function closeAddCustomerModal() {
  const modal = document.getElementById("addCustomerModal");
  if (!modal) return;
  modal.style.display = "none";
}

function fillCustomerForm(name, phone, gst) {
  const nameField = document.getElementById('newCustomerName');
  const phoneField = document.getElementById('newCustomerPhone');
  const gstField = document.getElementById('newCustomerGST');
  if (nameField) nameField.value = name || '';
  if (phoneField) phoneField.value = phone || '';
  if (gstField) gstField.value = gst || '';
}

function clearCustomerForm() {
  fillCustomerForm('', '', '');
}

function editCustomer(id, name, phone, gst) {
  const modal = document.getElementById('addCustomerModal');
  if (!modal) return;
  modal.style.display = 'flex';
  modal.dataset.mode = 'edit';
  modal.dataset.customerId = id;
  fillCustomerForm(name, phone, gst);
}

function saveNewCustomer() {
  const name = document.getElementById('newCustomerName')?.value.trim();
  const phone = document.getElementById('newCustomerPhone')?.value.trim();
  const gst = document.getElementById('newCustomerGST')?.value.trim();
  const branch_id = document.getElementById('branchId')?.value;

  if (!name || !phone) {
    alert("Name and phone are required.");
    return;
  }

  const modal = document.getElementById('addCustomerModal');
  if (!modal) return;

  const mode = modal.dataset.mode;
  const customerId = modal.dataset.customerId;
  const url = mode === 'edit' ? `/customers/edit/${customerId}/` : "/customers/add/";

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
    body: JSON.stringify({ name, phone, gst, branch_id })
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Error: " + data.error);
      } else {
        alert(mode === 'edit' ? 'Customer updated!' : 'Customer added!');
        window.location.reload();
      }
    })
    .catch(err => {
      alert("Request failed.");
      console.error(err);
    });
}

function showCustomerDetails(select) {
  const selected = select?.selectedOptions?.[0];
  if (!selected) return;

  const modalPhone = document.getElementById("modalPhone");
  const modalGST = document.getElementById("modalGST");

  if (modalPhone) modalPhone.textContent = selected.dataset.phone || 'N/A';
  if (modalGST) modalGST.textContent = selected.dataset.gst || 'N/A';
}

function proceedToOrder() {
  const select = document.getElementById("modalCustomerSelect");
  if (!select || !select.value) return alert("Please select a customer.");

  const selected = select.selectedOptions[0];
  if (!selected) return;

  const customerId = document.getElementById("customer_id");
  const custName = document.getElementById("custName");
  const custPhone = document.getElementById("custPhone");
  const custGST = document.getElementById("custGST");
  const phoneInput = document.getElementById("customerPhone");
  const gstInput = document.getElementById("customerGST");

  if (customerId) customerId.value = selected.value;
  if (custName) custName.textContent = selected.textContent;
  if (custPhone) custPhone.textContent = selected.dataset.phone;
  if (custGST) custGST.textContent = selected.dataset.gst;
  if (phoneInput) phoneInput.value = selected.dataset.phone;
  if (gstInput) gstInput.value = selected.dataset.gst;

  closeCustomerModal();
}

function deleteCustomer(customerId) {
  if (!confirm("Are you sure you want to delete this customer?")) return;

  fetch(`/customers/delete/${customerId}/`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Customer deleted!");
        window.location.reload();
      } else {
        alert(data.error || "Failed to delete.");
      }
    })
    .catch(err => {
      alert("Failed to delete.");
      console.error(err);
    });
}

function getCSRFToken() {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
}

// Open the "Select Customer" modal on page load (not add modal)
window.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("customerModal");
  if (modal) {
    modal.style.display = "flex";
  }
});

function closeCustomerModal() {
  const modal = document.getElementById("customerModal"); // ✅ correct one
  if (!modal) return;
  modal.style.display = "none";
}

// ✅ Apply Select2 on customer dropdown
window.addEventListener("DOMContentLoaded", () => {
  const customerSelect = document.getElementById("modalCustomerSelect");
  if (customerSelect) {
    $(customerSelect).select2({
      placeholder: "Search by name or phone",
      allowClear: true,
      width: "resolve"
    });
  }
});
