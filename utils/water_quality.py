"""
Water quality assessment module for evaluating treated wastewater reuse in agriculture.
Based on official Algerian standards and regulations.
"""

# Water quality assessment constants
WATER_QUALITY_THRESHOLDS = {
    'microbiological': {
        'coliform_fecal': {'A': 100, 'B': 1000},
        'nematodes': {'A': 0.1, 'B': 1.0}
    },
    'physical': {
        'ph': {'min': 6.5, 'max': 8.5},
        'mes': {'max': 30},
        'ce': {'max': 3}
    },
    'chemical': {
        'dbo5': {'max': 30},
        'dco': {'max': 90},
        'chlorure': {'max': 10}
    },
    'toxic': {
        'cadmium': {'max': 0.05},
        'mercury': {'max': 0.002},
        'arsenic': {'max': 0.5},
        'lead': {'max': 0.05}
    }
}

CROP_CATEGORIES = {
    'category1': {
        'name': 'Légumes consommés crus',
        'requirements': {'micro': 'A', 'physico': 'OK'},
        'restrictions': []
    },
    'category2': {
        'name': 'Arbres fruitiers',
        'requirements': {'micro': 'B', 'physico': 'OK'},
        'restrictions': ["Arrêter l'irrigation 2 semaines avant la récolte", "Ne pas ramasser les fruits tombés"]
    },
    'category3': {
        'name': 'Cultures fourragères',
        'requirements': {'micro': 'B', 'physico': 'OK'},
        'restrictions': ["Pas de pâturage direct", "Arrêter l'irrigation 1 semaine avant la coupe"]
    },
    'category4': {
        'name': 'Cultures industrielles et céréalières',
        'requirements': {'micro': 'C', 'physico': 'OK'},
        'restrictions': ["Paramètres plus permissifs possibles selon réglementation"]
    }
}

# Parameter metadata for UI and validation
PARAMETER_METADATA = {
    'microbiological': {
        'title': 'Paramètres Microbiologiques',
        'icon': 'bacteria',
        'color': 'info',
        'parameters': {
            'coliform_fecal': {
                'name': 'Coliformes fécaux',
                'unit': 'CFU/100ml',
                'step': 0.1,
                'min': 0
            },
            'nematodes': {
                'name': 'Nématodes',
                'unit': 'œufs/L',
                'step': 0.01,
                'min': 0
            }
        }
    },
    'physical': {
        'title': 'Paramètres Physiques',
        'icon': 'flask',
        'color': 'success',
        'parameters': {
            'ph': {
                'name': 'pH',
                'unit': '',
                'step': 0.1,
                'min': 0
            },
            'mes': {
                'name': 'MES',
                'unit': 'mg/L',
                'step': 0.1,
                'min': 0
            },
            'ce': {
                'name': 'CE',
                'unit': 'dS/m',
                'step': 0.1,
                'min': 0
            }
        }
    },
    'chemical': {
        'title': 'Paramètres Chimiques',
        'icon': 'vial',
        'color': 'warning',
        'parameters': {
            'dbo5': {
                'name': 'DBO5',
                'unit': 'mg/L',
                'step': 0.1,
                'min': 0
            },
            'dco': {
                'name': 'DCO',
                'unit': 'mg/L',
                'step': 0.1,
                'min': 0
            },
            'chlorure': {
                'name': 'Chlorure',
                'unit': 'meq/L',
                'step': 0.1,
                'min': 0
            }
        }
    },
    'toxic': {
        'title': 'Éléments Toxiques',
        'icon': 'skull-crossbones',
        'color': 'danger',
        'parameters': {
            'cadmium': {
                'name': 'Cadmium',
                'unit': 'mg/L',
                'step': 0.001,
                'min': 0
            },
            'mercury': {
                'name': 'Mercure',
                'unit': 'mg/L',
                'step': 0.001,
                'min': 0
            },
            'arsenic': {
                'name': 'Arsenic',
                'unit': 'mg/L',
                'step': 0.001,
                'min': 0
            },
            'lead': {
                'name': 'Plomb',
                'unit': 'mg/L',
                'step': 0.001,
                'min': 0
            }
        }
    }
}

