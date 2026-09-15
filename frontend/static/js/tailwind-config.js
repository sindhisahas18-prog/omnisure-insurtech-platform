// Design tokens sourced from the Stitch "Sovereign Intelligence" export (DESIGN.md).
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "secondary-fixed-dim": "#c3c0ff", "on-secondary-container": "#fffbff",
        "on-primary-fixed": "#131b2e", "on-secondary-fixed-variant": "#3323cc",
        "on-tertiary-fixed-variant": "#004e5c", "inverse-surface": "#213145",
        "surface-container-low": "#eff4ff", "inverse-primary": "#bec6e0",
        "on-primary": "#ffffff", "on-background": "#0b1c30",
        "inverse-on-surface": "#eaf1ff", "surface-variant": "#d3e4fe",
        "on-secondary": "#ffffff", "on-tertiary-fixed": "#001f26",
        "error-container": "#ffdad6", "on-tertiary-container": "#0090a9",
        "secondary-fixed": "#e2dfff", "primary-fixed": "#dae2fd",
        surface: "#f8f9ff", "surface-container": "#e5eeff",
        "on-surface": "#0b1c30", "surface-dim": "#cbdbf5",
        "surface-tint": "#565e74", "primary-fixed-dim": "#bec6e0",
        "tertiary-fixed": "#acedff", "on-primary-container": "#7c839b",
        background: "#f8f9ff", "tertiary-container": "#001f26",
        "on-error-container": "#93000a", "on-tertiary": "#ffffff",
        error: "#ba1a1a", secondary: "#4b41e1",
        "surface-container-lowest": "#ffffff", "on-surface-variant": "#45464d",
        "primary-container": "#131b2e", "on-error": "#ffffff",
        primary: "#000000", "on-secondary-fixed": "#0f0069",
        "outline-variant": "#c6c6cd", "tertiary-fixed-dim": "#4cd7f6",
        tertiary: "#000000", "surface-bright": "#f8f9ff",
        "surface-container-high": "#dce9ff", "secondary-container": "#645efb",
        outline: "#76777d", "surface-container-highest": "#d3e4fe",
        "on-primary-fixed-variant": "#3f465c"
      },
      borderRadius: { DEFAULT: "0.25rem", lg: "0.5rem", xl: "0.75rem", full: "9999px" },
      spacing: { "space-sm": "0.5rem", "space-md": "1rem", "space-lg": "1.5rem", "space-xs": "0.25rem", margin: "1rem", "space-xl": "2rem", gutter: "1rem" },
      fontFamily: {
        "headline-lg": ["Plus Jakarta Sans"], "body-lg": ["Inter"], "currency-display": ["Plus Jakarta Sans"],
        "headline-md": ["Plus Jakarta Sans"], "headline-sm": ["Plus Jakarta Sans"], "currency-display-mobile": ["Plus Jakarta Sans"],
        "headline-xl-mobile": ["Plus Jakarta Sans"], "body-sm": ["Inter"], "headline-xl": ["Plus Jakarta Sans"],
        "label-md": ["Inter"], "label-lg": ["Inter"], "body-md": ["Inter"], "label-sm": ["Inter"]
      },
      fontSize: {
        "headline-lg": ["24px", { lineHeight: "32px", fontWeight: "700" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "currency-display": ["28px", { lineHeight: "36px", fontWeight: "700" }],
        "headline-md": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "headline-sm": ["18px", { lineHeight: "24px", fontWeight: "600" }],
        "currency-display-mobile": ["22px", { lineHeight: "30px", fontWeight: "700" }],
        "headline-xl-mobile": ["26px", { lineHeight: "34px", fontWeight: "700" }],
        "body-sm": ["12px", { lineHeight: "16px", fontWeight: "400" }],
        "headline-xl": ["32px", { lineHeight: "40px", fontWeight: "700" }],
        "label-md": ["12px", { lineHeight: "16px", fontWeight: "600" }],
        "label-lg": ["14px", { lineHeight: "20px", fontWeight: "600" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "label-sm": ["10px", { lineHeight: "14px", fontWeight: "700" }]
      }
    }
  }
};
