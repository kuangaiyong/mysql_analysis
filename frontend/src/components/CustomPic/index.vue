<template>
  <div class="custom-pic-wrapper">
    <div
      class="custom-pic-container"
      :class="[`custom-pic-${size}`, `custom-pic-${shape}`, { 'custom-pic-editable': editable }]"
      @click="handleClick"
    >
      <img v-if="displaySrc" :src="displaySrc" alt="avatar" class="custom-pic-image" />
      <div v-else class="custom-pic-placeholder">
        <el-icon :size="iconSize"><User /></el-icon>
      </div>

      <div v-if="editable" class="custom-pic-overlay">
        <el-icon :size="20"><Camera /></el-icon>
      </div>

      <input
        ref="fileInputRef"
        type="file"
        accept="image/jpeg,image/jpg,image/png,image/gif"
        :style="{ display: 'none' }"
        @change="handleFileChange"
      />
    </div>

    <el-dialog
      v-model="previewVisible"
      title="图片预览"
      width="500px"
      :append-to-body="true"
    >
      <img :src="previewSrc" alt="preview" style="width: 100%; display: block;" />
    </el-dialog>

    <el-dialog
      v-model="cropperVisible"
      title="裁剪图片"
      width="600px"
      :append-to-body="true"
      @close="handleCropperClose"
    >
      <div class="cropper-container">
        <img ref="cropperImageRef" :src="cropSrc" alt="crop" />
      </div>
      <template #footer>
        <el-button @click="cropperVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCropConfirm" :loading="cropping">
          确认裁剪
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Camera } from '@element-plus/icons-vue'

interface Props {
  src?: string
  size?: 'small' | 'medium' | 'large'
  shape?: 'circle' | 'square'
  editable?: boolean
  maxSize?: number
  enableCrop?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  src: '',
  size: 'medium',
  shape: 'circle',
  editable: false,
  maxSize: 2,
  enableCrop: true
})

const emit = defineEmits<{
  'update:src': [value: string]
  change: [file: File, url: string]
  error: [error: string]
}>()

const displaySrc = ref(props.src)
const previewVisible = ref(false)
const previewSrc = ref('')
const cropperVisible = ref(false)
const cropSrc = ref('')
const cropping = ref(false)
const fileInputRef = ref<HTMLInputElement>()
const cropperImageRef = ref<HTMLImageElement>()

let cropperInstance: any = null

const iconSize = computed(() => {
  const sizes = {
    small: 24,
    medium: 32,
    large: 40
  }
  return sizes[props.size]
})

const handleClick = () => {
  if (!props.editable) {
    if (displaySrc.value) {
      previewSrc.value = displaySrc.value
      previewVisible.value = true
    }
    return
  }
  fileInputRef.value?.click()
}

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (!isValidFile(file)) return

  const url = URL.createObjectURL(file)

  if (props.enableCrop) {
    cropSrc.value = url
    cropperVisible.value = true
  } else {
    displaySrc.value = url
    emit('update:src', url)
    emit('change', file, url)
  }

  target.value = ''
}

const isValidFile = (file: File): boolean => {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
  if (!validTypes.includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、GIF 格式的图片')
    emit('error', '不支持的图片格式')
    return false
  }

  const maxSizeMB = props.maxSize
  const maxSizeBytes = maxSizeMB * 1024 * 1024
  if (file.size > maxSizeBytes) {
    ElMessage.error(`图片大小不能超过 ${maxSizeMB}MB`)
    emit('error', '图片大小超出限制')
    return false
  }

  return true
}

const handleCropperClose = () => {
  if (cropperInstance) {
    cropperInstance.destroy()
    cropperInstance = null
  }
}

const handleCropConfirm = () => {
  if (!cropperInstance) return

  cropping.value = true
  try {
    const canvas = cropperInstance.getCroppedCanvas({
      width: 400,
      height: 400
    })
    const croppedUrl = canvas.toDataURL('image/png')
    displaySrc.value = croppedUrl
    emit('update:src', croppedUrl)
    emit('change', new File([croppedUrl], 'cropped.png'), croppedUrl)
    cropperVisible.value = false
    ElMessage.success('裁剪成功')
  } catch (error) {
    ElMessage.error('裁剪失败')
    emit('error', '裁剪失败')
  } finally {
    cropping.value = false
  }
}

const reset = () => {
  displaySrc.value = props.src || ''
}

const loadImage = async (url: string) => {
  return new Promise<void>((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      displaySrc.value = url
      resolve()
    }
    img.onerror = () => {
      reject(new Error('图片加载失败'))
    }
    img.src = url
  })
}

defineExpose({
  reset,
  loadImage
})
</script>

<script lang="ts">
export default {
  name: 'CustomPic'
}
</script>

<style scoped>
.custom-pic-wrapper {
  display: inline-block;
}

.custom-pic-container {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  background: #f5f7fa;
  border: 2px solid #dcdfe6;
  transition: all 0.3s;
}

.custom-pic-container:hover {
  border-color: #409eff;
}

.custom-pic-small {
  width: 32px;
  height: 32px;
}

.custom-pic-medium {
  width: 64px;
  height: 64px;
}

.custom-pic-large {
  width: 100px;
  height: 100px;
}

.custom-pic-circle {
  border-radius: 50%;
}

.custom-pic-square {
  border-radius: 8px;
}

.custom-pic-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.custom-pic-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.custom-pic-editable .custom-pic-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.3s;
}

.custom-pic-editable:hover .custom-pic-overlay {
  opacity: 1;
}

.cropper-container {
  width: 100%;
  height: 400px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cropper-container img {
  max-width: 100%;
  max-height: 100%;
}

@media (max-width: 768px) {
  .custom-pic-small {
    width: 28px;
    height: 28px;
  }

  .custom-pic-medium {
    width: 56px;
    height: 56px;
  }

  .custom-pic-large {
    width: 80px;
    height: 80px;
  }
}
</style>
