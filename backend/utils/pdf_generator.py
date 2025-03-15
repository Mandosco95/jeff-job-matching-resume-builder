from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import black, gray
import markdown
from bs4 import BeautifulSoup
from io import BytesIO

class PDFGenerator:
    @staticmethod
    def get_style_definitions():
        styles = getSampleStyleSheet()
        return {
            'CustomName': {
                'parent': styles['Heading1'],
                'fontSize': 24,
                'textColor': black,
                'spaceAfter': 20,
                'alignment': TA_CENTER,
                'leading': 28
            },
            'CustomContact': {
                'parent': styles['Normal'],
                'fontSize': 11,
                'textColor': gray,
                'alignment': TA_CENTER,
                'spaceAfter': 20
            },
            'CustomSection': {
                'parent': styles['Heading2'],
                'fontSize': 14,
                'textColor': black,
                'spaceBefore': 15,
                'spaceAfter': 10,
                'alignment': TA_LEFT,
                'borderWidth': 1,
                'borderColor': gray,
                'borderPadding': (0, 0, 8, 0)
            },
            'CustomNormal': {
                'parent': styles['Normal'],
                'fontSize': 11,
                'textColor': black,
                'alignment': TA_LEFT,
                'spaceBefore': 6,
                'spaceAfter': 6,
                'leading': 14
            },
            'CustomBullet': {
                'parent': styles['Normal'],
                'fontSize': 11,
                'textColor': black,
                'alignment': TA_LEFT,
                'leftIndent': 20,
                'spaceBefore': 0,
                'spaceAfter': 6,
                'bulletIndent': 10,
                'leading': 14
            }
        }

    @staticmethod
    def setup_styles(doc):
        styles = getSampleStyleSheet()
        style_definitions = PDFGenerator.get_style_definitions()
        
        # Safely add or update styles
        for style_name, style_props in style_definitions.items():
            parent = style_props.pop('parent')
            if style_name in styles:
                # Update existing style
                for prop, value in style_props.items():
                    setattr(styles[style_name], prop, value)
            else:
                # Create new style
                styles.add(ParagraphStyle(
                    name=style_name,
                    parent=parent,
                    **style_props
                ))
        return styles

    @staticmethod
    def create_pdf(text: str, is_resume: bool = True) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        styles = PDFGenerator.setup_styles(doc)
        
        # Convert markdown to HTML
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, 'html.parser')
        
        story = []
        
        if is_resume:
            PDFGenerator._process_resume_content(soup, story, styles)
        else:
            PDFGenerator._process_cover_letter_content(soup, story, styles)

        # Build PDF
        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def _process_resume_content(soup, story, styles):
        for element in soup.find_all(['h1', 'h2', 'p', 'ul']):
            if element.name == 'h1':
                story.append(Paragraph(element.get_text().strip(), styles['CustomName']))
            elif element.name == 'h2':
                story.append(Paragraph(element.get_text().strip(), styles['CustomSection']))
            elif element.name == 'p':
                if not story:
                    story.append(Paragraph(element.get_text().strip(), styles['CustomName']))
                elif len(story) == 1:
                    story.append(Paragraph(element.get_text().strip(), styles['CustomContact']))
                else:
                    story.append(Paragraph(element.get_text().strip(), styles['CustomNormal']))
            elif element.name == 'ul':
                PDFGenerator._process_bullet_points(element, story, styles)

    @staticmethod
    def _process_cover_letter_content(soup, story, styles):
        for element in soup.find_all(['h1', 'p']):
            if element.name == 'h1':
                story.append(Paragraph(element.get_text().strip(), styles['CustomNormal']))
                story.append(Spacer(1, 12))
            else:
                story.append(Paragraph(element.get_text().strip(), styles['CustomNormal']))
                story.append(Spacer(1, 12))

    @staticmethod
    def _process_bullet_points(element, story, styles):
        bullets = []
        for li in element.find_all('li'):
            bullets.append(
                ListItem(
                    Paragraph(li.get_text().strip(), styles['CustomBullet']),
                    leftIndent=20,
                    bulletFormat='•'
                )
            )
        story.append(ListFlowable(
            bullets,
            bulletType='bullet',
            start='•'
        )) 