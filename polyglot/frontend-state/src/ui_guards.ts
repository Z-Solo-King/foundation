(() => {
  'use strict';

  interface ChatStoreLike {
    repairSavedOwnership?: () => void;
  }

  interface RIEFrontendWindow extends Window {
    RIEFrontend?: {
      chatStore?: ChatStoreLike;
    };
  }

  const api = (window as RIEFrontendWindow).RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before ui_guards.ts');

  function repairSavedOwnership(): void {
    api.chatStore?.repairSavedOwnership?.();
  }

  window.addEventListener('load', repairSavedOwnership);
  repairSavedOwnership();
})();