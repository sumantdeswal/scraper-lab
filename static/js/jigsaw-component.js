if ('customElements' in window) {
    class SecureTileImage extends HTMLElement {
        constructor() {
            super();
            this._shadow = this.attachShadow({ mode: 'closed' });
        }

        connectedCallback() {
            const manifestUrl = this.getAttribute('manifest-url') || '/api/jigsaw-manifest';
            this._shadow.innerHTML = "<style>.shell{padding:1rem;border:1px solid #d3dce6;border-radius:.75rem;background:#f6f8fb}.placeholder{color:#5a6878;font-size:.95rem}.error{color:#a94442}</style><div class="shell"><p class="placeholder">Loading jigsaw tiles…</p></div>";

            fetch(manifestUrl)
                .then(r => {
                    if (!r.ok) throw new Error('manifest fetch failed');
                    return r.json();
                })
                .then(manifest => this._renderManifest(manifest))
                .catch(() => {
                    this._shadow.innerHTML = '<style>.shell{padding:1rem;border:1px solid #d3dce6;border-radius:.75rem;background:#f6f8fb}.error{color:#a94442}</style><div class="shell"><p class="error">Jigsaw tiles unavailable.</p></div>';
                });
        }

        _renderManifest(manifest) {
            const gridSize = manifest.grid_size || 4;
            const imgWidth = manifest.image_width || 400;
            const imgHeight = manifest.image_height || 300;
            const tileWidth = Math.ceil(imgWidth / gridSize);
            const tileHeight = Math.ceil(imgHeight / gridSize);

            this._shadow.innerHTML = "<style>:host{display:block;box-sizing:border-box}*,*::before,*::after{box-sizing:inherit}.shell{padding:1rem;border:1px solid #d3dce6;border-radius:.75rem;background:#f6f8fb}.tile-grid{display:grid;grid-template-columns:repeat(" + gridSize + "," + tileWidth + "px);grid-template-rows:repeat(" + gridSize + "," + tileHeight + "px);width:" + imgWidth + "px;overflow:hidden}.tile{width:" + tileWidth + "px;height:" + tileHeight + "px;display:block;object-fit:cover}.placeholder{width:" + tileWidth + "px;height:" + tileHeight + "px;display:flex;align-items:center;justify-content:center;color:#8a9aad;font-size:.75rem;background:#f6f8fb;border:1px dashed #d3dce6}.caption{margin-top:.5rem;color:#5a6878;font-size:.85rem}</style><div class=\"shell\"><div class=\"tile-grid\" id=\"tile-grid\"></div><p class=\"caption\">Jigsaw Partitioning · " + gridSize + "×" + gridSize + " grid · Randomized delivery</p></div>";

            const grid = this._shadow.getElementById("tile-grid");

            manifest.tiles.forEach(tile => {
                const wrapper = document.createElement("div");
                wrapper.style.gridRow = String(tile.row + 1);
                wrapper.style.gridColumn = String(tile.col + 1);

                if (tile.tile_url) {
                    const img = document.createElement("img");
                    img.className = "tile";
                    img.src = tile.tile_url;
                    img.alt = "";
                    img.draggable = false;
                    img.referrerPolicy = "no-referrer";
                    img.addEventListener("contextmenu", e => e.preventDefault());

                    img.onerror = () => {
                        img.replaceWith(this._createPlaceholder(tileWidth, tileHeight));
                    };

                    wrapper.appendChild(img);
                } else {
                    wrapper.appendChild(this._createPlaceholder(tileWidth, tileHeight));
                }

                grid.appendChild(wrapper);
            });
        }

        _createPlaceholder(w, h) {
            const div = document.createElement("div");
            div.className = "placeholder";
            div.style.width = w + "px";
            div.style.height = h + "px";
            div.textContent = "•";
            return div;
        }
    }

    customElements.define("secure-tile-image", SecureTileImage);
}
