import re
import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

# ==============================================================================
# STOP WORDS & VOCABULARY FILTERING
# ==============================================================================
# Standard English stop words + generic industry jargon to penalize high-frequency words.
# By filtering these out, we prevent generic terms (e.g. "software", "development") 
# from skewing the similarity metrics, ensuring that highly specific skills (like 
# "tensorflow" or "kubernetes") carry the appropriate matching weight.
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't",
    # Generic developer words to avoid skewing similarity metrics
    'software', 'developer', 'engineer', 'engineering', 'development', 'computer', 'science', 'application',
    'applications', 'system', 'systems', 'platform', 'platforms', 'tool', 'tools', 'technology', 'technologies',
    'role', 'roles', 'expert', 'specialist', 'specializes', 'focus', 'focuses'
}

def clean_and_tokenize(text: str) -> List[str]:
    """
    Cleans raw input text:
      1. Converts to lowercase.
      2. Replaces punctuation and special characters with spaces (keeps hyphens for tags like 'ci-cd' or 'rest-apis').
      3. Splits the string into individual words (tokens).
      4. Removes standard stopwords and generic industry terms.
      5. Discards words shorter than 2 characters.
    """
    if not text:
        return []
    # Replace non-alphanumeric (excluding hyphens) with spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\-]', ' ', text.lower())
    tokens = cleaned.split()
    # Remove standard and custom stop words
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


