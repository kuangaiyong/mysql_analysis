<template>
  <div class="page-header">
    <div class="header-left">
      <el-button
        v-if="showBack"
        :icon="ArrowLeft"
        @click="handleBack"
      >
        返回
      </el-button>
      <h2 class="page-title">{{ title }}</h2>
      <slot name="extra" />
    </div>
    <div class="header-actions">
      <slot name="actions">
        <el-button
          v-if="showRefresh"
          :loading="refreshLoading"
          :icon="Refresh"
          @click="$emit('refresh')"
        >
          刷新
        </el-button>
        <el-button
          v-if="showAdd"
          type="primary"
          :icon="Plus"
          @click="$emit('add')"
        >
          {{ addText }}
        </el-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowLeft, Refresh, Plus } from '@element-plus/icons-vue'

interface Props {
  title: string
  showBack?: boolean
  showRefresh?: boolean
  showAdd?: boolean
  addText?: string
  refreshLoading?: boolean
  backTo?: string
}

const props = withDefaults(defineProps<Props>(), {
  showBack: false,
  showRefresh: false,
  showAdd: false,
  addText: '新增',
  refreshLoading: false,
  backTo: ''
})

const emit = defineEmits<{
  refresh: []
  add: []
  back: []
}>()

const router = useRouter()

const handleBack = () => {
  emit('back')
  if (props.backTo) {
    router.push(props.backTo)
  } else {
    router.back()
  }
}
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      margin: 0;
      color: var(--el-text-color-primary);
    }
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}
</style>
