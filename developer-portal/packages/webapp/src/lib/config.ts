/**
 * App-wide design & branding config.
 * Clean palette: White bg, dark text, accent highlights.
 */
export const BRAND = {
  name: "Codatta",
  logo: "/assets/company-logo.png",
  version: "0.2.1",
} as const;

export const THEME = {
  /** Page background */
  bg: "#FFFFFF",
  /** Card / surface */
  surface: "#FFFFFF",
  /** Primary accent */
  accent: "#834DFB",
  accentHover: "#7340E0",
  accentLight: "#F0EBFF",
  /** Buttons, primary text, borders */
  btnBg: "#1B1034",
  btnHover: "#2A1D4E",
  /** Text */
  textPrimary: "#1B1034",
  textSecondary: "#5C5470",
  textMuted: "#9890A8",
  /** Borders */
  border: "#1B1034",
  borderWidth: "1.5px",
  /** Danger */
  danger: "#EF4444",
  /** Avatar */
  avatarBg: "#834DFB",
} as const;
