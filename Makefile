load:
	@-rm -rf db > /dev/null 2>&1
	@-rm loaded.json > /dev/null 2>&1
	./src/document_loader.py

run:
	# Web app removed - use test commands instead
	python3 test/test_basic_functionality.py

createdb:
	@-rm -f rag-youtube.db > /dev/null 2>&1
	sqlite3 rag-youtube.db < schema.sql
	echo 'DELETE FROM runs' | sqlite3 rag-youtube.db

compare:
	./test/compare.py
