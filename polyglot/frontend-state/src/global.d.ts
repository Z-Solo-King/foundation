export {};

declare global {
  interface RIEFrontendGlobalApi {
    escapeHtml?: (value: unknown) => string;
    renderMarkdown?: (value: unknown) => string;
    chatStore?: {
      repairSavedOwnership?: () => void;
    };
    [key: string]: unknown;
  }

  interface Window {
    RIEFrontend?: RIEFrontendGlobalApi;
  }
}
