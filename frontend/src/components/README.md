# 全局组件使用说明

## Application组件

全局应用级组件，提供加载状态管理、错误处理和应用状态显示。

### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| loading | 是否显示加载遮罩 | boolean | false |
| loadingText | 加载提示文字 | string | '加载中...' |
| wsStatus | WebSocket连接状态 | 'connected' \| 'disconnected' \| 'connecting' \| 'error' | - |
| lastUpdateTime | 最后更新时间戳 | number | - |

### Events

通过 `defineExpose` 暴露的方法：

- `handleError(error: Error)` - 显示错误通知
- `handleWarning(message: string)` - 显示警告通知
- `handleSuccess(message: string)` - 显示成功通知
- `handleInfo(message: string)` - 显示信息通知
- `showNotification(options)` - 显示自定义通知

### 示例

```vue
<template>
  <Application
    :loading="loading"
    :loading-text="'正在加载...'"
    :ws-status="wsStatus"
    :last-update-time="lastUpdateTime"
    ref="appRef"
  />
</template>

<script setup>
import { ref } from 'vue'
import Application from '@/components/Application/index.vue'

const appRef = ref()
const loading = ref(false)

const showError = () => {
  appRef.value?.handleError(new Error('操作失败'))
}
</script>
```

---

## WarningBar组件

警告提示组件，支持多种类型和自定义样式。

### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| title | 标题 | string | '' |
| message | 消息内容（必填） | string | '' |
| type | 类型 | 'info' \| 'warning' \| 'error' \| 'success' | 'info' |
| closable | 是否可关闭 | boolean | true |
| icon | 图标名称 | string | '' |
| showIcon | 是否显示图标 | boolean | true |

### Events

| 事件名 | 说明 |
|--------|------|
| close | 关闭时触发 |

### 示例

```vue
<template>
  <WarningBar
    title="提示"
    message="这是一条提示信息"
    type="info"
    @close="handleClose"
  />

  <WarningBar
    title="警告"
    message="这是一条警告信息"
    type="warning"
  />

  <WarningBar
    title="错误"
    message="这是一条错误信息"
    type="error"
  />

  <WarningBar
    title="成功"
    message="操作成功！"
    type="success"
  />
</template>

<script setup>
import WarningBar from '@/components/WarningBar/index.vue'

const handleClose = () => {
  console.log('WarningBar closed')
}
</script>
```

---

## CustomPic组件

自定义图片组件，支持图片上传、预览和裁剪。

### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| src | 图片URL | string | '' |
| size | 尺寸 | 'small' \| 'medium' \| 'large' | 'medium' |
| shape | 形状 | 'circle' \| 'square' | 'circle' |
| editable | 是否可编辑 | boolean | false |
| maxSize | 最大文件大小（MB） | number | 2 |
| enableCrop | 是否启用裁剪 | boolean | true |

### Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| update:src | 图片更新 | (value: string) |
| change | 图片改变 | (file: File, url: string) |
| error | 错误发生 | (error: string) |

### Methods (通过 `defineExpose` 暴露)

| 方法名 | 说明 | 参数 |
|--------|------|------|
| reset | 重置图片 | - |
| loadImage | 加载图片 | (url: string) |

### 示例

```vue
<template>
  <CustomPic
    v-model:src="avatar"
    size="large"
    shape="circle"
    :editable="true"
    :max-size="2"
    @change="handleImageChange"
    @error="handleError"
  />
</template>

<script setup>
import { ref } from 'vue'
import CustomPic from '@/components/CustomPic/index.vue'

const avatar = ref('')

const handleImageChange = (file, url) => {
  console.log('Image changed:', file, url)
}

const handleError = (error) => {
  console.error('Image error:', error)
}
</script>
```

---

## Charts组件

### QPSChart组件

QPS趋势图表组件。

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| connectionId | 连接ID | number | - |
| title | 图表标题 | string | 'QPS趋势' |
| height | 图表高度 | string \| number | 300 |
| loading | 是否加载中 | boolean | false |
| maxDataPoints | 最大数据点数 | number | 60 |
| showArea | 是否显示面积 | boolean | true |
| smooth | 是否平滑曲线 | boolean | true |
| color | 线条颜色 | string | '#409EFF' |

#### Events

| 事件名 | 说明 |
|--------|------|
| refresh | 刷新时触发 |
| export | 导出时触发 |

#### Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| updateData | 更新数据 | (newData: number, newTimestamp: string) |
| clearData | 清空数据 | - |

### TPSChart组件

