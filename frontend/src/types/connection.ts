export interface Connection {
  id: number
  name: string
  host: string
  port: number
  username: string
  password_encrypted: string
  database_name?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ConnectionCreate {
  name: string
  host: string
  port?: number
  username: string
  password: string
  database_name?: string
  connection_pool_size?: number
}

export interface ConnectionUpdate {
  name?: string
  host?: string
  port?: number
  username?: string
  password?: string
  database_name?: string
  connection_pool_size?: number
}

export interface ConnectionTest {
  name?: string
  host: string
  port: number
  username: string
  password: string
  database_name?: string
}

export interface ConnectionTestResult {
  status: string
  message: string
  latency?: number
}
