// @ts-check
// The docs site: the Markdown pages in ../docs, generated tables included (src/docs.py), published on GitHub Pages.

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "slicer-profiles",
  tagline: "Tuned presets for the P2S, U1 and X-Max 4 in OrcaSlicer, Bambu Studio, QIDI Studio and Snapmaker Orca",
  url: "https://eschuderer.github.io",
  baseUrl: "/slicer-profiles/",
  organizationName: "ESchuderer",
  projectName: "slicer-profiles",
  trailingSlash: false,
  onBrokenLinks: "throw",
  onBrokenAnchors: "throw",
  markdown: { format: "detect", hooks: { onBrokenMarkdownLinks: "throw" } },
  i18n: { defaultLocale: "en", locales: ["en"] },
  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          path: "../docs",
          // docs/agents/ is local agent setup, never published
          exclude: ["agents/**"],
          routeBasePath: "docs",
          sidebarPath: false,
          editUrl: "https://github.com/ESchuderer/slicer-profiles/edit/main/",
        },
        blog: false,
        theme: {},
      }),
    ],
  ],
  themeConfig: {
    navbar: {
      title: "slicer-profiles",
      items: [
        { to: "/docs/install", label: "Install", position: "left" },
        { to: "/docs/profiles", label: "What the presets do", position: "left" },
        { to: "/docs/catalog", label: "Catalog", position: "left" },
        { href: "https://github.com/ESchuderer/slicer-profiles", label: "GitHub", position: "right" },
      ],
    },
    footer: {
      copyright: "Code ISC, data and docs CC BY 4.0, OrcaSlicer machine presets AGPL-3.0-only",
    },
  },
};

module.exports = config;
