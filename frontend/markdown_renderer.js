(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before markdown_renderer.js');

  const inline = (value) => {
    let text = api.escapeHtml(String(value || ''));
    const codeTokens = [];
    text = text.replace(/`([^`\n]+)`/g, (_m, code) => {
      const token = `@@CODE_${codeTokens.length}@@`;
      codeTokens.push(`<code>${code}</code>`);
      return token;
    });
    text = text.replace(/!\[([^\]]*)\]\((https?:\/\/[^)\s]+)\)/g, (_m, alt, url) => `<a href="${api.escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${alt || 'image'}</a>`);
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (_m, label, url) => `<a href="${api.escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${label}</a>`);
    text = text.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__([^_\n]+)__/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
    text = text.replace(/_([^_\n]+)_/g, '<em>$1</em>');
    text = text.replace(/~~([^~\n]+)~~/g, '<del>$1</del>');
    return text.replace(/@@CODE_(\d+)@@/g, (_m, index) => codeTokens[Number(index)]);
  };

  function render(markdown) {
    const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
    const out = [];
    let inFence = false;
    let fenceLanguage = '';
    let code = [];
    let paragraph = [];
    let listType = null;

    const flushParagraph = () => {
      if (!paragraph.length) return;
      out.push(`<p>${inline(paragraph.join('\n')).replace(/\n/g, '<br>')}</p>`);
      paragraph = [];
    };
    const closeList = () => {
      if (!listType) return;
      out.push(`</${listType}>`);
      listType = null;
    };
    const flushFence = () => {
      const className = fenceLanguage ? ` class="language-${api.escapeHtml(fenceLanguage)}"` : '';
      out.push(`<pre class="code-block"><code${className}>${api.escapeHtml(code.join('\n'))}</code></pre>`);
      code = [];
      fenceLanguage = '';
    };

    for (const line of lines) {
      if (line.trimStart().startsWith('```')) {
        if (inFence) flushFence();
        else fenceLanguage = line.trim().slice(3).trim().split(/\s+/)[0] || '';
        inFence = !inFence;
        closeList();
        flushParagraph();
        continue;
      }
      if (inFence) {
        code.push(line);
        continue;
      }

      const heading = /^(#{1,6})\s+(.+)$/.exec(line);
      if (heading) {
        flushParagraph(); closeList();
        const level = heading[1].length;
        out.push(`<h${level}>${inline(heading[2].trim())}</h${level}>`);
        continue;
      }

      const quote = /^>\s?(.*)$/.exec(line);
      if (quote) {
        flushParagraph(); closeList();
        out.push(`<blockquote>${inline(quote[1])}</blockquote>`);
        continue;
      }

      const unordered = /^\s*[-*+]\s+(.+)$/.exec(line);
      const ordered = /^\s*\d+[.)]\s+(.+)$/.exec(line);
      if (unordered || ordered) {
        flushParagraph();
        const wanted = unordered ? 'ul' : 'ol';
        if (listType !== wanted) { closeList(); out.push(`<${wanted}>`); listType = wanted; }
        out.push(`<li>${inline((unordered || ordered)[1])}</li>`);
        continue;
      }

      if (!line.trim()) {
        flushParagraph(); closeList();
        continue;
      }

      closeList();
      paragraph.push(line.trimEnd());
    }

    if (inFence) flushFence();
    flushParagraph(); closeList();
    return out.join('');
  }

  api.renderMarkdown = Object.freeze(render);
})();
