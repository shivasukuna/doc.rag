import pickle

with open("documents.pkl", "rb") as f:
    docs = pickle.load(f)

print("Total chunks:", len(docs))

for i in range(min(5, len(docs))):
    print(docs[i])
