if self.embedding_model:
    self.conocimiento_procesado, self.corpus_embeddings = self.procesar_conocimiento()
else:
    self.conocimiento_procesado, self.corpus_embeddings = [], None
