/* ReconFTW UI – client-side utilities */

'use strict';

// ── DataTables default init ───────────────────────────────────────────────
/**
 * Initialise a DataTable with sensible defaults for ReconFTW data.
 * @param {string} selector  CSS selector for the <table>
 * @param {object} [extra]   Additional DataTables options (merged)
 */
function initDataTable(selector, extra) {
  var el = document.querySelector(selector);
  if (!el) return;
  if ($.fn.DataTable.isDataTable(selector)) return;

  var defaults = {
    pageLength: 25,
    lengthMenu: [10, 25, 50, 100, 500],
    stateSave: false,
    responsive: true,
    language: {
      search: '',
      searchPlaceholder: 'Filter…',
      emptyTable: 'No data available',
      zeroRecords: 'No matching records found',
      info: '_START_–_END_ of _TOTAL_',
      infoEmpty: '0 records',
      infoFiltered: '(filtered from _MAX_)',
    },
    dom: '<"d-flex align-items-center gap-3 mb-2 flex-wrap"lf>rt<"d-flex align-items-center gap-3 mt-2 flex-wrap"ip>',
  };

  $(selector).DataTable(Object.assign({}, defaults, extra || {}));
}

// ── Toast notifications ───────────────────────────────────────────────────
function showToast(message, duration) {
  duration = duration || 2500;
  var container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  var toast = document.createElement('div');
  toast.className = 'rftw-toast d-flex align-items-center gap-2';
  toast.innerHTML = '<i class="bi bi-check-circle text-accent"></i>' + message;
  container.appendChild(toast);
  setTimeout(function() {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(function() { toast.remove(); }, 300);
  }, duration);
}

// ── Tab switching ─────────────────────────────────────────────────────────
// Manual implementation — does not rely on Bootstrap's data-API so it works
// regardless of CDN/SRI issues or DataTables interfering with event delegation.
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(function (trigger) {
      trigger.addEventListener('click', function (e) {
        e.preventDefault();

        var targetId = trigger.getAttribute('data-bs-target');
        if (!targetId) return;
        var targetPane = document.querySelector(targetId);
        if (!targetPane) return;

        // Deactivate every trigger in this nav-tabs list
        var navTabs = trigger.closest('.nav-tabs, [role="tablist"]');
        if (navTabs) {
          navTabs.querySelectorAll('[data-bs-toggle="tab"]').forEach(function (t) {
            t.classList.remove('active');
          });
        }
        trigger.classList.add('active');

        // Hide every pane in the associated tab-content block
        var tabContent = targetPane.closest('.tab-content');
        if (tabContent) {
          tabContent.querySelectorAll('.tab-pane').forEach(function (p) {
            p.classList.remove('show', 'active');
          });
        }

        // Reveal the target pane; add 'show' on the next frame so the CSS
        // fade transition fires correctly after 'active' sets display:block.
        targetPane.classList.add('active');
        requestAnimationFrame(function () {
          targetPane.classList.add('show');
          // Recalculate DataTable column widths now the pane is visible
          if (window.$ && $.fn.DataTable) {
            $.fn.DataTable.tables({ visible: true, api: true }).columns.adjust();
          }
        });
      });
    });
  });
})();

// ── Auto-refresh ──────────────────────────────────────────────────────────
(function() {
  var toggle = document.getElementById('autoRefreshToggle');
  var label  = document.getElementById('refresh-label');
  if (!toggle) return;

  var STORAGE_KEY = 'rftw_autorefresh';
  var REFRESH_MS  = 30000; // 30 seconds
  var interval    = null;

  function enable() {
    toggle.checked = true;
    label.textContent = 'Auto-refresh: 30s';
    interval = setInterval(function() { location.reload(); }, REFRESH_MS);
    localStorage.setItem(STORAGE_KEY, '1');
  }

  function disable() {
    toggle.checked = false;
    label.textContent = 'Auto-refresh: off';
    clearInterval(interval);
    interval = null;
    localStorage.removeItem(STORAGE_KEY);
  }

  // Restore state from previous page load
  if (localStorage.getItem(STORAGE_KEY) === '1') {
    enable();
  }

  toggle.addEventListener('change', function() {
    if (toggle.checked) { enable(); } else { disable(); }
  });
})();
