// Resume Screening Drag & Drop Upload Handler
document.addEventListener('DOMContentLoaded', () => {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('resumeFileInput');
    const fileListContainer = document.getElementById('fileListContainer');
    const uploadForm = document.getElementById('screeningUploadForm');
    const submitBtn = document.getElementById('submitScreeningBtn');
    const loadingState = document.getElementById('screeningLoadingState');

    if (!uploadZone || !fileInput) return;

    // Trigger file dialog on click
    uploadZone.addEventListener('click', () => fileInput.click());

    // Drag & drop visual events
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadZone.classList.remove('dragover');
        });
    });

    // Handle dropped files
    uploadZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            renderFileList(files);
        }
    });

    // Handle standard file selection
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            renderFileList(fileInput.files);
        }
    });

    function renderFileList(files) {
        if (!fileListContainer) return;
        fileListContainer.innerHTML = '';

        Array.from(files).forEach((file, index) => {
            const sizeKb = (file.size / 1024).toFixed(1);
            const ext = file.name.split('.').pop().toLowerCase();
            const isSupported = ['pdf', 'docx'].includes(ext);

            const fileItem = document.createElement('div');
            fileItem.className = 'file-preview-item';
            fileItem.style.cssText = `
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.65rem 1rem;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid ${isSupported ? 'var(--border-subtle)' : 'var(--danger)'};
                border-radius: var(--radius-md);
                margin-top: 0.5rem;
                font-size: 0.85rem;
            `;

            fileItem.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.75rem; overflow: hidden;">
                    <span style="color: ${ext === 'pdf' ? '#ef4444' : '#3b82f6'}; font-weight: 700;">.${ext.toUpperCase()}</span>
                    <span style="color: var(--text-white); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 260px;">${file.name}</span>
                    <span style="color: var(--text-dim); font-size: 0.75rem;">(${sizeKb} KB)</span>
                </div>
                <div>
                    ${isSupported 
                        ? '<span class="badge badge-success" style="font-size: 0.7rem;">Ready</span>' 
                        : '<span class="badge badge-danger" style="font-size: 0.7rem;">Unsupported</span>'}
                </div>
            `;
            fileListContainer.appendChild(fileItem);
        });

        if (submitBtn) {
            submitBtn.disabled = false;
        }
    }

    // Submit handler with dynamic loading animation
    if (uploadForm && submitBtn) {
        uploadForm.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg class="animate-spin" style="width: 16px; height: 16px; margin-right: 8px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
                </svg>
                Processing & Screening Resumes...
            `;
            if (loadingState) {
                loadingState.style.display = 'block';
            }
        });
    }
});
