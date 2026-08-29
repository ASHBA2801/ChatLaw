"""Thin orchestration service around the existing RAG-05/RAG-06 modules."""

from context.case_documents import attach_case_context
from embeddings.provider import create_embedding_provider
from generation.answer import answer_question
from retrieval.vector_search import VectorSearcher, connect_from_environment


class RagService:
    def __init__(self, connection, embedding_provider, generator_factory=None):
        self.connection = connection
        self.searcher = VectorSearcher(connection, embedding_provider)
        self.generator_factory = generator_factory

    def search(self, query: str, top_k: int, min_similarity: float):
        return self.searcher.search(query, top_k=top_k, min_similarity=min_similarity)

    def chat(self, message: str, top_k: int, min_similarity: float, history: str = "",
             case_context: list | None = None, *, language: str = "en",
             retrieval_query: str | None = None):
        query_for_search = (retrieval_query or message).strip() or message
        retrieval = attach_case_context(
            self.search(query_for_search, top_k, min_similarity),
            case_context,
        )
        generator = None if retrieval.no_relevant_context else self.generator_factory()
        generate = None if generator is None else (
            lambda question, context: generator.generate(question, context, history, language=language)
        )
        response = answer_question(message, retrieval, generate, top_k=top_k, language=language)
        return retrieval, response

    def _text_generator(self, use_model: bool = True):
        if not use_model or self.generator_factory is None:
            return None
        try:
            model = self.generator_factory()
            return lambda prompt: model.generate_text(prompt)
        except (ValueError, RuntimeError):
            return None

    def generate_document(self, template_id: str, values: dict, *, use_model: bool = True,
                          section_ids: list[str] | None = None, top_k: int = 8, min_similarity: float = 0.6):
        from generation.document import generate_structured_document

        return generate_structured_document(
            template_id,
            values,
            searcher=self.searcher,
            generator=self._text_generator(use_model),
            top_k=top_k,
            min_similarity=min_similarity,
            section_ids=section_ids,
        )

    def revise_document(self, template_id: str, values: dict, sections: list, instruction: str, *,
                        target_section_ids: list[str] | None = None, use_model: bool = True,
                        top_k: int = 8, min_similarity: float = 0.6):
        from generation.document_edit import revise_structured_document

        return revise_structured_document(
            template_id,
            values,
            sections,
            instruction,
            searcher=self.searcher,
            generator=self._text_generator(use_model),
            top_k=top_k,
            min_similarity=min_similarity,
            target_section_ids=target_section_ids,
        )

    def selection_edit(self, *, selected_text: str, action: str, surrounding_section: dict,
                       document_title: str, jurisdiction: str, custom_instruction: str = "",
                       language: str = "en", use_model: bool = True):
        from generation.document_edit import edit_document_selection

        return edit_document_selection(
            selected_text=selected_text,
            action=action,
            surrounding_section=surrounding_section,
            document_title=document_title,
            jurisdiction=jurisdiction,
            custom_instruction=custom_instruction,
            language=language,
            generator=self._text_generator(use_model),
        )

    def close(self) -> None:
        self.connection.close()


def create_service() -> RagService:
    connection = connect_from_environment()
    try:
        provider = create_embedding_provider()
        # Keep Gemini initialization lazy so /api/search does not require a
        # generation client and no-context chat never initializes Gemini.
        def generator_factory():
            from generation.gemini import GeminiGenerator
            return GeminiGenerator()
        return RagService(connection, provider, generator_factory)
    except Exception:
        connection.close()
        raise