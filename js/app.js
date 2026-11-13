/**
 * SPHEREx Explorer — Main Application Logic
 * Initializes modules, diagnostic tabs, modal image viewers, and interactive features.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Load Catalogue Data (with dual support for local file:// via window.CATALOGUE_DATA and web fetch)
  let catalogueData = window.CATALOGUE_DATA;
  
  if (!catalogueData) {
    try {
      const response = await fetch('data/observations.json');
      if (response.ok) {
        catalogueData = await response.json();
      }
    } catch (err) {
      console.warn('Could not load observations via fetch, using fallback or empty array:', err);
      catalogueData = [];
    }
  }

  // 2. Initialize Catalogue Explorer
  if (typeof CatalogueExplorer === 'function') {
    new CatalogueExplorer(catalogueData || []);
  }

  // 3. Tab switching for Diagnostic Lab (August vs December)
  const tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
  const tabPanels = document.querySelectorAll('.tab-panel');

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      
      tabButtons.forEach((b) => b.classList.remove('active'));
      tabPanels.forEach((p) => p.classList.remove('active'));
      
      btn.classList.add('active');
      const targetPanel = document.getElementById(targetTab);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }
    });
  });

  // 3b. Tab switching & Telemetry Sync for Calibration Benchmark (August vs December)
  const calibTabBtns = document.querySelectorAll('.calib-tab-btn[data-calib-tab]');
  const calibPanels = document.querySelectorAll('.calib-tab-panel');
  const calibTbodyAugust = document.getElementById('calibTbodyAugust');
  const calibTbodyDecember = document.getElementById('calibTbodyDecember');

  calibTabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-calib-tab');
      
      calibTabBtns.forEach((b) => b.classList.remove('active'));
      calibPanels.forEach((p) => p.classList.remove('active'));
      
      btn.classList.add('active');
      const targetPanel = document.getElementById(targetTab);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }

      if (calibTbodyAugust && calibTbodyDecember) {
        if (targetTab === 'calib-tab-december') {
          calibTbodyAugust.style.display = 'none';
          calibTbodyDecember.style.display = 'table-row-group';
        } else {
          calibTbodyAugust.style.display = 'table-row-group';
          calibTbodyDecember.style.display = 'none';
        }
      }
    });
  });

  // 3c. Verify / Hydrate Calibration Comparison Data (Offline window.QR3_COMPARISON_DATA or fetch)
  let calibData = window.QR3_COMPARISON_DATA;
  if (!calibData) {
    try {
      const resp = await fetch('data/qr3_comparison_v2/comparison_summary.json');
      if (resp.ok) {
        calibData = await resp.json();
      }
    } catch (e) {
      console.warn('Could not fetch comparison_summary.json (using embedded static markup):', e);
    }
  }

  // 4. Interactive Image Modal Preview
  const imageModal = document.getElementById('imageViewerModal');
  const modalImg = document.getElementById('modalImageDisplay');
  const modalCaption = document.getElementById('modalImageCaption');
  const modalImgClose = document.getElementById('imageModalCloseBtn');

  document.querySelectorAll('[data-zoom-img]').forEach((imgTrigger) => {
    imgTrigger.addEventListener('click', () => {
      const src = imgTrigger.getAttribute('src') || imgTrigger.getAttribute('data-zoom-img');
      const title = imgTrigger.getAttribute('data-caption') || imgTrigger.getAttribute('alt') || 'Astronomical Image Detail';
      
      if (imageModal && modalImg) {
        modalImg.src = src;
        if (modalCaption) modalCaption.textContent = title;
        imageModal.classList.add('open');
      }
    });
  });

  if (modalImgClose && imageModal) {
    modalImgClose.addEventListener('click', () => {
      imageModal.classList.remove('open');
    });
    imageModal.addEventListener('click', (e) => {
      if (e.target === imageModal) {
        imageModal.classList.remove('open');
      }
    });
  }

  // 5. Mobile Menu Toggle
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const navMenu = document.getElementById('navMenu');

  if (mobileMenuBtn && navMenu) {
    mobileMenuBtn.addEventListener('click', () => {
      const isVisible = navMenu.style.display === 'flex';
      navMenu.style.display = isVisible ? 'none' : 'flex';
      navMenu.style.flexDirection = 'column';
      navMenu.style.position = 'absolute';
      navMenu.style.top = '100%';
      navMenu.style.left = '0';
      navMenu.style.right = '0';
      navMenu.style.background = 'rgba(7, 10, 18, 0.98)';
      navMenu.style.padding = '1.5rem';
      navMenu.style.borderBottom = '1px solid var(--border-subtle)';
    });

    navMenu.querySelectorAll('.nav-link').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          navMenu.style.display = 'none';
        }
      });
    });
  }

  // 6. Active nav link tracking on scroll
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', () => {
    let current = '';
    const scrollPos = window.scrollY + 120;

    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach((link) => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });
});