# Rating classifications
RATING_CLASSIFICATIONS = {
    'high': {
        'title': 'Eau de haute qualité',
        'description': 'Convient à tous types de cultures',
        'icon': 'award',
        'color': 'success'
    },
    'medium': {
        'title': 'Eau de qualité moyenne',
        'description': 'Convient à certaines cultures avec restrictions',
        'icon': 'info-circle',
        'color': 'warning'
    },
    'low': {
        'title': 'Eau de qualité insuffisante',
        'description': 'Traitement supplémentaire recommandé',
        'icon': 'exclamation-circle',
        'color': 'danger'
    }
}

def assess_microbiological_quality(coliform_fecal: float, nematodes: float) -> str:
    """
    Assess microbiological quality rating based on coliform and nematode levels.
    
    Args:
        coliform_fecal: Fecal coliform count in CFU/100ml
        nematodes: Nematode count in œufs/L
        
    Returns:
        str: Quality rating ('A', 'B', or 'C')
    """
    if (coliform_fecal <= WATER_QUALITY_THRESHOLDS['microbiological']['coliform_fecal']['A'] and 
        nematodes <= WATER_QUALITY_THRESHOLDS['microbiological']['nematodes']['A']):
        return 'A'
    elif (coliform_fecal <= WATER_QUALITY_THRESHOLDS['microbiological']['coliform_fecal']['B'] and 
          nematodes <= WATER_QUALITY_THRESHOLDS['microbiological']['nematodes']['B']):
        return 'B'
    return 'C'

def check_physical_parameters(ph: float, mes: float, ce: float) -> list:
    """
    Check physical parameters against thresholds.
    
    Args:
        ph: pH value
        mes: MES in mg/L
        ce: CE in dS/m
        
    Returns:
        list: List of violation messages
    """
    violations = []
    
    if not (WATER_QUALITY_THRESHOLDS['physical']['ph']['min'] <= ph <= WATER_QUALITY_THRESHOLDS['physical']['ph']['max']):
        violations.append(f"pH hors plage ({ph})")
    if mes > WATER_QUALITY_THRESHOLDS['physical']['mes']['max']:
        violations.append(f"MES trop élevé ({mes} mg/L)")
    if ce > WATER_QUALITY_THRESHOLDS['physical']['ce']['max']:
        violations.append(f"CE trop élevée ({ce} dS/m)")
        
    return violations

def check_chemical_parameters(dbo5: float, dco: float, chlorure: float) -> list:
    """
    Check chemical parameters against thresholds.
    
    Args:
        dbo5: DBO5 in mg/L
        dco: DCO in mg/L
        chlorure: Chlorure in meq/L
        
    Returns:
        list: List of violation messages
    """
    violations = []
    
    if dbo5 > WATER_QUALITY_THRESHOLDS['chemical']['dbo5']['max']:
        violations.append(f"DBO5 trop élevé ({dbo5} mg/L)")
    if dco > WATER_QUALITY_THRESHOLDS['chemical']['dco']['max']:
        violations.append(f"DCO trop élevé ({dco} mg/L)")
    if chlorure > WATER_QUALITY_THRESHOLDS['chemical']['chlorure']['max']:
        violations.append(f"Chlorure trop élevé ({chlorure} meq/L)")
        
    return violations

def check_toxic_elements(cadmium: float, mercury: float, arsenic: float, lead: float) -> list:
    """
    Check toxic element levels against thresholds.
    
    Args:
        cadmium: Cadmium in mg/L
        mercury: Mercury in mg/L
        arsenic: Arsenic in mg/L
        lead: Lead in mg/L
        
    Returns:
        list: List of violation messages
    """
    violations = []
    elements = {
        'cadmium': cadmium,
        'mercury': mercury,
        'arsenic': arsenic,
        'lead': lead
    }
    
    for element, value in elements.items():
        if value > WATER_QUALITY_THRESHOLDS['toxic'][element]['max']:
            violations.append(f"{element.capitalize()} trop élevé ({value} mg/L)")
            
    return violations

