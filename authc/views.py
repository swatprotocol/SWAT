from django.shortcuts import render
from django.template import loader
import json, random
import os

from django.http import HttpResponse, HttpResponseRedirect
from .forms import LoginForm, CheckFpForm, UpdateCanvasForm, RegisterForm
from django.contrib.auth.models import User
from .models import Computer, Canvas
from django.core.exceptions import ObjectDoesNotExist
from django_user_agents.utils import get_user_agent
from keras.models import load_model
import subprocess
import numpy as np

CANVASVERSION = 1
def index(request, errorMessage=None, infoMessage=None):
    #Return simple login fora
    form = RegisterForm()
    action = '/participate/'
    return render(request, 'authc/index.html', {'form':form,
        'action':action, 'valueSubmit':"Participate",
        'errorMessage':errorMessage, 'infoMessage':infoMessage})


def participate(request):
    form = RegisterForm(request.POST)
    if form.is_valid():
        return render(request, 'authc/canvas.html', {'errorMessage':None, 'infoMessage':None,
            'email':request.POST['email']})
    return render(request, 'authc/index.html', {'form':form,
        'action':'/participate/', 'valueSubmit':'Participate',
        'errorMessage': "It seems that a least one form was not valid"})


def check_fp(request):
    form = CheckFpForm(request.POST)
    user_agent = get_user_agent(request)
    if form.is_valid():
        email = form.cleaned_data['email']
        fingerprint = form.cleaned_data['fingerprint']
        try:
            user = User.objects.get(email=email)
            try:
                computer = Computer.objects.get(user_id=user,
                        fingerprint=fingerprint)
                return HttpResponse(json.dumps({'errorType':1,
                    'errorMessage': "We already know you, please try again with another computer or another browser"}));
            except ObjectDoesNotExist:
                newComputer = Computer.objects.create(
                        user_id=user,
                        fingerprint=fingerprint,
                        os_family = user_agent.os.family,
                        browser_family = user_agent.browser.family,
                        is_mobile = user_agent.is_mobile)
                newComputer.save()
                return HttpResponse(json.dumps({'infoMessage':
                    "We are collecting the data. Thank you for adding one computer !"}));
        except ObjectDoesNotExist:
            #We never heard about this user
            try:
                computer = Computer.objects.get(fingerprint=fingerprint);
                return HttpResponse(json.dumps({'errorType':3,
                    'errorMessage': "We already know you with another email account on the same computer"}));
            except ObjectDoesNotExist:
                newUser = User.objects.create(email=email,
                    username=email)
                newComputer = Computer.objects.create(
                    user_id = newUser,
                    fingerprint=fingerprint,
                    os_family = user_agent.os.family,
                    browser_family = user_agent.browser.family,
                    is_mobile = user_agent.is_mobile)
                newComputer.save()
                newUser.save()
                return HttpResponse(json.dumps({'infoMessage':
                "We are collecting the data. Thank you !"}))
    else:
        return HttpResponse(json.dumps({'errorMessage':
            "", 'errorType':2}));

def canvas(request):
    return render(request, 'authc/canvas.html', {'logged':logged})

def update_canvas(request):
    form = UpdateCanvasForm(request.POST);
    if form.is_valid():
        email = form.cleaned_data['email']
        fingerprint = form.cleaned_data['fingerprint']
        canvasURLs = form.cleaned_data['canvasURL'].split(";-;")
        version = form.cleaned_data['version']
        try:
            user = User.objects.get(email=email)
            computer = Computer.objects.get(user_id=user,
                    fingerprint=fingerprint)
            for canvasURL in canvasURLs:
                if canvasURL.startswith("data") :
                    newCanvas = Canvas.objects.create(
                            computer_id=computer,
                            canvas=canvasURL,
                            version=version)
                    newCanvas.save()

            #Counts canvas in the database and triggers
            #learning phase if we have reached 2000 canvas

            count = Canvas.objects.filter(computer_id=computer,\
                    version=version).count()
            if (count >= 2000):
                pass  #deactivate
                #Launch learning phase using a subprocess
                #THIS IS NOT SAFE! But this is a demo, so 
                #who care?
                #p = subprocess.Popen("python convnet.py --email {0} --db /home/www-data/canvasauth/db.sqlite3 --store"
                #        .format(email))

                #return HttpResponse(json.dumps({'count': count}))
            return HttpResponse(json.dumps({})) #everything ok
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps({'erroMessage':
                "Something wrong happened - Data collection stopped",
                'errorType':2}));
    else:
        return HttpResponse(json.dumps({'errorMessage':
            "Something wrong happened - Data collection stopped",
            'errorType':2}))
    

def authenticate(request):
    #generate some random texts
    def random_string(length):
        txt = ''
        alpha = 'abcdefghijklmnopqrstuvwxyz1234567890'
        for i in range(0, length):
            txt += random.choice(alpha)
        return txt
    texts = []
    for i in range(0, 32):
        texts.append(random_string(25))
    return render(request, 'authc/authenticate.html', {'form':LoginForm(),
        'infoMessage':"Please authenticate",
        'errorMessage': '',
        'action':'/check_authentication/',
        'valueSubmit':'Let me in',
        'canvas_text':json.dumps({'canvas_text':texts}),
        'canvas_version': CANVASVERSION})

def check_authentication(request):
    form = UpdateCanvasForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        fingerprint = form.cleaned_data['fingerprint']
        canvasURLs = form.cleaned_data['canvasURL'].split(";-;")[:-1] #last is ""
        version = form.cleaned_data['version']
        #TODO: Check if it is likely the canvas we wanted
        #How ? Ask to draw a random pixel-patern with known
        #position and color.  and verify it

        filepath = "/home/www-data/canvasauth/authc/models/{0}.h5".format(email.replace("@", "").replace(".",""))
        if os.path.isfile(filepath):
            model = load_model(filepath)
            c_to_evaluate = []
            for canvas in canvasURLs:
                c_to_evaluate.append(Canvas.canvas_to_numpy_array(canvas, 35, 280))
            predictions = model.predict(np.array(c_to_evaluate))
            if float(sum(predictions))/len(predictions) > 0.6:
                return HttpResponse(json.dumps({'infoMessage':
                    "Successfully authenticate with prob {0}".format(float(sum(predictions))/len(predictions))}))
            else:
                return HttpResponse(json.dumps({'infoMessage':
                    "Not successfully authenticatied:  {0}".format(float(sum(predictions))/len(predictions))}))
                
        else:
            return HttpResponse(json.dumps({'errorMessage':
                "Either you're not in the database or the learning phase is not finished yet"}))
    
        return Canvas.verify_with_simple_mean(canvasURLs, email)
    else:
        return HttpResponse(json.dumps({'errorMessage':
                "Something wrong happened - Authentication failed, form not valid",
                'errorType':2}));


