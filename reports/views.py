from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse # Import messages framework
from django.http import HttpResponse, Http404
from django.utils import timezone
import json # For converting Python dicts/lists to JSON strings for JavaScript
from django.conf import settings
import os
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd # For easier data handling with Excel
from datetime import datetime

# Import models from other apps
from users.models import User
from exams.models import CalendarExam, ExamRequest, ReviewRequest
from exam_management.models import Notification # Assuming Notification is in exam_management

REPORT_DIR = os.path.join(settings.MEDIA_ROOT, 'reports_data')
REPORT_FILE_NAME = 'generated_report.xlsx'
REPORT_FILE_PATH = os.path.join(REPORT_DIR, REPORT_FILE_NAME)

def report_dashboard(request):
    print("[report_dashboard] Entered view.")
    stats = request.session.get('report_stats', None)
    report_exists = os.path.exists(REPORT_FILE_PATH)
    print(f"[report_dashboard] Report exists: {report_exists}, Stats in session: {bool(stats)}")

    if not report_exists and 'report_stats' in request.session:
        print("[report_dashboard] Report file deleted, clearing stats from session.")
        del request.session['report_stats']
        request.session.modified = True
        stats = None
    
    # For displaying Django messages
    django_messages = messages.get_messages(request)

    context = {
        'stats': stats,
        'report_exists': report_exists,
        'report_file_url': os.path.join(settings.MEDIA_URL, 'reports_data', REPORT_FILE_NAME) if report_exists else None,
        'django_messages': django_messages
    }
    print(f"[report_dashboard] Context for template: {context}")
    return render(request, 'reports/report_dashboard.html', context)

from django.db.models import Count

def get_choice_display_name(choice_value, choices_tuple, choices_dict_attr_name=None, model_class=None):
    """Helper to get display name for a choice field, with fallback for dict attribute."""
    if model_class and choices_dict_attr_name:
        choices_dict = getattr(model_class, choices_dict_attr_name, None)
        if choices_dict and isinstance(choices_dict, dict):
            return choices_dict.get(choice_value, choice_value) # Return value itself if not found in dict
    # Fallback to iterating choices tuple if dict not found or not provided
    for value, display_name in choices_tuple:
        if value == choice_value:
            return display_name
    return choice_value # Return value itself if not found