def determine_allowed_crops(micro_rating: str, physico_rating: str) -> tuple:
    """
    Determine which crops can be safely irrigated and their restrictions.
    
    Args:
        micro_rating: Microbiological rating ('A', 'B', or 'C')
        physico_rating: Physico-chemical rating ('OK' or 'FAIL')
        
    Returns:
        tuple: (list of allowed crops, set of restrictions)
    """
    allowed_crops = []
    restrictions = set()

    for category in CROP_CATEGORIES.values():
        if (category['requirements']['micro'] >= micro_rating and 
            (category['requirements']['physico'] == 'OK' and physico_rating == 'OK')):
            allowed_crops.append(category['name'])
            restrictions.update(category['restrictions'])
            
    return allowed_crops, restrictions

def get_parameter_metadata():
    """
    Get metadata for all water quality parameters.
    
    Returns:
        dict: Parameter metadata including titles, icons, and units
    """
    return PARAMETER_METADATA

def get_rating_classification(micro_rating: str, physico_rating: str) -> dict:
    """
    Get the rating classification based on microbiological and physico-chemical ratings.
    
    Args:
        micro_rating: Microbiological rating ('A', 'B', or 'C')
        physico_rating: Physico-chemical rating ('OK' or 'FAIL')
        
    Returns:
        dict: Rating classification including title, description, icon, and color
    """
    if micro_rating == 'A' and physico_rating == 'OK':
        return RATING_CLASSIFICATIONS['high']
    elif micro_rating in ['A', 'B'] and physico_rating == 'OK':
        return RATING_CLASSIFICATIONS['medium']
    else:
        return RATING_CLASSIFICATIONS['low']

def get_parameter_with_unit(param_type: str, param_name: str, value: float) -> str:
    """
    Format a parameter value with its unit.
    
    Args:
        param_type: Parameter type ('microbiological', 'physical', 'chemical', 'toxic')
        param_name: Parameter name
        value: Parameter value
        
    Returns:
        str: Formatted string with value and unit
    """
    unit = PARAMETER_METADATA[param_type]['parameters'][param_name]['unit']
    return f"{value} {unit}".strip()

def assess_water_quality(data: dict) -> dict:
    """
    Assess water quality and determine suitable crops based on provided parameters.
    
    Args:
        data: Dictionary containing all water quality parameters
        
    Returns:
        dict: Assessment results including rating, allowed crops, restrictions, and violations
    """
    # Assess microbiological quality
    micro_rating = assess_microbiological_quality(data['coliform_fecal'], data['nematodes'])
    
    # Check all parameters for violations
    violations = []
    violations.extend(check_physical_parameters(data['ph'], data['mes'], data['ce']))
    violations.extend(check_chemical_parameters(data['dbo5'], data['dco'], data['chlorure']))
    violations.extend(check_toxic_elements(data['cadmium'], data['mercury'], data['arsenic'], data['lead']))
    
    physico_rating = 'OK' if not violations else 'FAIL'
    
    # Determine allowed crops and restrictions
    allowed_crops, restrictions = determine_allowed_crops(micro_rating, physico_rating)
    
    # Get rating classification
    rating_info = get_rating_classification(micro_rating, physico_rating)
    
    return {
        'general_rating': f"{rating_info['title']} - {rating_info['description']}",
        'rating_info': rating_info,
        'allowed_crops': allowed_crops,
        'restrictions': list(restrictions),
        'violations': violations,
        'parameters': data
    }

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def generate_water_quality_pdf(result_data, output_path=None):
    """
    Generate a professional PDF report for water quality assessment.
    
    :param result_data: Dictionary containing water quality assessment results
    :param output_path: Optional path to save the PDF. If None, generates a default path.
    :return: Path to the generated PDF file
    """
    # Determine output path
    if output_path is None:
        output_path = os.path.join(
            os.path.expanduser('~'), 
            'Downloads', 
            f'Rapport_Qualite_Eau_{result_data.get("timestamp", "")}.pdf'
        )
    
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
    parameter_metadata = result_data.get('parameter_metadata', {})
    parameters = result_data.get('parameters', {})
    
    for param_type, metadata in parameter_metadata.items():
        for param_id, param in metadata.get('parameters', {}).items():
            parameter_data.append([
                param.get('name', param_id),
                str(parameters.get(param_id, 'N/A')),
                param.get('unit', '')
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

    # Build PDF
    doc.build(story)
    
    return output_path
