# ============================================================
# BLOODBRIDGE UI LAUNCHER — Paste this as the LAST cell
# in your Google Colab notebook.
# Renders the full frontend UI directly inside Colab output.
# ============================================================

# ─────────────────────────────────────────────────────────────
# STEP 1: Upload bloodbridge_ui.html to your Colab environment
# (either via the Files panel or using the cell below)
# Then run this launcher cell.
# ─────────────────────────────────────────────────────────────

import os
from IPython.display import display, HTML

UI_PATH = "bloodbridge_ui.html"

if not os.path.exists(UI_PATH):
    print("⚠️  bloodbridge_ui.html not found.")
    print("   Please upload it to your Colab environment first.")
    print("   Drag and drop it into the Files panel on the left sidebar.")
else:
    with open(UI_PATH, "r") as f:
        html_content = f.read()

    # Wrap in a scrollable iframe for Colab
    colab_wrapper = f"""
    <div style="width:100%;border:1px solid #3d1a1a;border-radius:12px;overflow:hidden;background:#0a0707;">
        <div style="padding:8px 16px;background:#140c0c;border-bottom:1px solid #3d1a1a;
                    font-family:monospace;font-size:12px;color:#e74c3c;display:flex;align-items:center;gap:8px;">
            <span style="width:10px;height:10px;background:#e74c3c;border-radius:50%;display:inline-block;
                         box-shadow:0 0 6px rgba(231,76,60,0.5)"></span>
            BloodBridge — Full System UI
        </div>
        <iframe srcdoc="{html_content.replace(chr(34), '&quot;').replace(chr(39), '&#39;')}"
                style="width:100%;height:850px;border:none;background:#0a0707;"
                sandbox="allow-scripts allow-same-origin">
        </iframe>
    </div>
    """

    display(HTML(colab_wrapper))
    print("✅ BloodBridge UI launched successfully.")
    print("   Interact with the UI above to use all features.")


# ─────────────────────────────────────────────────────────────
# ALTERNATIVE: Open as a standalone tab (more space)
# Uncomment and run if you prefer full-browser view
# ─────────────────────────────────────────────────────────────

# from google.colab import files
# files.download('bloodbridge_ui.html')
# print("Downloaded bloodbridge_ui.html — open in your browser for full experience.")


# ─────────────────────────────────────────────────────────────
# EXTENSION IMPORT — Load all new feature functions
# ─────────────────────────────────────────────────────────────

EXTENSION_PATH = "bloodbridge_extensions.py"

if os.path.exists(EXTENSION_PATH):
    exec(open(EXTENSION_PATH).read())
    print("\n✅ BloodBridge extension module loaded.")
    print("   All new functions are now available in this session.")
else:
    print(f"\n⚠️  {EXTENSION_PATH} not found.")
    print("   Please upload bloodbridge_extensions.py to Colab too.")
