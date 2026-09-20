// TypeScript migration candidate. @ts-nocheck is temporary while this lane preserves exact browser semantics before type-hardening.
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

  function highlightCode(source, language) {
    const lang = String(language || '').toLowerCase();
    const supported = new Set(['js', 'jsx', 'javascript', 'ts', 'tsx', 'typescript', 'py', 'python', 'json', 'bash', 'sh', 'shell', 'sql']);
    if (!supported.has(lang)) return api.escapeHtml(source);

    const keyword = /\b(?:const|let|var|function|return|async|await|if|else|for|while|do|class|extends|new|try|catch|throw|import|from|export|default|def|in|with|as|True|False|None|null|true|false|SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|ON|AND|OR)\b/g;
    const number = /\b\d+(?:\.\d+)?\b/g;
    const tokenPattern = /(\/\*[\s\S]*?\*\/|\/\/[^\n]*|#[^\n]*|"[^"\n]*"|'[^'\n]*')/g;
    const held = [];
    const hold = (html) => {
      const token = `@@HL_${held.length}@@`;
      held.push(html);
      return token;
    };

    let text = String(source || '').replace(/[&<>]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[char]);
    text = text.replace(tokenPattern, (match) => {
      if (match.startsWith('//') || match.startsWith('#') || match.startsWith('/*')) return hold(`<span class="code-comment">${match}</span>`);
      return hold(`<span class="code-string">${match}</span>`);
    });
    text = text.replace(keyword, (match) => `<span class="code-keyword">${match}</span>`);
    text = text.replace(number, (match) => `<span class="code-number">${match}</span>`);
    return text.replace(/@@HL_(\d+)@@/g, (_m, index) => held[Number(index)]);
  }

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
      out.push(`<pre class="code-block"><code${className}>${highlightCode(code.join('\n'), fenceLanguage)}</code></pre>`);
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
