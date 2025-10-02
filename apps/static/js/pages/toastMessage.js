document.addEventListener("DOMContentLoaded", function () {
  // Select all toast elements
  var toastElLists = document.querySelectorAll(".toastCommon");
  // Loop through and initialize each toast
  toastElLists.forEach(function (toastEl) {
    var toast = new bootstrap.Toast(toastEl);
    toast.show(); // Dynamically add the `show` class and display the toast
  });
});
