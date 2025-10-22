/**
 * Template Name: INSPINIA - Multipurpose Admin & Dashboard Template
 * By (Author): WebAppLayers
 * Module/App (File Name): Form Colorpickr
 * Version: 4.2.0
 */

function ins(colorName) {
  const themeColors = {
    primary: "#000000",
    danger: "#F06548",
    info: "#47B2E4",
    // Add other theme colors you use
  };
  return themeColors[colorName] || "#4A81D4"; // Return the color or a default
}

function initPickr(selector, options = {}) {
  const elements = document.querySelectorAll(selector);
  if (elements && elements.length > 0) {
    elements.forEach((el) => {
      const pickr = Pickr.create({
        el: el,
        ...options,
      });

      if (!pickr) {
        console.warn(`Pickr not initialized for: ${selector}`);
        return;
      }

      const targetInputSelector = el.dataset.hiddenInput;
      if (targetInputSelector) {
        const hiddenInput = document.querySelector(targetInputSelector);
        if (hiddenInput) {
          // --- START: MODIFIED LOGIC ---
          const updateColor = (color) => {
            let colorString = color.toHEXA().toString();
            // Ensure the hex string starts with a '#'
            if (colorString.length === 6 || colorString.length === 8) {
              colorString = "#" + colorString;
            }
            hiddenInput.value = colorString;
          };

          // 1. Set the initial default value on page load
          updateColor(pickr.getColor());

          // 2. Set up the listener for any future changes
          pickr.on("save", (color, instance) => {
            updateColor(color);
          });
          // --- END: MODIFIED LOGIC ---
        }
      }
    });
  }
}

const swatches = [
  "rgba(244, 67, 54, 1)",
  "rgba(233, 30, 99, 0.95)",
  "rgba(156, 39, 176, 0.9)",
  "rgba(103, 58, 183, 0.85)",
  "rgba(63, 81, 181, 0.8)",
  "rgba(33, 150, 243, 0.75)",
  "rgba(3, 169, 244, 0.7)",
];

// classic color picker
initPickr(".classic-colorpicker", {
  theme: "classic",
  default: ins("primary"),
  swatches: [
    "rgba(244, 67, 54, 1)",
    "rgba(233, 30, 99, 1)",
    "rgba(156, 39, 176, 1)",
    "rgba(103, 58, 183, 1)",
    "rgba(63, 81, 181, 1)",
    "rgba(33, 150, 243, 1)",
    "rgba(3, 169, 244, 1)",
    "rgba(0, 188, 212, 1)",
    "rgba(0, 150, 136, 1)",
    "rgba(76, 175, 80, 1)",
    "rgba(139, 195, 74, 1)",
    "rgba(205, 220, 57, 1)",
    "rgba(255, 235, 59, 1)",
    "rgba(255, 193, 7, 1)",
  ],
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      hex: true,
      rgba: true,
      hsva: true,
      input: true,
      clear: true,
      save: true,
    },
  },
});

// monolith color picker
initPickr(".monolith-colorpicker", {
  theme: "monolith",
  default: ins("danger"),
  swatches: swatches,
  defaultRepresentation: "HEXA",
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      hex: false,
      rgba: false,
      hsva: false,
      input: true,
      clear: true,
      save: true,
    },
  },
});

// nano color picker
initPickr(".nano-colorpicker", {
  theme: "nano",
  default: ins("info"),
  swatches: swatches,
  defaultRepresentation: "HEXA",
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      hex: false,
      rgba: false,
      hsva: false,
      input: true,
      clear: true,
      save: true,
    },
  },
});

// demo color picker
initPickr(".colorpicker-demo", {
  theme: "monolith",
  default: ins("primary"),
  components: {
    preview: true,
    interaction: {
      clear: true,
      save: true,
    },
  },
});

// color picker opacity & hue
initPickr(".colorpicker-opacity-hue", {
  theme: "monolith",
  default: ins("danger"),
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      clear: true,
      save: true,
    },
  },
});

// color picker swatches
initPickr(".colorpicker-switch", {
  theme: "monolith",
  default: ins("info"),
  swatches: swatches,
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      clear: true,
      save: true,
    },
  },
});

// color picker input
initPickr(".colorpicker-input", {
  theme: "monolith",
  default: "#f7b84b",
  swatches: swatches,
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      input: true,
      clear: true,
      save: true,
    },
  },
});

// color picker Format
initPickr(".colorpicker-format", {
  theme: "monolith",
  default: "#f06548",
  swatches: swatches,
  components: {
    preview: true,
    opacity: true,
    hue: true,
    interaction: {
      hex: true,
      rgba: true,
      hsva: true,
      input: true,
      clear: true,
      save: true,
    },
  },
});
