import { Document, HeadingLevel, Packer, Paragraph, TextRun } from "docx";

import { DISCLAIMER } from "../constants";
import type { GeneratedDocumentPayload } from "../types";

function paragraphsFrom(text: string, bold = false): Paragraph[] {
  return text.split(/\n/).map((line) => new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text: line || " ", bold, font: "Times New Roman", size: 22 })],
  }));
}

export async function buildDocx(payload: GeneratedDocumentPayload): Promise<Buffer> {
  const children: Paragraph[] = [
    new Paragraph({
      heading: HeadingLevel.TITLE,
      spacing: { after: 200 },
      children: [new TextRun({ text: payload.title, bold: true, font: "Times New Roman", size: 32 })],
    }),
    new Paragraph({
      spacing: { after: 300 },
      children: [new TextRun({
        text: `Jurisdiction: India${payload.jurisdiction_region ? ` — ${payload.jurisdiction_region}` : ""}`,
        italics: true,
        font: "Times New Roman",
        size: 20,
      })],
    }),
  ];

  for (const section of payload.sections) {
    const heading = section.number ? `${section.number}. ${section.title}` : section.title;
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_1,
      spacing: { before: 240, after: 120 },
      children: [new TextRun({ text: heading, bold: true, font: "Times New Roman", size: 24 })],
    }));
    children.push(...paragraphsFrom(section.body));
    if (section.legal_basis?.length) {
      children.push(new Paragraph({
        spacing: { before: 80, after: 80 },
        children: [new TextRun({ text: "Legal basis:", bold: true, font: "Times New Roman", size: 20 })],
      }));
      for (const basis of section.legal_basis) {
        children.push(new Paragraph({
          bullet: { level: 0 },
          children: [new TextRun({ text: basis.label, font: "Times New Roman", size: 20 })],
        }));
      }
    }
    if (section.include_signature) {
      for (const block of payload.signatures) {
        children.push(new Paragraph({ spacing: { before: 200 } }));
        for (const line of block.lines) {
          children.push(new Paragraph({
            spacing: { after: 80 },
            children: [new TextRun({ text: line, font: "Times New Roman", size: 22 })],
          }));
        }
      }
    }
  }

  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 400 },
    children: [new TextRun({ text: "Disclaimer", bold: true, font: "Times New Roman", size: 20 })],
  }));
  children.push(...paragraphsFrom(payload.disclaimer || DISCLAIMER));

  const document = new Document({
    sections: [{ properties: { page: { margin: { top: 720, bottom: 720, left: 720, right: 720 } } }, children }],
  });
  return Packer.toBuffer(document);
}