TPS趋势图表组件，支持读写分离显示。

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| connectionId | 连接ID | number | - |
| title | 图表标题 | string | 'TPS趋势' |
| height | 图表高度 | string \| number | 300 |
| loading | 是否加载中 | boolean | false |
| maxDataPoints | 最大数据点数 | number | 60 |
| showArea | 是否显示面积 | boolean | true |
| smooth | 是否平滑曲线 | boolean | true |
| showDataLabel | 是否显示数据标签 | boolean | false |
| readColor | 读TPS颜色 | string | '#409EFF' |
| writeColor | 写TPS颜色 | string | '#67C23A' |
| showRead | 是否显示读TPS | boolean | true |
| showWrite | 是否显示写TPS | boolean | true |

#### Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| refresh | 刷新时触发 | - |
| export | 导出时触发 | (chart: echarts.ECharts) |
| legendChange | 图例切换时触发 | (selected: string[]) |

#### Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| updateData | 更新数据 | (readTPS: number, writeTPS: number, newTimestamp: string) |
| clearData | 清空数据 | - |

### MetricChart组件

通用指标图表组件，支持多种图表类型。

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| connectionId | 连接ID | number | - |
| chartType | 图表类型 | 'line' \| 'bar' \| 'pie' | 'line' |
| title | 图表标题 | string | '指标趋势' |
| metricName | 指标名称 | string | '指标' |
| height | 图表高度 | string \| number | 300 |
| loading | 是否加载中 | boolean | false |
| maxDataPoints | 最大数据点数 | number | 60 |
| showArea | 是否显示面积 | boolean | true |
| smooth | 是否平滑曲线 | boolean | true |
| seriesConfig | 系列配置 | MetricSeriesConfig[] | [] |
| categories | 分类数据 | string[] | [] |
| showDataZoom | 是否显示数据缩放 | boolean | false |
| showDataLabel | 是否显示数据标签 | boolean | false |
| theme | 主题 | 'light' \| 'dark' | 'light' |

#### MetricSeriesConfig接口

```typescript
interface MetricSeriesConfig {
  name: string
  type: 'line' | 'bar' | 'pie'
  data: number[] | { name?: string; value: number }[]
  color?: string
  smooth?: boolean
  areaStyle?: boolean
  stack?: string
  yAxisIndex?: number
}
```

#### Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| refresh | 刷新时触发 | - |
| export | 导出时触发 | (chart: echarts.ECharts) |
| dataZoom | 数据缩放时触发 | (start: number, end: number) |
| dataPointClick | 数据点点击时触发 | (params: any) |

#### Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| updateData | 更新数据 | (newData: number, newTimestamp: string) |
| clearData | 清空数据 | - |
| refreshChart | 刷新图表 | - |

#### 示例

```vue
<template>
  <QPSChart
    ref="qpsChartRef"
    :connection-id="connectionId"
    title="QPS实时监控"
    :loading="loading"
    @refresh="handleRefresh"
  />

  <TPSChart
    ref="tpsChartRef"
    :connection-id="connectionId"
    title="TPS实时监控"
    :loading="loading"
    :show-data-label="true"
    @legend-change="handleLegendChange"
  />

  <MetricChart
    ref="metricChartRef"
    :connection-id="connectionId"
    chart-type="line"
    title="多指标对比"
    :series-config="seriesConfig"
    :show-data-zoom="true"
    @data-point-click="handlePointClick"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { QPSChart, TPSChart, MetricChart } from '@/components/Charts'

const connectionId = ref(1)
const loading = ref(false)
const qpsChartRef = ref()
const tpsChartRef = ref()
const metricChartRef = ref()

const seriesConfig = ref([
  {
    name: 'CPU使用率',
    type: 'line',
    data: [],
    color: '#409EFF'
  },
  {
    name: '内存使用率',
    type: 'line',
    data: [],
    color: '#67C23A'
  }
])

const handleRefresh = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1000)
}

const handleLegendChange = (selected) => {
  console.log('Legend changed:', selected)
}

const handlePointClick = (params) => {
  console.log('Point clicked:', params)
}

onMounted(() => {
  setInterval(() => {
    const now = new Date().toLocaleTimeString()
    const qps = Math.floor(Math.random() * 1000)
    const readTps = Math.floor(Math.random() * 500)
    const writeTps = Math.floor(Math.random() * 200)

    qpsChartRef.value?.updateData(qps, now)
    tpsChartRef.value?.updateData(readTps, writeTps, now)
  }, 2000)
})
</script>
```

---

## 组件全局注册

如需全局注册这些组件，在 `main.ts` 中添加：

```typescript
import Application from '@/components/Application/index.vue'
import WarningBar from '@/components/WarningBar/index.vue'
import CustomPic from '@/components/CustomPic/index.vue'

app.component('Application', Application)
app.component('WarningBar', WarningBar)
app.component('CustomPic', CustomPic)
```
