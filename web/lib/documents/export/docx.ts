import {
  AlignmentType,
  Document,
  HeadingLevel,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} from "docx";

import { DISCLAIMER } from "../constants";
import type { GeneratedDocumentPayload } from "../types";

function paragraphsFrom(
  text: string,
  bold = false,
  align: (typeof AlignmentType)[keyof typeof AlignmentType] = AlignmentType.JUSTIFIED,
): Paragraph[] {
  return text.split(/\n/).map((line) => {
    const trimmed = line.trim();
    return new Paragraph({
      alignment: align,
      spacing: { after: 120, line: 276 },
      children: [
        new TextRun({
          text: trimmed || " ",
          bold,
          font: "Times New Roman",
          size: 22, // 11pt
        }),
      ],
    });
  });
}

export async function buildDocx(payload: GeneratedDocumentPayload): Promise<Buffer> {
  const children: (Paragraph | Table)[] = [];

  // 1. Formal Uppercase Centered Document Title
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 140 },
      children: [
        new TextRun({
          text: payload.title.toUpperCase(),
          bold: true,
          font: "Times New Roman",
          size: 28, // 14pt
        }),
      ],
    }),
  );

  // 2. Jurisdiction & Provenance Subtitle
  const jurisdictionText = `Jurisdiction: India${payload.jurisdiction_region ? ` — State / UT: ${payload.jurisdiction_region}` : ""}`;
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 280 },
      children: [
        new TextRun({
          text: jurisdictionText,
          italics: true,
          font: "Times New Roman",
          size: 20, // 10pt
        }),
      ],
    }),
  );

  // 3. Execution Requirements Notice (if provided)
  if (payload.execution_requirements && payload.execution_requirements.length > 0) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { before: 100, after: 80 },
        children: [
          new TextRun({
            text: "STATUTORY EXECUTION REQUIREMENTS & STAMP DUTY NOTICE:",
            bold: true,
            font: "Times New Roman",
            size: 18,
          }),
        ],
      }),
    );
    for (const req of payload.execution_requirements) {
      children.push(
        new Paragraph({
          bullet: { level: 0 },
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: req,
              italics: true,
              font: "Times New Roman",
              size: 18,
            }),
          ],
        }),
      );
    }
    children.push(new Paragraph({ spacing: { after: 200 } }));
  }

  // 4. Document Sections & Numbered Clauses
  for (const section of payload.sections) {
    const isUnnumbered =
      section.number === null || section.number === undefined;

    if (isUnnumbered) {
      // Centered or uppercase bold for structural headers
      const isMajorHeader =
        section.title.includes("TITLE") ||
        section.title.includes("PREAMBLE") ||
        section.title.includes("VERIFICATION") ||
        section.title.includes("ATTESTATION") ||
        section.title.includes("SCHEDULE") ||
        section.title.includes("BEFORE THE");

      children.push(
        new Paragraph({
          alignment: isMajorHeader
            ? AlignmentType.CENTER
            : AlignmentType.LEFT,
          spacing: { before: 240, after: 120 },
          children: [
            new TextRun({
              text: isMajorHeader
                ? section.title.toUpperCase()
                : section.title,
              bold: true,
              font: "Times New Roman",
              size: 24, // 12pt
            }),
          ],
        }),
      );
    } else {
      const heading = `${section.number}. ${section.title}`;
      children.push(
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 240, after: 100 },
          children: [
            new TextRun({
              text: heading,
              bold: true,
              font: "Times New Roman",
              size: 22,
            }),
          ],
        }),
      );
    }

    // Section Body Text
    children.push(...paragraphsFrom(section.body));

    // Optional Legal Basis
    if (section.legal_basis?.length) {
      children.push(
        new Paragraph({
          spacing: { before: 80, after: 60 },
          children: [
            new TextRun({
              text: "Statutory Legal Basis & Verification:",
              bold: true,
              font: "Times New Roman",
              size: 18,
            }),
          ],
        }),
      );
      for (const basis of section.legal_basis) {
        children.push(
          new Paragraph({
            bullet: { level: 0 },
            children: [
              new TextRun({
                text: basis.label,
                font: "Times New Roman",
                size: 18,
              }),
            ],
          }),
        );
      }
    }

    // Signatures and Witness Attestation Block
    if (section.include_signature && payload.signatures?.length) {
      children.push(new Paragraph({ spacing: { before: 240 } }));

      // Split into parties and witnesses
      const partyBlocks = payload.signatures.filter(
        (b) => !b.role.toLowerCase().includes("witness"),
      );
      const witnessBlocks = payload.signatures.filter((b) =>
        b.role.toLowerCase().includes("witness"),
      );

      // Render Party Signature Blocks
      if (partyBlocks.length > 0) {
        for (const block of partyBlocks) {
          children.push(
            new Paragraph({
              spacing: { before: 160, after: 60 },
              children: [
                new TextRun({
                  text: block.role.toUpperCase(),
                  bold: true,
                  font: "Times New Roman",
                  size: 20,
                }),
              ],
            }),
          );
          children.push(
            new Paragraph({
              spacing: { after: 60 },
              children: [
                new TextRun({
                  text: `Name: ${block.name}`,
                  font: "Times New Roman",
                  size: 20,
                }),
              ],
            }),
          );
          children.push(
            new Paragraph({
              spacing: { after: 60 },
              children: [
                new TextRun({
                  text: "Signature: ____________________________________",
                  font: "Times New Roman",
                  size: 20,
                }),
              ],
            }),
          );
          children.push(
            new Paragraph({
              spacing: { after: 120 },
              children: [
                new TextRun({
                  text: "Date: ________________________",
                  font: "Times New Roman",
                  size: 20,
                }),
              ],
            }),
          );
        }
      }

      // Render Witness Attestation Blocks
      if (witnessBlocks.length > 0) {
        children.push(
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { before: 240, after: 120 },
            children: [
              new TextRun({
                text: "ATTESTATION BY TWO INDEPENDENT WITNESSES",
                bold: true,
                font: "Times New Roman",
                size: 22,
              }),
            ],
          }),
        );

        for (const block of witnessBlocks) {
          children.push(
            new Paragraph({
              spacing: { before: 100, after: 40 },
              children: [
                new TextRun({
                  text: block.role.toUpperCase(),
                  bold: true,
                  font: "Times New Roman",
                  size: 20,
                }),
              ],
            }),
          );
          for (const line of block.lines) {
            if (line.toUpperCase() === block.role.toUpperCase()) continue;
            children.push(
              new Paragraph({
                spacing: { after: 40 },
                children: [
                  new TextRun({
                    text: line,
                    font: "Times New Roman",
                    size: 20,
                  }),
                ],
              }),
            );
          }
          children.push(new Paragraph({ spacing: { after: 80 } }));
        }
      }
    }
  }

  // 5. Schedules (if defined)
  if (payload.schedules && payload.schedules.length > 0) {
    for (const sched of payload.schedules) {
      children.push(
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 300, after: 120 },
          children: [
            new TextRun({
              text: sched.title.toUpperCase(),
              bold: true,
              font: "Times New Roman",
              size: 24,
            }),
          ],
        }),
      );
      if (sched.description) {
        children.push(...paragraphsFrom(sched.description));
      }
      if (sched.boundaries && Object.keys(sched.boundaries).length > 0) {
        children.push(
          new Paragraph({
            spacing: { before: 100, after: 60 },
            children: [
              new TextRun({
                text: "Boundaries of the Property:",
                bold: true,
                font: "Times New Roman",
                size: 20,
              }),
            ],
          }),
        );
        for (const [side, desc] of Object.entries(sched.boundaries)) {
          children.push(
            new Paragraph({
              bullet: { level: 0 },
              spacing: { after: 40 },
              children: [
                new TextRun({
                  text: `${side.toUpperCase()}: ${desc}`,
                  font: "Times New Roman",
                  size: 20,
                }),
              ],
            }),
          );
        }
      }
    }
  }

  // 6. Disclaimer
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 400, after: 100 },
      children: [
        new TextRun({
          text: "Legal Disclaimer & Notice",
          bold: true,
          font: "Times New Roman",
          size: 18,
        }),
      ],
    }),
  );
  children.push(
    ...paragraphsFrom(
      payload.disclaimer || DISCLAIMER,
      false,
      AlignmentType.LEFT,
    ),
  );

  // A4 Standard Page Layout: 1440 twips = 1 inch margins
  const document = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1440,
              bottom: 1440,
              left: 1440,
              right: 1440,
            },
          },
        },
        children,
      },
    ],
  });

  return Packer.toBuffer(document);
}
