document.addEventListener("DOMContentLoaded", () => {
  const choicesInstances = []; // Array to hold all our Choices instances
  const choiceElements = document.querySelectorAll("[data-choices]");
  if (choiceElements.length > 0) {
    choiceElements.forEach((item) => {
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
      choicesInstances.push(instance);
      if (item.hasAttribute("data-choices-text-disabled-true")) instance.disable();
    });
  }
});

// -------- Date Range Picker -------- //
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
    autoUpdateInput: false,
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

// -------- Tagify (for tags input) -------- //
class TagifyInitializer {
  constructor() {
    this.whitelist = [
      "A# .NET",
      "A# (Axiom)",
      "A-0 System",
      "A+",
      "A++",
      "ABAP",
      "ABC",
      "ABC ALGOL",
      "ABSET",
      "ABSYS",
      "ACC",
      "Accent",
      "Ace DASL",
      "ACL2",
      "Avicsoft",
      "ACT-III",
      "Action!",
      "ActionScript",
      "Ada",
      "Adenine",
      "Agda",
      "Agilent VEE",
      "Agora",
      "AIMMS",
      "Alef",
      "ALF",
      "ALGOL 58",
      "ALGOL 60",
      "ALGOL 68",
      "ALGOL W",
      "Alice",
      "Alma-0",
      "AmbientTalk",
      "Amiga E",
      "AMOS",
      "AMPL",
      "Apex (Salesforce.com)",
      "APL",
      "AppleScript",
      "Arc",
      "ARexx",
      "Argus",
      "AspectJ",
      "Assembly language",
      "ATS",
      "Ateji PX",
      "AutoHotkey",
      "Autocoder",
      "AutoIt",
      "AutoLISP / Visual LISP",
      "Averest",
      "AWK",
      "Axum",
      "Active Server Pages",
      "ASP.NET",
      "B",
      "Babbage",
      "Bash",
      "BASIC",
      "bc",
      "BCPL",
      "BeanShell",
      "Batch (Windows/Dos)",
      "Bertrand",
      "BETA",
      "Bigwig",
      "Bistro",
      "BitC",
      "BLISS",
      "Blockly",
      "BlooP",
      "Blue",
      "Boo",
      "Boomerang",
      "Bourne shell (including bash and ksh)",
      "BREW",
      "BPEL",
      "B",
      "C--",
      "C++ – ISO/IEC 14882",
      "C# – ISO/IEC 23270",
      "C/AL",
      "Caché ObjectScript",
      "C Shell",
      "Caml",
      "Cayenne",
      "CDuce",
      "Cecil",
      "Cesil",
      "Céu",
      "Ceylon",
      "CFEngine",
      "CFML",
      "Cg",
      "Ch",
      "Chapel",
      "Charity",
      "Charm",
      "Chef",
      "CHILL",
      "CHIP-8",
      "chomski",
      "ChucK",
      "CICS",
      "Cilk",
      "Citrine (programming language)",
      "CL (IBM)",
      "Claire",
      "Clarion",
      "Clean",
      "Clipper",
      "CLIPS",
      "CLIST",
      "Clojure",
      "CLU",
      "CMS-2",
      "COBOL – ISO/IEC 1989",
      "CobolScript – COBOL Scripting language",
      "Cobra",
      "CODE",
      "CoffeeScript",
      "ColdFusion",
      "COMAL",
      "Combined Programming Language (CPL)",
      "COMIT",
      "Common Intermediate Language (CIL)",
      "Common Lisp (also known as CL)",
      "COMPASS",
      "Component Pascal",
      "Constraint Handling Rules (CHR)",
      "COMTRAN",
      "Converge",
      "Cool",
      "Coq",
      "Coral 66",
      "Corn",
      "CorVision",
      "COWSEL",
      "CPL",
      "CPL",
      "Cryptol",
      "csh",
      "Csound",
      "CSP",
      "CUDA",
      "Curl",
      "Curry",
      "Cybil",
      "Cyclone",
      "Cython",
      "Java",
      "Javascript",
      "M2001",
      "M4",
      "M#",
      "Machine code",
      "MAD (Michigan Algorithm Decoder)",
      "MAD/I",
      "Magik",
      "Magma",
      "make",
      "Maple",
      "MAPPER now part of BIS",
      "MARK-IV now VISION:BUILDER",
      "Mary",
      "MASM Microsoft Assembly x86",
      "MATH-MATIC",
      "Mathematica",
      "MATLAB",
      "Maxima (see also Macsyma)",
      "Max (Max Msp – Graphical Programming Environment)",
      "Maya (MEL)",
      "MDL",
      "Mercury",
      "Mesa",
      "Metafont",
      "Microcode",
      "MicroScript",
      "MIIS",
      "Milk (programming language)",
      "MIMIC",
      "Mirah",
      "Miranda",
      "MIVA Script",
      "ML",
      "Model 204",
      "Modelica",
      "Modula",
      "Modula-2",
      "Modula-3",
      "Mohol",
      "MOO",
      "Mortran",
      "Mouse",
      "MPD",
      "Mathcad",
      "MSIL – deprecated name for CIL",
      "MSL",
      "MUMPS",
      "Mystic Programming L",
    ];
  }

