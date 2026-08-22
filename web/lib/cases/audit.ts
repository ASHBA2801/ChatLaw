type AuditDetails = {
  userId: string;
  caseId?: string;
  documentId?: string;
};

export function auditCaseAction(action: string, details: AuditDetails): void {
  console.info("[case-audit]", action, {
    userId: details.userId,
    caseId: details.caseId ?? null,
    documentId: details.documentId ?? null,
  });
}
