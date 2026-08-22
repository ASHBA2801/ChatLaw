export class DocumentAccessError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "DocumentAccessError";
    this.status = status;
  }
}
