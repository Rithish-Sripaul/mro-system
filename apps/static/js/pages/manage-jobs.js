document.addEventListener("DOMContentLoaded", () => {
  // --------------------------------------------------------------- //
  // -------------- HELPERS ------------ //
  // --------------------------------------------------------------- //

  async function fetchNextSchedulePosition(schedule_type) {
    try {
      const response = await fetch(`/helper/get_schedule_position?schedule_type=${encodeURIComponent(schedule_type)}`);
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      return data.next_position;
    } catch (error) {
      console.error("Error fetching next schedule position:", error);
      return null;
    }
  }

  const scheduleTypeSelect = document.getElementById("schedule_type");
  const positionInput = document.getElementById("schedule_position");

  scheduleTypeSelect.addEventListener("change", async (event) => {
    const selectedType = event.target.value;
    const nextPosition = await fetchNextSchedulePosition(selectedType);
    const positionInfoDiv = document.getElementById("empty_schedule_position");
    if (nextPosition !== null) {
      positionInput.value = nextPosition;
      positionInput.max = nextPosition; // Set maximum to next position

      let htmlContent = `                   
      <div class="col-xl-3 d-flex justify-content-start gap-3 mb-1">
        <div class="h-6">Min Position: 1</div>
        <div class="h-6 fw-semibold">Max Position: ${nextPosition}</div>
      </div>
    `;
      positionInfoDiv.insertAdjacentHTML("afterend", htmlContent);
      updateSchedulePreview();
      console.log(`Next position for ${selectedType}: ${nextPosition}`);
    }
  });

  // -------- CHOICES INITIALIZER -------- //
  // --------------------------------------------------------------- //
  const elements = document.querySelectorAll("[data-choices]");
  if (elements && elements.length > 0) {
    elements.forEach((item) => {
      const config = {
        placeholderValue: item.hasAttribute("data-choices-groups")
          ? "This is a placeholder set in the config"
          : undefined,
        searchEnabled: item.hasAttribute("data-choices-search-true"),
        removeItemButton:
          item.hasAttribute("data-choices-removeItem") || item.hasAttribute("data-choices-multiple-remove"),
        shouldSort: !item.hasAttribute("data-choices-sorting-false"),
        maxItemCount: item.getAttribute("data-choices-limit") || undefined,
        duplicateItemsAllowed: !item.hasAttribute("data-choices-text-unique-true"),
        addItems: !item.hasAttribute("data-choices-text-disabled-true"),
      };
      const instance = new Choices(item, config);
      item.choices = instance;
      if (item.hasAttribute("data-choices-text-disabled-true")) instance.disable();
    });
  }

  // --------------------------------------------------------------- //
  // -------- JOB SCHEDULE PREVIEW -------- //
  // --------------------------------------------------------------- //

  // --- Get references to the form elements and tables ---
  const jobNameInput = document.querySelector('input[name="job_name"]');
  const schedulePositionInput = document.getElementById("schedule_position");

  const generalScheduleBody = document.getElementById("general_schedule_tbody");
  const priorityScheduleBody = document.getElementById("priority_schedule_tbody");

  // We need to get the actual Choices.js instance to listen for its events
  const scheduleTypeChoices = scheduleTypeSelect.choices;

  // --- Main function to update the preview ---
  function updateSchedulePreview() {
    // First, remove any old preview
    cleanupPreview();

    // Get current values from the form
    const jobName = jobNameInput.value.trim() || "[New Job Name]";
    const scheduleType = scheduleTypeChoices.getValue(true);
    const position = parseInt(schedulePositionInput.value, 10);

    if (!scheduleType || isNaN(position) || position < 1) {
      return;
    }

    const targetTableBody = scheduleType === "general_schedule" ? generalScheduleBody : priorityScheduleBody;
    if (!targetTableBody) return;

    const tableCard = targetTableBody.closest("[data-table]");
    const tableInstance = window.customTable.tables.find((t) => t.table === tableCard);

    // This function contains the logic to create and insert the row
    const insertPreviewRow = () => {
      const previewRow = document.createElement("tr");
      previewRow.id = "job-preview-row";
      previewRow.classList.add("table-info");
      previewRow.innerHTML = `
        <td>${position} <span class="badge bg-primary ms-1">Preview</span></td>
        <td><div><h5 class="mb-1">${jobName}</h5></div></td>
        <td>
          <div class="d-flex justify-content-center">
            <a class="btn btn-light btn-icon btn-sm rounded-circle" style="opacity: 0.5; cursor: not-allowed;">
              <i class="ti ti-eye fs-lg"></i>
            </a>
          </div>
        </td>`;

      // Use the absolute position to find the insertion index on the current page
      const indexOnPage = (position - 1) % tableInstance.rowsPerPage;
      const allRowsOnPage = Array.from(targetTableBody.querySelectorAll("tr"));

      if (indexOnPage < allRowsOnPage.length) {
        targetTableBody.insertBefore(previewRow, allRowsOnPage[indexOnPage]);
      } else {
        targetTableBody.appendChild(previewRow);
      }

      // Re-number the rows correctly after insertion
      const startPosition = (tableInstance.currentPage - 1) * tableInstance.rowsPerPage;
      const updatedRows = targetTableBody.querySelectorAll("tr:not(#job-preview-row)");
      updatedRows.forEach((row, index) => {
        const positionCell = row.querySelector("td:first-child");
        const correctPosition = startPosition + index + 1;
        if (!positionCell.dataset.originalPosition) {
          positionCell.dataset.originalPosition = correctPosition;
        }
        positionCell.textContent = correctPosition;
      });
    };

    if (tableInstance) {
      const targetPage = Math.ceil(position / tableInstance.rowsPerPage);
      if (tableInstance.currentPage !== targetPage) {
        tableInstance.currentPage = targetPage;
        // Call update WITH the callback
        tableInstance.update(insertPreviewRow);
      } else {
        // If we are already on the correct page, just insert the row
        insertPreviewRow();
      }
    }
  }

  // --- Function to clean up the preview ---
  function cleanupPreview() {
    // Remove the old preview row if it exists
    const oldPreview = document.getElementById("job-preview-row");
    if (oldPreview) {
      oldPreview.remove();
    }

    // Restore original position numbers for all rows in both tables
    const allTableRows = document.querySelectorAll("#general_schedule_tbody tr, #priority_schedule_tbody tr");
    allTableRows.forEach((row) => {
      const positionCell = row.querySelector("td:first-child");
      if (positionCell && positionCell.dataset.originalPosition) {
        positionCell.textContent = positionCell.dataset.originalPosition;
      }
    });
  }

  // --- Attach Event Listeners ---
  jobNameInput.addEventListener("input", updateSchedulePreview);
  schedulePositionInput.addEventListener("input", updateSchedulePreview);
  // For Choices.js, we listen to the 'change' event on the original select element
  scheduleTypeSelect.addEventListener("change", updateSchedulePreview);

  // --------------------------------------------------------------- //
  // -------- PLUGINS -------- //
  // --------------------------------------------------------------- //

  // --------------------------------------------------------------- //
  // -------- TAGIFY INITIALIZER -------- //
  // --------------------------------------------------------------- //

  class TagifyInitializer {
    constructor() {
      this.whitelist = [];
    }

    initBasic() {
      const input = document.querySelector("#basicTagify");
      if (input) {
        input.tagify = new Tagify(input); // Store the instance on the element
      }
    }

    initManualSuggestions() {
      const input = document.querySelector('input[name="tags-manual-suggestions"]');
      if (input) {
        const tagify = new Tagify(input, {
          whitelist: this.whitelist,
          enforceWhitelist: true,
          dropdown: {
            position: "manual",
            maxItems: Infinity,
            enabled: 0,
            classname: "customSuggestionsList",
          },
          templates: {
            dropdownItemNoMatch() {
              return "Nothing Found";
            },
          },
        });

        tagify.dropdown.show();
        tagify.DOM.scope.parentNode.appendChild(tagify.DOM.dropdown);
      }
    }

    init() {
      this.initBasic();
      this.initManualSuggestions();
    }
  }
  new TagifyInitializer().init();

  // --------------------------------------------------------------- //
  // -------- DATE RANGE PICKER -------- //
  // --------------------------------------------------------------- //
  if (jQuery().daterangepicker) {
    const start = moment().subtract(29, "days");
    const end = moment();

    // Default config for range pickers
    const defaultRangeOptions = {
      startDate: start,
      endDate: end,
      ranges: {
        Today: [moment(), moment()],
        Yesterday: [moment().subtract(1, "days"), moment().subtract(1, "days")],
        "Last 7 Days": [moment().subtract(6, "days"), moment()],
        "Last 30 Days": [moment().subtract(29, "days"), moment()],
        "This Month": [moment().startOf("month"), moment().endOf("month")],
        "Last Month": [moment().subtract(1, "month").startOf("month"), moment().subtract(1, "month").endOf("month")],
      },
      locale: {
        format: "MM/DD/YYYY",
      },
      cancelClass: "btn-light",
      applyButtonClasses: "btn-success",
    };

    // Initialize range picker
    $('[data-toggle="date-picker-range"]').each(function () {
      const $this = $(this);
      const dataOptions = $this.data();

      const options = $.extend(true, {}, defaultRangeOptions, dataOptions);
      const targetSelector = $this.attr("data-target-display");

      $this.daterangepicker(options, function (start, end) {
        if (targetSelector) {
          $(targetSelector).html(start.format("MMMM D, YYYY") + " - " + end.format("MMMM D, YYYY"));
        }
      });

      // Set initial display value
      if (targetSelector) {
        $(targetSelector).html(start.format("MMMM D, YYYY") + " - " + end.format("MMMM D, YYYY"));
      }
    });

    // Default config for single date pickers
    const defaultSingleOptions = {
      singleDatePicker: true,
      showDropdowns: true,
      minDate: moment(),
      autoUpdateInput: true,
      locale: {
        format: "MM/DD/YYYY hh:mm A",
      },
      cancelClass: "btn-light",
      applyButtonClasses: "btn-success",
    };

    // Initialize single date pickers
    $('[data-toggle="date-picker"]').each(function () {
      const $this = $(this);
      const dataOptions = $this.data();
      const options = $.extend(true, {}, defaultSingleOptions, dataOptions);

      // Handle stringified locale object safely
      if (typeof options.locale === "string") {
        try {
          options.locale = JSON.parse(options.locale.replace(/'/g, '"'));
        } catch (e) {
          console.warn("Invalid JSON format in data-locale:", e);
        }
      }

      $this.daterangepicker(options);
    });
  }

  // -------- DROPZONE INITIALIZER -------- //
  class FileUpload {
    constructor() {
      this.init();
    }

    init() {
      if (typeof Dropzone === "undefined") {
        console.warn("Dropzone is not loaded.");
        return;
      }

      Dropzone.autoDiscover = false;

      const dropzones = document.querySelectorAll('[data-plugin="dropzone"]');
      if (dropzones) {
        dropzones.forEach((dropzoneEl) => {
          const actionUrl = dropzoneEl.getAttribute("action") || "/";
          const previewContainer = dropzoneEl.dataset.previewsContainer;
          const uploadPreviewTemplate = dropzoneEl.dataset.uploadPreviewTemplate;

          const options = {
            url: actionUrl,
            acceptedFiles: "image/*",
          };

          if (previewContainer) {
            options.previewsContainer = previewContainer;
          }

          if (uploadPreviewTemplate) {
            const template = document.querySelector(uploadPreviewTemplate);
            if (template) {
              options.previewTemplate = template.innerHTML;
            }
          }

          try {
            new Dropzone(dropzoneEl, options);
          } catch (e) {
            console.error("Dropzone initialization failed:", e);
          }
        });
      }
    }
  }

  new FileUpload();
  if (typeof FilePond !== "undefined") {
    // FilePond Plugins
    try {
      FilePond.registerPlugin(FilePondPluginImagePreview);
    } catch (e) {
      console.warn("FilePond plugins registration failed:", e);
    }

    // multiple-file inputs
    const multiInputs = document.querySelectorAll("input.filepond-input-multiple");
    multiInputs.forEach((input) => {
      FilePond.create(input);
    });

    // circle-style FilePond inputs
    const circleInputs = document.querySelectorAll("input.filepond-input-circle");
    circleInputs.forEach((input) => {
      FilePond.create(input, {
        imageCropAspectRatio: "1:1",
        imageResizeTargetWidth: 200,
        imageResizeTargetHeight: 200,
        stylePanelLayout: "compact circle",
        styleLoadIndicatorPosition: "center bottom",
        styleProgressIndicatorPosition: "right bottom",
        styleButtonRemoveItemPosition: "left bottom",
        styleButtonProcessItemPosition: "right bottom",
        allowImagePreview: true,
        imagePreviewHeight: 100,
        labelIdle: `<i class="fs-32 text-muted ti ti-camera"></i>`,
      });
    });
  } else {
    console.warn("FilePond is not loaded.");
  }
});
