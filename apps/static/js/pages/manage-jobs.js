// Initialize Choices.js
// -------- CHOICES INITIALIZER -------- //
document.addEventListener("DOMContentLoaded", () => {
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
});

// Initialize Tagify
// -------- TAGIFY INITIALIZER -------- //
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

document.addEventListener("DOMContentLoaded", function () {
  new TagifyInitializer().init();
});

// -------- DATE RANGE PICKER -------- //
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

document.addEventListener("DOMContentLoaded", () => {
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