# ==============================================================================
# CONTENT-BASED RECOMMENDATION ENGINE
# ==============================================================================
class ContentBasedRecommender:
    def __init__(self, csv_path: str):
        """
        Initializes the recommender engine:
          - Loads the database CSV dataset.
          - Builds the global vocabulary and computes the TF-IDF profile vectors.
        """
        self.csv_path = csv_path
        self.df = None
        self.vocabulary: List[str] = []
        self.vocab_index: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: np.ndarray = None  # Holds the computed TF-IDF matrix (num_docs, vocab_size)
        self.load_dataset()
        self.fit()

    def load_dataset(self):
        """
        Loads the job roles dataset from CSV and verifies that the required schema columns 
        ('role', 'skills', 'description', 'tech_stack') are present.
        """
        try:
            self.df = pd.read_csv(self.csv_path)
            required_cols = {'role', 'skills', 'description', 'tech_stack'}
            if not required_cols.issubset(self.df.columns):
                raise ValueError(f"CSV must contain columns: {required_cols}")
        except Exception as e:
            print(f"Error loading dataset: {e}")
            raise

    def fit(self):
        """
        Builds the vector space model (TF-IDF Weighting) from the job roles dataset.
        Math Steps:
          1. Document Concatenation: Combines 'skills' and 'description' columns to form item documents.
          2. Vocabulary Extraction: Compiles a unique set of all filtered tokens across the entire corpus.
          3. Document Frequency (DF): Counts how many documents contain each unique term.
          4. Inverse Document Frequency (IDF): Penalizes common terms using the smooth math model:
             IDF(t) = ln( (1 + N) / (1 + DF(t)) ) + 1.0
             - N: total number of documents in the corpus
             - DF(t): number of documents containing term 't'
             - Smooth add-1 offsets prevent division-by-zero or negative log outputs.
          5. Term Frequency (TF): For each term in a document, computes TF(t, d) = count(t in d) / total_words_in_d.
          6. Matrix Vectorization: Populates doc_vectors[d_idx, t_idx] = TF(t, d) * IDF(t)
        """
        num_docs = len(self.df)
        all_doc_tokens = []
        
        # Step 1: Tokenize all roles (combining skills list with description text)
        for _, row in self.df.iterrows():
            combined_text = f"{row['skills']} {row['description']}"
            tokens = clean_and_tokenize(combined_text)
            all_doc_tokens.append(tokens)

        # Step 2: Extract unique terms to construct vocabulary space
        unique_terms = set()
        for tokens in all_doc_tokens:
            unique_terms.update(tokens)
        
        # Sort vocabulary alphabetically to ensure consistent vector ordering
        self.vocabulary = sorted(list(unique_terms))
        self.vocab_index = {term: idx for idx, term in enumerate(self.vocabulary)}
        vocab_size = len(self.vocabulary)

        # Step 3: Compute Document Frequency (DF) counts
        df_counts = {term: 0 for term in self.vocabulary}
        for tokens in all_doc_tokens:
            unique_tokens_in_doc = set(tokens)
            for token in unique_tokens_in_doc:
                if token in df_counts:
                    df_counts[token] += 1

        # Step 4: Compute Inverse Document Frequency (IDF) weights (using scikit-learn standard)
        self.idf = {}
        for term, df_count in df_counts.items():
            self.idf[term] = math.log((1 + num_docs) / (1 + df_count)) + 1.0

        # Step 5 & 6: Compute TF-IDF matrix representation for all database documents
        self.doc_vectors = np.zeros((num_docs, vocab_size))
        for doc_idx, tokens in enumerate(all_doc_tokens):
            if not tokens:
                continue
            
            # Count local term frequencies
            term_counts = {}
            for token in tokens:
                term_counts[token] = term_counts.get(token, 0) + 1
            
            total_tokens = len(tokens)
            for token, count in term_counts.items():
                if token in self.vocab_index:
                    term_idx = self.vocab_index[token]
                    tf = count / total_tokens
                    # Multiply local frequency by global relevance weight (TF * IDF)
                    self.doc_vectors[doc_idx, term_idx] = tf * self.idf[token]

    def transform(self, user_tokens: List[str]) -> np.ndarray:
        """
        Transforms a user's tokenized profile input (query) into a TF-IDF numerical vector.
        Maps each matching word to its index in the shared vocabulary space.
        Uses query Term Frequency (TF = count / total_query_words) multiplied by precomputed IDF weights.
        """
        vector = np.zeros(len(self.vocabulary))
        if not user_tokens:
            return vector
            
        # Count term frequencies in query
        term_counts = {}
        for token in user_tokens:
            if token in self.vocab_index:
                term_counts[token] = term_counts.get(token, 0) + 1
                
        total_tokens = len(user_tokens)
        for token, count in term_counts.items():
            term_idx = self.vocab_index[token]
            tf = count / total_tokens
            # Align query with vocabulary space using the fit IDF weights
            vector[term_idx] = tf * self.idf[token]
            
        return vector

    def get_cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Computes the Cosine Similarity between two vectors:
        Math:
          cos(theta) = (A . B) / (||A|| * ||B||)
        - np.dot(A, B): measures structural overlap
        - np.linalg.norm(A): Euclidean length / magnitude of vector A
        - Returns a score between 0.0 (no overlap) and 1.0 (perfect directional alignment).
        - Prevents division-by-zero for empty user profiles.
        """
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        # Handle zero vectors (cold start, or no matching words in vocab)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
            
        return float(dot_product / (norm_a * norm_b))

    def recommend(self, skills: List[str], interests: List[str], goals: List[str], top_n: int = 3) -> Dict[str, Any]:
        """
        Recommendation Pipeline (IPO Framework):
          1. Ingestion (Input): Combines skills list, interests list, and goal tags.
          2. Cold Start Detection: If input results in zero valid vocabulary words, 
             returns a cold_start response prompting onboarding survey.
          3. Vector Mapping & Scoring (Process): Transforms query into TF-IDF vector,
             then computes cosine similarity against all role vectors in the dataset.
          4. Overlap Tracking: Intersects query tokens with document skills to track matches.
          5. Sorting (Process): Sorts matches by similarity score descending.
          6. Filtering (Output): Truncates the results to the top 'N' roles to cure choice overload.
        """
        # Step 1: Combine inputs into a single query document
        combined_input = " ".join(skills + interests + goals)
        user_tokens = clean_and_tokenize(combined_input)
        
        # Step 2: Intercept Cold Start (all zeros / empty inputs)
        if not user_tokens:
            return {
                "cold_start": True,
                "recommendations": []
            }
            
        # Step 3: Map user text to the vocabulary vector space
        user_vector = self.transform(user_tokens)
        
        # Double check if vector is empty (terms do not exist in vocab at all)
        if np.linalg.norm(user_vector) == 0.0:
            return {
                "cold_start": True,
                "recommendations": []
            }

        # Step 4: Loop through dataset documents and compute similarity scores
        recommendations = []
        for idx, row in self.df.iterrows():
            doc_vector = self.doc_vectors[idx]
            similarity_score = self.get_cosine_similarity(user_vector, doc_vector)
            
            # Extract common matched keywords that triggered the recommendation
            doc_tokens = set(clean_and_tokenize(f"{row['skills']}"))
            user_tokens_set = set(user_tokens)
            matched_skills = sorted(list(doc_tokens.intersection(user_tokens_set)))
            
            recommendations.append({
                "role": row["role"],
                "description": row["description"],
                "tech_stack": row["tech_stack"],
                "similarity_score": round(similarity_score, 4),
                "matched_skills": matched_skills
            })

        # Step 5: Sort dataset descending based on calculated similarity score
        recommendations = sorted(recommendations, key=lambda x: x["similarity_score"], reverse=True)
        
        # Step 6: Filter list to prevent choice overload by cutting off at Top-N
        truncated_recommendations = recommendations[:top_n]
        
        return {
            "cold_start": False,
            "recommendations": truncated_recommendations
        }

    def get_all_unique_skills(self) -> List[str]:
        """
        UI Helper Method:
        Parses all skill strings in the dataset, extracts clean individual skill tags, 
        and returns them as a sorted list. Used to populate selection chips in onboarding.
        """
        unique_skills = set()
        for skills_str in self.df["skills"]:
            skills_list = re.split(r'[\s,]+', skills_str.lower())
            for skill in skills_list:
                cleaned = skill.strip()
                if cleaned and cleaned not in STOP_WORDS and len(cleaned) > 1:
                    unique_skills.add(cleaned)
        return sorted(list(unique_skills))
