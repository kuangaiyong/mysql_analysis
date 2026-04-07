<template>
  <div ref="chartRef" class="foreign-key-graph"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref } from 'vue'
import * as echarts from 'echarts'
import { useElementSize } from '@vueuse/core'
import type { ForeignKey } from '@/types/table'

const props = defineProps<{
  foreignKeys: ForeignKey[]
  tableName: string
}>()

const chartRef = ref<HTMLElement>()
const { width, height } = useElementSize(chartRef)

let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value, 'dark')
  renderGraph()
}

const renderGraph = () => {
  if (!chart) return

  const nodes: any[] = []
  const links: any[] = []
  const nodeSet = new Set<string>()

  nodes.push({
    id: props.tableName,
    name: props.tableName,
    symbolSize: 50,
    itemStyle: { color: '#409EFF' },
    category: 0
  })
  nodeSet.add(props.tableName)

  props.foreignKeys.forEach((fk) => {
    const refTable = fk.referenced_table_name

    if (!nodeSet.has(refTable)) {
      nodes.push({
        id: refTable,
        name: refTable,
        symbolSize: 40,
        itemStyle: { color: '#67C23A' },
        category: 1
      })
      nodeSet.add(refTable)
    }

    links.push({
      source: props.tableName,
      target: refTable,
      label: {
        show: true,
        formatter: `${fk.column_name} → ${fk.referenced_column_name}`,
        fontSize: 10
      },
      lineStyle: {
        color: '#F56C6C',
        curveness: 0.2
      },
      data: fk
    })
  })

  const option = {
    title: {
      text: '外键关系图',
      textStyle: { color: '#fff' }
    },
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          const fk = params.data.data as ForeignKey
          return `
            <div style="padding: 8px;">
              <div><strong>约束名:</strong> ${fk.constraint_name}</div>
              <div><strong>列:</strong> ${fk.column_name}</div>
              <div><strong>引用表:</strong> ${fk.referenced_table_name}</div>
              <div><strong>引用列:</strong> ${fk.referenced_column_name}</div>
              <div><strong>ON UPDATE:</strong> ${fk.on_update}</div>
              <div><strong>ON DELETE:</strong> ${fk.on_delete}</div>
            </div>
          `
        }
        return params.name
      }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      roam: true,
      label: {
        show: true,
        position: 'bottom',
        color: '#fff'
      },
      force: {
        repulsion: 300,
        edgeLength: 150
      },
      lineStyle: {
        width: 2,
        curveness: 0.2
      }
    }]
  }

  chart.setOption(option, true)
}

watch(() => props.foreignKeys, () => {
  renderGraph()
}, { deep: true })

watch([width, height], () => {
  chart?.resize()
})

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  chart?.dispose()
})
</script>

<style scoped>
.foreign-key-graph {
  width: 100%;
  height: 400px;
}
</style>
