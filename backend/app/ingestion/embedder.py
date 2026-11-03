from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def generate_embeddings(texts):
    
    vectors = model.encode(texts, normalize_embeddings=True)

    return vectors.tolist()



if __name__ == "__main__":
     from app.database.repository import get_email
     from app.ingestion.chunker import chunk_email

     email = get_email("1a18df4d156aad64")
     if email:
          chunks = chunk_email(email, chunk_size=200, chunk_overlap=40)

          texts = []
          for c in chunks:
               texts.append(c["text"])

          vectors = generate_embeddings(texts)


          print("Subject:", email["subject"])
          print("Total chunks:", len(chunks))
          print("Total embeddings:", len(vectors))

           
