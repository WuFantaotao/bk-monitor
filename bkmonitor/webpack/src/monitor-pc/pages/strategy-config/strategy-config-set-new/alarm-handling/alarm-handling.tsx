/*
 * Tencent is pleased to support the open source community by making
 * 蓝鲸智云PaaS平台 (BlueKing PaaS) available.
 *
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 *
 * 蓝鲸智云PaaS平台 (BlueKing PaaS) is licensed under the MIT License.
 *
 * License for 蓝鲸智云PaaS平台 (BlueKing PaaS):
 *
 * ---------------------------------------------------
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of
 * the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
 * THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 * CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
import { Component, Emit, Inject, Prop, Ref, Watch } from 'vue-property-decorator';
import { Component as tsc } from 'vue-tsx-support';

import SetMealDeail from 'fta-solutions/pages/setting/set-meal-detail/set-meal-detail';
import { deepClone } from 'monitor-common/utils/utils';

import AIWhaleIcon from '../../../../components/ai-whale-icon/ai-whale-icon';
import * as ruleAuth from '../../authority-map';
import CommonItem from '../components/common-form-item';
import GroupSelect, { type IGroupItem } from '../components/group-select';

import type { IActionConfig } from '../type';
import type { strategyType } from '../typings/index';

import './alarm-handling.scss';

/**
 * @description: 转换为分组列表
 * @param {IActionConfig} actionConfigList
 * @return {*}
 */
export const actionConfigGroupList = (actionConfigList: IActionConfig[]): IGroupItem[] => {
  const groupMap = {};
  const groupList = [];
  actionConfigList.forEach(item => {
    if (groupMap?.[item.plugin_type]?.list.length) {
      groupMap[item.plugin_type].list.push({ id: item.id, name: item.name });
    } else {
      groupMap[item.plugin_type] = { groupName: item.plugin_name, list: [{ id: item.id, name: item.name }] };
    }
  });
  Object.keys(groupMap).forEach(key => {
    const obj = groupMap[key];
    groupList.push({ id: key, name: obj.groupName, children: obj.list });
  });
  return groupList;
};

export interface IValue {
  config_id?: number;
  user_groups?: number[];
  options: {
    converge_config: {
      converge_func: string; // 防御动作
      timedelta: number; // 防御窗口大小（秒），默认设置为 60
      count: number; // 执行次数，默认设置为 1
      is_enabled?: boolean; // 是否启用
    };
    enable_delay: number; // 数据延迟秒数
  };
  signal?: string[];
}

export interface IAllDefense {
  key: string;
  name: string;
  description?: string;
}

interface IAlarmHandlingNewProps {
  value?: IValue;
  allDefense?: IAllDefense[]; // 防御动作列表
  allAction?: IGroupItem[]; // 套餐列表
  readonly?: boolean;
  strategyId?: number | string;
  extCls?: string;
  isSimple?: boolean; // 简洁模式(无预览，无回填)
  list?: signalOptionsItem[];
}

interface IAlarmHandlingNewEvent {
  onChange?: IValue;
  onAddMeal?: () => void;
}

interface signalOptionsItem {
  id: string;
  name: string;
}

@Component({
  name: 'AlarmHandlingNew',
})
export default class AlarmHandlingNew extends tsc<IAlarmHandlingNewProps, IAlarmHandlingNewEvent> {
  @Prop({
    type: Object,
    default: () => ({
      config_id: 0,
      user_groups: [],
      options: {
        converge_config: {
          converge_func: 'skip_when_success', // 防御动作
          timedelta: 1, // 防御窗口大小（秒），默认设置为 60
          count: 1, // 执行次数，默认设置为 1
          is_enabled: true,
        },
        enable_delay: 1, // 数据延迟秒数
      },
    }),
  })
  value: IAlarmHandlingNewProps['value'];
  @Prop({ type: Array, default: () => [] }) allDefense: IAlarmHandlingNewProps['allDefense'];
  @Prop({ type: Array, default: () => [] }) allAction: IGroupItem[];
  @Prop({ type: Boolean, default: false }) readonly: boolean;
  @Prop({ default: '', type: [Number, String] }) strategyId: number;
  @Prop({ default: '', type: String }) extCls: string;
  @Prop({ default: false, type: Boolean }) isSimple: boolean;
  @Prop({ type: Array, default: () => [] }) list: signalOptionsItem[];

