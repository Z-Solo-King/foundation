(() => {
  'use strict';

  const TOKEN_KEY = 'rie.frontend.sessionToken.v1';

  document.addEventListener('click', (event) => {
    const saveButton = event.target.closest('[data-action="save-session-token"]');
    if (saveButton) {
      const input = document.getElementById('session-token');
      const value = input?.value?.trim() || '';
      if (value) sessionStorage.setItem(TOKEN_KEY, value);
      else sessionStorage.removeItem(TOKEN_KEY);
      return;
    }

    const clearButton = event.target.closest('[data-action="clear-session-token"]');
    if (clearButton) sessionStorage.removeItem(TOKEN_KEY);
  }, true);
})();
