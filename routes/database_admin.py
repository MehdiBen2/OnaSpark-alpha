from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
from utils.decorators import admin_required
from models import db
from sqlalchemy import inspect, text, MetaData
import sqlalchemy as sa
import os
import shutil
from datetime import datetime

database_admin = Blueprint('database_admin', __name__)

@database_admin.route('/admin/database')
@login_required
@admin_required
def database_overview():
    """Show all tables in the database"""
    inspector = inspect(db.engine)
    tables = []
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column.get('default', ''))
            })
        tables.append({
            'name': table_name,
            'columns': columns
        })
    return render_template('admin/database/overview.html', tables=tables)

def get_foreign_keys(table_name):
    """Get foreign key information for a table"""
    inspector = inspect(db.engine)
    foreign_keys = {}
    for fk in inspector.get_foreign_keys(table_name):
        constrained_column = fk['constrained_columns'][0]
        referred_table = fk['referred_table']
        foreign_keys[constrained_column] = referred_table
    return foreign_keys

def get_display_column(table_name):
    """Get the appropriate display column for a table"""
    display_columns = {
        'users': 'username',
        'zones': 'name',
        'units': 'name',
        'centers': 'name',
        'incidents': 'title'
    }
    return display_columns.get(table_name, 'id')

def get_related_data(table_name):
    """Get data for related tables"""
    inspector = inspect(db.engine)
    foreign_keys = get_foreign_keys(table_name)
    related_data = {}
    
    for column, referred_table in foreign_keys.items():
        # Get the display column for the referred table
        display_column = get_display_column(referred_table)
        
        # Get the data from the referred table
        query = text(f'SELECT id, {display_column} as display_name FROM {referred_table}')
        result = db.session.execute(query)
        related_data[referred_table] = [dict(row._mapping) for row in result]
    
    return related_data

@database_admin.route('/admin/database/table/<table_name>')
@login_required
@admin_required
def view_table(table_name):
    """View and edit table data"""
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        flash('Table not found', 'error')
        return redirect(url_for('database_admin.database_overview'))
    
    # Get table columns and their foreign keys
    columns = inspector.get_columns(table_name)
    foreign_keys = get_foreign_keys(table_name)
    
    # Add foreign key information to columns
    for column in columns:
        column['foreign_key'] = column['name'] in foreign_keys
        if column['foreign_key']:
            column['foreign_table'] = foreign_keys[column['name']]
    
    # Get table data
    query = text(f'SELECT * FROM {table_name}')
    result = db.session.execute(query)
    rows = [dict(row._mapping) for row in result]
    
    # Get related data for foreign keys
    related_data = get_related_data(table_name)
    
    return render_template('admin/database/table.html', 
                         table_name=table_name, 
                         columns=columns, 
                         rows=rows,
                         related_data=related_data)

@database_admin.route('/admin/database/related-data/<table_name>')
@login_required
@admin_required
def get_related_table_data(table_name):
    """Get data for a related table"""
    display_column = get_display_column(table_name)
    query = text(f'SELECT id, {display_column} as display_name FROM {table_name}')
    result = db.session.execute(query)
    data = [dict(row._mapping) for row in result]
    return jsonify(data)

@database_admin.route('/admin/database/table/<table_name>/row/<int:row_id>')
@login_required
@admin_required
def get_row(table_name, row_id):
    """Get a single row's data"""
    query = text(f'SELECT * FROM {table_name} WHERE id = :id')
    result = db.session.execute(query, {'id': row_id})
    row = dict(result.fetchone()._mapping)
    return jsonify(row)

@database_admin.route('/admin/database/table/<table_name>/add-column', methods=['POST'])
@login_required
@admin_required
def add_column(table_name):
    """Add a new column to the table"""
    column_name = request.form.get('column_name')
    column_type = request.form.get('column_type')
    nullable = request.form.get('nullable') == 'true'
    
    try:
        with db.engine.begin() as conn:
            column_type_obj = getattr(sa, column_type)()
            conn.execute(
                text(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_obj}')
            )
        flash('Column added successfully', 'success')
    except Exception as e:
        flash(f'Error adding column: {str(e)}', 'error')
    
    return redirect(url_for('database_admin.view_table', table_name=table_name))

@database_admin.route('/admin/database/table/<table_name>/add-row', methods=['POST'])
@login_required
@admin_required
def add_row(table_name):
    """Add a new row to the table"""
    data = {k: v for k, v in request.form.items() if k != 'table_name' and v}
    
    try:
        # Build the INSERT query
        columns = ', '.join(data.keys())
        values = ', '.join([f":{k}" for k in data.keys()])
        query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        
        # Execute the query
        db.session.execute(query, data)
        db.session.commit()
        flash('Row added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding row: {str(e)}', 'error')
    
    return redirect(url_for('database_admin.view_table', table_name=table_name))

@database_admin.route('/admin/database/table/<table_name>/edit-row', methods=['POST'])
@login_required
@admin_required
def edit_row(table_name):
    """Edit a row in the table"""
    row_id = request.form.get('id')
    data = {k: v for k, v in request.form.items() if k not in ['table_name', 'id'] and v}
    
    try:
        # Build the UPDATE query
        set_clause = ', '.join([f"{k} = :{k}" for k in data.keys()])
        query = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id")
        
        # Execute the query
        db.session.execute(query, {'id': row_id, **data})
        db.session.commit()
        flash('Row updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating row: {str(e)}', 'error')
    
    return redirect(url_for('database_admin.view_table', table_name=table_name))

@database_admin.route('/admin/database/table/<table_name>/delete-row/<int:row_id>', methods=['POST'])
@login_required
@admin_required
def delete_row(table_name, row_id):
    """Delete a row from the table"""
    try:
        query = text(f"DELETE FROM {table_name} WHERE id = :id")
        db.session.execute(query, {'id': row_id})
        db.session.commit()
        flash('Row deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting row: {str(e)}', 'error')
    
    return redirect(url_for('database_admin.view_table', table_name=table_name))

@database_admin.route('/admin/database/download')
@login_required
@admin_required
def download_database():
    """Download the SQLite database file"""
    try:
        db_path = db.engine.url.database
        if not db_path or not os.path.exists(db_path):
            flash("Base de données introuvable.", "error")
            return redirect(url_for('database_admin.database_overview'))

        # Create a copy of the database file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'OnaDB_backup_{timestamp}.db'
        temp_path = os.path.join(os.path.dirname(db_path), backup_filename)
        
        # Copy the database file
        shutil.copy2(db_path, temp_path)
        
        try:
            return send_file(
                temp_path,
                mimetype='application/x-sqlite3',
                as_attachment=True,
                download_name=backup_filename
            )
        finally:
            # Clean up the temporary file after sending
            try:
                os.unlink(temp_path)
            except:
                pass  # Ignore cleanup errors
                
    except Exception as e:
        flash(f"Erreur lors du téléchargement de la base de données: {str(e)}", "error")
        return redirect(url_for('database_admin.database_overview'))
