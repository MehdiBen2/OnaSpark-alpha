from flask import flash, request
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
import re

class FormValidator:
    @staticmethod
    def validate_required_fields(fields: Dict[str, str], error_message: str = 'Tous les champs sont obligatoires') -> Optional[Dict[str, str]]:
        """
        Validate that all specified fields are non-empty.
        
        :param fields: Dictionary of field names and their values
        :param error_message: Custom error message to display
        :return: Dictionary of form data if validation fails, otherwise None
        """
        missing_fields = [field for field, value in fields.items() if not value]
        
        if missing_fields:
            flash(error_message, 'error')
            return fields
        
        return None

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format using a simple regex.
        
        :param email: Email address to validate
        :return: True if email is valid, False otherwise
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @staticmethod
    def validate_date(date_str: str, format: str = '%Y-%m-%d') -> Optional[datetime]:
        """
        Validate and parse a date string.
        
        :param date_str: Date string to validate
        :param format: Expected date format
        :return: Parsed datetime object if valid, None otherwise
        """
        try:
            return datetime.strptime(date_str, format)
        except ValueError:
            return None

    @staticmethod
    def validate_unique_constraint(
        query_func: Callable, 
        field_name: str, 
        field_value: str, 
        error_message: Optional[str] = None
    ) -> bool:
        """
        Check if a field value is unique in the database.
        
        :param query_func: Function to query the database
        :param field_name: Name of the field to check
        :param field_value: Value to check for uniqueness
        :param error_message: Custom error message
        :return: True if unique, False otherwise
        """
        existing = query_func()
        if existing:
            flash(error_message or f'Ce {field_name} est déjà utilisé', 'error')
            return False
        return True

    @staticmethod
    def validate_form(
        form_data: Dict[str, Any], 
        required_fields: List[str], 
        additional_validations: Optional[List[Callable[[Dict[str, Any]], Optional[str]]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Comprehensive form validation method.
        
        :param form_data: Dictionary of form data
        :param required_fields: List of field names that are required
        :param additional_validations: Optional list of validation functions
        :return: Form data if validation fails, None if validation passes
        """
        # Validate required fields
        required_validation = FormValidator.validate_required_fields(
            {field: form_data.get(field, '') for field in required_fields}
        )
        if required_validation:
            return form_data

        # Run additional validations
        if additional_validations:
            for validation_func in additional_validations:
                validation_error = validation_func(form_data)
                if validation_error:
                    flash(validation_error, 'error')
                    return form_data

        return None

def handle_form_exception(e: Exception, form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic exception handler for form submissions.
    
    :param e: Exception raised during form processing
    :param form_data: Original form data
    :return: Form data to re-render the form
    """
    error_message = str(e)
    
    # Common database constraint errors
    if 'UNIQUE constraint failed' in error_message:
        if 'email' in error_message:
            flash('Cette adresse email est déjà utilisée', 'error')
        elif 'professional_number' in error_message:
            flash('Ce numéro professionnel est déjà utilisé', 'error')
        else:
            flash('Un élément unique existe déjà', 'error')
    else:
        # Generic error handling
        flash(f'Erreur lors du traitement du formulaire: {error_message}', 'error')
    
    return form_data
