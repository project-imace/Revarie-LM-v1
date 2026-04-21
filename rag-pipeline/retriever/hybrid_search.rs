//! hybrid_search.rs – RAG Pipeline: Hybrid Search
//!
//! Combines dense vector search with sparse keyword search (BM25).
//! Fuses results using reciprocal rank fusion (RRF) or weighted score combination.
//!
//! Theoretical Foundations:
//! - Robertson & Zaragoza (2009): The Probabilistic Relevance Framework (BM25)
//! - Cormack et al. (2009): Reciprocal Rank Fusion (RRF)
//! - Lin et al. (2021): SPLADE v2 – Sparse Lexical and Expansion Model

use std::collections::{HashMap, HashSet};
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone)]
pub struct SearchResult {
    pub id: String,
    pub content: String,
    pub vector_score: f64,
    pub keyword_score: f64,
    pub fused_score: f64,
    pub metadata: HashMap<String, String>,
}

impl PartialEq for SearchResult {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}

impl Eq for SearchResult {}

impl Hash for SearchResult {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
    }
}

pub struct HybridSearcher {
    /// Reciprocal Rank Fusion constant (typically 60)
    rrf_k: f64,
    /// Weight for vector search (0.0 to 1.0)
    vector_weight: f64,
    /// Weight for keyword search (0.0 to 1.0)
    keyword_weight: f64,
}

impl Default for HybridSearcher {
    fn default() -> Self {
        Self {
            rrf_k: 60.0,
            vector_weight: 0.7,
            keyword_weight: 0.3,
        }
    }
}

impl HybridSearcher {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_weights(mut self, vector_weight: f64, keyword_weight: f64) -> Self {
        self.vector_weight = vector_weight;
        self.keyword_weight = keyword_weight;
        self
    }

    /// Combine vector and keyword search results using Reciprocal Rank Fusion.
    pub fn fuse_rrf(
        &self,
        vector_results: &[SearchResult],
        keyword_results: &[SearchResult],
        top_k: usize,
    ) -> Vec<SearchResult> {
        let mut rrf_scores: HashMap<String, f64> = HashMap::new();
        let mut result_map: HashMap<String, SearchResult> = HashMap::new();

        // Vector results RRF
        for (rank, result) in vector_results.iter().enumerate() {
            let rrf = 1.0 / (self.rrf_k + (rank + 1) as f64);
            *rrf_scores.entry(result.id.clone()).or_insert(0.0) += rrf;
            result_map.entry(result.id.clone()).or_insert_with(|| {
                let mut r = result.clone();
                r.fused_score = 0.0;
                r
            });
        }

        // Keyword results RRF
        for (rank, result) in keyword_results.iter().enumerate() {
            let rrf = 1.0 / (self.rrf_k + (rank + 1) as f64);
            *rrf_scores.entry(result.id.clone()).or_insert(0.0) += rrf;
            result_map.entry(result.id.clone()).or_insert_with(|| {
                let mut r = result.clone();
                r.fused_score = 0.0;
                r
            });
        }

        // Sort by RRF score and take top_k
        let mut fused: Vec<SearchResult> = result_map
            .into_values()
            .map(|mut r| {
                r.fused_score = *rrf_scores.get(&r.id).unwrap_or(&0.0);
                r
            })
            .collect();

        fused.sort_by(|a, b| b.fused_score.partial_cmp(&a.fused_score).unwrap());
        fused.truncate(top_k);
        fused
    }

    /// Combine using weighted score multiplication.
    pub fn fuse_weighted(
        &self,
        vector_results: &[SearchResult],
        keyword_results: &[SearchResult],
        top_k: usize,
    ) -> Vec<SearchResult> {
        let mut result_map: HashMap<String, SearchResult> = HashMap::new();

        for r in vector_results {
            result_map.insert(r.id.clone(), r.clone());
        }
        for r in keyword_results {
            result_map.entry(r.id.clone()).or_insert_with(|| r.clone());
        }

        let mut fused: Vec<SearchResult> = result_map
            .into_values()
            .map(|mut r| {
                r.fused_score = self.vector_weight * r.vector_score +
                                self.keyword_weight * r.keyword_score;
                r
            })
            .collect();

        fused.sort_by(|a, b| b.fused_score.partial_cmp(&a.fused_score).unwrap());
        fused.truncate(top_k);
        fused
    }

    /// Simple BM25 scoring for keyword matches.
    pub fn score_keywords(
        &self,
        query_terms: &[String],
        documents: &[SearchResult],
    ) -> Vec<SearchResult> {
        let k1 = 1.5;
        let b = 0.75;
        let avg_doc_len = documents.iter()
            .map(|d| d.content.split_whitespace().count() as f64)
            .sum::<f64>() / (documents.len() as f64).max(1.0);

        let mut doc_freq: HashMap<String, usize> = HashMap::new();
        for term in query_terms {
            for doc in documents {
                if doc.content.contains(term) {
                    *doc_freq.entry(term.clone()).or_insert(0) += 1;
                }
            }
        }

        let n = documents.len() as f64;

        let mut scored: Vec<SearchResult> = documents.iter().map(|doc| {
            let mut score = 0.0;
            let doc_len = doc.content.split_whitespace().count() as f64;

            for term in query_terms {
                let df = *doc_freq.get(term).unwrap_or(&0) as f64;
                if df == 0.0 { continue; }

                let idf = ((n - df + 0.5) / (df + 0.5)).ln();
                let tf = doc.content.matches(term).count() as f64;
                let numerator = tf * (k1 + 1.0);
                let denominator = tf + k1 * (1.0 - b + b * doc_len / avg_doc_len);
                score += idf * numerator / denominator;
            }

            let mut r = doc.clone();
            r.keyword_score = score;
            r
        }).collect();

        scored.sort_by(|a, b| b.keyword_score.partial_cmp(&a.keyword_score).unwrap());
        scored
    }
}

// =============================================================================
// Tests
// =============================================================================
