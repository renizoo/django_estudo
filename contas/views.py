# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
import datetime
from .models import Transacao
from django.http import HttpResponse


# Create your views here.

def home(request):
    data = {}

    data['transacoes'] = ['t1', 't2', 't3']

    data['now'] = datetime.datetime.now()
    # html = "<html><body>It is now %s.</body></html>" % now

    return render(request, 'contas/home.html', data)


def listagem(request):
    data = {}
    data['transacoes'] = Transacao.objects.all()
    return render(request, 'contas/listagem.html', data)
