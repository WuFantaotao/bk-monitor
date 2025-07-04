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

from django.utils.translation import gettext_lazy as _  # noqa

from apps.api.base import (  # noqa  pylint: disable=unused-import
    DataAPI,
    DataApiRetryClass,
)
from apps.api.modules.utils import add_esb_info_before_request_for_bkdata_user, biz_to_tenant_getter  # noqa
from config.domains import AIOPS_APIGATEWAY_ROOT, AIOPS_MODEL_APIGATEWAY_ROOT  # noqa


class _BkDataAIOPSApi:
    MODULE = _("数据平台aiops模块")

    def __init__(self):
        self.update_execute_config = DataAPI(
            method="POST",
            url=AIOPS_APIGATEWAY_ROOT + "meta_data/update_execute_config/",
            module=self.MODULE,
            description="更新实验执行配置",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )
        self.aiops_release = DataAPI(
            method="GET",
            url=AIOPS_APIGATEWAY_ROOT + "models/{model_id}/release/",
            module=self.MODULE,
            url_keys=["model_id"],
            description="备选模型列表",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )

        self.aiops_release_model_release_id_model_file = DataAPI(
            method="GET",
            url=AIOPS_APIGATEWAY_ROOT + "models/{model_id}/release/{model_release_id}/model_file/",
            module=self.MODULE,
            url_keys=["model_id", "model_release_id"],
            description="获取发布的模型对应的模型文件",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )

        self.serving_data_processing_id_model_file = DataAPI(
            method="GET",
            url=AIOPS_APIGATEWAY_ROOT + "serving/{data_processing_id}/model_file/",
            module=self.MODULE,
            url_keys=["data_processing_id"],
            description="获取结果表对应的模型文件",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )
        self.serving_data_processing_id_config = DataAPI(
            method="GET",
            url=AIOPS_APIGATEWAY_ROOT + "serving/{data_processing_id}/config/",
            module=self.MODULE,
            url_keys=["data_processing_id"],
            description="AIOps 模型实例信息",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
            bk_tenant_id=biz_to_tenant_getter(lambda p: p["data_processing_id"].split("_", 1)[0]),
        )
        self.aiops_get_model_storage_cluster = DataAPI(
            method="GET",
            url=AIOPS_APIGATEWAY_ROOT + "models/storage_clusters/",
            module=self.MODULE,
            description="获取模型存储集群列表",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )
        self.aiops_get_model_release_info = DataAPI(
            method="GET",
            url=AIOPS_APIGATEWAY_ROOT + "releases/{model_release_id}/",
            module=self.MODULE,
            description="获取模型发布信息",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )
        self.create_online_task = DataAPI(
            method="POST",
            url=AIOPS_APIGATEWAY_ROOT + "auto/serving/ci/",
            module=self.MODULE,
            description="创建应用CI-在线训练任务",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )

        self.update_online_task = DataAPI(
            method="PUT",
            url=AIOPS_APIGATEWAY_ROOT + "auto/serving/ci/{online_task_id}/",
            module=self.MODULE,
            url_keys=["online_task_id"],
            description="更新应用CI-在线训练任务",
            before_request=add_esb_info_before_request_for_bkdata_user,
            after_request=None,
            default_timeout=300,
        )


BkDataAIOPSApi = _BkDataAIOPSApi()
