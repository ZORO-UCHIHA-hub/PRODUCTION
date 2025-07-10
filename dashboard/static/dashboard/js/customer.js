document.getElementById('customerSearch').addEventListener('keyup', function () {
  const filter = this.value.toLowerCase();
  const rows = document.querySelectorAll('tbody tr');

  rows.forEach(row => {
    const name = row.querySelector('td').textContent.toLowerCase();
    row.style.display = name.includes(filter) ? '' : 'none';
  });
});

function openCustomerModal(customer = null) {
  document.getElementById("customerModal").style.display = "flex";
  document.getElementById("customerModalTitle").textContent = customer ? "Edit Customer" : "Add New Customer";

  document.getElementById("customerId").value = customer?.id || "";
  document.getElementById("customerNameInput").value = customer?.name || "";
  document.getElementById("customerPhoneInput").value = customer?.phone || "";
  document.getElementById("customerGSTInput").value = customer?.gst || "";
}

function closeCustomerModal() {
  document.getElementById("customerModal").style.display = "none";
}

async function saveCustomer() {
  const id = document.getElementById("customerId").value;
  const name = document.getElementById("customerNameInput").value.trim();
  const phone = document.getElementById("customerPhoneInput").value.trim();
  const gst = document.getElementById("customerGSTInput").value.trim();

  if (!name || !phone) {
    alert("Name and Phone are required.");
    return;
  }

  const res = await fetch("/customers/save/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken()
    },
    body: JSON.stringify({ id, name, phone, gst })
  });

  const result = await res.json();
  if (result.success) {
    location.reload();
  } else {
    alert("Failed to save customer");
  }
}

async function deleteCustomer(id) {
  if (!confirm("Are you sure you want to delete this customer?")) return;

  const res = await fetch(`/customers/delete/${id}/`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": getCSRFToken()
    }
  });

  const result = await res.json();
  if (result.success) {
    location.reload();
  } else {
    alert("Failed to delete customer");
  }
}

function getCSRFToken() {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
}

