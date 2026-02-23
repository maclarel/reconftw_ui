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

// ── Modal utility ─────────────────────────────────────────────────────────
// Manual show/hide so modals work without Bootstrap's data-API.
var _activeModal = null;
var _modalBackdrop = null;

function showModal(id) {
  var el = document.getElementById(id);
  if (!el) return;
  _activeModal = el;
  el.style.display = 'block';
  document.body.classList.add('modal-open');
  _modalBackdrop = document.createElement('div');
  _modalBackdrop.className = 'modal-backdrop fade';
  document.body.appendChild(_modalBackdrop);
  requestAnimationFrame(function () {
    el.classList.add('show');
    _modalBackdrop.classList.add('show');
  });
  // Click outside the dialog to close
  el.addEventListener('click', function onBgClick(e) {
    if (e.target === el) { hideModal(); el.removeEventListener('click', onBgClick); }
  });
}

function hideModal() {
  if (!_activeModal) return;
  var el = _activeModal;
  _activeModal = null;
  el.classList.remove('show');
  document.body.classList.remove('modal-open');
  if (_modalBackdrop) { _modalBackdrop.remove(); _modalBackdrop = null; }
  setTimeout(function () { el.style.display = 'none'; }, 150);
}

// ── Tab switching + stat card navigation ──────────────────────────────────
// activateTab is also called directly by stat cards via data-tab-target.
(function () {
  function activateTab(targetId) {
    var targetPane = document.querySelector(targetId);
    if (!targetPane) return;

    // Update the active state on the corresponding trigger button
    var trigger = document.querySelector('[data-bs-toggle="tab"][data-bs-target="' + targetId + '"]');
    if (trigger) {
      var navTabs = trigger.closest('.nav-tabs, [role="tablist"]');
      if (navTabs) {
        navTabs.querySelectorAll('[data-bs-toggle="tab"]').forEach(function (t) {
          t.classList.remove('active');
        });
      }
      trigger.classList.add('active');
    }

    // Hide every pane in the same tab-content block, then show the target
    var tabContent = targetPane.closest('.tab-content');
    if (tabContent) {
      tabContent.querySelectorAll('.tab-pane').forEach(function (p) {
        p.classList.remove('show', 'active');
      });
    }
    targetPane.classList.add('active');
    requestAnimationFrame(function () {
      targetPane.classList.add('show');
      if (window.$ && $.fn.DataTable) {
        $.fn.DataTable.tables({ visible: true, api: true }).columns.adjust();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Tab trigger buttons
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(function (trigger) {
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        var targetId = trigger.getAttribute('data-bs-target');
        if (targetId) activateTab(targetId);
      });
    });

    // Stat cards / any element with data-tab-target
    document.querySelectorAll('[data-tab-target]').forEach(function (el) {
      el.addEventListener('click', function () {
        var targetId = el.getAttribute('data-tab-target');
        if (targetId) activateTab(targetId);
      });
    });

    // [data-bs-dismiss="modal"] close buttons
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(function (btn) {
      btn.addEventListener('click', hideModal);
    });

    // ESC key closes open modal
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && _activeModal) hideModal();
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
