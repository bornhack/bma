$(document).ready(function() {
  // remove the .noscript class from <body>
  // this allows us to add the class .hide-for-nojs-users to any element as needed
  $('body,html').removeClass("no-js");

  // enable all js tooltips on the page
  $('[data-bs-toggle="tooltip"]').tooltip();
});

window.addEventListener("load", (event) => {
  // make "select/unselect all" checkboxes in <th> work
  check = document.querySelector("th > input");
  if (check) {
    check.addEventListener("click", function() {
      document.querySelectorAll("td > input[type='checkbox']").forEach((element) => {
        element.click();
      });
    });
  }

  // disable unused filter inputs from form on submit to make the filtered url shorter
  if (document.getElementsByName("FilterForm").length > 0) {
    document.forms["FilterForm"].addEventListener('submit', function() {
      Array.prototype.forEach.call(this.elements, function(el) {
        if (el.type == "select-one") {
          // select-one type selects default to "unknown" when not used
          el.disabled = el.value == 'unknown';
        } else if (el.type == "text" || el.type == "number") {
          // text and number inputs default to the empty string when not used
          el.disabled = el.value == '';
        }
      });
    }, false);
  };

});