  initBasic() {
    const input = document.querySelector("#basicTagify");
    if (input) new Tagify(input);
  }

  initWhitelist() {
    const input = document.querySelector("#removeTagify");

    if (input) {
      const tagify = new Tagify(input, {
        enforceWhitelist: true,
        whitelist: input.value.trim().split(/\s*,\s*/),
      });

      const removeBtn = document.querySelector(".tags--removeAllBtn");
      if (removeBtn) {
        removeBtn.addEventListener("click", () => tagify.removeAllTags());
      }

      const fetchWhitelist = () => new Promise((resolve) => setTimeout(() => resolve(this.whitelist), 700));

      tagify.on("input", async (e) => {
        tagify.whitelist = null;
        tagify.loading(true);
        try {
          const result = await fetchWhitelist();
          tagify.settings.whitelist = result.concat(tagify.value);
          tagify.loading(false).dropdown.show(e.detail.value);
        } catch {
          tagify.dropdown.hide();
        }
      });
    }
  }

  initDropdown() {
    const input = document.querySelector('input[name="input-custom-dropdown"]');
    if (input) {
      new Tagify(input, {
        whitelist: this.whitelist,
        maxTags: 10,
        dropdown: {
          maxItems: 20,
          classname: "tags-look",
          enabled: 0,
          closeOnSelect: false,
        },
      });
    }
  }

  initEmail() {
    const input = document.querySelector(".customLook");
    const button = input?.nextElementSibling;
    if (!input || !button) return;

    const tagify = new Tagify(input, {
      editTags: { keepInvalid: false },
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      whitelist: Array.from({ length: 20 }, () => `user${Math.floor(Math.random() * 1000)}@mail.com`),
      dropdown: {
        position: "text",
        enabled: 1,
      },
    });

    button.addEventListener("click", () => tagify.addEmptyTag());
  }

