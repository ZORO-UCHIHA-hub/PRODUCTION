document.addEventListener("DOMContentLoaded", function () {
  const addModal = document.getElementById("expense-modal");
  const editModal = document.getElementById("edit-expense-modal");

  // Open Add Expense Modal
  window.openAddExpenseModal = function () {
    addModal.style.display = "flex";
  };

  // Close Add Expense Modal
  window.closeAddExpenseModal = function () {
    addModal.style.display = "none";
    document.getElementById("add-expense-form").reset();
  };

  // Open Edit Expense Modal with data
  window.openEditModal = function (title, amount, category, date, id) {
    document.getElementById("edit-id").value = id;
    document.getElementById("edit-title").value = title;
    document.getElementById("edit-amount").value = amount;
    document.getElementById("edit-category").value = category;
    document.getElementById("edit-date").value = date;
    editModal.style.display = "flex";
  };

  // Close Edit Modal
  window.closeEditExpenseModal = function () {
    editModal.style.display = "none";
    document.getElementById("edit-expense-form").reset();
  };

  // Get CSRF Token
  function getCSRFToken() {
    return document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1];
  }

  // Save Expense (Add)
  window.saveExpense = function (e) {
    e.preventDefault();
    const title = document.getElementById("add-title").value;
    const amount = document.getElementById("add-amount").value;
    const category = document.getElementById("add-category").value;
    const date = document.getElementById("add-date").value;

    fetch("/expenses/add/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({ title, amount, category, date }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          closeAddExpenseModal();
          window.location.reload();
        } else {
          alert(data.error || "Failed to add expense.");
        }
      });
  };

  // Update Expense
  window.updateExpense = function (e) {
    e.preventDefault();
    const id = document.getElementById("edit-id").value;
    const title = document.getElementById("edit-title").value;
    const amount = document.getElementById("edit-amount").value;
    const category = document.getElementById("edit-category").value;
    const date = document.getElementById("edit-date").value;

    fetch(`/expenses/edit/${id}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({ title, amount, category, date }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          closeEditExpenseModal();
          window.location.reload();
        } else {
          alert(data.error || "Failed to update expense.");
        }
      });
  };

  // Delete Expense
  window.deleteExpense = function (id) {
    if (!confirm("Delete this expense?")) return;

    fetch(`/expenses/delete/${id}/`, {
      method: "DELETE",
      headers: {
        "X-CSRFToken": getCSRFToken(),
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          window.location.reload();
        } else {
          alert(data.error || "Failed to delete expense.");
        }
      });
  };

  // Optional: Click outside modal to close
  window.onclick = function (event) {
    if (event.target === addModal) closeAddExpenseModal();
    if (event.target === editModal) closeEditExpenseModal();
  };
});
