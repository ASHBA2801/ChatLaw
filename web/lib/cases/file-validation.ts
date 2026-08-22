const MAX_FILE_SIZE = 15 * 1024 * 1024;
const SAFE_NAME = /^[\w .()\-]+$/u;

export function validateCaseFile(file: File) {
  const name = file.name.trim();
  if (file.type !== "application/pdf") throw new Error("Only PDF documents are supported currently.");
  if (!name.toLowerCase().endsWith(".pdf")) throw new Error("Only PDF documents are supported currently.");
  if (file.size <= 0 || file.size > MAX_FILE_SIZE) throw new Error("PDF files must be between 1 byte and 15 MB.");
  if (!SAFE_NAME.test(name) || name.includes("..") || name.includes("/") || name.includes("\\")) {
    throw new Error("The filename contains unsupported characters.");
  }
}