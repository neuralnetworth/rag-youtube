load:
	@-rm -rf db > /dev/null 2>&1
	@-rm loaded.json > /dev/null 2>&1
	uv run python src/document_loader_faiss.py

test:
	uv run python test/test_basic_functionality.py

test-all:
	uv run python test/test_suite.py

createdb:
	@-rm -f rag-youtube.db > /dev/null 2>&1
	sqlite3 rag-youtube.db < schema.sql
	echo 'DELETE FROM runs' | sqlite3 rag-youtube.db

compare:
	uv run python test/compare.py
