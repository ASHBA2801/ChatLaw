import { access, mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

export const STORAGE_KEY_PATTERN =
  /^case\/[A-Za-z0-9_-]+\/[A-Za-z0-9_-]+\/[a-f0-9]{64}\.pdf$/;

export class StorageKeyError extends Error {
  constructor(message = "Invalid storage key") {
    super(message);
    this.name = "StorageKeyError";
  }
}

export interface StorageAdapter {
  put(key: string, bytes: Buffer): Promise<void>;
  get(key: string): Promise<Buffer>;
  delete(key: string): Promise<void>;
  exists(key: string): Promise<boolean>;
}

export function assertStorageKey(key: string): string {
  if (typeof key !== "string" || !STORAGE_KEY_PATTERN.test(key)) {
    throw new StorageKeyError();
  }
  if (key.includes("..") || key.includes("\\") || path.isAbsolute(key)) {
    throw new StorageKeyError();
  }
  return key;
}

export function caseStorageKey(userId: string, caseId: string, checksum: string): string {
  const key = `case/${userId}/${caseId}/${checksum}.pdf`;
  return assertStorageKey(key);
}

export class LocalStorageAdapter implements StorageAdapter {
  constructor(private readonly root: string) {}

  resolve(key: string): string {
    const safeKey = assertStorageKey(key);
    const root = path.resolve(this.root);
    const full = path.resolve(root, ...safeKey.split("/"));
    const relative = path.relative(root, full);
    if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
      throw new StorageKeyError();
    }
    return full;
  }

  async put(key: string, bytes: Buffer): Promise<void> {
    const full = this.resolve(key);
    await mkdir(path.dirname(full), { recursive: true });
    await writeFile(full, bytes, { flag: "wx" }).catch(async (error: NodeJS.ErrnoException) => {
      if (error.code === "EEXIST") {
        await writeFile(full, bytes);
        return;
      }
      throw error;
    });
  }

  async get(key: string): Promise<Buffer> {
    return readFile(this.resolve(key));
  }

  async delete(key: string): Promise<void> {
    try {
      await unlink(this.resolve(key));
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }

  async exists(key: string): Promise<boolean> {
    try {
      await access(this.resolve(key));
      return true;
    } catch {
      return false;
    }
  }
}

export class MemoryStorageAdapter implements StorageAdapter {
  readonly files = new Map<string, Buffer>();

  async put(key: string, bytes: Buffer): Promise<void> {
    this.files.set(assertStorageKey(key), Buffer.from(bytes));
  }

  async get(key: string): Promise<Buffer> {
    const value = this.files.get(assertStorageKey(key));
    if (!value) throw Object.assign(new Error("Object not found"), { code: "ENOENT" });
    return Buffer.from(value);
  }

  async delete(key: string): Promise<void> {
    this.files.delete(assertStorageKey(key));
  }

  async exists(key: string): Promise<boolean> {
    return this.files.has(assertStorageKey(key));
  }
}

export function defaultCaseStorageRoot(): string {
  return process.env.CASE_STORAGE_ROOT?.trim() || path.join(process.cwd(), ".data", "case-documents");
}

export function getCaseStorage(): StorageAdapter {
  return new LocalStorageAdapter(defaultCaseStorageRoot());
}