  initAvatars() {
    const input = document.querySelector('input[name="extra-properties"]');
    if (input) {
      const users = [
        {
          value: 1,
          name: "Justinian Hattersley",
          avatar: "/static/images/users/user-1.jpg",
          email: "jhattersley0@ucsd.edu",
          team: "A",
        },
        {
          value: 2,
          name: "Antons Esson",
          avatar: "/static/images/users/user-2.jpg",
          email: "aesson1@ning.com",
          team: "B",
        },
        {
          value: 3,
          name: "Ardeen Batisse",
          avatar: "/static/images/users/user-3.jpg",
          email: "abatisse2@nih.gov",
          team: "A",
        },
        {
          value: 4,
          name: "Graeme Yellowley",
          avatar: "/static/images/users/user-4.jpg",
          email: "gyellowley3@behance.net",
          team: "C",
        },
        {
          value: 5,
          name: "Dido Wilford",
          avatar: "assets/images/users/user-5.jpg",
          email: "dwilford4@jugem.jp",
          team: "A",
        },
        {
          value: 6,
          name: "Celesta Orwin",
          avatar: "assets/images/users/user-6.jpg",
          email: "corwin5@meetup.com",
          team: "C",
        },
        {
          value: 7,
          name: "Sally Main",
          avatar: "assets/images/users/user-7.jpg",
          email: "smain6@techcrunch.com",
          team: "A",
        },
        {
          value: 8,
          name: "Grethel Haysman",
          avatar: "assets/images/users/user-8.jpg",
          email: "ghaysman7@mashable.com",
          team: "B",
        },
        {
          value: 9,
          name: "Marvin Mandrake",
          avatar: "assets/images/users/user-9.jpg",
          email: "mmandrake8@sourceforge.net",
          team: "B",
        },
        {
          value: 10,
          name: "Corrie Tidey",
          avatar: "assets/images/users/user-10.jpg",
          email: "ctidey9@youtube.com",
          team: "A",
        },
      ];

      const tagify = new Tagify(input, {
        tagTextProp: "name",
        skipInvalid: true,
        dropdown: {
          closeOnSelect: false,
          enabled: 0,
          classname: "users-list",
          searchKeys: ["name", "email"],
        },
        templates: {
          tag: tagTemplate,
          dropdownItem: suggestionItemTemplate,
          dropdownHeader: dropdownHeaderTemplate,
        },
        whitelist: users,
        transformTag(tagData) {
          const { name, email } = parseFullValue(tagData.name);
          tagData.name = name;
          tagData.email = email || tagData.email;
        },
        validate({ name, email }) {
          if (!email && name) ({ name, email } = parseFullValue(name));
          if (!name) return "Missing name";
          if (!validateEmail(email)) return "Invalid email";
          return true;
        },
      });

      tagify.dropdown.createListHTML = (suggestions) => {
        const grouped = suggestions.reduce((acc, item) => {
          const team = item.team || "Unassigned";
          (acc[team] ||= []).push(item);
          return acc;
        }, {});

        return Object.entries(grouped)
          .map(
            ([team, members]) => `
            <div class="tagify__dropdown__itemsGroup" data-title="Team ${team}">
                ${members.map((m) => tagify.settings.templates.dropdownItem.call(tagify, m)).join("")}
            </div>
        `
          )
          .join("");
      };

      tagify.on("dropdown:select", onSelectSuggestion);
      tagify.on("edit:start", onEditStart);

      // Template for tag (in input)
      function tagTemplate(tagData) {
        return `
            <tag title="${tagData.email}" contenteditable="false" class="tagify__tag rounded-pill ${tagData.class || ""}" ${this.getAttributes(tagData)}>
                <x class="tagify__tag__removeBtn" role="button" aria-label="remove tag"></x>
                <div class="d-flex gap-2 align-item-center p-1">
                    <div class="avatar rounded-circle">
                        <img src="${tagData.avatar}" onerror="this.style.visibility='hidden'" class="avatar-xs">
                    </div>
                    <span class="tagify__tag-text align-middle tagify-user-tag-name fw-semibold">${tagData.name}</span>
                </div>
            </tag>`;
      }

      // Template for dropdown suggestion
      function suggestionItemTemplate(tagData) {
        return `
            <div ${this.getAttributes(tagData)} class="tagify__dropdown__item py-2 d-flex align-item-center gap-2 ${tagData.class || ""}" tabindex="0" role="option">
                ${
                  tagData.avatar
                    ? `
                    <div class="tagify__dropdown__item__avatar-wrap mb-0">
                        <img class="avatar-sm rounded-circle" src="${tagData.avatar}" onerror="this.style.visibility='hidden'">
                    </div>`
                    : ""
                }
                <div>
                    <h5 class="mb-0">${tagData.name}</h5>
                    <span class="fs-base opacity-75">${tagData.email}</span>
                </div>
            </div>`;
      }

      // Dropdown header template
      function dropdownHeaderTemplate(suggestions) {
        return `
            <header class="d-flex justify-content-between px-3 py-2 gap-3 ${this.settings.classNames.dropdownItem} ${this.settings.classNames.dropdownItem}__addAll">
                <strong>${this.value.length ? "Add Remaining" : "Add All"} <span class="badge align-middle badge-soft-warning">${suggestions.length}</span> members</strong>
                <a class="remove-all-tags link-danger">Remove all</a>
            </header>`;
      }

      function onSelectSuggestion(e) {
        if (e.detail.event?.target?.matches(".remove-all-tags")) {
          tagify.removeAllTags();
        } else if (e.detail.elm?.classList.contains(`${tagify.settings.classNames.dropdownItem}__addAll`)) {
          tagify.dropdown.selectAll();
        }
      }

      function onEditStart({ detail: { tag, data } }) {
        tagify.setTagTextNode(tag, `${data.name} <${data.email}>`);
      }

      function parseFullValue(value) {
        const parts = value.split(/<(.*?)>/g);
        return {
          name: parts[0].trim(),
          email: parts[1]?.replace(/<(.*?)>/g, "").trim(),
        };
      }

      function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      }
    }
  }

  initDragSort() {
    const input = document.querySelector('input[name="drag-sort"]');
    if (input) {
      const tagify = new Tagify(input);
      new DragSort(tagify.DOM.scope, {
        selector: "." + tagify.settings.classNames.tag,
        callbacks: {
          dragEnd: () => tagify.updateValueByDOMTags(),
        },
      });
    }
  }

  initVarious() {
    const outside = document.querySelector('input[name="tags-outside"]');
    if (outside) {
      new Tagify(outside, {
        whitelist: ["alpha", "beta"],
        focusable: false,
        dropdown: {
          position: "input",
          enabled: 0,
        },
      });
    }

    const readonlyMix = document.querySelector('input[name="readonly-mix"]');
    if (readonlyMix) new Tagify(readonlyMix);

    const readonly = document.querySelector("input[readonly]");
    if (readonly) new Tagify(readonly);
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
    this.initWhitelist();
    this.initDropdown();
    this.initEmail();
    this.initAvatars();
    this.initDragSort();
    this.initVarious();
    this.initManualSuggestions();
  }
}

