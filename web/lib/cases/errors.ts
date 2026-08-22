export class CaseAccessError extends Error {
  constructor(public readonly status: number, message = "Case not found") {
    super(message);
    this.name = "CaseAccessError";
  }
}