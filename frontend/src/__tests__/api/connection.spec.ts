import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import { connectionsApi } from "@/api/connection"
import service from "@/api/client"

describe("connection API", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe("getAll", () => {
    it("should return connection list", async () => {
      const mockData = [{ id: 1, name: "Test Connection" }]
      ;(service.get as any).mockResolvedValue({ data: mockData })

      const result = await connectionsApi.getAll()

      expect(service.get).toHaveBeenCalledWith("/connections/", {})
      expect(result).toEqual(mockData)
    })

    it("should handle API error", async () => {
      ;(service.get as any).mockRejectedValue(new Error("Failed to fetch connections"))

      await expect(connectionsApi.getAll()).rejects.toThrow("Failed to fetch connections")
    })
  })

  describe("getById", () => {
    it("should return single connection", async () => {
      const mockData = { id: 1, name: "Test Connection" }
      ;(service.get as any).mockResolvedValue({ data: mockData })

      const result = await connectionsApi.getById(1)

      expect(service.get).toHaveBeenCalledWith("/connections/1")
      expect(result).toEqual(mockData)
    })
  })

  describe("create", () => {
    it("should create new connection", async () => {
      const mockData = { id: 4, name: "New Connection" }
      ;(service.post as any).mockResolvedValue({ data: mockData })

      const result = await connectionsApi.create({ name: "New Connection", host: "localhost", port: 3306, username: "root", password: "test" })

      expect(service.post).toHaveBeenCalledWith("/connections/", { name: "New Connection", host: "localhost", port: 3306, username: "root", password: "test" })
      expect(result).toHaveProperty("id", 4)
    })
  })

  describe("update", () => {
    it("should update connection", async () => {
      const mockData = { id: 1, name: "Updated Connection" }
      ;(service.put as any).mockResolvedValue({ data: mockData })

      const result = await connectionsApi.update(1, { name: "Updated Connection" })

      expect(service.put).toHaveBeenCalledWith("/connections/1", { name: "Updated Connection" })
      expect(result.name).toBe("Updated Connection")
    })
  })

  describe("delete", () => {
    it("should delete connection", async () => {
      ;(service.delete as any).mockResolvedValue(undefined)

      const result = await connectionsApi.delete(1)

      expect(service.delete).toHaveBeenCalledWith("/connections/1")
      expect(result).toBeUndefined()
    })
  })

  describe("test", () => {
    it("should test connection", async () => {
      const mockData = { status: "success", message: "Connection successful", latency: 10.5 }
      ;(service.post as any).mockResolvedValue({ data: mockData })

      const result = await connectionsApi.test({ host: "localhost", port: 3306, username: "root", password: "test" })

      expect(service.post).toHaveBeenCalledWith("/connections/test", { host: "localhost", port: 3306, username: "root", password: "test" })
      expect(result).toEqual(mockData)
    })
  })
})
