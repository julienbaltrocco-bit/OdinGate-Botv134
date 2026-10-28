import os from "node:os";
import path from "node:path";

process.env.DATABASE_URL = process.env.TEST_DATABASE_URL ?? "postgres://postgres:postgres@localhost:5432/contentengine_test";
process.env.APP_ENCRYPTION_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
process.env.LLM_PROVIDER = "mock";
process.env.STORAGE_DRIVER = "local";
process.env.STORAGE_LOCAL_DIR = path.join(os.tmpdir(), "ce-test-media");
process.env.APP_URL = "http://localhost:3000";
process.env.INSTAGRAM_PUBLISHING_ENABLED = "false";
