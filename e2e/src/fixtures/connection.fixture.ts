import { test as base } from './base.fixture';

type ConnectionFixtures = {
  apiClient: {
    get: (url: string) => Promise<any>;
    post: (url: string, data: any) => Promise<any>;
    put: (url: string, data: any) => Promise<any>;
    delete: (url: string) => Promise<any>;
  };
};

export const test = base.extend<ConnectionFixtures>({
  apiClient: async ({ apiBaseURL }, use) => {
    const createAPIClient = () => ({
      get: async (url: string) => {
        const response = await fetch(`${apiBaseURL}${url}`);
        return response.json();
      },
      post: async (url: string, data: any) => {
        const response = await fetch(`${apiBaseURL}${url}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        return response.json();
      },
      put: async (url: string, data: any) => {
        const response = await fetch(`${apiBaseURL}${url}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        return response.json();
      },
      delete: async (url: string) => {
        const response = await fetch(`${apiBaseURL}${url}`, {
          method: 'DELETE'
        });
        return response.json();
      }
    });

    await use(createAPIClient());
  }
});
