(() => {
  'use strict';

  interface ChatStoreLike {
    repairSavedOwnership?: () => void;
  }

  interface FrontendApi {
    chatStore?: ChatStoreLike;
  }

  interface RIEWindow extends Window {
    RIEFrontend?: FrontendApi;
  }

  const api = (window as RIEWindow).RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before ui_guards.ts');
  const safeApi: FrontendApi = api;

  function repairSavedOwnership(): void {
    safeApi.chatStore?.repairSavedOwnership?.();
  }

  window.addEventListener('load', repairSavedOwnership);
  repairSavedOwnership();
})();
