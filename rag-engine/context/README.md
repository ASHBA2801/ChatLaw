# Context Construction

Intended to assemble retrieved chunks, hierarchical coordinates, and citations
into a prompt context for the generation model.

`builder.py` preserves each retrieved chunk verbatim and adds document,
hierarchy, page, chunk, and similarity metadata for prompt construction.