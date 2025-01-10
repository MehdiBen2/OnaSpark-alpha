from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from datetime import datetime
import os
import tempfile
from .water_quality import PARAMETER_METADATA

def clean_unit_name(unit_text):
    """Clean and format the unit name"""
    if not unit_text:
        return "N/A"
    
    # If unit_text is a string
    if isinstance(unit_text, str):
        prefixes = ["UNITE DE ", "Unité de ", "UNITÉ DE ", "Unite de "]
        cleaned_text = unit_text
        for prefix in prefixes:
            if cleaned_text.upper().startswith(prefix.upper()):
                cleaned_text = cleaned_text[len(prefix):]
                break
        return cleaned_text.strip()
    
    # If unit_text is an object (like Unit model), try to get the name
    try:
        if hasattr(unit_text, 'name'):
            return clean_unit_name(unit_text.name)
        return str(unit_text)
    except (AttributeError, TypeError):
        return "N/A"

def create_paragraph_style(name, font_name='Helvetica', font_size=10, text_color=colors.black, 
                         alignment=0, space_before=0, space_after=0, leading=12):
    """Create a custom paragraph style"""
    return ParagraphStyle(
        name,
        fontName=font_name,
        fontSize=font_size,
        textColor=text_color,
        alignment=alignment,
        spaceBefore=space_before,
        spaceAfter=space_after,
        leading=leading,
        wordWrap='CJK'  # Improved word wrapping
    )

