(() => {
  'use strict';

  interface ChatStoreLike {
    repairSavedOwnership?: () => void;
  }

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before ui_guards.ts');
  const safeApi = api;

  function repairSavedOwnership(): void {
    safeApi.chatStore?.repairSavedOwnership?.();
  }

  window.addEventListener('load', repairSavedOwnership);
  repairSavedOwnership();
})();
