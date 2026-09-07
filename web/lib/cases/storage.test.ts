import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  assertStorageKey,
  caseStorageKey,
  LocalStorageAdapter,
  MemoryStorageAdapter,
  StorageKeyError,
} from "./storage";

describe("case storage keys", () => {
  it("accepts owned case object keys", () => {
    expect(caseStorageKey("user1", "case1", "a".repeat(64))).toBe(`case/user1/case1/${"a".repeat(64)}.pdf`);
  });

  it("rejects path traversal and arbitrary keys", () => {
    expect(() => assertStorageKey("../secret.pdf")).toThrow(StorageKeyError);
    expect(() => assertStorageKey("case/user/../case/ab.pdf")).toThrow(StorageKeyError);
    expect(() => assertStorageKey("/tmp/file.pdf")).toThrow(StorageKeyError);
    expect(() => assertStorageKey("case/user/case/not-a-hash.pdf")).toThrow(StorageKeyError);
  });
});

describe("local storage adapter", () => {
  it("writes, reads, and deletes only under the root", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "chatlaw-storage-"));
    const storage = new LocalStorageAdapter(root);
    const key = caseStorageKey("user1", "case1", "b".repeat(64));
    await storage.put(key, Buffer.from("%PDF-test"));
    expect(await storage.exists(key)).toBe(true);
    expect((await storage.get(key)).toString()).toBe("%PDF-test");
    await storage.delete(key);
    expect(await storage.exists(key)).toBe(false);
    await rm(root, { recursive: true, force: true });
  });
});

describe("memory storage adapter", () => {
  it("isolates objects by key", async () => {
    const storage = new MemoryStorageAdapter();
    const key = caseStorageKey("user1", "case1", "c".repeat(64));
    await storage.put(key, Buffer.from("one"));
    expect((await storage.get(key)).toString()).toBe("one");
    await storage.delete(key);
    await expect(storage.get(key)).rejects.toMatchObject({ code: "ENOENT" });
  });
});
