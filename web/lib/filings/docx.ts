import { AlignmentType, Document, Packer, Paragraph, TextRun } from "docx";

/** Strip characters that are illegal in XML 1.0 (they corrupt the .docx). */
function clean(value: string): string {
  return value.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F￾￿]/g, "");
}

/**
 * A filing as an editable Word document. The text is the user's saved version,
 * so edits made on the document page carry over. A font with Indic coverage is
 * named so complaints drafted in Indian languages render in Word.
 */
export async function buildFilingDocx(input: { title: string; body: string; disclaimer?: string | null }): Promise<Buffer> {
  const font = "Nirmala UI";
  const lines = clean(input.body).replace(/\r/g, "").split("\n");
  const paragraphs = lines.map((line) => {
    const trimmed = line.trim();
    const heading = /^[A-Z0-9 .,'()/&:-]{6,}$/.test(trimmed) && !/[a-z]/.test(trimmed);
    return new Paragraph({
      alignment: heading ? AlignmentType.CENTER : AlignmentType.LEFT,
      spacing: { after: 100, line: 300 },
      children: [new TextRun({ text: line || " ", bold: heading, font, size: 24 })],
    });
  });
  if (input.disclaimer) {
    paragraphs.push(new Paragraph({ spacing: { before: 480 }, children: [new TextRun({ text: clean(input.disclaimer), italics: true, size: 16, font })] }));
  }
  const document = new Document({
    title: clean(input.title).slice(0, 200),
    creator: "ChatLaw",
    sections: [{ properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: paragraphs }],
  });
  return Packer.toBuffer(document);
}
