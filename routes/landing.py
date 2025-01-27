from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import current_user
from utils.url_endpoints import MAIN_DASHBOARD

# Create blueprint with url_prefix=None to handle root URL
landing = Blueprint('landing', __name__, url_prefix='')

@landing.route('/')
def index():
    """
    Handle the landing page routing based on user authentication and visit history.
    - If user is authenticated: redirect to dashboard
    - If user has visited before: show main landing page
    - If first visit: show hero landing page
    """
    # Check if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_DASHBOARD))
    
    # Check if user has visited before using session
    if session.get('has_visited'):
        return render_template('dashboard/landing.html')
    
    # First time visitor
    session['has_visited'] = True
    session.permanent = True  # Make the session last longer
    return render_template('landing/hero.html')

@landing.route('/landing')
def main_landing():
    """Direct route to the main landing page"""
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_DASHBOARD))
    return render_template('dashboard/landing.html')

@landing.route('/welcome')
def hero():
    """Direct route to the hero landing page"""
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_DASHBOARD))
    return render_template('landing/hero.html')

@landing.route('/introspark')
def introspark():
    """Direct route to the introspark introduction page"""
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_DASHBOARD))
    return render_template('landing/introspark.html')
