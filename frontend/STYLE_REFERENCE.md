# 样式工具类快速参考

> 本文档提供常用工具类的快速查找，详细说明请参考 [REFACTOR_GUIDE.md](./REFACTOR_GUIDE.md)

## 🚀 快速开始

### 页面容器
```vue
<!-- 所有页面使用统一的页面容器 -->
<div class="page-container">
  <!-- 页面内容 -->
</div>
```

### 搜索表单
```vue
<!-- 搜索表单区域 -->
<el-form class="search-form" :model="searchForm" inline>
  <!-- 表单内容 -->
</el-form>
```

### 输入框宽度
```vue
<el-input class="input-sm" />  <!-- 120px -->
<el-input class="input-md" />  <!-- 150px -->
<el-input class="input-lg" />  <!-- 200px -->
<el-input class="input-xl" />  <!-- 280px -->
```

### 间距工具
```vue
<div class="u-mb-20">...</div>  <!-- margin-bottom: 20px -->
<div class="u-mt-16">...</div>  <!-- margin-top: 16px -->
<div class="u-p-20">...</div>   <!-- padding: 20px -->
```

---

## 📋 常用工具类速查

### Spacing（间距）
| 类名 | CSS属性 | 值 |
|-----|---------|---|
| `.u-mb-4` | margin-bottom | 4px |
| `.u-mb-8` | margin-bottom | 8px |
| `.u-mb-12` | margin-bottom | 12px |
| `.u-mb-16` | margin-bottom | 16px |
| `.u-mb-20` | margin-bottom | 20px |
| `.u-mb-24` | margin-bottom | 24px |
| `.u-mt-*` | margin-top | 同上 |
| `.u-ml-*` | margin-left | 同上 |
| `.u-mr-*` | margin-right | 同上 |
| `.u-p-*` | padding | 同上 |

### Width（宽度）
| 类名 | 值 |
|-----|---|
| `.input-xs` | 80px |
| `.input-sm` | 120px |
| `.input-md` | 150px |
| `.input-lg` | 200px |
| `.input-xl` | 280px |
| `.w-full` | 100% |

### Flexbox（弹性布局）
| 类名 | CSS属性 |
|-----|---------|
| `.flex` | display: flex |
| `.flex-col` | flex-direction: column |
| `.items-center` | align-items: center |
| `.justify-between` | justify-content: space-between |
| `.justify-center` | justify-content: center |
| `.gap-4` | gap: 16px |

### Text（文本）
| 类名 | CSS属性 |
|-----|---------|
| `.text-center` | text-align: center |
| `.text-sm` | font-size: 13px |
| `.text-lg` | font-size: 16px |
| `.font-semibold` | font-weight: 600 |
| `.text-success` | color: 成功色 |
| `.text-warning` | color: 警告色 |
| `.text-danger` | color: 危险色 |

---

## 🔄 常见替换对照

| 替换前 | 替换后 |
|-------|--------|
| `style="width: 200px"` | `class="input-lg"` |
| `style="width: 100%"` | `class="w-full"` |
| `style="margin-bottom: 20px"` | `class="u-mb-20"` |
| `style="margin-top: 16px"` | `class="u-mt-16"` |
| `style="padding: 20px"` | `class="u-p-20"` |

---

## 📦 组件样式类

### 卡片头部
```vue
<template #header>
  <div class="card-header">
    <span>标题</span>
    <el-button>操作</el-button>
  </div>
</template>
```

### 统计项
```vue
<div class="stat-item">
  <div class="stat-label">标签</div>
  <div class="stat-value success">100</div>
</div>
```

### 状态指示器
```vue
<div class="status-indicator">
  <span class="status-dot online"></span>
  <span>在线</span>
</div>
```

---

## ⚠️ 注意事项

1. **优先使用工具类**：避免内联 `style` 属性
2. **组合使用**：可以同时使用多个工具类
3. **避免重复定义**：不要在组件内重新定义工具类已有的样式

```vue
<!-- ✅ 推荐 -->
<div class="u-mb-20 u-p-16 flex items-center">

<!-- ❌ 避免 -->
<div style="margin-bottom: 20px; padding: 16px; display: flex; align-items: center;">
```

---

*更多详情请参考 [REFACTOR_GUIDE.md](./REFACTOR_GUIDE.md)*
