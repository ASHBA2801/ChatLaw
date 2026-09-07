import { PDFDocument, StandardFonts, rgb } from "pdf-lib";

import { DISCLAIMER } from "../constants";
import type { GeneratedDocumentPayload } from "../types";

function wrap(
  text: string,
  font: { widthOfTextAtSize: (text: string, size: number) => number },
  size: number,
  maxWidth: number,
): string[] {
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
  const italic = await pdf.embedFont(StandardFonts.TimesRomanItalic);

  const pageSize: [number, number] = [595.28, 841.89]; // ISO A4
  const margin = 54; // 0.75 in
  const maxWidth = pageSize[0] - margin * 2;
  const bottomThreshold = margin + 36;

  let page = pdf.addPage(pageSize);
  let y = pageSize[1] - margin;
  const ink = rgb(0.08, 0.12, 0.1);
  const muted = rgb(0.35, 0.4, 0.38);

  const addPage = () => {
    page = pdf.addPage(pageSize);
    y = pageSize[1] - margin;
  };

  const write = (
    text: string,
    size: number,
    face = font,
    gap = 5,
    align: "left" | "center" = "left",
    color = ink,
  ) => {
    for (const line of wrap(text, face, size, maxWidth)) {
      if (y < bottomThreshold) addPage();
      if (line) {
        let x = margin;
        if (align === "center") {
          const lineWidth = face.widthOfTextAtSize(line, size);
          x = Math.max(margin, (pageSize[0] - lineWidth) / 2);
        }
        page.drawText(line, { x, y, size, font: face, color });
      }
      y -= size + gap;
    }
  };

  // 1. Centered Formal Document Title
  write(payload.title.toUpperCase(), 14, bold, 8, "center");

  // 2. Centered Jurisdiction Line
  const jurisdictionText = `Jurisdiction: India${payload.jurisdiction_region ? ` — State / UT: ${payload.jurisdiction_region}` : ""}`;
  write(jurisdictionText, 9.5, italic, 16, "center", muted);

  // 3. Execution Requirements Callout (if present)
  if (payload.execution_requirements && payload.execution_requirements.length > 0) {
    write("EXECUTION & STAMP DUTY REQUIREMENTS:", 9, bold, 4, "left", muted);
    for (const req of payload.execution_requirements) {
      write(`• ${req}`, 8.5, italic, 3, "left", muted);
    }
    y -= 10;
  }

  // 4. Sections & Clauses
  for (const section of payload.sections) {
    const isUnnumbered = section.number === null || section.number === undefined;

    if (isUnnumbered) {
      const isMajor =
        section.title.includes("TITLE") ||
        section.title.includes("PREAMBLE") ||
        section.title.includes("VERIFICATION") ||
        section.title.includes("ATTESTATION") ||
        section.title.includes("SCHEDULE") ||
        section.title.includes("BEFORE THE");

      y -= 6;
      write(
        isMajor ? section.title.toUpperCase() : section.title,
        isMajor ? 11.5 : 11,
        bold,
        6,
        isMajor ? "center" : "left",
      );
    } else {
      y -= 4;
      const heading = `${section.number}. ${section.title}`;
      write(heading, 11, bold, 6, "left");
    }

    // Body
    write(section.body, 10, font, 4, "left");

    // Legal Basis
    if (section.legal_basis?.length) {
      y -= 3;
      write("Statutory Basis:", 8.5, bold, 3, "left", muted);
      for (const basis of section.legal_basis) {
        write(`• ${basis.label}`, 8.5, italic, 2, "left", muted);
      }
    }

    // Signatures and Witnesses
    if (section.include_signature && payload.signatures?.length) {
      y -= 10;
      const partyBlocks = payload.signatures.filter(
        (b) => !b.role.toLowerCase().includes("witness"),
      );
      const witnessBlocks = payload.signatures.filter((b) =>
        b.role.toLowerCase().includes("witness"),
      );

      // Party signatures
      for (const block of partyBlocks) {
        if (y < bottomThreshold + 60) addPage();
        write(block.role.toUpperCase(), 10, bold, 4);
        write(`Name: ${block.name}`, 9.5, font, 4);
        write("Signature: ____________________________________", 9.5, font, 4);
        write("Date: ________________________", 9.5, font, 10);
      }

      // Witness attestation
      if (witnessBlocks.length > 0) {
        y -= 8;
        if (y < bottomThreshold + 60) addPage();
        write("ATTESTATION BY TWO INDEPENDENT WITNESSES", 10.5, bold, 6, "center");
        for (const block of witnessBlocks) {
          write(block.role.toUpperCase(), 9.5, bold, 3);
          for (const line of block.lines) {
            if (line.toUpperCase() === block.role.toUpperCase()) continue;
            write(line, 9, font, 3);
          }
          y -= 4;
        }
      }
    }

    y -= 6;
  }

  // 5. Schedules
  if (payload.schedules && payload.schedules.length > 0) {
    for (const sched of payload.schedules) {
      y -= 10;
      write(sched.title.toUpperCase(), 11.5, bold, 6, "center");
      if (sched.description) {
        write(sched.description, 10, font, 4);
      }
      if (sched.boundaries && Object.keys(sched.boundaries).length > 0) {
        write("Boundaries of Property:", 9.5, bold, 4);
        for (const [side, desc] of Object.entries(sched.boundaries)) {
          write(`• ${side.toUpperCase()}: ${desc}`, 9, font, 3);
        }
      }
    }
  }

  // 6. Disclaimer
  y -= 12;
  write("LEGAL DISCLAIMER", 8.5, bold, 3, "left", muted);
  write(payload.disclaimer || DISCLAIMER, 8, italic, 3, "left", muted);

  // 7. Add running page numbers and headers across all pages
  const totalPages = pdf.getPageCount();
  for (let i = 0; i < totalPages; i++) {
    const p = pdf.getPage(i);
    const footerText = `Page ${i + 1} of ${totalPages} — ChatLaw Legal Drafting System (Review Required)`;
    const textWidth = font.widthOfTextAtSize(footerText, 8);
    p.drawText(footerText, {
      x: (pageSize[0] - textWidth) / 2,
      y: margin / 2,
      size: 8,
      font,
      color: muted,
    });
  }

  return pdf.save();
}
