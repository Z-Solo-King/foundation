export {};

declare global {
  interface RIEFrontendGlobalApi {
    escapeHtml(value: unknown): string;
    renderMarkdown?: (value: unknown) => string;
    chatStore?: {
      repairSavedOwnership?: () => void;
    };
  }

  interface Window {
    RIEFrontend?: RIEFrontendGlobalApi;
  }
}
