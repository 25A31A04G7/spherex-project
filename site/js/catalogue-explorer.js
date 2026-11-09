/**
 * SPHEREx Explorer — Catalogue Explorer Module
 * Handles client-side filtering, searching, sorting, and modal inspection for all 259 observations.
 */

class CatalogueExplorer {
  constructor(data) {
    this.allData = Array.isArray(data) ? data : [];
    this.filteredData = [...this.allData];
    
    this.filters = {
      epoch: 'all',
      detector: 'all',
      search: '',
    };
    
    this.pagination = {
      currentPage: 1,
      pageSize: 10,
    };
    
    this.dom = (typeof document !== 'undefined') ? {
      tableBody: document.getElementById('catalogueTableBody'),
      resultsCount: document.getElementById('resultsCount'),
      totalCount: document.getElementById('totalCount'),
      searchInput: document.getElementById('catalogueSearch'),
      epochPills: document.querySelectorAll('[data-filter-epoch]'),
      detectorPills: document.querySelectorAll('[data-filter-detector]'),
      prevBtn: document.getElementById('prevPageBtn'),
      nextBtn: document.getElementById('nextPageBtn'),
      pageIndicator: document.getElementById('pageIndicator'),
      modal: document.getElementById('obsModal'),
      modalBody: document.getElementById('modalBody'),
      modalCloseBtn: document.getElementById('modalCloseBtn'),
    } : {};
    
    this.init();
  }
  
  init() {
    if (!this.dom.tableBody) return;
    
    this.bindEvents();
    this.applyFilters();
  }
  
