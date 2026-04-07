import { test as base } from './base.fixture';

type DatabaseFixtures = {
  testConnection: {
    name: string;
    host: string;
    port: number;
    username: string;
    password: string;
    database: string;
  };
  mockSlowQueries: any[];
  mockMetrics: any;
};

export const test = base.extend<DatabaseFixtures>({
  testConnection: async ({}, use) => {
    const connection = {
      name: 'Test Connection',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'test-password',
      database: 'test_db'
    };
    await use(connection);
  },

  mockSlowQueries: async ({}, use) => {
    const queries = [
      {
        id: 1,
        query_hash: 'abc123',
        sql: 'SELECT * FROM users WHERE email = "test@example.com"',
        execution_count: 100,
        avg_query_time: 2.5,
        max_query_time: 5.0,
        timestamp: new Date().toISOString()
      },
      {
        id: 2,
        query_hash: 'def456',
        sql: 'SELECT * FROM orders WHERE user_id = 123',
        execution_count: 50,
        avg_query_time: 1.8,
        max_query_time: 3.0,
        timestamp: new Date().toISOString()
      }
    ];
    await use(queries);
  },

  mockMetrics: async ({}, use) => {
    const metrics = {
      qps: 1250.5,
      tps: 85.3,
      connections: 42,
      active_threads: 15,
      buffer_pool_hit_rate: 98.5,
      timestamp: new Date().toISOString()
    };
    await use(metrics);
  }
});
