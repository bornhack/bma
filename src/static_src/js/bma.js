check = document.querySelector("th > input");
check.addEventListener("click", toggleCheckboxes);
function toggleCheckboxes() {
  document.querySelectorAll("td > input[type='checkbox']").forEach((element) => {
    element.click();
  });
}
