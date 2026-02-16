/**
 * Trendy Threads – Global UI behavior
 * Support chat, back-to-top, HTMX scroll
 */

(function () {
  'use strict';

  function openSupportChat() {
    var btn = document.getElementById('chatbot-toggle');
    if (btn) btn.click();
  }

  var supportLink = document.getElementById('support-link');
  if (supportLink) {
    supportLink.addEventListener('click', function (e) {
      e.preventDefault();
      openSupportChat();
    });
  }

  document.querySelectorAll('a[href="#support"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      openSupportChat();
    });
  });

  if (window.location.hash === '#support') {
    openSupportChat();
  }

  var backToTop = document.getElementById('back-to-top');
  if (backToTop) {
    function onScroll() {
      if (window.scrollY > 400) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
    }
    window.addEventListener('scroll', function () {
      onScroll();
    }, { passive: true });
    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  document.body.addEventListener('htmx:afterSwap', function (ev) {
    if (ev.detail.target.tagName === 'BODY') {
      window.scrollTo(0, 0);
    }
  });
})();
