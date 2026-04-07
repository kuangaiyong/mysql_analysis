<template>
  <div class="connection-selector">
    <span v-if="showLabel" class="selector-label">{{ label }}</span>
    <el-select
      :model-value="modelValue"
      :placeholder="placeholder"
      :style="{ width: `${width}px` }"
      :disabled="disabled"
      :clearable="clearable"
      @update:model-value="handleChange"
    >
      <el-option
        v-for="conn in connections"
        :key="conn.id"
        :label="conn.name"
        :value="conn.id"
      >
        <div class="connection-option">
          <span class="connection-name">{{ conn.name }}</span>
          <span class="connection-info">{{ conn.host }}:{{ conn.port }}</span>
        </div>
      </el-option>
    </el-select>
    <el-tag v-if="showStatus && modelValue" :type="statusType" size="small">
      已连接
    </el-tag>
    <el-tag v-else-if="showStatus" type="warning" size="small">
      未选择
    </el-tag>
    <slot name="actions" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useConnectionStore } from '@/pinia/modules/connection'
import type { Connection } from '@/types/connection'

interface Props {
  modelValue: number | null | undefined
  connections: Connection[]
  label?: string
  placeholder?: string
  width?: number
  showLabel?: boolean
  showStatus?: boolean
  disabled?: boolean
  clearable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: '当前连接：',
  placeholder: '请选择数据库连接',
  width: 280,
  showLabel: true,
  showStatus: true,
  disabled: false,
  clearable: false
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  change: [connectionId: number, connection: Connection | undefined]
}>()

const connectionStore = useConnectionStore()

const statusType = computed(() => {
  const conn = props.connections.find(c => c.id === props.modelValue)
  return conn?.is_active ? 'success' : 'info'
})

const handleChange = (value: number | null) => {
  emit('update:modelValue', value)
  
  if (value) {
    const connection = props.connections.find(c => c.id === value)
    if (connection) {
      connectionStore.setCurrentConnection(connection)
    }
    emit('change', value, connection)
  } else {
    emit('change', value as unknown as number, undefined)
  }
}
</script>

<style scoped lang="scss">
.connection-selector {
  display: flex;
  align-items: center;
  gap: 12px;

  .selector-label {
    font-weight: 500;
    color: var(--el-text-color-primary);
    white-space: nowrap;
  }

  .connection-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;

    .connection-name {
      font-weight: 500;
    }

    .connection-info {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-left: 8px;
    }
  }
}
</style>
