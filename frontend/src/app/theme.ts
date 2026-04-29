import { createTheme, rem } from "@mantine/core";

export const appTheme = createTheme({
  primaryColor: "indigo",
  defaultRadius: "md",
  fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
  headings: {
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    sizes: {
      h1: { fontSize: rem(32), lineHeight: "1.2", fontWeight: "700" },
      h2: { fontSize: rem(26), lineHeight: "1.25", fontWeight: "700" },
      h3: { fontSize: rem(22), lineHeight: "1.3", fontWeight: "650" },
      h4: { fontSize: rem(18), lineHeight: "1.35", fontWeight: "650" },
    },
  },
  spacing: {
    xs: rem(8),
    sm: rem(12),
    md: rem(16),
    lg: rem(24),
    xl: rem(32),
  },
  components: {
    Paper: {
      defaultProps: {
        shadow: "xs",
        radius: "md",
      },
    },
    Button: {
      defaultProps: {
        radius: "md",
      },
    },
    Table: {
      defaultProps: {
        striped: true,
        highlightOnHover: true,
      },
    },
  },
});
