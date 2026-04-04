#!/usr/bin/env python3
"""
Generate a printable PDF from PAPER_DRAFT.md with embedded figures.
This creates a quick-preview version for sharing.
"""

import markdown2
from weasyprint import HTML, CSS
import os

# Configuration
PAPER_DIR = "/app/backend/qmrt_topology"
OUTPUT_PDF = f"{PAPER_DIR}/paper/QMRT_paper_markdown.pdf"

# Read the markdown
with open(f"{PAPER_DIR}/PAPER_DRAFT.md", "r") as f:
    md_content = f.read()

# Convert figure references to absolute paths
figure_mapping = {
    "fig1_quantization.png": f"{PAPER_DIR}/fig1_quantization.png",
    "fig2_robustness.png": f"{PAPER_DIR}/fig2_robustness.png",
    "fig3_structure_vs_random.png": f"{PAPER_DIR}/fig3_structure_vs_random.png",
    "lc_qmrt_equivalence.png": f"{PAPER_DIR}/lc_qmrt_equivalence.png",
    "fig_experimental_setup.png": f"{PAPER_DIR}/fig_experimental_setup.png",
    "test_p31_speed_mapping.png": f"{PAPER_DIR}/test_p31_speed_mapping.png",
    "test_p32_curvature.png": f"{PAPER_DIR}/test_p32_curvature.png",
    "test_p33_geodesic.png": f"{PAPER_DIR}/test_p33_geodesic.png",
    "test_multi_defect_interference.png": f"{PAPER_DIR}/test_multi_defect_interference.png",
}

# Add figure references to markdown (they're mentioned but not embedded)
figure_section = """

---

## Figures

"""
for i, (name, path) in enumerate(figure_mapping.items(), 1):
    if os.path.exists(path):
        figure_section += f"### Figure {i}: {name.replace('.png', '').replace('_', ' ').title()}\n\n"
        figure_section += f"![{name}](file://{path})\n\n"

md_content += figure_section

# Convert markdown to HTML
html_content = markdown2.markdown(md_content, extras=[
    "fenced-code-blocks",
    "tables",
    "header-ids"
])

# Wrap in full HTML with styling
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Times New Roman', Times, serif;
            font-size: 11pt;
            line-height: 1.6;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in;
        }}
        h1 {{
            font-size: 16pt;
            text-align: center;
            margin-bottom: 0.5em;
        }}
        h2 {{
            font-size: 14pt;
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.3em;
            margin-top: 1.5em;
        }}
        h3 {{
            font-size: 12pt;
            margin-top: 1em;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            font-family: monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 3px solid #ccc;
            margin-left: 0;
            padding-left: 1em;
            font-style: italic;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }}
        @page {{
            size: letter;
            margin: 1in;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Generate PDF
print("Generating PDF...")
HTML(string=full_html).write_pdf(OUTPUT_PDF)
print(f"PDF generated: {OUTPUT_PDF}")

# Get file size
size = os.path.getsize(OUTPUT_PDF)
print(f"File size: {size / 1024 / 1024:.2f} MB")
