# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - 监控平台 (BlueKing - Monitor) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
from collections import OrderedDict, defaultdict
from datetime import datetime

from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

from apm.core.discover.base import (
    DiscoverBase,
    exists_field,
    extract_field_value,
    get_topo_instance_key,
)
from apm.models import ApmTopoDiscoverRule, TopoNode
from bkmonitor.utils.thread_backend import ThreadPool
from constants.apm import OtlpKey, TopoServiceAttributes


class NodeDiscover(DiscoverBase):
    MAX_COUNT = 100000
    model = TopoNode
    MAX_CONCURRENCY_NUMBER = 5  # 线程池的线程数量
    BATCH_NUM = 100  # 多线程处理span的数量

    @property
    def extra_data_factory(self):
        return defaultdict(
            lambda: {
                "extra_data": {"category": "", "kind": "", "predicate_value": "", "service_language": "", "type": ""},
                "framework": [],
                "platform": {},
                "sdk": [],
            }
        )

    def discover(self, origin_data):
        rules_map = {}

        rules, other_rule = self.get_rules()
        for rule in rules:
            if rule.type not in rules_map:
                rules_map[rule.type] = []
            rules_map[rule.type].append(rule)

        sort_order = ["category", "framework", "platform", "sdk"]
        # 创建有序字典
        sorted_rules_map = OrderedDict()
        for key in sort_order:
            if key in rules_map:
                sorted_rules_map[key] = rules_map[key]

        exists_instances = self.list_exists()

        create_topo_instances = {}
        update_topo_instances = {}
        further_instances = {}

        # 设置线程数量
        pool = ThreadPool(self.MAX_CONCURRENCY_NUMBER)
        # 将 origin_data 列表分成批次
        for i in range(0, len(origin_data), self.BATCH_NUM):
            batch_list = origin_data[i : i + self.BATCH_NUM]
            # 提交每一批次到线程池
            pool.apply_async(
                self.batch_execute,
                args=(
                    batch_list,
                    sorted_rules_map,
                    other_rule,
                    further_instances,
                    exists_instances,
                    update_topo_instances,
                    create_topo_instances,
                ),
            )

        for k, v in further_instances.items():
            if k not in update_topo_instances and k not in create_topo_instances and k not in exists_instances.keys():
                # avoid the problem that the service of the fixed-format component span is not found
                create_topo_instances.update({k: v})

        # update
        for topo_key, topo_value in update_topo_instances.items():
            TopoNode.objects.filter(bk_biz_id=self.bk_biz_id, app_name=self.app_name, topo_key=topo_key).update(
                **topo_value, updated_at=datetime.now()
            )

        # create
        create_instances = [
            TopoNode(bk_biz_id=self.bk_biz_id, app_name=self.app_name, topo_key=topo_key, **topo_value)
            for topo_key, topo_value in create_topo_instances.items()
        ]
        TopoNode.objects.bulk_create(create_instances)

        self.clear_if_overflow()
        self.clear_expired()

    def batch_execute(
        self,
        batch_list,
        sorted_rules_map,
        other_rule,
        further_instances,
        exists_instances,
        update_topo_instances,
        create_topo_instances,
    ):
        for span in batch_list:
            find_instances = self.extra_data_factory
            topo_key = None
            for topo_type, rule_list in sorted_rules_map.items():
                if topo_type == ApmTopoDiscoverRule.APM_TOPO_TYPE_CATEGORY:
                    match_rule = self.get_match_rule(span, rule_list, other_rule)
                    if match_rule:
                        topo_key = self.get_topo_key(match_rule, span)
                        self.find_category(match_rule, other_rule, span, find_instances, further_instances, topo_key)

                if topo_type == ApmTopoDiscoverRule.APM_TOPO_TYPE_FRAMEWORK:
                    match_rule = self.get_match_rule(span, rule_list, other_rule)
                    if match_rule:
                        self.find_framework(match_rule, span, find_instances, topo_key)

                if topo_type == ApmTopoDiscoverRule.APM_TOPO_TYPE_PLATFORM:
                    match_rule = self.get_match_rule(span, rule_list, other_rule)
                    if match_rule:
                        self.find_platform(match_rule, span, find_instances, topo_key)

                if topo_type == ApmTopoDiscoverRule.APM_TOPO_SDK_SDK:
                    match_rule = self.get_match_rule(span, rule_list, other_rule)
                    if match_rule:
                        self.find_sdk(match_rule, span, find_instances, topo_key)

            update_keys = find_instances.keys() & exists_instances.keys()
            create_keys = find_instances.keys() - update_keys

            update_topo_instances.update({k: find_instances[k] for k in update_keys})
            create_topo_instances.update({k: find_instances[k] for k in create_keys})

    def get_topo_key(self, match_rule, span):
        topo_key = get_topo_instance_key(
            match_rule.instance_keys,
            match_rule.topo_kind,
            match_rule.category_id,
            span,
            component_predicate_keys=match_rule.predicate_key,
        )
        if match_rule.topo_kind == ApmTopoDiscoverRule.TOPO_COMPONENT:
            # 组件类型的节点名称需要添加上服务名称的前缀 (不考虑拼接后与用户定义的服务重名情况需要引导用户进行更改)
            topo_key = f"{self.get_service_name(span)}-{topo_key}"
        return topo_key

    def find_category(self, match_rule, other_rule, span, find_instances, further_instances, topo_key):
        self.find_remote_service(span, match_rule, find_instances)

        find_instances[topo_key]["extra_data"]["category"] = match_rule.category_id
        find_instances[topo_key]["extra_data"]["kind"] = match_rule.topo_kind
        find_instances[topo_key]["extra_data"]["type"] = match_rule.type
        find_instances[topo_key]["extra_data"]["predicate_value"] = extract_field_value(match_rule.predicate_key, span)
        find_instances[topo_key]["extra_data"]["service_language"] = extract_field_value(
            (OtlpKey.RESOURCE, ResourceAttributes.TELEMETRY_SDK_LANGUAGE), span
        )
        if match_rule.topo_kind == ApmTopoDiscoverRule.TOPO_COMPONENT:
            other_rule_topo_key = get_topo_instance_key(
                other_rule.instance_keys,
                other_rule.topo_kind,
                other_rule.category_id,
                span,
            )
            if other_rule_topo_key not in further_instances:
                further_instances[other_rule_topo_key] = {}
            further_instances[other_rule_topo_key]["extra_data"] = {
                "category": other_rule.category_id,
                "kind": other_rule.topo_kind,
                "predicate_value": extract_field_value(other_rule.predicate_key, span),
                "service_language": extract_field_value(
                    (OtlpKey.RESOURCE, ResourceAttributes.TELEMETRY_SDK_LANGUAGE), span
                ),
            }

    def find_framework(self, match_rule, span, find_instances, topo_key):
        find_instances[topo_key]["framework"].append(
            {
                "name": match_rule.category_id,
                "extra_data": {''.join(match_rule.predicate_key): extract_field_value(match_rule.predicate_key, span)}
                if extract_field_value(match_rule.predicate_key, span)  # 当predicate_key为('','')时，"extra_data"的值为{}
                else {},
            }
        )

    def find_platform(self, match_rule, span, find_instances, topo_key):
        if match_rule.category_id == TopoServiceAttributes.K8S:
            # 如果span内的resource.telemetry.sdk值为"gelileo"，则将resource.target值通过.分割，取第一部分
            if (
                extract_field_value((OtlpKey.RESOURCE, TopoServiceAttributes.TELEMETRY_SDK_NAME), span)
                == ApmTopoDiscoverRule.APM_TOPO_GELILEO
            ):
                resource_target = extract_field_value((OtlpKey.RESOURCE, TopoServiceAttributes.RESOURCE_TARGET), span)
                if resource_target:
                    resource_target = resource_target.split('.', 1)[0]
                find_instances[topo_key]["platform"] = {
                    "name": match_rule.category_id,
                    # 以resource.target为key，以被.分割并取第一部分的resource.target的值作为value
                    "extra_data": {OtlpKey.get_resource_key(TopoServiceAttributes.RESOURCE_TARGET): resource_target}
                    if resource_target
                    else {},
                }

            else:
                find_instances[topo_key]["platform"] = {"name": TopoServiceAttributes.K8S}
        elif match_rule.category_id == TopoServiceAttributes.NODE:
            find_instances[topo_key]["platform"] = {"name": TopoServiceAttributes.NODE}

    def find_sdk(self, match_rule, span, find_instances, topo_key):
        find_instances[topo_key]["sdk"].append(
            {"name": extract_field_value(match_rule.predicate_key, span), "extra_data": {}}
        )

    def list_exists(self):
        res = {}
        topo_nodes = TopoNode.objects.filter(bk_biz_id=self.bk_biz_id, app_name=self.app_name)
        for node in topo_nodes:
            if node.topo_key not in res:
                res[node.topo_key] = {}
            res[node.topo_key]["extra_data"] = node.extra_data
            res[node.topo_key]["framework"] = node.framework
            res[node.topo_key]["platform"] = node.platform
            res[node.topo_key]["sdk"] = node.sdk

        return res

    def find_remote_service(self, span, rule, instance_map):
        predicate_key = (OtlpKey.ATTRIBUTES, SpanAttributes.PEER_SERVICE)

        if exists_field(predicate_key, span):
            instance_key = get_topo_instance_key(
                [predicate_key],
                ApmTopoDiscoverRule.TOPO_REMOTE_SERVICE,
                rule.category_id,
                span,
            )
            instance_map[instance_key]["extra_data"]["category"] = rule.category_id
            # remote service found by span additionally
            instance_map[instance_key]["extra_data"]["kind"] = ApmTopoDiscoverRule.TOPO_REMOTE_SERVICE
            instance_map[instance_key]["extra_data"]["predicate_value"] = extract_field_value(predicate_key, span)
