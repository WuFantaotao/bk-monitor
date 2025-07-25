<!--
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
-->

<template>
  <div class="preview-file-content">
    <div class="flex-box">
      <bk-select
        style="width: 190px; margin-right: 20px; background-color: #fff"
        v-model="previewIp"
        :clearable="false"
        data-test-id="addNewExtraction_div_selectPreviewAddress"
        multiple
        show-select-all
      >
        <bk-option
          v-for="option in ipSelectNewNameList"
          :id="option.selectID"
          :key="option.selectID"
          :name="option.name"
        ></bk-option>
      </bk-select>
      <span style="font-size: 12px">{{ $t('文件日期') }}：</span>
      <file-date-picker
        :time-range.sync="timeRange"
        :time-value.sync="timeValue"
      />
      <bk-checkbox
        style="margin-right: 20px"
        v-model="isSearchChild"
        data-test-id="addNewExtraction_div_isSearchSubdirectory"
        >{{ $t('是否搜索子目录') }}</bk-checkbox
      >
      <bk-button
        :disabled="!ipList.length || !fileOrPath"
        :loading="isLoading"
        data-test-id="addNewExtraction_button_searchFilterCondition"
        size="small"
        theme="primary"
        @click="getExplorerList({})"
        >{{ $t('搜索') }}
      </bk-button>
    </div>
    <span class="table-head-text">{{ $t('从下载目标中选择预览目标') }}</span>
    <div
      class="flex-box"
      v-bkloading="{ isLoading, opacity: 0.7, zIndex: 0 }"
    >
      <bk-table
        ref="previewTable"
        style="background-color: #fff"
        class="preview-scroll-table"
        :data="explorerList"
        :height="360"
        @selection-change="handleSelect"
      >
        <bk-table-column
          width="60"
          :selectable="row => row.size !== '0'"
          type="selection"
        ></bk-table-column>
        <bk-table-column
          :label="$t('文件名')"
          :render-header="$renderHeader"
          :sort-by="['path', 'mtime', 'size']"
          min-width="400"
          prop="path"
          sortable
        >
          <template #default="{ row }">
            <div class="table-ceil-container">
              <span
                v-if="row.size === '0'"
                class="download-url-text"
                v-bk-overflow-tips
                @click="getExplorerList(row)"
              >
                {{ row.path }}
              </span>
              <span
                v-else
                v-bk-overflow-tips
                >{{ row.path }}</span
              >
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="$t('最后修改时间')"
          :render-header="$renderHeader"
          :sort-by="['mtime', 'path', 'size']"
          min-width="40"
          prop="mtime"
          sortable
        >
        </bk-table-column>
        <bk-table-column
          :label="$t('文件大小')"
          :render-header="$renderHeader"
          :sort-by="['size', 'mtime', 'path']"
          min-width="30"
          prop="size"
          sortable
        >
        </bk-table-column>
        <template #empty>
          <div>
            <empty-status
              :empty-type="emptyType"
              @operation="handleOperation"
            >
              <div v-if="emptyType === 'search-empty'">
                {{ $t('可以尝试{0}或{1}', { 0: $t('调整预览地址'), 1: $t('调整文件日期') }) }}
              </div>
            </empty-status>
          </div>
        </template>
      </bk-table>
    </div>
  </div>
</template>

