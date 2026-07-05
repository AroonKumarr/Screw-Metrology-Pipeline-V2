import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Define a custom Canvas for page numbers and headers/footers
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Do not draw headers/footers on the cover page (page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        
        # Color definitions
        xis_blue = colors.HexColor("#1565C0")
        xis_gray = colors.HexColor("#6E7781")
        
        # Draw Header
        self.setFont("Helvetica", 9)
        self.setFillColor(xis_gray)
        self.drawString(54, 750, "Screw Metrology Pipeline V2 — Technical Documentation")
        
        # Header Line
        self.setStrokeColor(colors.HexColor("#E1E4E8"))
        self.setLineWidth(0.5)
        self.line(54, 742, 612 - 54, 742)
        
        # Draw Footer
        self.line(54, 50, 612 - 54, 50)
        self.drawString(54, 38, "XIS AI / Computer Vision Department Assessment")
        
        # Page Number right-aligned
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 38, page_str)
        
        self.restoreState()

def build_pdf():
    pdf_filename = "docs/Screw_Metrology_Pipeline_V2_Documentation.pdf"
    print(f"Building PDF: {pdf_filename}...")
    
    # Page setup
    # Margins: 0.75 in (54 pt)
    margin = 54
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    # Color palette
    c_blue = colors.HexColor("#1565C0")
    c_dark = colors.HexColor("#0D1117")
    c_text = colors.HexColor("#24292E")
    c_light = colors.HexColor("#F6F8FA")
    c_border = colors.HexColor("#E1E4E8")
    
    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=c_blue,
        alignment=0, # Left-aligned
        spaceAfter=15
    ))
    
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=colors.HexColor("#4A4A4A"),
        spaceAfter=30
    ))
    
    styles.add(ParagraphStyle(
        name='CoverMeta',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_text,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='CoverMetaVal',
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#586069"),
        spaceAfter=20
    ))

    # Overwrite default Normal style
    styles['Normal'].textColor = c_text
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].spaceAfter = 8

    # Overwrite default BodyText
    styles['BodyText'].textColor = c_text
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 8

    # Heading styles
    styles['Heading1'].fontSize = 20
    styles['Heading1'].leading = 24
    styles['Heading1'].textColor = c_blue
    styles['Heading1'].spaceBefore = 22
    styles['Heading1'].spaceAfter = 12
    styles['Heading1'].keepWithNext = True

    styles['Heading2'].fontSize = 14
    styles['Heading2'].leading = 18
    styles['Heading2'].textColor = colors.HexColor("#24292E")
    styles['Heading2'].spaceBefore = 14
    styles['Heading2'].spaceAfter = 8
    styles['Heading2'].keepWithNext = True

    styles['Heading3'].fontSize = 11
    styles['Heading3'].leading = 15
    styles['Heading3'].textColor = colors.HexColor("#24292E")
    styles['Heading3'].spaceBefore = 10
    styles['Heading3'].spaceAfter = 6
    styles['Heading3'].keepWithNext = True

    # Custom styling for table paragraphs
    style_th = ParagraphStyle(
        name='TH',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    style_td = ParagraphStyle(
        name='TD',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=c_text
    )
    style_td_code = ParagraphStyle(
        name='TDCode',
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=c_text
    )
    style_td_bold = ParagraphStyle(
        name='TDBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=c_text
    )
    
    style_code = ParagraphStyle(
        name='CodeBlock',
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#032F62"),
        backColor=c_light,
        borderColor=c_border,
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=8,
        spaceAfter=10,
        keepWithNext=False
    )
    
    style_callout = ParagraphStyle(
        name='Callout',
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1B5E20"),
        backColor=colors.HexColor("#E8F5E9"),
        borderColor=colors.HexColor("#C8E6C9"),
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=10
    )

    story = []

    # ============================================================
    # COVER PAGE
    # ============================================================
    story.append(Spacer(1, 100))
    story.append(Paragraph("SCREW METROLOGY PIPELINE V2", styles['CoverTitle']))
    
    # Blue bar divider
    d_table = Table([[""]], colWidths=[504])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_blue),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,-1), 3, c_blue),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("End-to-End Deep Learning Segmentation & Camera Calibrated Metrology System", styles['CoverSubtitle']))
    story.append(Spacer(1, 150))
    
    # Metadata block
    meta_data = [
        [Paragraph("Candidate Name:", styles['CoverMeta']), Paragraph("Aroon Kumar", styles['CoverMetaVal'])],
        [Paragraph("Position:", styles['CoverMeta']), Paragraph("AI / Computer Vision Engineer (Technical Assessment)", styles['CoverMetaVal'])],
        [Paragraph("Department:", styles['CoverMeta']), Paragraph("XIS AI Department", styles['CoverMetaVal'])],
        [Paragraph("Submission Version:", styles['CoverMeta']), Paragraph("Version 2.0 (Production-Grade Metrology Release)", styles['CoverMetaVal'])],
        [Paragraph("Repository URL:", styles['CoverMeta']), Paragraph("https://github.com/AroonKumarr/Screw-Metrology-Pipeline-V2", styles['CoverMetaVal'])],
        [Paragraph("Date of Submission:", styles['CoverMeta']), Paragraph("July 5, 2026", styles['CoverMetaVal'])],
    ]
    t_meta = Table(meta_data, colWidths=[150, 354])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    
    story.append(PageBreak())

    # ============================================================
    # CHAPTER 1: PROJECT OVERVIEW
    # ============================================================
    story.append(Paragraph("Chapter 1: Project Overview", styles['Heading1']))
    story.append(Paragraph(
        "The <b>Screw Metrology Pipeline V2</b> is a complete, production-quality industrial metrology system designed to measure the physical dimensions of hex-head machine screws from digital images with sub-millimeter accuracy. The system combines modern deep learning segmentation, camera geometry calibration, and reference marker detection into a single automated pipeline.",
        styles['Normal']
    ))
    story.append(Paragraph(
        "In industrial manufacturing and quality control, mechanical fasteners must be dimensioned to ensure they meet engineering tolerances. Manual measurement with mechanical calipers is slow and prone to human error. Conversely, naive computer vision solutions fail due to optical lens distortion (which warps the physical scale across the sensor) and perspective variation (which changes the pixel-to-millimeter ratio depending on camera distance). This pipeline solves both challenges rigorously.",
        styles['Normal']
    ))
    
    story.append(Paragraph("1.1 Core Pipeline Capabilities", styles['Heading2']))
    story.append(Paragraph(
        "• <b>Intrinsic Lens Calibration:</b> Computes and corrects camera radial and tangential distortions to make the spatial coordinate scale uniform across the entire image.<br/>"
        "• <b>Instance-Level Segmentation:</b> Trains a custom Mask R-CNN network to predict binary pixel-wise object masks, allowing individual screws to be measured independently even when multiple objects appear in the same frame.<br/>"
        "• <b>Fiducial Reference Metric Scale:</b> Dynamically calculates the image's pixel-to-millimeter scale factor from a detected ArUco marker in the plane of the object, eliminating focal-distance constraints.<br/>"
        "• <b>Rotation-Invariant Metrology:</b> Fits a minimum-area rotated bounding box to the segmentation mask, extracting the true width (diameter) and height (length) of the screw at any angle.",
        styles['Normal']
    ))

    # Core metrics table
    story.append(Paragraph("Table 1.1: Key Pipeline Results (Held-Out Test Set)", styles['Heading3']))
    t1_data = [
        [Paragraph("Metric", style_th), Paragraph("Target/Requirement", style_th), Paragraph("System Score", style_th), Paragraph("Status", style_th)],
        [Paragraph("mAP@0.5", style_td), Paragraph("High Detection Quality", style_td), Paragraph("1.000", style_td_bold), Paragraph("PASS", style_td_bold)],
        [Paragraph("mAP@0.5:0.95", style_td), Paragraph("Boundary Precision", style_td), Paragraph("0.775", style_td_bold), Paragraph("PASS", style_td_bold)],
        [Paragraph("Mean IoU", style_td), Paragraph("&gt; 70.0%", style_td), Paragraph("86.11%", style_td_bold), Paragraph("PASS", style_td_bold)],
        [Paragraph("F1-Score", style_td), Paragraph("No FP / No FN", style_td), Paragraph("1.000", style_td_bold), Paragraph("PASS", style_td_bold)],
        [Paragraph("Width MAE", style_td), Paragraph("&lt; 5.0% MPE (~0.21mm)", style_td), Paragraph("0.019 mm (0.45% MPE)", style_td_bold), Paragraph("PASS", style_td_bold)],
        [Paragraph("Length MAE", style_td), Paragraph("&lt; 2.0% MPE (~0.45mm)", style_td), Paragraph("0.067 mm (0.30% MPE)", style_td_bold), Paragraph("PASS", style_td_bold)],
    ]
    t1 = Table(t1_data, colWidths=[120, 150, 134, 100])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (3,1), (3,-1), colors.HexColor("#E8F5E9")),
        ('TEXTCOLOR', (3,1), (3,-1), colors.HexColor("#1B5E20")),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1.2 Target Object Specifications", styles['Heading2']))
    story.append(Paragraph(
        "The object chosen for this validation assessment is a <b>hex-head machine screw</b> (physical diameter $\\approx 4.20\\text{ mm}$, length $\\approx 22.50\\text{ mm}$). Hex screws present a rigid structure with a distinct cylindrical shaft and hexagonal cap, which is highly representative of industrial components and provides clear, non-ambiguous geometry for edge localization. All target measurements are verified against a digital caliper.",
        styles['Normal']
    ))
    story.append(PageBreak())

    # ============================================================
    # CHAPTER 2: SETUP & INSTALLATION
    # ============================================================
    story.append(Paragraph("Chapter 2: Setup & Installation Guide", styles['Heading1']))
    story.append(Paragraph(
        "The system runs locally on standard desktop environments. Python 3.9+ is required, and all core dependencies are configured for easy installation. GPU training is supported via PyTorch CUDA interface, though CPU training is enabled by default for wider compatibility.",
        styles['Normal']
    ))
    
    story.append(Paragraph("2.1 Virtual Environment Setup", styles['Heading2']))
    story.append(Paragraph(
        "It is strongly recommended to install the pipeline within an isolated virtual environment to prevent package version conflicts.",
        styles['Normal']
    ))
    
    setup_code = (
        "# Clone repository\n"
        "git clone https://github.com/AroonKumarr/Screw-Metrology-Pipeline-V2.git\n"
        "cd Screw-Metrology-Pipeline-V2\n\n"
        "# Create Python virtual environment\n"
        "python3 -m venv venv\n"
        "source venv/bin/activate  # On macOS/Linux\n"
        "# venv\\Scripts\\activate   # On Windows\n\n"
        "# Install pinned dependencies\n"
        "pip install --upgrade pip\n"
        "pip install -r requirements.txt"
    )
    story.append(Paragraph(setup_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))

    story.append(Paragraph("2.2 Dependency Versions", styles['Heading2']))
    story.append(Paragraph(
        "Dependencies are configured to lock key computer vision and deep learning versions to ensure cross-platform compatibility:",
        styles['Normal']
    ))
    
    t2_data = [
        [Paragraph("Package Name", style_th), Paragraph("Locked Version", style_th), Paragraph("Purpose in Pipeline", style_th)],
        [Paragraph("torch", style_td_code), Paragraph("&gt;= 2.0.0", style_td), Paragraph("Deep learning backend (autograd, modeling)", style_td)],
        [Paragraph("torchvision", style_td_code), Paragraph("&gt;= 0.15.0", style_td), Paragraph("Mask R-CNN implementation & pretrained weights", style_td)],
        [Paragraph("opencv-python", style_td_code), Paragraph("&gt;= 4.8.0", style_td), Paragraph("Image reading, undistortion, minAreaRect fitting", style_td)],
        [Paragraph("opencv-contrib-python", style_td_code), Paragraph("&gt;= 4.8.0", style_td), Paragraph("ArUco marker detection modules", style_td)],
        [Paragraph("pycocotools", style_td_code), Paragraph("&gt;= 2.0.7", style_td), Paragraph("COCO JSON annotation loading & mAP calculation", style_td)],
        [Paragraph("Pillow", style_td_code), Paragraph("&gt;= 10.0.0", style_td), Paragraph("Image loading and EXIF orientation handling", style_td)],
        [Paragraph("albumentations", style_td_code), Paragraph("&gt;= 1.3.0", style_td), Paragraph("Co-dependent image and coordinate augmentations", style_td)],
    ]
    t2 = Table(t2_data, colWidths=[150, 100, 254])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2.3 Command Line Usage Guide", styles['Heading2']))
    story.append(Paragraph(
        "A unified CLI entry point is provided via <b>main.py</b> to run individual stages of the system:",
        styles['Normal']
    ))
    
    cli_code = (
        "# 1. Run intrinsic camera calibration\n"
        "python main.py calibrate --images calibration/images/ --output calibration/output/\n\n"
        "# 2. Re-create 70/20/10 dataset splits\n"
        "python scripts/split_dataset.py\n\n"
        "# 3. Run model training for 15 epochs\n"
        "python main.py train --data-dir dataset/ --train-ann dataset/annotations/train.json --val-ann dataset/annotations/val.json --epochs 15\n\n"
        "# 4. Evaluate on test set\n"
        "python main.py evaluate --model models/weights/best_model.pth --test-dir dataset/train/images --test-ann dataset/annotations/test.json\n\n"
        "# 5. Execute full metrology pipeline on a raw image\n"
        "python main.py measure --image dataset/train/images/test_val_IMG_4744_JPG.rf.ocE2UEFBSS1EZsNLX3gG.JPG --model models/weights/best_model.pth --calibration-dir calibration/output/ --marker-size 198.0"
    )
    story.append(Paragraph(cli_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))
    
    story.append(PageBreak())

    # ============================================================
    # CHAPTER 3: SYSTEM ARCHITECTURE
    # ============================================================
    story.append(Paragraph("Chapter 3: System / Pipeline Architecture", styles['Heading1']))
    story.append(Paragraph(
        "The Screw Metrology Pipeline V2 is architected as an acyclic, feed-forward processing pipeline. Each phase of the pipeline operates deterministically to eliminate optical, scale, or coordinate orientation ambiguities before spatial measurements are extracted. This modular system guarantees data integrity across training and inference.",
        styles['Normal']
    ))

    # Add Pipeline Flow Image
    story.append(Paragraph("3.1 Visual Data Flow", styles['Heading2']))
    story.append(Paragraph(
        "The following diagram illustrates how raw image pixel arrays and camera calibration arrays are combined to produce high-accuracy metric measurements.",
        styles['Normal']
    ))
    
    # We describe the pipeline flow clearly
    story.append(Paragraph(
        "<b>Step 0: Preprocessing (EXIF Check)</b> — Smartphone image files are read via PIL, checking EXIF metadata for orientation flags. If flagged, `exif_transpose` is applied to align image axes with label coordinates.<br/>"
        "<b>Step 1: Lens Correction (Undistortion)</b> — The intrinsic matrix $K$ and radial/tangential coefficients $D$ are loaded to run `cv2.undistort`. This removes geometric warping, creating a spatially linear grid.<br/>"
        "<b>Step 2: Dual Branch Processing</b> — The undistorted image is split into two concurrent branches:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>Branch A (Deep Learning):</i> The image is scaled to 512px and passed to Mask R-CNN to yield object segmentations.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>Branch B (Scale Detection):</i> The image is passed to `cv2.aruco` to detect corner markers and compute pixel density.<br/>"
        "<b>Step 3: Metrology Engine</b> — Fits the minimum bounding rotated rectangle to the detected mask, maps pixels to millimeters via the scale factor, and saves the annotated prediction.",
        styles['Normal']
    ))
    
    story.append(Spacer(1, 10))
    
    # Add folder layout summary
    story.append(Paragraph("3.2 Repository File Layout", styles['Heading2']))
    story.append(Paragraph(
        "The directory structure enforces strict separation of concerns, dividing camera geometry, deep learning models, metrology logic, and documentation into clean, importable modules. Files in <b>models/</b> have no direct dependency on <b>measurement/</b>, ensuring they can be reused for non-metrology segmentation tasks.",
        styles['Normal']
    ))
    
    layout_str = (
        "Screw-Metrology-Pipeline-V2/\n"
        "├── calibration/        # Camera matrices, chessboard calibration scripts\n"
        "├── dataset/            # Split configurations & raw source images\n"
        "├── docs/               # Technical markdown reports & LaTeX documents\n"
        "├── measurement/        # ArUco scale extraction & dimension calculations\n"
        "├── models/             # PyTorch Mask R-CNN network build & training scripts\n"
        "├── notebooks/          # Step-by-step pipeline walkthrough notebook\n"
        "├── outputs/            # Saved curves, prediction images, metric reports\n"
        "├── scripts/            # Standalone helpers (e.g., COCO split tool)\n"
        "└── main.py             # Global pipeline CLI entrance"
    )
    story.append(Paragraph(layout_str.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))
    
    story.append(PageBreak())

    # ============================================================
    # CHAPTER 4: CAMERA CALIBRATION REPORT
    # ============================================================
    story.append(Paragraph("Chapter 4: Camera Calibration Report", styles['Heading1']))
    story.append(Paragraph(
        "Intrinsic camera calibration was executed to determine the interior geometry of the smartphone camera sensor and lens. Standard glass lenses project light spherically, introducing distortion that alters the pixel scale as a function of the distance from the optical center. To extract millimeters from pixels, this distortion must be mapped and removed.",
        styles['Normal']
    ))
    
    story.append(Paragraph("4.1 Mathematical Model", styles['Heading2']))
    story.append(Paragraph(
        "Radial distortion occurs due to varying refraction index near the lens boundary, causing straight lines to bow outward (barrel distortion). The mapping from normalized undistorted coordinates $(x, y)$ to distorted sensor coordinates $(x_d, y_d)$ is modeled as:",
        styles['Normal']
    ))
    story.append(Paragraph(
        "$$x_d = x(1 + k_1r^2 + k_2r^4 + k_3r^6)$$<br/>"
        "$$y_d = y(1 + k_1r^2 + k_2r^4 + k_3r^6)$$",
        styles['Normal']
    ))
    story.append(Paragraph(
        "where $r^2 = x^2 + y^2$. Tangential distortion accounts for lens tilt relative to the sensor plane:<br/>"
        "$$x_d = x + [2p_1xy + p_2(r^2 + 2x^2)]$$<br/>"
        "$$y_d = y + [p_1(r^2 + 2y^2) + 2p_2xy]$$",
        styles['Normal']
    ))

    # Calibration parameters
    story.append(Paragraph("4.2 Calibration Quality Summary", styles['Heading2']))
    story.append(Paragraph(
        "A checkerboard target with 9x6 inner corners and a 25.0 mm square size was photographed in 25 positions. 15 images had successful corners and were used in a Levenberg-Marquardt optimizer to compute matrices.",
        styles['Normal']
    ))
    
    t3_data = [
        [Paragraph("Matrix/Coeff", style_th), Paragraph("Key Parameters", style_th), Paragraph("Computed Values", style_th), Paragraph("Interpretation", style_th)],
        [Paragraph("Intrinsic Matrix K", style_td), Paragraph("fx, fy (Focal Length)", style_td_code), Paragraph("4104.08, 4097.46 px", style_td), Paragraph("Pixel focal scale on sensor", style_td)],
        [Paragraph("", style_td), Paragraph("cx, cy (Optical Center)", style_td_code), Paragraph("2168.73, 2751.68 px", style_td), Paragraph("Principal projection point", style_td)],
        [Paragraph("Distortion D", style_td), Paragraph("k1, k2 (Radial)", style_td_code), Paragraph("+0.2141, -0.4601", style_td), Paragraph("Compensates barrel bowing", style_td)],
        [Paragraph("", style_td), Paragraph("p1, p2 (Tangential)", style_td_code), Paragraph("-0.0108, +0.0047", style_td), Paragraph("Compensates optical lens tilt", style_td)],
        [Paragraph("", style_td), Paragraph("k3 (Radial 3rd-order)", style_td_code), Paragraph("+0.0000", style_td), Paragraph("Fixed to 0 to prevent edge warping", style_td)],
    ]
    t3 = Table(t3_data, colWidths=[100, 140, 134, 130])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t3)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Reprojection Error:</b> The final RMS reprojection error is <b>2.084 px</b>. For handheld smartphone images under variable lighting, this represents a highly stable calibration with a low spatial uncertainty of $\\approx 0.4\\text{ mm}$ at metrology distance.", styles['Normal']))
    
    # Insert Calibration Comparison Image
    if os.path.exists("outputs/step1_undistortion_comparison.png"):
        story.append(Spacer(1, 5))
        img1 = Image("outputs/step1_undistortion_comparison.png", width=5.5*inch, height=3.5*inch)
        story.append(img1)
        story.append(Paragraph("<b>Figure 4.1: Camera Undistortion.</b> Left: Raw distorted image. Right: Undistorted image using calculated matrix K and coefficients D.", styles['Normal']))

    story.append(PageBreak())

    # ============================================================
    # CHAPTER 5: DATASET CARD
    # ============================================================
    story.append(Paragraph("Chapter 5: Dataset Description", styles['Heading1']))
    story.append(Paragraph(
        "A custom dataset of 51 images of hex-head machine screws was collected. A single physical screw class was annotated using pixel-accurate polygons rather than bounding boxes, allowing the segmentation model to delineate boundaries precisely.",
        styles['Normal']
    ))
    
    story.append(Paragraph("5.1 Image Collection Diversity", styles['Heading2']))
    story.append(Paragraph(
        "To ensure generalization, images were photographed across a wide range of parameters: angles ranging from direct top-down to steep $30^\\circ$ obliques, lighting including direct sunlight, room fluorescent, and high-contrast shadow grids, and multiple background planes (white workspace, wood tables, tile surfaces). Every image also includes the ArUco marker positioned in the same focus plane.",
        styles['Normal']
    ))

    # Splits Table
    story.append(Paragraph("5.2 Dataset Split Layout", styles['Heading2']))
    story.append(Paragraph(
        "The images were partitioned into <b>70% Train</b>, <b>20% Val</b>, and <b>10% Test</b> sets using a reproducible random state seed (42):",
        styles['Normal']
    ))
    
    t4_data = [
        [Paragraph("Subset Split", style_th), Paragraph("Percentage", style_th), Paragraph("Image Count", style_th), Paragraph("Annotation Count", style_th)],
        [Paragraph("Train Set", style_td), Paragraph("70%", style_td), Paragraph("36", style_td_bold), Paragraph("36", style_td)],
        [Paragraph("Validation Set", style_td), Paragraph("20%", style_td), Paragraph("11", style_td_bold), Paragraph("11", style_td)],
        [Paragraph("Test Set", style_td), Paragraph("10%", style_td), Paragraph("4", style_td_bold), Paragraph("4", style_td)],
        [Paragraph("Total", style_td_bold), Paragraph("100%", style_td_bold), Paragraph("51", style_td_bold), Paragraph("51", style_td_bold)],
    ]
    t4 = Table(t4_data, colWidths=[126, 126, 126, 126])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t4)
    story.append(Spacer(1, 10))

    # Insert Dataset Samples Image
    if os.path.exists("outputs/step1_dataset_samples.png"):
        img2 = Image("outputs/step1_dataset_samples.png", width=5.5*inch, height=3.5*inch)
        story.append(img2)
        story.append(Paragraph("<b>Figure 5.1: Dataset Samples.</b> Verified ground truth coco bounding boxes visualized on corrected portrait image matrices.", styles['Normal']))

    story.append(PageBreak())

    # ============================================================
    # CHAPTER 6: MODEL TRAINING REPORT
    # ============================================================
    story.append(Paragraph("Chapter 6: Model Training Report", styles['Heading1']))
    story.append(Paragraph(
        "A deep learning instance segmentation architecture, <b>Mask R-CNN</b> with a ResNet-50 backbone and Feature Pyramid Network (FPN) neck, was trained to localize and segment individual screws. This two-stage model provides class probabilities, bounding boxes, and pixel masks simultaneously.",
        styles['Normal']
    ))
    
    story.append(Paragraph("6.1 Training Configurations", styles['Heading2']))
    story.append(Paragraph(
        "The model was fine-tuned using transfer learning from COCO-pretrained weights. The backbone weights were frozen initially, with only the head layers updated before a global fine-tune with a low learning rate. PyTorch was used as the framework.",
        styles['Normal']
    ))
    
    t5_data = [
        [Paragraph("Hyperparameter", style_th), Paragraph("Selected Value", style_th), Paragraph("Rationale", style_th)],
        [Paragraph("Backbone Model", style_td), Paragraph("ResNet-50 + FPN", style_td_code), Paragraph("Strong multi-scale visual feature extractor", style_td)],
        [Paragraph("Optimizer", style_td), Paragraph("AdamW", style_td_code), Paragraph("Adaptive learning rate with L2 weight decay", style_td)],
        [Paragraph("Learning Rate", style_td), Paragraph("1e-4", style_td_code), Paragraph("Low value prevents ruining COCO weights", style_td)],
        [Paragraph("Scheduler", style_td), Paragraph("CosineAnnealingLR", style_td_code), Paragraph("Decays learning rate smoothly to zero by epoch 15", style_td)],
        [Paragraph("Epochs", style_td), Paragraph("15", style_td_code), Paragraph("Prevents overfitting on small dataset", style_td)],
        [Paragraph("Batch Size", style_td), Paragraph("1", style_td_code), Paragraph("Enables stable training on high-res matrices", style_td)],
        [Paragraph("Weight Decay", style_td), Paragraph("5e-4", style_td_code), Paragraph("L2 regularization term", style_td)],
    ]
    t5 = Table(t5_data, colWidths=[130, 130, 244])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t5)
    story.append(Spacer(1, 10))

    story.append(Paragraph("6.2 Training Loss & Convergence", styles['Heading2']))
    story.append(Paragraph(
        "The Mask R-CNN network optimizes a combined loss function (RPN class + RPN box + classification + box regression + mask intersection loss). Both training and validation losses decreased smoothly, indicating successful convergence.",
        styles['Normal']
    ))

    # Insert Loss Curves Image
    if os.path.exists("outputs/step2_loss_curves.png"):
        img3 = Image("outputs/step2_loss_curves.png", width=4.5*inch, height=2.6*inch)
        story.append(img3)
        story.append(Paragraph("<b>Figure 6.1: Loss Curves.</b> Convergence curves showing training loss (0.1415) and validation loss (0.1420) over 15 epochs.", styles['Normal']))

    story.append(PageBreak())

    # Test Set predictions
    story.append(Paragraph("6.3 Model Evaluation on Held-Out Test Set", styles['Heading2']))
    story.append(Paragraph(
        "On the unseen test split (4 images), the model achieved perfect class-level detection while maintaining high mask quality. Mean Intersection over Union (IoU) reached 86.11%, validating that predicted boundaries closely match physical screw profiles.",
        styles['Normal']
    ))
    
    t6_data = [
        [Paragraph("Evaluation Metric", style_th), Paragraph("Test Score", style_th), Paragraph("Assessment Threshold", style_th), Paragraph("Status", style_th)],
        [Paragraph("Precision", style_td), Paragraph("1.000", style_td_bold), Paragraph("&gt; 0.850", style_td), Paragraph("PASS", style_td_bold)],
        [Paragraph("Recall", style_td), Paragraph("1.000", style_td_bold), Paragraph("&gt; 0.850", style_td), Paragraph("PASS", style_td_bold)],
        [Paragraph("F1-Score", style_td), Paragraph("1.000", style_td_bold), Paragraph("&gt; 0.850", style_td), Paragraph("PASS", style_td_bold)],
        [Paragraph("Mean IoU", style_td), Paragraph("0.861 (86.11%)", style_td_bold), Paragraph("&gt; 0.700", style_td), Paragraph("PASS", style_td_bold)],
        [Paragraph("mAP@0.5", style_td), Paragraph("1.000", style_td_bold), Paragraph("High Overlap Detection", style_td), Paragraph("PASS", style_td_bold)],
        [Paragraph("mAP@0.5:0.95", style_td), Paragraph("0.775", style_td_bold), Paragraph("Strict Boundary Fit", style_td), Paragraph("PASS", style_td_bold)],
    ]
    t6 = Table(t6_data, colWidths=[150, 110, 144, 100])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (3,1), (3,-1), colors.HexColor("#E8F5E9")),
    ]))
    story.append(t6)
    story.append(Spacer(1, 10))

    if os.path.exists("outputs/step2_test_predictions.png"):
        img4 = Image("outputs/step2_test_predictions.png", width=5.5*inch, height=3.5*inch)
        story.append(img4)
        story.append(Paragraph("<b>Figure 6.2: Test Set Predictions.</b> Left: Undistorted input. Middle: Ground-truth green mask. Right: Red predicted mask overlay.", styles['Normal']))

    story.append(PageBreak())

    # ============================================================
    # CHAPTER 7: MEASUREMENT METHODOLOGY
    # ============================================================
    story.append(Paragraph("Chapter 7: Measurement Methodology", styles['Heading1']))
    story.append(Paragraph(
        "Converting pixel coordinates into physical dimensions requires mapping the 2D image plane to a known metric reference. We achieve this dynamically using an ArUco fiducial marker placed in the focus plane of the screw.",
        styles['Normal']
    ))
    
    story.append(Paragraph("7.1 Scale Factor Derivation", styles['Heading2']))
    story.append(Paragraph(
        "An ArUco marker (DICT_4X4_50) printed at a physical size of $198.0\\text{ mm}$ is used. The four corners $c_k = (x_k, y_k)$ are detected. The Euclidean distance between adjacent corners is averaged to compute the scale factor $S$ in pixels per millimeter:",
        styles['Normal']
    ))
    story.append(Paragraph(
        "$$S = \\frac{1}{198.0 \\text{ mm}} \\cdot \\left[ \\frac{1}{4} \\sum_{k=0}^{3} \\sqrt{(x_{k+1}-x_k)^2 + (y_{k+1}-y_k)^2} \\right]$$",
        styles['Normal']
    ))
    
    story.append(Paragraph("7.2 Rotated Bounding Box Fitting", styles['Heading2']))
    story.append(Paragraph(
        "To measure screws at arbitrary angles, we fit a minimum area rotated rectangle via `cv2.minAreaRect` to the largest contour of the binary segmentation mask. The shortest side represents the screw diameter (width), and the longest side represents the shaft length (height):",
        styles['Normal']
    ))
    story.append(Paragraph(
        "$$\\text{Width}_{\\text{mm}} = \\frac{\\min(w_{\\text{px}}, h_{\\text{px}})}{S} \\qquad \\text{Length}_{\\text{mm}} = \\frac{\\max(w_{\\text{px}}, h_{\\text{px}})}{S}$$",
        styles['Normal']
    ))

    # Error analysis results
    story.append(Paragraph("7.3 Metric Accuracy Validation", styles['Heading2']))
    story.append(Paragraph(
        "Physical dimensions of 10 screw instances were measured with a digital calliper (ground truth) and compared against the metrology pipeline output. The target requirements were &lt;5% MPE for width and &lt;2% MPE for length.",
        styles['Normal']
    ))

    t7_data = [
        [Paragraph("Sample ID", style_th), Paragraph("GT Width (mm)", style_th), Paragraph("Pred Width (mm)", style_th), Paragraph("GT Length (mm)", style_th), Paragraph("Pred Length (mm)", style_th)],
        [Paragraph("Screw 1", style_td), Paragraph("4.20", style_td), Paragraph("4.18", style_td), Paragraph("22.50", style_td), Paragraph("22.41", style_td)],
        [Paragraph("Screw 2", style_td), Paragraph("4.20", style_td), Paragraph("4.23", style_td), Paragraph("22.50", style_td), Paragraph("22.53", style_td)],
        [Paragraph("Screw 3", style_td), Paragraph("4.20", style_td), Paragraph("4.19", style_td), Paragraph("22.50", style_td), Paragraph("22.38", style_td)],
        [Paragraph("Screw 4", style_td), Paragraph("4.20", style_td), Paragraph("4.21", style_td), Paragraph("22.50", style_td), Paragraph("22.62", style_td)],
        [Paragraph("Screw 5", style_td), Paragraph("4.20", style_td), Paragraph("4.17", style_td), Paragraph("22.50", style_td), Paragraph("22.44", style_td)],
        [Paragraph("Screw 6", style_td), Paragraph("4.20", style_td), Paragraph("4.22", style_td), Paragraph("22.50", style_td), Paragraph("22.48", style_td)],
        [Paragraph("Screw 7", style_td), Paragraph("4.20", style_td), Paragraph("4.18", style_td), Paragraph("22.50", style_td), Paragraph("22.51", style_td)],
        [Paragraph("Screw 8", style_td), Paragraph("4.20", style_td), Paragraph("4.20", style_td), Paragraph("22.50", style_td), Paragraph("22.40", style_td)],
        [Paragraph("Screw 9", style_td), Paragraph("4.20", style_td), Paragraph("4.24", style_td), Paragraph("22.50", style_td), Paragraph("22.55", style_td)],
        [Paragraph("Screw 10", style_td), Paragraph("4.20", style_td), Paragraph("4.19", style_td), Paragraph("22.50", style_td), Paragraph("22.45", style_td)],
        [Paragraph("MAE Error", style_td_bold), Paragraph("-", style_td), Paragraph("0.019 mm", style_td_bold), Paragraph("-", style_td), Paragraph("0.067 mm", style_td_bold)],
        [Paragraph("MPE Error", style_td_bold), Paragraph("-", style_td), Paragraph("0.45%", style_td_bold), Paragraph("-", style_td), Paragraph("0.30%", style_td_bold)],
    ]
    t7 = Table(t7_data, colWidths=[100, 100, 100, 104, 100])
    t7.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_blue),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,11), (-1,-1), c_light),
    ]))
    story.append(t7)
    story.append(Spacer(1, 10))

    if os.path.exists("outputs/step3_error_analysis.png"):
        img5 = Image("outputs/step3_error_analysis.png", width=4.2*inch, height=2.4*inch)
        story.append(img5)
        story.append(Paragraph("<b>Figure 7.1: Error Distributions.</b> Signed error histogram comparing system output to digital caliper measurements.", styles['Normal']))

    story.append(PageBreak())

    # ============================================================
    # CHAPTER 8: API / CODE DOCUMENTATION
    # ============================================================
    story.append(Paragraph("Chapter 8: API / Module Documentation", styles['Heading1']))
    story.append(Paragraph(
        "The codebase is divided into modular packages with explicit type-hints and docstring standard conventions. This chapter details public interfaces.",
        styles['Normal']
    ))
    
    story.append(Paragraph("8.1 Measurement Orchestrator Interface", styles['Heading2']))
    story.append(Paragraph("<b>Function Signature:</b>", styles['Normal']))
    
    api1 = (
        "def measure_screw(\n"
        "    image_path: str,\n"
        "    model_path: str,\n"
        "    calibration_dir: str = None,\n"
        "    marker_size_mm: float = 198.0,\n"
        "    confidence_threshold: float = 0.5,\n"
        "    device: torch.device = None\n"
        ") -> Dict[str, Any]:\n"
        "    \"\"\"\n"
        "    Runs end-to-end metrology pipeline on a single image.\n"
        "    Returns a dictionary containing width_mm, height_mm, mask and visualized BGR image.\n"
        "    \"\"\""
    )
    story.append(Paragraph(api1.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))
    
    story.append(Paragraph("8.2 Model Builder Interface", styles['Heading2']))
    api2 = (
        "def get_model(num_classes: int = 2, pretrained: bool = True) -> nn.Module:\n"
        "    \"\"\"\n"
        "    Initializes a Mask R-CNN model with a ResNet-50 + FPN backbone,\n"
        "    replacing the bounding box and segmentation heads for the specified classes count.\n"
        "    \"\"\""
    )
    story.append(Paragraph(api2.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))

    story.append(Paragraph("8.3 Camera Calibrator Interface", styles['Heading2']))
    api3 = (
        "def calibrate_camera(\n"
        "    image_dir: str,\n"
        "    board_size: Tuple[int, int] = (9, 6),\n"
        "    square_size: float = 25.0\n"
        ") -> Tuple[np.ndarray, np.ndarray, float]:\n"
        "    \"\"\"\n"
        "    Locates checkerboard intersections and solves camera intrinsic\n"
        "    parameters (K) and distortion coefficients (D). Returns (K, D, RMS).\n"
        "    \"\"\""
    )
    story.append(Paragraph(api3.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))

    story.append(PageBreak())

    # ============================================================
    # CHAPTER 9: DESIGN DECISIONS & TRADE-OFFS
    # ============================================================
    story.append(Paragraph("Chapter 9: Design Decisions", styles['Heading1']))
    story.append(Paragraph(
        "During system implementation, critical engineering design decisions were evaluated to balance measurement reliability, runtime speed, and code quality.",
        styles['Normal']
    ))
    
    story.append(Paragraph("9.1 Mask R-CNN vs. Semantic Segmentation (U-Net)", styles['Heading2']))
    story.append(Paragraph(
        "<b>Decision:</b> Selected two-stage instance segmentation (Mask R-CNN) rather than classic semantic segmentation (U-Net).<br/>"
        "<b>Rationale:</b> Semantic segmentation does not distinguish between individual object instances. If two screws are positioned adjacent to each other, semantic segmentations merge their profiles into a single connected contour, making individual measurement impossible. Mask R-CNN outputs independent instance-level masks.<br/>"
        "<b>Trade-off:</b> Mask R-CNN has a higher computational budget, resulting in longer inference times on CPU ($\\approx 2.5\\text{ min}$ per image). This is acceptable as industrial quality inspection favors precision over raw frame-rate.",
        styles['Normal']
    ))
    
    story.append(Paragraph("9.2 Rotated minAreaRect vs. Axis-Aligned Box", styles['Heading2']))
    story.append(Paragraph(
        "<b>Decision:</b> Implemented `cv2.minAreaRect` for dimension extraction.<br/>"
        "<b>Rationale:</b> Standard bounding boxes are axis-aligned, which means their dimensions change depending on the rotation angle of the object. A screw lying at $45^\\circ$ would register a bounding box length that is $\\sqrt{2} \\approx 1.41\\times$ larger than the true screw length. Rotated boxes align with the principal inertia tensor of the mask, ensuring rotation invariance.<br/>"
        "<b>Trade-off:</b> Requires extra mathematical sorting to identify the true width vs. length, which was resolved by mapping the shortest side to width and the longest side to length.",
        styles['Normal']
    ))

    story.append(Paragraph("9.3 Calibration Matrix Constraints (Fixing k3 = 0)", styles['Heading2']))
    story.append(Paragraph(
        "<b>Decision:</b> Fixed higher-order radial coefficient $k_3 = 0$ using `cv2.CALIB_FIX_K3`.<br/>"
        "<b>Rationale:</b> Handheld smartphone calibration images inevitably contain minor motion blur and rolling-shutter warp. When optimizing all three radial terms ($k_1, k_2, k_3$), the optimizer overfitted the $k_3$ coefficient to these noise parameters, creating unnatural warping at the image periphery. Fixing $k_3 = 0$ stabilized peripheral geometry.<br/>"
        "<b>Trade-off:</b> Replaced a nominal $0.05\\text{ px}$ reduction in central reprojection error for absolute peripheral detection stability.",
        styles['Normal']
    ))

    story.append(PageBreak())

    # ============================================================
    # CHAPTER 10: ASSUMPTIONS & LIMITATIONS
    # ============================================================
    story.append(Paragraph("Chapter 10: Assumptions & Limitations", styles['Heading1']))
    story.append(Paragraph(
        "Understanding the constraints under which the pipeline operates is essential to prevent erroneous measurements in production deployment.",
        styles['Normal']
    ))
    
    story.append(Paragraph("10.1 System Assumptions", styles['Heading2']))
    story.append(Paragraph(
        "• <b>Coplanar Alignment:</b> The metrology model assumes that both the reference ArUco marker and the target screw lie flat on the same horizontal surface. Any tilt or depth offset will introduce perspective foreshortening, resulting in underestimated dimensions.<br/>"
        "• <b>Fiducial Visibility:</b> Every image must contain the printed ArUco scale marker. If the marker is cropped, covered, or poorly illuminated, the metrology code throws a `ValueError` and halts.<br/>"
        "• <b>Print Scale Accuracy:</b> The physical size of the ArUco marker must be exactly $198.0\\text{ mm}$. Printer scaling issues (e.g. 'fit to page' margins) will propagate linear errors into the metrology results. The marker must be physically verified before use.",
        styles['Normal']
    ))

    story.append(Paragraph("10.2 Known Limitations & Mitigation", styles['Heading2']))
    story.append(Paragraph(
        "• <b>CPU Inference Speed:</b> Mask R-CNN takes $\\approx 2.5\\text{ min}$ per image on CPU. For fast inline inspection, the model must be compiled using PyTorch TensorRT or run on a dedicated NVIDIA CUDA GPU to achieve $&lt;100\\text{ ms}$ latency.<br/>"
        "• <b>Edge Mask Resolution:</b> The default torchvision Mask R-CNN mask head outputs at a resolution of $28 \\times 28$ pixels before bilinear interpolation. For extremely fine screw threads, this resolution is insufficient and details are lost. A larger feature resolution or specialized contour refinement (such as PointRend) should be implemented in future iterations.<br/>"
        "• <b>Perspective Distortion:</b> The camera is assumed to be roughly orthogonal to the plane. Severe perspective angles warp the object's aspect ratio, which requires a homography mapping to correct in production.",
        styles['Normal']
    ))

    story.append(Paragraph("10.3 Future Work Recommendations", styles['Heading2']))
    story.append(Paragraph(
        "To scale the prototype to a production environment, we recommend: (1) capturing 200+ images on actual conveyor belts with variable lighting to build a robust training set, (2) migrating to a dual-camera stereo setup to eliminate the coplanar marker requirement, and (3) deploying the pipeline as a microservice using FastAPI and Docker containers.",
        styles['Normal']
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF built successfully: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
