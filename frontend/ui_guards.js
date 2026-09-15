(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before ui_guards.js');

  function repairSavedOwnership() {
    api.chatStore?.repairSavedOwnership();
  }

  window.addEventListener('load', repairSavedOwnership);
  repairSavedOwnership();
})();
