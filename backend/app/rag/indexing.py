from app.core.database import connect_db
from app.rag.embeddings import LocalEmbeddingModel
from app.rag.ingestion import ingest_structured_documents
from app.services.knowledge_repository import KnowledgeRepository


def main() -> None:
    print("Reading authoritative source documents...")

    records = ingest_structured_documents()

    print(f"Validated {len(records)} knowledge records.")

    # Upsert validated records into the knowledge repository
    with connect_db() as connection:
        repository = KnowledgeRepository(connection)
        changed = repository.upsert_records(records)

    print(f"Inserted or updated records: {changed}")

    # Generate embeddings for records that do not have them
    with connect_db() as connection:
        repository = KnowledgeRepository(connection)
        pending = repository.list_unembedded_records()

    print(f"Records requiring embeddings: {len(pending)}")

    if pending:
        print("Generating embeddings locally...")

        model = LocalEmbeddingModel()

        vectors = model.embed_documents([record.content for record in pending])

        # Store the generated embeddings in the knowledge repository
        with connect_db() as connection:
            repository = KnowledgeRepository(connection)

            for record, vector in zip(
                pending,
                vectors,
                strict=True,
            ):
                repository.save_embedding(
                    record.document_id,
                    record.record_id,
                    vector,
                )

        print(f"Stored {len(pending)} embeddings.")

    # Summarize the current state of the knowledge repository
    with connect_db() as connection:
        repository = KnowledgeRepository(connection)

        total = repository.count_records()
        remaining = len(repository.list_unembedded_records())

    print("\nKnowledge indexing complete")
    print(f"Database records: {total}")
    print(f"Records without embeddings: {remaining}")


if __name__ == "__main__":
    main()
