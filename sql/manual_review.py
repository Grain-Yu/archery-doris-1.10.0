# -*- coding: UTF-8 -*-
import logging
import traceback
import MySQLdb
import pymysql
import re



# -*- coding: UTF-8 -*-

import simplejson as json
from django.contrib.auth.decorators import permission_required


from django.http import HttpResponse, JsonResponse
from sql.utils.instance_management import (
    SUPPORTED_MANAGEMENT_DB_TYPE,
)
from common.utils.extend_json_encoder import ExtendJSONEncoder
from sql.engines import get_engine, ResultSet
from sql.utils.resource_group import user_instances
from .models import Instance, InstanceAccount

from sql.engines.mysql import MysqlEngine



@permission_required("sql.menu_instance_account", raise_exception=True)
def listreview(request):
    """获取优化详情列表"""
    checksum = request.POST.get("review_checksum")

    if not checksum:
        return JsonResponse({"status": 0, "msg": "", "data": []})
    try:
        instance = user_instances(
            request.user, db_type=SUPPORTED_MANAGEMENT_DB_TYPE
        ).get(id=1)
    except Instance.DoesNotExist:
        return JsonResponse({"status": 1, "msg": "你所在组未关联该实例", "data": []})

    #获取checksum对应的优化详情
    query_engine = MysqlEngine(instance=instance)
    query_result = query_engine.get_review_status_summary(checksum)
    if not query_result.error:
        rows = query_result.rows
        result = {"status": 0, "msg": "ok", "rows": rows}
    else:
        result = {"status": 1, "msg": query_result.error}
    return HttpResponse(
        json.dumps(result, cls=ExtendJSONEncoder, bigint_as_string=True),
        content_type="application/json",
    )

@permission_required("sql.instance_account_manage", raise_exception=True)
def editreview(request):
    """编辑优化详情"""
    checksum = request.POST.get("checksum")
    reviewed_by = request.POST.get("reviewed_by", "")
    reviewed_on = request.POST.get("reviewed_on", "")
    comments = request.POST.get("comments", "")
    reviewed_status = request.POST.get("reviewed_status", "")

    if (
         not all([checksum, reviewed_by, reviewed_on, comments,reviewed_status])
    ):
        return JsonResponse({"status": 1, "msg": "参数不完整，请确认后提交", "data": []})

    try:
        instance = user_instances(
            request.user, db_type=SUPPORTED_MANAGEMENT_DB_TYPE
        ).get(id=1)
    except Instance.DoesNotExist:
        return JsonResponse({"status": 1, "msg": "你所在组未关联该实例", "data": []})
    
    exec_engine = MysqlEngine(instance=instance)    
    exec_result = exec_engine.set_review_details(
        checksum=checksum, reviewed_by=reviewed_by, reviewed_on=reviewed_on,comments=comments,reviewed_status=reviewed_status
    )
    return JsonResponse({"status": 0, "msg": "", "data": []})
