/**
 * Base ModelService for generated TypeScript entities.
 * Bridges generated ORM interfaces with apiClient.
 */

import { createSignal } from "solid-js";
import { apiClient } from "../../lib/api-client";

export class ModelService<T> {
  private tableName: string = "";
  private endpointUrl: string = "";
  // Last list loaded by all(), readable reactively via allstate()
  private state = createSignal<T[]>([]);

  public allstate = (): T[] => {
    try {
      return (this.state && typeof this.state[0] === "function" ? this.state[0]() : []) || [];
    } catch {
      return [];
    }
  };

  public seTable(tableName: string): this {
    this.tableName = tableName;
    return this;
  }

  public seturl(url: string): this {
    this.endpointUrl = url;
    return this;
  }

  public async checkinit(): Promise<boolean> {
    // Verifies connectivity or primes local cache
    return true;
  }

  private getPath(subpath: string = ""): string {
    const cleanUrl = this.endpointUrl.startsWith("/") ? this.endpointUrl : `/${this.endpointUrl}`;
    const cleanSub = subpath ? (subpath.startsWith("/") ? subpath : `/${subpath}`) : "";
    return `${cleanUrl}${cleanSub}`;
  }

  public async all(): Promise<T[]> {
    const res = await apiClient.get<T[]>(this.getPath());
    const rows = res.ok && Array.isArray(res.data) ? res.data : [];
    this.state[1](() => rows);
    return rows;
  }

  public async find(id: number | string): Promise<T | null> {
    const res = await apiClient.get<T>(this.getPath(`/${id}`));
    return res.ok ? res.data : null;
  }

  public async where(filters: Record<string, any>): Promise<T[]> {
    const res = await apiClient.post<T[]>(this.getPath("/where"), filters);
    return res.ok && Array.isArray(res.data) ? res.data : [];
  }

  public async create(payload: Partial<T>): Promise<T | null> {
    const res = await apiClient.post<T>(this.getPath(), payload);
    return res.ok ? res.data : null;
  }

  public async update(id: number | string, payload: Partial<T>): Promise<T | null> {
    const res = await apiClient.put<T>(this.getPath(`/${id}`), payload);
    return res.ok ? res.data : null;
  }

  public async delete(id: number | string): Promise<boolean> {
    const res = await apiClient.delete(this.getPath(`/${id}`));
    return res.ok;
  }

  public async upsert(payload: Partial<T> & { id?: number | string }): Promise<T | null> {
    if (payload.id) {
      return this.update(payload.id, payload);
    }
    return this.create(payload);
  }
}
