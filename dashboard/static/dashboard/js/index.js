// Modal show/hide logic
const modal = document.getElementById('employeeModal');
const openModalBtn = document.querySelector('.add-employee a');
const closeModalBtn = document.getElementById('closeModalBtn');

openModalBtn.addEventListener('click', (e) => {
  e.preventDefault();
  modal.classList.remove('hidden');
});

closeModalBtn.addEventListener('click', () => {
  modal.classList.add('hidden');
});

window.addEventListener('click', (e) => {
  if (e.target === modal) {
    modal.classList.add('hidden');
  }
});

// Form submission handling (you can customize or send to backend here)
document.getElementById('employeeForm').addEventListener('submit', function (e) {
  e.preventDefault();
  const name = document.getElementById('empName').value;
  const phone = document.getElementById('empPhone').value;
  const password = document.getElementById('empPassword').value;

  console.log("New Employee:", { name, phone, password });
  alert("Employee added!");

  this.reset();
  modal.classList.add('hidden');
});


function openCustomerModal() {
  document.getElementById('addCustomerModal').classList.remove('hidden');
}

function closeCustomerModal() {
  document.getElementById('addCustomerModal').classList.add('hidden');
}

function submitCustomer() {
  const name = document.getElementById('custName').value.trim();
  const phone = document.getElementById('custPhone').value.trim();

  if (name && phone) {
    alert(`Customer "${name}" added with phone "${phone}"`);
    closeCustomerModal();
    // Add actual logic to save customer here
  } else {
    alert("Please fill in all fields.");
  }
}

// Toggle dropdown
document.querySelectorAll('.dropdown-header').forEach(header => {
  header.addEventListener('click', () => {
    const parent = header.closest('.with-dropdown');
    parent.classList.toggle('active-dropdown');
  });
});

// Filter product table
document.getElementById('productSearch').addEventListener('input', function () {
  const filter = this.value.toLowerCase();
  const rows = document.querySelectorAll('#productTableBody tr');
  rows.forEach(row => {
    const name = row.cells[0].textContent.toLowerCase();
    row.style.display = name.includes(filter) ? '' : 'none';
  });
});
