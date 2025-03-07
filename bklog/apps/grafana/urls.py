# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
License for BK-LOG 蓝鲸日志平台:
--------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
We undertake not to change the open source license (MIT license) applicable to the current version of
the project delivered to anyone in the future.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from apps.grafana import views
from apps.grafana.views import CustomESDatasourceViewSet, GrafanaProxyView
from bk_dataview.grafana.views import StaticView, SwitchOrgView

router = routers.DefaultRouter(trailing_slash=True)
router.register(r"grafana", views.GrafanaViewSet, basename="grafana_api")

proxy_router = routers.DefaultRouter(trailing_slash=False)

proxy_router.register(r"trace", views.GrafanaTraceViewSet, basename="trace_api")

urlpatterns = [
    re_path(r"^api/v1/", include(router.urls)),
    # iframe访问地址 org_name 可以是项目id/业务id 需要保证唯一
    re_path(r"^bk-dataview/orgs/(?P<org_name>[a-zA-Z0-9\-_]+)/grafana/", SwitchOrgView.as_view()),
    # grafana访问地址, 需要和grafana前缀保持一致
    re_path(r"^grafana/$", SwitchOrgView.as_view()),
    # 自定义ES数据源 mapping
    re_path(
        r"^grafana/custom_es_datasource/(?P<index_set_id>.+)/_mapping$",
        CustomESDatasourceViewSet.as_view({"get": "mapping"}),
    ),
    # 自定义ES数据源 msearch
    re_path(
        r"^grafana/custom_es_datasource/_msearch$",
        CustomESDatasourceViewSet.as_view({"post": "msearch"}),
    ),
    re_path(r"^grafana/proxy/", include(proxy_router.urls)),
    re_path(r"^grafana/public/", StaticView.as_view()),
    re_path(r"^grafana/", GrafanaProxyView.as_view()),
]
