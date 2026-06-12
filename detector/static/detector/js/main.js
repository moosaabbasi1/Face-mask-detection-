// ── Dark mode toggle ──
const toggle = document.getElementById('themeToggle');
const icon = document.getElementById('themeIcon');
const html = document.documentElement;

const saved = localStorage.getItem('theme') || 'light';
html.setAttribute('data-bs-theme', saved);
icon.className = saved === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';

toggle?.addEventListener('click', () => {
  const current = html.getAttribute('data-bs-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-bs-theme', next);
  localStorage.setItem('theme', next);
  icon.className = next === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
});

// ── Upload zone drag & drop ──
const zone = document.querySelector('.upload-zone');
if (zone) {
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) {
      const input = document.querySelector('input[type="file"]');
      if (input) {
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        input.dispatchEvent(new Event('change'));
      }
    }
  });
}

// ── Auto-dismiss toasts ──
document.querySelectorAll('.toast').forEach(el => {
  new bootstrap.Toast(el, { delay: 4000 }).show();
});
