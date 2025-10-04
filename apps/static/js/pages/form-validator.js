// File: form-validator.js

document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form[novalidate]");

  forms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      let formIsValid = true;
      event.preventDefault();
      event.stopPropagation();
      form.classList.add("was-validated");

      // Validate all standard fields + Choices.js
      form.querySelectorAll("input[required], select[required], textarea[required]").forEach((field) => {
        // --- MODIFIED LOGIC FOR CHOICES.JS ---
        if (field.choices) {
          if (!validateChoices(field)) {
            formIsValid = false;
          }
        } else {
          // For all other standard fields
          if (!field.checkValidity()) {
            formIsValid = false;
          }
        }
      });

      const quillEditor = form.querySelector(".quill-editor-required");
      if (quillEditor && quillEditor.__quill) {
        const quill = quillEditor.__quill;
        const descriptionInput = form.querySelector("#description");

        if (quill.getText().trim().length === 0) {
          // If empty, mark as invalid and stop the form
          quillEditor.classList.add("is-invalid");
          formIsValid = false;
        } else {
          // If not empty, mark as valid and update the hidden input
          quillEditor.classList.remove("is-invalid");
          descriptionInput.value = quill.root.innerHTML;
        }
      }

      const tagifyInput = form.querySelector("#basicTagify[required]");
      if (tagifyInput && tagifyInput.tagify) {
        const tagifyInstance = tagifyInput.tagify;
        if (tagifyInstance.value.length === 0) {
          tagifyInstance.DOM.scope.classList.add("is-invalid");
          const feedback = tagifyInput.closest("div").querySelector(".invalid-feedback");
          if (feedback) feedback.style.display = "block";
          formIsValid = false;
        } else {
          tagifyInstance.DOM.scope.classList.remove("is-invalid");
          const feedback = tagifyInput.closest("div").querySelector(".invalid-feedback");
          if (feedback) feedback.style.display = "";
        }
      }

      const dropzoneElement = form.querySelector(".dropzone[required]");
      if (dropzoneElement && typeof Dropzone !== "undefined" && Dropzone.forElement(dropzoneElement)) {
        const dropzoneInstance = Dropzone.forElement(dropzoneElement);
        if (dropzoneInstance.getQueuedFiles().length === 0 && dropzoneInstance.getAcceptedFiles().length === 0) {
          dropzoneElement.classList.add("is-invalid");
          const errorContainer = form.querySelector("#dropzone-error");
          if (errorContainer) {
            errorContainer.textContent = "Please upload at least one file.";
            errorContainer.style.display = "block";
          }
          formIsValid = false;
        } else {
          dropzoneElement.classList.remove("is-invalid");
          const errorContainer = form.querySelector("#dropzone-error");
          if (errorContainer) errorContainer.style.display = "none";
        }
      }

      if (formIsValid) {
        console.log("Form is valid and ready to be submitted!");
        form.submit();
      } else {
        console.log("Form is invalid. Please check the fields.");
      }
    });
  });
});

const validateChoices = (choicesField) => {
  // Ensure the choices instance actually exists before trying to access it
  if (!choicesField.choices) return true; // Can't validate, so don't block form

  const choicesContainer = choicesField.choices.containerOuter.element;
  if (choicesField.value === "") {
    choicesContainer.classList.add("is-invalid");
    choicesContainer.classList.remove("is-valid");
    return false; // Invalid
  } else {
    choicesContainer.classList.remove("is-invalid");
    choicesContainer.classList.add("is-valid");
    return true; // Valid
  }
};

window.addEventListener("load", () => {
  document.querySelectorAll("select[required][data-choices]").forEach((selectElement) => {
    if (selectElement.choices) {
      const form = selectElement.closest("form");
      selectElement.addEventListener("change", () => {
        if (form && form.classList.contains("was-validated")) {
          validateChoices(selectElement);
        }
      });
    }
  });
  document.querySelectorAll(".quill-editor-required").forEach((quillEditor) => {
    if (quillEditor && quillEditor.__quill) {
      const quill = quillEditor.__quill;
      const form = quillEditor.closest("form");
      const descriptionInput = form.querySelector("#description");

      quill.on("text-change", () => {
        if (form && form.classList.contains("was-validated")) {
          if (quill.getText().trim().length === 0) {
            quillEditor.classList.add("is-invalid");
          } else {
            quillEditor.classList.remove("is-invalid");
            descriptionInput.value = quill.root.innerHTML;
          }
        }
      });
    }
  });
});
