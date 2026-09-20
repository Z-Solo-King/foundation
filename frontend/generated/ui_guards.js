// Generated from polyglot/frontend-state/src/ui_guards.ts. Do not edit directly.
"use strict";
(() => {
  'use strict';
  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before ui_guards.ts');
  function repairSavedOwnership() {
    api.chatStore?.repairSavedOwnership?.();
  }
  window.addEventListener('load', repairSavedOwnership);
  repairSavedOwnership();
})();