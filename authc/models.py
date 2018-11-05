from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import Image, io, base64, json
from django.http import HttpResponse
import math, random
import numpy as np
import subprocess
from django.core.exceptions import ObjectDoesNotExist
# Create your models here.


class Computer(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    fingerprint = models.CharField(max_length=200)
    os_family = models.CharField(max_length=200)
    browser_family = models.CharField(max_length=200)
    is_mobile = models.BooleanField()

class Canvas(models.Model):
    computer_id = models.ForeignKey(Computer, on_delete=models.CASCADE)
    canvas = models.TextField()
    #define to type of canvas we are working on
    version = models.PositiveSmallIntegerField()
    date_creation = models.DateTimeField(default=timezone.now)
    #feature_nbr_pixels_text = models.IntegerField() 
    AUTH_PIX_THREASHOLD = 10000
    
    @classmethod 
    def canvas_to_numpy_array(cls, canvas, height, width):
        """
            Canvas should be the base64 reprensentation of the image strating by image type
            height and width are the size of the image in pixels
        """
        # split function is actually performed to get to image data without the
        # encoding type detail
        img = Image.open(io.BytesIO(base64.b64decode(canvas.split(',')[1])))
        # turns the image into a list of pixels starting at the top left corner
        # line by line
        img_list = list(img.getdata())
        img_nparray = np.array(img_list)/255.0
        img_nparray = img_nparray.reshape(height, width, 4) # 4 channels (rgba)
        return img_nparray

    @classmethod
    def get_random_canvas(cls, rcanvas_nbr, email, version):
        """
            Get random canvas from all computer_id within the
            database, except the one from user email.
            @rcanvas_nbr: number random canvas to fetch in the
            database
            @email: user to avoid
            @version: version of the canvas requested
        """
        def get_n_rint_on_range(n, on_range):
            all_index = []
            while len(all_index) < n:
                index = random.randint(0, on_range-1)
                if index not in all_index:
                    all_index.append(index)
            return all_index
        rcanvas = []
        usrcount = User.objects.count()-1
        canvas_per_user = rcanvas_nbr/usrcount + 1
        q1 = User.objects.exclude(email=email)[:rcanvas_nbr] #takes at most 2k users
        for user in q1:
            canvas_range = get_n_rint_on_range(n, on_range)
            rcanvas.extend(Canvas.objects.filter(computer__user=user, version=version)[canvas_range])
        return rcanvas[:rcanvas_nbr]
    
    @classmethod
    def train_and_save_model(rcanvas_nbr, email, version):
        canvas = Canvas.objects.filter(computer__user__email=email, version=version)
        r_canvas = Canvas.get_random_canvas(2000, email, version)
        learning_set = np.concatenate((canvas, r_canvas), axis=0)
        label_yes = [[1]]*len(canvas)
        label_no = [[0]]*len(r_canvas)
        labels = np.concatenate((label_yes, label_no), axis=0)
        #call module train.

        #TODO

        #save model


    @classmethod
    def verify_with_simple_mean(cls, canvasURLs, email):

        measures = []
        for canva in canvasURLs:
            im = Image.open(io.BytesIO(base64.b64decode(canva.split(',')[1])))
            count = 0
            for i in range(0, im.size[0]):
                for j in range(0, im.size[1]):
                    if im.getpixel((i,j)) != (0, 0, 0, 0):
                        count+=1
            measures.append(count)
        ## compare with training set and decide  -- that's the tough work => should be done
        # in a model class
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps({'errorMessage':
                "Authentication failed, {0} not in the database".format(email),
                'errorType':2}));
        try:
            computers = Computer.objects.filter(user_id=user)
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps({'errorMessage':
                "Computer not recognized - Authentication failed",
                'errorType':4}));
        for computer in computers:
            canvas = Canvas.objects.filter(computer_id=computer)
            sumC = 0
            sumSq = 0
            for canva in canvas:
                if canva.feature_nbr_pixels_text == -1:
                    return HttpResponse(json.dumps({'errorMessage':
                        "Something wrong happened - Learning phase on server side has not been executed",
                        'errorType':2}));

                sumC += canva.feature_nbr_pixels_text
                sumSq += (canva.feature_nbr_pixels_text*canva.feature_nbr_pixels_text)
            avrg = sumC/len(canvas)
            end_result = 0
            for measure in measures:
                end_result +=  (measure - avrg)  # shooud goes to infinity for non-related user and oscilatte around 0
                                                 # for the related used
            variance = (sumSq-(sumC*sumC)/len(canvas))/(len(canvas)-1)
            if abs(end_result) < 2*math.sqrt(variance):
                return HttpResponse(json.dumps({'infoMessage':
                    "Successfully authenticated", 'result':end_result, 'avrg':avrg, 'variance':variance}))
    
        return HttpResponse(json.dumps({'errorMessage':
            "Authenticationf failed - you do no seem to be {0} --- {1} {2} and variance:{3}".format(email, end_result, avrg, variance)}))

