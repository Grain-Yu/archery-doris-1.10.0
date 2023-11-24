# -*- coding: UTF-8 -*-
import logging
import traceback
import MySQLdb
import pymysql
import re

import schemaobject
import sqlparse
from MySQLdb.constants import FIELD_TYPE
from schemaobject.connection import build_database_url

from sql.engines.goinception import GoInceptionEngine
from sql.utils.sql_utils import get_syntax_type, remove_comments
from . import EngineBase
from .models import ResultSet, ReviewResult, ReviewSet
from sql.utils.data_masking import data_masking
from common.config import SysConfig

# -*- coding: UTF-8 -*-
import MySQLdb
import simplejson as json
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.http import HttpResponse, JsonResponse
from sql.utils.instance_management import (
    SUPPORTED_MANAGEMENT_DB_TYPE,
    get_instanceaccount_unique_value,
    get_instanceaccount_unique_key,
)
from common.utils.extend_json_encoder import ExtendJSONEncoder
from sql.engines import get_engine, ResultSet
from sql.utils.resource_group import user_instances
from .models import Instance, InstanceAccount

@permission_required("sql.menu_instance_account", raise_exception=True)
def sqllist(request):
    """获取优化详情列表"""
    checksum = request.POST.get("review_checksum")

    if not checksum:
        return JsonResponse({"status": 0, "msg": "", "data": []})
    try:
        instance = user_instances(
            request.user, db_type=SUPPORTED_MANAGEMENT_DB_TYPE
        ).get(instance_name='archery')
    except Instance.DoesNotExist:
        return JsonResponse({"status": 1, "msg": "你所在组未关联该实例", "data": []})
    



    

    # 获取已录入用户
    cnf_users = dict()
    for user in InstanceAccount.objects.filter(instance=instance).values(
        "id", "user", "host", "db_name", "remark"
    ):
        user["saved"] = True
        cnf_users[get_instanceaccount_unique_value(instance.db_type, user)] = user
    # 获取所有用户
    query_engine = get_engine(instance=instance)
    query_result = query_engine.get_instance_users_summary()
    if not query_result.error:
        rows = []
        key = get_instanceaccount_unique_key(db_type=instance.db_type)
        for row in query_result.rows:
            # 合并数据
            if row[key] in cnf_users.keys():
                row = dict(row, **cnf_users[row[key]])
            rows.append(row)
        # 过滤参数
        if saved:
            rows = [row for row in rows if row["saved"]]

        result = {"status": 0, "msg": "ok", "rows": rows}
    else:
        result = {"status": 1, "msg": query_result.error}

    # 关闭连接
    query_engine.close()
    return HttpResponse(
        json.dumps(result, cls=ExtendJSONEncoder, bigint_as_string=True),
        content_type="application/json",
    )

def create_instance_user(self, **kwargs):
        """实例账号管理功能，创建实例账号"""
        # escape
        user = self.escape_string(kwargs.get("user", ""))
        host = self.escape_string(kwargs.get("host", ""))
        password1 = self.escape_string(kwargs.get("password1", ""))
        remark = kwargs.get("remark", "")
        # 在一个事务内执行
        hosts = host.split("|")
        create_user_cmd = ""
        accounts = []
        for host in hosts:
            create_user_cmd += (
                f"create user '{user}'@'{host}' identified by '{password1}';"
            )
            accounts.append(
                {
                    "instance": self.instance,
                    "user": user,
                    "host": host,
                    "password": password1,
                    "remark": remark,
                }
            )
        exec_result = self.execute(db_name="mysql", sql=create_user_cmd)
        exec_result.rows = accounts
        return exec_result