<script>
  import { formatDate } from '@/common/util';
  import EmptyStatus from '@/components/empty-status';
  import FileDatePicker from '@/views/extract/home/file-date-picker';

  export default {
    components: {
      FileDatePicker,
      EmptyStatus,
    },
    model: {
      prop: 'downloadFiles',
      event: 'checked',
    },
    props: {
      ipList: {
        type: Array,
        required: true,
      },
      fileOrPath: {
        type: String,
        required: true,
      },
      ipSelectNewNameList: {
        type: Array,
        required: true,
      },
    },
    data() {
      // 默认范围一周
      const currentTime = Date.now();
      const startTime = new Date(currentTime - 1000 * 60 * 60 * 24 * 7);
      const endTime = new Date(currentTime);

      return {
        isLoading: false,
        previewIp: [],
        timeRange: '1w', // 时间跨度 ["1d", "1w", "1m", "all", "custom"]
        timeValue: [formatDate(startTime), formatDate(endTime)],
        isSearchChild: false,
        explorerList: [],
        historyStack: [], // 预览地址历史
        emptyType: 'empty',
      };
    },
    computed: {
      timeStringValue() {
        return [this.timeValue[0], this.timeValue[1]];
      },
    },
    watch: {
      ipList(val) {
        this.previewIp.splice(0);
        if (val.length) {
          this.previewIp.push(this.getIpListID(val[0]));
        }
        this.explorerList.splice(0); // 选择服务器后清空表格
        this.historyStack.splice(0); // 选择服务器后清空历史堆栈
      },
    },
    methods: {
      getExplorerList(row) {
        const { path = this.fileOrPath, size } = row;
        const cacheList = {
          exploreList: this.explorerList.splice(0),
          fileOrPath: path,
        };
        this.$emit('checked', []);
        if (path === '../' && this.historyStack.length) {
          // 返回上一级
          const cache = this.historyStack.pop();
          this.explorerList = cache.exploreList;
          const { fileOrPath } = this.historyStack[this.historyStack.length - 1];
          this.$emit('update:file-or-path', fileOrPath);
          return;
        }
        this.$emit('update:file-or-path', path);
        const ipList = this.getFindIpList();

        this.isLoading = true;
        this.emptyType = 'search-empty';
        this.$http
          .request('extract/getExplorerList', {
            data: {
              bk_biz_id: this.$store.state.bkBizId,
              ip_list: ipList,
              path: path || this.fileOrPath,
              time_range: this.timeRange,
              start_time: this.timeStringValue[0],
              end_time: this.timeStringValue[1],
              is_search_child: this.isSearchChild,
            },
          })
          .then(res => {
            if (path) {
              // 指定目录搜索
              this.historyStack.push(cacheList);
              const temp = {
                ...row,
                path: '../',
              };

              if (size === '0') this.explorerList = [temp, ...res.data];
              else this.explorerList = [...res.data];
            } else {
              // 搜索按钮
              this.historyStack = [];
              this.explorerList = res.data;
            }
          })
          .catch(err => {
            console.warn(err);
            this.emptyType = '500';
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      getFindIpList() {
        const ipList = [];
        for (let i = 0; i < this.previewIp.length; i++) {
          const target = this.ipList.find(item => this.getIpListID(item) === this.previewIp[i]);
          ipList.push(target);
        }
        return ipList;
      },
      // 拼接预览地址唯一key
      getIpListID(option) {
        return `${option.bk_host_id ?? ''}_${option.ip ?? ''}_${option.bk_cloud_id ?? ''}`;
      },
      // 父组件克隆时调用
      handleClone({
        ip_list: ipList,
        preview_ip_list: previewIpList,
        preview_directory: path,
        preview_time_range: timeRange,
        preview_start_time: startTime,
        preview_end_time: endTime,
        preview_is_search_child: isSearchChild,
        file_path: downloadFiles,
      }) {
        this.timeRange = timeRange;
        this.timeValue = [formatDate(new Date(startTime)), formatDate(new Date(endTime))];
        this.isSearchChild = isSearchChild;
        const findIpList = this.findPreviewIpListValue(previewIpList, ipList);
        this.previewIp = findIpList.map(item => this.getIpListID(item));

        this.isLoading = true;
        this.emptyType = 'search-empty';
        this.$http
          .request('extract/getExplorerList', {
            data: {
              bk_biz_id: this.$store.state.bkBizId,
              ip_list: findIpList,
              path,
              time_range: timeRange,
              start_time: startTime,
              end_time: endTime,
              is_search_child: isSearchChild,
            },
          })
          .then(res => {
            this.historyStack = [];
            this.explorerList = res.data;
            this.$nextTick(() => {
              downloadFiles.forEach(path => {
                for (const item of this.explorerList) {
                  if (item.path === path) {
                    this.$refs.previewTable.toggleRowSelection(item, true);
                    break;
                  }
                }
              });
            });
          })
          .catch(e => {
            console.warn(e);
            this.emptyType = '500';
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      findPreviewIpListValue(previewIpList, ipList) {
        // 获取previewIpList对应的ipList参数
        if (previewIpList?.length) {
          return previewIpList.map(item => {
            return ipList.find(dItem => {
              const hostMatch = item.bk_host_id === dItem.bk_host_id;
              const ipMatch = `${item.ip}_${item.bk_cloud_id}` === `${dItem.ip}_${dItem.bk_cloud_id}`;
              if (item?.bk_host_id) return hostMatch || ipMatch;
              return ipMatch;
            });
          });
        }
        return [];
      },
      handleOperation(type) {
        if (type === 'clear-filter') {
          this.params.keyword = '';
          this.getExplorerList({});
          return;
        }

        if (type === 'refresh') {
          this.emptyType = 'empty';
          this.getExplorerList({});
          return;
        }
      },
      handleSelect(selection) {
        this.$emit(
          'checked',
          selection.map(item => item.path),
        );
      },
    },
  };
</script>

<style lang="scss">
  .preview-file-content {
    display: flex;
    flex-flow: column;
    justify-content: center;
    width: calc(100% - 140px);
    max-width: 1000px;
    min-height: 40px;

    .flex-box {
      display: flex;
      align-items: center;

      .download-url-text {
        color: #3a84ff;
        cursor: pointer;

        &:hover {
          color: #699df4;
        }

        &:active {
          color: #2761dd;
        }

        &.is-disabled {
          color: #c4c6cc;
          cursor: not-allowed;
        }
      }
    }

    .table-head-text {
      margin: 18px 0 8px;
      font-size: 12px;
    }
  }

  .preview-scroll-table {
    .bk-table-body-wrapper {
      overflow-y: auto;
    }

    .cell {
      /* stylelint-disable-next-line declaration-no-important */
      display: flex !important;
    }
  }
</style>