  @Inject('authority') authority;
  @Inject('handleShowAuthorityDetail') handleShowAuthorityDetail;
  @Inject('authorityMap') authorityMap;
  @Inject() strategyType: strategyType;

  @Ref('selectMeal') selectMealRef: GroupSelect;

  get defenseTips() {
    const tips = {};
    this.allDefense.forEach(item => {
      tips[item.key] = item.description;
    });
    return tips;
  }
  get noNoticeActionConfigList() {
    return this.allAction.filter(item => item.id !== 'notice');
  }

  data: IValue = {
    config_id: 0,
    user_groups: [],
    options: {
      converge_config: {
        converge_func: 'skip_when_success', // 防御动作
        timedelta: 1, // 防御窗口大小（秒），默认设置为 60
        count: 1, // 执行次数，默认设置为 1
        is_enabled: true,
      },
      enable_delay: 1, // 数据延迟秒数
    },
  };
  isShowDetail = false;

  disableDelay = false; // 关闭数据延迟秒数输入

  @Watch('value', { immediate: true, deep: true })
  handleValue(data: IAlarmHandlingNewProps['value']) {
    this.data = deepClone(data);
  }
  @Emit('change')
  handleChange() {
    return this.data;
  }

  // 切换套餐
  handleChangeConfigId(v: number | string) {
    this.data.config_id = Number(v);
    if (!this.isSimple) {
      this.handleShowMealDetail();
    }
    this.handleChange();
  }
  handleClearConfigId() {
    this.data.config_id = 0;
    this.handleChange();
  }

  // 数据延迟switch
  handleChangeDelay(isSwitchOn: boolean) {
    this.disableDelay = !isSwitchOn;
    if (!isSwitchOn) {
      this.data.options.enable_delay = 0;
      this.handleChange();
    }
  }

  handleToAddSetMeal() {
    this.handleAddMeal();
    this.selectMealRef?.destroyPopoverInstance();
    setTimeout(() => {
      this.$router.push({
        name: 'set-meal-add',
        params: {
          strategyId: !this.isSimple ? `${this.strategyId}` : undefined,
        },
      });
    }, 300);
  }

  @Emit('addMeal')
  handleAddMeal() {}

  handleShowMealDetail() {
    this.isShowDetail = true;
  }