def generate_report(request):
    print("--- [generate_report] STARTING REPORT GENERATION ---")
    os.makedirs(REPORT_DIR, exist_ok=True)

    # --- Fetch data from models (with print for counts) ---
    users = User.objects.all()
    print(f"[generate_report] Fetched {users.count()} users.")
    calendar_exams = CalendarExam.objects.all()
    print(f"[generate_report] Fetched {calendar_exams.count()} calendar exams.")
    exam_requests = ExamRequest.objects.all()
    print(f"[generate_report] Fetched {exam_requests.count()} exam requests.")
    review_requests = ReviewRequest.objects.all()
    print(f"[generate_report] Fetched {review_requests.count()} review requests.")
    notifications = Notification.objects.all()
    print(f"[generate_report] Fetched {notifications.count()} notifications.")

    if not (users.exists() or calendar_exams.exists() or exam_requests.exists() or review_requests.exists() or notifications.exists()):
        print("[generate_report] No data found in any model. Aborting report generation.")
        messages.warning(request, "No hay datos disponibles para generar el reporte.")
        return redirect(reverse('reports:report_dashboard'))

    # --- Calculate Statistics ---
    stats = {}
    stats['report_generation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # User Statistics & Chart Data
    stats['total_users'] = users.count()
    users_by_role_counts = {get_choice_display_name(role_val, User.ROLES, 'ROLES_DICT', User): users.filter(role=role_val).count() for role_val, _ in User.ROLES}
    stats['users_by_role'] = users_by_role_counts
    stats['chart_users_by_role_labels'] = json.dumps(list(users_by_role_counts.keys()))
    stats['chart_users_by_role_data'] = json.dumps(list(users_by_role_counts.values()))
    
    # Calendar Exam Statistics & Chart Data
    stats['total_calendar_exams'] = calendar_exams.count()
    calendar_exams_by_type_counts = {get_choice_display_name(type_val, CalendarExam.EXAM_TYPES, 'EXAM_TYPES_DICT', CalendarExam): calendar_exams.filter(exam_type=type_val).count() for type_val, _ in CalendarExam.EXAM_TYPES}
    stats['calendar_exams_by_type'] = calendar_exams_by_type_counts
    stats['chart_calendar_exams_by_type_labels'] = json.dumps(list(calendar_exams_by_type_counts.keys()))
    stats['chart_calendar_exams_by_type_data'] = json.dumps(list(calendar_exams_by_type_counts.values()))
        
    # Exam Request Statistics & Chart Data
    total_exam_requests_count = exam_requests.count()
    stats['total_exam_requests'] = total_exam_requests_count
    exam_requests_by_status_percentage = {}
    exam_requests_status_counts_for_chart = {}
    if total_exam_requests_count > 0:
        for status_value, status_display_tuple in ExamRequest.REQUEST_STATUS:
            count = exam_requests.filter(status=status_value).count()
            percentage = (count / total_exam_requests_count * 100)
            # Use display name from tuple for keys
            exam_requests_by_status_percentage[status_display_tuple] = {'count': count, 'percentage': percentage}
            exam_requests_status_counts_for_chart[status_display_tuple] = count
    stats['exam_requests_by_status_percentage'] = exam_requests_by_status_percentage
    stats['chart_exam_requests_by_status_labels'] = json.dumps(list(exam_requests_status_counts_for_chart.keys()))
    stats['chart_exam_requests_by_status_data'] = json.dumps(list(exam_requests_status_counts_for_chart.values()))
    
    approved_requests_with_grades = exam_requests.filter(status='Approved', grade__isnull=False)
    if approved_requests_with_grades.exists():
        valid_grades = [req.grade for req in approved_requests_with_grades if req.grade is not None]
        avg_grade_decimal = sum(valid_grades) / len(valid_grades) if valid_grades else None
        stats['average_grade'] = float(avg_grade_decimal) if avg_grade_decimal is not None else None
    else:
        stats['average_grade'] = None

    most_requested_subjects_query = exam_requests.values('calendar_exam__subject').annotate(count=Count('calendar_exam__subject')).order_by('-count')[:5]
    stats['most_requested_subjects'] = {item['calendar_exam__subject']: item['count'] for item in most_requested_subjects_query}
        
    # Review Request Statistics & Chart Data
    total_review_requests_count = review_requests.count()
    stats['total_review_requests'] = total_review_requests_count
    review_requests_by_status_percentage = {}
    review_requests_status_counts_for_chart = {}
    if total_review_requests_count > 0:
        for status_value, status_display_tuple in ReviewRequest.STATUS_CHOICES:
            count = review_requests.filter(status=status_value).count()
            percentage = (count / total_review_requests_count * 100)
            review_requests_by_status_percentage[status_display_tuple] = {'count': count, 'percentage': percentage}
            review_requests_status_counts_for_chart[status_display_tuple] = count
    stats['review_requests_by_status_percentage'] = review_requests_by_status_percentage
    stats['chart_review_requests_by_status_labels'] = json.dumps(list(review_requests_status_counts_for_chart.keys()))
    stats['chart_review_requests_by_status_data'] = json.dumps(list(review_requests_status_counts_for_chart.values()))
        
    stats['total_notifications'] = notifications.count()
    stats['unread_notifications'] = notifications.filter(is_read=False).count()

    print(f"[generate_report] Calculated Stats: {stats}")
    request.session['report_stats'] = stats
    request.session.modified = True

    print("[generate_report] --- STARTING EXCEL FILE GENERATION ---")
    try:
        os.makedirs(REPORT_DIR, exist_ok=True)
        with pd.ExcelWriter(REPORT_FILE_PATH, engine='openpyxl') as writer:
            print("[generate_report] ExcelWriter opened.")
            # Users Data
            if users.exists():
                users_df = pd.DataFrame(list(users.values('username', 'first_name', 'last_name', 'email', 'role', 'curso_programa', 'departamento_facultad')))
                print(f"[generate_report] Users DataFrame created. Length: {len(users_df)}. Head:\n{users_df.head()}")
                users_df.to_excel(writer, sheet_name='Usuarios', index=False)
                print("[generate_report] 'Usuarios' sheet written.")
            else: print("[generate_report] No user data to write.")

            # Calendar Exams Data
            if calendar_exams.exists():
                calendar_exams_df = pd.DataFrame(list(calendar_exams.values('date', 'turn', 'exam_type', 'subject')))
                print(f"[generate_report] CalendarExams DataFrame created. Length: {len(calendar_exams_df)}. Head:\n{calendar_exams_df.head()}")
                calendar_exams_df.to_excel(writer, sheet_name='ExamenesCalendario', index=False)
                print("[generate_report] 'ExamenesCalendario' sheet written.")
            else: print("[generate_report] No calendar exam data to write.")

            # Exam Requests Data
            if exam_requests.exists():
                exam_requests_df = pd.DataFrame(list(exam_requests.values(
                    'student__username', 'calendar_exam__subject', 'calendar_exam__date', 
                    'calendar_exam__exam_type', 'grade', 'status', 'request_timestamp', 'comments'
                )))
                exam_requests_df.rename(columns={
                    'student__username': 'estudiante', 'calendar_exam__subject': 'asignatura_examen',
                    'calendar_exam__date': 'fecha_examen', 'calendar_exam__exam_type': 'tipo_examen',
                    'grade': 'calificacion', 'status': 'estado',
                    'request_timestamp': 'fecha_solicitud', 'comments': 'comentarios'
                }, inplace=True)
                print(f"[generate_report] ExamRequests DataFrame created. Length: {len(exam_requests_df)}. Head:\n{exam_requests_df.head()}")
                if 'fecha_solicitud' in exam_requests_df.columns:
                    exam_requests_df['fecha_solicitud'] = pd.to_datetime(exam_requests_df['fecha_solicitud']).dt.tz_localize(None)
                exam_requests_df.to_excel(writer, sheet_name='SolicitudesExamen', index=False)
                print("[generate_report] 'SolicitudesExamen' sheet written.")
            else: print("[generate_report] No exam request data to write.")

            # Review Requests Data
            if review_requests.exists():
                review_requests_df = pd.DataFrame(list(review_requests.values(
                    'exam_request__student__username', 'exam_request__calendar_exam__subject', 
                    'exam_request__grade', 'reason', 'status', 'created_at', 'updated_at'
                )))
                review_requests_df.rename(columns={
                    'exam_request__student__username': 'estudiante', 'exam_request__calendar_exam__subject': 'asignatura_examen',
                    'exam_request__grade': 'calificacion_original', 'reason': 'motivo', 'status': 'estado',
                    'created_at': 'fecha_creacion', 'updated_at': 'fecha_actualizacion'
                }, inplace=True)
                print(f"[generate_report] ReviewRequests DataFrame created. Length: {len(review_requests_df)}. Head:\n{review_requests_df.head()}")
                if 'fecha_creacion' in review_requests_df.columns:
                    review_requests_df['fecha_creacion'] = pd.to_datetime(review_requests_df['fecha_creacion']).dt.tz_localize(None)
                if 'fecha_actualizacion' in review_requests_df.columns:
                    review_requests_df['fecha_actualizacion'] = pd.to_datetime(review_requests_df['fecha_actualizacion']).dt.tz_localize(None)
                review_requests_df.to_excel(writer, sheet_name='SolicitudesRevision', index=False)
                print("[generate_report] 'SolicitudesRevision' sheet written.")
            else: print("[generate_report] No review request data to write.")

            # Notifications Data
            notifications = Notification.objects.all()
            if notifications.exists():
                notification_fields = ['user__username', 'message', 'timestamp', 'is_read']
                notifications_df = pd.DataFrame(list(notifications.values(*notification_fields)))
                notifications_df.rename(columns={
                    'user__username': 'usuario', 'message': 'mensaje', 'timestamp': 'fecha',
                    'is_read': 'leido'
                }, inplace=True)
                print(f"[generate_report] Notifications DataFrame created. Length: {len(notifications_df)}. Head:\n{notifications_df.head()}")
                if 'fecha' in notifications_df.columns:
                    notifications_df['fecha'] = pd.to_datetime(notifications_df['fecha']).dt.tz_localize(None)
                notifications_df.to_excel(writer, sheet_name='Notificaciones', index=False)
                print("[generate_report] 'Notificaciones' sheet written.")
            else: print("[generate_report] No notification data to write.")
            
            # Statistics Summary Sheet
            stats_summary_list = []
            stats_summary_list.append(['Fecha de Generación del Reporte', stats.get('report_generation_date')])
            stats_summary_list.append(['Total de Usuarios', stats.get('total_users')])
            for role_disp, count in stats.get('users_by_role', {}).items(): # Using display name as key now
                stats_summary_list.append([f'Usuarios - {role_disp}', count])
            
            stats_summary_list.append(['Total de Exámenes en Calendario', stats.get('total_calendar_exams')])
            for type_disp, count in stats.get('calendar_exams_by_type', {}).items(): # Using display name as key
                stats_summary_list.append([f'Exámenes por Tipo - {type_disp}', count])

            stats_summary_list.append(['Total de Solicitudes de Examen', stats.get('total_exam_requests')])
            for status_display, data in stats.get('exam_requests_by_status_percentage', {}).items():
                stats_summary_list.append([f'Solicitudes de Examen ({status_display})', f"{data['count']} ({data['percentage']:.2f}%)"])
            
            avg_grade_val = stats.get('average_grade')
            avg_grade_str = f"{avg_grade_val:.2f}" if isinstance(avg_grade_val, float) else 'N/A'
            stats_summary_list.append(['Calificación Promedio (Aprobadas)', avg_grade_str])
            
            stats_summary_list.append(['Asignaturas Más Solicitadas', ''])
            for subject, count in stats.get('most_requested_subjects', {}).items():
                stats_summary_list.append([f'  - {subject}', count])

            stats_summary_list.append(['Total de Solicitudes de Revisión', stats.get('total_review_requests')])
            for status_display, data in stats.get('review_requests_by_status_percentage', {}).items():
                stats_summary_list.append([f'Solicitudes de Revisión ({status_display})', f"{data['count']} ({data['percentage']:.2f}%)"])

            stats_summary_list.append(['Total de Notificaciones', stats.get('total_notifications')])
            stats_summary_list.append(['Notificaciones No Leídas', stats.get('unread_notifications')])
            
            stats_df = pd.DataFrame(stats_summary_list, columns=['Estadística', 'Valor'])
            print(f"[generate_report] Statistics Summary DataFrame created. Length: {len(stats_df)}. Head:\n{stats_df.head()}")
            stats_df.to_excel(writer, sheet_name='ResumenEstadisticas', index=False)
            print("[generate_report] 'ResumenEstadisticas' sheet written.")
        print("[generate_report] Excel file successfully written and closed.")

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print("--- ERROR DURING EXCEL GENERATION ---")
        print(error_traceback)
        print("--- END ERROR TRACEBACK ---")
        
        if 'report_stats' in request.session:
            del request.session['report_stats']
            request.session.modified = True

        messages.error(request, f"Error al generar el reporte Excel. Detalles en consola. Error: {e}")
    
    print("--- [generate_report] ENDING REPORT GENERATION ---")
    return redirect(reverse('reports:report_dashboard'))

def delete_last_report(request):
    if os.path.exists(REPORT_FILE_PATH):
        try:
            os.remove(REPORT_FILE_PATH)
        except OSError as e:
            # Handle error during file deletion (e.g., log it)
            # messages.error(request, f"Error deleting report file: {e}")
            pass # Or raise
            
    if 'report_stats' in request.session:
        del request.session['report_stats']
        
    return redirect(reverse('reports:report_dashboard'))
