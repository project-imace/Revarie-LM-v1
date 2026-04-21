#[cfg(test)]
mod tests {
    include!("../hybrid_search.rs");
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_rrf_fusion_basic() {
        let searcher = HybridSearcher::new();
        let vector = vec![SearchResult {
            id: "a".to_string(), content: "".to_string(),
            vector_score: 1.0, keyword_score: 0.0, fused_score: 0.0,
            metadata: HashMap::new(),
        }];
        let keyword = vec![];
        let fused = searcher.fuse_rrf(&vector, &keyword, 1);
        assert_eq!(fused.len(), 1);
    }
}
