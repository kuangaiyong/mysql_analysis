import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'

// 模拟连接列表组件
const ConnectionList = defineComponent({
  template: `
    <div class="connection-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="connections.length === 0" class="empty">暂无连接</div>
      <div v-else class="list">
        <div v-for="conn in connections" :key="conn.id" class="connection-item">
          <span class="name">{{ conn.name }}</span>
          <span class="host">{{ conn.host }}:{{ conn.port }}</span>
          <button @click="editConnection(conn)" class="edit-btn">编辑</button>
          <button @click="deleteConnection(conn)" class="delete-btn">删除</button>
        </div>
      </div>
    </div>
  `,
  props: {
    connections: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const editConnection = (conn: any) => {
      console.log('Edit:', conn)
    }
    
    const deleteConnection = (conn: any) => {
      console.log('Delete:', conn)
    }
    
    return { editConnection, deleteConnection }
  }
})

describe('ConnectionList', () => {
  it('should show loading state', () => {
    const wrapper = mount(ConnectionList, {
      props: { loading: true }
    })
    
    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.find('.loading').text()).toBe('加载中...')
  })

  it('should show empty state', () => {
    const wrapper = mount(ConnectionList, {
      props: { connections: [], loading: false }
    })
    
    expect(wrapper.find('.empty').exists()).toBe(true)
    expect(wrapper.find('.empty').text()).toBe('暂无连接')
  })

  it('should render connection items', () => {
    const connections = [
      { id: 1, name: 'Local MySQL', host: 'localhost', port: 3306 },
      { id: 2, name: 'Production DB', host: '192.168.1.100', port: 3307 }
    ]
    
    const wrapper = mount(ConnectionList, {
      props: { connections, loading: false }
    })
    
    const items = wrapper.findAll('.connection-item')
    expect(items.length).toBe(2)
    expect(items[0].find('.name').text()).toBe('Local MySQL')
    expect(items[1].find('.host').text()).toBe('192.168.1.100:3307')
  })

  it('should render action buttons for each item', () => {
    const connections = [{ id: 1, name: 'Test', host: 'localhost', port: 3306 }]
    
    const wrapper = mount(ConnectionList, {
      props: { connections, loading: false }
    })
    
    const item = wrapper.find('.connection-item')
    expect(item.find('.edit-btn').exists()).toBe(true)
    expect(item.find('.delete-btn').exists()).toBe(true)
  })
})
