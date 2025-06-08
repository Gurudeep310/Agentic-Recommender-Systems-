import requests
from sentence_transformers import SentenceTransformer, util
import torch
import traceback

class SimilaritySearchUtilities:
    _model = None  # class-level shared model
    def __init__(self, model_name="all-mpnet-base-v2"):
        if SimilaritySearchUtilities._model is None:
            SimilaritySearchUtilities._model = SentenceTransformer(model_name)
        self.model = SimilaritySearchUtilities._model

    def _load_model_from_sentence_transformer(self, model = "all-mpnet-base-v2"):
        model = SentenceTransformer(model)
        return model

    def generate_embedding(self, text):
        embedding = self.model.encode(text)
        return embedding
    
    def get_top_k_results(self, user_query, list_of_document_embeddings, list_of_documents, top_k=5):
        try:
            top_k_documents = []
            top_k_scores = []
            embeddings_tensor = list_of_document_embeddings


            # FIX: Wrap user_query in a list and get the first result
            query_embedding = self.generate_embedding([user_query])[0]

            cosine_scores = util.cos_sim(query_embedding, embeddings_tensor)[0]
            top_results = torch.topk(cosine_scores, k=top_k)

            for score, idx in zip(top_results.values, top_results.indices):
                print(f"{list_of_documents[idx]} (score: {score:.4f})")
                top_k_documents.append(list_of_documents[idx])
                top_k_scores.append(round(score.item(), 4))

            return {
                "top_k_documents": top_k_documents,
                "top_k_scores": top_k_scores
            }
        except Exception as error:
            print(error)
            print(traceback.print_exc())
    