document.addEventListener("DOMContentLoaded", function () {
  new TagifyInitializer().init();
});

// -------- Multi Step Form / Wizard -------- //
class FormWizard {
  constructor(wizardElement) {
    this.wizard = wizardElement;
    this.form = wizardElement.closest("form");
    this.validate = this.form?.hasAttribute("data-wizard-validation") ?? false;
    this.tabs = wizardElement.querySelectorAll("[data-wizard-nav] .nav-link");
    this.tabPanes = wizardElement.querySelectorAll("[data-wizard-content] .tab-pane");
    this.progressBar = wizardElement.querySelector("[data-wizard-progress]");
    this.currentIndex = 0;
  }

  init() {
    this.disableFutureTabs();
    this.bindTabClicks();
    this.bindButtons();
    this.updateProgress(this.currentIndex);
    this.showTab(this.currentIndex);
  }

  disableFutureTabs() {
    if (this.validate) {
      this.tabs.forEach((tab, index) => {
        if (index > 0) tab.classList.add("disabled");
      });
    }
  }

  bindTabClicks() {
    this.tabs.forEach((tab, index) => {
      tab.addEventListener("click", (e) => {
        if (this.validate && index > this.currentIndex && !this.validateStep(this.currentIndex)) {
          e.preventDefault();
          e.stopImmediatePropagation();
        }
      });

      tab.addEventListener("shown.bs.tab", () => {
        this.currentIndex = index;
        this.updateProgress(index);
      });
    });
  }

  bindButtons() {
    this.wizard.querySelectorAll("[data-wizard-next]").forEach((btn) => {
      btn.addEventListener("click", () => this.nextStep());
    });

    this.wizard.querySelectorAll("[data-wizard-prev]").forEach((btn) => {
      btn.addEventListener("click", () => this.prevStep());
    });

    if (this.form) {
      this.form.addEventListener("submit", () => {
        if (this.progressBar) {
          this.progressBar.style.width = "100%";
        }
      });
    }
  }

  nextStep() {
    if (this.currentIndex >= this.tabs.length - 1) return;

    if (!this.validate || this.validateStep(this.currentIndex)) {
      if (this.validate) this.tabs[this.currentIndex + 1].classList.remove("disabled");
      this.tabs[this.currentIndex].classList.add("wizard-item-done");
      this.showTab(this.currentIndex + 1);
    }
  }

  prevStep() {
    if (this.currentIndex <= 0) return;
    this.tabs[this.currentIndex - 1].classList.remove("wizard-item-done");
    this.showTab(this.currentIndex - 1);
  }

  validateStep(index) {
    if (!this.validate) return true;

    const inputs = this.tabPanes[index].querySelectorAll("input, select, textarea");
    let isValid = true;

    inputs.forEach((input) => {
      input.classList.remove("is-invalid", "is-valid");

      if (!input.checkValidity()) {
        input.classList.add("is-invalid");
        isValid = false;
      } else {
        input.classList.add("is-valid");
      }
    });

    return isValid;
  }

  updateProgress(index) {
    if (this.progressBar) {
      const percent = (index / (this.tabs.length - 1)) * 100;
      this.progressBar.style.width = `${Math.min(percent, 100)}%`;
    }
  }

  showTab(index) {
    if (index < 0 || index >= this.tabs.length) return;
    if (this.validate && this.tabs[index].classList.contains("disabled")) return;

    new bootstrap.Tab(this.tabs[index]).show();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-wizard]").forEach((wizardEl) => {
    const wizard = new FormWizard(wizardEl);
    wizard.init();
  });
});

// -------- Dropzone (for file uploads) -------- //
class FileUpload {
  constructor(choicesInstances) {
    this.choicesInstances = choicesInstances;
  }

