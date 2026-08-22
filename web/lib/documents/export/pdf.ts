import { PDFDocument, StandardFonts, rgb } from "pdf-lib";

import { DISCLAIMER } from "../constants";
import type { GeneratedDocumentPayload } from "../types";

function wrap(text: string, font: { widthOfTextAtSize: (text: string, size: number) => number }, size: number, maxWidth: number): string[] {
  const paragraphs = text.replace(/\r/g, "").split("\n");
  const lines: string[] = [];
  for (const paragraph of paragraphs) {
    if (!paragraph.trim()) {
      lines.push("");
      continue;
    }
    const words = paragraph.split(/\s+/);
    let current = "";
    for (const word of words) {
      const next = current ? `${current} ${word}` : word;
      if (font.widthOfTextAtSize(next, size) <= maxWidth) {
        current = next;
      } else {
        if (current) lines.push(current);
        current = word;
      }
    }
    if (current) lines.push(current);
  }
  return lines;
}

export async function buildPdf(payload: GeneratedDocumentPayload): Promise<Uint8Array> {
  const pdf = await PDFDocument.create();
  const font = await pdf.embedFont(StandardFonts.TimesRoman);
  const bold = await pdf.embedFont(StandardFonts.TimesRomanBold);
  const pageSize: [number, number] = [595.28, 841.89];
  const margin = 64;
  const maxWidth = pageSize[0] - margin * 2;
  let page = pdf.addPage(pageSize);
  let y = pageSize[1] - margin;
  const ink = rgb(0.09, 0.13, 0.11);

  const addPage = () => {
    page = pdf.addPage(pageSize);
    y = pageSize[1] - margin;
  };

  const write = (text: string, size: number, face = font, gap = 6) => {
    for (const line of wrap(text, face, size, maxWidth)) {
      if (y < margin + 28) addPage();
      if (line) {
        page.drawText(line, { x: margin, y, size, font: face, color: ink });
      }
      y -= size + gap;
    }
  };

  write(payload.title, 16, bold, 10);
  write(`Jurisdiction: India${payload.jurisdiction_region ? ` — ${payload.jurisdiction_region}` : ""}`, 10, font, 14);

  for (const section of payload.sections) {
    const heading = section.number ? `${section.number}. ${section.title}` : section.title;
    write(heading, 12, bold, 8);
    write(section.body, 11, font, 5);
    if (section.legal_basis?.length) {
      write("Legal basis:", 10, bold, 4);
      for (const basis of section.legal_basis) write(`• ${basis.label}`, 10, font, 3);
    }
    if (section.include_signature) {
      for (const block of payload.signatures) {
        y -= 8;
        for (const line of block.lines) write(line, 11, font, 6);
      }
    }
    y -= 8;
  }

  write("Disclaimer", 10, bold, 6);
  write(payload.disclaimer || DISCLAIMER, 9, font, 4);
  return pdf.save();
}
