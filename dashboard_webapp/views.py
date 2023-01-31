from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import LoginForm, SignUpForm
from . import models

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse

import mysql.connector
import datetime
from django.core import serializers
from django.contrib.auth.models import User
# Create your views here

"""
def chart_view(request, selected_sensor):
    return render('includes/chart.html', {"selected_sensor": selected_sensor})
"""

def db_r_query(query, param):
    Connection = mysql.connector.connect(host="localhost", user="root", password="!password")
    Cursor = Connection.cursor(buffered=True)
    Connection.connect() 
    Cursor.execute("USE dashboard_webapp")
    try:
        Cursor.execute(query, param)
        returned_rows = Cursor.fetchall()
        Connection.close()
        return returned_rows
    except (mysql.connector.DatabaseError, mysql.connector.OperationalError) as e:
        Connection.close()
        return []


def fetch_unit_info(request, hdb_block, unit_number):
    unit_info = []

    ReturnedRows = db_r_query(
        "SELECT DISTINCT * FROM dashboard_webapp_raspberry_location WHERE hdb_block=%s AND unit_number=%s ORDER BY raspberry_id ASC", 
        [hdb_block, '#' + unit_number]
    )  

    for info in ReturnedRows: 
        unit_info.append(info) 
    
    return JsonResponse(data={
        'unit_info': unit_info,             
    })
    

def fetch_units(request, hdb_block):
    units = []

    ReturnedRows = db_r_query("SELECT * FROM dashboard_webapp_raspberry_location WHERE hdb_block=%s", [hdb_block])  
    for household_unit in ReturnedRows: 
        units.append(household_unit) 
    
    return JsonResponse(data={
        'units': units,             
    })


def fetch_blocks(request):
    blocks = []

    ReturnedRows = db_r_query("SELECT DISTINCT(hdb_block) FROM dashboard_webapp_raspberry_location", [])  
    for household_block in ReturnedRows: 
        blocks.append(household_block) 
    
    return JsonResponse(data={
        'blocks': blocks,             
    })


def time_axis_formatter(capturedDate_str, startDate, endDate):
     # if same day, exclude date, show time in AM/PM on x-axis
    if startDate == endDate:    
        dt = datetime.datetime.strptime(capturedDate_str[11:16], '%H:%M').strftime('%I:%M %p')
        return dt

    # if same year, exclude year, show '13 Dec, 01:40 PM' on x-axis
    elif startDate[0:4] == endDate[0:4]:
        dt = datetime.datetime.strptime(capturedDate_str[0:16], '%Y-%m-%d %H:%M').strftime('%d %b, %I:%M %p')
        return dt

    # if different year, exclude time, show date on x-axis
    else:
        dt = datetime.datetime.strptime(capturedDate_str[0:16], '%Y-%m-%d %H:%M').strftime('%d %b %Y')
        return dt


def fetch_smoke_occurence(request, hdb_block, unit_no, startDate, startTime, endDate, endTime):
    data = []

    datetime_start = startDate + " " + startTime + ":00"
    datetime_end = endDate + " " + endTime + ":00"

    data = [
        [{'x': 10,'y': 59}, {'x': 16,'y': 28}, {'x': 16,'y': 5}], 
        [{'x': 21,'y': 51}, {'x': 63,'y': 12}, {'x': 71,'y': 30}],
        [{'x': 94,'y': 53}, {'x': 36,'y': 24}, {'x': 84,'y': 49}],
        [{'x': 92,'y': 13}, {'x': 64,'y': 25}, {'x': 16,'y': 10}],
        [{'x': 49,'y': 54}, {'x': 65,'y': 5}, {'x': 63,'y': 9}],
    ]

    return JsonResponse(data={      
        'data': data,                  
    })


def fetch_smoke_data(request, sensorId, startDate, startTime, endDate, endTime):
    labels = []
    data = []

    datetime_start = startDate + " " + startTime + ":00"
    datetime_end = endDate + " " + endTime + ":00"

    ReturnedRows = db_r_query(
        "SELECT captured_date, smoke_value FROM dashboard_webapp_smokereading WHERE raspberry_id=%s AND (captured_date BETWEEN %s AND %s) ORDER BY captured_date", 
        [sensorId, datetime_start, datetime_end]
    )                

    for smokeReading in ReturnedRows:   
        capturedDate_str = str(smokeReading[0])

        dt = time_axis_formatter(capturedDate_str, startDate, endDate)
            
        labels.append(str(dt))
        data.append(smokeReading[1])    
    
    return JsonResponse(data={
        'labels': labels,              
        'data': data,                  
    })


def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "authentication/login.html", {"form": form, "msg": msg})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        print(form)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "authentication/register.html", {"form": form, "msg": msg, "success": success})


def profile_view(request):
    context = {
        'segment': 'profile/',
    }
    html_template = loader.get_template('home/profile.html')
    return HttpResponse(html_template.render(context, request))


def table_view(request):
    context = {
        'segment': 'tables/',
    }
    html_template = loader.get_template('home/tables.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def index(request):
    context = {
        'segment': 'index',
    }
    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
            
        context['segment'] = load_template
        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))
