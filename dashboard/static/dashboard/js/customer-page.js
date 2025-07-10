document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('customerModal');
  const custIdInput = document.getElementById('custId');
  const nameInput = document.getElementById('custName');
  const phoneInput = document.getElementById('custPhone');
  const gstInput = document.getElementById('custGST');
  const table = document.getElementById('customerTable');
  const totalCount = document.getElementById('totalCustomers');

  document.getElementById('openAddBtn').onclick = () => openModal();

  document.getElementById('modalCancelBtn').onclick = () => closeModal();

  document.getElementById('modalSaveBtn').onclick = async () => {
    const id = custIdInput.value;
    const payload = {
      name: nameInput.value.trim(),
      phone: phoneInput.value.trim(),
      gst: gstInput.value.trim()
    };
    const url = id ? `/customer/edit/${id}/save/` : '/customer/add_ajax/';
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRF()
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.error) return alert(data.error);

    if (id) {
      // Update row
      const row = table.querySelector(`tr[data-id="${id}"]`);
      row.querySelector('.cust-name').textContent = data.name;
      row.querySelector('.cust-phone').textContent = data.phone;
    } else {
      // Add new row
      const tr = document.createElement('tr');
      tr.dataset.id = data.id;
      tr.innerHTML = `
        <td class="cust-name">${data.name}</td>
        <td class="cust-phone">${data.phone}</td>
        <td class="cust-credit success">₹ 0.00</td>
        <td class="actions">
          <button class="view-btn" data-id="${data.id}">visibility</button>
          <button class="edit-btn" data-id="${data.id}">edit</button>
          <button class="delete-btn" data-id="${data.id}">delete</button>
        </td>`;
      table.prepend(tr);
      totalCount.textContent = table.children.length;
    }
    closeModal();
  };

  // Event delegation
  table.onclick = async (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;
    const id = btn.dataset.id;

    if (btn.classList.contains('edit-btn')) {
      const row = table.querySelector(`tr[data-id="${id}"]`);
      nameInput.value = row.querySelector('.cust-name').textContent;
      phoneInput.value = row.querySelector('.cust-phone').textContent;
      gstInput.value = ''; // You can fetch GST via AJAX if needed
      custIdInput.value = id;
      document.getElementById('modalTitle').textContent = 'Edit Customer';
      openModal();

    } else if (btn.classList.contains('delete-btn')) {
      if (!confirm('Delete this customer?')) return;
      const res = await fetch(`/customer/delete/${id}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRF() }
      });
      if (res.ok) {
        const row = table.querySelector(`tr[data-id="${id}"]`);
        row.remove();
        totalCount.textContent = table.children.length;
      }
    } else if (btn.classList.contains('view-btn')) {
      // Redirect to detail page
      window.location.href = `/customer/${id}/`;
    }
  };

  document.getElementById('customerSearch').oninput = (e) => {
    const q = e.target.value.toLowerCase();
    [...table.rows].forEach(r => {
      const name = r.querySelector('.cust-name').textContent.toLowerCase();
      r.style.display = name.includes(q) ? '' : 'none';
    });
  };

  function openModal() {
    modal.classList.remove('hidden');
  }
  function closeModal() {
    modal.classList.add('hidden');
    custIdInput.value = '';
    nameInput.value = phoneInput.value = gstInput.value = '';
    document.getElementById('modalTitle').textContent = 'Add Customer';
  }
  function getCSRF() {
    return document.cookie.split('; ').find(v=>v.startsWith('csrftoken=')).split('=')[1];
  }
});