  render() {
    return (
      <div class={['alarm-handling-new-component', this.extCls, { readonly: this.readonly }]}>
        <CommonItem
          title={this.$t('处理套餐')}
          show-semicolon
        >
          <span>{this.$t('当告警触发时执行')}</span>
          <GroupSelect
            ref='selectMeal'
            class='select-warp'
            list={this.noNoticeActionConfigList}
            placeholder={this.$tc('选择套餐')}
            readonly={this.readonly}
            value={this.data.config_id}
            onChange={data => this.handleChangeConfigId(data)}
            onClear={() => this.handleClearConfigId()}
          >
            <div
              style={{ width: '100%', height: '100%', display: 'flex', 'align-items': 'center' }}
              slot='extension'
              v-authority={{ active: !this.authority.MANAGE_ACTION_CONFIG }}
              onClick={() =>
                this.authority.MANAGE_ACTION_CONFIG
                  ? this.handleToAddSetMeal()
                  : this.handleShowAuthorityDetail(ruleAuth.MANAGE_ACTION_CONFIG)
              }
            >
              <i
                style='margin: 4px 4px 0 0;'
                class='icon-monitor icon-jia'
              />
              <span
                class='add-text'
                v-bk-tooltips={{
                  content: this.$t('进入新增页，新增完可直接返回不会丢失数据'),
                  disabled: this.isSimple,
                }}
              >
                {this.$t('新建套餐')}
                {!this.isSimple ? (
                  <span style={{ marginLeft: '10px', color: '#ea3636' }}>{`(${this.$t('新增后会进行回填')})`}</span>
                ) : undefined}
              </span>
            </div>
          </GroupSelect>
          {!this.isSimple ? (
            <bk-button
              style={{ padding: 0 }}
              disabled={this.data.config_id === 0}
              size='small'
              title='primary'
              text
              on-click={this.handleShowMealDetail}
            >
              {this.$t('button-预览')}
            </bk-button>
          ) : undefined}
        </CommonItem>
        <CommonItem
          title={this.$t('防御规则')}
          show-semicolon
        >
          <bk-switcher
            style={{ marginRight: '8px' }}
            v-model={this.data.options.converge_config.is_enabled}
            disabled={this.readonly}
            size='small'
            theme='primary'
            on-change={this.handleChange}
          />
          {this.data.options.converge_config.is_enabled && (
            <i18n
              class={`defense-wrap ${this.isSimple ? 'simple' : ''}`}
              path='当{0}分钟内执行{1}次时，防御动作{2}'
            >
              {!this.readonly ? (
                <bk-input
                  class='small-input'
                  v-model={this.data.options.converge_config.timedelta}
                  behavior='simplicity'
                  readonly={this.readonly}
                  showControls={false}
                  size='small'
                  type='number'
                  on-change={this.handleChange}
                />
              ) : (
                <span>{this.data.options.converge_config.timedelta}</span>
              )}
              {!this.readonly ? (
                <bk-input
                  class='small-input'
                  v-model={this.data.options.converge_config.count}
                  behavior='simplicity'
                  readonly={this.readonly}
                  showControls={false}
                  size='small'
                  type='number'
                  on-change={this.handleChange}
                />
              ) : (
                <span>{this.data.options.converge_config.count}</span>
              )}
              <bk-select
                class='select-inline'
                v-model={this.data.options.converge_config.converge_func}
                behavior={'simplicity'}
                clearable={false}
                popover-min-width={140}
                readonly={this.readonly}
                size='small'
                searchable
                on-change={this.handleChange}
              >
                {this.allDefense.map(option => (
                  <bk-option
                    id={option.key}
                    key={option.key}
                    name={option.name}
                  />
                ))}
              </bk-select>
            </i18n>
          )}
        </CommonItem>
        {this.data.options.converge_config.is_enabled && (
          <div class='tips-key1'>
            <AIWhaleIcon
              content={
                this.defenseTips[this.data.options.converge_config.converge_func] ||
                this.allDefense[0]?.description ||
                ''
              }
              type='explanation'
            />{' '}
            <span class='tip-text'>
              {this.defenseTips[this.data.options.converge_config.converge_func] ||
                this.allDefense[0]?.description ||
                ''}
            </span>
          </div>
        )}
        {this.data.options.converge_config.is_enabled && this.data.signal.includes(this.list[0].id) && (
          <CommonItem
            class='no-label'
            title=''
          >
            <bk-switcher
              class='converge-config-option'
              disabled={this.readonly}
              size='small'
              theme='primary'
              value
              on-change={this.handleChangeDelay}
            />
            <i18n
              class={`defense-wrap ${this.isSimple ? 'simple' : ''}`}
              path='当首次异常时间超过{0}分钟时不执行该套餐'
            >
              {!this.readonly ? (
                <bk-input
                  class='small-input'
                  v-model={this.data.options.enable_delay}
                  behavior='simplicity'
                  readonly={this.readonly || this.disableDelay}
                  showControls={false}
                  size='small'
                  type='number'
                  on-change={this.handleChange}
                />
              ) : (
                <span>{this.data.options.enable_delay}</span>
              )}
            </i18n>
          </CommonItem>
        )}

        <SetMealDeail
          id={this.data.config_id}
          v-model={this.isShowDetail}
          needEditTips={!this.readonly}
          strategyId={this.strategyId}
          strategyType={this.strategyType}
        />
      </div>
    );
  }
}