def create_incident_pdf(incidents, output_path, unit=None):
    """Generate a PDF report for incidents"""
    # Document setup
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    elements = []
    
    # Custom styles
    title_style = create_paragraph_style(
        'CustomTitle',
        font_name='Helvetica',
        font_size=14,
        alignment=0,  # Left alignment
        space_after=2
    )
    
    # Header with logo
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'ona_logoFull.png')
    
    # Create header content
    header_text = [
        [Paragraph("OFFICE NATIONAL DE L'ASSAINISSEMENT", title_style)],
        [Paragraph("ZONE D'ALGER", title_style)]
    ]
    
    if unit:
        cleaned_unit = clean_unit_name(unit)
        if cleaned_unit:
            header_text.append([Paragraph(f"UNITE DE {cleaned_unit.upper()}", title_style)])
    
    # Create header table with logo
    if os.path.exists(logo_path):
        img = Image(logo_path)
        img.drawHeight = 2.0 * inch
        img.drawWidth = 2.0 * inch
        
        header_table_data = [
            [
                Table(header_text, colWidths=[350]),#img
                img
            ]
        ]
        
        header_table = Table(header_table_data, colWidths=[400, 200])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(header_table)
    else:
        header_table = Table(header_text)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(header_table)
    
    # Add title "Rapport des Incidents"
    title_style = create_paragraph_style(
        'ReportTitle',
        font_name='Helvetica-Bold',
        font_size=16,
        alignment=1,  # Center
        space_before=20,
        space_after=20
    )
    elements.append(Paragraph("Rapport des Incidents", title_style))
    
    # Add generation date
    date_style = create_paragraph_style('DateStyle', font_size=10, alignment=0)
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    elements.append(Paragraph(f"Généré le {generation_date}", date_style))
    elements.append(Spacer(1, 10))
    
    # Create cell styles for content
    cell_style = create_paragraph_style(
        'CellStyle',
        font_size=9,
        leading=12,
        alignment=4  # Justified alignment
    )
    
    # Table headers
    headers = [
        'Type de Station',
        'Wilaya',
        'Commune',
        'Localités',
        'Nature et Cause',
        'Date et Heure',
        'Mesures Prises',
        'Impact'
    ]
    
    # Convert headers to Paragraph objects
    header_style = create_paragraph_style(
        'HeaderStyle',
        font_name='Helvetica-Bold',
        font_size=10,
        alignment=1  # Center alignment
    )
    headers = [Paragraph(h, header_style) for h in headers]
    
    # Table data with proper text wrapping
    data = [headers]
    for incident in incidents:
        row = [
            Paragraph('Conduits', cell_style),
            Paragraph(incident.wilaya, cell_style),
            Paragraph(incident.commune, cell_style),
            Paragraph(incident.localite, cell_style),
            Paragraph(incident.nature_cause, cell_style),
            Paragraph(incident.date_incident.strftime('%Y-%m-%d\n%H:%M'), cell_style),
            Paragraph(incident.mesures_prises, cell_style),
            Paragraph(incident.impact, cell_style)
        ]
        data.append(row)
    
    # Column widths in millimeters (adjusted for better text display)
    col_widths = [25*mm, 20*mm, 25*mm, 25*mm, 35*mm, 25*mm, 35*mm, 35*mm]
    
    # Create table with row heights
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Table style
    table_style = TableStyle([
        # Header style - using the exact color from the image
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8cb2e3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        
        # Alignment
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Font
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        # Minimum row height
        ('MINROWHEIGHT', (0, 0), (-1, -1), 40),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)

def generate_water_quality_pdf(result_data, output_path=None):
    """
    Generate a professional PDF report for water quality assessment.
    
    Args:
        result_data: Dictionary containing water quality assessment results
        output_path: Optional path to save the PDF. If None, generates in a temporary directory.
    Returns:
        Path to the generated PDF file
    """
    if output_path is None:
        # Create a temporary file with .pdf extension
        temp_fd, output_path = tempfile.mkstemp(suffix='.pdf', prefix='Rapport_Qualite_Eau_')
        os.close(temp_fd)  # Close the file descriptor as we'll use the path
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = styles['Title'].clone('Title')
    title_style.fontSize = 16
    title_style.textColor = colors.darkblue
    
    subtitle_style = styles['Heading2'].clone('Subtitle')
    subtitle_style.fontSize = 14
    subtitle_style.textColor = colors.darkblue
    
    normal_style = styles['Normal'].clone('Normal')
    normal_style.fontSize = 10

    # Date style
    date_style = styles['Normal'].clone('Date')
    date_style.fontSize = 10
    date_style.alignment = 2  # Right alignment
    
    # Footer style
    footer_style = styles['Normal'].clone('Footer')
    footer_style.fontSize = 8
    footer_style.textColor = colors.darkblue
    footer_style.alignment = 1  # Center alignment
    
    story = []

    # Add Header
    logo_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'ona_logoFull.png'),
        os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'ona_logo.png')
    ]
    
    logo_added = False
    for logo_path in logo_paths:
        try:
            if os.path.exists(logo_path):
                from PIL import Image as PILImage
                
                # Open image and maintain aspect ratio
                pil_img = PILImage.open(logo_path)
                original_width, original_height = pil_img.size
                
                # Calculate new dimensions maintaining aspect ratio
                max_width = 2*inch
                aspect_ratio = original_width / original_height
                new_height = max_width / aspect_ratio
                
                # Create ReportLab Image with correct dimensions
                logo = Image(logo_path, width=max_width, height=new_height)
                story.append(logo)
                logo_added = True
                break
        except Exception as e:
            print(f"Could not add logo from {logo_path}: {e}")
    
    if not logo_added:
        # Add a text placeholder if no logo is found
        story.append(Paragraph("OFFICE NATIONAL D'ASSAINISSEMENT", title_style))

    # Add Date
    current_date = datetime.now().strftime("%d/%m/%Y")
    story.append(Paragraph(f"Date: {current_date}", date_style))
    story.append(Spacer(1, 12))

    # Title
    title = Paragraph("Rapport d'Évaluation de la Qualité de l'Eau", title_style)
    story.append(title)
    story.append(Spacer(1, 12))

    # General Classification
    rating_info = result_data.get('rating_info', {})
    classification_text = Paragraph(f"Classification Générale: {rating_info.get('title', 'N/A')}", subtitle_style)
    classification_desc = Paragraph(rating_info.get('description', 'Aucune description disponible'), normal_style)
    story.append(classification_text)
    story.append(classification_desc)
    story.append(Spacer(1, 12))

    # Parameters Table
    parameter_data = [['Paramètre', 'Valeur', 'Unité']]
    parameters = result_data.get('parameters', {})
    
    for param_type in ['microbiological', 'physical', 'chemical', 'toxic']:
        for param_name, param_value in parameters.items():
            if param_name in PARAMETER_METADATA.get(param_type, {}).get('parameters', {}):
                param_info = PARAMETER_METADATA[param_type]['parameters'][param_name]
                parameter_data.append([
                    param_info.get('name', param_name),
                    str(param_value),
                    param_info.get('unit', '')
                ])

    parameter_table = Table(parameter_data, colWidths=[3*inch, 1.5*inch, 1*inch])
    parameter_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.Color(0.2, 0.4, 0.6, 0.5)),  # Softer blue background
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.Color(0.9, 0.9, 1, 0.5)),  # Light blue background
        ('GRID', (0,0), (-1,-1), 1, colors.Color(0.7, 0.7, 0.7)),  # Soft grey grid
        ('FONTSIZE', (0,1), (-1,-1), 9)
    ]))
    story.append(parameter_table)
    story.append(Spacer(1, 12))

    # Helper function to create consistent tables
    def create_styled_table(title, data_list, styles_sheet):
        # Create table data
        table_data = [[title]]
        for item in data_list or [f'Aucun {title.lower()}']:
            table_data.append([item])
        
        # Create table
        table = Table(table_data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.2, 0.4, 0.6, 0.5)),  # Softer blue background
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.Color(0.9, 0.9, 1, 0.5)),  # Light blue background
            ('GRID', (0,0), (-1,-1), 1, colors.Color(0.7, 0.7, 0.7)),  # Soft grey grid
            ('FONTSIZE', (0,1), (-1,-1), 9)
        ]))
        return table

    # Water Quality Norms and Standards Section
    norms_title = Paragraph("Normes et Standards de Qualité de l'Eau", subtitle_style)
    story.append(norms_title)
    story.append(Spacer(1, 12))

    # Detailed Norms Content
    norms_content = [
        "1. Paramètres Microbiologiques:",
        "   - Coliformes fécaux : Maximum 0 CFU/100ml pour l'irrigation",
        "   - Nématodes : Maximum 1 œuf/L selon les normes OMS",
        "",
        "2. Paramètres Physiques:",
        "   - pH : Entre 6.5 et 8.5 (acceptable pour l'irrigation)",
        "   - Conductivité Électrique (CE) : < 3 dS/m pour une irrigation sans risque",
        "   - Matières En Suspension (MES) : < 50 mg/L",
        "",
        "3. Paramètres Chimiques:",
        "   - DBO5 : < 30 mg/L (indiquant une faible charge organique)",
        "   - DCO : < 100 mg/L (niveau acceptable de pollution organique)",
        "   - Chlorures : < 350 meq/L pour minimiser les risques de salinité",
        "",
        "4. Éléments Toxiques (Limites Maximales):",
        "   - Cadmium : < 0.01 mg/L",
        "   - Mercure : < 0.001 mg/L",
        "   - Arsenic : < 0.1 mg/L",
        "   - Plomb : < 0.1 mg/L",
        "",
        "Recommandations Générales :",
        "- Toujours traiter l'eau avant utilisation",
        "- Effectuer des tests réguliers de qualité de l'eau",
        "- Consulter les autorités locales pour des normes spécifiques"
    ]

    # Create Paragraph style for norms
    norms_style = styles['Normal'].clone('NormsStyle')
    norms_style.fontSize = 9
    norms_style.leading = 12

    # Add norms content
    for line in norms_content:
        story.append(Paragraph(line, norms_style))
    
    story.append(Spacer(1, 12))

    # Allowed Crops
    crops_text = Paragraph("Cultures Autorisées:", subtitle_style)
    story.append(crops_text)
    story.append(create_styled_table('Cultures', result_data.get('allowed_crops', []), styles))
    story.append(Spacer(1, 12))

    # Restrictions
    restrictions_text = Paragraph("Restrictions:", subtitle_style)
    story.append(restrictions_text)
    story.append(create_styled_table('Restrictions', result_data.get('restrictions', []), styles))
    story.append(Spacer(1, 12))

    # Violations
    violations_text = Paragraph("Paramètres Hors Normes:", subtitle_style)
    story.append(violations_text)
    story.append(create_styled_table('Violations', result_data.get('violations', ['Tous les paramètres sont conformes']), styles))

    # Add Footer with governmental details
    story.append(Spacer(1, 20))
    footer_text = [
        "OFFICE NATIONAL DE L'ASSAINISSEMENT",
        "République Algérienne Démocratique et Populaire",
        "Ministère des Ressources en Eau",
        " 2025 ONA Spark - Tous droits réservés"
    ]
    
    for line in footer_text:
        story.append(Paragraph(line, footer_style))
        story.append(Spacer(1, 4))

    # Build PDF
    doc.build(story)
    
    return output_path