  bindEvents() {
    // Search input
    if (this.dom.searchInput) {
      this.dom.searchInput.addEventListener('input', (e) => {
        this.filters.search = e.target.value.trim().toLowerCase();
        this.pagination.currentPage = 1;
        this.applyFilters();
      });
    }
    
    // Epoch pill buttons
    this.dom.epochPills.forEach((btn) => {
      btn.addEventListener('click', () => {
        this.dom.epochPills.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.filters.epoch = btn.getAttribute('data-filter-epoch');
        this.pagination.currentPage = 1;
        this.applyFilters();
      });
    });
    
    // Detector pill buttons
    this.dom.detectorPills.forEach((btn) => {
      btn.addEventListener('click', () => {
        this.dom.detectorPills.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.filters.detector = btn.getAttribute('data-filter-detector');
        this.pagination.currentPage = 1;
        this.applyFilters();
      });
    });
    
    // Pagination buttons
    if (this.dom.prevBtn) {
      this.dom.prevBtn.addEventListener('click', () => {
        if (this.pagination.currentPage > 1) {
          this.pagination.currentPage--;
          this.render();
        }
      });
    }
    
    if (this.dom.nextBtn) {
      this.dom.nextBtn.addEventListener('click', () => {
        const totalPages = Math.ceil(this.filteredData.length / this.pagination.pageSize) || 1;
        if (this.pagination.currentPage < totalPages) {
          this.pagination.currentPage++;
          this.render();
        }
      });
    }
    
    // Modal close events
    if (this.dom.modalCloseBtn) {
      this.dom.modalCloseBtn.addEventListener('click', () => this.closeModal());
    }
    
    if (this.dom.modal) {
      this.dom.modal.addEventListener('click', (e) => {
        if (e.target === this.dom.modal) {
          this.closeModal();
        }
      });
    }
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeModal();
    });
  }
  
  applyFilters() {
    this.filteredData = this.allData.filter((item) => {
      // Epoch filter
      if (this.filters.epoch !== 'all' && item.epoch !== this.filters.epoch) {
        return false;
      }
      
      // Detector filter
      if (this.filters.detector !== 'all' && item.detector !== this.filters.detector) {
        return false;
      }
      
      // Search filter (matches Obs ID, Title, Date, Detector)
      if (this.filters.search) {
        const q = this.filters.search;
        const matchTitle = (item.obs_title || '').toLowerCase().includes(q);
        const matchId = (item.obs_id || '').toLowerCase().includes(q);
        const matchDate = (item.obs_date || '').toLowerCase().includes(q);
        const matchDetector = (item.detector || '').toLowerCase().includes(q);
        const matchRa = String(item.comet_ra || '').includes(q);
        const matchDec = String(item.comet_dec || '').includes(q);
        
        if (!matchTitle && !matchId && !matchDate && !matchDetector && !matchRa && !matchDec) {
          return false;
        }
      }
      
      return true;
    });
    
    this.render();
  }
  
  render() {
    this.renderMeta();
    this.renderTable();
    this.renderPagination();
  }
  
  renderMeta() {
    if (this.dom.resultsCount) {
      this.dom.resultsCount.textContent = this.filteredData.length;
    }
    if (this.dom.totalCount) {
      this.dom.totalCount.textContent = this.allData.length;
    }
  }
  
  renderTable() {
    if (!this.dom.tableBody) return;
    
    const start = (this.pagination.currentPage - 1) * this.pagination.pageSize;
    const end = start + this.pagination.pageSize;
    const pageItems = this.filteredData.slice(start, end);
    
    if (pageItems.length === 0) {
      this.dom.tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
            <svg style="width: 2rem; height: 2rem; margin-bottom: 0.5rem; opacity: 0.5;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>No matching SPHEREx observations found for active filters.</div>
          </td>
        </tr>
      `;
      return;
    }
    
    this.dom.tableBody.innerHTML = pageItems.map((item) => {
      const isAug = (item.epoch || '').includes('August');
      const epochClass = isAug ? 'epoch-august' : 'epoch-december';
      
      return `
        <tr data-obs-id="${escapeHtml(item.obs_id)}" title="Click to view detailed scientific metadata">
          <td>
            <strong style="font-family: var(--font-mono); color: var(--text-primary);">${escapeHtml(item.obs_id)}</strong>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(item.obs_title)}</div>
          </td>
          <td>
            <span class="epoch-badge ${epochClass}">${escapeHtml(item.epoch || 'N/A')}</span>
          </td>
          <td>
            <span class="detector-badge badge-${escapeHtml(item.detector)}">${escapeHtml(item.detector)}</span>
          </td>
          <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary);">
            ${item.obs_date || 'N/A'} ${item.obs_time ? '<span style="color:var(--text-muted);">' + item.obs_time + '</span>' : ''}
          </td>
          <td style="font-family: var(--font-mono); font-size: 0.825rem;">
            ${item.comet_ra.toFixed(4)}°, ${item.comet_dec.toFixed(4)}°
          </td>
          <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent-cyan);">
            ${item.em_min.toFixed(2)} – ${item.em_max.toFixed(2)} µm
          </td>
          <td style="text-align: right;">
            <button class="page-btn inspect-btn" style="padding: 0.25rem 0.65rem;" data-id="${escapeHtml(item.obs_id)}">
              Inspect
            </button>
          </td>
        </tr>
      `;
    }).join('');
    
    // Add row click handlers
    this.dom.tableBody.querySelectorAll('tr').forEach((row) => {
      row.addEventListener('click', (e) => {
        const obsId = row.getAttribute('data-obs-id');
        if (obsId) this.openDetailModal(obsId);
      });
    });
  }
  
  renderPagination() {
    const totalPages = Math.ceil(this.filteredData.length / this.pagination.pageSize) || 1;
    
    if (this.dom.pageIndicator) {
      this.dom.pageIndicator.textContent = `Page ${this.pagination.currentPage} of ${totalPages}`;
    }
    
    if (this.dom.prevBtn) {
      this.dom.prevBtn.disabled = this.pagination.currentPage <= 1;
    }
    
    if (this.dom.nextBtn) {
      this.dom.nextBtn.disabled = this.pagination.currentPage >= totalPages;
    }
  }
  
  openDetailModal(obsId) {
    const item = this.allData.find((x) => x.obs_id === obsId);
    if (!item || !this.dom.modal || !this.dom.modalBody) return;
    
    const isAugust = (item.epoch || '').includes('August');
    
    this.dom.modalBody.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
        <div>
          <span class="detector-badge badge-${escapeHtml(item.detector)}" style="font-size: 0.85rem; padding: 0.25rem 0.75rem; margin-bottom: 0.5rem;">
            Detector ${escapeHtml(item.detector)}
          </span>
          <h3 style="font-size: 1.25rem; font-family: var(--font-mono); margin-top: 0.25rem;">${escapeHtml(item.obs_id)}</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(item.obs_title)}</p>
        </div>
        <span class="epoch-badge ${isAugust ? 'epoch-august' : 'epoch-december'}" style="font-size: 0.8rem; padding: 0.3rem 0.7rem;">
          ${escapeHtml(item.epoch || 'Observation Epoch')}
        </span>
      </div>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
        <div class="calculation-box">
          <div class="calculation-title">Target Ephemeris Coordinates</div>
          <div style="font-family: var(--font-mono); font-size: 0.95rem; color: var(--accent-cyan);">
            RA: ${item.comet_ra.toFixed(6)}°<br>
            Dec: ${item.comet_dec.toFixed(6)}°
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">Moving Target: ${item.target_moving ? 'True (3I/ATLAS)' : 'False'}</div>
        </div>
        
        <div class="calculation-box">
          <div class="calculation-title">Spacecraft Pointing (Boresight)</div>
          <div style="font-family: var(--font-mono); font-size: 0.95rem; color: #fff;">
            RA: ${item.s_ra.toFixed(6)}°<br>
            Dec: ${item.s_dec.toFixed(6)}°
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">Calibration Level: ${item.calib_level || 'Level 2A'}</div>
        </div>
      </div>
      
      <table class="meta-table" style="margin-bottom: 1.5rem;">
        <tr>
          <td>Spectral Bandwidth:</td>
          <td>${item.em_min.toFixed(3)} – ${item.em_max.toFixed(3)} µm</td>
        </tr>
        <tr>
          <td>Observation Timestamp:</td>
          <td>${item.t_min} (UTC)</td>
        </tr>
        <tr>
          <td>Exposure Duration:</td>
          <td>${item.t_exptime ? item.t_exptime + ' seconds' : 'Standard SPHEREx Integration (~7.0s)'}</td>
        </tr>
        <tr>
          <td>Primary Target Identifier:</td>
          <td>${escapeHtml(item.target_name)}</td>
        </tr>
        <tr>
          <td>Fine Astrometry Flag:</td>
          <td><span style="color: var(--accent-amber); font-weight: 700;">FINAST = 0</span> (Coarse star-tracker attitude)</td>
        </tr>
        <tr>
          <td>Archive File Size:</td>
          <td>${item.access_estsize ? (item.access_estsize / 1024).toFixed(1) + ' MB (FITS)' : '~71.6 MB (Excluded from Web)'}</td>
        </tr>
      </table>
      
      <div class="scientific-notice" style="margin-top: 0; padding: 1rem;">
        <div class="notice-icon" style="font-size: 1.25rem;">ⓘ</div>
        <div class="notice-text">
          <h4 style="font-size: 0.85rem;">Scientific Data Access & Provenance</h4>
          <p style="font-size: 0.785rem; margin-top: 0.2rem;">
            This observation record was retrieved from the official NASA/IPAC Infrared Science Archive (IRSA) ObsCore catalogue.
            Large raw 71.6 MB FITS image cubes are archived at IPAC and are not bundled locally to ensure fast, lightweight web delivery.
          </p>
        </div>
      </div>
    `;
    
    this.dom.modal.classList.add('open');
  }
  
  closeModal() {
    if (this.dom.modal) {
      this.dom.modal.classList.remove('open');
    }
  }
}

function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

window.CatalogueExplorer = CatalogueExplorer;