  init() {
    if (typeof Dropzone === "undefined") {
      console.warn("Dropzone is not loaded.");
      return;
    }

    Dropzone.autoDiscover = false;

    // A variable to hold the specific Dropzone instance for our main form
    let jobFormDropzone;

    const dropzones = document.querySelectorAll('[data-plugin="dropzone"]');
    dropzones.forEach((dropzoneEl) => {
      const actionUrl = dropzoneEl.getAttribute("action") || "/upload-documents"; // Set a default upload URL
      const previewContainer = dropzoneEl.dataset.previewsContainer;
      const uploadPreviewTemplate = dropzoneEl.dataset.uploadPreviewTemplate;

      const options = {
        url: actionUrl,
        addRemoveLinks: true,
        init: function () {
          this.on("addedfile", function (file) {
            handleFilePreview(file);
          });
        },
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

      // === MODIFIED LOGIC STARTS HERE ===

      // Check if this is the special Dropzone for our main form
      if (dropzoneEl.id === "myAwesomeDropzone") {
        // Apply special settings for manual submission
        options.autoProcessQueue = false;
        options.uploadMultiple = true;
        options.parallelUploads = 5;
        options.paramName = "job_documents";
        options.clickable = "#myAwesomeDropzone .dz-message";

        // Create the instance and store it
        jobFormDropzone = new Dropzone(dropzoneEl, options);
      } else {
        // For any other Dropzone, initialize it normally
        try {
          new Dropzone(dropzoneEl, options);
        } catch (e) {
          console.error("Generic Dropzone initialization failed:", e);
        }
      }
    });

    // In your manage-jobs.js file, inside the FileUpload class's init() method...

    // === NEW, IMPROVED FORM SUBMISSION LOGIC ===
    const mainForm = document.getElementById("createJobForm");

    if (mainForm && jobFormDropzone) {
      mainForm.addEventListener("submit", function (e) {
        e.preventDefault();
        e.stopPropagation();

        // --- NEW VALIDATION LOGIC ---
        let isChoicesValid = true;
        // 1. Loop through each Choices instance
        this.choicesInstances.forEach((choice) => {
          const element = choice.passedElement.element; // The original <select>
          const container = choice.containerOuter.element; // The visible <div>

          // 2. Check if it's required and has no value
          if (element.required && choice.getValue(true).length === 0) {
            isChoicesValid = false;
            container.classList.add("is-invalid"); // Add error class
          } else {
            container.classList.remove("is-invalid"); // Remove error class if valid
          }
        });

        // 3. Check validity of the rest of the form
        const isFormValid = mainForm.checkValidity();

        if (!isFormValid || !isChoicesValid) {
          mainForm.classList.add("was-validated");

          // Switch to the tab with the first error
          const firstInvalidElement = mainForm.querySelector(":invalid, .choices.is-invalid");
          if (firstInvalidElement) {
            const invalidTabPane = firstInvalidElement.closest(".tab-pane");
            if (invalidTabPane) {
              const invalidTabId = invalidTabPane.id;
              const invalidTabNavLink = document.querySelector(`.nav-tabs .nav-link[href="#${invalidTabId}"]`);
              if (invalidTabNavLink) {
                new bootstrap.Tab(invalidTabNavLink).show();
              }
            }
          }
          return; // Stop submission
        }

        // --- FORM IS VALID, PROCEED ---
        mainForm.classList.remove("was-validated");
        if (jobFormDropzone.getQueuedFiles().length > 0) {
          jobFormDropzone.processQueue();
        } else {
          HTMLFormElement.prototype.submit.call(mainForm);
        }
      });

      jobFormDropzone.on("queuecomplete", () => {
        HTMLFormElement.prototype.submit.call(mainForm);
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

function handleFilePreview(file) {
  // We only need to intervene if the file is NOT an image.
  // Dropzone handles image previews automatically.
  if (!file.type.match(/image.*/) && file.previewElement) {
    const imgElement = file.previewElement.querySelector("[data-dz-thumbnail]");

    // Ensure the thumbnail image element exists before trying to replace it.
    if (imgElement) {
      let iconClass = "ti ti-file-text"; // Default stock icon

      // Check for PDF
      if (file.type === "application/pdf") {
        iconClass = "ti ti-file-type-pdf"; // Specific PDF icon
      }
      // You could add more else-if blocks here for other file types
      // else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
      //   iconClass = 'ti ti-file-type-doc';
      // }

      // Create the icon element
      const icon = document.createElement("i");
      icon.className = `${iconClass} display-6 ps-0 text-muted`; // display-6 makes the icon large

      // Replace the <img> tag with our new icon <i> tag
      imgElement.parentNode.replaceChild(icon, imgElement);
    }
  }
}
