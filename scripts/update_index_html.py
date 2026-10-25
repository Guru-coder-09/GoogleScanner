from pathlib import Path

html_path = Path(r"C:\Users\tejag\neat-workspace\static\index.html")
content = html_path.read_text(encoding="utf-8")

old_appstate = """      const AppState = {
        studioMode: 'drive', // 'drive' or 'photos'
        simulationMode: true,
        driveSubtab: 'subtab-declutter',
        driveCategory: 'all',
        driveSearch: '',"""

new_appstate = """      const AppState = {
        studioMode: 'drive', // 'drive' or 'photos'
        simulationMode: true,
        scanRecursive: false,
        driveSubtab: 'subtab-declutter',
        driveCategory: 'all',
        driveSearch: '',"""

if old_appstate in content:
    content = content.replace(old_appstate, new_appstate)
    print("Updated AppState")

start_marker = "      function getFilteredDriveFiles() {"

if start_marker in content:
    pre = content[:content.find(start_marker)]
    
    new_code = """      function getFilteredDriveFiles() {
        return AppState.driveFiles.filter(f => {
          const matchesCat =
            AppState.driveCategory === 'all' ||
            (AppState.driveCategory === 'docs' && f.type === 'docs') ||
            (AppState.driveCategory === 'sheets' && f.type === 'sheets') ||
            (AppState.driveCategory === 'slides' && f.type === 'slides') ||
            (AppState.driveCategory === 'pdfs' && f.type === 'pdfs') ||
            (AppState.driveCategory === 'archives' && (f.type === 'archives' || f.type === 'media'));

          const matchesQuery =
            AppState.driveSearch === '' ||
            f.name.toLowerCase().includes(AppState.driveSearch) ||
            f.targetFolder.toLowerCase().includes(AppState.driveSearch) ||
            f.geminiReason.toLowerCase().includes(AppState.driveSearch);

          return matchesCat && matchesQuery;
        });
      }

      function setScanScope(recursive) {
        AppState.scanRecursive = recursive;
        playPopSound();
        const rootBtn = document.getElementById('scopeRootBtn');
        const allBtn = document.getElementById('scopeAllBtn');
        if (recursive) {
          if (allBtn) allBtn.className = 'px-2.5 py-1 rounded-lg font-bold bg-blue-600 text-white transition-all cursor-pointer';
          if (rootBtn) rootBtn.className = 'px-2.5 py-1 rounded-lg font-semibold text-slate-400 hover:text-white transition-all cursor-pointer';
          showToast('Switching scan scope to Entire 5 TB Drive...', 'info');
        } else {
          if (rootBtn) rootBtn.className = 'px-2.5 py-1 rounded-lg font-bold bg-blue-600 text-white transition-all cursor-pointer';
          if (allBtn) allBtn.className = 'px-2.5 py-1 rounded-lg font-semibold text-slate-400 hover:text-white transition-all cursor-pointer';
          showToast('Switching scan scope to Root Folder...', 'info');
        }
        syncLiveDriveData();
      }

      function updateCategoryCounts() {
        const allCount = AppState.driveFiles.length;
        const docsCount = AppState.driveFiles.filter(f => f.type === 'docs').length;
        const sheetsCount = AppState.driveFiles.filter(f => f.type === 'sheets').length;
        const slidesCount = AppState.driveFiles.filter(f => f.type === 'slides').length;
        const pdfsCount = AppState.driveFiles.filter(f => f.type === 'pdfs').length;
        const archivesCount = AppState.driveFiles.filter(f => f.type === 'archives' || f.type === 'media').length;
        const dupCount = AppState.driveDuplicates.length;

        const setVal = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        };

        setVal('catCountAll', allCount);
        setVal('catCountDocs', docsCount);
        setVal('catCountSheets', sheetsCount);
        setVal('catCountSlides', slidesCount);
        setVal('catCountPdfs', pdfsCount);
        setVal('catCountArchives', archivesCount);

        setVal('driveTabFilesBadge', allCount);
        setVal('driveTabDuplicatesBadge', dupCount);
        setVal('quarantineBadgeCount', `${dupCount} Duplicate Copies`);
        setVal('heroDriveFilesCount', `${allCount} Drive Files Evaluated`);
        setVal('heroDuplicatesCount', `${dupCount} File Duplicates`);

        const qBtn = document.getElementById('quarantineAllDriveBtn');
        if (qBtn) {
          qBtn.innerHTML = `<i data-lucide="shield-alert" class="w-4 h-4"></i><span>🧹 Quarantine All ${dupCount} Duplicates to _Duplicates/</span>`;
        }
      }

      /**
       * DRIVE STUDIO: Render Table
       */
      function renderDriveTable() {
        const tbody = document.getElementById('driveTableBody');
        const emptyState = document.getElementById('driveTableEmptyState');
        const files = getFilteredDriveFiles();

        if (files.length === 0) {
          tbody.innerHTML = '';
          emptyState.classList.remove('hidden');
          return;
        }

        emptyState.classList.add('hidden');

        const rowsHtml = files.map(file => {
          const isChecked = AppState.selectedDriveIds.has(file.id);

          let iconName = 'file-text';
          let iconClass = 'text-blue-400 bg-blue-500/10 border-blue-500/20';

          if (file.type === 'sheets') {
            iconName = 'table';
            iconClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
          } else if (file.type === 'slides') {
            iconName = 'presentation';
            iconClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
          } else if (file.type === 'pdfs') {
            iconName = 'file-text';
            iconClass = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
          } else if (file.type === 'archives' || file.type === 'media') {
            iconName = 'archive';
            iconClass = 'text-purple-400 bg-purple-500/10 border-purple-500/20';
          }

          let statusHtml = '';
          if (file.status === 'routed') {
            statusHtml = `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              <i data-lucide="check" class="w-3 h-3"></i> Routed
            </span>`;
          } else if (file.status === 'duplicate') {
            statusHtml = `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
              <i data-lucide="copy" class="w-3 h-3 text-amber-400"></i> Duplicate
            </span>`;
          } else {
            statusHtml = `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/5 text-slate-300 border border-white/10">
              <i data-lucide="compass" class="w-3 h-3 text-blue-400"></i> Pending
            </span>`;
          }

          return `
            <tr class="hover:bg-white/5 transition-colors group cursor-pointer ${isChecked ? 'bg-blue-500/5' : ''}">
              <td class="py-3.5 pl-4 pr-2">
                <input
                  type="checkbox"
                  class="drive-file-cb w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  ${isChecked ? 'checked' : ''}
                  onchange="toggleDriveFileSelection('${file.id}', this.checked)"
                />
              </td>
              <td class="py-3.5 px-3">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg ${iconClass} border flex items-center justify-center shrink-0">
                    <i data-lucide="${iconName}" class="w-4 h-4"></i>
                  </div>
                  <div class="max-w-[220px] sm:max-w-xs md:max-w-sm">
                    <p class="font-semibold text-slate-100 group-hover:text-blue-300 transition-colors truncate" title="${file.name}">
                      ${file.name}
                    </p>
                    <p class="text-[11px] text-slate-400">${file.modified}</p>
                  </div>
                </div>
              </td>
              <td class="py-3.5 px-3 text-xs text-slate-300 font-mono hidden sm:table-cell">
                ${file.size}
              </td>
              <td class="py-3.5 px-3">
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white/10 text-white border border-white/15">
                  <i data-lucide="folder" class="w-3 h-3 text-blue-400"></i>
                  ${file.targetFolder}
                </span>
              </td>
              <td class="py-3.5 px-3 text-xs text-slate-400 max-w-xs hidden md:table-cell">
                <span class="line-clamp-1 italic">${file.geminiReason}</span>
              </td>
              <td class="py-3.5 px-3">
                ${statusHtml}
              </td>
              <td class="py-3.5 pr-4 pl-2 text-right">
                <button
                  onclick="openInspectModal('${file.id}')"
                  class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                  title="Inspect AI Classification"
                >
                  <i data-lucide="info" class="w-4 h-4"></i>
                </button>
              </td>
            </tr>
          `;
        }).join('');

        tbody.innerHTML = rowsHtml;
        lucide.createIcons();
      }

      function toggleDriveFileSelection(fileId, checked) {
        playPopSound();
        if (checked) AppState.selectedDriveIds.add(fileId);
        else AppState.selectedDriveIds.delete(fileId);
        updateDriveActionBar();
      }

      function toggleDriveMasterCheckbox(checked) {
        playPopSound();
        const files = getFilteredDriveFiles();
        files.forEach(f => {
          if (checked) AppState.selectedDriveIds.add(f.id);
          else AppState.selectedDriveIds.delete(f.id);
        });
        renderDriveTable();
        updateDriveActionBar();
      }

      function selectAllDriveFiles(select) {
        playPopSound();
        const files = getFilteredDriveFiles();
        files.forEach(f => {
          if (select) AppState.selectedDriveIds.add(f.id);
          else AppState.selectedDriveIds.delete(f.id);
        });
        renderDriveTable();
        updateDriveActionBar();
      }

      function updateDriveActionBar() {
        const count = AppState.selectedDriveIds.size;
        const bar = document.getElementById('floatingActionBar');
        const countLabel = document.getElementById('selectedCountLabel');
        const masterBox = document.getElementById('driveMasterCheckbox');

        if (countLabel) countLabel.textContent = count;

        const files = getFilteredDriveFiles();
        if (masterBox) {
          if (files.length > 0 && files.every(f => AppState.selectedDriveIds.has(f.id))) {
            masterBox.checked = true;
            masterBox.indeterminate = false;
          } else if (count > 0) {
            masterBox.checked = false;
            masterBox.indeterminate = true;
          } else {
            masterBox.checked = false;
            masterBox.indeterminate = false;
          }
        }

        if (bar) {
          if (count > 0 && AppState.studioMode === 'drive') {
            bar.classList.remove('translate-y-32', 'opacity-0', 'pointer-events-none');
            bar.classList.add('translate-y-0', 'opacity-100');
          } else {
            bar.classList.add('translate-y-32', 'opacity-0', 'pointer-events-none');
            bar.classList.remove('translate-y-0', 'opacity-100');
          }
        }
      }

      async function organizeSelectedFiles() {
        const count = AppState.selectedDriveIds.size;
        if (count === 0) {
          showToast('Please select at least one file to route.', 'warning');
          return;
        }

        const isSim = AppState.simulationMode;
        showToast(isSim ? `🔍 Running simulation on ${count} files...` : `🚀 Moving ${count} files into cloud folders...`, 'info');

        try {
          const res = await fetch('/api/drive/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              file_ids: Array.from(AppState.selectedDriveIds),
              dry_run: isSim
            })
          });
          const data = await res.json();
          if (data.dry_run) {
            triggerConfetti('sparkle');
            playChimeSound();
            showToast(`🛡️ Simulation Preview: ${data.planned_moves} files mapped to target folders. Toggle "Live Mode" above to execute.`, 'info');
            AppState.selectedDriveIds.forEach(id => {
              const f = AppState.driveFiles.find(item => item.id === id);
              if (f) f.status = 'routed';
            });
            AppState.selectedDriveIds.clear();
            updateDriveActionBar();
            renderDriveTable();
          } else {
            triggerConfetti('full');
            playChimeSound();
            showToast(`✨ Success: ${data.moved_count} files moved to Google Drive folders!`, 'success');
            AppState.selectedDriveIds.clear();
            updateDriveActionBar();
            await syncLiveDriveData();
            await loadHistory();
          }
        } catch (err) {
          showToast('Error organizing files: ' + err.message, 'error');
        }
      }

      /**
       * DRIVE STUDIO: Render MD5 Duplicates
       */
      function renderDriveDuplicatePairs() {
        const container = document.getElementById('driveDuplicatePairsContainer');
        if (!container) return;

        if (AppState.driveDuplicates.length === 0) {
          container.innerHTML = `
            <div class="p-8 rounded-2xl glass-card-dark text-center border border-white/10">
              <i data-lucide="check-circle" class="w-8 h-8 text-emerald-400 mx-auto mb-2"></i>
              <h4 class="text-sm font-bold text-white">No Byte-Exact Duplicates Found</h4>
              <p class="text-xs text-slate-400 mt-1">Your Google Drive is clean with zero redundant MD5 checksum copies.</p>
            </div>
          `;
          lucide.createIcons();
          return;
        }

        const dHtml = AppState.driveDuplicates.map((dup, idx) => {
          return `
            <div class="p-4 rounded-2xl glass-card-dark border ${dup.quarantined ? 'border-emerald-500/30 bg-emerald-950/20' : 'border-white/10'} transition-all">
              <div class="flex items-center justify-between pb-2 mb-3 border-b border-white/5">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-amber-400 font-mono">PAIR #${idx + 1}</span>
                  <span class="text-xs text-slate-400">· MD5 Byte-Exact Match</span>
                </div>
                ${dup.quarantined
                  ? `<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                      <i data-lucide="check" class="w-3 h-3"></i> Quarantined
                    </span>`
                  : `<button
                      onclick="quarantineSingleDrivePair('${dup.id}')"
                      class="px-3 py-1 rounded-xl text-xs font-bold bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <i data-lucide="shield-alert" class="w-3 h-3"></i> Quarantine Copy
                    </button>`
                }
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div class="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-500/30 backdrop-blur-md">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                      <i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Master File (Keep)
                    </span>
                    <span class="text-[10px] font-mono text-emerald-300/80 bg-emerald-500/10 px-2 py-0.5 rounded">ORIGINAL</span>
                  </div>
                  <h4 class="text-sm font-bold text-white truncate" title="${dup.master}">${dup.master}</h4>
                  <p class="text-xs text-slate-300 font-mono mt-1">${dup.size}</p>
                </div>

                <div class="p-3.5 rounded-xl bg-amber-950/25 border border-amber-500/30 backdrop-blur-md">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1">
                      <i data-lucide="alert-triangle" class="w-3.5 h-3.5"></i> Duplicate Copy (Quarantine)
                    </span>
                    <span class="text-[10px] font-mono text-amber-300/80 bg-amber-500/10 px-2 py-0.5 rounded">${dup.hash || 'MD5 MATCH'}</span>
                  </div>
                  <h4 class="text-sm font-bold text-amber-200 truncate" title="${dup.copy}">${dup.copy}</h4>
                  <p class="text-xs text-slate-300 font-mono mt-1">${dup.size} · Target: _Duplicates/</p>
                </div>
              </div>
            </div>
          `;
        }).join('');

        container.innerHTML = dHtml;
        lucide.createIcons();
      }

      async function quarantineAllDriveDuplicates() {
        const dupIds = AppState.driveDuplicates.map(d => d.fileId).filter(Boolean);
        if (dupIds.length === 0) {
          showToast('No duplicate copies available to quarantine.', 'info');
          return;
        }

        const isSim = AppState.simulationMode;
        showToast(isSim ? `🔍 Simulating quarantine of ${dupIds.length} duplicates...` : `🧹 Quarantining ${dupIds.length} duplicate copies...`, 'info');

        try {
          const res = await fetch('/api/drive/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              file_ids: dupIds,
              dry_run: isSim
            })
          });
          const data = await res.json();
          if (data.dry_run) {
            triggerConfetti('sparkle');
            playChimeSound();
            showToast(`🛡️ Simulation: ${data.planned_moves} duplicate copies previewed for _Duplicates/ quarantine. Switch to Live Mode to execute.`, 'info');
            AppState.driveDuplicates.forEach(d => d.quarantined = true);
            renderDriveDuplicatePairs();
          } else {
            triggerConfetti('full');
            playChimeSound();
            showToast(`⚠️ Quarantined: ${data.moved_count} duplicate files moved to _Duplicates/!`, 'success');
            await syncLiveDriveData();
            await loadHistory();
          }
        } catch (err) {
          showToast('Error during duplicate quarantine: ' + err.message, 'error');
        }
      }

      async function quarantineSingleDrivePair(pairId) {
        const pair = AppState.driveDuplicates.find(d => d.id === pairId);
        if (!pair || !pair.fileId) return;

        const isSim = AppState.simulationMode;
        showToast(isSim ? `🔍 Simulating quarantine for "${pair.copy}"...` : `🧹 Quarantining "${pair.copy}"...`, 'info');

        try {
          const res = await fetch('/api/drive/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              file_ids: [pair.fileId],
              dry_run: isSim
            })
          });
          const data = await res.json();
          if (data.dry_run) {
            pair.quarantined = true;
            renderDriveDuplicatePairs();
            showToast(`🛡️ Simulation: "${pair.copy}" mapped to _Duplicates/ folder.`, 'info');
          } else {
            playChimeSound();
            triggerConfetti('sparkle');
            showToast(`⚠️ Quarantined "${pair.copy}" into _Duplicates/!`, 'success');
            await syncLiveDriveData();
            await loadHistory();
          }
        } catch (err) {
          showToast('Error quarantining duplicate: ' + err.message, 'error');
        }
      }

      /**
       * DRIVE STUDIO: Render Audit Logs & 1-Click Rollback
       */
      function renderDriveAuditLogs() {
        const container = document.getElementById('driveAuditLogContainer');
        if (!container) return;

        if (AppState.auditLogs.length === 0) {
          container.innerHTML = `
            <div class="p-8 rounded-2xl glass-card-dark text-center border border-white/10">
              <i data-lucide="history" class="w-8 h-8 text-blue-400 mx-auto mb-2"></i>
              <h4 class="text-sm font-bold text-white">No Cloud Operations Yet</h4>
              <p class="text-xs text-slate-400 mt-1">Actions performed in GoogleScanner are automatically tracked here for 100% reversible undo.</p>
            </div>
          `;
          lucide.createIcons();
          return;
        }

        const logsHtml = AppState.auditLogs.map(log => {
          return `
            <div class="p-4 rounded-2xl glass-card-dark border border-white/10 flex items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 shrink-0">
                  <i data-lucide="history" class="w-4 h-4"></i>
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <h4 class="text-sm font-bold text-white">${log.action}</h4>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-mono ${log.status === 'Rolled back' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}">${log.status}</span>
                  </div>
                  <p class="text-xs text-slate-300 mt-0.5">${log.target}</p>
                  <p class="text-[11px] text-slate-400 font-mono mt-0.5">${log.timestamp}</p>
                </div>
              </div>

              ${log.canUndo
                ? `<button
                    onclick="rollbackSpecificTx('${log.id}')"
                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/40 transition-colors flex items-center gap-1.5 cursor-pointer shrink-0"
                  >
                    <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i> Undo
                  </button>`
                : `<span class="text-xs text-slate-400 font-mono">Snapshot</span>`
              }
            </div>
          `;
        }).join('');

        container.innerHTML = logsHtml;
        lucide.createIcons();
      }

      async function restoreOriginalFolders() {
        playSweepSound();
        showToast('Reversing last cloud organization session...', 'info');
        try {
          const res = await fetch('/api/drive/undo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
          });
          const data = await res.json();
          if (data.success) {
            playChimeSound();
            triggerConfetti('full');
            showToast(`⏪ Rollback complete: ${data.restored_count} files restored to original locations!`, 'success');
            await syncLiveDriveData();
            await loadHistory();
          } else {
            showToast(data.message || 'No active moves found to reverse.', 'warning');
          }
        } catch (err) {
          showToast('Undo failed: ' + err.message, 'error');
        }
      }

      async function rollbackSpecificTx(sessionId) {
        playSweepSound();
        showToast(`Reversing session ${sessionId ? sessionId.substring(0, 8) : ''}...`, 'info');
        try {
          const res = await fetch('/api/drive/undo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
          });
          const data = await res.json();
          if (data.success) {
            playChimeSound();
            triggerConfetti('full');
            showToast(`⏪ Reverted ${data.restored_count} files for session ${sessionId.substring(0, 8)}!`, 'success');
            await syncLiveDriveData();
            await loadHistory();
          } else {
            showToast(data.message || 'Undo could not be completed.', 'warning');
          }
        } catch (err) {
          showToast('Undo failed: ' + err.message, 'error');
        }
      }

      async function loadHistory() {
        try {
          const res = await fetch('/api/history');
          if (!res.ok) return;
          const sessions = await res.json();
          if (sessions && sessions.length > 0) {
            AppState.auditLogs = sessions.map((s) => ({
              id: s.session_id,
              action: `Cloud Move Session (${s.count} items)`,
              target: `Files organized by Gemini rules (Rollback Session: ${s.session_id.substring(0, 8)})`,
              timestamp: s.timestamp ? new Date(s.timestamp).toLocaleString() : 'Recent',
              status: s.rolled_back ? 'Rolled back' : 'Completed',
              canUndo: !s.rolled_back
            }));
            renderDriveAuditLogs();
            const badge = document.getElementById('driveTabRollbackBadge');
            if (badge) badge.textContent = AppState.auditLogs.filter(l => l.canUndo).length;
          }
        } catch (err) {
          console.log('History load failed:', err);
        }
      }

      /**
       * File Inspect Modal
       */
      function openInspectModal(fileId) {
        playPopSound();
        const file = AppState.driveFiles.find(f => f.id === fileId);
        if (!file) return;

        AppState.currentlyInspectingFile = file;

        document.getElementById('modalFileName').textContent = file.name;
        document.getElementById('modalFileSize').textContent = `${file.size} · ${file.type.toUpperCase()}`;
        document.getElementById('modalTargetFolder').textContent = file.targetFolder;
        document.getElementById('modalGeminiReason').textContent = file.geminiReason;
        document.getElementById('modalModifiedDate').textContent = file.modified;
        document.getElementById('modalStatusBadge').textContent = file.status === 'routed' ? 'Routed in Folder' : 'Unorganized in Root';

        const modal = document.getElementById('inspectModal');
        const card = document.getElementById('inspectModalCard');
        modal.classList.remove('hidden');

        setTimeout(() => {
          card.classList.remove('scale-95', 'opacity-0');
          card.classList.add('scale-100', 'opacity-100');
        }, 10);

        lucide.createIcons();
      }

      function closeInspectModal() {
        playSweepSound();
        const modal = document.getElementById('inspectModal');
        const card = document.getElementById('inspectModalCard');
        card.classList.remove('scale-100', 'opacity-100');
        card.classList.add('scale-95', 'opacity-0');

        setTimeout(() => {
          modal.classList.add('hidden');
          AppState.currentlyInspectingFile = null;
        }, 200);
      }

      async function organizeSingleModalFile() {
        if (!AppState.currentlyInspectingFile) return;
        const file = AppState.currentlyInspectingFile;
        const isSim = AppState.simulationMode;

        try {
          const res = await fetch('/api/drive/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              file_ids: [file.id],
              dry_run: isSim
            })
          });
          const data = await res.json();
          closeInspectModal();
          if (data.dry_run) {
            file.status = 'routed';
            renderDriveTable();
            showToast(`🛡️ Simulation: "${file.name}" mapped to "${file.targetFolder}". Switch to Live Mode to execute.`, 'info');
          } else {
            playChimeSound();
            triggerConfetti('burst');
            showToast(`✨ Routed "${file.name}" to "${file.targetFolder}"`, 'success');
            await syncLiveDriveData();
            await loadHistory();
          }
        } catch (err) {
          showToast('Error organizing file: ' + err.message, 'error');
        }
      }

      /**
       * Confetti Engine
       */
      function triggerConfetti(mode = 'burst') {
        if (typeof confetti !== 'function') return;
        const googleColors = ['#4285F4', '#EA4335', '#FBBC05', '#34A853', '#EC4899', '#9B72CB'];

        if (mode === 'sparkle') {
          confetti({
            particleCount: 40,
            spread: 60,
            origin: { y: 0.7 },
            colors: googleColors,
            ticks: 180,
            scalar: 0.9,
          });
        } else if (mode === 'full') {
          confetti({
            particleCount: 80,
            angle: 60,
            spread: 65,
            origin: { x: 0, y: 0.75 },
            colors: googleColors,
          });
          confetti({
            particleCount: 80,
            angle: 120,
            spread: 65,
            origin: { x: 1, y: 0.75 },
            colors: googleColors,
          });
        } else {
          confetti({
            particleCount: 100,
            spread: 80,
            origin: { y: 0.6 },
            colors: googleColors,
          });
        }
      }

      /**
       * Toast Notifications
       */
      function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');

        let borderColor = 'border-purple-500/40 text-purple-300';
        let iconName = 'sparkles';

        if (type === 'success') {
          borderColor = 'border-emerald-500/40 text-emerald-300';
          iconName = 'check-circle';
        } else if (type === 'warning') {
          borderColor = 'border-amber-500/40 text-amber-300';
          iconName = 'alert-triangle';
        } else if (type === 'info') {
          borderColor = 'border-blue-500/40 text-blue-300';
          iconName = 'info';
        }

        toast.className = `p-3.5 rounded-2xl bg-slate-900/90 dark:bg-slate-950/95 border ${borderColor} backdrop-blur-xl shadow-xl flex items-center justify-between gap-3 text-xs text-slate-100 transition-all duration-300 transform translate-y-4 opacity-0 pointer-events-auto`;
        toast.innerHTML = `
          <div class="flex items-center gap-2.5">
            <i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i>
            <span class="font-medium">${message}</span>
          </div>
          <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-white p-0.5 cursor-pointer">
            <i data-lucide="x" class="w-3.5 h-3.5"></i>
          </button>
        `;

        container.appendChild(toast);
        lucide.createIcons();

        setTimeout(() => {
          toast.classList.remove('translate-y-4', 'opacity-0');
          toast.classList.add('translate-y-0', 'opacity-100');
        }, 10);

        setTimeout(() => {
          toast.classList.remove('translate-y-0', 'opacity-100');
          toast.classList.add('translate-y-4', 'opacity-0');
          setTimeout(() => toast.remove(), 300);
        }, 4000);
      }

      /**
       * Real Storage Quota Loader
       */
      async function loadStorageQuota() {
        try {
          const res = await fetch('/api/account/storage');
          if (!res.ok) return;
          const data = await res.json();
          if (data && data.quota) {
            const q = data.quota;
            const u = data.user;
            
            if (u) {
              const avatar = document.getElementById('userAvatarImg');
              const name = document.getElementById('userNameLabel');
              const email = document.getElementById('userEmailLabel');
              if (avatar && u.avatar) avatar.src = u.avatar;
              if (name && u.name) name.textContent = u.name;
              if (email && u.email) email.textContent = `(${u.email})`;
            }

            const totalLabel = document.getElementById('quotaTotalLabel');
            const usedBadge = document.getElementById('quotaUsedBadge');
            const usedFormatted = document.getElementById('quotaUsedFormatted');
            const freeFormatted = document.getElementById('quotaFreeFormatted');
            const otherFormatted = document.getElementById('quotaOtherFormatted');
            const driveFormatted = document.getElementById('quotaDriveFormatted');
            const legendPhotos = document.getElementById('legendPhotosVal');
            const legendDrive = document.getElementById('legendDriveVal');
            const legendFree = document.getElementById('legendFreeVal');

            if (totalLabel) totalLabel.textContent = `(${q.limit_formatted} Account Plan)`;
            if (usedBadge) usedBadge.textContent = `${q.total_used_percent}% Used`;
            if (usedFormatted) usedFormatted.textContent = `${q.usage_formatted} used`;
            if (freeFormatted) freeFormatted.textContent = `${q.free_formatted} Free`;
            if (otherFormatted) otherFormatted.textContent = q.other_formatted;
            if (driveFormatted) driveFormatted.textContent = q.drive_formatted;
            if (legendPhotos) legendPhotos.textContent = q.other_formatted;
            if (legendDrive) legendDrive.textContent = q.drive_formatted;
            if (legendFree) legendFree.textContent = q.free_formatted;

            const segPhotos = document.getElementById('barSegmentPhotos');
            const segDrive = document.getElementById('barSegmentDrive');
            const segFree = document.getElementById('barSegmentFree');

            if (segPhotos) {
              const wPhotos = Math.max(q.other_percent, 2);
              segPhotos.style.width = `${wPhotos}%`;
              segPhotos.title = `Google Photos & Cloud Media: ${q.other_formatted} (${q.other_percent}%)`;
            }
            if (segDrive) {
              const wDrive = Math.max(q.drive_percent, 0.8);
              segDrive.style.width = `${wDrive}%`;
              segDrive.title = `Google Drive: ${q.drive_formatted} (${q.drive_percent}%)`;
            }
            if (segFree) {
              segFree.title = `Free Space: ${q.free_formatted} (${q.free_percent}%)`;
            }
          }
        } catch (err) {
          console.log('Storage quota load failed:', err);
        }
      }

      /**
       * Initialization
       */
      async function syncLiveDriveData() {
        try {
          const isRecursive = AppState.scanRecursive || false;
          const url = `/api/drive/scan?recursive=${isRecursive}`;
          const res = await fetch(url);
          if (!res.ok) return;
          const data = await res.json();
          if (data && data.files) {
            AppState.driveFiles = data.files.map((f) => {
              const mime = (f.mime_type || '').toLowerCase();
              const name = (f.name || '').toLowerCase();
              
              let fileType = 'file';
              if (mime.includes('spreadsheet') || name.endsWith('.xlsx') || name.endsWith('.xls') || name.endsWith('.csv')) {
                fileType = 'sheets';
              } else if (mime.includes('presentation') || name.endsWith('.pptx') || name.endsWith('.ppt')) {
                fileType = 'slides';
              } else if (mime.includes('document') || name.endsWith('.docx') || name.endsWith('.doc') || name.endsWith('.txt') || name.endsWith('.md')) {
                fileType = 'docs';
              } else if (mime.includes('pdf') || name.endsWith('.pdf')) {
                fileType = 'pdfs';
              } else if (mime.includes('image') || mime.includes('video') || mime.includes('zip') || name.endsWith('.zip') || name.endsWith('.jpg') || name.endsWith('.png')) {
                fileType = 'archives';
              }

              const sizeFormatted = f.size ? (f.size > 1048576 ? (f.size / 1048576).toFixed(1) + ' MB' : (f.size / 1024).toFixed(0) + ' KB') : 'Cloud File';

              return {
                id: f.id,
                name: f.name,
                type: fileType,
                size: sizeFormatted,
                targetFolder: f.category || 'General',
                geminiReason: f.reason || 'Categorized by file taxonomy rules.',
                status: f.is_duplicate ? 'duplicate' : 'unorganized',
                modified: 'Google Drive',
                selected: false
              };
            });

            const dups = data.files.filter(f => f.is_duplicate);
            if (dups.length > 0) {
              AppState.driveDuplicates = dups.map((d, i) => {
                const sizeFormatted = d.size ? (d.size > 1048576 ? (d.size / 1048576).toFixed(1) + ' MB' : (d.size / 1024).toFixed(0) + ' KB') : 'Clean Copy';
                return {
                  id: `dup-${i}`,
                  fileId: d.id,
                  master: d.master_name || 'Original Master',
                  copy: d.name,
                  size: sizeFormatted,
                  hash: 'MD5 MATCH',
                  quarantined: false
                };
              });
            } else {
              AppState.driveDuplicates = [];
            }

            updateCategoryCounts();
            renderDriveTable();
            renderDriveDuplicatePairs();
            const scopeDesc = isRecursive ? 'Entire 5 TB Drive' : 'Root Folder';
            showToast(`✨ Live Google Drive Connected (${scopeDesc})! Loaded ${data.total_files} items (${dups.length} duplicates).`, 'success');
          }
        } catch (err) {
          console.log('Running standalone mode or fetch failed:', err);
        }
      }

      document.addEventListener('DOMContentLoaded', () => {
        setStudioMode('drive');
        renderBurstGroups();
        renderScreenshots();
        renderAlbums();
        renderDriveTable();
        renderDriveDuplicatePairs();
        renderDriveAuditLogs();
        lucide.createIcons();
        loadStorageQuota();
        syncLiveDriveData();
        loadHistory();
      });
    </script>
  </body>
</html>"""

    full_updated = pre + new_code
    html_path.write_text(full_updated, encoding="utf-8")
    print("Successfully updated static/index.html with all dynamic functions!")
else:
    print("Start marker not found")
