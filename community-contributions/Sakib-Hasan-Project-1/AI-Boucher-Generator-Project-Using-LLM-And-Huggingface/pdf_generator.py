from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle

from reportlab.lib.enums import TA_CENTER

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

from reportlab.lib.units import inch


# ============================================================
# CREATE BROCHURE PDF
# ============================================================

def create_brochure_pdf(
    brochure_data,
    image_path,
    output_path="ai_brochure.pdf"
):

    # --------------------------------------------------------
    # 1. CREATE PDF DOCUMENT
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )


    # --------------------------------------------------------
    # 2. LOAD DEFAULT STYLES
    # --------------------------------------------------------

    styles = getSampleStyleSheet()


    # --------------------------------------------------------
    # 3. CREATE CUSTOM STYLES
    # --------------------------------------------------------

    title_style = ParagraphStyle(
        "BrochureTitle",
        parent=styles["Title"],
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        spaceAfter=20
    )


    heading_style = ParagraphStyle(
        "BrochureHeading",
        parent=styles["Heading2"],
        fontSize=18,
        leading=22,
        spaceBefore=15,
        spaceAfter=10
    )


    body_style = ParagraphStyle(
        "BrochureBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=17,
        spaceAfter=10
    )


    bullet_style = ParagraphStyle(
        "BrochureBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6
    )


    # --------------------------------------------------------
    # 4. CREATE CONTENT CONTAINER
    # --------------------------------------------------------

    story = []


    # ========================================================
    # COVER PAGE
    # ========================================================

    story.append(
        Spacer(1, 40)
    )


    story.append(
        Paragraph(
            "AI GENERATED BROCHURE",
            title_style
        )
    )


    story.append(
        Spacer(1, 20)
    )


    # --------------------------------------------------------
    # ADD IMAGE
    # --------------------------------------------------------

    if image_path:

        brochure_image = Image(
            image_path,
            width=5.8 * inch,
            height=4.2 * inch
        )

        story.append(
            brochure_image
        )


    story.append(
        Spacer(1, 25)
    )


    # --------------------------------------------------------
    # COMPANY OVERVIEW
    # --------------------------------------------------------

    company_overview = brochure_data.get(
        "company_overview",
        ""
    )


    if company_overview:

        story.append(
            Paragraph(
                "Company Overview",
                heading_style
            )
        )

        story.append(
            Paragraph(
                company_overview,
                body_style
            )
        )


    story.append(
        PageBreak()
    )


    # ========================================================
    # PRODUCTS & SERVICES
    # ========================================================

    story.append(
        Paragraph(
            "Products & Services",
            heading_style
        )
    )


    products_services = brochure_data.get(
        "products_services",
        []
    )


    for product in products_services:

        story.append(
            Paragraph(
                f"• {product}",
                bullet_style
            )
        )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # KEY FEATURES
    # ========================================================

    story.append(
        Paragraph(
            "Key Features",
            heading_style
        )
    )


    key_features = brochure_data.get(
        "key_features",
        []
    )


    for feature in key_features:

        story.append(
            Paragraph(
                f"• {feature}",
                bullet_style
            )
        )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # MISSION
    # ========================================================

    story.append(
        Paragraph(
            "Our Mission",
            heading_style
        )
    )


    mission = brochure_data.get(
        "mission",
        ""
    )


    if mission:

        story.append(
            Paragraph(
                mission,
                body_style
            )
        )


    # ========================================================
    # IMPORTANT INFORMATION
    # ========================================================

    important_information = brochure_data.get(
        "important_information",
        ""
    )


    if important_information:

        story.append(
            Paragraph(
                "Important Information",
                heading_style
            )
        )

        story.append(
            Paragraph(
                important_information,
                body_style
            )
        )


    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story
    )


    print(
        f"PDF generated successfully: {output_path}"
    )


    return output_path