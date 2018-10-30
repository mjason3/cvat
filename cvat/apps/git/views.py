# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.decorators import permission_required
from django.db import transaction

from cvat.apps.authentication.decorators import login_required
from cvat.apps.engine.log import slogger
from cvat.apps.engine.models import Task, Job
from cvat.apps.git.models import GitData
from cvat.apps.git.git import Git


import json


@login_required
@permission_required('engine.add_task', raise_exception=True)
def create_repository(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        tid = data['tid']
        url = data['url']

        db_task = Task.objects.get(pk = tid)
        if GitData.objects.filter(pk = db_task).exists():
            raise Exception('git repository for task already exists')

        db_git = GitData()
        db_git.task = db_task
        db_git.url = url
        db_git.save()
    except Exception as e:
        slogger.glob.error("cannot create git repository for task #{}".format(tid), exc_info=True)
        return HttpResponseBadRequest(str(e))

    return HttpResponse()


@transaction.atomic
@login_required
@permission_required(perm=['engine.view_task', 'engine.change_task'], raise_exception=True)
def update_repository(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        tid = data['tid']
        url = data['url']

        db_task = Task.objects.get(pk = tid)

        db_git = GitData.objects.select_for_update().get(pk = db_task)
        db_git.url = url
        db_git.save()
    except Exception as e:
        try:
            slogger.task[tid].error("can not update git repository", exc_info=True)
        except:
            pass

        return HttpResponseBadRequest(str(e))

    return HttpResponse()


@login_required
@permission_required(perm=['engine.view_task'], raise_exception=True)
def get_repository(request, tid):
    try:
        response = {
            'url': {
                'value': None,
            },
            'status': {
                'value': None,
                'error': None
            }
        }

        db_task = Task.objects.get(pk = tid)
        if not GitData.objects.filter(pk = db_task).exists():
            return JsonResponse(response)

        response['url']['value'] = GitData.objects.get(pk = db_task).url
        response['status']['error'] = 'not implemented'

        return JsonResponse(response)
    except Exception as e:
        try:
            slogger.task[tid].error("can not get git repository info", exc_info=True)
        except:
            pass
        return HttpResponseBadRequest(str(e))


@transaction.atomic
@login_required
@permission_required(perm=['engine.view_task', 'engine.change_task'], raise_exception=True)
def delete_repository(request, tid):
    try:
        db_task = Task.objects.get(pk = tid)

        if GitData.objects.filter(pk = db_task).exists():
            db_git = GitData.objects.select_for_update().get(pk = db_task)
            db_git.delete()

    except Exception as e:
        try:
            slogger.task[tid].error("can not delete git repository data", exc_info=True)
        except:
            pass
        return HttpResponseBadRequest(str(e))

    return HttpResponse()
